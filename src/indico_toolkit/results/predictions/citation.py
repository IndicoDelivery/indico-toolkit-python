from dataclasses import dataclass
from typing import Any, Final

from ...etloutput import NULL_SPAN, Span
from ..utils import get


@dataclass(order=True, frozen=True)
class Citation:
    start: int
    end: int
    span: Span

    @property
    def slice(self) -> slice:
        return slice(self.start, self.end)

    def __bool__(self) -> bool:
        return self != NULL_CITATION

    @staticmethod
    def from_dict(span: object) -> "Citation":
        return Citation(
            start=get(span, int, "response", "start"),
            end=get(span, int, "response", "end"),
            span=Span.from_dict(get(span, dict, "document")),
        )

    def to_dict(self) -> "dict[str, Any]":
        return {
            "response": {
                "start": self.start,
                "end": self.end,
            },
            "document": self.span.to_dict(),
        }


# It's more ergonomic to represent the lack of citations with a special null citation
# object rather than using `None` or raising an error. This lets you e.g. sort by the
# `citation` attribute without having to constantly check for `None`, while still
# allowing you do a "None check" with `bool(summarization.citation)` or
# `summarization.citation == NULL_CITATION`.
NULL_CITATION: Final = Citation(start=0, end=0, span=NULL_SPAN)
