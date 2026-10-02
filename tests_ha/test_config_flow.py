"""Real Home Assistant flow-manager coverage, separate from Windows unit tests."""

import struct
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

DOMAIN = "taelek"


def discovery(address="AA:BB:CC:DD:EE:FF", serial=123):
    return SimpleNamespace(
        name="Tael",
        address=address,
        manufacturer_data={1162: struct.pack("<hBBI10s", 215, 0xA6, 0x4D, serial, b"Room")},
    )


async def test_bluetooth_discovery_and_confirmation(hass):
    with patch("custom_components.taelek.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_BLUETOOTH}, data=discovery()
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "confirm"
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["result"].unique_id == "serial_0000007b"
        assert result["data"] == {"address": "AA:BB:CC:DD:EE:FF"}
        await hass.async_block_till_done()


async def test_duplicate_updates_address(hass):
    entry = MockConfigEntry(domain=DOMAIN, unique_id="serial_0000007b", data={"address": "OLD"})
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_BLUETOOTH}, data=discovery()
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.data["address"] == "AA:BB:CC:DD:EE:FF"


async def test_simultaneous_duplicate_flow(hass):
    first = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_BLUETOOTH}, data=discovery()
    )
    assert first["type"] is FlowResultType.FORM
    second = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=discovery("11:22:33:44:55:66"),
    )
    assert second["type"] is FlowResultType.ABORT
    assert second["reason"] == "already_in_progress"


async def test_malformed_bluetooth_discovery(hass):
    info = discovery()
    info.manufacturer_data = {1162: b"bad"}
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_BLUETOOTH}, data=info
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "not_supported"


async def test_manual_selection(hass):
    with patch(
        "custom_components.taelek.config_flow.bluetooth.async_discovered_service_info",
        return_value=[discovery()],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["step_id"] == "user"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"address": "AA:BB:CC:DD:EE:FF"}
        )
        assert result["step_id"] == "confirm"


async def test_options(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id="serial_0000007b", data={"address": "AA:BB:CC:DD:EE:FF"}
    )
    entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["step_id"] == "init"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"enable_gatt": True}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {"enable_gatt": True}


@pytest.mark.parametrize("raw_type", [0x55, 0x6A, 0x91])
async def test_nonthermostat_discovery_is_rejected(hass, raw_type):
    info = discovery()
    info.manufacturer_data = {1162: struct.pack("<hBBI10s", 215, 0xA6, raw_type, 123, b"Other")}
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_BLUETOOTH}, data=info
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "not_supported"
