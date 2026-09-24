from copy import copy
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any

from ..utils import get, has, omit
from .citation import NULL_CITATION, Citation
from .extraction import Extraction

if TYPE_CHECKING:
    from typing_extensions import Self

    from ...etloutput import Span
    from ..document import Document
    from ..review import Review
    from ..task import Task


@dataclass
class Summarization(Extraction):
    citations: "list[Citation]"

    @property
    def citation(self) -> Citation:
        """
        Return the first `Citation` the summarization covers else `NULL_CITATION`.

        Predictions added in review may not have citations.
        """
        return self.citations[0] if self.citations else NULL_CITATION

    @citation.setter
    def citation(self, citation: Citation) -> None:
        """
        Overwrite all citations with the one provided, handling `NULL_CITATION`.

        This is assumes if you're setting a single citation it should be the only one.
        Multiple-citation sensitive contexts should work with `summarization.citations`.
        """
        self.citations = [citation] if citation else []

    @property
    def spans(self) -> "tuple[Span, ...]":
        """
        Return the `Span`s covered by `self.citations`.
        """
        return tuple(citation.span for citation in self.citations)

    @property
    def span(self) -> "Span":
        """
        Return the `Span` the first citation covers else `NULL_SPAN`.

        Predictions added in review may not have citations.
        """
        return self.citation.span

    @span.setter
    def span(self, span: "Span") -> None:
        """
        Overwrite all citations with the first,
        replacing its span with the one provided.

        Using `NULL_SPAN` for a citation is not explicitly handled,
        and should be considered undefined behavior.

        This is assumes if you're setting a single span,
        there's only one citation and you want it to update its span.
        Multiple-context/span sensitive contexts should work with
        `summarization.citations` instead.
        """
        self.citation = replace(self.citation, span=span)

    def __deepcopy__(self, memo: Any) -> "Self":
        """
        Supports `copy.deepcopy(prediction)` without copying immutable objects.
        """
        new_instance = super().__deepcopy__(memo)
        new_instance.citations = copy(self.citations)
        return new_instance

    @staticmethod
    def from_dict(
        document: "Document",
        task: "Task",
        review: "Review | None",
        prediction: object,
    ) -> "Summarization":
        """
        Create a `Summarization` from a prediction dictionary.
        """
        return Summarization(
            document=document,
            task=task,
            review=review,
            label=get(prediction, str, "label"),
            confidences=get(prediction, dict, "confidence"),
            text=get(prediction, str, "text"),
            accepted=(
                has(prediction, bool, "accepted") and get(prediction, bool, "accepted")
            ),
            rejected=(
                has(prediction, bool, "rejected") and get(prediction, bool, "rejected")
            ),
            citations=sorted(
                map(Citation.from_dict, get(prediction, list, "citations"))
            ),
            extras=omit(
                prediction,
                "label",
                "confidence",
                "text",
                "accepted",
                "rejected",
                "citations",
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
            "text": self.text,
            "citations": [citation.to_dict() for citation in self.citations],
        }

        if self.accepted:
            prediction["accepted"] = True
        elif self.rejected:
            prediction["rejected"] = True

        return prediction
