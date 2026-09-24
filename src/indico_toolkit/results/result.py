from copy import deepcopy
from dataclasses import dataclass, replace
from functools import partial
from itertools import chain
from typing import TYPE_CHECKING, Any

from . import predictions as prediction
from .document import Document
from .normalization import normalize_result_dict
from .predictionlist import PredictionList
from .predictions import Prediction
from .review import Review, ReviewType
from .task import Task
from .utils import get

if TYPE_CHECKING:
    from typing_extensions import Self


@dataclass(frozen=True, order=True)
class Result:
    submission_id: int
    documents: "tuple[Document, ...]"
    tasks: "tuple[Task, ...]"
    reviews: "tuple[Review, ...]"
    predictions: "PredictionList[Prediction]"

    @property
    def rejected(self) -> bool:
        return len(self.reviews) > 0 and self.reviews[-1].rejected

    @property
    def pre_review(self) -> "PredictionList[Prediction]":
        return self.predictions.where(review=None)

    @property
    def auto_review(self) -> "PredictionList[Prediction]":
        return self.predictions.where(review=ReviewType.AUTO)

    @property
    def manual_review(self) -> "PredictionList[Prediction]":
        return self.predictions.where(review=ReviewType.MANUAL)

    @property
    def admin_review(self) -> "PredictionList[Prediction]":
        return self.predictions.where(review=ReviewType.ADMIN)

    @property
    def final(self) -> "PredictionList[Prediction]":
        return self.predictions.where(review=self.reviews[-1] if self.reviews else None)

    def __deepcopy__(self, memo: Any) -> "Self":
        """
        Supports `copy.deepcopy(result)` without copying immutable objects.
        """
        return replace(self, predictions=deepcopy(self.predictions, memo))

    @staticmethod
    def from_dict(result: object) -> "Result":
        """
        Create a `Result` from a result file dictionary.
        """
        file_version = get(result, int, "file_version")

        if file_version != 3:
            raise ValueError(f"unsupported result file version `{file_version}`")

        normalize_result_dict(result)

        submission_id = get(result, int, "submission_id")
        submission_results = get(result, list, "submission_results")
        modelgroup_metadata = get(result, dict, "modelgroup_metadata")
        component_metadata = get(result, dict, "component_metadata")
        review_metadata = get(result, dict, "reviews")
        errored_files = get(result, dict, "errored_files").values()

        static_model_components = filter(
            lambda component: (
                get(component, str, "component_type").casefold() == "static_model"
            ),
            component_metadata.values(),
        )

        documents = sorted(
            chain(
                map(Document.from_dict, submission_results),
                map(Document.from_errored_file_dict, errored_files),
            )
        )
        tasks = sorted(
            chain(
                map(Task.from_dict, modelgroup_metadata.values()),
                map(Task.from_dict, static_model_components),
            )
        )
        reviews = sorted(map(Review.from_dict, review_metadata.values()))

        predictions: "PredictionList[Prediction]" = PredictionList()

        for document_dict in submission_results:
            document_id = get(document_dict, int, "submissionfile_id")
            document = next(
                filter(lambda document: document.id == document_id, documents)
            )
            model_results = get(document_dict, dict, "model_results")
            component_results = get(document_dict, dict, "component_results")

            # Parse original predictions (which don't have an associated review).
            original_results = {
                **get(model_results, dict, "ORIGINAL"),
                **get(component_results, dict, "ORIGINAL"),
            }

            for task_id, task_predictions in original_results.items():
                task = next(filter(lambda task: task.id == int(task_id), tasks))
                predictions.extend(
                    map(
                        partial(prediction.from_dict, document, task, None),
                        task_predictions,
                    )
                )

            # Parse final predictions (associated with the most recent review).
            if reviews:
                review = reviews[-1]
                final_results = {
                    **get(model_results, dict, "FINAL"),
                    **get(component_results, dict, "FINAL"),
                }

                for task_id, task_predictions in final_results.items():
                    task = next(filter(lambda task: task.id == int(task_id), tasks))
                    predictions.extend(
                        map(
                            partial(prediction.from_dict, document, task, review),
                            task_predictions,
                        )
                    )

        return Result(
            submission_id=submission_id,
            documents=tuple(documents),
            tasks=tuple(tasks),
            reviews=tuple(reviews),
            predictions=predictions,
        )
