import re
from typing import Any

from .task import TaskType
from .utils import get, has


def normalize_result_dict(result: "Any") -> None:
    """
    Fix inconsistencies observed in result file structure.
    """
    for errored_file in get(result, dict, "errored_files").values():
        # Parse filenames for errored files.
        if not has(errored_file, str, "input_filename"):
            reason = get(errored_file, str, "reason")
            match = re.search(r"file '([^']*)' with id", reason)
            errored_file["input_filename"] = match.group(1) if match else ""

        # Parse error from trackback for errored files.
        if not has(errored_file, str, "traceback"):
            traceback = get(errored_file, str, "error")
            error = traceback.split("\n")[-1].strip()
            errored_file["traceback"] = traceback
            errored_file["error"] = error

    # Convert `None` review notes to "".
    for review in get(result, dict, "reviews").values():
        if not has(review, str, "review_notes"):
            review["review_notes"] = ""


def normalize_prediction_dict(task_type: TaskType, prediction: "Any") -> None:
    """
    Fix inconsistencies observed in prediction structure.
    """
    # Predictions added in review lack a `confidence` section.
    # (And should theoretically have 100% confidence.)
    if not has(prediction, dict, "confidence"):
        prediction["confidence"] = {get(prediction, str, "label"): 1.0}

    # Extractions added in review may lack a `normalized` section.
    if task_type in (
        TaskType.DOCUMENT_EXTRACTION,
        TaskType.FORM_EXTRACTION,
        TaskType.GENAI_EXTRACTION,
    ) and not has(prediction, dict, "normalized"):
        prediction["normalized"] = {"formatted": get(prediction, str, "text")}

    # Document Extractions added in review may lack a `spans` section.
    # This value will match `NULL_SPAN`.
    if task_type in (
        TaskType.DOCUMENT_EXTRACTION,
        TaskType.GENAI_EXTRACTION,
    ) and not has(prediction, list, "spans"):
        prediction["spans"] = []

    # Form Extraction bounding boxes may very rarely have a `.0` decimal place,
    # which causes them to fail strict validation.
    if task_type == TaskType.FORM_EXTRACTION:
        for edge in ("top", "left", "right", "bottom"):
            if has(prediction, float, edge):
                prediction[edge] = int(prediction[edge])

    # Form Extractions added in review may lack bounding box information.
    # These values will match `NULL_BOX`.
    if task_type == TaskType.FORM_EXTRACTION and not has(prediction, int, "top"):
        prediction["page_num"] = 0
        prediction["top"] = 0
        prediction["left"] = 0
        prediction["right"] = 0
        prediction["bottom"] = 0

    # Document Extractions that didn't go through a linked labels transformer
    # lack a `groupings` section.
    if task_type in (
        TaskType.DOCUMENT_EXTRACTION,
        TaskType.GENAI_EXTRACTION,
    ) and not has(prediction, list, "groupings"):
        prediction["groupings"] = []

    # Summarizations added in review may lack a `citations` section.
    # This value will match `NULL_CITATION`.
    if task_type == TaskType.GENAI_SUMMARIZATION and not has(
        prediction, list, "citations"
    ):
        prediction["citations"] = []
