from dataclasses import dataclass
from typing import Any, Final

from .utils import get


@dataclass(order=True, frozen=True)
class Span:
    page: int
    start: int
    end: int

    @property
    def slice(self) -> slice:
        return slice(self.start, self.end)

    def __bool__(self) -> bool:
        return self != NULL_SPAN

    def __and__(self, other: "Span") -> "Span":
        """
        Return a new `Span` for the overlap between `self` and `other`
        or `NULL_SPAN` if they don't overlap.

        Supports set-like `extraction.span & cell.span` syntax.
        """
        if (
            self.page != other.page
            or self.end <= other.start  # `self` is to the left of `other`
            or self.start >= other.end  # `self` is to the right of `other`
        ):
            return NULL_SPAN
        else:
            return Span(
                page=self.page,
                start=max(self.start, other.start),
                end=min(self.end, other.end),
            )

    @staticmethod
    def from_dict(span: object) -> "Span":
        return Span(
            page=get(span, int, "page_num"),
            start=get(span, int, "start"),
            end=get(span, int, "end"),
        )

    def to_dict(self) -> "dict[str, Any]":
        return {
            "page_num": self.page,
            "start": self.start,
            "end": self.end,
        }


# It's more ergonomic to represent the lack of spans with a special null span object
# rather than using `None` or raising an error. This lets you e.g. sort by the `span`
# attribute without having to constantly check for `None`, while still allowing you do
# a "None check" with `bool(extraction.span)` or `extraction.span == NULL_SPAN`.
NULL_SPAN: Final = Span(page=0, start=0, end=0)
