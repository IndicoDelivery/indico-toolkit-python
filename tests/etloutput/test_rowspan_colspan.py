from pathlib import Path

import pytest

from indico_toolkit import etloutput
from indico_toolkit.etloutput import EtlOutput, Span, Table

data_folder = Path(__file__).parent / "data"
etl_output_file = data_folder / "4725" / "112731" / "112257" / "etl_output_rs_cs.json"


def read_uri(uri: str | Path) -> bytes:
    uri = str(uri)
    storage_folder_path = uri.split("/storage/submission/")[-1]
    file_path = data_folder / storage_folder_path
    return file_path.read_bytes()


@pytest.fixture(scope="module")
def etl_output() -> EtlOutput:
    return etloutput.load(etl_output_file, reader=read_uri)


@pytest.fixture(scope="module")
def table(etl_output: EtlOutput) -> Table:
    """
    Return the table from the rowspan / colspan sample:

    |   Alfa   |  Bravo  | Charlie |  Delta  |
    |----------|-------------------|---------|
    |          |      Foxtrot      | Golf    |
    | Echo     |-------------------|---------|
    |          | Hotel   | India   | Juliett |
    |----------|-------------------|---------|
    | Kilo     |                   | Mike    |
    |----------|        Lima       |---------|
    | November |                   | Oscar   |
     ----------------------------------------
    """
    return etl_output.tables[0]


def test_cells(table: Table) -> None:
    parsed_cells = [cell.text for cell in table.cells]
    expected_cells = [
        "Alfa", "Bravo", "Charlie", "Delta",
        "Echo", "Foxtrot", "Golf",
        "Hotel", "India", "Juliett",
        "Kilo", "Lima", "Mike",
        "November", "Oscar",
    ]  # fmt: skip
    assert parsed_cells == expected_cells


def test_rows(table: Table) -> None:
    parsed_rows = [[cell.text for cell in row] for row in table.rows]
    expected_rows = [
        ["Alfa", "Bravo", "Charlie", "Delta"],
        ["Echo", "Foxtrot", "Foxtrot", "Golf"],
        ["Echo", "Hotel", "India", "Juliett"],
        ["Kilo", "Lima", "Lima", "Mike"],
        ["November", "Lima", "Lima", "Oscar"],
    ]
    assert parsed_rows == expected_rows


def test_columns(table: Table) -> None:
    parsed_columns = [[cell.text for cell in column] for column in table.columns]
    expected_columns = [
        [
            "Alfa",
            "Echo",
            "Echo",
            "Kilo",
            "November",
        ],
        [
            "Bravo",
            "Foxtrot",
            "Hotel",
            "Lima",
            "Lima",
        ],
        [
            "Charlie",
            "Foxtrot",
            "India",
            "Lima",
            "Lima",
        ],
        [
            "Delta",
            "Golf",
            "Juliett",
            "Mike",
            "Oscar",
        ],
    ]
    assert parsed_columns == expected_columns


@pytest.mark.parametrize(
    "span, expected_text",
    [
        (Span(page=0, start=25, end=29), "Alfa"),
        (Span(page=0, start=30, end=35), "Bravo"),
        (Span(page=0, start=36, end=43), "Charlie"),
        (Span(page=0, start=44, end=49), "Delta"),
        (Span(page=0, start=50, end=54), "Echo"),
        (Span(page=0, start=55, end=62), "Foxtrot"),
        (Span(page=0, start=64, end=68), "Golf"),
        (Span(page=0, start=70, end=75), "Hotel"),
        (Span(page=0, start=76, end=81), "India"),
        (Span(page=0, start=82, end=89), "Juliett"),
        (Span(page=0, start=90, end=94), "Kilo"),
        (Span(page=0, start=111, end=115), "Lima"),
        (Span(page=0, start=97, end=101), "Mike"),
        (Span(page=0, start=102, end=110), "November"),
        (Span(page=0, start=117, end=122), "Oscar"),
    ],
)
def test_table_cell_for(etl_output: EtlOutput, span: Span, expected_text: str) -> None:
    (table, cell), *_ = etl_output.table_cells_for(span)
    assert cell.text == expected_text
