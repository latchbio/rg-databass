from dataclasses import dataclass
from typing import Generic, Iterator, TypeVar

from .internal import InternalNode, Key
from .leaf import LeafNode, Entry

K = TypeVar("K")
V = TypeVar("V")


@dataclass(init=False)
class Tree(Generic[K, V]):
    def __init__(self, fanout: int):
        if fanout < 3:
            raise ValueError(f"fanout too small: {fanout} < 3")

        self.fanout = fanout
        self.root: InternalNode[K, V] | LeafNode[K, V] = LeafNode(fanout)

    def insert(self, /, x: Entry[K, V]) -> None:
        lhs, split_data = self.root.insert(x)
        if split_data is None:
            return

        key, rhs = split_data

        self.root = InternalNode(self.fanout)
        self.root.keys[0] = Key(key)
        self.root.children[:2] = [lhs, rhs]

    def delete(self, /, k: K) -> bool:
        # todo(maximsmol): merge
        return self.root.delete(k)

    def __iter__(self) -> Iterator[Entry[K, V]]:
        return iter(self.root)

    def __str__(self) -> str:
        return str(self.root)

    def __repr__(self) -> str:
        return f"Tree{self}"
