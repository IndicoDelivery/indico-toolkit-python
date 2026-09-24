from pathlib import Path

import pytest

from indico_toolkit import results

data_folder = Path(__file__).parent / "data"


@pytest.mark.parametrize("result_file", list(data_folder.glob("*.json")))
def test_file_load(result_file: Path) -> None:
    result = results.load(result_file, reader=Path.read_text)
    result.pre_review.to_changes(result)
    assert result.submission_id


@pytest.mark.parametrize("result_file", list(data_folder.glob("*.json")))
async def test_file_load_async(result_file: Path) -> None:
    async def path_read_bytes_async(path: Path) -> bytes:
        return path.read_bytes()

    result = await results.load_async(result_file, reader=path_read_bytes_async)
    result.pre_review.to_changes(result)
    assert result.submission_id


def test_usupported_version() -> None:
    with pytest.raises(ValueError):
        results.load({"file_version": 1})
