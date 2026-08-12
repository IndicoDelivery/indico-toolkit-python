from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def tests_folder() -> Path:
    return Path(__file__).parent
