"""Keep passive availability independent of optional active read failures."""

import asyncio
import logging
from contextlib import suppress
from copy import deepcopy
from dataclasses import replace
from datetime import timedelta
from time import monotonic
from uuid import UUID

from bleak.exc import BleakError
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection
from homeassistant.components import bluetooth
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .taelek_ble.client import TaelekClient
from .taelek_ble.debug import validate_steps
from .taelek_ble.discovery import device_unique_id, parse_discovery

_LOGGER = logging.getLogger(__name__)
VERIFIED_ADVERTISEMENT_MAX_AGE = 90


class AdvertisementCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(hass, _LOGGER, name=f"{DOMAIN} advertisements", config_entry=entry)
        self.entry = entry
        self.address = entry.data[CONF_ADDRESS]
        self.present = False
        self.last_verified_at = None

    def start(self):
        self.entry.async_on_unload(
            bluetooth.async_register_callback(
                self.hass,
                self._receive,
                {"address": self.address, "connectable": False},
                bluetooth.BluetoothScanningMode.PASSIVE,
            )
        )
        self.entry.async_on_unload(
            bluetooth.async_track_unavailable(
                self.hass,
                self._unavailable,
                self.address,
                connectable=False,
            )
        )
        info = bluetooth.async_last_service_info(self.hass, self.address, connectable=False)
        if info is not None and bluetooth.async_address_present(
            self.hass, self.address, connectable=False
        ):
            self._receive(info, None)
            # HA's cached startup record is not evidence of a fresh reception.
            self.last_verified_at = None

    @callback
    def _receive(self, info, change):
        advertisement = parse_discovery(info.name, info.manufacturer_data)
        if advertisement is None or not advertisement.thermostat_layout:
            return
        # Do not attribute a reused Bluetooth address to a different serial.
        if (
            self.entry.unique_id.startswith("serial_")
            and device_unique_id(advertisement, info.address) != self.entry.unique_id
        ):
            self.last_verified_at = None
            return
        self.present = True
        self.last_verified_at = monotonic()
        self.async_set_updated_data(advertisement)

    @callback
    def _unavailable(self, info):
        self.present = False
        self.last_verified_at = None
        self.async_update_listeners()


class ActiveCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, *, passive=None):
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} GATT",
            config_entry=entry,
            update_interval=timedelta(minutes=5),
        )
        self.address = entry.data[CONF_ADDRESS]
        self.unique_id = entry.unique_id
        self.passive = passive
        self.client = TaelekClient(self._connect, clock=dt_util.now)
        self.last_command_test = None
        self._experiment_lock = asyncio.Lock()
        self._debug_session = None
        self._last_debug_session = None
        self._debug_ids = set()
        self._debug_gate = None
        self._debug_task = None

    def _check_debug_idle(self):
        if self._debug_session is not None:
            raise ValueError("A held debug session is active; use its control action")

    async def async_debug_gatt(self, steps, *, sync_time=True, session_id=None):
        # Validate all steps and identity before connecting or writing the clock.
        validated = validate_steps(steps)
        held = any(s["operation"] == "wait_for_continue" for s in validated)
        if held:
            try:
                session_id = str(UUID(session_id))
            except (ValueError, TypeError, AttributeError) as err:
                raise ValueError("A UUID session_id is required for a confirmation wait") from err
        elif session_id is not None:
            raise ValueError("session_id is only used with wait_for_continue")
        self._check_debug_idle()
        async with self._experiment_lock:
            self._check_debug_idle()
            self._get_advertisement()
            if not held:
                return await self.client.debug_gatt(steps, sync_time=sync_time)
            if session_id in self._debug_ids:
                raise ValueError("Use a fresh session_id; an old identity cannot be reused")
            self._debug_ids.add(session_id)
            session = {"session_id": session_id, "phase": "running", "result": None}
            self._debug_session = session
            self._debug_task = asyncio.current_task()
            self._debug_gate = None

            async def pause(result):
                session.update(phase="waiting", result=result)
                self._debug_gate = asyncio.get_running_loop().create_future()
                try:
                    await self._debug_gate
                finally:
                    self._debug_gate = None

            try:
                result = await self.client.debug_gatt(steps, sync_time=sync_time, pause=pause)
                session.update(phase="finished", result=result)
                return {**result, "session_id": session_id}
            except asyncio.CancelledError:
                result = session["result"] or {}
                result.update(
                    success=False,
                    error_type="CancelledError",
                    retry="none",
                    error="Session cancelled; prior write effects may be unknown",
                )
                session.update(phase="cancelled", result=result)
                raise
            finally:
                self._last_debug_session = session
                self._debug_session = None
                self._debug_task = None

    async def async_debug_control(self, session_id, operation):
        try:
            session_id = str(UUID(session_id))
        except (ValueError, TypeError, AttributeError) as err:
            raise ValueError("session_id must be a UUID") from err
        session = self._debug_session or self._last_debug_session
        if session is None or session["session_id"] != session_id:
            raise ValueError("No matching debug session")
        if operation == "status":
            return deepcopy(session)
        if operation not in ("continue", "abort"):
            raise ValueError("Control operation must be status, continue or abort")
        gate = self._debug_gate
        if session["phase"] != "waiting" or gate is None or gate.done():
            raise ValueError("Session is not waiting; control was not applied")
        session["phase"] = "resuming" if operation == "continue" else "aborting"
        if operation == "continue":
            gate.set_result(None)
        else:
            gate.set_exception(ValueError("Experiment aborted by operator; not retried"))
        return {
            "session_id": session_id,
            "phase": session["phase"],
            "note": "Control accepted; consult status for GATT completion",
        }

    async def async_shutdown_debug(self):
        if self._debug_session is not None:
            task = self._debug_task
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    async def async_test_eco_temperature(self, target):
        self._check_debug_idle()
        async with self._experiment_lock:
            self._check_debug_idle()
            self.last_command_test = {"experiment": "manual ECO target", "result": "pending"}
            try:
                ad = self._get_advertisement()
                before_c, after_c, before, after = await self.client.test_manual_eco_temperature(
                    target, device_type=ad.device_type
                )
            except (BleakError, OSError, TimeoutError, ValueError, UpdateFailed) as err:
                self.last_command_test.update(
                    result="failed; effect may be unknown; not retried",
                    original_eco_c=self.client.original_manual_eco_c,
                )
                self.async_update_listeners()
                raise HomeAssistantError(f"Taelek temperature experiment failed: {err}") from err
            self.last_command_test.update(
                result="target read back; ECO activation unverified"
                if after_c == (target if target is not None else self.client.original_manual_eco_c)
                else "target did not match requested value",
                before_eco_c=before_c,
                after_eco_c=after_c,
                original_eco_c=self.client.original_manual_eco_c,
                before_state_a=before.raw_data.hex(),
                after_state_a=after.raw_data.hex(),
            )
            self.async_set_updated_data(after)

    async def async_test_runtime_command(self, command):
        self._check_debug_idle()
        async with self._experiment_lock:
            self._check_debug_idle()
            await self._test_runtime_command(command)

    async def _test_runtime_command(self, command):
        """Explicit diagnostic experiment; periodic updates never call this."""
        self.last_command_test = {"command": f"0x{command:02x}", "result": "pending"}
        try:
            advertisement = self._get_advertisement()
            before, after = await self.client.test_runtime_command(
                command, device_type=advertisement.device_type
            )
        except (BleakError, OSError, TimeoutError, ValueError, UpdateFailed) as err:
            self.last_command_test["result"] = "failed; effect may be unknown; not retried"
            self.async_update_listeners()
            raise HomeAssistantError(f"Taelek command test failed: {err}") from err
        self.last_command_test.update(
            result="write acknowledged; ECO effect unverified",
            before_state_a=before.raw_data.hex(),
            after_state_a=after.raw_data.hex(),
        )
        if self.data is not None:
            after = replace(
                after,
                eco_program_mode=self.data.eco_program_mode,
                device_version=self.data.device_version,
                buttons_raw=self.data.buttons_raw,
                buttons2_raw=self.data.buttons2_raw,
            )
        self.async_set_updated_data(after)

    def _get_advertisement(self):
        info = bluetooth.async_last_service_info(self.hass, self.address, connectable=False)
        if info is not None and info.name == "Tae1":
            passive = self.passive
            if (
                passive is None
                or not passive.present
                or passive.last_verified_at is None
                or not 0 <= monotonic() - passive.last_verified_at <= VERIFIED_ADVERTISEMENT_MAX_AGE
                or not bluetooth.async_address_present(self.hass, self.address, connectable=False)
            ):
                raise UpdateFailed("No recent verified thermostat advertisement alongside Tae1")
            advertisement = passive.data
        else:
            advertisement = parse_discovery(info.name, info.manufacturer_data) if info else None
        if advertisement is None or not advertisement.thermostat_layout:
            raise UpdateFailed("No supported thermostat advertisement available for GATT reads")
        if (
            self.unique_id.startswith("serial_")
            and device_unique_id(advertisement, self.address) != self.unique_id
        ):
            raise UpdateFailed("Advertisement serial does not match the configured device")
        return advertisement

    async def _connect(self):
        self._get_advertisement()
        device = bluetooth.async_ble_device_from_address(self.hass, self.address, connectable=True)
        if device is None:
            raise UpdateFailed("No connectable Bluetooth adapter or proxy can reach the device")
        return await establish_connection(
            BleakClientWithServiceCache, device, device.name or self.address, timeout=15
        )

    async def _async_update_data(self):
        if self._debug_session is not None:
            raise UpdateFailed("Active polling paused during held debug session")
        try:
            advertisement = self._get_advertisement()
            return await self.client.read_state_with_details(device_type=advertisement.device_type)
        except (BleakError, OSError, TimeoutError, ValueError) as err:
            raise UpdateFailed(f"Taelek state read failed: {err}") from err
