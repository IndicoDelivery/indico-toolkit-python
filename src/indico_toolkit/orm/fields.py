import dataclasses
import typing
from collections.abc import Callable, Collection
from datetime import date, datetime
from functools import cache
from types import NoneType, UnionType
from typing import Any, Union

from .types import Categorical


@dataclasses.dataclass(frozen=True)
class Field:
    id: str
    multi: bool
    scalar_type: type
    scalar_parser: Any
    collection_type: type | None
    attribute: str


def validate_fields(
    orm: type,
    supported_scalar_types: Collection[type | None],
    supported_collection_types: Collection[type | None],
) -> None:
    for field in get_fields(orm):
        if not (
            field.scalar_type in supported_scalar_types
            and field.collection_type in supported_collection_types
        ):
            raise TypeError(f"{field.attribute} is not a supported type")


@cache
def get_fields(orm: type) -> tuple[Field, ...]:
    return tuple(
        map(
            _get_field,
            filter(
                lambda field: field.init,
                dataclasses.fields(orm),  # type: ignore[ty:invalid-argument-type]
            ),
        )
    )


def _get_field(field: dataclasses.Field[Any]) -> Field:
    attribute = f"attribute `{field.name}: {field.type}`"
    collection_type = typing.get_origin(field.type)
    args = typing.get_args(field.type)

    if collection_type is None:
        raise TypeError(f"{attribute} must be an optional type or a collection type")
    elif collection_type in (Union, UnionType):
        if len(args) != 2 or NoneType not in args:
            raise TypeError(f"{attribute} must be a single optional type")
    else:
        if len(args) != 1 or typing.get_origin(args[0]) is not None:
            raise TypeError(f"{attribute} must be a single collection type")

    scalar_type = next(arg for arg in args if arg is not NoneType)
    scalar_parser = SCALAR_PARSER_SERIALZER_BY_TYPE.get(scalar_type)
    multi = collection_type not in (Union, UnionType)

    return Field(
        id=field.name,
        multi=multi,
        scalar_type=scalar_type,
        scalar_parser=scalar_parser,
        collection_type=collection_type if multi else None,
        attribute=attribute,
    )


SCALAR_PARSER_SERIALZER_BY_TYPE: dict[type, Callable[[type], object]] = {  # type: ignore[ty:invalid-assignment]
    bool: bool,
    Categorical: Categorical,
    date: date.fromisoformat,
    datetime: datetime.fromisoformat,
    float: float,
    int: int,
    str: str,
}
