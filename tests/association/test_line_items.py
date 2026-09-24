import pytest

from indico_toolkit.association import LineItems


def test_grouper_row_number_false_add_to_all(
    three_row_invoice_preds, three_row_invoice_tokens
):
    litems = LineItems(
        three_row_invoice_preds,
        ["work_order_number", "line_date", "work_order_tonnage"],
    )
    litems.get_bounding_boxes(three_row_invoice_tokens)
    litems.assign_row_number()
    assert len(litems._mapped_positions) == 5
    assert len(litems._unmapped_positions) == 1
    assert len(three_row_invoice_preds) == len(litems.updated_predictions)
    assert litems._unmapped_positions[0]["label"] == "should be ignored"
    for pred in litems._mapped_positions:
        if "row 1" in pred["text"]:
            assert "row_number" in pred.keys()
            assert pred["row_number"] == 1
        elif "row 2" in pred["text"]:
            assert "row_number" in pred.keys()
            assert pred["row_number"] == 2
        elif "row 3" in pred["text"]:
            assert "row_number" in pred.keys()
            assert pred["row_number"] == 3


def test_grouper_no_token_match_raise_exception(
    three_row_invoice_preds, three_row_invoice_tokens
):
    three_row_invoice_tokens.pop()
    litems = LineItems(
        three_row_invoice_preds,
        ["work_order_number", "line_date", "work_order_tonnage"],
    )
    with pytest.raises(Exception):
        litems.get_bounding_boxes(three_row_invoice_tokens)


def test_grouper_no_token_match_no_exception(
    three_row_invoice_preds, three_row_invoice_tokens
):
    three_row_invoice_tokens.pop()
    litems = LineItems(
        three_row_invoice_preds,
        ["work_order_number", "line_date", "work_order_tonnage"],
    )
    litems.get_bounding_boxes(three_row_invoice_tokens, raise_for_no_match=False)
    litems.assign_row_number()
    assert len(litems._errored_predictions) == 1
    assert "error" in litems._errored_predictions[0]
    assert "row_number" not in litems._errored_predictions[0]


def test_get_line_items_in_groups(three_row_invoice_preds, three_row_invoice_tokens):
    litems = LineItems(
        three_row_invoice_preds,
        ["work_order_number", "line_date", "work_order_tonnage"],
    )
    litems.get_bounding_boxes(three_row_invoice_tokens, raise_for_no_match=False)
    litems.assign_row_number()
    grouped_rows = litems.grouped_line_items
    assert len(grouped_rows) == 3
    assert isinstance(grouped_rows[0], list)
    assert isinstance(grouped_rows[0][0], dict)


def test_prediction_reordering(three_row_invoice_preds, three_row_invoice_tokens):
    # move the last ordered prediction to the front of the list
    three_row_invoice_preds.insert(0, three_row_invoice_preds.pop())
    litems = LineItems(
        three_row_invoice_preds,
        ["work_order_number", "line_date", "work_order_tonnage"],
    )
    litems.get_bounding_boxes(three_row_invoice_tokens, raise_for_no_match=False)
    litems.assign_row_number()
    assert len(litems.grouped_line_items) == 3


def test_empty_line_items_init(three_row_invoice_preds, three_row_invoice_tokens):
    with pytest.raises(TypeError):
        LineItems(three_row_invoice_preds)  # type: ignore[ty:missing-argument]


def test_mapped_positions_by_page(three_row_invoice_preds, three_row_invoice_tokens):
    litems = LineItems(
        three_row_invoice_preds,
        ("work_order_number", "line_date", "work_order_tonnage"),
    )
    litems.get_bounding_boxes(three_row_invoice_tokens)
    assert isinstance(litems.mapped_positions_by_page, dict)
    assert len(litems.mapped_positions_by_page) == 2
    assert len(litems.mapped_positions_by_page[0]) == 3
    assert len(litems.mapped_positions_by_page[1]) == 2


def test_predictions_sorted_by_bbtop(
    two_row_bank_statement_preds, two_row_bank_statement_tokens
):
    litems = LineItems(
        two_row_bank_statement_preds,
        ["Deposit Date", "Withdrawal Amount", "Deposit Amount", "Withdrawal Date"],
    )
    litems.get_bounding_boxes(two_row_bank_statement_tokens, raise_for_no_match=False)
    litems.assign_row_number()
    for row in litems.grouped_line_items:
        # without sorting by bbTop, rows would be 1 & 3 length
        assert len(row) == 2
