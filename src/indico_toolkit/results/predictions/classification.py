from dataclasses import dataclass
from typing import Any

from ..document import Document
from ..review import Review
from ..task import Task
from ..utils import get, omit
from .prediction import Prediction


@dataclass
class Classification(Prediction):
    @staticmethod
    def from_dict(
        document: Document,
        task: Task,
        review: Review | None,
        prediction: object,
    ) -> "Classification":
        """
        Create a `Classification` from a prediction dictionary.
        """
        return Classification(
            document=document,
            task=task,
            review=review,
            label=get(prediction, str, "label"),
            confidences=get(prediction, dict, "confidence"),
            extras=omit(prediction, "label", "confidence"),
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Create a prediction dictionary for auto review changes.
        """
        return {
            **self.extras,
            "label": self.label,
            "confidence": self.confidences,
        }
