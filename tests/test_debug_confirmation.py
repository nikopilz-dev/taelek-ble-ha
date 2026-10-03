"""Human continuation gates never infer approval from elapsed time."""

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from taelek_ble.client import TaelekClient
from taelek_ble.const import PRODUCT_COMMANDS, PRODUCT_PARAM_B, TIME

STEPS = [
    {"operation": "patch", "uuid": PRODUCT_PARAM_B, "offset": 2, "hex": "6400"},
    {"operation": "wait_for_continue", "timeout": 1},
    {"operation": "write", "uuid": PRODUCT_COMMANDS, "hex": "83"},
]


async def test_gate_keeps_one_connection_one_clock_and_does_not_write_until_released():
    transport = AsyncMock()
    original = bytes(range(16))
    transport.read_gatt_char.return_value = original
    connector = AsyncMock(return_value=transport)
    paused, release = asyncio.Event(), asyncio.Event()

    async def pause(result):
        assert result["steps"][0]["original_hex"] == original.hex()
        assert (
            result["steps"][0]["written_hex"] == (original[:2] + b"\x64\x00" + original[4:]).hex()
        )
        paused.set()
        await release.wait()

    client = TaelekClient(connector, clock=lambda: datetime(2026, 10, 3, tzinfo=UTC))
    task = asyncio.create_task(client.debug_gatt(STEPS, pause=pause))
    await paused.wait()
    assert [c.args[0] for c in transport.write_gatt_char.await_args_list] == [TIME, PRODUCT_PARAM_B]
    transport.disconnect.assert_not_called()
    release.set()
    result = await task
    assert result["success"]
    connector.assert_awaited_once()
    assert [c.args[0] for c in transport.write_gatt_char.await_args_list] == [
        TIME,
        PRODUCT_PARAM_B,
        PRODUCT_COMMANDS,
    ]
    transport.disconnect.assert_awaited_once()
    assert result["steps"][1]["completed_at"] <= result["steps"][2]["started_at"]


@pytest.mark.parametrize("abort", [False, True])
async def test_timeout_or_abort_never_sends_confirmation(abort):
    transport = AsyncMock()
    transport.read_gatt_char.return_value = bytes(16)

    async def pause(result):
        if abort:
            raise ValueError("Operator aborted")
        await asyncio.Event().wait()

    result = await TaelekClient(AsyncMock(return_value=transport)).debug_gatt(STEPS, pause=pause)
    assert not result["success"]
    assert result["error_type"] == ("ValueError" if abort else "TimeoutError")
    assert len(result["steps"]) == 2
    transport.write_gatt_char.assert_awaited_once()
    transport.disconnect.assert_awaited_once()


@pytest.mark.parametrize(
    "steps",
    [
        STEPS,
        [{"operation": "wait_for_continue", "timeout": 181}],
        [{"operation": "wait_for_continue", "timeout": True}],
        [{"operation": "wait_for_continue"}, {"operation": "wait_for_continue"}],
    ],
)
async def test_invalid_or_unmanaged_wait_fails_before_connection(steps):
    connector = AsyncMock()
    with pytest.raises(ValueError):
        await TaelekClient(connector).debug_gatt(steps)
    connector.assert_not_called()


async def test_cancellation_while_waiting_disconnects_without_later_write():
    transport = AsyncMock()
    transport.read_gatt_char.return_value = bytes(16)
    paused = asyncio.Event()

    async def pause(result):
        paused.set()
        await asyncio.Event().wait()

    task = asyncio.create_task(
        TaelekClient(AsyncMock(return_value=transport)).debug_gatt(STEPS, pause=pause)
    )
    await paused.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    transport.write_gatt_char.assert_awaited_once()
    transport.disconnect.assert_awaited_once()
