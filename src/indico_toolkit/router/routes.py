from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Final, Self, TypeAlias, TypeVar

from ..microclient import MicroClient

Callback: TypeAlias = Callable[..., Any]


@dataclass(frozen=True)
class Route(ABC):
    @classmethod
    @abstractmethod
    def from_signal(cls, signal: Any) -> Self: ...

    @abstractmethod
    def matches(self, other: Any) -> bool: ...

    @abstractmethod
    async def run(
        self,
        callback: Callback,
        client: MicroClient,
        signal: Any,
    ) -> None: ...


T = TypeVar("T", bound=Callback)
ROUTES: Final[list[tuple[Route, Callback]]] = []


def register(route: Route) -> Callable[[T], T]:
    def decorator(callback: T) -> T:
        ROUTES.append((route, callback))
        return callback

    return decorator


async def trigger(triggered_route: Route, client: MicroClient, signal: Any) -> None:
    for callback_route, callback in ROUTES:
        if callback_route.matches(triggered_route):
            await callback_route.run(callback, client, signal)
