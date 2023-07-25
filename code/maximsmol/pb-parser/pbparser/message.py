import builtins
from dataclasses import dataclass, field
import dataclasses
from enum import Enum
from collections.abc import Generator, Iterable, Sized
from typing import ClassVar, Protocol, Self, Type, Union, get_origin
import typing

from .varint import varint_bytes, varint_parse
from .common import ParserMessage, Read


class DataclassInstance(Protocol):
    __dataclass_fields__: ClassVar[dict[str, dataclasses.Field[object]]]


class FieldType(Enum):
    varint = 0
    """int32, int64, uint32, uint64, sint32, sint64, bool, enum"""
    i64 = 1
    """fixed64, sfixed64, double"""
    len = 2
    """string, bytes, embedded messages, packed repeated fields"""
    sgroup = 3
    """group start (deprecated)"""
    egroup = 4
    """group end (deprecated)"""
    i32 = 5
    """fixed32, sfixed32, float"""


@dataclass
class FieldTag:
    idx: int
    type: FieldType

    @property
    def bytes(self) -> Generator[int, None, None]:
        yield from varint_bytes((self.idx << 3) + self.type.value)


def field_tag_parse() -> Generator[ParserMessage, bytes, FieldTag]:
    data = yield from varint_parse()
    return FieldTag(data >> 3, FieldType(data & 0b111))


def raw_message_bytes(
    data: dict[int, int | bytes | list[int | bytes]]
) -> Generator[int, None, None]:
    for idx, values in data.items():
        if not isinstance(values, list):
            values = [values]

        for value in values:
            if isinstance(value, (int, bool)):
                type_ = FieldType.varint
            elif isinstance(value, (str, bytes)):
                type_ = FieldType.len
            else:
                raise NotImplementedError(f"field value not supported: {repr(value)}")

            yield from FieldTag(idx, type_).bytes
            if type_ == FieldType.varint:
                assert isinstance(value, (int, bool))

                yield from varint_bytes(value)
            elif type_ == FieldType.len:
                assert isinstance(value, (str, bytes))

                if isinstance(value, str):
                    value = value.encode()

                yield from varint_bytes(len(value))
                yield from value
            else:
                raise NotImplementedError(f"field type not supported: {repr(type_)}")


def raw_message_parse() -> (
    Generator[ParserMessage, bytes, dict[int, int | bytes | list[int | bytes]]]
):
    res: dict[int, int | bytes | list[int | bytes]] = {}
    while True:
        try:
            tag = yield from field_tag_parse()
        except EOFError:
            break

        if tag.type == FieldType.varint:
            value = yield from varint_parse()
        elif tag.type == FieldType.len:
            l = yield from varint_parse()
            value = yield Read(l)
        else:
            raise NotImplementedError(f"field type not supported: {repr(tag.type)}")

        if tag.idx in res:
            existing = res[tag.idx]
            if isinstance(existing, list):
                existing.append(value)
            else:
                res[tag.idx] = [existing, value]
        else:
            res[tag.idx] = value

    return res
