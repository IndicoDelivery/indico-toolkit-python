from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Awaitable, Self, TypeVar

import asyncstdlib as a

from .. import orm
from ..microclient import MicroClient
from . import annotations
from .annotations import AsyncOrmIter, OrmIter
from .routes import Callback, Route, register


@dataclass(frozen=True)
class UpdateField(Route):
    field_ids: frozenset[str] = frozenset()

    @classmethod
    def from_signal(cls, signal: Any) -> Self:
        return cls(
            field_ids=frozenset(update["field_id"] for update in signal["updates"])
        )

    def matches(self, other: Any) -> bool:
        return isinstance(other, type(self)) and (
            not self.field_ids
            or not other.field_ids
            or not self.field_ids.isdisjoint(other.field_ids)
        )

    async def run(self, callback: Callback, client: MicroClient, signal: Any) -> None:
        kwargs = await a.dict(
            a.chain(
                annotations.resolve_field(callback, signal),
                annotations.resolve_microclient(callback, client),
                annotations.resolve_orm(callback, client, signal),
                annotations.resolve_submission(callback, signal),
            )
        )

        changes = await a.list((await a.sync(callback)(**kwargs)) or [])

        for query, variables in orm.save(changes, signal["submission_id"]):
            await client.graphql(query, variables)


T = TypeVar("T", bound=Callable[..., OrmIter | AsyncOrmIter | None | Awaitable[None]])


def on_update_field(*field_ids: str) -> Callable[[T], T]:
    return register(UpdateField(field_ids=frozenset(field_ids)))
