from dataclasses import dataclass

from .prediction import Prediction


@dataclass
class Extraction(Prediction):
    text: str
    accepted: bool
    rejected: bool

    @property
    def page(self) -> int:
        """
        Convenience property to get an extraction's page without knowing its subclass.
        Allows you to do `predictions.extractions.groupby(attrgetter("page"))` et al.
        """
        if hasattr(self, "box"):
            return self.box.page  # type: ignore
        else:
            return self.span.page  # type: ignore

    def accept(self) -> None:
        self.accepted = True
        self.rejected = False

    def unaccept(self) -> None:
        self.accepted = False

    def reject(self) -> None:
        self.accepted = False
        self.rejected = True

    def unreject(self) -> None:
        self.rejected = False
