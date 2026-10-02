"""Heating is inferred only from the documented GATT valve state."""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity

from .entity import TaelekEntity


async def async_setup_entry(hass, entry, async_add_entities):
    if entry.runtime_data.active is not None:
        async_add_entities([TaelekHeating(entry.runtime_data.active, entry)])


class TaelekHeating(TaelekEntity, BinarySensorEntity):
    _attr_name = "Heating"
    _attr_device_class = BinarySensorDeviceClass.HEAT

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "heating", active=True)

    @property
    def is_on(self):
        if self.coordinator.data is None:
            return None
        state = self.coordinator.data.valve_state
        return state == 1 if state in (0, 1, 2) else None
