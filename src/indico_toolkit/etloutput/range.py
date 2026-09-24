from dataclasses import dataclass
from typing import Final

from .utils import get


@dataclass(order=True, frozen=True)
class Range:
    row: int
    column: int
    rowspan: int
    columnspan: int
    rows: "tuple[int, ...]"
    columns: "tuple[int, ...]"

    def __bool__(self) -> bool:
        return self != NULL_RANGE

    @staticmethod
    def from_dict(cell: object) -> "Range":
        """
        Create a `Range` from a cell dictionary.
        """
        rows = get(cell, list, "rows")
        columns = get(cell, list, "columns")

        return Range(
            row=min(rows),
            column=min(columns),
            rowspan=len(rows),
            columnspan=len(columns),
            rows=tuple(rows),
            columns=tuple(columns),
        )


# It's more ergonomic to represent the lack of ranges with a special null range object
# rather than using `None` or raising an error. This lets you e.g. sort by the `range`
# attribute without having to constantly check for `None`, while still allowing you do
# a "None check" with `bool(cell.range)` or `cell.range == NULL_RANGE`.
NULL_RANGE: Final = Range(
    row=0,
    column=0,
    rowspan=0,
    columnspan=0,
    rows=tuple(),
    columns=tuple(),
)
