from dataclasses import dataclass
from operator import attrgetter
from typing import Final

from .box import NULL_BOX, Box
from .cell import Cell
from .span import NULL_SPAN, Span
from .utils import get


@dataclass(frozen=True)
class Table:
    box: Box
    spans: "tuple[Span, ...]"
    cells: "tuple[Cell, ...]"
    rows: "tuple[tuple[Cell, ...], ...]"
    columns: "tuple[tuple[Cell, ...], ...]"

    def __bool__(self) -> bool:
        return self != NULL_TABLE

    def __hash__(self) -> int:
        """
        Uniquely identify tables by hashing their bounding box and spans.

        This is an order of magnitude speedup for `.groupby(attrgetter("table"))`
        compared to dataclasses's default __hash__ implementation.
        """
        return hash((self.box, self.spans))

    @property
    def span(self) -> Span:
        """
        Return the first `Span` the table covers or `NULL_SPAN` otherwise.
        """
        return self.spans[0] if self.spans else NULL_SPAN

    @staticmethod
    def from_dict(table: object) -> "Table":
        """
        Create a `Table` from a table dictionary.
        """
        page = get(table, int, "page_num")
        get(table, dict, "position")["page_num"] = page
        row_count = get(table, int, "num_rows")
        column_count = get(table, int, "num_columns")

        cells = tuple(
            sorted(
                (Cell.from_dict(cell, page) for cell in get(table, list, "cells")),
                key=attrgetter("range"),
            )
        )
        cells_by_row_col = {
            (row, column): cell
            for cell in cells
            for row in cell.range.rows
            for column in cell.range.columns
        }
        rows = tuple(
            tuple(
                cells_by_row_col[row, column]
                for column in range(column_count)
            )
            for row in range(row_count)
        )  # fmt: skip
        columns = tuple(
            tuple(
                cells_by_row_col[row, column]
                for row in range(row_count)
            )
            for column in range(column_count)
        )  # fmt: skip

        for doc_offset in get(table, list, "doc_offsets"):
            doc_offset["page_num"] = page

        return Table(
            box=Box.from_dict(get(table, dict, "position")),
            spans=tuple(map(Span.from_dict, get(table, list, "doc_offsets"))),
            cells=cells,
            rows=rows,
            columns=columns,
        )


# It's more ergonomic to represent the lack of tables with a special null table object
# rather than using `None` or raising an error. This lets you e.g. group by the `table`
# attribute without having to constantly check for `None`, while still allowing you do
# a "None check" with `bool(extraction.table)` or `extraction.table == NULL_TABLE`.
NULL_TABLE: Final = Table(
    box=NULL_BOX,
    spans=tuple(),
    cells=tuple(),
    rows=tuple(),
    columns=tuple(),
)
