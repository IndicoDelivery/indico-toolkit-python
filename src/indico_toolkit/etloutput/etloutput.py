import itertools
from bisect import bisect_left, bisect_right
from collections import namedtuple
from dataclasses import dataclass
from functools import cached_property
from operator import attrgetter
from typing import TYPE_CHECKING

from .box import Box
from .table import Table
from .token import NULL_TOKEN, Token

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from .cell import Cell
    from .span import Span


@dataclass(frozen=True)
class EtlOutput:
    text: str
    text_on_page: "tuple[str, ...]"

    tokens: "tuple[Token, ...]"
    tokens_on_page: "tuple[tuple[Token, ...], ...]"

    tables: "tuple[Table, ...]"
    tables_on_page: "tuple[tuple[Table, ...], ...]"

    @staticmethod
    def from_pages(
        text_pages: "Iterable[str]",
        token_dict_pages: "Iterable[Iterable[object]]",
        table_dict_pages: "Iterable[Iterable[object]]",
    ) -> "EtlOutput":
        """
        Create an `EtlOutput` from pages of text, tokens, and tables.
        """
        text_pages = tuple(text_pages)
        token_pages = tuple(
            tuple(sorted(map(Token.from_dict, token_dict_page), key=attrgetter("span")))
            for token_dict_page in token_dict_pages
        )
        table_pages = tuple(
            tuple(sorted(map(Table.from_dict, table_dict_page), key=attrgetter("box")))
            for table_dict_page in table_dict_pages
        )

        return EtlOutput(
            text="\n".join(text_pages),
            text_on_page=text_pages,
            tokens=tuple(itertools.chain.from_iterable(token_pages)),
            tokens_on_page=token_pages,
            tables=tuple(itertools.chain.from_iterable(table_pages)),
            tables_on_page=table_pages,
        )

    def token_for(self, span: "Span") -> Token:
        """
        Return a `Token` that contains every character from `span`
        or `NULL_TOKEN` if one doesn't exist.
        """
        try:
            tokens = self.tokens_on_page[span.page]
            first = bisect_right(tokens, span.start, key=attrgetter("span.end"))
            last = bisect_left(tokens, span.end, lo=first, key=attrgetter("span.start"))
            tokens = tokens[first:last]
            assert tokens
        except (AssertionError, IndexError, ValueError):
            return NULL_TOKEN

        return Token(
            text=self.text[span.slice],
            box=Box(
                page=span.page,
                top=min(token.box.top for token in tokens),
                left=min(token.box.left for token in tokens),
                right=max(token.box.right for token in tokens),
                bottom=max(token.box.bottom for token in tokens),
            ),
            span=span,
        )

    _TableCellSpan = namedtuple("_TableCellSpan", ["table", "cell", "span"])

    @cached_property
    def _table_cell_spans_on_page(self) -> "tuple[tuple[_TableCellSpan, ...], ...]":
        """
        Order table cells on each page by their spans such that they can be bisected.
        """
        return tuple(
            tuple(
                sorted(
                    (
                        self._TableCellSpan(table, cell, span)
                        for table in page_tables
                        for cell in table.cells
                        for span in cell.spans
                        if span
                    ),
                    key=attrgetter("span"),
                )
            )
            for page_tables in self.tables_on_page
        )

    def table_cells_for(self, span: "Span") -> "Iterator[tuple[Table, Cell]]":
        """
        Yield the table cells that overlap with `span`.

        Note: a single span may overlap the same cell multiple times causing it to be
        yielded multiple times. Deduplication in `DocumentExtraction.table_cells`
        accounts for this when OCR is assigned with `PredictionList.assign_ocr()`.
        """
        try:
            page_table_cell_spans = self._table_cell_spans_on_page[span.page]
            first = bisect_right(
                page_table_cell_spans,
                span.start,
                key=attrgetter("span.end"),
            )
            last = bisect_left(
                page_table_cell_spans,
                span.end,
                lo=first,
                key=attrgetter("span.start"),
            )
            table_cell_spans = page_table_cell_spans[first:last]
        except (IndexError, ValueError):
            table_cell_spans = tuple()

        for table, cell, span in table_cell_spans:
            yield table, cell
