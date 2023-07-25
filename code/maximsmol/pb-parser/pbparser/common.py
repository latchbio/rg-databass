from collections.abc import Generator, Iterable
from dataclasses import dataclass
import itertools
from typing import TypeVar


T = TypeVar("T")


class ParserMessage:
    ...


@dataclass
class Read(ParserMessage):
    num_bytes: int


def parse(p: Generator[ParserMessage, bytes, T], xs: Iterable[int]) -> T:
    it = iter(xs)

    try:
        msg = next(p)
        while True:
            if isinstance(msg, Read):
                chunk = bytes(itertools.islice(it, msg.num_bytes))
                if len(chunk) != msg.num_bytes:
                    p.throw(EOFError())
                    continue

                msg = p.send(chunk)
    except StopIteration as res:
        return res.value
