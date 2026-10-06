import math
import struct

import pytest

from taelek_ble.advertisement import decode_manufacturer_payload
from taelek_ble.capabilities import (
    AdvertisementEncoding,
    DeviceCapabilities,
    FloorEncoding,
    capabilities_for_device,
)
from taelek_ble.codec import (
    decode_calibration,
    decode_param_a,
    decode_param_b,
    decode_state_a,
    decode_temp8,
    encode_calibration,
    encode_temp8,
    patch_param_a,
    patch_param_b,
)
from taelek_ble.discovery import device_unique_id, parse_discovery


def payload(serial=123, temperature=-123):
    return struct.pack("<hBBI10s", temperature, 0xAF, 0x77, serial, b"Room\x00     ")


def test_all_temperature_and_calibration_bytes_round_trip():
    for raw in range(256):
        assert encode_temp8(decode_temp8(raw)) == raw
        assert encode_calibration(decode_calibration(raw)) == raw


@pytest.mark.parametrize("value", [-51, 78, 17.1, math.nan, math.inf, -math.inf])
def test_invalid_temperature(value):
    with pytest.raises(ValueError):
        encode_temp8(value)


@pytest.mark.parametrize("value", [-1, 256, 1.5, True])
def test_invalid_raw_byte(value):
    for decoder in (decode_temp8, decode_calibration):
        with pytest.raises(ValueError):
            decoder(value)


@pytest.mark.parametrize(
    "decoder,length",
    [
        (decode_manufacturer_payload, 18),
        (decode_state_a, 12),
        (decode_param_a, 10),
        (decode_param_b, 16),
    ],
)
def test_all_truncated_lengths(decoder, length):
    for size in range(length):
        with pytest.raises(ValueError):
            decoder(bytes(size))


def test_negative_advertisement_and_unknown_type():
    adv = decode_manufacturer_payload(
        payload(),
        capabilities=DeviceCapabilities(
            advertisement_encoding=AdvertisementEncoding.LEGACY_LOW_BITS
        ),
    )
    assert adv.temperature_c == -12.3
    assert (adv.state, adv.error, adv.relay) == (10, 3, 3)
    assert adv.type_name == "BASE/UNKNOWN"
    assert adv.name == "Room"


def test_param_a_offsets_and_reserved_tail():
    raw = bytes([110, 170, 120, 180, 5, 90, 10, 18, 75, 0x44, 0xAB, 0xCD])
    decoded = decode_param_a(raw)
    assert (decoded.air_min_c, decoded.air_max_c, decoded.floor_min_c, decoded.floor_max_c) == (
        5,
        35,
        10,
        40,
    )
    assert (decoded.floor_calibration_c, decoded.air_calibration_c) == (-2, 2)
    assert decoded.wireless_sensor_enabled and decoded.wireless_eco_enabled
    result = patch_param_a(raw, floor_min_c=15)
    assert result[:2] == raw[:2] and result[3:] == raw[3:]
    with pytest.raises(ValueError):
        patch_param_a(raw, floor_min_c=45)


def test_param_b_preserves_network_key_and_extension():
    raw = struct.pack("<HHBBB8sB", 150, 125, 3, 1, 4, b"KEY12345", 2) + b"\xaa\xbb"
    decoded = decode_param_b(raw)
    assert (decoded.auto_eco_c, decoded.manual_eco_c, decoded.mode, decoded.sensor_type) == (
        15,
        12.5,
        3,
        4,
    )
    result = patch_param_b(raw, auto_eco_c=16.1)
    assert result[2:] == raw[2:]
    for invalid in (-1, 6553.6, 12.55, math.nan):
        with pytest.raises(ValueError):
            patch_param_b(raw, manual_eco_c=invalid)
    with pytest.raises(ValueError):
        patch_param_b(raw, eco_mode=3)


def test_discovery_and_stable_identity():
    adv = parse_discovery(None, {0x048A: payload()})
    assert adv is not None
    assert device_unique_id(adv, "AA:BB") == device_unique_id(adv, "CC:DD") == "serial_0000007b"
    assert parse_discovery("Tael-thermostat", {999: payload()}) == adv
    assert parse_discovery("Other", {999: payload()}) is None
    assert parse_discovery("Tael", {1: payload(), 2: payload()}) is None
    assert parse_discovery("Tael", {0x048A: b"short"}) is None
    assert parse_discovery("Tae1", {0x048A: bytes(18)}) is None
    for serial in (0, 0xFFFFFFFF):
        assert (
            device_unique_id(decode_manufacturer_payload(payload(serial)), "AA:BB")
            == "address_aa:bb"
        )


def test_state_preserves_unconfirmed_unsigned_sentinels():
    state = decode_state_a(struct.pack("<BBBBhHHH", 50, 3, 4, 2, -100, 65535, 240, 65534))
    assert state.setpoint_c == -10
    assert state.sensor_error == 3
    assert state.measured_air_c is None
    assert state.raw_data[6:8] == b"\xff\xff"
    assert state.measured_external_c == 6553.4


def test_observed_high_bit_status_and_signed_floor_are_distinct_from_legacy():
    legacy_caps = DeviceCapabilities(AdvertisementEncoding.LEGACY_LOW_BITS, FloorEncoding.UNSIGNED)
    signed_caps = DeviceCapabilities(AdvertisementEncoding.HIGH_RELAY_BIT, FloorEncoding.SIGNED)
    legacy = decode_manufacturer_payload(payload(), capabilities=legacy_caps)
    modern = decode_manufacturer_payload(payload(), capabilities=signed_caps)
    assert legacy.status_raw == modern.status_raw == 0xAF
    assert (legacy.state, legacy.relay) == (10, 3)
    assert (modern.state, modern.relay) == (2, 1)
    raw = struct.pack("<BBBBhHhH", 0, 0, 0, 1, 200, 210, -100, 0)
    assert decode_state_a(raw, capabilities=signed_caps).measured_floor_c == -10
    assert decode_state_a(raw, capabilities=legacy_caps).measured_floor_c == 6543.6
    assert decode_state_a(raw).measured_floor_c is None


@pytest.mark.parametrize(
    "raw_type,name",
    [
        (0x55, "ECO_PLUG"),
        (0x6A, "TSENSE_3PHASE"),
        (0x91, "MSC"),
        (0x4D, "OLED_4D"),
        (0x2E, "FLAT_ABB"),
    ],
)
def test_device_classification(raw_type, name):
    raw = bytearray(payload())
    raw[3] = raw_type
    adv = decode_manufacturer_payload(raw)
    assert adv.type_name == name
    assert adv.thermostat_layout == (name in ("OLED_4D", "FLAT_ABB"))


@pytest.mark.parametrize("raw_type", [0x00, 0x11, 0x22, 0x2B, 0x2E, 0x33, 0x3B, 0x4D, 0xEE, 0x77])
def test_app_version_does_not_prove_device_wire_capabilities(raw_type):
    raw = bytearray(payload())
    raw[3] = raw_type
    caps = capabilities_for_device(raw_type)
    assert caps.advertisement_encoding == AdvertisementEncoding.UNRESOLVED
    assert caps.floor_encoding == FloorEncoding.UNRESOLVED
    adv = decode_manufacturer_payload(raw)
    assert adv.state is None and adv.relay is None
    assert adv.status_raw == 0xAF and adv.error == 3


@pytest.mark.parametrize("encoding", list(FloorEncoding))
def test_ffff_is_never_a_valid_temperature_in_any_encoding(encoding):
    raw = bytes([0, 0, 0, 1]) + b"\xff\xff" * 4
    state = decode_state_a(raw, capabilities=DeviceCapabilities(floor_encoding=encoding))
    assert state.raw_data == raw
    assert state.setpoint_c is None
    assert state.measured_floor_c is None
    assert state.measured_air_c is None
    assert state.measured_external_c is None


@pytest.mark.parametrize("raw_floor", [0, 245, 32767, 32768, 65436, 65535])
def test_unresolved_floor_accepts_only_sign_unambiguous_non_sentinel(raw_floor):
    raw = struct.pack("<BBBBhHHH", 0, 0, 0, 1, 200, 210, raw_floor, 0)
    state = decode_state_a(raw, device_type=0x77)
    assert state.measured_floor_c == (raw_floor / 10 if raw_floor < 32768 else None)


@pytest.mark.parametrize(
    "ad_encoding", [AdvertisementEncoding.LEGACY_LOW_BITS, AdvertisementEncoding.HIGH_RELAY_BIT]
)
@pytest.mark.parametrize("floor_encoding", [FloorEncoding.UNSIGNED, FloorEncoding.SIGNED])
def test_wire_capabilities_are_independent(ad_encoding, floor_encoding):
    caps = DeviceCapabilities(ad_encoding, floor_encoding)
    advertisement = decode_manufacturer_payload(payload(), capabilities=caps)
    assert advertisement.relay == (3 if ad_encoding == AdvertisementEncoding.LEGACY_LOW_BITS else 1)
    raw = struct.pack("<BBBBhHhH", 0, 0, 0, 1, 200, 210, -100, 0)
    state = decode_state_a(raw, capabilities=caps)
    assert state.measured_floor_c == (-10 if floor_encoding == FloorEncoding.SIGNED else 6543.6)
