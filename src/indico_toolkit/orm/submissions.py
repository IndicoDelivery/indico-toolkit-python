import dataclasses
import textwrap
import typing
from collections.abc import Iterable, Iterator
from datetime import date, datetime
from typing import Any

from .collections import WeakIdKeyDictionary
from .fields import get_fields, validate_fields
from .types import Categorical, GraphqlIterator, SubmissionType

_SUPPORTED_COLLECTION_TYPES = (
    list,
    set,
    None,
)
_SUPPORTED_SCALAR_TYPES: tuple[type, ...] = (  # type: ignore[ty:invalid-assignment]
    bool,
    Categorical,
    date,
    datetime,
    float,
    int,
    str,
)

_INSTANCE_PREV_VALUES = WeakIdKeyDictionary()
_INSTANCE_PREV_IDS = WeakIdKeyDictionary()


@typing.dataclass_transform()
class Submission:
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        dataclasses.dataclass(cls)
        validate_fields(
            cls,
            _SUPPORTED_SCALAR_TYPES,
            _SUPPORTED_COLLECTION_TYPES,
        )


def load(submission_class: type[Submission], submission_id: int) -> GraphqlIterator:
    """
    Yield GraphQL queries to load the fields specified on dataclass `submission_class`
    for submission ID `submission_id`.
    """
    yield (
        textwrap.dedent("""
            query load(
                $submissionId: ID!
                $fieldIds: [String!]!
            ) {
                submission(id: $submissionId) {
                    fields(fieldIds: $fieldIds) {
                        field {
                            fieldId
                        }
                        values(
                            filters: [
                                {
                                    field: "status"
                                    op: EQUAL
                                    textValues: "ACCEPTED"
                                }
                            ]
                        ) {
                            id
                            value
                        }
                    }
                }
            }
        """).strip(),
        {
            "submissionId": submission_id,
            "fieldIds": [field.id for field in get_fields(submission_class)],
        },
    )


def init(submission_class: type[SubmissionType], graphql: Iterable[Any]) -> Iterator[SubmissionType]:  # fmt: skip  # noqa: E501
    """
    Yield instances of `submission_class` using the GraphQL responses `graphql`
    for queries produced by `submissions.load()`.
    """
    submission = next(iter(graphql)).submission
    values_by_field_id = {
        field.field.fieldId: field.values
        for field in submission.fields
    }  # fmt: skip
    kwargs: dict[str, Any] = {}
    prev_values: dict[str, Any] = {}
    prev_ids: dict[str, Any] = {}

    for field in get_fields(submission_class):
        values = values_by_field_id.get(field.id)

        if field.multi and field.collection_type:
            if not values:
                kwargs[field.id] = field.collection_type()
                prev_values[field.id] = field.collection_type()
                prev_ids[field.id] = None
            else:
                kwargs[field.id] = field.collection_type(
                    field.scalar_parser(value.value) for value in values
                )
                prev_values[field.id] = field.collection_type(
                    field.scalar_parser(value.value) for value in values
                )
                prev_ids[field.id] = {
                    field.scalar_parser(value.value): value.id for value in values
                }
        else:
            if not values:
                kwargs[field.id] = None
                prev_values[field.id] = None
                prev_ids[field.id] = None
            else:
                kwargs[field.id] = field.scalar_parser(values[0].value)
                prev_values[field.id] = field.scalar_parser(values[0].value)
                prev_ids[field.id] = values[0].id

    instance = submission_class(**kwargs)
    _INSTANCE_PREV_VALUES[instance] = prev_values
    _INSTANCE_PREV_IDS[instance] = prev_ids
    yield instance


def save(submissions: Iterable[Submission], submission_id: int) -> GraphqlIterator:
    """
    Yield GraphQL queries to persist changes made to fields specified on `submissions`
    for submission ID `submission_id`.
    """
    for submission in submissions:
        prev_values = _INSTANCE_PREV_VALUES.get(submission, {})
        prev_ids = _INSTANCE_PREV_IDS.get(submission, {})

        for field in get_fields(type(submission)):
            next_value = getattr(submission, field.id)
            prev_value = prev_values.get(field.id)
            prev_id = prev_ids.get(field.id)

            if field.multi:
                next_value = set(next_value or [])
                prev_value = set(prev_value or [])
                prev_id = prev_id or {}
                added_values = next_value - prev_value
                removed_values = prev_value - next_value

                if removed_values:
                    yield (
                        textwrap.dedent("""
                            mutation remove(
                                $submissionId: ID!
                                $fieldId: String!
                                $linkIds: [ID!]!
                            ) {
                                candidateSubmissionFieldValues(
                                    submissionId: $submissionId
                                    fieldId: $fieldId
                                    fieldValueLinkIds: $linkIds
                                ) {
                                    id
                                }
                            }
                        """).strip(),
                        {
                            "submissionId": submission_id,
                            "fieldId": field.id,
                            "linkIds": [prev_id[value] for value in removed_values],
                        },
                    )

                for value in added_values:
                    yield (
                        textwrap.dedent("""
                            mutation add(
                                $submissionId: ID!
                                $fieldId: String!
                                $structuredValue: StructuredInput!
                            ) {
                                createSubmissionFieldValue(
                                    submissionId: $submissionId
                                    fieldId: $fieldId
                                    structuredValue: $structuredValue
                                ) {
                                    id
                                }
                            }
                        """).strip(),
                        {
                            "submissionId": submission_id,
                            "fieldId": field.id,
                            "structuredValue": _structured(
                                field.scalar_type,
                                value,
                            ),
                        },
                    )

            else:  # not field.multi
                if next_value is None and prev_id is not None:
                    yield (
                        textwrap.dedent("""
                            mutation remove(
                                $submissionId: ID!
                                $fieldId: String!
                                $linkIds: [ID!]!
                            ) {
                                candidateSubmissionFieldValues(
                                    submissionId: $submissionId
                                    fieldId: $fieldId
                                    fieldValueLinkIds: $linkIds
                                ) {
                                    id
                                }
                            }
                        """).strip(),
                        {
                            "submissionId": submission_id,
                            "fieldId": field.id,
                            "linkIds": [prev_id],
                        },
                    )

                if next_value is not None and next_value != prev_value:
                    yield (
                        textwrap.dedent("""
                            mutation add(
                                $submissionId: ID!
                                $fieldId: String!
                                $structuredValue: StructuredInput!
                            ) {
                                createSubmissionFieldValue(
                                    submissionId: $submissionId
                                    fieldId: $fieldId
                                    structuredValue: $structuredValue
                                ) {
                                    id
                                }
                            }
                        """).strip(),
                        {
                            "submissionId": submission_id,
                            "fieldId": field.id,
                            "structuredValue": _structured(
                                field.scalar_type,
                                next_value,
                            ),
                        },
                    )


def _structured(scalar_type: type[Any], value: Any) -> dict[str, dict[str, Any]]:
    """
    Return a `structuredValue` dictionary for `scalar_type` and `value`.
    """
    if scalar_type is bool:
        return {"boolean": {"value": value}}
    elif scalar_type is Categorical:
        return {"lookup": {"option": value}}
    elif scalar_type is date:
        return {"date": {"year": value.year, "month": value.month, "day": value.day}}
    elif scalar_type is datetime:
        return {
            "dateTime": {
                "year": value.year, "month": value.month, "day": value.day,
                "hour": value.hour, "minute": value.minute, "second": value.second,
                "microsecond": value.microsecond,
            }
        }  # fmt: skip
    elif scalar_type is int or scalar_type is float:
        return {"number": {"numberPrecise": str(value)}}
    elif scalar_type is str:
        return {"text": {"text": value}}
    else:
        raise TypeError(f"unmapped scalar type {scalar_type}")
