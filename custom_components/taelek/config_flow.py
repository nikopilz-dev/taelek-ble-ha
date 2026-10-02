"""Bluetooth discovery, manual selection and optional read-only GATT polling."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import callback

from .const import CONF_DEBUG, CONF_GATT, DOMAIN
from .taelek_ble.discovery import device_unique_id, parse_discovery


class TaelekConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_bluetooth(self, discovery_info):
        advertisement = parse_discovery(discovery_info.name, discovery_info.manufacturer_data)
        if advertisement is None or not advertisement.thermostat_layout:
            return self.async_abort(reason="not_supported")
        self._address = discovery_info.address
        self._title = advertisement.name or discovery_info.name or "Taelek BLE"
        await self.async_set_unique_id(device_unique_id(advertisement, self._address))
        self._abort_if_unique_id_configured(
            updates={CONF_ADDRESS: self._address}, reload_on_update=False
        )
        self.context["title_placeholders"] = {"name": self._title}
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title=self._title, data={CONF_ADDRESS: self._address})
        return self.async_show_form(
            step_id="confirm", description_placeholders={"name": self._title}
        )

    async def async_step_user(self, user_input=None):
        devices = {}
        for info in bluetooth.async_discovered_service_info(self.hass, connectable=False):
            adv = parse_discovery(info.name, info.manufacturer_data)
            if (
                adv
                and adv.thermostat_layout
                and device_unique_id(adv, info.address) not in self._async_current_ids()
            ):
                devices[info.address] = info
        if user_input is not None:
            info = devices.get(user_input[CONF_ADDRESS])
            if info is None:
                return self.async_abort(reason="device_not_found")
            return await self.async_step_bluetooth(info)
        if not devices:
            return self.async_abort(reason="no_devices_found")
        choices = {
            address: f"{info.name or 'Taelek BLE'} ({address})" for address, info in devices.items()
        }
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema({vol.Required(CONF_ADDRESS): vol.In(choices)})
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return TaelekOptionsFlow()


class TaelekOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_GATT: user_input[CONF_GATT],
                    CONF_DEBUG: user_input.get(CONF_DEBUG, False),
                },
            )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_GATT, default=self.config_entry.options.get(CONF_GATT, False)
                    ): bool,
                    vol.Required(
                        CONF_DEBUG, default=self.config_entry.options.get(CONF_DEBUG, False)
                    ): bool,
                }
            ),
        )
