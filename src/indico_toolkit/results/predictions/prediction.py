from copy import copy, deepcopy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing_extensions import Self

    from ..document import Document
    from ..review import Review
    from ..task import Task


@dataclass
class Prediction:
    document: "Document"
    task: "Task"
    review: "Review | None"

    label: str
    confidences: "dict[str, float]"
    extras: "dict[str, Any]"

    @property
    def confidence(self) -> float:
        return self.confidences[self.label]

    @confidence.setter
    def confidence(self, value: float) -> None:
        self.confidences[self.label] = value

    def __deepcopy__(self, memo: Any) -> "Self":
        """
        Supports `copy.deepcopy(prediction)` without copying immutable objects.
        """
        new_instance = copy(self)
        new_instance.confidences = copy(self.confidences)
        new_instance.extras = deepcopy(self.extras, memo)
        return new_instance

    def __replace__override__(self, **attributes: Any) -> "Self":
        """
        Supports `copy.replace(prediction, **attrs)` on Python 3.13+

        Unlike `dataclasses.replace(**attrs)` this performs a deep copy and allows
        assigning properties in addition to attributes.

        E.g.
        >>> dataclasses.replace(prediction, confidence=1.0)
        Shallow copy and raises TypeError(...)
        >>> copy.replace(prediction, confidence=1.0)
        Deep copy and returns Prediction(confidence=1.0, ...)
        """
        new_instance = deepcopy(self)

        for attribute, value in attributes.items():
            setattr(new_instance, attribute, value)

        return new_instance

    def to_dict(self) -> "dict[str, Any]":
        """
        Create a prediction dictionary for auto review changes.
        """
        raise NotImplementedError()


# `dataclass()` doesn't (yet) provide a way to override the generated `__replace__`
# method on Python 3.13+. It must be overridden after class generation and unshadowed
# on all derived classes.
Prediction.__replace__ = Prediction.__replace__override__  # type:ignore
del Prediction.__replace__override__
