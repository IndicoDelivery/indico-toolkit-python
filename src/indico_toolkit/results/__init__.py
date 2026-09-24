from typing import TYPE_CHECKING, TypeAlias, TypeVar, overload

from ..etloutput import NULL_BOX, NULL_SPAN, Box, Span
from .document import Document
from .predictionlist import PredictionList
from .predictions import (
    NULL_CITATION,
    Classification,
    DocumentExtraction,
    Extraction,
    FormExtraction,
    FormExtractionType,
    Group,
    Prediction,
    Summarization,
    Unbundling,
)
from .result import Result
from .review import Review, ReviewType
from .task import Task, TaskType
from .utils import json_loaded

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


__all__ = (
    "Box",
    "Classification",
    "Document",
    "DocumentExtraction",
    "Extraction",
    "FormExtraction",
    "FormExtractionType",
    "Group",
    "load",
    "load_async",
    "NULL_BOX",
    "NULL_CITATION",
    "NULL_SPAN",
    "Prediction",
    "PredictionList",
    "Result",
    "Review",
    "ReviewType",
    "Span",
    "Summarization",
    "Task",
    "TaskType",
    "Unbundling",
)

Loadable: TypeAlias = "dict[str, object] | str | bytes"
Readable = TypeVar("Readable")


@overload
def load(result: Loadable) -> Result: ...
@overload
def load(result: Readable, *, reader: "Callable[[Readable], Loadable]") -> Result: ...
def load(result: object, *, reader: "Callable[..., object] | None" = None) -> Result:
    """
    Load `result` as a `Result` dataclass. `result` can be a dict or JSON string/bytes.

    If `reader` is provided, it should read `result` to produce a loadable type.

    ```
    for result_file in result_folder.glob("*.json"):
        result = results.load(result_file, reader=Path.read_text)
    ```
    """
    if reader:
        result = reader(result)

    return Result.from_dict(json_loaded(result))


@overload
async def load_async(result: Loadable) -> Result: ...
@overload
async def load_async(
    result: Readable, *, reader: "Callable[[Readable], Awaitable[Loadable]]"
) -> Result: ...
async def load_async(
    result: object, *, reader: "Callable[..., Awaitable[object]] | None" = None
) -> Result:
    """
    Load `result` as a `Result` dataclass. `result` can be a dict or JSON string/bytes.

    If `reader` is provided, it should read `result` to produce a loadable type.

    ```
    result = await results.load_async(submission.result_file, reader=read_uri)
    ```
    """
    if reader:
        result = await reader(result)

    return Result.from_dict(json_loaded(result))
