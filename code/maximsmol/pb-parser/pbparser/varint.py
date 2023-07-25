from collections.abc import Generator
from .common import ParserMessage, Read


varint_payload_len = 7
varint_msb_mask = 1 << varint_payload_len
max_varint_payload = varint_msb_mask - 1
varint_payload_mask = ~varint_msb_mask & 0xFF


def varint_parse() -> Generator[ParserMessage, bytes, int]:
    res = 0
    shift = 0

    msb = varint_msb_mask
    while msb == varint_msb_mask:
        byte = (yield Read(1))[0]

        msb = byte & varint_msb_mask
        payload = byte & varint_payload_mask

        res += payload << shift
        shift += varint_payload_len

    return res


def varint_bytes(x: int) -> Generator[int, None, None]:
    while x > max_varint_payload:
        cur_payload = x & varint_payload_mask
        x >>= varint_payload_len

        cur = varint_msb_mask
        cur |= cur_payload
        yield cur

    yield x
