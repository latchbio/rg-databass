use core::panic;
use prost::Message;
use std::io;
use std::str;

use test::test_data;

pub mod test {
    pub mod test_data {
        include!(concat!(env!("OUT_DIR"), "/test.rs"));
    }
}

fn get_test_data_one() -> test::test_data::Datum {
    test::test_data::Datum {
        kind: Some(test::test_data::datum::Kind::NumberValue(124)),
    }
}

fn get_test_data_two() -> test::test_data::Datum {
    test::test_data::Datum {
        kind: Some(test::test_data::datum::Kind::StringValue(
            "test".to_string(),
        )),
    }
}

#[derive(Debug)]
enum FieldType {
    VarInt = 0,
    I64,
    Len,
    SGroup,
    EGroup,
    I32,
}

fn serialize_test_data(data: &test_data::Datum) -> Vec<u8> {
    let mut buf = Vec::new();
    buf.reserve(data.encoded_len());

    data.encode(&mut buf).unwrap();
    buf
}

const VARINT_PAYLOAD_LENGTH: u8 = 7;
const VARINT_MSB_MASK: u8 = 1 << VARINT_PAYLOAD_LENGTH;
const MAX_VARINT_PAYLOAD: u8 = VARINT_MSB_MASK - 1;
const VARINT_PAYLOAD_MASK: u8 = !VARINT_MSB_MASK & 0xFF;

fn try_read_byte(buf: &[u8], position: usize) -> (u8, Option<usize>) {
    if position >= buf.len() {
        return (0, None);
    }

    (buf[position], Some(position + 1))
}

fn decode_varint(buf: &[u8], position: usize) -> (u64, usize) {
    let mut res: u64 = 0;
    let mut shift = 0;

    let mut msb = VARINT_MSB_MASK;
    let mut next_position = position;
    while msb == VARINT_MSB_MASK {
        let (byte, new_position) = try_read_byte(buf, next_position);

        if new_position.is_none() {
            panic!("Unexpected end of buffer");
        }
        next_position = new_position.unwrap();

        msb = byte & VARINT_MSB_MASK;
        let payload = byte & VARINT_PAYLOAD_MASK;

        res += u64::from(payload << shift);
        shift += VARINT_PAYLOAD_LENGTH;
    }

    (res, next_position)
}

fn field_tag_parse(buf: &[u8], position: usize) -> (FieldType, usize) {
    let (varint, new_position) = decode_varint(buf, position);
    let field_number = varint >> 3;

    let enum_value = match field_number {
        0 => FieldType::VarInt,
        1 => FieldType::I64,
        2 => FieldType::Len,
        3 => FieldType::SGroup,
        4 => FieldType::EGroup,
        5 => FieldType::I32,
        _ => panic!("Unknown field type"),
    };

    (enum_value, new_position)
}

fn parse_test_data(buf: Vec<u8>) -> test_data::Datum {
    let buf = buf.as_slice();
    let mut position = 0;
    while buf.len() > position {
        let (field_type, new_position) = field_tag_parse(buf, position);
        position = new_position;

        println!("field_type: {:?}, position: {:?}", field_type, position);

        match field_type {
            FieldType::VarInt => {
                let (value, new_position) = decode_varint(buf, position);
                position = new_position;
                println!("value: {:?}", value);
            }
            FieldType::I64 => {
                let (value, new_position) = decode_varint(buf, position);
                position = new_position;
                println!("value: {:?}", value);
            }
            FieldType::I32 => {
                let (value, new_position) = decode_varint(buf, position);
                position = new_position;
                println!("value: {:?}", value);
            }
            FieldType::Len => {
                let (len, new_position) = decode_varint(buf, position);
                println!("len: {:?}", len);
                position = new_position;
                let raw_string = &buf[position..position + len as usize];
                let value = match str::from_utf8(raw_string) {
                    Ok(v) => v,
                    Err(e) => panic!("Invalid UTF-8 sequence: {}", e),
                };
                position += len as usize;
                println!("value: {:?}", value);
            }
            _ => panic!("Not implemented"),
        }
    }

    test_data::Datum::default()
}

fn main() -> io::Result<()> {
    let test_data = get_test_data_one();
    let serial_test_data = serialize_test_data(&test_data);
    println!("test_data: {:?}", test_data);
    println!("serial_test_data: {:?}", serial_test_data);
    let parsed_test_data = parse_test_data(serial_test_data);
    Ok(())
}
