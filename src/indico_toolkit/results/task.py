from dataclasses import dataclass
from enum import Enum

from .utils import get


class TaskType(Enum):
    CLASSIFICATION = "classification"
    DOCUMENT_EXTRACTION = "annotation"
    FORM_EXTRACTION = "form_extraction"
    GENAI_CLASSIFICATION = "genai_classification"
    GENAI_EXTRACTION = "genai_annotation"
    GENAI_SUMMARIZATION = "summarization"
    UNBUNDLING = "classification_unbundling"


@dataclass(frozen=True, order=True)
class Task:
    id: int
    name: str
    type: TaskType

    @staticmethod
    def from_dict(metadata: object) -> "Task":
        """
        Create a `Task` from a model group or component metadata dictionary.
        """
        return Task(
            id=get(metadata, int, "id"),
            name=get(metadata, str, "name"),
            type=TaskType(get(metadata, str, "task_type")),
        )
