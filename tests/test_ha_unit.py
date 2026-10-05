"""Integration logic tests with HA boundaries stubbed for Windows.

These test our callbacks/flows/entities, not the real HA event loop or loader.
The separate tests_ha suite must run on supported Linux/Python with real HA.
"""

import asyncio
import importlib
import struct
import sys
from datetime import UTC, datetime, timedelta, timezone
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest


async def test_held_debug_service_preserves_connection_and_gates_all_following_writes(ha):
    from uuid import uuid4

    from custom_components.taelek.taelek_ble.const import PRODUCT_COMMANDS, PRODUCT_PARAM_B, TIME

    ha.bluetooth.async_last_service_info.return_value = ha.info
    ha.bluetooth.async_ble_device_from_address.return_value = SimpleNamespace(name="Tael")
    transport = AsyncMock()
    transport.read_gatt_char.return_value = bytes(range(16))
    ha.coordinator.establish_connection.return_value = transport
    active = ha.coordinator.ActiveCoordinator(ha.hass, ha.entry)
    ha.entry.domain, ha.entry.state = "taelek", "loaded"
    ha.entry.options["enable_debug_gatt"] = True
    ha.entry.runtime_data = SimpleNamespace(active=active)
    ha.hass.config_entries.async_get_entry = Mock(return_value=ha.entry)
    ha.hass.services = SimpleNamespace(async_register=Mock())
    await ha.integration.async_setup(ha.hass, {})
    registrations = {c.args[1]: c for c in ha.hass.services.async_register.call_args_list}

    async def call(name, data):
        reg = registrations[name]
        return await reg.args[2](SimpleNamespace(data=reg.kwargs["schema"](data)))

    sid = str(uuid4())
    data = {
        "config_entry_id": "test",
        "session_id": sid,
        "steps": [
            {"operation": "patch", "uuid": PRODUCT_PARAM_B, "offset": 2, "hex": "6400"},
            {"operation": "wait_for_continue", "timeout": 1},
            {"operation": "write", "uuid": PRODUCT_COMMANDS, "hex": "83"},
        ],
    }
    task = asyncio.create_task(call("debug_gatt", data))
    await asyncio.sleep(0)
    control = {"config_entry_id": "test", "session_id": sid, "operation": "status"}
    snapshot = await call("debug_gatt_control", control)
    assert snapshot["phase"] == "waiting"
    assert snapshot["result"]["steps"][0]["original_hex"] == bytes(range(16)).hex()
    assert [c.args[0] for c in transport.write_gatt_char.await_args_list] == [TIME, PRODUCT_PARAM_B]
    transport.disconnect.assert_not_called()
    with pytest.raises(ValueError, match="held debug"):
        await active.async_debug_gatt([{"operation": "read", "uuid": PRODUCT_PARAM_B}])
    with pytest.raises(Exception, match="polling paused"):
        await active._async_update_data()
    with pytest.raises(Exception, match="No matching"):
        await call(
            "debug_gatt_control", {**control, "session_id": str(uuid4()), "operation": "continue"}
        )
    await call("debug_gatt_control", {**control, "operation": "continue"})
    with pytest.raises(Exception, match="not waiting"):
        await call("debug_gatt_control", {**control, "operation": "continue"})
    result = await task
    assert result["success"] and result["session_id"] == sid
    assert snapshot["phase"] == "waiting"  # Response was a detached snapshot.
    assert (await call("debug_gatt_control", control))["phase"] == "finished"
    assert [c.args[0] for c in transport.write_gatt_char.await_args_list] == [
        TIME,
        PRODUCT_PARAM_B,
        PRODUCT_COMMANDS,
    ]
    ha.coordinator.establish_connection.assert_awaited_once()
    transport.disconnect.assert_awaited_once()
    with pytest.raises(Exception, match="cannot be reused"):
        await call("debug_gatt", data)


@pytest.mark.parametrize("operation", ["abort", "unload"])
async def test_held_debug_abort_or_unload_disconnects_without_confirmation(ha, operation):
    from uuid import uuid4

    from custom_components.taelek.taelek_ble.const import PRODUCT_COMMANDS

    ha.bluetooth.async_last_service_info.return_value = ha.info
    ha.bluetooth.async_ble_device_from_address.return_value = SimpleNamespace(name="Tael")
    transport = AsyncMock()
    ha.coordinator.establish_connection.return_value = transport
    active = ha.coordinator.ActiveCoordinator(ha.hass, ha.entry)
    sid = str(uuid4())
    task = asyncio.create_task(
        active.async_debug_gatt(
            [
                {"operation": "wait_for_continue", "timeout": 1},
                {"operation": "write", "uuid": PRODUCT_COMMANDS, "hex": "83"},
            ],
            session_id=sid,
            sync_time=False,
        )
    )
    await asyncio.sleep(0)
    assert (await active.async_debug_control(sid, "status"))["phase"] == "waiting"
    if operation == "abort":
        await active.async_debug_control(sid, "abort")
        assert not (await task)["success"]
    else:
        ha.entry.runtime_data = SimpleNamespace(active=active)
        assert await ha.integration.async_unload_entry(ha.hass, ha.entry)
        with pytest.raises(asyncio.CancelledError):
            await task
    assert active._debug_session is None
    transport.write_gatt_char.assert_not_called()
    transport.disconnect.assert_awaited_once()


@pytest.fixture
def ha(monkeypatch):
    def module(name, **attrs):
        value = ModuleType(name)
        value.__dict__.update(attrs)
        value.__path__ = []
        monkeypatch.setitem(sys.modules, name, value)
        return value

    class Abort(Exception):
        pass

    class Flow:
        hass = None

        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__()

        async def async_set_unique_id(self, unique_id):
            self.unique_id = unique_id

        def _abort_if_unique_id_configured(self, updates, reload_on_update=False):
            if self.unique_id in self._async_current_ids():
                raise Abort(updates)

        def _async_current_ids(self):
            return getattr(self, "configured", set())

        def async_abort(self, **kwargs):
            return {"type": "abort", **kwargs}

        def async_show_form(self, **kwargs):
            return {"type": "form", **kwargs}

        def async_create_entry(self, **kwargs):
            return {"type": "create_entry", **kwargs}

    class Coordinator:
        def __init__(self, hass, logger, **kwargs):
            self.hass = hass
            self.data = None
            self.last_update_success = True
            self.notify = Mock()

        def async_set_updated_data(self, data):
            self.data = data
            self.last_update_success = True
            self.notify()

        def async_update_listeners(self):
            self.notify()

        async def async_request_refresh(self):
            try:
                self.async_set_updated_data(await self._async_update_data())
            except (OSError, ValueError, UpdateFailed) as err:
                self.last_exception = err
                # Mirror HA's error boundary in this test double.
                self.last_update_success = False

    class Entity:
        def __init__(self, coordinator):
            self.coordinator = coordinator

        async def async_added_to_hass(self):
            pass

    class UpdateFailed(Exception):
        pass

    module("homeassistant")
    module(
        "homeassistant.config_entries",
        ConfigFlow=Flow,
        OptionsFlow=Flow,
        ConfigEntry=object,
        ConfigEntryState=SimpleNamespace(LOADED="loaded"),
    )
    module(
        "homeassistant.core",
        callback=lambda fn: fn,
        HomeAssistant=object,
        SupportsResponse=SimpleNamespace(ONLY="only"),
    )
    module(
        "homeassistant.exceptions", HomeAssistantError=type("HomeAssistantError", (Exception,), {})
    )
    module(
        "homeassistant.const",
        CONF_ADDRESS="address",
        EntityCategory=SimpleNamespace(DIAGNOSTIC="diagnostic"),
        UnitOfTemperature=SimpleNamespace(CELSIUS="°C"),
    )
    module("homeassistant.components")
    module("homeassistant.components.button", ButtonEntity=type("ButtonEntity", (), {}))
    bluetooth = module(
        "homeassistant.components.bluetooth",
        BluetoothScanningMode=SimpleNamespace(PASSIVE="passive"),
        async_register_callback=Mock(return_value=Mock()),
        async_track_unavailable=Mock(return_value=Mock()),
        async_last_service_info=Mock(return_value=None),
        async_address_present=Mock(return_value=True),
        async_ble_device_from_address=Mock(return_value=None),
        async_discovered_service_info=Mock(return_value=[]),
    )
    module(
        "homeassistant.components.sensor",
        SensorEntity=type("SensorEntity", (), {}),
        SensorDeviceClass=SimpleNamespace(TEMPERATURE="temperature"),
        SensorStateClass=SimpleNamespace(MEASUREMENT="measurement"),
    )
    module(
        "homeassistant.components.binary_sensor",
        BinarySensorEntity=type("BinarySensorEntity", (), {}),
        BinarySensorDeviceClass=SimpleNamespace(HEAT="heat"),
    )
    module("homeassistant.helpers")
    module("homeassistant.util")
    module("homeassistant.util.dt", now=lambda: datetime(2026, 10, 3, tzinfo=UTC))
    module(
        "homeassistant.helpers.device_registry", CONNECTION_BLUETOOTH="bluetooth", DeviceInfo=dict
    )
    module(
        "homeassistant.helpers.update_coordinator",
        DataUpdateCoordinator=Coordinator,
        CoordinatorEntity=Entity,
        UpdateFailed=UpdateFailed,
    )
    module("bleak")
    module("bleak.exc", BleakError=type("BleakError", (Exception,), {}))
    module(
        "bleak_retry_connector",
        BleakClientWithServiceCache=object,
        establish_connection=AsyncMock(),
    )
    # Reload our integration so each test uses its own boundary doubles.
    for name in list(sys.modules):
        if name.startswith("custom_components.taelek"):
            monkeypatch.delitem(sys.modules, name)
    integration = importlib.import_module("custom_components.taelek")
    flow = importlib.import_module("custom_components.taelek.config_flow")
    coordinator = importlib.import_module("custom_components.taelek.coordinator")
    sensor = importlib.import_module("custom_components.taelek.sensor")
    binary = importlib.import_module("custom_components.taelek.binary_sensor")
    info = SimpleNamespace(
        name="Tael",
        address="AA:BB:CC:DD:EE:FF",
        manufacturer_data={1162: struct.pack("<hBBI10s", 215, 0xA6, 0x4D, 123, b"Room")},
    )
    entry = SimpleNamespace(
        data={"address": info.address},
        options={},
        unique_id="serial_0000007b",
        title="Room",
        entry_id="test",
        async_on_unload=Mock(),
        add_update_listener=Mock(return_value=Mock()),
    )
    hass = SimpleNamespace(
        config_entries=SimpleNamespace(
            async_forward_entry_setups=AsyncMock(),
            async_unload_platforms=AsyncMock(return_value=True),
        )
    )
    return SimpleNamespace(
        integration=integration,
        flow=flow,
        coordinator=coordinator,
        sensor=sensor,
        binary=binary,
        bluetooth=bluetooth,
        info=info,
        entry=entry,
        hass=hass,
        Abort=Abort,
    )


async def test_command_button_disabled_by_default_and_never_writes_during_setup(ha):
    button = importlib.import_module("custom_components.taelek.button")
    active = SimpleNamespace(
        async_request_refresh=AsyncMock(),
        async_test_runtime_command=AsyncMock(),
        async_test_eco_temperature=AsyncMock(),
    )
    ha.entry.runtime_data = SimpleNamespace(active=active)
    add_entities = Mock()
    await button.async_setup_entry(ha.hass, ha.entry, add_entities)
    refresh, close, command, low, high, restore = add_entities.call_args.args[0]
    for entity in (low, high, restore):
        assert entity._attr_entity_registry_enabled_default is False
        await entity.async_added_to_hass()
    active.async_test_eco_temperature.assert_not_called()
    assert close._attr_entity_registry_enabled_default is False
    assert command._attr_entity_registry_enabled_default is False
    await command.async_added_to_hass()
    await refresh.async_press()
    active.async_test_runtime_command.assert_not_called()
    await command.async_press()
    active.async_test_runtime_command.assert_awaited_once_with(0x84)
    await low.async_press()
    await high.async_press()
    await restore.async_press()
    assert [call.args[0] for call in active.async_test_eco_temperature.await_args_list] == [
        10.0,
        25.0,
        None,
    ]


async def test_command_failure_preserves_active_data_and_never_retries(ha):
    ha.bluetooth.async_last_service_info.return_value = ha.info
    active = ha.coordinator.ActiveCoordinator(ha.hass, ha.entry)
    original = object()
    active.data = original
    active.client.test_runtime_command = AsyncMock(side_effect=OSError("write lost"))
    with pytest.raises(Exception, match="Taelek command test failed"):
        await active.async_test_runtime_command(0x84)
    active.client.test_runtime_command.assert_awaited_once()
    assert active.data is original
    assert "not retried" in active.last_command_test["result"]


async def test_discovery_confirmation_no_gatt(ha):
    flow = ha.flow.TaelekConfigFlow()
    flow.context = {}
    result = await flow.async_step_bluetooth(ha.info)
    assert result["step_id"] == "confirm"
    assert flow.unique_id == "serial_0000007b"
    result = await flow.async_step_confirm({})
    assert result["data"] == {"address": ha.info.address}
    ha.coordinator.establish_connection.assert_not_called()


async def test_duplicate_and_address_stability(ha):
    flow = ha.flow.TaelekConfigFlow()
    flow.context = {}
    flow.configured = {"serial_0000007b"}
    ha.info.address = "11:22:33:44:55:66"
    with pytest.raises(ha.Abort) as err:
        await flow.async_step_bluetooth(ha.info)
    assert err.value.args[0] == {"address": ha.info.address}


async def test_manual_and_invalid_discovery(ha):
    flow = ha.flow.TaelekConfigFlow()
    flow.hass = ha.hass
    flow.context = {}
    assert (await flow.async_step_user())["reason"] == "no_devices_found"
    ha.bluetooth.async_discovered_service_info.return_value = [ha.info]
    assert (await flow.async_step_user())["step_id"] == "user"
    assert (await flow.async_step_user({"address": ha.info.address}))["step_id"] == "confirm"
    ha.info.manufacturer_data = {1162: b"bad"}
    assert (await flow.async_step_bluetooth(ha.info))["reason"] == "not_supported"


async def test_options_flow(ha):
    flow = ha.flow.TaelekOptionsFlow()
    flow.config_entry = ha.entry
    form = await flow.async_step_init()
    assert form["data_schema"]({}) == {"enable_gatt": False, "enable_debug_gatt": False}
    result = await flow.async_step_init({"enable_gatt": True})
    assert result["data"]["enable_gatt"] is True


async def test_passive_setup_never_connects(ha):
    ha.bluetooth.async_last_service_info.return_value = ha.info
    assert await ha.integration.async_setup_entry(ha.hass, ha.entry)
    assert ha.entry.runtime_data.active is None
    ha.coordinator.establish_connection.assert_not_called()
    assert await ha.integration.async_unload_entry(ha.hass, ha.entry)


async def test_passive_update_unavailable_recovery_and_wrong_serial(ha):
    coordinator = ha.coordinator.AdvertisementCoordinator(ha.hass, ha.entry)
    sensor = ha.sensor.TaelekSensor(
        coordinator, ha.entry, "temperature_c", "Advertised temperature"
    )
    coordinator._receive(ha.info, None)
    assert sensor.available and sensor.native_value == 21.5
    assert coordinator.data.state is None and coordinator.data.relay is None
    assert coordinator.data.status_raw == 0xA6
    coordinator._unavailable(ha.info)
    assert not sensor.available
    coordinator._receive(ha.info, None)
    assert sensor.available
    original = coordinator.data
    ha.info.manufacturer_data[1162] = struct.pack("<hBBI10s", 300, 0, 0, 999, b"Other")
    coordinator._receive(ha.info, None)
    assert coordinator.data == original


async def test_gatt_failure_recovery_and_passive_independence(ha):
    ha.bluetooth.async_last_service_info.return_value = ha.info
    passive = ha.coordinator.AdvertisementCoordinator(ha.hass, ha.entry)
    passive._receive(ha.info, None)
    active = ha.coordinator.ActiveCoordinator(ha.hass, ha.entry)
    active.client.read_state_with_details = AsyncMock(side_effect=OSError("offline"))
    await active.async_request_refresh()
    assert not active.last_update_success
    assert passive.present and passive.data.temperature_c == 21.5
    state = SimpleNamespace(measured_floor_c=24.5, valve_state=1)
    active.client.read_state_with_details = AsyncMock(return_value=state)
    await active.async_request_refresh()
    assert active.last_update_success and active.data == state
    entity = ha.binary.TaelekHeating(active, ha.entry)
    assert entity.is_on and entity.available
    state.valve_state = 99
    assert entity.is_on is None


async def test_ha_sessions_sync_configured_clock_and_failure_preserves_passive(ha):
    from custom_components.taelek.taelek_ble.const import TIME

    ha.bluetooth.async_last_service_info.return_value = ha.info
    ha.bluetooth.async_ble_device_from_address.return_value = SimpleNamespace(name="Tael")
    ha.coordinator.dt_util.now = lambda: datetime(
        2026, 10, 3, 1, 2, 3, tzinfo=timezone(timedelta(hours=3))
    )
    passive = ha.coordinator.AdvertisementCoordinator(ha.hass, ha.entry)
    passive._receive(ha.info, None)
    active = ha.coordinator.ActiveCoordinator(ha.hass, ha.entry)
    client = AsyncMock()
    client.read_gatt_char.return_value = struct.pack("<BBBBhHHH", 0, 0, 0, 1, 230, 210, 245, 0)
    ha.coordinator.establish_connection.return_value = client
    await active.async_request_refresh()
    assert active.last_update_success
    client.write_gatt_char.assert_awaited_once_with(TIME, bytes((1, 2, 3, 6)), response=True)
    assert client.mock_calls[0].args == (TIME, bytes((1, 2, 3, 6)))
    ha.coordinator.establish_connection.assert_awaited_once()
    client.write_gatt_char.reset_mock()
    client.read_gatt_char.reset_mock()
    client.write_gatt_char.side_effect = OSError("authorization denied")
    await active.async_request_refresh()
    assert not active.last_update_success
    assert "clock synchronization failed" in str(active.last_exception)
    assert passive.present and passive.data.temperature_c == 21.5
    client.write_gatt_char.assert_awaited_once()
    client.read_gatt_char.assert_not_called()


@pytest.mark.parametrize("sync_time,clock_failure", [(True, False), (False, False), (True, True)])
async def test_debug_service_schema_through_coordinator_and_vendored_clock(
    ha, sync_time, clock_failure
):
    from custom_components.taelek.taelek_ble.const import PRODUCT_COMMANDS, PRODUCT_STATE_A, TIME

    ha.bluetooth.async_last_service_info.return_value = ha.info
    ha.bluetooth.async_ble_device_from_address.return_value = SimpleNamespace(name="Tael")
    ha.coordinator.dt_util.now = lambda: datetime(
        2026, 10, 3, 1, 2, 3, tzinfo=timezone(timedelta(hours=3))
    )
    client = AsyncMock()
    client.read_gatt_char.return_value = b"observed"
    if clock_failure:
        client.write_gatt_char.side_effect = OSError("authorization denied")
    ha.coordinator.establish_connection.return_value = client
    active = ha.coordinator.ActiveCoordinator(ha.hass, ha.entry)
    ha.entry.domain = "taelek"
    ha.entry.state = "loaded"
    ha.entry.options["enable_debug_gatt"] = True
    ha.entry.runtime_data = SimpleNamespace(active=active)
    ha.hass.config_entries.async_get_entry = Mock(return_value=ha.entry)
    ha.hass.services = SimpleNamespace(async_register=Mock())
    await ha.integration.async_setup(ha.hass, {})
    registration = next(
        c for c in ha.hass.services.async_register.call_args_list if c.args[1] == "debug_gatt"
    )
    handler = registration.args[2]
    data = {
        "config_entry_id": "test",
        "steps": [
            {"operation": "read", "uuid": PRODUCT_STATE_A},
            {"operation": "write", "uuid": PRODUCT_COMMANDS, "hex": "84"},
        ],
    }
    # Exercise both the public schema's default and its explicit false value.
    if not sync_time:
        data["sync_time"] = False
    call = SimpleNamespace(data=registration.kwargs["schema"](data))
    assert call.data["sync_time"] is sync_time
    result = await handler(call)
    time_writes = [c for c in client.write_gatt_char.await_args_list if c.args[0] == TIME]
    assert len(time_writes) == int(sync_time)
    if time_writes:
        assert time_writes[0].args == (TIME, bytes((1, 2, 3, 6)))
    if clock_failure:
        assert not result["success"] and result["steps"] == []
        assert "clock synchronization failed" in result["error"]
        assert "authorization denied" in result["clock_sync"]["error"]
        client.read_gatt_char.assert_not_called()
        client.write_gatt_char.assert_awaited_once()
    else:
        assert result["success"] and len(result["steps"]) == 2
        client.read_gatt_char.assert_awaited_once_with(PRODUCT_STATE_A)
        assert client.write_gatt_char.await_args_list[-1].args == (PRODUCT_COMMANDS, b"\x84")
        if not sync_time:
            assert result["clock_sync"]["status"] == "skipped by request"
            client.write_gatt_char.assert_awaited_once()
    client.disconnect.assert_awaited_once()


@pytest.mark.parametrize("bad_guard", [False, True])
async def test_cached_service_through_coordinator_uses_only_initial_read(ha, bad_guard):
    from custom_components.taelek.taelek_ble.const import PRODUCT_PARAM_B, TIME

    ha.bluetooth.async_last_service_info.return_value = ha.info
    ha.bluetooth.async_ble_device_from_address.return_value = SimpleNamespace(name="Tael")
    transport = AsyncMock()
    original = bytes(range(16))
    transport.read_gatt_char.return_value = original
    ha.coordinator.establish_connection.return_value = transport
    active = ha.coordinator.ActiveCoordinator(ha.hass, ha.entry)
    ha.entry.domain, ha.entry.state = "taelek", "loaded"
    ha.entry.options["enable_debug_gatt"] = True
    ha.entry.runtime_data = SimpleNamespace(active=active)
    ha.hass.config_entries.async_get_entry = Mock(return_value=ha.entry)
    ha.hass.services = SimpleNamespace(async_register=Mock())
    await ha.integration.async_setup(ha.hass, {})
    registration = next(
        c for c in ha.hass.services.async_register.call_args_list if c.args[1] == "debug_gatt"
    )
    data = {
        "config_entry_id": "test",
        "sync_time": False,
        "steps": [
            {
                "operation": "read",
                "uuid": PRODUCT_PARAM_B,
                "expected_length": 15 if bad_guard else 16,
            },
            {
                "operation": "write_cached",
                "uuid": PRODUCT_PARAM_B,
                "source_step": 0,
                "offset": 2,
                "hex": "6400",
            },
        ],
    }
    result = await registration.args[2](SimpleNamespace(data=registration.kwargs["schema"](data)))
    transport.read_gatt_char.assert_awaited_once_with(PRODUCT_PARAM_B)
    assert not any(c.args[0] == TIME for c in transport.write_gatt_char.await_args_list)
    assert result["success"] is not bad_guard
    if bad_guard:
        transport.write_gatt_char.assert_not_called()
    else:
        transport.write_gatt_char.assert_awaited_once_with(
            PRODUCT_PARAM_B, original[:2] + b"\x64\x00" + original[4:], response=True
        )
        assert result["steps"][1]["source_step"] == 0
    transport.disconnect.assert_awaited_once()


async def test_nonthermostat_blocks_gatt_and_temperature(ha):
    ha.info.manufacturer_data[1162] = struct.pack("<hBBI10s", 300, 0, 0x55, 123, b"Plug")
    ha.bluetooth.async_last_service_info.return_value = ha.info
    active = ha.coordinator.ActiveCoordinator(ha.hass, ha.entry)
    with pytest.raises(ha.coordinator.UpdateFailed, match="supported thermostat"):
        await active._connect()
    ha.coordinator.establish_connection.assert_not_called()
    passive = ha.coordinator.AdvertisementCoordinator(ha.hass, ha.entry)
    passive._receive(ha.info, None)
    entity = ha.sensor.TaelekSensor(passive, ha.entry, "temperature_c", "Advertised temperature")
    assert entity.native_value is None


async def test_gatt_uses_ha_device_and_minimum_timeout(ha):
    ha.bluetooth.async_last_service_info.return_value = ha.info
    device = SimpleNamespace(name="Tael")
    ha.bluetooth.async_ble_device_from_address.return_value = device
    active = ha.coordinator.ActiveCoordinator(ha.hass, ha.entry)
    await active._connect()
    args = ha.coordinator.establish_connection.await_args
    assert args.args[1] is device and args.kwargs["timeout"] >= 10
    ha.bluetooth.async_ble_device_from_address.assert_called_once_with(
        ha.hass, ha.info.address, connectable=True
    )


@pytest.mark.parametrize("raw_type", [0x55, 0x6A, 0x90, 0x91, 0x9F])
async def test_flow_rejects_nonthermostats_in_bluetooth_and_manual_selection(ha, raw_type):
    ha.info.manufacturer_data[1162] = struct.pack("<hBBI10s", 300, 0, raw_type, 123, b"Other")
    flow = ha.flow.TaelekConfigFlow()
    flow.context = {}
    flow.hass = ha.hass
    assert (await flow.async_step_bluetooth(ha.info))["reason"] == "not_supported"
    ha.bluetooth.async_discovered_service_info.return_value = [ha.info]
    assert (await flow.async_step_user())["reason"] == "no_devices_found"
    ha.coordinator.establish_connection.assert_not_called()


async def test_flow_keeps_unknown_type_as_hardware_test_candidate(ha):
    ha.info.manufacturer_data[1162] = struct.pack("<hBBI10s", 215, 0, 0x77, 123, b"Unknown")
    flow = ha.flow.TaelekConfigFlow()
    flow.context = {}
    flow.hass = ha.hass
    assert (await flow.async_step_bluetooth(ha.info))["step_id"] == "confirm"
    ha.bluetooth.async_discovered_service_info.return_value = [ha.info]
    assert (await flow.async_step_user())["step_id"] == "user"


@pytest.mark.parametrize("floor_encoding", ["unresolved", "signed", "unsigned"])
async def test_ha_never_exposes_ffff_as_minus_point_one(ha, floor_encoding):
    from taelek_ble.capabilities import DeviceCapabilities, FloorEncoding
    from taelek_ble.codec import decode_state_a

    raw = struct.pack("<BBBBhHHH", 0, 0, 0, 1, 200, 210, 0xFFFF, 0)
    coordinator = ha.coordinator.ActiveCoordinator(ha.hass, ha.entry)
    coordinator.data = decode_state_a(
        raw, capabilities=DeviceCapabilities(floor_encoding=FloorEncoding(floor_encoding))
    )
    entity = ha.sensor.TaelekSensor(
        coordinator, ha.entry, "measured_floor_c", "Floor temperature", active=True
    )
    assert entity.native_value is None
    assert coordinator.data.raw_data[8:10] == b"\xff\xff"


async def test_removed_profile_is_cleaned_from_existing_entry(ha):
    ha.entry.options = {"enable_gatt": False, "protocol_profile": "v2"}
    ha.hass.config_entries.async_update_entry = Mock()
    await ha.integration.async_setup_entry(ha.hass, ha.entry)
    ha.hass.config_entries.async_update_entry.assert_called_once_with(
        ha.entry, options={"enable_gatt": False}
    )


async def test_old_profile_is_not_saved_by_options_flow(ha):
    flow = ha.flow.TaelekOptionsFlow()
    result = await flow.async_step_init({"enable_gatt": True, "protocol_profile": "legacy"})
    assert result["data"] == {"enable_gatt": True, "enable_debug_gatt": False}


async def test_debug_service_is_registered_without_connecting_and_gated(ha):
    ha.hass.services = SimpleNamespace(async_register=Mock())
    await ha.integration.async_setup(ha.hass, {})
    registration = next(
        c for c in ha.hass.services.async_register.call_args_list if c.args[1] == "debug_gatt"
    )
    assert registration.args[:2] == ("taelek", "debug_gatt")
    assert registration.kwargs["supports_response"] == "only"
    handler = registration.args[2]
    ha.entry.domain = "taelek"
    ha.entry.state = "loaded"
    active = SimpleNamespace(async_debug_gatt=AsyncMock(return_value={"success": True}))
    ha.entry.runtime_data = SimpleNamespace(active=active)
    ha.hass.config_entries.async_get_entry = Mock(return_value=ha.entry)
    call = SimpleNamespace(data={"config_entry_id": "test", "steps": []})
    with pytest.raises(Exception, match="Enable raw GATT"):
        await handler(call)
    active.async_debug_gatt.assert_not_called()
    ha.entry.options["enable_debug_gatt"] = True
    assert await handler(call) == {"success": True}
    active.async_debug_gatt.assert_awaited_once_with([], sync_time=True)
    call.data["sync_time"] = False
    assert await handler(call) == {"success": True}
    active.async_debug_gatt.assert_awaited_with([], sync_time=False)
    ha.entry.state = "not_loaded"
    with pytest.raises(Exception, match="must be loaded"):
        await handler(call)


async def test_debug_service_rejects_wrong_entry_and_disabled_gatt(ha):
    ha.hass.services = SimpleNamespace(async_register=Mock())
    await ha.integration.async_setup(ha.hass, {})
    handler = next(
        c.args[2]
        for c in ha.hass.services.async_register.call_args_list
        if c.args[1] == "debug_gatt"
    )
    ha.hass.config_entries.async_get_entry = Mock(return_value=None)
    call = SimpleNamespace(data={"config_entry_id": "missing", "steps": []})
    with pytest.raises(Exception, match="Select a Taelek"):
        await handler(call)
    ha.entry.domain = "other"
    ha.hass.config_entries.async_get_entry.return_value = ha.entry
    with pytest.raises(Exception, match="Select a Taelek"):
        await handler(call)
    ha.entry.domain = "taelek"
    ha.entry.state = "loaded"
    ha.entry.options["enable_debug_gatt"] = True
    ha.entry.runtime_data = SimpleNamespace(active=None)
    with pytest.raises(Exception, match="GATT enabled"):
        await handler(call)
