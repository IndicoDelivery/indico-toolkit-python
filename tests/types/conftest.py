import json
from copy import deepcopy

import pytest

from indico_toolkit.types import (
    Classification,
    Extractions,
    WorkflowResult,
)


@pytest.fixture(scope="module")
def static_extract_results():
    with open("tests/types/data/fin_disc_result.json", "r") as infile:
        results = json.load(infile)
    return results


@pytest.fixture(scope="module")
def static_class_results():
    with open("tests/types/data/fin_disc_classification.json", "r") as infile:
        results = json.load(infile)
    return results


@pytest.fixture(scope="module")
def static_extract_preds(static_extract_results):
    return static_extract_results["results"]["document"]["results"][
        "Toolkit Test Financial Model"
    ]


@pytest.fixture(scope="module")
def static_class_preds(static_class_results):
    return static_class_results["results"]["document"]["results"][
        "Toolkit Test Classification Model"
    ]


@pytest.fixture(scope="function")
def extractions_obj(static_extract_preds):
    return Extractions(deepcopy(static_extract_preds))


@pytest.fixture(scope="function")
def classification_obj(static_class_preds):
    return Classification(deepcopy(static_class_preds))


@pytest.fixture(scope="module")
def wf_result_obj(static_extract_results):
    return WorkflowResult(static_extract_results)
