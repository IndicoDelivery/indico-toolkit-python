from dataclasses import dataclass
from enum import Enum

from .utils import get


class ReviewType(Enum):
    ADMIN = "admin"
    AUTO = "auto"
    MANUAL = "manual"


@dataclass(frozen=True, order=True)
class Review:
    id: int
    reviewer_id: int
    notes: str
    rejected: bool
    type: ReviewType

    @staticmethod
    def from_dict(review: object) -> "Review":
        """
        Create a `Review` from a review dictionary.
        """
        return Review(
            id=get(review, int, "review_id"),
            reviewer_id=get(review, int, "reviewer_id"),
            notes=get(review, str, "review_notes"),
            rejected=get(review, bool, "review_rejected"),
            type=ReviewType(get(review, str, "review_type")),
        )
