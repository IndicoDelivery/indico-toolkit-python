import pytest

from indico_toolkit.types import (
    Classification,
    ClassificationMGP,
    Extractions,
    Predictions,
)


def test_bad_type():
    with pytest.raises(TypeError):
        Predictions.get_obj("Bad type")


def test_get_obj_extractions(static_extract_preds):
    extraction_obj = Predictions.get_obj(static_extract_preds)
    assert isinstance(extraction_obj, Extractions)
    assert extraction_obj._preds == static_extract_preds


def test_get_obj_classification(static_class_preds):
    classification_obj = Predictions.get_obj(static_class_preds)
    assert isinstance(classification_obj, Classification)
    assert classification_obj._pred == static_class_preds


def test_get_obj_classification_mgp():
    classification_obj = Predictions.get_obj({"class A": 0.6, "class B": 0.4})
    assert isinstance(classification_obj, ClassificationMGP)
