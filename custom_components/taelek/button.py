"""User-requested refresh of read-only GATT evidence."""

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory

from .entity import TaelekEntity


async def async_setup_entry(hass, entry, async_add_entities):
    if entry.runtime_data.active is not None:
        async_add_entities([TaelekRefreshButton(entry.runtime_data.active, entry)])


class TaelekRefreshButton(TaelekEntity, ButtonEntity):
    _attr_name = "Refresh GATT"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "refresh_gatt", active=True)

    @property
    def available(self):
        # A failed read must not prevent the user from trying again.
        return True

    async def async_press(self):
        await self.coordinator.async_request_refresh()
