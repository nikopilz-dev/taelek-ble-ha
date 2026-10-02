"""Independent wire capabilities; app releases are not device capabilities."""

from dataclasses import dataclass
from enum import StrEnum


class AdvertisementEncoding(StrEnum):
    UNRESOLVED = "unresolved"
    LEGACY_LOW_BITS = "legacy_low_bits"
    HIGH_RELAY_BIT = "high_relay_bit"


class FloorEncoding(StrEnum):
    UNRESOLVED = "unresolved"
    UNSIGNED = "unsigned"
    SIGNED = "signed"


@dataclass(frozen=True, slots=True)
class DeviceCapabilities:
    advertisement_encoding: AdvertisementEncoding = AdvertisementEncoding.UNRESOLVED
    floor_encoding: FloorEncoding = FloorEncoding.UNRESOLVED


def capabilities_for_device(device_type: int | None) -> DeviceCapabilities:
    """Resolve only independently demonstrated wire capabilities.

    F8565 applies high-bit status to all non-plug/non-3phase types, including
    BASE. F8411 selects signed floor by field name, not device generation.
    Neither establishes a hardware-type mapping for these two capabilities.
    Keep all thermostat types unresolved until a capture/version gate proves it.
    This is the single extension point for future validated type/firmware gates.
    """
    return DeviceCapabilities()
