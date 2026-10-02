"""Passive advertisement decoder."""

from __future__ import annotations

import struct

from .capabilities import AdvertisementEncoding, DeviceCapabilities, capabilities_for_device
from .models import Advertisement


def _decode_name(raw: bytes) -> str:
    chars = []
    for b in raw:
        if b == 0:
            chars.append(" ")
        elif 32 <= b <= 126:
            chars.append(chr(b))
        else:
            return ""
    return "".join(chars).strip()


def decode_manufacturer_payload(
    payload: bytes, *, capabilities: DeviceCapabilities | None = None
) -> Advertisement:
    """Decode manufacturer payload with Bluetooth company-id bytes already removed."""
    if len(payload) < 18:
        raise ValueError(f"Taelek manufacturer payload too short: {len(payload)}")
    capabilities = capabilities or capabilities_for_device(payload[3])

    if payload[0:2] == b"\xff\xff":
        temperature = None
    else:
        temperature = struct.unpack_from("<h", payload, 0)[0] / 10.0

    status = payload[2]
    state = relay = None
    if capabilities.advertisement_encoding == AdvertisementEncoding.LEGACY_LOW_BITS:
        state, relay = (status & 0xF0) >> 4, status & 0x03
    elif capabilities.advertisement_encoding == AdvertisementEncoding.HIGH_RELAY_BIT:
        state, relay = (status & 0x70) >> 4, int(bool(status & 0x80))
    return Advertisement(
        temperature_c=temperature,
        state=state,
        error=(status & 0x0C) >> 2,
        relay=relay,
        device_type=payload[3],
        serial=struct.unpack_from("<I", payload, 4)[0],
        name=_decode_name(payload[8:18]),
        status_raw=status,
    )
