from collections import defaultdict
from collections.abc import Iterable, Iterator
from typing import Any

from . import submissions, tables
from .submissions import Submission
from .tables import Table
from .types import Categorical, GraphqlIterator, OrmType

__all__ = (
    "Categorical",
    "init",
    "load",
    "save",
    "Submission",
    "Table",
)


def load(orm_class: type[OrmType], submission_id: int) -> GraphqlIterator:
    if issubclass(orm_class, Submission):
        yield from submissions.load(orm_class, submission_id)
    elif issubclass(orm_class, Table):
        yield from tables.load(orm_class, submission_id)
    else:
        raise TypeError(f"{orm_class} is not a known ORM subclass")


def init(orm_class: type[OrmType], graphql: Iterable[Any]) -> Iterator[OrmType]:
    if issubclass(orm_class, Submission):
        yield from submissions.init(orm_class, graphql)  # type: ignore[ty:invalid-yield]
    elif issubclass(orm_class, Table):
        yield from tables.init(orm_class, graphql)  # type: ignore[ty:invalid-yield]
    else:
        raise TypeError(f"{orm_class} is not a known ORM subclass")


def save(orms: Iterable[OrmType], submission_id: int) -> GraphqlIterator:
    orms_by_class = defaultdict(list)

    for orm in orms:
        orms_by_class[type(orm)].append(orm)

    for orm_class, orms in orms_by_class.items():
        if issubclass(orm_class, Submission):
            yield from submissions.save(orms, submission_id)  # type: ignore[arg-type]
        elif issubclass(orm_class, Table):
            yield from tables.save(orms, submission_id)  # type: ignore[arg-type]
        else:
            raise TypeError(f"{orm_class} is not a known ORM subclass")
