import typing as t
from dataclasses import dataclass
from enum import Enum

PBValue: t.TypeAlias = int | str | t.Dict[int, "PBValue"] | t.List["PBValue"]
PBMessage: t.TypeAlias = t.Dict[int, "PBValue"]


PBType: t.TypeAlias = t.Type[int] | t.Type[str] | "PBMessageSchema"


@dataclass
class PBField:
    name: str
    type: PBType
    repeated: bool
    optional: bool


PBMessageSchema: t.TypeAlias = t.Dict[int, PBField]


class WireType(Enum):
    var = 0
    i64 = 1
    len = 2
    i32 = 5


class IntType(Enum):
    i32 = 0
    i64 = 1
    var = 2


class PBDecoder:
    message: bytes
    schema: PBMessageSchema

    cur_field_loc: t.List[int] = []
    cur_idx: int = 0

    def __init__(self, schema: PBMessageSchema):
        self.schema = schema

    def get_cur_field(self):
        cur_field: PBField
        if len(self.cur_field_loc) == 0:
            raise Exception("no field set")

        next = self.schema
        for i, f in enumerate(self.cur_field_loc):
            x = next.get(f)
            if x is None:
                raise Exception("unknown field index")

            cur_field = x

            if i < len(self.cur_field_loc) - 1:
                if not type(cur_field.type) == PBMessageSchema:
                    raise Exception("too many field indices")

                next = cur_field.type

        return cur_field

    def decode(self, message: bytes) -> PBMessage:
        self.message = message
        return self._parse()

    def _parse(self, bound: t.Optional[int] = None) -> PBMessage:
        cond = lambda x: (bound is None) or (x < bound)

        res: PBMessage = {}
        counter = 0
        while cond(counter):
            sub_res: PBValue

            field_no, wt = self._parse_tag()
            self.cur_field_loc.append(field_no)

            if wt == WireType.var:
                sub_res = self._parse_varint()
            elif wt == WireType.i64:
                sub_res = self._parse_i64()
            elif wt == WireType.i32:
                sub_res = self._parse_i32()
            elif wt == WireType.len:
                sub_res = self._parse_len()
            else:
                raise Exception(f"unknown wire type: {wt}")

            cur_field = self.get_cur_field()
            if cur_field.repeated:
                if field_no not in res:
                    res[field_no] = []

                res[field_no].append(sub_res)
            else:
                res[field_no] = sub_res

            self.cur_field_loc.pop()

        return res

    def _parse_tag(self) -> t.Tuple[int, WireType]:
        if self.cur_idx >= len(self.message):
            raise Exception("no tag to parse")

        b = self._parse_varint()

        wire_type = WireType(b & (0b111))
        field_no = b >> 3

        return field_no, wire_type

    def _parse_len(self) -> PBValue:
        l = self._parse_i32()

        if self.get_cur_field().type == str:
            return self._parse_str(l)

        return self._parse(l)

    def _parse_str(self, length: int) -> str:
        if self.cur_idx + length > len(self.message):
            raise Exception("unterminated string in message")

        b = self.message[self.cur_idx : self.cur_idx + length]
        self.cur_idx += length

        return b.decode()

    def _parse_i32(self) -> int:
        return self._parse_varint(IntType.i32)

    def _parse_i64(self) -> int:
        return self._parse_varint(IntType.i64)

    def _parse_varint(self, typ: IntType = IntType.var) -> int:
        cond = (
            lambda x: (typ == IntType.var)
            or (typ == IntType.i64 and x < 10)
            or (typ == IntType.i32 and x < 5)
        )

        res = []
        counter = 0
        while cond(counter):
            if self.cur_idx >= len(self.message):
                break

            b = self.message[self.cur_idx]
            val = (b << 1) >> 1
            msb = b & (1 << 7)

            res.append(val)
            self.cur_idx += 1
            counter += 1

            if msb == 0:
                break

        x = 0
        for i, val in enumerate(res):
            x += val * ((1 << 7) ** i)

        return x
