import pytest

from indico_toolkit.types import Extractions, WorkflowResult
from indico_toolkit.types.classification import Classification


def test_get_predictions_set_model_name(wf_result_obj: WorkflowResult):
    preds = wf_result_obj.post_reviews_predictions
    assert isinstance(preds, Extractions)
    assert isinstance(wf_result_obj.model_name, str)


def test_bad_model_name(wf_result_obj):
    wf_result_obj.model_name = "invalid model name"
    with pytest.raises(KeyError):
        wf_result_obj.get_predictions()


def test_no_final_preds():
    wf_result = WorkflowResult(
        {
            "submission_id": 12,
            "results": {"document": {"results": {"model_v1": {"pre_review": []}}}},
        },
        "model_v1",
    )
    assert wf_result.final_predictions._preds == []  # type: ignore[ty:unresolved-attribute]


def test_predictions_no_pre_review():
    wf_result = WorkflowResult(
        {
            "submission_id": 12,
            "results": {"document": {"results": {"model_v1": {"pre_review": []}}}},
        },
        "model_v1",
    )
    assert isinstance(wf_result.get_predictions, Extractions)


def test_classification_predictions():
    wf_result = WorkflowResult(
        {
            "submission_id": 12,
            "results": {"document": {"results": {"model_v1": {"pre_review": {}}}}},
        },
        "model_v1",
    )
    assert isinstance(wf_result.get_predictions, Classification)
