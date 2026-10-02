"""Read refresh and disabled-by-default explicit command experiments."""

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory

from .entity import TaelekEntity
from .taelek_ble.const import COMMAND_NORMAL


async def async_setup_entry(hass, entry, async_add_entities):
    if entry.runtime_data.active is not None:
        active = entry.runtime_data.active
        async_add_entities(
            [
                TaelekRefreshButton(active, entry),
                TaelekCommandTestButton(active, entry, COMMAND_NORMAL, "Test NORMAL command"),
            ]
        )


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


class TaelekCommandTestButton(TaelekEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator, entry, command, name):
        super().__init__(coordinator, entry, f"test_command_{command:02x}", active=True)
        self._command = command
        self._attr_name = name

    async def async_press(self):
        await self.coordinator.async_test_runtime_command(self._command)
