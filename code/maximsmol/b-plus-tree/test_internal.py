from random import randint
from leaf import LeafNode, Entry, NoEntry
from internal import InternalNode, Key, NoKey

from hypothesis import given, note
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


def test_key_order():
    assert Key(1) < Key(2)
    assert Key(1) <= Key(1)
    assert Key(1) <= Key(2)
    assert Key(1) == Key(1)
    assert Key(1) != Key(2)
    assert Key(1) >= Key(1)
    assert Key(1) > Key(0)

    assert not (Key(1) > Key(2))
    assert not (Key(1) >= Key(2))
    assert not (Key(1) == Key(2))
    assert not (Key(1) != Key(1))
    assert not (Key(2) < Key(1))
    assert not (Key(2) <= Key(1))

    assert Key(0) < NoKey()
    assert NoKey() > Key(0)
    assert NoKey() == NoKey()


@given(a=..., b=...)
def test_key_order_pbt(a: int, b: int):
    a_entry = Key(a)
    b_entry = Key(b)

    assert a_entry < NoKey()
    assert b_entry < NoKey()
    assert NoKey() > a_entry
    assert NoKey() > b_entry

    assert a_entry <= NoKey()
    assert b_entry <= NoKey()
    assert NoKey() >= a_entry
    assert NoKey() >= b_entry

    assert a_entry != NoKey()
    assert b_entry != NoKey()
    assert NoKey() != a_entry
    assert NoKey() != b_entry

    for op in cmp_ops:
        assert op(a, b) == op(a_entry, b_entry)


def test_init():
    n = InternalNode(3)
    assert str(n) == "[- . - . -]"


def test_insert():
    n = InternalNode(3)
    n.keys[0] = Key(3)

    l = LeafNode(3)
    l.insert(Entry(2, "a"))

    r = LeafNode(3)
    r.insert(Entry(3, "a"))

    n.children[:2] = [l, r]
    assert str(n) == "[[2=a - -] 3 [3=a - -] . -]"
    assert n.get(0) is None
    assert n.get(1) is None
    assert n.get(2) == "a"
    assert n.get(3) == "a"
    assert n.get(4) is None
    assert n.get(999) is None

    n.insert(Entry(2, "a2"))
    assert str(n) == "[[2=a2 - -] 3 [3=a - -] . -]"
    assert n.get(0) is None
    assert n.get(1) is None
    assert n.get(2) == "a2"
    assert n.get(3) == "a"
    assert n.get(4) is None
    assert n.get(999) is None

    n.insert(Entry(1, "b"))
    assert str(n) == "[[1=b 2=a2 -] 3 [3=a - -] . -]"
    assert n.get(0) is None
    assert n.get(1) == "b"
    assert n.get(2) == "a2"
    assert n.get(3) == "a"
    assert n.get(4) is None
    assert n.get(999) is None

    n.insert(Entry(4, "c"))
    assert str(n) == "[[1=b 2=a2 -] 3 [3=a 4=c -] . -]"
    assert n.get(0) is None
    assert n.get(1) == "b"
    assert n.get(2) == "a2"
    assert n.get(3) == "a"
    assert n.get(4) == "c"
    assert n.get(999) is None

    n.insert(Entry(0, "d"))
    assert str(n) == "[[0=d 1=b 2=a2] 3 [3=a 4=c -] . -]"
    assert n.get(0) == "d"
    assert n.get(1) == "b"
    assert n.get(2) == "a2"
    assert n.get(3) == "a"
    assert n.get(4) == "c"
    assert n.get(999) is None

def test_get_wide():
    n = InternalNode(3)
    n.keys = [Key(5), Key(10)]

    a = LeafNode(3)
    a.insert(Entry(0, "a"))

    b = LeafNode(3)
    b.insert(Entry(5, "b"))

    c = LeafNode(3)
    c.insert(Entry(10, "c"))

    n.children = [a, b, c]
    assert str(n) == "[[0=a - -] 5 [5=b - -] 10 [10=c - -]]"

    assert n.get(0) == "a"
    assert n.get(5) == "b"
    assert n.get(10) == "c"
    assert n.get(999) is None

def test_delete():
    n = InternalNode(3)
    n.keys = [Key(5), Key(10)]

    a = LeafNode(3)
    a.insert(Entry(0, "a"))

    b = LeafNode(3)
    b.insert(Entry(5, "b"))

    c = LeafNode(3)
    c.insert(Entry(10, "c"))

    n.children = [a, b, c]
    assert str(n) == "[[0=a - -] 5 [5=b - -] 10 [10=c - -]]"

    assert n.get(0) == "a"

    assert n.delete(5)
    assert str(n) == "[[0=a - -] 5 [- - -] 10 [10=c - -]]"

    assert not n.delete(5)
    assert not n.delete(999)

    assert n.get(5) is None

def test_iterator():
    n = InternalNode(3)
    n.keys = [Key(5), Key(10)]

    a = LeafNode(3)
    a.insert(Entry(-3, "a"))
    a.insert(Entry(1, "a"))
    a.insert(Entry(-2, "a"))

    b = LeafNode(3)
    b.insert(Entry(7, "b"))
    b.insert(Entry(5, "b"))

    c = LeafNode(3)
    c.insert(Entry(10, "c"))

    n.children = [a, b, c]
    assert str(n) == "[[-3=a -2=a 1=a] 5 [5=b 7=b -] 10 [10=c - -]]"

    assert list(x.key for x in n) == [-3, -2, 1, 5, 7, 10]


def test_len():
    n = InternalNode(3)
    n.keys[0] = Key(5)
    n.children[:2] = [LeafNode(3), LeafNode(3)]
    assert str(n) == "[[- - -] 5 [- - -] . -]"

    assert len(n) == 0

    n.insert(Entry(1, "a"))
    assert len(n) == 1

    n.insert(Entry(1, "a2"))
    assert len(n) == 1

    n.insert(Entry(2, "a"))
    assert len(n) == 2

    n.insert(Entry(6, "a"))
    assert len(n) == 3

def test_leaf_split():
    n = InternalNode(3)
    n.keys[0] = Key(10)

    l = LeafNode(3)
    l.insert(Entry(0, "a"))
    l.insert(Entry(1, "a"))
    l.insert(Entry(5, "a"))

    r = LeafNode(3)
    r.insert(Entry(10, "a"))

    n.children[:2] = [l, r]
    assert str(n) == "[[0=a 1=a 5=a] 10 [10=a - -] . -]"

    n.insert(Entry(6, "a"))
    # pre-split: "[[0=a 1=a 5=a 6=a] 10 [10=a - -] . -]"
    assert str(n) == "[[0=a 1=a -] 5 [5=a 6=a -] 10 [10=a - -]]"


def test_internal_split_left():
    n = InternalNode(3)
    n.keys = [Key(5), Key(10)]

    a = LeafNode(3)
    a.insert(Entry(-3, "a"))
    a.insert(Entry(-2, "a"))
    a.insert(Entry(1, "a"))

    b = LeafNode(3)
    b.insert(Entry(5, "b"))

    c = LeafNode(3)
    c.insert(Entry(10, "c"))

    n.children = [a, b, c]
    assert str(n) == "[[-3=a -2=a 1=a] 5 [5=b - -] 10 [10=c - -]]"

    lhs, split_data = n.insert(Entry(0, "a"))
    # pre-leaf-split:     "[[-3=a -2=a 0=a 1=a] 5 [5=b - -] 10 [10=c - -]]"
    # pre-internal-split: "[[-3=a -2=a -] 0 [0=a 1=a -] 5 [5=b - -] 10 [10=c - -]]"

    assert split_data is not None
    key, rhs = split_data

    print("lhs", lhs)
    print("key", key)
    print("rhs", rhs)

    assert key == 5
    assert str(lhs) == "[[-3=a -2=a -] 0 [0=a 1=a -] . -]"
    assert str(rhs) == "[[5=b - -] 10 [10=c - -] . -]"


def test_internal_split_mid():
    n = InternalNode(3)
    n.keys = [Key(5), Key(10)]

    a = LeafNode(3)
    a.insert(Entry(-3, "a"))

    b = LeafNode(3)
    b.insert(Entry(5, "b"))
    b.insert(Entry(6, "b"))
    b.insert(Entry(8, "b"))

    c = LeafNode(3)
    c.insert(Entry(10, "c"))

    n.children = [a, b, c]
    assert str(n) == "[[-3=a - -] 5 [5=b 6=b 8=b] 10 [10=c - -]]"

    lhs, split_data = n.insert(Entry(7, "b"))
    # pre-leaf-split:     "[[-3=a - -] 5 [5=b 6=b 7=b 8=b] 10 [10=c - -]]"
    # pre-internal-split: "[[-3=a - -] 5 [5=b 6=b -] 7 [7=b 8=b -] 10 [10=c - -]]"

    assert split_data is not None
    key, rhs = split_data

    print("lhs", lhs)
    print("key", key)
    print("rhs", rhs)

    assert key == 7
    assert str(lhs) == "[[-3=a - -] 5 [5=b 6=b -] . -]"
    assert str(rhs) == "[[7=b 8=b -] 10 [10=c - -] . -]"


def test_internal_split_right():
    n = InternalNode(3)
    n.keys = [Key(5), Key(10)]

    a = LeafNode(3)
    a.insert(Entry(-3, "a"))

    b = LeafNode(3)
    b.insert(Entry(5, "b"))

    c = LeafNode(3)
    c.insert(Entry(10, "c"))
    c.insert(Entry(11, "c"))
    c.insert(Entry(16, "c"))

    n.children = [a, b, c]
    assert str(n) == "[[-3=a - -] 5 [5=b - -] 10 [10=c 11=c 16=c]]"

    lhs, split_data = n.insert(Entry(15, "c"))
    # pre-leaf-split:     "[[-3=a - -] 5 [5=b - -] 10 [10=c 11=c 15=c 16=c]]"
    # pre-internal-split: "[[-3=a - -] 5 [5=b - -] 10 [10=c 11=c -] 15 [15=c 16=c -]]"

    assert split_data is not None
    key, rhs = split_data

    print("lhs", lhs)
    print("key", key)
    print("rhs", rhs)

    assert key == 10
    assert str(lhs) == "[[-3=a - -] 5 [5=b - -] . -]"
    assert str(rhs) == "[[10=c 11=c -] 15 [15=c 16=c -] . -]"

# todo(maximsmol): test: works with keys that are in no internal node (need delete)

# todo(maximsmol): invariant: all elements in a child are between adjacent separator keys
# todo(maximsmol): invariant: all separator keys are in order
class Stateful(RuleBasedStateMachine):
    """Test 1-deep internal nodes using an infinite list as a parent node."""

    # todo(maximsmol): unify with test_leaf.Stateful
    def __init__(self):
        super().__init__()
        self.separator_keys: list[int] = []
        self.nodes: list[InternalNode[int, str]] = []
        self.latest_values: dict[int, dict[int, str]] = {}

    keys: Bundle[int] = Bundle("keys")

    @initialize(fanout=st.integers(min_value=3, max_value=10), initial_key=st.integers())
    def init_nodes(self, fanout: int, initial_key: int):
        res = InternalNode(fanout)
        res.keys[0] = Key(initial_key)
        res.children[:2] = [LeafNode(fanout), LeafNode(fanout)]

        self.nodes = [res]
        self.latest_values[id(res)] = {}

    def _find_node_idx(self, k: int) -> int:
        idx = 0
        for cur in self.separator_keys:
            if k < cur:
                note(f"_find_node_idx({k}) = {idx}")
                return idx

            idx += 1

        note(f"_find_node_idx({k}) = {idx}")
        return idx

    def _find_node(self, k: int) -> InternalNode[int, str]:
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

            note(f"Split {lhs} < {key} <= {rhs}")

            idx = self._find_node_idx(key)
            self.separator_keys.insert(idx, key)
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

            if node_idx > 0:
                del self.separator_keys[node_idx-1]
            else:
                del self.separator_keys[0]

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
            seen_leaf: set[int] = set()
            for x in node.keys:
                if not isinstance(x, Key):
                    continue

                assert x.key not in seen
                seen.add(x.key)

            for x in node.children:
                if x is None:
                    continue

                assert isinstance(x, LeafNode), "not 1-deep"

                for e in x.entries:
                    if not isinstance(e, Entry):
                        continue

                    assert e.key not in seen_leaf
                    seen_leaf.add(e.key)

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
            assert node.fanout == len(node.keys) + 1
            assert node.fanout == len(node.children)

    @invariant()
    def inv_ordered(self):
        last_entry = NoEntry()
        for node in self.nodes:
            for child in node.children:
                if child is None:
                    continue

                assert isinstance(child, LeafNode), "not 1-deep"

                first = child.entries[0]
                if not isinstance(last_entry, NoEntry):
                    assert first > last_entry

                for i in range(len(child.entries) - 1):
                    l = child.entries[i]
                    r = child.entries[i + 1]

                    if not isinstance(r, NoEntry):
                        assert l < r
                    else:
                        assert l <= r

                last_entry = next(
                    (x for x in reversed(child.entries) if isinstance(x, Entry)),
                    NoEntry(),
                )

    @invariant()
    def inv_nulls_last(self):
        for node in self.nodes:
            found_null = False
            for k in node.keys:
                if isinstance(k, NoKey):
                    found_null = True
                else:
                    assert not found_null

            found_null = False
            for x in node.children:
                if x is None:
                    found_null = True
                else:
                    assert not found_null

            for child in node.children:
                if child is None:
                    continue

                assert isinstance(child, LeafNode), "not 1-deep"

                found_null = False
                for x in child.entries:
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
        note(str(self.separator_keys))
        note(str(self.nodes))
        note(str(self.latest_values))

TestStateful = Stateful.TestCase
