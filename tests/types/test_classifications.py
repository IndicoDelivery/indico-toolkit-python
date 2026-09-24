import tempfile
from copy import deepcopy

import pytest

from indico_toolkit.types import Classification, ClassificationMGP

pd = pytest.importorskip("pandas")


def test_init(static_class_preds):
    classification = Classification(static_class_preds)
    assert classification._pred == static_class_preds


def test_properties(classification_obj):
    assert classification_obj.label == "1"
    assert len(classification_obj.labels) == 4
    assert len(classification_obj.confidence_scores.keys()) == 4
    assert classification_obj.confidence == 0.31


def test_set_confidence_key_to_max_value(classification_obj):
    max_conf = max(classification_obj.confidence_scores.values())
    classification_obj.set_confidence_key_to_max_value()
    assert classification_obj.confidence_scores == max_conf


def test_to_csv(classification_obj):
    duplicated_obj = deepcopy(classification_obj)
    with tempfile.NamedTemporaryFile(suffix=".csv") as tf:
        filepath = tf.name
        classification_obj.to_csv(filepath, filepath, append_if_exists=False)
        df = pd.read_csv(filepath)
        assert (
            "confidence" in df.columns
            and "label" in df.columns
            and "filename" in df.columns
        )
        assert df.shape == (1, 3)
        duplicated_obj.to_csv(filepath, append_if_exists=True)
        df = pd.read_csv(filepath)
        assert df.shape == (2, 3)


def test_classification_MGP():
    obj = ClassificationMGP({"class A": 0.6, "class B": 0.4})
    assert obj.label == "class A"
    assert obj.confidence == 0.6
    assert obj.confidence_scores == {"class A": 0.6, "class B": 0.4}
    assert obj.labels == ["class A", "class B"]
