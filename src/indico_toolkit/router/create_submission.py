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
class CreateSubmission(Route):
    @classmethod
    def from_signal(cls, signal: Any) -> Self:
        return cls()

    def matches(self, other: Any) -> bool:
        return isinstance(other, type(self))

    async def run(self, callback: Callback, client: MicroClient, signal: Any) -> None:
        kwargs = await a.dict(
            a.chain(
                annotations.resolve_microclient(callback, client),
                annotations.resolve_orm(callback, client, signal),
                annotations.resolve_submission(callback, signal),
            )
        )

        changes = await a.list((await a.sync(callback)(**kwargs)) or [])

        for query, variables in orm.save(changes, signal["submission_id"]):
            await client.graphql(query, variables)


T = TypeVar("T", bound=Callable[..., OrmIter | AsyncOrmIter | None | Awaitable[None]])


def on_create_submission() -> Callable[[T], T]:
    return register(CreateSubmission())
