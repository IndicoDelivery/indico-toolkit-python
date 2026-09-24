from dataclasses import dataclass
from typing import Final

from .utils import get


@dataclass(frozen=True)
class Box:
    page: int
    top: int
    left: int
    right: int
    bottom: int

    def __bool__(self) -> bool:
        return self != NULL_BOX

    def __and__(self, other: "Box") -> "Box":
        """
        Return a new `Box` for the overlap between `self` and `other`
        or `NULL_BOX` if they don't overlap.

        Supports set-like `extraction.box & cell.box` syntax.
        """
        if (
            self.page != other.page
            or self.bottom <= other.top  # `self` is above `other`
            or self.top >= other.bottom  # `self` is below `other`
            or self.right <= other.left  # `self` is to the left of `other`
            or self.left >= other.right  # `self` is to the right of `other`
        ):
            return NULL_BOX
        else:
            return Box(
                page=self.page,
                top=max(self.top, other.top),
                left=max(self.left, other.left),
                right=min(self.right, other.right),
                bottom=min(self.bottom, other.bottom),
            )

    def __lt__(self, other: "Box") -> bool:
        """
        Bounding boxes are sorted with vertical hysteresis. Those on the same line are
        sorted left-to-right, even when later tokens are higher than earlier ones,
        as long as they overlap vertically.

        ┌──────────────────┐ ┌───────────────────┐
        │        1         │ │         2         │
        └──────────────────┘ │                   │
                             └───────────────────┘
                        ┌────────────────┐
        ┌─────────────┐ │        4       │ ┌─────┐
        │      3      │ └────────────────┘ │  5  │
        └─────────────┘                    └─────┘
        """
        return (
            self.page < other.page
            or (self.page == other.page and self.bottom < other.top)
            or (
                self.page == other.page
                and self.top < other.bottom
                and self.left < other.left
            )
        )

    @staticmethod
    def from_dict(box: object) -> "Box":
        return Box(
            page=get(box, int, "page_num"),
            top=get(box, int, "top"),
            left=get(box, int, "left"),
            right=get(box, int, "right"),
            bottom=get(box, int, "bottom"),
        )


# It's more ergonomic to represent the lack of a bounding box with a special null box
# object rather than using `None` or raising an error. This lets you e.g. sort by the
# `box` attribute without having to constantly check for `None`, while still allowing
# you do a "None check" with `bool(extraction.box)` or `extraction.box == NULL_BOX`.
NULL_BOX: Final = Box(page=0, top=0, left=0, right=0, bottom=0)
