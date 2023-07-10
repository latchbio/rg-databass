from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from functools import total_ordering
from typing import Generic, Self, TypeVar

from util import shift_right
from leaf import Entry, LeafNode, LeafNodeIterator, NoEntry

K = TypeVar("K")
V = TypeVar("V")


@total_ordering
@dataclass(eq=False)
class KeyBase(Generic[K]):
    def __lt__(self, that: object) -> bool:
        if isinstance(that, NoKey):
            return not isinstance(self, NoKey)

        if not isinstance(self, Key) or not isinstance(that, Key):
            return NotImplemented

        return self.key < that.key

    def __eq__(self, that: object) -> bool:
        if isinstance(that, NoKey):
            return isinstance(self, NoKey)

        if not isinstance(self, Key) or not isinstance(that, Key):
            return NotImplemented

        return self.key == that.key


@dataclass(eq=False)
class NoKey(KeyBase):
    ...


@dataclass(eq=False)
class Key(Generic[K], KeyBase[K]):
    key: K


@dataclass(init=False)
class InternalNodeIterator(Generic[K, V]):
    def __init__(self, root: "InternalNode[K, V]"):
        self.stack: list[tuple[InternalNode, int] | LeafNodeIterator] = [(root, 0)]
        # todo(maximsmol): in cases of concurrent iteration, might be better to store last key

    def __next__(self) -> Entry[K, V]:
        while len(self.stack) > 0:
            cur = self.stack.pop()
            if isinstance(cur, LeafNodeIterator):
                try:
                    res = next(cur)
                except StopIteration:
                    continue

                self.stack.append(cur)
                return res

            node, idx = cur
            if idx >= node.fanout:
                continue

            child = node.children[idx]
            if child is None:
                continue

            self.stack.append((node, idx + 1))

            if isinstance(child, LeafNode):
                self.stack.append(iter(child))
            else:
                self.stack.append((child, 0))

        raise StopIteration

    def __iter__(self) -> Self:
        return self


@dataclass(init=False)
class InternalNode(Generic[K, V]):
    def __init__(self, fanout: int):
        if fanout < 3:
            raise ValueError(f"fanout too small: {fanout} < 3")

        self.fanout = fanout
        self.keys: list[KeyBase[K]] = [NoKey()] * (fanout - 1)
        self.children: list[LeafNode[K, V] | InternalNode[K, V] | None] = [
            None
        ] * fanout

    def __len__(self) -> int:
        res = 0

        stack: list[InternalNode[K, V]] = [self]
        while len(stack) > 0:
            cur = stack.pop()
            idx = bisect_left(cur.keys, NoKey())

            for x in cur.children[: idx + 2]:
                if x is None:
                    break

                if isinstance(x, InternalNode):
                    stack.append(x)
                else:
                    res += len(x)
        return res

    def get(self, /, key_value: K) -> V | None:
        cur: InternalNode[K, V] = self

        key = Key(key_value)
        while True:
            idx = bisect_right(cur.keys, key)
            assert idx <= len(
                cur.children
            ), f"cur.keys ({cur.keys}) is the wrong length (fanout = {cur.fanout})"

            child = cur.children[idx]
            if child is None:
                return None

            if isinstance(child, LeafNode):
                return child.get(key_value)

            cur = child

    def _split(
        self,
        /,
        spilled_key: KeyBase[K],
        spilled_node: "LeafNode[K, V] | InternalNode[K, V]",
    ) -> "tuple[InternalNode[K, V], tuple[K, InternalNode[K, V]]]":
        # todo(maximsmol): unify with leaf._split ?
        # todo(maximsmol): try a version with a temporary key array

        # three cases
        # left:  [a 5 b 10 c] +  0 x = spill a, [a' 0 x ]  5 [b  10 c ]
        # mid:   [a 5 b 10 c] +  7 x = spill b, [a  5 b']  7 [x  10 c ]
        # right: [a 5 b 10 c] + 15 x = spill c, [a  5 b ] 10 [c' 15 x ]

        # entry to the right of the median
        # ["a", "b", "c"] -> 4 // 2 = 2 ("c")
        # ["a", "b", "c", "d"] -> 5 // 2 = 2 ("c")
        median_rhs_idx = (len(self.keys) + 1) // 2
        median_lhs_idx = median_rhs_idx - 1

        median_lhs = self.keys[median_lhs_idx]
        median_rhs = self.keys[median_rhs_idx]

        if spilled_key < median_lhs:
            # case: left
            split_key = self.keys[median_lhs_idx]

            lhs_keys = self.keys[:median_lhs_idx]
            rhs_keys = self.keys[median_rhs_idx:]
        elif spilled_key < median_rhs:
            # case: mid
            split_key = spilled_key
            lhs_keys = self.keys[:median_rhs_idx]
            rhs_keys = self.keys[median_rhs_idx:]
        else:
            # case: right
            split_key = self.keys[median_rhs_idx]
            lhs_keys = self.keys[:median_rhs_idx]
            rhs_keys = self.keys[median_rhs_idx + 1 :]

        rhs_children = self.children[len(lhs_keys) + 1 :]

        assert isinstance(split_key, Key)

        for idx in range(len(lhs_keys), len(self.keys)):
            self.keys[idx] = NoKey()
            self.children[idx + 1] = None

        rhs = InternalNode(self.fanout)
        rhs.keys[: len(rhs_keys)] = rhs_keys
        rhs.children[: len(rhs_children)] = rhs_children

        if spilled_key < split_key:
            assert self._insert_child(spilled_key, spilled_node)
        elif spilled_key == split_key:
            shift_right(rhs.children, 0)
            rhs.children[0] = spilled_node
        else:
            assert rhs._insert_child(spilled_key, spilled_node)

        return self, (split_key.key, rhs)

    def _insert_child(
        self, /, key: KeyBase[K], child: "LeafNode[K, V] | InternalNode[K, V]"
    ) -> bool:
        # todo(maximsmol): explicit stack
        # todo(maximsmol): this is basically duplicated from LeafNode.insert
        idx = bisect_right(self.keys, key)

        if idx >= len(self.keys):
            return False

        existing = self.keys[idx]
        if not isinstance(existing, Key):
            self.keys[idx] = key
            self.children[idx + 1] = child
            return True

        if all(not isinstance(x, NoKey) for x in self.keys):
            return False

        shift_right(self.keys, idx)
        self.keys[idx] = key

        shift_right(self.children, idx + 1)
        self.children[idx + 1] = child

        return True

    def insert(
        self, /, x: Entry[K, V]
    ) -> "tuple[InternalNode[K, V], tuple[K, InternalNode[K, V]] | None]":
        # todo(maximsmol): explicit stack
        idx = bisect_right(self.keys, Key(x.key))
        assert idx <= len(
            self.children
        ), f"self.keys ({self.keys}) is the wrong length (fanout = {self.fanout})"

        existing = self.children[idx]
        assert existing is not None, f"{x.key} has no associated child"

        self.children[idx], split_data = existing.insert(x)
        if split_data is None:
            return self, None

        split_key_value, rhs = split_data
        split_key = Key(split_key_value)

        if not self._insert_child(split_key, rhs):
            return self._split(split_key, rhs)

        return self, None

    def delete(self, /, key_value: K) -> bool:
        stack: list[tuple[InternalNode[K, V], int]] = []

        cur = self
        key = Key(key_value)
        while True:
            idx = bisect_right(cur.keys, key)
            assert idx <= len(
                cur.children
            ), f"cur.keys ({cur.keys}) is the wrong length (fanout = {cur.fanout})"

            child = cur.children[idx]
            if child is None:
                return False

            stack.append((cur, idx))

            if isinstance(child, LeafNode):
                if not child.delete(key_value):
                    return False

                if not isinstance(child.entries[0], NoEntry):
                    return True

                break

            cur = child

        while len(stack) > 0:
            cur, idx = stack.pop()
            child = cur.children[idx]

            # todo(maximsmol): merge

        return True

    def __iter__(self) -> InternalNodeIterator[K, V]:
        return InternalNodeIterator(self)

    def __str__(self) -> str:
        items: list[str] = []
        for idx, k in enumerate(self.keys):
            child = self.children[idx]
            items.append(str(child) if child is not None else "-")
            items.append(str(k.key) if isinstance(k, Key) else ".")

        last = self.children[-1]
        items.append(str(last) if last is not None else "-")

        return f"[{' '.join(items)}]"

    def __repr__(self) -> str:
        return f"InternalNode{self}"
