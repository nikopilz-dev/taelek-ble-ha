"""Wire-format models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Advertisement:
    temperature_c: float | None
    state: int | None
    error: int
    relay: int | None
    device_type: int
    serial: int
    name: str
    status_raw: int = 0

    @property
    def type_name(self) -> str:
        known = {
            0x11: "RADIATOR",
            0x22: "RADIATOR22",
            0x2B: "RADIATOR_2B",
            0x2C: "RADIATOR_2C",
            0x2D: "RADIATOR_2D",
            0x2E: "FLAT_ABB",
            0x33: "RADIATOR3",
            0x3B: "RADIATOR_3B",
            0x3C: "RADIATOR_3C",
            0x4D: "OLED_4D",
            0x4E: "OLED_4E",
            0xEE: "RADIATOR_EE",
            0x55: "ECO_PLUG",
            0x6A: "TSENSE_3PHASE",
        }
        if self.device_type in known:
            return known[self.device_type]
        return {0x20: "RADIATOR2", 0x40: "OLED", 0x90: "MSC"}.get(
            self.device_type & 0xF0, "BASE/UNKNOWN"
        )

    @property
    def thermostat_layout(self) -> bool:
        """Exclude device classes whose model reuses temperature fields."""
        return self.type_name not in ("ECO_PLUG", "TSENSE_3PHASE", "MSC")


@dataclass(frozen=True, slots=True)
class StateA:
    humidity: int
    sensor_error: int | None
    operation_mode: int
    valve_state: int
    setpoint_c: float | None
    measured_air_c: float | None
    measured_floor_c: float | None
    measured_external_c: float | None
    raw_data: bytes = b""


@dataclass(frozen=True, slots=True)
class ParamA:
    air_min_c: float
    air_max_c: float
    floor_min_c: float
    floor_max_c: float
    pwm_min: int
    pwm_max: int
    floor_calibration_c: float
    air_calibration_c: float
    led_brightness: int
    wireless_flags: int
    wireless_sensor_enabled: bool
    wireless_eco_enabled: bool


@dataclass(frozen=True, slots=True)
class ParamB:
    auto_eco_c: float
    manual_eco_c: float
    mode: int
    valve_protection: int
    sensor_type: int
    network_key: bytes
    eco_mode: int
