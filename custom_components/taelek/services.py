"""Opt-in raw GATT action with an explicit response, independent of entities."""

import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import SupportsResponse
from homeassistant.exceptions import HomeAssistantError

from .const import CONF_DEBUG, DOMAIN


def register_debug_service(hass):
    async def handle(call):
        entry = hass.config_entries.async_get_entry(call.data["config_entry_id"])
        if entry is None or entry.domain != DOMAIN:
            raise HomeAssistantError("Select a Taelek config entry")
        if not entry.options.get(CONF_DEBUG, False):
            raise HomeAssistantError("Enable raw GATT debugging in Taelek options first")
        runtime = getattr(entry, "runtime_data", None)
        if entry.state != ConfigEntryState.LOADED or runtime is None or runtime.active is None:
            raise HomeAssistantError("Taelek must be loaded with GATT enabled")
        try:
            return await runtime.active.async_debug_gatt(call.data["steps"])
        except ValueError as err:
            raise HomeAssistantError(f"Invalid GATT sequence: {err}") from err

    hass.services.async_register(
        DOMAIN,
        "debug_gatt",
        handle,
        schema=vol.Schema({vol.Required("config_entry_id"): str, vol.Required("steps"): list}),
        supports_response=SupportsResponse.ONLY,
    )
