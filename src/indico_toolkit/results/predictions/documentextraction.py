from copy import copy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ...etloutput import (
    NULL_CELL,
    NULL_SPAN,
    NULL_TABLE,
    NULL_TOKEN,
    Cell,
    Span,
    Table,
    Token,
)
from ..utils import get, has, omit
from .extraction import Extraction
from .group import Group

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from typing_extensions import Self

    from ..document import Document
    from ..review import Review
    from ..task import Task


@dataclass
class DocumentExtraction(Extraction):
    groups: "set[Group]"
    spans: "list[Span]"

    tokens: "list[Token]" = field(default_factory=list)
    tables: "list[Table]" = field(default_factory=list)
    cells: "list[Cell]" = field(default_factory=list)

    @property
    def span(self) -> Span:
        """
        Return the first `Span` the document extraction covers else `NULL_SPAN`.

        Predictions added in review may not have spans.
        """
        return self.spans[0] if self.spans else NULL_SPAN

    @span.setter
    def span(self, span: Span) -> None:
        """
        Overwrite all spans with the one provided, handling `NULL_SPAN`.

        This is assumes if you're setting a single span you want it to be the only one.
        Multiple-span sensitive contexts should work with `extraction.spans` instead.
        """
        self.spans = [span] if span else []

    @property
    def token(self) -> Token:
        """
        Return the first `Token` the document extraction covers
        or `NULL_TOKEN` if it doesn't cover a token or OCR hasn't been assigned yet.
        """
        return self.tokens[0] if self.tokens else NULL_TOKEN

    @token.setter
    def token(self, token: Token) -> None:
        """
        Overwrite all tokens with the one provided, handling `NULL_TOKEN`.

        This is assumes if you're setting a single token you want it to be the only one.
        Multiple-token sensitive contexts should work with `extraction.tokens` instead.
        """
        self.tokens = [token] if token else []

    @property
    def table(self) -> Table:
        """
        Return the first `Table` the document extraction is in
        or `NULL_TABLE` if it's not in a table or OCR hasn't been assigned yet.
        """
        return self.tables[0] if self.tables else NULL_TABLE

    @table.setter
    def table(self, table: Table) -> None:
        """
        Overwrite all tables with the one provided, handling `NULL_TABLE`.

        This is assumes if you're setting a single table you want it to be the only one.
        Multiple-table sensitive contexts should work with `extraction.tables` instead.
        """
        self.tables = [table] if table else []

    @property
    def cell(self) -> Cell:
        """
        Return the first `Cell` the document extraction is in
        or `NULL_CELL` if it's not in a cell or OCR hasn't been assigned yet.
        """
        return self.cells[0] if self.cells else NULL_CELL

    @cell.setter
    def cell(self, cell: Cell) -> None:
        """
        Overwrite all cells with the one provided, handling `NULL_CELL`.

        This is assumes if you're setting a single cell you want it to be the only one.
        Multiple-cell sensitive contexts should work with `extraction.cells` instead.
        """
        self.cells = [cell] if cell else []

    @property
    def table_cells(self) -> "Iterator[tuple[Table, Cell]]":
        """
        Yield the table cells the document extraction is in.
        """
        yield from zip(self.tables, self.cells)

    @table_cells.setter
    def table_cells(self, table_cells: "Iterable[tuple[Table, Cell]]") -> None:
        """
        Set the tables cells the document extraction is in.

        Deduplicate cells to handle the case where multiple
        spans are contained within the same cell.
        """
        self.tables = []
        self.cells = []

        for table, cell in table_cells:
            if cell not in self.cells:
                self.tables.append(table)
                self.cells.append(cell)

    def __deepcopy__(self, memo: Any) -> "Self":
        """
        Supports `copy.deepcopy(prediction)` without copying immutable objects.
        This provides a significant time and memory improvement when OCR is assigned.
        """
        new_instance = super().__deepcopy__(memo)
        new_instance.groups = copy(self.groups)
        new_instance.spans = copy(self.spans)
        new_instance.tokens = copy(self.tokens)
        new_instance.tables = copy(self.tables)
        new_instance.cells = copy(self.cells)
        return new_instance

    @staticmethod
    def from_dict(
        document: "Document",
        task: "Task",
        review: "Review | None",
        prediction: object,
    ) -> "DocumentExtraction":
        """
        Create a `DocumentExtraction` from a prediction dictionary.
        """
        return DocumentExtraction(
            document=document,
            task=task,
            review=review,
            label=get(prediction, str, "label"),
            confidences=get(prediction, dict, "confidence"),
            text=get(prediction, str, "normalized", "formatted"),
            accepted=(
                has(prediction, bool, "accepted") and get(prediction, bool, "accepted")
            ),
            rejected=(
                has(prediction, bool, "rejected") and get(prediction, bool, "rejected")
            ),
            groups=set(map(Group.from_dict, get(prediction, list, "groupings"))),
            spans=sorted(map(Span.from_dict, get(prediction, list, "spans"))),
            extras=omit(
                prediction,
                "label",
                "confidence",
                "accepted",
                "rejected",
                "groupings",
                "spans",
            ),
        )

    def to_dict(self) -> "dict[str, Any]":
        """
        Create a prediction dictionary for auto review changes.
        """
        prediction = {
            **self.extras,
            "label": self.label,
            "confidence": self.confidences,
            "groupings": [group.to_dict() for group in self.groups],
            "spans": [span.to_dict() for span in self.spans],
        }

        if self.text != get(prediction, str, "normalized", "formatted"):
            prediction["normalized"]["formatted"] = self.text
            prediction["normalized"]["text"] = self.text
            prediction["text"] = self.text

        if self.accepted:
            prediction["accepted"] = True
        elif self.rejected:
            prediction["rejected"] = True

        return prediction
