import asyncio
from datetime import UTC, datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from taelek_ble.client import TaelekClient
from taelek_ble.clock import encode_time
from taelek_ble.const import PRODUCT_COMMANDS, PRODUCT_STATE_A, TIME

LOCAL = timezone(timedelta(hours=3))


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (datetime(2026, 10, 3, 1, 2, 59, tzinfo=LOCAL), b"\x01\x02\x3b\x06"),
        (datetime(2026, 10, 4, 0, 0, 0, tzinfo=LOCAL), b"\x00\x00\x00\x07"),
        (datetime(2026, 10, 5, 23, 59, 59, tzinfo=LOCAL), b"\x17\x3b\x3b\x01"),
    ],
)
def test_local_clock_bytes_and_iso_weekday(value, expected):
    assert encode_time(value) == expected


def test_local_midnight_uses_local_weekday_rather_than_utc():
    instant = datetime(2026, 10, 3, 22, 15, 1, tzinfo=UTC)
    assert encode_time(instant.astimezone(LOCAL)) == b"\x01\x0f\x01\x07"


def test_naive_time_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        encode_time(datetime(2026, 10, 3, tzinfo=UTC).replace(tzinfo=None))


async def test_sync_once_each_session_before_reads_with_fresh_time():
    clients = [AsyncMock(), AsyncMock()]
    for client in clients:
        client.read_gatt_char.return_value = bytes(12)
    clock = Mock(
        side_effect=[
            datetime(2026, 10, 3, 23, 59, 59, tzinfo=LOCAL),
            datetime(2026, 10, 4, 0, 0, 0, tzinfo=LOCAL),
        ]
    )
    reader = TaelekClient(AsyncMock(side_effect=clients), clock=clock)
    await reader.read_state()
    await reader.read_state()
    for client, payload in zip(clients, (b"\x17\x3b\x3b\x06", bytes((0, 0, 0, 7)))):
        assert client.mock_calls[0].args == (TIME, payload)
        client.write_gatt_char.assert_awaited_once_with(TIME, payload, response=True)
        client.read_gatt_char.assert_awaited_once_with(PRODUCT_STATE_A)
        client.disconnect.assert_awaited_once()
    assert clock.call_count == 2


async def test_debug_prelude_reported_separately_and_never_saves():
    client = AsyncMock()
    client.read_gatt_char.return_value = b"state"
    reader = TaelekClient(
        AsyncMock(return_value=client), clock=lambda: datetime(2026, 10, 3, 1, 2, 3, tzinfo=LOCAL)
    )
    result = await reader.debug_gatt(
        [
            {"operation": "read", "uuid": PRODUCT_STATE_A},
            {"operation": "read", "uuid": PRODUCT_STATE_A},
        ]
    )
    assert result["success"] and len(result["steps"]) == 2
    assert result["clock_sync"]["hex"] == "01020306"
    assert result["clock_sync"]["status"] == "completed; device clock not read back"
    client.write_gatt_char.assert_awaited_once_with(TIME, b"\x01\x02\x03\x06", response=True)


async def test_debug_without_sync_is_really_read_only():
    client = AsyncMock()
    client.read_gatt_char.return_value = b"state"
    clock = Mock()
    result = await TaelekClient(AsyncMock(return_value=client), clock=clock).debug_gatt(
        [{"operation": "read", "uuid": PRODUCT_STATE_A}], sync_time=False
    )
    assert result["success"] and result["clock_sync"]["status"] == "skipped by request"
    clock.assert_not_called()
    client.write_gatt_char.assert_not_called()


async def test_failed_clock_stops_debug_steps_disconnects_and_never_retries():
    client = AsyncMock()
    client.write_gatt_char.side_effect = OSError("authorization denied")
    reader = TaelekClient(
        AsyncMock(return_value=client), clock=lambda: datetime(2026, 10, 3, tzinfo=LOCAL)
    )
    result = await reader.debug_gatt(
        [{"operation": "write", "uuid": PRODUCT_COMMANDS, "hex": "83"}]
    )
    assert not result["success"] and result["steps"] == []
    assert "clock synchronization failed" in result["error"]
    assert result["clock_sync"]["status"] == "write attempted; effect may be unknown"
    client.write_gatt_char.assert_awaited_once()
    client.read_gatt_char.assert_not_called()
    client.disconnect.assert_awaited_once()


async def test_invalid_debug_sequence_prevents_clock_write_and_connection():
    connect = AsyncMock()
    reader = TaelekClient(connect, clock=Mock())
    with pytest.raises(ValueError):
        await reader.debug_gatt([{"operation": "write", "uuid": TIME, "hex": "a"}])
    connect.assert_not_called()


async def test_cancel_during_clock_write_disconnects_without_read_or_retry():
    client = AsyncMock()
    started = asyncio.Event()

    async def write(*args, **kwargs):
        started.set()
        await asyncio.Event().wait()

    client.write_gatt_char.side_effect = write
    reader = TaelekClient(
        AsyncMock(return_value=client), clock=lambda: datetime(2026, 10, 3, tzinfo=LOCAL)
    )
    task = asyncio.create_task(reader.read_state())
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    client.write_gatt_char.assert_awaited_once()
    client.read_gatt_char.assert_not_called()
    client.disconnect.assert_awaited_once()
