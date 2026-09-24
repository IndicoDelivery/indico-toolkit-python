from dataclasses import dataclass

from .utils import get


@dataclass(frozen=True, order=True)
class Document:
    id: int
    name: str
    etl_output_uri: str
    failed: bool
    error: str
    traceback: str

    # Auto review changes must reproduce all model and component sections that were
    # present in the original result file. This may not be possible from the
    # predictions alone--if a model or component had an empty section because it didn't
    # produce predictions or if all of the predictions for that section were dropped.
    # As such, the model and component IDs seen when parsing a result file are tracked
    # per-document so that the empty sections can be reproduced later.
    _model_ids: "frozenset[str]"
    _component_ids: "frozenset[str]"

    @staticmethod
    def from_dict(document: object) -> "Document":
        """
        Create a `Document` from a document dictionary.
        """
        model_results = get(document, dict, "model_results", "ORIGINAL")
        component_results = get(document, dict, "component_results", "ORIGINAL")

        return Document(
            id=get(document, int, "submissionfile_id"),
            name=get(document, str, "input_filename"),
            etl_output_uri=get(document, str, "etl_output"),
            failed=False,
            error="",
            traceback="",
            _model_ids=frozenset(model_results.keys()),
            _component_ids=frozenset(component_results.keys()),
        )

    @staticmethod
    def from_errored_file_dict(errored_file: object) -> "Document":
        """
        Create a `Document` from an errored file dictionary.
        """
        return Document(
            id=get(errored_file, int, "submissionfile_id"),
            name=get(errored_file, str, "input_filename"),
            etl_output_uri="",
            failed=True,
            error=get(errored_file, str, "error"),
            traceback=get(errored_file, str, "traceback"),
            _model_ids=frozenset(),
            _component_ids=frozenset(),
        )
