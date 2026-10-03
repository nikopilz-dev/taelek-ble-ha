"""Experimental Taelek BLE integration."""

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_GATT, PLATFORMS
from .coordinator import ActiveCoordinator, AdvertisementCoordinator
from .services import register_debug_service


async def async_setup(hass: HomeAssistant, config) -> bool:
    register_debug_service(hass)
    return True


@dataclass
class RuntimeData:
    passive: AdvertisementCoordinator
    active: ActiveCoordinator | None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Discard the removed experimental app-version option from existing entries.
    if "protocol_profile" in entry.options:
        hass.config_entries.async_update_entry(
            entry,
            options={
                key: value for key, value in entry.options.items() if key != "protocol_profile"
            },
        )
    passive = AdvertisementCoordinator(hass, entry)
    active = ActiveCoordinator(hass, entry) if entry.options.get(CONF_GATT, False) else None
    entry.runtime_data = RuntimeData(passive, active)
    passive.start()
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if entry.runtime_data.active is not None:
        await entry.runtime_data.active.async_shutdown_debug()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
