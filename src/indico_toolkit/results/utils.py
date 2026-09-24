from collections.abc import Iterable, Iterator
from typing import Callable

from ..etloutput.utils import Value, get, has, json_loaded, str_decoded

__all__ = (
    "get",
    "has",
    "json_loaded",
    "nfilter",
    "omit",
    "str_decoded",
)


def nfilter(
    predicates: "Iterable[Callable[[Value], bool]]",
    values: "Iterable[Value]",
) -> "Iterator[Value]":
    """
    Apply multiple filter predicates to an iterable of values.

    `nfilter([first, second, third], values)` is equivalent to
    `filter(third, filter(second, filter(first, values)))`.
    """
    for predicate in predicates:
        values = filter(predicate, values)

    yield from values


def omit(dictionary: object, *keys: str) -> "dict[str, Value]":
    """
    Return a shallow copy of `dictionary` with `keys` omitted.
    """
    if not isinstance(dictionary, dict):
        return {}
    return {
        key: value
        for key, value in dictionary.items()
        if key not in keys
    }  # fmt: skip
