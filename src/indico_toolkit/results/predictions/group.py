from dataclasses import dataclass, replace
from typing import Any

from ..utils import get


@dataclass(frozen=True, order=True)
class Group:
    id: int
    name: str
    index: int

    def __next__(self) -> "Group":
        """
        Return the `Group` with the next index.

        Supports `group = next(group)`.
        """
        return replace(self, index=self.index + 1)

    @staticmethod
    def from_dict(group: object) -> "Group":
        return Group(
            id=int(get(group, str, "group_id").split(":")[0]),
            name=get(group, str, "group_name"),
            index=get(group, int, "group_index"),
        )

    def to_dict(self) -> "dict[str, Any]":
        return {
            "group_id": f"{self.id}:{self.name}",
            "group_name": self.name,
            "group_index": self.index,
        }
