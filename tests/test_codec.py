import struct

import pytest

from taelek_ble.advertisement import decode_manufacturer_payload
from taelek_ble.capabilities import AdvertisementEncoding, DeviceCapabilities
from taelek_ble.codec import (
    decode_param_b,
    decode_state_a,
    decode_temp8,
    encode_temp8,
    patch_param_a,
    patch_param_b,
)


def test_temp8_roundtrip():
    for t in (-50.0, 0.0, 5.0, 17.0, 27.5, 50.0):
        assert decode_temp8(encode_temp8(t)) == t


def test_temp8_requires_half_degree_steps():
    with pytest.raises(ValueError):
        encode_temp8(17.1)


def test_advertisement_decode():
    payload = bytearray(18)
    struct.pack_into("<h", payload, 0, 215)  # 21.5 C
    payload[2] = 0xA6  # state=10 error=1 relay=2
    payload[3] = 0x44
    struct.pack_into("<I", payload, 4, 0x12345678)
    payload[8:18] = b"Bathroom  "
    adv = decode_manufacturer_payload(
        bytes(payload),
        capabilities=DeviceCapabilities(
            advertisement_encoding=AdvertisementEncoding.LEGACY_LOW_BITS
        ),
    )
    assert adv.temperature_c == 21.5
    assert adv.state == 10
    assert adv.error == 1
    assert adv.relay == 2
    assert adv.serial == 0x12345678
    assert adv.name == "Bathroom"


def test_advertisement_unavailable_temperature():
    payload = bytearray(18)
    payload[0:2] = b"\xff\xff"
    assert decode_manufacturer_payload(bytes(payload)).temperature_c is None


def test_state_a_decode():
    data = bytearray(12)
    data[0:4] = bytes([45, 0, 0, 1])
    struct.pack_into("<h", data, 4, 230)
    struct.pack_into("<H", data, 6, 210)
    struct.pack_into("<H", data, 8, 245)
    struct.pack_into("<H", data, 10, 190)
    state = decode_state_a(bytes(data))
    assert state.humidity == 45
    assert state.sensor_error is None
    assert state.valve_state == 1
    assert state.setpoint_c == 23.0
    assert state.measured_floor_c == 24.5


def test_param_a_patch_preserves_other_bytes():
    raw = bytes(range(10))
    patched = patch_param_a(raw, floor_min_c=17.0, floor_max_c=27.0)
    assert patched[:2] == raw[:2]
    assert patched[4:] == raw[4:]
    assert patched[2] == encode_temp8(17.0)
    assert patched[3] == encode_temp8(27.0)


def test_param_b_length_and_patch_preservation():
    raw = bytes(range(16))
    parsed = decode_param_b(raw)
    assert parsed.network_key == bytes(range(7, 15))
    patched = patch_param_b(raw, manual_eco_c=12.5, eco_mode=2)
    assert patched[0:2] == raw[0:2]
    assert patched[4:15] == raw[4:15]
    assert struct.unpack_from("<H", patched, 2)[0] == 125
    assert patched[15] == 2
