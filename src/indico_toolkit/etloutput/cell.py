from dataclasses import dataclass
from enum import Enum
from typing import Final

from .box import NULL_BOX, Box
from .range import NULL_RANGE, Range
from .span import NULL_SPAN, Span
from .utils import get


class CellType(Enum):
    HEADER = "header"
    CONTENT = "content"


@dataclass(frozen=True)
class Cell:
    type: CellType
    text: str
    box: Box
    range: Range
    spans: "tuple[Span, ...]"

    def __bool__(self) -> bool:
        return self != NULL_CELL

    def __hash__(self) -> int:
        """
        Uniquely identify cells by hashing their bounding box and spans.

        This is small speedup for `.groupby(attrgetter("cell"))` compared to
        dataclasses's default __hash__ implementation.
        """
        return hash((self.box, self.spans))

    @property
    def span(self) -> Span:
        """
        Return the first `Span` the cell covers or `NULL_SPAN` otherwise.

        Empty cells have no spans.
        """
        return self.spans[0] if self.spans else NULL_SPAN

    @staticmethod
    def from_dict(cell: object, page: int) -> "Cell":
        """
        Create a `Cell` from a cell dictionary.
        """
        get(cell, dict, "position")["page_num"] = page

        for doc_offset in get(cell, list, "doc_offsets"):
            doc_offset["page_num"] = page

        return Cell(
            type=CellType(get(cell, str, "cell_type")),
            text=get(cell, str, "text"),
            box=Box.from_dict(get(cell, dict, "position")),
            range=Range.from_dict(cell),
            spans=tuple(map(Span.from_dict, get(cell, list, "doc_offsets"))),
        )


# It's more ergonomic to represent the lack of cells with a special null cell object
# rather than using `None` or raising an error. This lets you e.g. sort by the `cell`
# attribute without having to constantly check for `None`, while still allowing you do
# a "None check" with `bool(extraction.cell)` or `extraction.cell == NULL_CELL`.
NULL_CELL: Final = Cell(
    type=CellType.CONTENT,
    text="",
    box=NULL_BOX,
    range=NULL_RANGE,
    spans=tuple(),
)
