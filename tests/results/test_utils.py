import pytest

from indico_toolkit.results.utils import get, has, nfilter, omit


@pytest.fixture
def prediction() -> "dict[str, object]":
    return {
        "label": "Invoice Number",
        "text": "INV12345",
        "confidence": {
            "Invoice Number": 0.9,
        },
        "spans": [
            {"start": 123, "end": 456, "page_num": 0},
        ],
    }


def test_get_has(prediction: "dict[str, object]") -> None:
    assert has(prediction, str, "label")
    assert get(prediction, str, "label") == "Invoice Number"

    assert has(prediction, dict, "confidence")
    assert has(prediction, float, "confidence", "Invoice Number")
    assert get(prediction, float, "confidence", "Invoice Number") == 0.9

    assert has(prediction, list, "spans")
    assert has(prediction, int, "spans", 0, "start")
    assert get(prediction, int, "spans", 0, "start") == 123


def test_get_has_not(prediction: object) -> None:
    assert not has(prediction, str, "missing")
    with pytest.raises(KeyError):
        get(prediction, str, "missing")

    assert not has(prediction, int, "label")
    with pytest.raises(TypeError):
        get(prediction, int, "label")

    assert not has(prediction, float, "confidence", "Invoice Number", 0)
    with pytest.raises(TypeError):
        get(prediction, float, "confidence", "Invoice Number", 0)

    assert not has(prediction, int, "spans", "0", "start")
    with pytest.raises(TypeError):
        get(prediction, int, "spans", "0", "start")

    assert not has(prediction, int, "spans", -1, "start")
    with pytest.raises(IndexError):
        get(prediction, int, "spans", -1, "start")

    assert not has(prediction, int, "spans", -1, "start")
    with pytest.raises(IndexError):
        get(prediction, int, "spans", 1, "start")


def test_nfilter() -> None:
    values = list(range(100))
    filtered = list(filter(lambda n: n % 2, filter(lambda n: n % 3, values)))
    nfiltered = list(nfilter([(lambda n: n % 3), (lambda n: n % 2)], values))  # type: ignore[ty:invalid-argument-type]
    assert filtered == nfiltered


def test_omit(prediction: "dict[str, object]") -> None:
    assert omit(None) == {}
    assert omit(None, "missing") == {}

    assert omit({}) == {}
    assert omit({}, "missing") == {}

    assert omit({"key": "value"}) == {"key": "value"}
    assert omit({"key": "value"}, "missing") == {"key": "value"}
    assert omit({"key": "value"}, "key") == {}

    assert omit(prediction) == prediction
    assert omit(prediction, "confidence", "spans") == {
        "label": prediction["label"],
        "text": prediction["text"],
    }
