from typing import TYPE_CHECKING, TypeAlias, TypeVar

from .box import NULL_BOX, Box
from .cell import NULL_CELL, Cell, CellType
from .etloutput import EtlOutput
from .range import NULL_RANGE, Range
from .span import NULL_SPAN, Span
from .table import NULL_TABLE, Table
from .token import NULL_TOKEN, Token
from .utils import get, has, json_loaded, str_decoded

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

__all__ = (
    "Box",
    "Cell",
    "CellType",
    "EtlOutput",
    "load",
    "load_async",
    "NULL_BOX",
    "NULL_CELL",
    "NULL_RANGE",
    "NULL_SPAN",
    "NULL_TABLE",
    "NULL_TOKEN",
    "Range",
    "Span",
    "Table",
    "Token",
)

Loadable: TypeAlias = "dict[str, object] | list[object] | str | bytes"
Readable = TypeVar("Readable")
URI: TypeAlias = str


def load(
    etl_output: "Loadable | Readable",
    *,
    reader: "Callable[[Readable | URI], Loadable]",
    text: bool = True,
    tokens: bool = True,
    tables: bool = True,
) -> EtlOutput:
    """
    Load `etl_output` as an `EtlOutput` dataclass.

    `etl_output` can be a dict, JSON string/bytes, or something that can be read by
    `reader` to produce a loadable type.

    `reader` must be able to load Indico storage URIs as lists or JSON strings/bytes.

    Use `text`, `tokens`, and `tables` to specify what not to load.

    ```
    result = results.load(submission.result_file, reader=read_uri)
    etl_outputs = {
        document: etloutput.load(document.etl_output_uri, reader=read_uri)
        for document in result.documents
        if not document.failed
    }
    ```
    """
    if not isinstance(etl_output, dict):
        if (isinstance(etl_output, str) and etl_output.startswith("{")) or (
            isinstance(etl_output, bytes) and etl_output.startswith(b"{")
        ):
            etl_output = json_loaded(etl_output)
        else:
            etl_output = json_loaded(reader(etl_output))  # type: ignore[arg-type]

    pages = get(etl_output, list, "pages")

    if text and has(pages, str, 0, "text"):
        text_pages = map(
            lambda page: str_decoded(reader(get(page, str, "text"))), pages  # type: ignore[arg-type]
        )
    else:
        text_pages = ()  # type: ignore[assignment]

    if tokens and has(pages, str, 0, "tokens"):
        token_dict_pages = map(
            lambda page: json_loaded(reader(get(page, str, "tokens"))), pages
        )
    else:
        token_dict_pages = ()  # type: ignore[assignment]

    if tables and has(pages, str, 0, "tables"):
        table_dict_pages = map(
            lambda page: json_loaded(reader(get(page, str, "tables"))), pages
        )
    else:
        table_dict_pages = ()  # type: ignore[assignment]

    return EtlOutput.from_pages(text_pages, token_dict_pages, table_dict_pages)


async def load_async(
    etl_output: "Loadable | Readable",
    *,
    reader: "Callable[[Readable | URI], Awaitable[Loadable]]",
    text: bool = True,
    tokens: bool = True,
    tables: bool = True,
) -> EtlOutput:
    """
    Load `etl_output` as an `EtlOutput` dataclass.

    `etl_output` can be a dict, JSON string/bytes, or something that can be read by
    `reader` to produce a loadable type.

    `reader` must be able to load Indico storage URIs as lists or JSON strings/bytes.

    Use `text`, `tokens`, and `tables` to specify what not to load.

    ```
    result = await results.load_async(submission.result_file, reader=read_uri)
    etl_outputs = {
        document: await etloutput.load_async(document.etl_output_uri, reader=read_uri)
        for document in result.documents
        if not document.failed
    }
    ```
    """
    if not isinstance(etl_output, dict):
        if (isinstance(etl_output, str) and etl_output.startswith("{")) or (
            isinstance(etl_output, bytes) and etl_output.startswith(b"{")
        ):
            etl_output = json_loaded(etl_output)
        else:
            etl_output = json_loaded(await reader(etl_output))  # type: ignore[arg-type]

    pages = get(etl_output, list, "pages")

    if text and has(pages, str, 0, "text"):
        text_pages = [
            str_decoded(await reader(get(page, str, "text"))) for page in pages  # type: ignore[arg-type]
        ]
    else:
        text_pages = ()  # type: ignore[assignment]

    if tokens and has(pages, str, 0, "tokens"):
        token_dict_pages = [
            json_loaded(await reader(get(page, str, "tokens"))) for page in pages
        ]
    else:
        token_dict_pages = ()  # type: ignore[assignment]

    if tables and has(pages, str, 0, "tables"):
        table_dict_pages = [
            json_loaded(await reader(get(page, str, "tables"))) for page in pages
        ]
    else:
        table_dict_pages = ()  # type: ignore[assignment]

    return EtlOutput.from_pages(text_pages, token_dict_pages, table_dict_pages)
