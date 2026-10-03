"""Opt-in raw GATT action with an explicit response, independent of entities."""

import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import SupportsResponse
from homeassistant.exceptions import HomeAssistantError

from .const import CONF_DEBUG, DOMAIN


def register_debug_service(hass):
    def get_active(call):
        entry = hass.config_entries.async_get_entry(call.data["config_entry_id"])
        if entry is None or entry.domain != DOMAIN:
            raise HomeAssistantError("Select a Taelek config entry")
        if not entry.options.get(CONF_DEBUG, False):
            raise HomeAssistantError("Enable raw GATT debugging in Taelek options first")
        runtime = getattr(entry, "runtime_data", None)
        if entry.state != ConfigEntryState.LOADED or runtime is None or runtime.active is None:
            raise HomeAssistantError("Taelek must be loaded with GATT enabled")
        return runtime.active

    async def handle(call):
        active = get_active(call)
        try:
            options = {"sync_time": call.data.get("sync_time", True)}
            if "session_id" in call.data:
                options["session_id"] = call.data["session_id"]
            return await active.async_debug_gatt(call.data["steps"], **options)
        except ValueError as err:
            raise HomeAssistantError(f"Invalid GATT sequence: {err}") from err

    hass.services.async_register(
        DOMAIN,
        "debug_gatt",
        handle,
        schema=vol.Schema(
            {
                vol.Required("config_entry_id"): str,
                vol.Required("steps"): list,
                vol.Optional("sync_time", default=True): bool,
                vol.Optional("session_id"): str,
            }
        ),
        supports_response=SupportsResponse.ONLY,
    )

    async def control(call):
        active = get_active(call)
        try:
            return await active.async_debug_control(call.data["session_id"], call.data["operation"])
        except ValueError as err:
            raise HomeAssistantError(f"Debug control not applied: {err}") from err

    hass.services.async_register(
        DOMAIN,
        "debug_gatt_control",
        control,
        schema=vol.Schema(
            {
                vol.Required("config_entry_id"): str,
                vol.Required("session_id"): str,
                vol.Required("operation"): vol.In(["status", "continue", "abort"]),
            }
        ),
        supports_response=SupportsResponse.ONLY,
    )
