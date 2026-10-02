"""Common device identity and availability."""

from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


class TaelekEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, key, *, active=False):
        super().__init__(coordinator)
        self._active = active
        self._attr_unique_id = f"{entry.unique_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
            connections={(CONNECTION_BLUETOOTH, entry.data["address"])},
            name=entry.title,
            manufacturer="Taelek",
        )

    @property
    def available(self):
        if self._active:
            return self.coordinator.last_update_success and self.coordinator.data is not None
        return self.coordinator.present and self.coordinator.data is not None

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        if self._active:
            # Only enabled active entities attach listeners and trigger reads.
            await self.coordinator.async_request_refresh()
