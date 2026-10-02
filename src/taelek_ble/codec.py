"""Pure codec functions for Taelek thermostat characteristics."""

from __future__ import annotations

import math
import struct

from .capabilities import DeviceCapabilities, FloorEncoding, capabilities_for_device
from .models import ParamA, ParamB, StateA


def decode_temp8(raw: int) -> float:
    if not isinstance(raw, int) or isinstance(raw, bool) or not 0 <= raw <= 0xFF:
        raise ValueError(raw)
    return round(raw * 0.5 - 50.0, 1)


def encode_temp8(celsius: float) -> int:
    if not math.isfinite(celsius):
        raise ValueError(celsius)
    raw = (celsius + 50.0) / 0.5
    rounded = round(raw)
    if abs(raw - rounded) > 1e-9:
        raise ValueError("8-bit Taelek temperatures require 0.5 °C steps")
    if not 0 <= rounded <= 0xFF:
        raise ValueError(celsius)
    return int(rounded)


def decode_calibration(raw: int) -> float:
    if not isinstance(raw, int) or isinstance(raw, bool) or not 0 <= raw <= 255:
        raise ValueError(raw)
    return (raw - 14) / 2.0


def encode_calibration(celsius: float) -> int:
    if not math.isfinite(celsius):
        raise ValueError(celsius)
    raw = celsius * 2.0 + 14
    rounded = round(raw)
    if abs(raw - rounded) > 1e-9 or not 0 <= rounded <= 0xFF:
        raise ValueError(celsius)
    return int(rounded)


def decode_state_a(
    data: bytes, *, device_type: int | None = None, capabilities: DeviceCapabilities | None = None
) -> StateA:
    if len(data) < 12:
        raise ValueError(f"productStateA too short: {len(data)}")
    capabilities = capabilities or capabilities_for_device(device_type)
    floor_raw = struct.unpack_from("<H", data, 8)[0]
    floor = None
    # Check raw sentinel before signed conversion: FFFF must not become -0.1.
    if floor_raw != 0xFFFF:
        if capabilities.floor_encoding == FloorEncoding.SIGNED:
            floor = struct.unpack_from("<h", data, 8)[0] / 10.0
        elif capabilities.floor_encoding == FloorEncoding.UNSIGNED or floor_raw < 0x8000:
            floor = floor_raw / 10.0

    def temperature(offset: int, signed: bool = False) -> float | None:
        if data[offset : offset + 2] == b"\xff\xff":
            return None
        return struct.unpack_from("<h" if signed else "<H", data, offset)[0] / 10.0

    return StateA(
        humidity=data[0],
        sensor_error=None if data[1] == 0 else data[1],
        operation_mode=data[2],
        valve_state=data[3],
        setpoint_c=temperature(4, signed=True),
        measured_air_c=temperature(6),
        measured_floor_c=floor,
        measured_external_c=temperature(10),
        raw_data=bytes(data),
    )


def decode_param_a(data: bytes) -> ParamA:
    if len(data) < 10:
        raise ValueError(f"productParamA too short: {len(data)}")
    flags = data[9]
    return ParamA(
        air_min_c=decode_temp8(data[0]),
        air_max_c=decode_temp8(data[1]),
        floor_min_c=decode_temp8(data[2]),
        floor_max_c=decode_temp8(data[3]),
        pwm_min=data[4],
        pwm_max=data[5],
        floor_calibration_c=decode_calibration(data[6]),
        air_calibration_c=decode_calibration(data[7]),
        led_brightness=data[8],
        wireless_flags=flags,
        wireless_sensor_enabled=(flags & 0x0F) == 0x04,
        wireless_eco_enabled=(flags & 0xF0) == 0x40,
    )


def patch_param_a(
    original: bytes,
    *,
    floor_min_c: float | None = None,
    floor_max_c: float | None = None,
) -> bytes:
    """Patch only requested known fields and preserve every other byte."""
    if len(original) < 10:
        raise ValueError(f"productParamA too short: {len(original)}")
    out = bytearray(original)
    if floor_min_c is not None:
        out[2] = encode_temp8(floor_min_c)
    if floor_max_c is not None:
        out[3] = encode_temp8(floor_max_c)
    if (floor_min_c is not None or floor_max_c is not None) and out[2] > out[3]:
        raise ValueError("Floor minimum exceeds maximum")
    return bytes(out)


def decode_param_b(data: bytes) -> ParamB:
    # Old model length sums to 16 bytes: 2+2+1+1+1+8+1.
    if len(data) < 16:
        raise ValueError(f"productParamB too short: {len(data)}")
    return ParamB(
        auto_eco_c=struct.unpack_from("<H", data, 0)[0] / 10.0,
        manual_eco_c=struct.unpack_from("<H", data, 2)[0] / 10.0,
        mode=data[4],
        valve_protection=data[5],
        sensor_type=data[6],
        network_key=bytes(data[7:15]),
        eco_mode=data[15],
    )


def patch_param_b(
    original: bytes,
    *,
    auto_eco_c: float | None = None,
    manual_eco_c: float | None = None,
    eco_mode: int | None = None,
) -> bytes:
    if len(original) < 16:
        raise ValueError(f"productParamB too short: {len(original)}")
    out = bytearray(original)
    if auto_eco_c is not None:
        struct.pack_into("<H", out, 0, _encode_temp16(auto_eco_c))
    if manual_eco_c is not None:
        struct.pack_into("<H", out, 2, _encode_temp16(manual_eco_c))
    if eco_mode is not None:
        if not isinstance(eco_mode, int) or isinstance(eco_mode, bool) or eco_mode not in (1, 2):
            raise ValueError(eco_mode)
        out[15] = eco_mode
    return bytes(out)


def _encode_temp16(celsius: float) -> int:
    if not math.isfinite(celsius):
        raise ValueError(celsius)
    raw = celsius * 10
    rounded = round(raw)
    if abs(raw - rounded) > 1e-9 or not 0 <= rounded <= 65535:
        raise ValueError("Unsigned temperature requires 0.1 °C steps in wire range")
    return rounded
