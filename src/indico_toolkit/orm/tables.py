import dataclasses
import textwrap
import typing
from collections.abc import Iterable, Iterator, Sequence
from typing import Any

from .fields import get_fields, validate_fields
from .types import GraphqlIterator, TableType
from .utils import snake_cased

_SUPPORTED_COLLECTION_TYPES = (None,)
_SUPPORTED_SCALAR_TYPES = (str,)


@typing.dataclass_transform()
class Table:
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        dataclasses.dataclass(cls)
        validate_fields(
            cls,
            _SUPPORTED_SCALAR_TYPES,
            _SUPPORTED_COLLECTION_TYPES,
        )


def load(table_class: type[Table], submission_id: int) -> GraphqlIterator:
    """
    Yield GraphQL queries to load the table fields specified on dataclass `table_class`
    for submission ID `submission_id` and table ID `snake_case(table_class.__name__)`.

    The GraphQL API doesn't currently allow filtering table fields by field ID;
    so this actually loads all fields regardless of what's specified on `table_class`.
    """
    yield (
        textwrap.dedent("""
            query load(
                $submissionId: ID!
                $tableIds: [String!]
            ) {
                submission(id: $submissionId) {
                    tables(tableIds: $tableIds) {
                        rows {
                            cells {
                                field {
                                    fieldId
                                }
                                value {
                                    value
                                }
                            }
                        }
                    }
                }
            }
        """).strip(),
        {
            "submissionId": submission_id,
            "tableIds": [_table_id(table_class)],
        },
    )


def init(table_class: type[TableType], graphql: Iterable[Any]) -> Iterator[TableType]:
    """
    Yield instances of `table_class` using the GraphQL responses `graphql`
    for queries produced by `tables.load()`.
    """
    submission = list(graphql)[0].submission
    table = submission.tables[0]
    rows = table.rows

    for row in rows:
        values_by_field_id = {
            cell.field.fieldId: cell.value
            for cell in row.cells
        }  # fmt: skip
        kwargs: dict[str, Any] = {}

        for field in get_fields(table_class):
            if value := values_by_field_id.get(field.id):
                kwargs[field.id] = field.scalar_type(value.value)
            else:
                kwargs[field.id] = None

        yield table_class(**kwargs)


def save(tables: Sequence[Table], submission_id: int) -> GraphqlIterator:
    """
    Yield GraphQL queries to persist changes made to fields specified on `tables`
    for submission ID `submission_id`.
    """
    yield (
        textwrap.dedent("""
            mutation add(
                $submissionId: ID!
                $tableId: String!
                $cellInputs: [TableCellInput!]!
            ) {
                updateTableValues(
                    submissionId: $submissionId
                    tableId: $tableId
                    cellInputs: $cellInputs
                ) {
                    id
                }
            }
        """).strip(),
        {
            "submissionId": submission_id,
            "tableId": _table_id(type(tables[0])),
            "cellInputs": [
                {
                    "rowNumber": row_number,
                    "fieldId": field.id,
                    "text": str(next_value),
                }
                for row_number, table in enumerate(tables)
                for field in get_fields(type(table))
                if (next_value := getattr(table, field.id)) is not None
            ],
        },
    )


def _table_id(table_class: type[Table]) -> str:
    """
    Convert the table subclass name to a snake case table ID.
    """
    return snake_cased(table_class.__name__)
