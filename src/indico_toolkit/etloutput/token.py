from dataclasses import dataclass
from typing import Final

from .box import NULL_BOX, Box
from .span import NULL_SPAN, Span
from .utils import get


@dataclass(frozen=True)
class Token:
    text: str
    box: Box
    span: Span

    def __bool__(self) -> bool:
        return self != NULL_TOKEN

    @staticmethod
    def from_dict(token: object) -> "Token":
        """
        Create a `Token` from a token dictionary.
        """
        get(token, dict, "position")["page_num"] = get(token, int, "page_num")
        get(token, dict, "doc_offset")["page_num"] = get(token, int, "page_num")

        return Token(
            text=get(token, str, "text"),
            box=Box.from_dict(get(token, dict, "position")),
            span=Span.from_dict(get(token, dict, "doc_offset")),
        )


# It's more ergonomic to represent the lack of tokens with a special null token object
# rather than using `None` or raising an error. This lets you e.g. sort by the `token`
# attribute without having to constantly check for `None`, while still allowing you do
# a "None check" with `bool(extraction.token)` or `extraction.token == NULL_TOKEN`.
NULL_TOKEN: Final = Token(
    text="",
    box=NULL_BOX,
    span=NULL_SPAN,
)
