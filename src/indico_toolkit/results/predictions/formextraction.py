from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

from ...etloutput import Box
from ..utils import get, has, omit
from .extraction import Extraction

if TYPE_CHECKING:
    from ..document import Document
    from ..review import Review
    from ..task import Task


class FormExtractionType(Enum):
    CHECKBOX = "checkbox"
    SIGNATURE = "signature"
    TEXT = "text"


@dataclass
class FormExtraction(Extraction):
    type: FormExtractionType
    box: Box
    checked: bool
    signed: bool

    @staticmethod
    def from_dict(
        document: "Document",
        task: "Task",
        review: "Review | None",
        prediction: object,
    ) -> "FormExtraction":
        """
        Create a `FormExtraction` from a prediction dictionary.
        """
        return FormExtraction(
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
            type=FormExtractionType(get(prediction, str, "type")),
            box=Box.from_dict(prediction),
            checked=(
                has(prediction, bool, "normalized", "structured", "checked")
                and get(prediction, bool, "normalized", "structured", "checked")
            ),
            signed=(
                has(prediction, bool, "normalized", "structured", "signed")
                and get(prediction, bool, "normalized", "structured", "signed")
            ),
            extras=omit(
                prediction,
                "label",
                "confidence",
                "accepted",
                "rejected",
                "type",
                "page_num",
                "top",
                "left",
                "right",
                "bottom",
                "checked",
                "signed",
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
            "type": self.type.value,
            "page_num": self.box.page,
            "top": self.box.top,
            "left": self.box.left,
            "right": self.box.right,
            "bottom": self.box.bottom,
        }

        if self.type == FormExtractionType.CHECKBOX:
            prediction["normalized"]["structured"] = {"checked": self.checked}
            text = "Checked" if self.checked else "Unchecked"
            prediction["normalized"]["formatted"] = text
            prediction["normalized"]["text"] = text
            prediction["text"] = text
        elif self.type == FormExtractionType.SIGNATURE:
            prediction["normalized"]["structured"] = {"signed": self.signed}
            text = "Signed" if self.signed else "Unsigned"
            prediction["normalized"]["formatted"] = text
            # Don't overwrite the text of the signature stored in these attributes.
            # prediction["normalized"]["text"] = text
            # prediction["text"] = text
        elif self.type == FormExtractionType.TEXT and self.text != get(
            prediction, str, "normalized", "formatted"
        ):
            prediction["normalized"]["formatted"] = self.text
            prediction["normalized"]["text"] = self.text
            prediction["text"] = self.text

        if self.accepted:
            prediction["accepted"] = True
        elif self.rejected:
            prediction["rejected"] = True

        return prediction
