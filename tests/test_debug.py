"""Raw experiments validate the full sequence, preserve bytes and never replay writes."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from taelek_ble.client import TaelekClient
from taelek_ble.const import PRODUCT_COMMANDS, PRODUCT_PARAM_B, PRODUCT_STATE_A


async def test_discover_returns_handles_without_reads_or_writes():
    transport = AsyncMock()
    transport.services = [
        SimpleNamespace(
            uuid="ABC",
            handle=1,
            characteristics=[
                SimpleNamespace(
                    uuid=PRODUCT_PARAM_B.upper(), handle=2, properties=["read", "write"]
                )
            ],
        )
    ]
    result = await TaelekClient(AsyncMock(return_value=transport)).debug_gatt(
        [{"operation": "discover"}], sync_time=False
    )
    assert result["success"]
    assert result["steps"][0]["services"] == [
        {
            "uuid": "abc",
            "handle": 1,
            "characteristics": [
                {"uuid": PRODUCT_PARAM_B, "handle": 2, "properties": ["read", "write"]}
            ],
        }
    ]
    transport.read_gatt_char.assert_not_awaited()
    transport.write_gatt_char.assert_not_awaited()
    transport.disconnect.assert_awaited_once()


async def test_missing_service_table_stops_before_requested_write():
    transport = AsyncMock()
    transport.services = None
    result = await TaelekClient(AsyncMock(return_value=transport)).debug_gatt(
        [{"operation": "discover"}, {"operation": "write", "uuid": PRODUCT_COMMANDS, "hex": "83"}],
        sync_time=False,
    )
    assert not result["success"] and result["error_type"] == "ValueError"
    assert len(result["steps"]) == 1
    transport.write_gatt_char.assert_not_awaited()
    transport.disconnect.assert_awaited_once()


async def test_debug_sequence_reads_patches_writes_and_reads_in_order():
    client = AsyncMock()
    original = bytes(range(18))
    client.read_gatt_char.side_effect = [b"\x01", original, b"\x02"]
    result = await TaelekClient(AsyncMock(return_value=client)).debug_gatt(
        [
            {"operation": "read", "uuid": PRODUCT_STATE_A},
            {"operation": "patch", "uuid": PRODUCT_PARAM_B, "offset": 2, "hex": "64 00"},
            {
                "operation": "write",
                "uuid": PRODUCT_COMMANDS.upper(),
                "hex": "83",
                "response": False,
            },
            {"operation": "delay", "seconds": 0},
            {"operation": "read", "uuid": PRODUCT_STATE_A},
        ]
    )
    assert result["success"]
    assert result["steps"][0]["hex"] == "01" and result["steps"][4]["hex"] == "02"
    writes = client.write_gatt_char.await_args_list
    assert writes[0].args == (PRODUCT_PARAM_B, original[:2] + b"\x64\x00" + original[4:])
    assert writes[1].args == (PRODUCT_COMMANDS, b"\x83")
    assert writes[1].kwargs == {"response": False}
    client.disconnect.assert_awaited_once()


@pytest.mark.parametrize(
    "bad",
    [
        {"operation": "write", "uuid": PRODUCT_COMMANDS, "hex": "8"},
        {"operation": "write", "uuid": "bad", "hex": "84"},
        {"operation": "write", "uuid": PRODUCT_COMMANDS, "hex": "00" * 513},
        {"operation": "write", "uuid": PRODUCT_COMMANDS, "hex": "84", "response": "false"},
        {"operation": "delay", "seconds": float("nan")},
        {"operation": "delay", "seconds": 6},
        {"operation": "patch", "uuid": PRODUCT_PARAM_B, "hex": "64", "offset": -1},
        {"operation": "read", "uuid": PRODUCT_STATE_A, "typo": True},
        {"operation": []},
    ],
)
async def test_invalid_later_step_prevents_even_first_write(bad):
    connect = AsyncMock()
    with pytest.raises(ValueError):
        await TaelekClient(connect).debug_gatt(
            [
                {"operation": "write", "uuid": PRODUCT_COMMANDS, "hex": "84"},
                bad,
            ]
        )
    connect.assert_not_called()


async def test_readback_failure_returns_partial_result_and_never_retries():
    client = AsyncMock()
    client.read_gatt_char.side_effect = OSError("read failed")
    result = await TaelekClient(AsyncMock(return_value=client)).debug_gatt(
        [
            {"operation": "write", "uuid": PRODUCT_COMMANDS, "hex": "84"},
            {"operation": "read", "uuid": PRODUCT_STATE_A},
            {"operation": "write", "uuid": PRODUCT_COMMANDS, "hex": "83"},
        ]
    )
    assert not result["success"] and result["error_type"] == "OSError"
    assert result["steps"][0]["status"] == "completed"
    assert result["steps"][1]["status"] == "started"
    assert len(result["steps"]) == 2
    client.write_gatt_char.assert_awaited_once()
    client.disconnect.assert_awaited_once()


async def test_failed_write_report_is_ambiguous_and_not_replayed():
    client = AsyncMock()
    client.write_gatt_char.side_effect = OSError("ack lost")
    result = await TaelekClient(AsyncMock(return_value=client)).debug_gatt(
        [
            {"operation": "write", "uuid": PRODUCT_COMMANDS, "hex": "84"},
        ]
    )
    assert not result["success"]
    assert result["steps"][0]["status"] == "write attempted; effect may be unknown"
    client.write_gatt_char.assert_awaited_once()
    client.disconnect.assert_awaited_once()


async def test_patch_beyond_actual_length_never_writes():
    client = AsyncMock()
    client.read_gatt_char.return_value = b"\x01"
    result = await TaelekClient(AsyncMock(return_value=client)).debug_gatt(
        [
            {"operation": "patch", "uuid": PRODUCT_PARAM_B, "offset": 2, "hex": "64"},
        ]
    )
    assert not result["success"]
    client.write_gatt_char.assert_not_called()


async def test_connection_failure_returns_no_steps():
    result = await TaelekClient(AsyncMock(side_effect=OSError("offline"))).debug_gatt(
        [
            {"operation": "read", "uuid": PRODUCT_STATE_A},
        ]
    )
    assert not result["success"] and result["steps"] == []


async def test_cancelled_debug_disconnects_without_continuing():
    client = AsyncMock()
    started = asyncio.Event()

    async def read(uuid):
        started.set()
        await asyncio.Event().wait()

    client.read_gatt_char.side_effect = read
    task = asyncio.create_task(
        TaelekClient(AsyncMock(return_value=client)).debug_gatt(
            [
                {"operation": "read", "uuid": PRODUCT_STATE_A},
                {"operation": "write", "uuid": PRODUCT_COMMANDS, "hex": "84"},
            ]
        )
    )
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    client.disconnect.assert_awaited_once()
    client.write_gatt_char.assert_not_called()
