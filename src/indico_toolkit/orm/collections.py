from collections.abc import Callable, Iterable, Iterator, Mapping, MutableMapping
from contextlib import suppress
from typing import TypeVar
from weakref import ref


class _IdKeyRef(ref):
    """
    Hashable reference to unhashable types by their object ID.

    Used as a hashable key for a weak key dictionary so data can be weakly associated
    with unhashable types by object ID.
    """

    __slots__ = ("_id",)

    def __init__(
        self,
        key: object,
        callback: "Callable[[_IdKeyRef], None] | None" = None,
    ):
        super().__init__(key, callback)  # type: ignore[ty:too-many-positional-arguments]
        self._id = id(key)

    def __hash__(self) -> int:
        return self._id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _IdKeyRef):
            return NotImplemented
        elif self() is None or other() is None:
            return self is other
        else:
            return self._id == other._id


_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


class WeakIdKeyDictionary(MutableMapping[_KT, _VT]):
    """
    Mapping class that references keys weakly by their object ID.

    Entries in the dictionary are discarded when there are no longer any strong
    references to the key. This can be used to associate additional data with
    unhashable types.

    Inspired by Pytorch's mapping class of the same name.
    """

    def __init__(
        self,
        *,
        items: Mapping[_KT, _VT] | Iterable[tuple[_KT, _VT]] | None = None,
    ):
        def del_key(key, self_ref=ref(self)):
            with suppress(AttributeError, KeyError):
                del self_ref()._items[key]  # type: ignore[ty:unresolved-attribute]

        self._items = {}
        self._del_key = del_key

        if items is not None:
            self.update(items)

    def __contains__(self, key: object) -> bool:
        return _IdKeyRef(key) in self._items

    def __delitem__(self, key: _KT):
        del self._items[_IdKeyRef(key)]

    def __getitem__(self, key: _KT):
        return self._items[_IdKeyRef(key)]

    def __iter__(self) -> Iterator[_KT]:
        yield from self.keys()

    def __len__(self) -> int:
        return len(tuple(self.items()))

    def __setitem__(self, key: _KT, value: _VT) -> None:
        self._items[_IdKeyRef(key, self._del_key)] = value

    def items(self) -> Iterator[tuple[_KT, _VT]]:  # type: ignore[ty:invalid-method-override]
        for id_key_ref, value in tuple(self._items.items()):
            key = id_key_ref()
            if key is not None:
                yield key, value

    def keys(self) -> Iterator[_KT]:  # type: ignore[ty:invalid-method-override]
        for key, value in self.items():
            yield key

    def values(self) -> Iterator[_VT]:  # type: ignore[ty:invalid-method-override]
        for key, value in self.items():
            yield value
