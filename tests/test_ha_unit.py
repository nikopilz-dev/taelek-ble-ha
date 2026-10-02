"""Integration logic tests with HA boundaries stubbed for Windows.

These test our callbacks/flows/entities, not the real HA event loop or loader.
The separate tests_ha suite must run on supported Linux/Python with real HA.
"""

import importlib
import struct
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest


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
    module("homeassistant.config_entries", ConfigFlow=Flow, OptionsFlow=Flow, ConfigEntry=object)
    module("homeassistant.core", callback=lambda fn: fn, HomeAssistant=object)
    module(
        "homeassistant.const",
        CONF_ADDRESS="address",
        EntityCategory=SimpleNamespace(DIAGNOSTIC="diagnostic"),
        UnitOfTemperature=SimpleNamespace(CELSIUS="°C"),
    )
    module("homeassistant.components")
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
    assert form["data_schema"]({}) == {"enable_gatt": False}
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
    assert result["data"] == {"enable_gatt": True}
