"""APK-derived passive fields and optional GATT temperatures."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import EntityCategory, UnitOfTemperature

from .entity import TaelekEntity

PASSIVE = {
    "status_raw": "Advertisement status byte",
    "temperature_c": "Advertised temperature",
    "relay": "Advertisement relay code",
    "error": "Advertisement error code",
    "state": "Advertisement state code",
    "device_type": "Device type code",
}
ACTIVE = {
    "measured_floor_c": "Floor temperature",
    "measured_air_c": "Air temperature",
    "measured_external_c": "External temperature",
    "setpoint_c": "Setpoint",
    "sensor_error": "Sensor error code",
    "operation_mode": "Operation mode code",
    "eco_program_mode": "ECO program mode code",
    "buttons_raw": "Buttons raw",
    "buttons2_raw": "Buttons 2 raw",
    "device_version": "Firmware version code",
}


async def async_setup_entry(hass, entry, async_add_entities):
    runtime = entry.runtime_data
    entities = [TaelekSensor(runtime.passive, entry, key, name) for key, name in PASSIVE.items()]
    if runtime.active is not None:
        entities.extend(
            TaelekSensor(runtime.active, entry, key, name, active=True)
            for key, name in ACTIVE.items()
        )
    async_add_entities(entities)


class TaelekSensor(TaelekEntity, SensorEntity):
    def __init__(self, coordinator, entry, key, name, *, active=False):
        super().__init__(coordinator, entry, key, active=active)
        self._key = key
        self._attr_name = name
        if key.endswith("_c"):
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
            self._attr_state_class = SensorStateClass.MEASUREMENT
        if key not in (
            "temperature_c",
            "measured_floor_c",
            "measured_air_c",
            "measured_external_c",
            "setpoint_c",
        ):
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        if key in ("measured_air_c", "measured_external_c"):
            self._attr_entity_registry_enabled_default = False

    @property
    def extra_state_attributes(self):
        if self._key == "operation_mode" and self.coordinator.data is not None:
            return {
                "raw_state_a": self.coordinator.data.raw_data.hex(),
                "last_command_test": self.coordinator.last_command_test,
            }
        if self._key == "eco_program_mode":
            return {"meaning": "1 = manual program, 2 = weekly program; not active ECO state"}
        return None

    @property
    def native_value(self):
        data = self.coordinator.data
        if data is None:
            return None
        value = getattr(data, self._key)
        if (
            not self._active
            and self._key in ("temperature_c", "state", "error", "relay")
            and not data.thermostat_layout
        ):
            return None
        if self._key == "sensor_error":
            return value or 0
        # The codec handles raw sentinels before signed conversion. The range
        # filter is only an additional plausibility check, not a sentinel rule.
        if value is None:
            return None
        if self._active and self._key.endswith("_c") and not -50 <= value <= 100:
            return None
        return value
