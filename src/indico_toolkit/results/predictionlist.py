from collections import defaultdict
from itertools import chain
from operator import attrgetter
from typing import TYPE_CHECKING, Any, Final, List, SupportsIndex, TypeVar, overload

from .predictions import (
    Classification,
    DocumentExtraction,
    Extraction,
    FormExtraction,
    FormExtractionType,
    Prediction,
    Summarization,
    Unbundling,
)
from .review import Review, ReviewType
from .utils import nfilter

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Container, Iterable, Mapping

    from typing_extensions import Self

    from ..etloutput import EtlOutput
    from .document import Document
    from .result import Result
    from .task import Task, TaskType

PredictionType = TypeVar("PredictionType", bound=Prediction)
OfType = TypeVar("OfType", bound=Prediction)
KeyType = TypeVar("KeyType")

# Non-None sentinel value to support `PredictionList.where(review=None)`.
REVIEW_UNSPECIFIED: Final = Review(
    id=None, reviewer_id=None, notes=None, rejected=None, type=None  # type: ignore[arg-type]
)


class PredictionList(List[PredictionType]):
    @property
    def classifications(self) -> "PredictionList[Classification]":
        return self.oftype(Classification)

    @property
    def document_extractions(self) -> "PredictionList[DocumentExtraction]":
        return self.oftype(DocumentExtraction)

    @property
    def extractions(self) -> "PredictionList[Extraction]":
        return self.oftype(Extraction)

    @property
    def form_extractions(self) -> "PredictionList[FormExtraction]":
        return self.oftype(FormExtraction)

    @property
    def summarizations(self) -> "PredictionList[Summarization]":
        return self.oftype(Summarization)

    @property
    def unbundlings(self) -> "PredictionList[Unbundling]":
        return self.oftype(Unbundling)

    @overload
    def __getitem__(self, index: "SupportsIndex", /) -> PredictionType: ...

    @overload
    def __getitem__(self, index: slice, /) -> "PredictionList[PredictionType]": ...

    def __getitem__(
        self, index: "SupportsIndex | slice"
    ) -> "PredictionType | PredictionList[PredictionType]":
        if isinstance(index, slice):
            return type(self)(super().__getitem__(index))
        else:
            return super().__getitem__(index)

    def apply(self, function: "Callable[[PredictionType], None]") -> "Self":
        """
        Apply `function` to all predictions.
        """
        for prediction in self:
            function(prediction)

        return self

    def assign_ocr(
        self,
        etl_outputs: "Mapping[Document, EtlOutput]",
        *,
        tokens: bool = True,
        tables: bool = True,
    ) -> "Self":
        """
        Assign OCR tokens, tables, and/or cells using `etl_outputs`.

        Use `tokens` or `tables` to skip lookup and assignment of those attributes.
        """
        extractions_by_document = self.oftype(
            DocumentExtraction,
        ).groupby(
            attrgetter("document"),
        )

        for document, extractions in extractions_by_document.items():
            etl_output = etl_outputs[document]

            for extraction in extractions:
                if tokens:
                    extraction.tokens = list(
                        filter(
                            None,
                            map(etl_output.token_for, extraction.spans),
                        )
                    )

                if tables:
                    extraction.table_cells = chain.from_iterable(
                        map(etl_output.table_cells_for, extraction.spans)
                    )

        return self

    def groupby(
        self, key: "Callable[[PredictionType], KeyType]"
    ) -> "dict[KeyType, Self]":
        """
        Group predictions into a dictionary using `key` to derive each prediction's key.
        E.g. `key=attrgetter("label")` or `key=attrgetter("task")`.

        If a derived key is an unhashable mutable collection (like set),
        it's automatically converted to its hashable immutable variant (like frozenset).
        This makes it easy to group by linked labels or unbundling pages.
        """
        grouped_predictions = defaultdict(type(self))  # type: ignore[var-annotated]

        for prediction in self:
            group_key = key(prediction)

            if isinstance(group_key, list):
                group_key = tuple(group_key)  # type: ignore[assignment]
            elif isinstance(group_key, set):
                group_key = frozenset(group_key)  # type: ignore[assignment]

            grouped_predictions[group_key].append(prediction)

        return grouped_predictions

    def groupbyiter(
        self, keys: "Callable[[PredictionType], Iterable[KeyType]]"
    ) -> "dict[KeyType, Self]":
        """
        Group predictions into a dictionary using `keys` to derive an iterable of keys.
        E.g. `key=attrgetter("groups")` or `key=attrgetter("pages")`.

        Each prediction is associated with every key in the iterable individually.
        If the iterable is empty, the prediction is not included in any group.
        """
        grouped_predictions = defaultdict(type(self))  # type: ignore[var-annotated]

        for prediction in self:
            for group_key in keys(prediction):
                grouped_predictions[group_key].append(prediction)

        return grouped_predictions

    def oftype(self, type: "type[OfType]") -> "PredictionList[OfType]":
        """
        Return a new prediction list containing predictions of type `type`.
        """
        return self.where(lambda prediction: isinstance(prediction, type))  # type: ignore[return-value]

    def orderby(
        self,
        key: "Callable[[PredictionType], Any]",
        *,
        reverse: bool = False,
    ) -> "Self":
        """
        Return a new prediction list with predictions sorted by `key`.
        """
        return type(self)(sorted(self, key=key, reverse=reverse))

    def where(
        self,
        predicate: "Callable[[PredictionType], bool] | None" = None,
        *,
        document: "Document | None" = None,
        document_in: "Container[Document] | None" = None,
        task: "Task | TaskType | str | None" = None,
        task_in: "Container[Task | TaskType | str] | None" = None,
        review: "Review | ReviewType | None" = REVIEW_UNSPECIFIED,
        review_in: "Container[Review | ReviewType | None]" = {REVIEW_UNSPECIFIED},
        label: "str | None" = None,
        label_in: "Container[str] | None" = None,
        page: "int | None" = None,
        page_in: "Collection[int] | None" = None,
        min_confidence: "float | None" = None,
        max_confidence: "float | None" = None,
        accepted: "bool | None" = None,
        rejected: "bool | None" = None,
        checked: "bool | None" = None,
        signed: "bool | None" = None,
    ) -> "Self":
        """
        Return a new prediction list containing predictions that match
        all of the specified filters.

        predicate: predictions for which this function returns True,
        document: predictions from this document,
        document_in: predictions from any of these documents,
        task: predictions from this task, task type, or task name,
        task_in: predictions from any of these tasks, task types, or task names,
        review: predictions from this review or review type,
        review_in: predictions from any of these reviews or review types,
        label: predictions with this label,
        label_in: predictions with any of these labels,
        page: extractions/unbundlings on this page,
        page_in: extractions/unbundlings on any of these pages,
        min_confidence: predictions with confidence >= this threshold,
        max_confidence: predictions with confidence <= this threshold,
        accepted: extractions that have or haven't been accepted,
        rejected: extractions that have or haven't been rejected,
        checked: form extractions that are or aren't checked,
        signed: form extractions that are or aren't signed.
        """
        predicates = []

        if predicate is not None:
            predicates.append(predicate)

        if document is not None:
            predicates.append(lambda prediction: prediction.document == document)

        if document_in is not None:
            predicates.append(lambda prediction: prediction.document in document_in)

        if task is not None:
            predicates.append(
                lambda prediction: (
                    prediction.task == task
                    or prediction.task.type == task
                    or prediction.task.name == task
                )
            )

        if task_in is not None:
            predicates.append(
                lambda prediction: (
                    prediction.task in task_in
                    or prediction.task.type in task_in
                    or prediction.task.name in task_in
                )
            )

        if review is not REVIEW_UNSPECIFIED:
            predicates.append(
                lambda prediction: (
                    prediction.review == review
                    or (
                        prediction.review is not None
                        and prediction.review.type == review
                    )
                )
            )

        if review_in != {REVIEW_UNSPECIFIED}:
            predicates.append(
                lambda prediction: (
                    prediction.review in review_in
                    or (
                        prediction.review is not None
                        and prediction.review.type in review_in
                    )
                )
            )

        if label is not None:
            predicates.append(lambda prediction: prediction.label == label)

        if label_in is not None:
            predicates.append(lambda prediction: prediction.label in label_in)

        if page is not None:
            predicates.append(
                lambda prediction: (
                    (isinstance(prediction, Extraction) and prediction.page == page)
                    or (isinstance(prediction, Unbundling) and page in prediction.pages)
                )
            )

        if page_in is not None:
            page_in = set(page_in)
            predicates.append(
                lambda prediction: (
                    (isinstance(prediction, Extraction) and prediction.page in page_in)
                    or (
                        isinstance(prediction, Unbundling)
                        and bool(page_in & set(prediction.pages))
                    )
                )
            )

        if min_confidence is not None:
            predicates.append(
                lambda prediction: prediction.confidence >= min_confidence
            )

        if max_confidence is not None:
            predicates.append(
                lambda prediction: prediction.confidence <= max_confidence
            )

        if accepted is not None:
            predicates.append(
                lambda prediction: isinstance(prediction, Extraction)
                and prediction.accepted == accepted
            )

        if rejected is not None:
            predicates.append(
                lambda prediction: isinstance(prediction, Extraction)
                and prediction.rejected == rejected
            )

        if checked is not None:
            predicates.append(
                lambda prediction: (
                    isinstance(prediction, FormExtraction)
                    and prediction.type == FormExtractionType.CHECKBOX
                    and prediction.checked == checked
                )
            )

        if signed is not None:
            predicates.append(
                lambda prediction: (
                    isinstance(prediction, FormExtraction)
                    and prediction.type == FormExtractionType.SIGNATURE
                    and prediction.signed == signed
                )
            )

        return type(self)(nfilter(predicates, self))

    def accept(self) -> "Self":
        """
        Mark extractions as accepted for auto review.
        """
        self.oftype(Extraction).apply(Extraction.accept)
        return self

    def unaccept(self) -> "Self":
        """
        Mark extractions as not accepted for auto review.
        """
        self.oftype(Extraction).apply(Extraction.unaccept)
        return self

    def reject(self) -> "Self":
        """
        Mark extractions as rejected for auto review.
        """
        self.oftype(Extraction).apply(Extraction.reject)
        return self

    def unreject(self) -> "Self":
        """
        Mark extractions as not rejected for auto review.
        """
        self.oftype(Extraction).apply(Extraction.unreject)
        return self

    def to_changes(self, result: "Result") -> "list[dict[str, Any]]":
        """
        Create a list for the `changes` argument of `SubmitReview` based on the
        predictions in this prediction list and the documents in `result`.
        """
        changes: "list[dict[str, Any]]" = []

        for document in result.documents:
            if document.failed:
                continue

            model_results: "dict[str, Any]" = {}
            component_results: "dict[str, Any]" = {}

            predictions_by_task = self.where(
                document=document,
            ).groupby(
                attrgetter("task"),
            )

            for task, predictions in predictions_by_task.items():
                task_id = str(task.id)
                prediction_dicts = [prediction.to_dict() for prediction in predictions]

                if task_id in document._model_ids:
                    model_results[task_id] = prediction_dicts
                elif task_id in document._component_ids:
                    component_results[task_id] = prediction_dicts

            for model_id in document._model_ids:
                if model_id not in model_results:
                    model_results[model_id] = []

            for component_id in document._component_ids:
                if component_id not in component_results:
                    component_results[component_id] = []

            changes.append(
                {
                    "submissionfile_id": document.id,
                    "model_results": model_results,
                    "component_results": component_results,
                }
            )

        return changes
