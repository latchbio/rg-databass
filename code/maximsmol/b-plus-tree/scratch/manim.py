from dataclasses import dataclass, field
from random import randint
from typing import Callable, ClassVar, TypeVar
from manim import Scene, Square, Rectangle, Line, VGroup, MathTex, Text, VMobject, UP, RIGHT, DOWN, DEFAULT_MOBJECT_TO_MOBJECT_BUFFER, Mobject, config, Create
from numpy import ndarray
import secrets

from internal import InternalNode, Key, KeyBase
from leaf import LeafNode, Entry
from tree import Tree

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

square_size = 1.0
small_size = 0.1
font_size = 14

varnothing = MathTex(r"\varnothing", font_size=font_size)

deferred: list[Callable[[], Mobject]] = []

def line_between(a: "VMobject | Flex", b: "VMobject | Flex", *, a_crit: ndarray, b_crit: ndarray):
    def res():
        line = Line()
        line.put_start_and_end_on(a.get_critical_point(a_crit), b.vgroup.get_critical_point(b_crit))
        return line

    return res

@dataclass
class Flex:
    gap: float = field(kw_only=True, default=DEFAULT_MOBJECT_TO_MOBJECT_BUFFER)
    children: "list[VMobject | Flex]" = field(kw_only=True, default_factory=list)

    _direction: ClassVar[ndarray] = RIGHT
    vgroup: VGroup = field(default_factory=VGroup)

    def get(self, /, i: int) -> "VMobject | Flex | None":
        if i >= len(self.children):
            return None

        return self.children[i]

    def add(self, /, obj: "VMobject | Flex") -> None:
        self.children.append(obj)

    def set(self, /, i: int, obj: "VMobject | Flex") ->  None:
        self.children[i] = obj

    def render(self) -> VGroup:
        res = self.vgroup

        prev = None
        for x in self.children:
            if isinstance(x, VMobject):
                obj = x
            else:
                obj = x.render()

            if prev is not None:
                obj.next_to(prev, direction=self._direction, buff=self.gap)
            prev = obj

            res.add(obj)

        res.center()
        return res

class Row(Flex):
    ...

class Column(Flex):
    _direction = DOWN

def r_leaf_node(node: LeafNode):
    res = Row(gap=0)

    for x in node.entries:
        cur = VGroup()
        res.add(cur)

        sq = Square(square_size)
        cur.add(sq)

        if isinstance(x, Entry):
            label = Text(f"{x.key}={repr(x.value)}", font_size=font_size)
            cur.add(label)

            label.move_to(sq)

    return res

def r_internal_node_child(child: InternalNode | LeafNode | None) -> tuple[VMobject, VMobject | Flex | None]:
    sq = Rectangle(width=small_size, height=square_size)
    if child is None:
        return sq, None

    if isinstance(child, LeafNode):
        res = r_leaf_node(child)
    else:
        res = r_internal_node(child)

    deferred.append(line_between(sq, res, a_crit=DOWN, b_crit=UP))

    return sq, res

def r_internal_node_key(key: KeyBase) -> VMobject:
    res = VGroup()

    sq = Square(square_size)
    res.add(sq)

    if isinstance(key, Key):
        label = Text(str(key.key), font_size=font_size)
        res.add(label)
        label.move_to(sq)

    return res

def r_internal_node(node: InternalNode) -> Flex:
    res = Column()

    main_row = Row(gap=0)
    res.add(main_row)

    child_row = Row()
    res.add(child_row)

    for idx, child in enumerate(node.children):
        child_sq, child_obj = r_internal_node_child(child)

        main_row.add(child_sq)

        if child_obj is not None:
            child_row.add(child_obj)

        if idx < len(node.keys):
            main_row.add(r_internal_node_key(node.keys[idx]))

    return res

def random_tree(entries: int = 20) -> Tree:
    res = Tree(3)

    for i in range(entries):
        key = randint(-100, 100)
        val = secrets.token_hex(2)

        res.insert(Entry(key, val))

    return res

class CreateCircle(Scene):
    def construct(self):
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

        # data = r_internal_node(n)

        tree = random_tree(10)
        if isinstance(tree.root, LeafNode):
            data = r_leaf_node(tree.root)
        else:
            data = r_internal_node(tree.root)

        obj = data.render()
        obj.scale_to_fit_width(config.frame_width)
        self.play(Create(obj))

        for x in deferred:
            self.play(Create(x()))
