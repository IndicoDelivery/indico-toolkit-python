import json
import os

import pytest

from indico_toolkit.association import Positioning


def generate_mapped_pred(
    bbTop=0,
    bbBot=10,
    bbLeft=0,
    bbRight=10,
    page_num=0,
    label="a",
):
    return {
        "bbTop": bbTop,
        "bbBot": bbBot,
        "bbLeft": bbLeft,
        "bbRight": bbRight,
        "label": label,
        "page_num": page_num,
    }


FILE_PATH = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope="function")
def bbox_token_page():
    with open(os.path.join(FILE_PATH, "data/token_page/tokens.json"), "r") as f:
        tokens = json.load(f)
    return tokens


@pytest.mark.parametrize(
    "input, expected",
    # first pred is "above", second is "below"
    [
        ((generate_mapped_pred(page_num=1), generate_mapped_pred(page_num=0)), False),
        ((generate_mapped_pred(page_num=0), generate_mapped_pred(page_num=1)), False),
        (
            (
                generate_mapped_pred(),
                generate_mapped_pred(11, 20),
            ),
            True,
        ),
        (
            (
                generate_mapped_pred(),
                generate_mapped_pred(11, 20, 11, 13),
            ),
            False,
        ),
        (
            (
                generate_mapped_pred(),
                generate_mapped_pred(11, 20, 5, 13),
            ),
            True,
        ),
        (
            (
                generate_mapped_pred(bbLeft=20, bbRight=30),
                generate_mapped_pred(11, 20, 5, 13),
            ),
            False,
        ),
        (
            (
                generate_mapped_pred(10, 20),
                generate_mapped_pred(),
            ),
            False,
        ),
    ],
)
def test_positioned_above_same_page_true(input, expected):
    print(input)
    positioning = Positioning()
    is_above = positioning.positioned_above(input[0], input[1], must_be_same_page=True)
    assert is_above == expected


@pytest.mark.parametrize(
    "input, expected",
    # first pred is "above", second is "below"
    [
        ((generate_mapped_pred(page_num=1), generate_mapped_pred()), False),
        ((generate_mapped_pred(), generate_mapped_pred(page_num=1)), True),
        (
            (
                generate_mapped_pred(bbLeft=20, bbRight=30),
                generate_mapped_pred(page_num=1),
            ),
            False,
        ),
    ],
)
def test_positioned_above_same_page_false(input, expected):
    positioning = Positioning()
    is_above = positioning.positioned_above(input[0], input[1], must_be_same_page=False)
    assert is_above == expected


@pytest.mark.parametrize(
    "input, expected",
    [
        ((generate_mapped_pred(), generate_mapped_pred(11, 20, 10, 20)), False),
        ((generate_mapped_pred(), generate_mapped_pred(-5, 5, 1, 9)), False),
        ((generate_mapped_pred(), generate_mapped_pred(11, 20, 6, 15)), False),
        (
            (generate_mapped_pred(0, 10, 10, 20), generate_mapped_pred(11, 20, 4, 15)),
            False,
        ),
        ((generate_mapped_pred(), generate_mapped_pred(11, 20, 1, 9)), True),
        ((generate_mapped_pred(), generate_mapped_pred(11, 20, 4, 15)), True),
        (
            (generate_mapped_pred(0, 10, 10, 20), generate_mapped_pred(11, 20, 5, 15)),
            True,
        ),
    ],
)
def test_positioned_above_overlap_same_page_true(input, expected):
    position = Positioning()
    output = position.positioned_above_overlap(
        input[0], input[1], min_overlap_percent=0.5
    )
    assert output == expected


def test_positioned_above_overlap_same_page_false():
    position = Positioning()
    with pytest.raises(ValueError):
        position.positioned_above_overlap(
            generate_mapped_pred(page_num=1),
            generate_mapped_pred(),
            min_overlap_percent=0.5,
        )


@pytest.mark.parametrize(
    "input, expected",
    [
        ((generate_mapped_pred(), generate_mapped_pred(-5, 5, 1, 9)), False),
        (
            (generate_mapped_pred(0, 10, 10, 20), generate_mapped_pred(11, 20, 4, 15)),
            True,
        ),
    ],
)
def test_positioned_above_overlap_min_overlap_percent_none(input, expected):
    position = Positioning()
    output = position.positioned_above_overlap(input[0], input[1])
    assert output == expected


@pytest.mark.parametrize(
    "input, expected",
    [
        ((generate_mapped_pred(), generate_mapped_pred()), True),
        ((generate_mapped_pred(), generate_mapped_pred(20, 30)), False),
        ((generate_mapped_pred(15, 21), generate_mapped_pred(20, 30)), True),
        ((generate_mapped_pred(29, 31), generate_mapped_pred(20, 30)), True),
        ((generate_mapped_pred(30, 31), generate_mapped_pred(20, 30)), False),
        ((generate_mapped_pred(29, 31), generate_mapped_pred(20, 30)), True),
    ],
)
def test_yaxis_overlap(input, expected):
    overlap = Positioning.yaxis_overlap(input[0], input[1])
    assert overlap == expected


@pytest.mark.parametrize(
    "input, expected",
    [
        ((generate_mapped_pred(), generate_mapped_pred()), True),
        ((generate_mapped_pred(), generate_mapped_pred(5, 7)), True),
        ((generate_mapped_pred(), generate_mapped_pred(9, 15, 50, 60)), True),
        ((generate_mapped_pred(), generate_mapped_pred(11, 30)), False),
        ((generate_mapped_pred(10, 20), generate_mapped_pred(20, 30)), False),
        ((generate_mapped_pred(), generate_mapped_pred(page_num=2)), True),
    ],
)
def test_positioned_on_same_level(input, expected):
    position = Positioning()
    output = position.positioned_on_same_level(
        input[0], input[1], must_be_same_page=False
    )
    assert output == expected


def test_positioned_on_same_level_must_be_same_page():
    position = Positioning()
    assert not position.positioned_on_same_level(
        generate_mapped_pred(), generate_mapped_pred(page_num=1)
    )


@pytest.mark.parametrize(
    "input, expected",
    [
        ((generate_mapped_pred(), generate_mapped_pred(0, 10, 20, 30)), 10),
        ((generate_mapped_pred(), generate_mapped_pred(20, 30)), 10),
        ((generate_mapped_pred(100, 110, 20, 30), generate_mapped_pred()), 90.55),
    ],
)
def test_get_min_distance(input, expected):
    position = Positioning()
    distance = position.get_min_distance(input[0], input[1])
    assert round(distance, 2) == expected


def test_get_min_distance_page_exception():
    position = Positioning()
    with pytest.raises(ValueError):
        position.get_min_distance(
            generate_mapped_pred(), generate_mapped_pred(page_num=1)
        )


@pytest.mark.parametrize(
    "input, expected",
    [
        ((generate_mapped_pred(page_num=2), generate_mapped_pred(0, 10, 20, 30)), 2010),
        ((generate_mapped_pred(page_num=1), generate_mapped_pred(20, 30)), 1010),
    ],
)
def test_get_min_distance_different_pages(input, expected):
    position = Positioning()
    distance = position.get_min_distance(input[0], input[1], page_height=1000)
    assert round(distance, 2) == expected


def test_get_horizontal_overlap_different_pages():
    position = Positioning()
    with pytest.raises(ValueError):
        position.get_horizontal_overlap(
            generate_mapped_pred(page_num=1),
            generate_mapped_pred(),
        )


@pytest.mark.parametrize(
    "input, expected",
    [
        (
            (generate_mapped_pred(0, 10, 0, 10), generate_mapped_pred(10, 20, 20, 40)),
            0.0,
        ),
        (
            (generate_mapped_pred(0, 10, 10, 20), generate_mapped_pred(10, 20, 0, 10)),
            0.0,
        ),
        ((generate_mapped_pred(0, 10, 0, 10), generate_mapped_pred(10, 20, 0, 5)), 1.0),
        ((generate_mapped_pred(0, 10, 0, 5), generate_mapped_pred(10, 20, 0, 10)), 0.5),
    ],
)
def test_get_horizontal_overlap(input, expected):
    position = Positioning()
    overlap = position.get_horizontal_overlap(input[0], input[1])
    assert round(overlap, 2) == expected


def test_get_vertical_overlap_different_pages():
    position = Positioning()
    with pytest.raises(ValueError):
        position.get_vertical_overlap(
            generate_mapped_pred(page_num=1),
            generate_mapped_pred(),
        )


@pytest.mark.parametrize(
    "input, expected",
    [
        (
            (generate_mapped_pred(0, 10, 0, 10), generate_mapped_pred(20, 40, 10, 20)),
            0.0,
        ),
        (
            (generate_mapped_pred(10, 20, 0, 10), generate_mapped_pred(0, 10, 10, 20)),
            0.0,
        ),
        ((generate_mapped_pred(0, 10, 0, 10), generate_mapped_pred(0, 5, 10, 20)), 1.0),
        ((generate_mapped_pred(0, 5, 0, 10), generate_mapped_pred(0, 10, 10, 20)), 0.5),
    ],
)
def test_get_vertical_overlap(input, expected):
    position = Positioning()
    overlap = position.get_vertical_overlap(input[0], input[1])
    assert round(overlap, 2) == expected


def test_get_vertical_min_distance():
    position = Positioning()
    input = (generate_mapped_pred(), generate_mapped_pred(20, 30, 20, 30))
    distance = position.get_vertical_min_distance(input[0], input[1], page_height=1000)
    assert round(distance, 2) == 10


@pytest.mark.parametrize(
    "input, expected",
    [
        ((generate_mapped_pred(page_num=2), generate_mapped_pred(0, 10, 20, 30)), 1990),
        ((generate_mapped_pred(page_num=1), generate_mapped_pred(20, 30)), 970),
    ],
)
def test_get_vertical_min_distance_different_pages(input, expected):
    position = Positioning()
    distance = position.get_vertical_min_distance(input[1], input[0], page_height=1000)
    assert round(distance, 2) == expected


def test_get_horizontal_min_distance():
    position = Positioning()
    input = (generate_mapped_pred(), generate_mapped_pred(0, 10, 20, 30))
    distance = position.get_horizontal_min_distance(input[0], input[1])
    assert round(distance, 2) == 10


@pytest.mark.parametrize(
    "input, expected",
    [
        (((10, 10), (10, 20)), 10),
        (((110, 30), (10, 10)), 101.98),
        (((100, 20), (10, 10)), 90.55),
    ],
)
def test_distance_between_points(input, expected):
    distance = Positioning._distance_between_points(input[0], input[1])
    assert round(distance, 2) == expected


@pytest.mark.parametrize(
    "input, expected",
    [
        (((10, 10), (10, 20)), 10),
        (((110, 30), (10, 10)), 120),
        (((100, 20), (10, 10)), 100),
    ],
)
def test_manhatan_distance_between_points(input, expected):
    distance = Positioning.manhattan_distance_between_points(input[0], input[1])
    assert round(distance, 2) == expected


def test_get_tokens_within_bounds(bbox_token_page):
    box = generate_mapped_pred(300, 360, 290, 450, page_num=0)
    positioning = Positioning()
    bounds = positioning.get_tokens_within_bounds(box, bbox_token_page)
    assert len(bounds) == 1
    assert "true" in bounds[0]["text"]


def test_get_tokens_within_bounds_excludes_overlap(bbox_token_page):
    box = generate_mapped_pred(300, 360, 290, 450, page_num=0)
    positioning = Positioning()
    bounds = positioning.get_tokens_within_bounds(box, bbox_token_page)
    assert "false" not in bounds[0]["text"] and "edge" not in bounds[0]["text"]


def test_get_tokens_within_bounds_includes_overlap(bbox_token_page):
    box = generate_mapped_pred(300, 360, 290, 450, page_num=0)
    positioning = Positioning()
    edges = positioning.get_tokens_within_bounds(
        box, bbox_token_page, include_overlap=True
    )
    assert len(edges) == 2
    for token in edges:
        assert "true" in token["text"] or "edge" in token["text"]


def test_get_tokens_null_bounds(bbox_token_page):
    null_box = generate_mapped_pred()
    positioning = Positioning()
    null = positioning.get_tokens_within_bounds(null_box, bbox_token_page)
    assert null == []


def test_get_tokens_within_bounds_throws_error():
    positioning = Positioning()
    with pytest.raises(RuntimeError):
        positioning.get_tokens_within_bounds(generate_mapped_pred(), [{}])
