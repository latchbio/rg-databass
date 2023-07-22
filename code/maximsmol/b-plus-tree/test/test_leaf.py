from random import randint

from bplustree.leaf import LeafNode, Entry, KeyEntry, NoEntry
from hypothesis import given, note, event
import hypothesis.strategies as st
from hypothesis.stateful import (
    RuleBasedStateMachine,
    Bundle,
    rule,
    invariant,
    consumes,
    multiple,
    initialize,
)

cmp_ops = [
    lambda a, b: a == b,
    lambda a, b: a != b,
    lambda a, b: a > b,
    lambda a, b: a < b,
    lambda a, b: a >= b,
    lambda a, b: a <= b,
]
entry_cls = [lambda k: Entry(k, ""), lambda k: KeyEntry(k)]


def test_entry_order():
    for cls1 in entry_cls:
        for cls2 in entry_cls:
            assert cls1(1) < cls2(2)
            assert cls1(1) <= cls2(1)
            assert cls1(1) <= cls2(2)
            assert cls1(1) == cls2(1)
            assert cls1(1) != cls2(2)
            assert cls1(1) >= cls2(1)
            assert cls1(1) > cls2(0)

            assert not (cls1(1) > cls2(2))
            assert not (cls1(1) >= cls2(2))
            assert not (cls1(1) == cls2(2))
            assert not (cls1(1) != cls2(1))
            assert not (cls1(2) < cls2(1))
            assert not (cls1(2) <= cls2(1))

    assert Entry(0, "") < NoEntry()
    assert NoEntry() > Entry(0, "")
    assert NoEntry() == NoEntry()


@given(a=..., b=...)
def test_entry_order_pbt(a: int, b: int):
    for cls1 in entry_cls:
        for cls2 in entry_cls:
            a_entry = cls1(a)
            b_entry = cls2(b)

            assert a_entry < NoEntry()
            assert b_entry < NoEntry()
            assert NoEntry() > a_entry
            assert NoEntry() > b_entry

            assert a_entry <= NoEntry()
            assert b_entry <= NoEntry()
            assert NoEntry() >= a_entry
            assert NoEntry() >= b_entry

            assert a_entry != NoEntry()
            assert b_entry != NoEntry()
            assert NoEntry() != a_entry
            assert NoEntry() != b_entry

            for op in cmp_ops:
                assert op(a, b) == op(a_entry, b_entry)


def test_init():
    n = LeafNode(3)
    assert str(n) == "[- - -]"

def test_insert():
    n = LeafNode(3)

    assert n.get(0) is None
    assert n.get(1) is None
    assert n.get(2) is None
    assert n.get(999) is None

    n.insert(Entry(1, "b"))
    assert str(n) == "[1=b - -]"
    assert n.get(0) is None
    assert n.get(1) == "b"
    assert n.get(2) is None
    assert n.get(999) is None

    n.insert(Entry(0, "a"))
    assert str(n) == "[0=a 1=b -]"
    assert n.get(0) == "a"
    assert n.get(1) == "b"
    assert n.get(2) is None
    assert n.get(999) is None

    n.insert(Entry(2, "c"))
    assert str(n) == "[0=a 1=b 2=c]"
    assert n.get(0) == "a"
    assert n.get(1) == "b"
    assert n.get(2) == "c"
    assert n.get(999) is None


def test_iterator():
    n = LeafNode(3)
    n.insert(Entry(1, "b"))
    n.insert(Entry(3, "d"))
    n.insert(Entry(2, "c"))
    assert str(n) == "[1=b 2=c 3=d]"

    assert list(x.key for x in n) == [1, 2, 3]


def test_delete():
    n = LeafNode(3)
    n.insert(Entry(1, "b"))
    assert str(n) == "[1=b - -]"
    n.delete(1)
    assert str(n) == "[- - -]"


def test_len():
    n = LeafNode(3)
    assert len(n) == 0
    n.insert(Entry(1, "a"))
    assert len(n) == 1
    n.insert(Entry(1, "a2"))
    assert len(n) == 1
    n.insert(Entry(2, "b"))
    assert len(n) == 2
    n.insert(Entry(3, "c"))
    assert len(n) == 3
    n.delete(2)
    assert len(n) == 2
    n.delete(3)
    assert len(n) == 1
    n.delete(999)
    assert len(n) == 1
    n.delete(1)
    assert len(n) == 0


# todo(maximsmol): rewrite the split tests to follow the example from the code
def test_split_right():
    n = LeafNode(3)
    n.insert(Entry(1, "a"))
    n.insert(Entry(2, "b"))
    n.insert(Entry(3, "c"))
    assert str(n) == "[1=a 2=b 3=c]"

    a, split_data = n.insert(Entry(4, "d"))

    assert split_data is not None
    key, b = split_data

    print("lhs", a)
    print("key", key)
    print("rhs", b)

    assert key == 3
    assert str(a) == "[1=a 2=b -]"
    assert str(b) == "[3=c 4=d -]"


def test_split_left():
    n = LeafNode(3)
    n.insert(Entry(0, "a"))
    n.insert(Entry(2, "b"))
    n.insert(Entry(3, "c"))
    assert str(n) == "[0=a 2=b 3=c]"

    a, split_data = n.insert(Entry(1, "d"))

    assert split_data is not None
    key, b = split_data

    print("lhs", a)
    print("key", key)
    print("rhs", b)

    assert key == 2
    assert str(a) == "[0=a 1=d -]"
    assert str(b) == "[2=b 3=c -]"


def test_split_new_median():
    n = LeafNode(3)
    n.insert(Entry(0, "a"))
    n.insert(Entry(1, "b"))
    n.insert(Entry(3, "c"))
    assert str(n) == "[0=a 1=b 3=c]"

    a, split_data = n.insert(Entry(2, "d"))

    assert split_data is not None
    key, b = split_data

    print("lhs", a)
    print("key", key)
    print("rhs", b)

    # assert key == 2
    assert str(a) == "[0=a 1=b -]"
    assert str(b) == "[2=d 3=c -]"


def test_split_odd():
    n = LeafNode(2)
    n.insert(Entry(0, "a"))
    n.insert(Entry(2, "b"))
    assert str(n) == "[0=a 2=b]"

    a, split_data = n.insert(Entry(1, "d"))

    assert split_data is not None
    key, b = split_data

    print("lhs", a)
    print("key", key)
    print("rhs", b)

    assert key == 1
    assert str(a) == "[0=a -]"
    assert str(b) == "[1=d 2=b]"


class Stateful(RuleBasedStateMachine):
    """Test leaf nodes using an infinite list as a parent node."""

    def __init__(self):
        super().__init__()
        self.nodes: list[LeafNode[int, str]] = []
        self.latest_values: dict[int, dict[int, str]] = {}

    keys: Bundle[int] = Bundle("keys")

    @initialize(fanout=st.integers(min_value=2, max_value=10))
    def init_nodes(self, fanout: int):
        res = LeafNode(fanout)
        self.nodes = [res]
        self.latest_values[id(res)] = {}

    def _find_node_idx(self, k: int) -> int:
        k_entry = KeyEntry(k)

        idx = 0
        for cur in self.nodes[1:]:
            if k_entry < cur.entries[0]:
                note(f"_find_node_idx({k}) = {idx}")
                return idx

            idx += 1

        note(f"_find_node_idx({k}) = {idx}")
        return idx

    def _find_node(self, k: int) -> LeafNode[int, str]:
        return self.nodes[self._find_node_idx(k)]

    @rule(target=keys, k=st.integers(), v=st.text())
    def insert(self, k: int, v: str):
        node = self._find_node(k)
        latest_values = self.latest_values[id(node)]

        existing = k in latest_values

        latest_values[k] = v
        lhs, split_data = node.insert(Entry(k, v))

        if existing:
            note("Updated")
            assert split_data is None
            return multiple()

        if split_data is not None:
            key, rhs = split_data
            assert rhs.fanout == lhs.fanout
            assert key in latest_values

            event("Split")
            note(f"Split {lhs} < {key} <= {rhs}")

            idx = self._find_node_idx(key)
            self.nodes.insert(idx + 1, rhs)
            self.latest_values[id(rhs)] = {}

            rhs_latest_values = self.latest_values[id(rhs)]
            for x in rhs:
                rhs_latest_values[x.key] = latest_values[x.key]
                del latest_values[x.key]
        else:
            note(f"Inserted, giving {node}")

        return k

    @rule(k=consumes(keys))
    def delete(self, k: int):
        node_idx = self._find_node_idx(k)
        node = self.nodes[node_idx]

        latest_values = self.latest_values[id(node)]

        del latest_values[k]
        assert node.delete(k)

        if len(node) == 0 and len(self.nodes) > 1:
            note("Empty, removing")
            del self.latest_values[id(node)]
            del self.nodes[node_idx]

    @invariant()
    def no_made_up_keys(self):
        for node in self.nodes:
            latest_values = self.latest_values[id(node)]
            while True:
                cur = randint(-1000000, 1000000)
                if cur not in latest_values:
                    break

            assert node.get(cur) is None

    @invariant()
    def no_duplicate_keys(self):
        for node in self.nodes:
            seen: set[int] = set()
            for x in node.entries:
                if not isinstance(x, Entry):
                    continue

                assert x.key not in seen
                seen.add(x.key)

    @invariant()
    def inv_values_agree(self):
        for node in self.nodes:
            latest_values = self.latest_values[id(node)]
            for e in node:
                node_v = node.get(e.key)
                model_v = latest_values.get(e.key)

                assert node_v == model_v, f"value for {e.key} does not match"

            for k in self.latest_values:
                node_v = node.get(k)
                model_v = latest_values.get(k)

                assert node_v == model_v, f"value for {k} does not match"

    @invariant()
    def inv_fanout(self):
        for node in self.nodes:
            assert node.fanout == len(node.entries)

    @invariant()
    def inv_ordered(self):
        last_entry = NoEntry()
        for node in self.nodes:
            first = node.entries[0]
            if not isinstance(last_entry, NoEntry):
                assert first > last_entry

            for i in range(len(node.entries) - 1):
                l = node.entries[i]
                r = node.entries[i + 1]

                if not isinstance(r, NoEntry):
                    assert l < r
                else:
                    assert l <= r

            last_entry = next(
                (x for x in reversed(node.entries) if isinstance(x, Entry)), NoEntry()
            )

    @invariant()
    def inv_nulls_last(self):
        for node in self.nodes:
            found_null = False
            for x in node.entries:
                if isinstance(x, NoEntry):
                    found_null = True
                else:
                    assert not found_null

    @invariant()
    def len_matches(self):
        for node in self.nodes:
            latest_values = self.latest_values[id(node)]
            assert len(node) == len(latest_values)

    def teardown(self):
        note(str(self.nodes))
        note(str(self.latest_values))


TestStateful = Stateful.TestCase
