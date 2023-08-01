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

fn try_read_byte(buf: &[u8], position: usize) -> (u8, Option<usize>) {
    if position >= buf.len() {
        return (0, None);
    }

    (buf[position], Some(position + 1))
}

const VARINT_PAYLOAD_LEN: usize = 7;
const VARINT_MSB_MASK: u8 = 1 << VARINT_PAYLOAD_LEN;
const MAX_VARINT_PAYLOAD: u8 = VARINT_MSB_MASK - 1;
const VARINT_PAYLOAD_MASK: u8 = !VARINT_MSB_MASK & 0xFF;

fn parse_varint(buf: &[u8], mut position: usize) -> (u64, usize) {
    let mut res = 0;
    let mut shift = 0;

    let mut msb = VARINT_MSB_MASK;

    loop {
        let try_current_byte = try_read_byte(buf, position);
        if try_current_byte.1.is_none() {
            panic!("Unexpected end of buffer");
        }

        let current_byte = try_current_byte.0;
        position = try_current_byte.1.unwrap();

        msb = current_byte & VARINT_MSB_MASK;
        let payload = current_byte & VARINT_PAYLOAD_MASK;

        res += u64::from(payload) << shift;
        shift += VARINT_PAYLOAD_LEN;

        if res > u64::from(MAX_VARINT_PAYLOAD) << shift {
            panic!("Varint overflow");
        }

        if msb != VARINT_MSB_MASK {
            break;
        }
    }

    (res, position)
}

fn parse_wire_type_and_field_number(buf: &[u8], position: usize) -> (FieldType, u64, usize) {
    let (varint, new_position) = parse_varint(buf, position);
    let field_number = varint >> 3;
    let wire_type = varint & 0x07;

    let parsed_wire_type = match wire_type {
        0 => FieldType::VarInt,
        1 => FieldType::I64,
        2 => FieldType::Len,
        3 => FieldType::SGroup,
        4 => FieldType::EGroup,
        5 => FieldType::I32,
        _ => panic!("Unknown field type"),
    };

    (parsed_wire_type, field_number, new_position)
}

fn parse_test_data(buf: Vec<u8>) -> test_data::Datum {
    let buf = buf.as_slice();
    let mut position = 0;

    let mut res = test_data::Datum::default();
    while buf.len() > position {
        let (field_type, field_number, new_position) =
            parse_wire_type_and_field_number(buf, position);
        position = new_position;

        println!(
            "field_type: {:?}, field_number: {:?}, position: {:?}",
            field_type, field_number, position
        );

        match field_type {
            FieldType::VarInt => {
                let (value, new_position) = parse_varint(buf, position);
                position = new_position;

                res.kind = Some(test_data::datum::Kind::NumberValue(
                    value.try_into().unwrap(),
                ));
            }
            FieldType::Len => {
                let (len, new_position) = parse_varint(buf, position);
                println!("len: {:?}", len);
                position = new_position;
                let raw_string = &buf[position..position + len as usize];
                let value = match str::from_utf8(raw_string) {
                    Ok(v) => v,
                    Err(e) => panic!("Invalid UTF-8 sequence: {}", e),
                };
                position += len as usize;

                res.kind = Some(test_data::datum::Kind::StringValue(value.to_string()));
            }
            _ => panic!("Not implemented"),
        }
    }

    return res;
}

fn main() -> io::Result<()> {
    let test_data_one = get_test_data_one();
    println!("test_data_one: {:?}", test_data_one);
    let serial_test_data_one = serialize_test_data(&test_data_one);
    println!("serial_test_data_one: {:?}", serial_test_data_one);
    let deserial_test_data_one = parse_test_data(serial_test_data_one);
    println!("deserial_test_data_one: {:?}", deserial_test_data_one);

    println!();

    let test_data_two = get_test_data_two();
    println!("test_data_two: {:?}", test_data_two);
    let serial_test_data_two = serialize_test_data(&test_data_two);
    println!("serial_test_data_two: {:?}", serial_test_data_two);
    let deserial_test_data_two = parse_test_data(serial_test_data_two);
    println!("deserial_test_data_two: {:?}", deserial_test_data_two);
    Ok(())
}
