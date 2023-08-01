from bisect import bisect_left
from dataclasses import dataclass
from functools import total_ordering
from typing import Generic, Self, TypeVar

from .util import shift_left, shift_right

K = TypeVar("K")
V = TypeVar("V")


@total_ordering
@dataclass(eq=False)
class EntryBase(Generic[K, V]):
    def __lt__(self, that: object) -> bool:
        if isinstance(that, NoEntry):
            return not isinstance(self, NoEntry)

        if not isinstance(self, (Entry, KeyEntry)) or not isinstance(
            that, (Entry, KeyEntry)
        ):
            return NotImplemented

        return self.key < that.key

    def __eq__(self, that: object) -> bool:
        if isinstance(that, NoEntry):
            return isinstance(self, NoEntry)

        if not isinstance(self, (Entry, KeyEntry)) or not isinstance(
            that, (Entry, KeyEntry)
        ):
            return NotImplemented

        return self.key == that.key


@dataclass(eq=False)
class KeyEntry(Generic[K], EntryBase[K, object]):
    key: K


@dataclass(eq=False)
class NoEntry(EntryBase):
    ...


@dataclass(eq=False)
class Entry(Generic[K, V], EntryBase[K, V]):
    key: K
    value: V


@dataclass
class LeafNodeIterator(Generic[K, V]):
    node: "LeafNode[K, V]"
    idx: int = 0
    # todo(maximsmol): in cases of concurrent iteration, might be better to store last key

    def __next__(self) -> Entry[K, V]:
        xs = self.node.entries
        if self.idx >= len(xs):
            raise StopIteration

        res = xs[self.idx]
        if not isinstance(res, Entry):
            raise StopIteration

        self.idx += 1
        return res

    def __iter__(self) -> Self:
        return self


@dataclass(init=False)
class LeafNode(Generic[K, V]):
    def __init__(self, fanout: int):
        if fanout < 2:
            raise ValueError(f"fanout too small: {fanout} < 2")

        self.fanout = fanout
        self.entries: list[EntryBase[K, V]] = [NoEntry()] * fanout

    def __len__(self) -> int:
        return bisect_left(self.entries, NoEntry())

    def get(self, /, key: K) -> V | None:
        idx = bisect_left(self.entries, KeyEntry(key))

        if idx >= len(self.entries):
            return None

        existing = self.entries[idx]
        if not isinstance(existing, Entry):
            return None

        if existing.key != key:
            return None

        return existing.value

    def _split(
        self, /, spilled: Entry[K, V]
    ) -> "tuple[LeafNode[K, V], tuple[K, LeafNode[K, V]]]":
        # three cases:
        # left:  [1, 2, 5] + 0 = [0, 1, -] [2, 5, -]
        # mid:   [1, 2, 5] + 4 = [1, 2, -] [4, 5, -]
        # right: [1, 2, 5] + 6 = [1, 2, -] [5, 6, -]

        # entry to the right of the median
        # ["a", "b", "c"] -> 4 // 2 = 2 ("c")
        # ["a", "b", "c", "d"] -> 5 // 2 = 2 ("c")
        median_rhs_idx = (len(self.entries) + 1) // 2
        median_lhs_idx = median_rhs_idx - 1

        median_lhs = self.entries[median_lhs_idx]
        median_rhs = self.entries[median_rhs_idx]

        if spilled < median_lhs:
            # case: left
            lhs_entires = self.entries[:median_lhs_idx]
            rhs_entries = self.entries[median_lhs_idx:]

            split_key = rhs_entries[0]
        elif spilled < median_rhs:
            # case: mid
            lhs_entires = self.entries[:median_rhs_idx]
            rhs_entries = self.entries[median_rhs_idx:]

            split_key = spilled
        else:
            # case: right
            lhs_entires = self.entries[:median_rhs_idx]
            rhs_entries = self.entries[median_rhs_idx:]

            split_key = rhs_entries[0]

        assert isinstance(split_key, Entry)

        for idx in range(len(lhs_entires), len(self.entries)):
            self.entries[idx] = NoEntry()

        rhs = LeafNode(self.fanout)
        rhs.entries[: len(rhs_entries)] = rhs_entries

        if spilled < split_key:
            self.insert(spilled)
        elif spilled == split_key:
            shift_right(rhs.entries, 0)
            rhs.entries[0] = spilled
        else:
            rhs.insert(spilled)

        return self, (split_key.key, rhs)

    def insert(
        self, /, x: Entry[K, V]
    ) -> "tuple[LeafNode[K, V], tuple[K, LeafNode[K, V]] | None]":
        idx = bisect_left(self.entries, x)

        if idx >= len(self.entries):
            return self._split(x)

        existing = self.entries[idx]
        if not isinstance(existing, Entry):
            self.entries[idx] = x
            return self, None

        if existing.key == x.key:
            self.entries[idx] = x
            return self, None

        if all(not isinstance(x, NoEntry) for x in self.entries):
            return self._split(x)

        shift_right(self.entries, idx)
        self.entries[idx] = x

        return self, None

    def delete(self, /, key: K) -> bool:
        idx = bisect_left(self.entries, KeyEntry(key))

        existing = self.entries[idx]
        if not isinstance(existing, Entry):
            return False

        if existing.key != key:
            return False

        shift_left(self.entries, idx)
        self.entries[-1] = NoEntry()

        return True

    def __iter__(self) -> LeafNodeIterator[K, V]:
        return LeafNodeIterator(self)

    def __str__(self) -> str:
        items = " ".join(
            (f"{x.key}={x.value}" if isinstance(x, Entry) else "-")
            for x in self.entries
        )
        return f"[{items}]"

    def __repr__(self) -> str:
        return f"LeafNode{self}"
