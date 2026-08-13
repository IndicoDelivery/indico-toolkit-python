from dataclasses import replace
from pathlib import Path

import pytest

from indico_toolkit import etloutput
from indico_toolkit.etloutput import NULL_SPAN, NULL_TOKEN, CellType, EtlOutput, Span

data_folder = Path(__file__).parent / "data"
etl_output_file = data_folder / "4725" / "111924" / "110239" / "etl_output.json"


def read_uri(uri: str | Path) -> bytes:
    uri = str(uri)
    storage_folder_path = uri.split("/storage/submission/")[-1]
    file_path = data_folder / storage_folder_path
    return file_path.read_bytes()


@pytest.fixture(scope="module")
def etl_output() -> EtlOutput:
    return etloutput.load(etl_output_file, reader=read_uri)


@pytest.fixture(scope="module")
def etl_output_no_tokens_tables() -> EtlOutput:
    return etloutput.load(etl_output_file, reader=read_uri, tokens=False, tables=False)


@pytest.fixture
def header_span() -> Span:
    return Span(page=1, start=1281, end=1285)


@pytest.fixture
def content_span() -> Span:
    return Span(page=1, start=1343, end=1349)


@pytest.fixture
def line_item_span() -> Span:
    return Span(page=1, start=1311, end=1344)


@pytest.fixture
def multiple_table_span() -> Span:
    return Span(page=1, start=1217, end=1299)


@pytest.fixture
def outside_table_span() -> Span:
    return Span(page=1, start=1056, end=1067)


def test_text_slice(
    etl_output: EtlOutput, header_span: Span, content_span: Span
) -> None:
    assert etl_output.text[header_span.slice] == "COST"
    assert etl_output.text[content_span.slice] == "720.00"


def test_token(etl_output: EtlOutput, header_span: Span, content_span: Span) -> None:
    header_token = etl_output.token_for(header_span)
    content_token = etl_output.token_for(content_span)

    assert header_token.span == header_span
    assert content_token.span == content_span

    assert header_token.text == "COST"
    assert content_token.text == "720.00"


def test_token_not_found(etl_output: EtlOutput, header_span: Span) -> None:
    assert etl_output.token_for(replace(header_span, page=3)) == NULL_TOKEN
    assert etl_output.token_for(NULL_SPAN) == NULL_TOKEN


def test_no_tokens(etl_output_no_tokens_tables: EtlOutput, header_span: Span) -> None:
    assert etl_output_no_tokens_tables.token_for(header_span) == NULL_TOKEN
    assert etl_output_no_tokens_tables.token_for(NULL_SPAN) == NULL_TOKEN


def test_table_cell(
    etl_output: EtlOutput, header_span: Span, content_span: Span
) -> None:
    (header_table, header_cell), *_ = etl_output.table_cells_for(header_span)
    (content_table, content_cell), *_ = etl_output.table_cells_for(content_span)

    assert header_cell.span == header_span
    assert content_cell.span == content_span

    assert header_cell.type == CellType.HEADER
    assert content_cell.type == CellType.CONTENT

    assert header_cell.text == "COST"
    assert content_cell.text == "720.00"


def test_table_cells(etl_output: EtlOutput, line_item_span: Span) -> None:
    table_cells = etl_output.table_cells_for(line_item_span)
    correct_table = etl_output.tables[3]
    correct_row = correct_table.rows[1]
    correct_cells = correct_row[1:4]

    for (table, cell), correct_cell in zip(table_cells, correct_cells):
        assert table == correct_table
        assert cell == correct_cell


def test_multiple_tables(etl_output: EtlOutput, multiple_table_span: Span) -> None:
    table_cells = etl_output.table_cells_for(multiple_table_span)
    cells = [cell for (table, cell) in table_cells]
    _correct_cells = etl_output.tables[2].rows[-1] + etl_output.tables[3].rows[0]
    correct_cells = [cell for cell in _correct_cells if cell.text]
    assert cells == correct_cells


def test_table_cell_not_found(etl_output: EtlOutput, outside_table_span: Span) -> None:
    assert not tuple(etl_output.table_cells_for(outside_table_span))
    assert not tuple(etl_output.table_cells_for(NULL_SPAN))
    assert not tuple(etl_output.table_cells_for(Span(-1, -1, -1)))


def test_no_tables(etl_output_no_tokens_tables: EtlOutput, header_span: Span) -> None:
    assert not tuple(etl_output_no_tokens_tables.table_cells_for(header_span))
    assert not tuple(etl_output_no_tokens_tables.table_cells_for(NULL_SPAN))


def test_empty_cell(etl_output: EtlOutput) -> None:
    table = etl_output.tables[2]
    filled_cell = table.rows[1][2]
    empty_cell = table.rows[1][3]

    assert filled_cell.text
    assert not empty_cell.text

    assert filled_cell.span
    assert not empty_cell.span
    assert empty_cell.span == NULL_SPAN
