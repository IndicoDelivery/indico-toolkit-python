from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Self, TypeVar

import asyncstdlib as a

from ..microclient import MicroClient
from . import annotations
from .annotations import FileNameBytes
from .routes import Callback, Route, register


class ExportFormat(StrEnum):
    JSON = "json"
    CUSTOM = "custom"


@dataclass(frozen=True)
class StartExport(Route):
    export_format: ExportFormat | None = None

    @classmethod
    def from_signal(cls, signal: Any) -> Self:
        return cls(export_format=ExportFormat(signal["format"].casefold()))

    def matches(self, other: Any) -> bool:
        return isinstance(other, type(self)) and (
            self.export_format is None
            or other.export_format is None
            or self.export_format == other.export_format
        )

    async def run(self, callback: Callback, client: MicroClient, signal: Any) -> None:
        kwargs = await a.dict(
            a.chain(
                annotations.resolve_export(callback, signal),
                annotations.resolve_microclient(callback, client),
                annotations.resolve_orm(callback, client, signal),
                annotations.resolve_submission(callback, signal),
            )
        )

        filename, filebytes = await a.sync(callback)(**kwargs)

        await client.graphql(
            """
            mutation CompleteExport($id: ID!, $file: Upload!) {
                completeExport(exportId: $id, file: $file) {
                    id
                }
            }
            """,
            variables={
                "id": signal["export_id"],
            },
            files={
                "file": (filename, filebytes),
            },
        )


T = TypeVar("T", bound=Callable[..., FileNameBytes | Awaitable[FileNameBytes]])


def on_start_export() -> Callable[[T], T]:
    return register(StartExport())


def on_start_json_export() -> Callable[[T], T]:
    return register(StartExport(export_format=ExportFormat.JSON))


def on_start_custom_export() -> Callable[[T], T]:
    return register(StartExport(export_format=ExportFormat.CUSTOM))
