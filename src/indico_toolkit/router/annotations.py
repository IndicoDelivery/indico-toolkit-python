import inspect
import typing
from collections.abc import AsyncIterator, Iterable, Iterator
from typing import Any, NewType, TypeAlias

from .. import orm
from ..microclient import MicroClient
from .routes import Callback

_KwargsIter: TypeAlias = Iterator[tuple[str, Any]]
_AsyncKwargsIter: TypeAlias = AsyncIterator[tuple[str, Any]]

# Annotations that callbacks can use in their arguments.
DocumentId = NewType("DocumentId", int)
ExportId = NewType("ExportId", int)
FieldIds = NewType("FieldIds", frozenset[str])
SubmissionId = NewType("SubmissionId", int)
TableId = NewType("TableId", str)

# Return types that callbacks can use.
OrmIter: TypeAlias = Iterator[orm.Submission | orm.Table]
AsyncOrmIter: TypeAlias = AsyncIterator[orm.Submission | orm.Table]
FileNameBytes: TypeAlias = tuple[str, bytes]


def _annotations(callback: Callback) -> Iterable[tuple[str, Any]]:
    return inspect.get_annotations(callback).items()


def resolve_document(callback: Callback, signal: Any) -> _KwargsIter:
    for annotation_name, annotation_type in _annotations(callback):
        if annotation_type is DocumentId:
            yield annotation_name, signal["document_id"]


def resolve_export(callback: Callback, signal: Any) -> _KwargsIter:
    for annotation_name, annotation_type in _annotations(callback):
        if annotation_type is ExportId:
            yield annotation_name, signal["export_id"]


def resolve_field(callback: Callback, signal: Any) -> _KwargsIter:
    for annotation_name, annotation_type in _annotations(callback):
        if annotation_type is FieldIds:
            yield (
                annotation_name,
                frozenset(update["field_id"] for update in signal["updates"]),
            )


def resolve_microclient(callback: Callback, client: MicroClient) -> _KwargsIter:
    for annotation_name, annotation_type in _annotations(callback):
        if annotation_type is MicroClient:
            yield annotation_name, client


async def resolve_orm(
    callback: Callback,
    client: MicroClient,
    signal: Any,
) -> _AsyncKwargsIter:
    for annotation_name, annotation_type in _annotations(callback):
        if inspect.isclass(annotation_type) and issubclass(
            annotation_type, orm.Submission
        ):
            submission, *_ = orm.init(
                annotation_type,
                [
                    await client.graphql(query, variables)
                    for query, variables in orm.load(
                        annotation_type, signal["submission_id"]
                    )
                ],
            )
            yield annotation_name, submission

        elif (
            (collection_type := typing.get_origin(annotation_type)) is not None
            and (args := typing.get_args(annotation_type))
            and len(args) == 1
            and (table_class := args[0])
            and inspect.isclass(table_class)
            and issubclass(table_class, orm.Table)
        ):
            tables = collection_type(
                orm.init(
                    table_class,
                    [
                        await client.graphql(query, variables)
                        for query, variables in orm.load(
                            table_class, signal["submission_id"]
                        )
                    ],
                )
            )
            yield annotation_name, tables


def resolve_submission(callback: Callback, signal: Any) -> _KwargsIter:
    for annotation_name, annotation_type in _annotations(callback):
        if annotation_type is SubmissionId:
            yield annotation_name, signal["submission_id"]


def resolve_table(callback: Callback, signal: Any) -> _KwargsIter:
    for annotation_name, annotation_type in _annotations(callback):
        if annotation_type is TableId:
            yield annotation_name, signal["table_id"]
