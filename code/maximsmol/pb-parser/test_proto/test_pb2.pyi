from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Data(_message.Message):
    __slots__ = ["fields"]
    class FieldsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: Datum
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[Datum, _Mapping]] = ...) -> None: ...
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    fields: _containers.MessageMap[str, Datum]
    def __init__(self, fields: _Optional[_Mapping[str, Datum]] = ...) -> None: ...

class Datum(_message.Message):
    __slots__ = ["number_value", "string_value", "struct_value"]
    NUMBER_VALUE_FIELD_NUMBER: _ClassVar[int]
    STRING_VALUE_FIELD_NUMBER: _ClassVar[int]
    STRUCT_VALUE_FIELD_NUMBER: _ClassVar[int]
    number_value: int
    string_value: str
    struct_value: Data
    def __init__(self, number_value: _Optional[int] = ..., string_value: _Optional[str] = ..., struct_value: _Optional[_Union[Data, _Mapping]] = ...) -> None: ...
