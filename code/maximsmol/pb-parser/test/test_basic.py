import base64
from typing import TypeAlias
from pbparser.message import (
    raw_message_bytes,
    raw_message_parse,
    FieldTag,
    FieldType,
    field_tag_parse,
)
from pbparser.varint import varint_parse, varint_bytes
from pbparser.common import parse
from hypothesis import given, note
import hypothesis.strategies as st

import test_proto.test_pb2 as test_pb2
from google.protobuf.json_format import ParseDict
import google.protobuf.internal.decoder as ref_dec
import google.protobuf.internal.encoder as ref_enc

# Custom strategies

st.register_type_strategy(FieldType, st.sampled_from(list(FieldType)))

# varint
int64_max = (1 << 63) - 1


@given(x=st.integers(min_value=0))
def test_varint_roundtrip(x: int):
    assert x == parse(varint_parse(), varint_bytes(x))


@given(x=st.integers(min_value=0))
def test_varint_ref_enc(x: int):
    assert bytes(varint_bytes(x)) == ref_enc._VarintBytes(x)


@given(x=st.integers(min_value=0, max_value=int64_max))
def test_varint_ref_dec(x: int):
    data = ref_enc._VarintBytes(x)
    assert parse(varint_parse(), data) == ref_dec._DecodeVarint(data, 0)[0]


# Field


@given(
    idx=st.integers(min_value=0),
    type_=...,
)
def test_field_tag_roundtrip(idx: int, type_: FieldType):
    res = parse(field_tag_parse(), FieldTag(idx, type_).bytes)

    assert res.idx == idx
    assert res.type == type_


@given(
    idx=st.integers(min_value=0),
    type_=...,
)
def test_field_tag_enc(idx: int, type_: FieldType):
    assert ref_enc.TagBytes(idx, type_.value) == bytes(FieldTag(idx, type_).bytes)


# note: ref_dec.ReadTag does not decode the tag so we cannot use it as reference

# Raw Messages


@given(
    data=st.dictionaries(
        st.integers(min_value=0),
        st.one_of(st.integers(min_value=0), st.binary()),
    )
)
def test_raw_message_roundtrip(data: dict[int, int | bytes]):
    assert data == parse(raw_message_parse(), raw_message_bytes(data))


st_field_names = st.text(st.characters(whitelist_categories=["Ll", "Lu"]))

st_struct_data = st.dictionaries(
    st_field_names,
    st.one_of(
        st.integers(min_value=0, max_value=int64_max),
        st.text(),
        st.deferred(lambda: st_struct_data),
    ),
)

StructData: TypeAlias = dict[str, "int | str | StructData"]


def encode_struct(x: StructData) -> test_pb2.Data:
    fields: dict[str, test_pb2.Datum] = {}
    for k, v in x.items():
        if isinstance(v, int):
            fields[k] = test_pb2.Datum(number_value=v)
        elif isinstance(v, str):
            fields[k] = test_pb2.Datum(string_value=v)
        elif isinstance(v, dict):
            fields[k] = test_pb2.Datum(struct_value=encode_struct(v))
        else:
            raise NotImplementedError(
                f"field {repr(k)} has unsupported value: {repr(v)}"
            )

    return test_pb2.Data(fields=fields)


@given(data=st_struct_data)
def test_raw_message_ref_enc(data: StructData):
    def serialize(x: StructData) -> bytes:
        fields: list[int | bytes] = []
        for raw_k, v in x.items():
            k = raw_k.encode()

            if isinstance(v, dict):
                struct_bytes = serialize(v)
                value_bytes = bytes(raw_message_bytes({5: struct_bytes}))
            elif isinstance(v, str):
                v = v.encode()
                value_bytes = bytes(raw_message_bytes({3: v}))
            elif isinstance(v, int):
                value_bytes = bytes(raw_message_bytes({2: v}))
            else:
                raise NotImplementedError(
                    f"field {repr(raw_k)} has unsupported value: {repr(v)}"
                )

            fields.append(bytes(raw_message_bytes({1: k, 2: value_bytes})))

        return bytes(raw_message_bytes({1: fields}))

    ours = serialize(data)
    ref = encode_struct(data).SerializeToString()

    note(f"Ours: {base64.b64encode(ours).decode()}")
    note(f"Ref: {base64.b64encode(ref).decode()}")

    decoded_ours = test_pb2.Data()
    decoded_ours.FromString(ours)

    decoded_ref = test_pb2.Data()
    decoded_ref.FromString(ref)

    # the binary directly is not comparable because protobuf does not preserve
    # field order for some reason
    assert decoded_ours == decoded_ref


@given(data=st_struct_data)
def test_raw_message_ref_dec(data: StructData):
    def deserialize(x: dict[int, int | bytes | list[int | bytes]]) -> dict[str, object]:
        if len(x) == 0:
            return {}

        fields: dict[str, object] = {}

        entries = x[1]
        if not isinstance(entries, list):
            entries = [entries]

        for entry_bytes in entries:
            assert isinstance(entry_bytes, bytes)

            entry = parse(raw_message_parse(), entry_bytes)

            key = entry[1]
            assert isinstance(key, bytes)

            key = key.decode()

            val_bytes = entry[2]
            assert isinstance(val_bytes, bytes)

            val = parse(raw_message_parse(), val_bytes)
            if 2 in val:
                decoded = val[2]
                assert isinstance(decoded, int)

                decoded = {"numberValue": decoded}
            elif 3 in val:
                decoded_bytes = val[3]
                assert isinstance(decoded_bytes, bytes)

                decoded = {"stringValue": decoded_bytes.decode()}
            elif 5 in val:
                decoded_bytes = val[5]
                assert isinstance(decoded_bytes, bytes)

                decoded_data = parse(raw_message_parse(), decoded_bytes)
                decoded = {"structValue": deserialize(decoded_data)}
            else:
                raise NotImplementedError(
                    f"field {repr(key)} has unknown datum type: {repr(val)}"
                )

            fields[key] = decoded

        return {"fields": fields}

    ref = encode_struct(data)

    binary = ref.SerializeToString()
    our_dict = deserialize(parse(raw_message_parse(), binary))
    our = ParseDict(our_dict, test_pb2.Data())

    assert our == ref
