from pathlib import Path

import pytest

from indico_toolkit import etloutput

data_folder = Path(__file__).parent / "data"


def read_uri(uri: str | Path) -> str:
    uri = str(uri)
    storage_folder_path = uri.split("/storage/submission/")[-1]
    file_path = data_folder / storage_folder_path
    return file_path.read_text()


async def read_uri_async(uri: str | Path) -> str:
    return read_uri(uri)


@pytest.mark.parametrize("etl_output_file", list(data_folder.rglob("etl_output.json")))
def test_file_load(etl_output_file: Path) -> None:
    etl_output = etloutput.load(etl_output_file, reader=read_uri)
    page_count = len(etl_output.text_on_page)
    char_count = len(etl_output.text)
    token_count = len(etl_output.tokens)
    table_count = len(etl_output.tables)

    assert page_count == 2
    assert 2090 <= char_count <= 2093
    assert 326 <= token_count <= 331
    assert table_count in (0, 4)


@pytest.mark.parametrize("etl_output_file", list(data_folder.rglob("etl_output.json")))
async def test_file_load_async(etl_output_file: Path) -> None:
    etl_output = await etloutput.load_async(etl_output_file, reader=read_uri_async)
    page_count = len(etl_output.text_on_page)
    char_count = len(etl_output.text)
    token_count = len(etl_output.tokens)
    table_count = len(etl_output.tables)

    assert page_count == 2
    assert 2090 <= char_count <= 2093
    assert 326 <= token_count <= 331
    assert table_count in (0, 4)


@pytest.mark.parametrize("etl_output_file", list(data_folder.rglob("etl_output.json")))
def test_file_load_disable_values(etl_output_file: Path) -> None:
    etl_output = etloutput.load(
        etl_output_file,
        reader=read_uri,
        text=False,
        tokens=False,
        tables=False,
    )
    page_count = len(etl_output.text_on_page)
    char_count = len(etl_output.text)
    token_count = len(etl_output.tokens)
    table_count = len(etl_output.tables)

    assert page_count == 0
    assert char_count == 0
    assert token_count == 0
    assert table_count == 0


@pytest.mark.parametrize("etl_output_file", list(data_folder.rglob("etl_output.json")))
async def test_file_load_disable_values_async(etl_output_file: Path) -> None:
    etl_output = await etloutput.load_async(
        etl_output_file,
        reader=read_uri_async,
        text=False,
        tokens=False,
        tables=False,
    )
    page_count = len(etl_output.text_on_page)
    char_count = len(etl_output.text)
    token_count = len(etl_output.tokens)
    table_count = len(etl_output.tables)

    assert page_count == 0
    assert char_count == 0
    assert token_count == 0
    assert table_count == 0
