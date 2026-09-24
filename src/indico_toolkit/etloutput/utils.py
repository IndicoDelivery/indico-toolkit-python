import json
from typing import Any, TypeVar

Value = TypeVar("Value")


def get(value: object, value_type: "type[Value]", *keys: "str | int") -> Value:
    """
    Return the value of type `value_type` obtained by traversing `value` using `keys`.
    Raise an error if a key doesn't exist or the value has the wrong type.
    """
    for key in keys:
        if isinstance(value, dict):
            if key in value:
                value = value[key]
            else:
                raise KeyError(f"{key!r} not in {value.keys()!r}")
        elif isinstance(value, list):
            if isinstance(key, int):
                if 0 <= key < len(value):
                    value = value[key]
                else:
                    raise IndexError(f"{key} out of range [0,{len(value)})")
            else:
                raise TypeError(f"list can't be indexed with {key!r}")
        else:
            raise TypeError(f"{type(value)} can't be traversed")

    if isinstance(value, value_type):
        return value
    else:
        raise TypeError(f"value `{value!r}` doesn't have type {value_type}")


def has(value: object, value_type: "type[Value]", *keys: "str | int") -> bool:
    """
    Check if `value` can be traversed using `keys` to a value of type `value_type`.
    """
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        elif isinstance(value, list) and isinstance(key, int) and 0 <= key < len(value):  # fmt: skip  # noqa: E501
            value = value[key]
        else:
            return False

    return isinstance(value, value_type)


def json_loaded(value: "Any") -> "Any":
    """
    Ensure `value` has been loaded as JSON.
    """
    value = str_decoded(value)

    if isinstance(value, str):
        value = json.loads(value)

    return value


def str_decoded(value: str | bytes) -> str:
    """
    Ensure `value` has been decoded to a string.
    """
    if isinstance(value, bytes):
        value = value.decode()

    return value
