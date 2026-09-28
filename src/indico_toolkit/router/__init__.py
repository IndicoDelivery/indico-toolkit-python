from typing import Any

from ..microclient import MicroClient
from . import routes
from .annotations import (
    AsyncOrmIter,
    DocumentId,
    ExportId,
    FieldIds,
    FileNameBytes,
    OrmIter,
    SubmissionId,
    TableId,
)
from .create_submission import CreateSubmission, on_create_submission
from .start_export import (
    StartExport,
    on_start_custom_export,
    on_start_export,
    on_start_json_export,
)
from .update_document_type import UpdateDocumentType, on_update_document_type
from .update_field import UpdateField, on_update_field
from .update_status import UpdateStatus, on_update_status
from .update_table import UpdateTable, on_update_table

__all__ = (
    "AsyncOrmIter",
    "DocumentId",
    "ExportId",
    "FieldIds",
    "FileNameBytes",
    "on_create_submission",
    "on_start_custom_export",
    "on_start_export",
    "on_start_json_export",
    "on_update_document_type",
    "on_update_field",
    "on_update_status",
    "on_update_table",
    "OrmIter",
    "SubmissionId",
    "TableId",
    "trigger",
)


_ROUTE_MAPPING = {
    "document_type_update": UpdateDocumentType,
    "export_start": StartExport,
    "fields_update": UpdateField,
    "new_submission": CreateSubmission,
    "status_change": UpdateStatus,
    "table_update": UpdateTable,
}


async def trigger(client: MicroClient, signal: Any) -> None:
    if signal["type"].casefold() not in _ROUTE_MAPPING:
        return

    route = _ROUTE_MAPPING[signal["type"].casefold()].from_signal(signal)
    await routes.trigger(route, client, signal)
