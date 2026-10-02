import asyncio
import struct
from unittest.mock import AsyncMock

import pytest

from taelek_ble.client import TaelekClient
from taelek_ble.const import (
    COMMAND_CLOSE,
    COMMAND_NORMAL,
    PRODUCT_BUTTONS,
    PRODUCT_BUTTONS_2,
    PRODUCT_COMMANDS,
    PRODUCT_INFO,
    PRODUCT_PARAM_B,
    PRODUCT_STATE_A,
)

STATE = struct.pack("<BBBBhHHH", 40, 0, 0, 1, 230, 210, 245, 65535)


async def test_read_reconnects_disconnects_and_never_writes():
    clients = [AsyncMock(), AsyncMock()]
    for client in clients:
        client.read_gatt_char.return_value = STATE
    connector = AsyncMock(side_effect=clients)
    reader = TaelekClient(connector)
    for client in clients:
        assert (await reader.read_state()).measured_floor_c == 24.5
        client.read_gatt_char.assert_awaited_once_with(PRODUCT_STATE_A)
        client.disconnect.assert_awaited_once()
        client.write_gatt_char.assert_not_called()
    assert connector.await_count == 2


async def test_read_error_keeps_original_error_and_disconnects():
    client = AsyncMock()
    client.read_gatt_char.side_effect = OSError("read failed")
    client.disconnect.side_effect = OSError("disconnect failed")
    with pytest.raises(OSError, match="read failed"):
        await TaelekClient(AsyncMock(return_value=client)).read_state()
    client.disconnect.assert_awaited_once()


async def test_cancelled_read_disconnects():
    started = asyncio.Event()
    client = AsyncMock()

    async def read(uuid):
        started.set()
        await asyncio.Event().wait()

    client.read_gatt_char.side_effect = read
    task = asyncio.create_task(TaelekClient(AsyncMock(return_value=client)).read_state())
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    client.disconnect.assert_awaited_once()


async def test_concurrent_reads_do_not_overlap_sessions():
    current = 0
    peak = 0

    async def connect():
        nonlocal current, peak
        current += 1
        peak = max(peak, current)
        client = AsyncMock()

        async def read(uuid):
            await asyncio.sleep(0)
            return STATE

        async def disconnect():
            nonlocal current
            current -= 1

        client.read_gatt_char.side_effect = read
        client.disconnect.side_effect = disconnect
        return client

    reader = TaelekClient(connect)
    await asyncio.gather(reader.read_state(), reader.read_state())
    assert peak == 1 and current == 0


async def test_malformed_read_and_settings_disconnect():
    client = AsyncMock()
    client.read_gatt_char.return_value = b"short"
    reader = TaelekClient(AsyncMock(return_value=client))
    with pytest.raises(ValueError):
        await reader.read_state()
    client.disconnect.assert_awaited_once()
    client.read_gatt_char.side_effect = [bytes(10), bytes(16)]
    assert len(await reader.read_settings()) == 2
    assert client.disconnect.await_count == 2


def test_timeout_minimum():
    with pytest.raises(ValueError):
        TaelekClient(AsyncMock(), timeout=9)


@pytest.mark.parametrize("command", [COMMAND_CLOSE, COMMAND_NORMAL])
async def test_runtime_command_reads_before_and_after_exactly_one_write(command):
    client = AsyncMock()
    after = struct.pack("<BBBBhHHH", 40, 0, 1, 0, 190, 210, 245, 65535)
    calls = []

    async def read(uuid):
        calls.append("read")
        return STATE if len(calls) == 1 else after

    async def write(uuid, data, *, response):
        calls.append("write")
        assert uuid == PRODUCT_COMMANDS and data == bytes([command]) and response is True

    client.read_gatt_char.side_effect = read
    client.write_gatt_char.side_effect = write
    before, observed = await TaelekClient(AsyncMock(return_value=client)).test_runtime_command(
        command
    )
    assert calls == ["read", "write", "read"]
    assert before.raw_data == STATE and observed.raw_data == after
    client.disconnect.assert_awaited_once()


@pytest.mark.parametrize("command", [0x62, 0x95, 0xA6, 0x83, 0, 256])
async def test_unverified_or_destructive_commands_rejected_before_connection(command):
    connector = AsyncMock()
    with pytest.raises(ValueError):
        await TaelekClient(connector).test_runtime_command(command)
    connector.assert_not_called()


async def test_command_pre_read_failure_prevents_any_write():
    client = AsyncMock()
    client.read_gatt_char.side_effect = OSError("pre-read failed")
    with pytest.raises(OSError, match="pre-read failed"):
        await TaelekClient(AsyncMock(return_value=client)).test_runtime_command(COMMAND_NORMAL)
    client.write_gatt_char.assert_not_called()
    client.disconnect.assert_awaited_once()


async def test_command_post_read_failure_never_retries_or_commits():
    client = AsyncMock()
    client.read_gatt_char.side_effect = [STATE, OSError("post-read failed")]
    with pytest.raises(OSError, match="post-read failed"):
        await TaelekClient(AsyncMock(return_value=client)).test_runtime_command(COMMAND_NORMAL)
    client.write_gatt_char.assert_awaited_once_with(PRODUCT_COMMANDS, b"\x84", response=True)
    client.disconnect.assert_awaited_once()


async def test_details_read_preserves_state_if_optional_characteristics_fail():
    client = AsyncMock()
    client.read_gatt_char.side_effect = [STATE, OSError("locked"), b"\x01", OSError("absent")]
    state = await TaelekClient(AsyncMock(return_value=client)).read_state_with_details()
    assert state.measured_floor_c == 24.5
    assert state.eco_program_mode is None
    assert state.buttons_raw == "01" and state.buttons2_raw is None
    client.disconnect.assert_awaited_once()
    client.write_gatt_char.assert_not_called()


async def test_details_read_returns_program_mode_without_exposing_network_key():
    client = AsyncMock()
    settings = bytearray(16)
    settings[7:15] = b"secret12"
    settings[15] = 2
    info = bytearray(17)
    info[14] = 64
    client.read_gatt_char.side_effect = [STATE, settings, b"\x01", b"\x02", info]
    state = await TaelekClient(AsyncMock(return_value=client)).read_state_with_details()
    assert state.eco_program_mode == 2
    assert state.buttons_raw == "01" and state.buttons2_raw == "02"
    assert state.device_version == 64
    assert "secret12" not in repr(state)
    assert [call.args[0] for call in client.read_gatt_char.await_args_list] == [
        PRODUCT_STATE_A,
        PRODUCT_PARAM_B,
        PRODUCT_BUTTONS,
        PRODUCT_BUTTONS_2,
        PRODUCT_INFO,
    ]
    client.write_gatt_char.assert_not_called()


async def test_eco_target_preserves_other_fields_and_restores_original():
    client = AsyncMock()
    raw = bytearray(range(18))
    raw[2:4] = struct.pack("<H", 190)
    current = bytes(raw)

    async def read(uuid):
        return STATE if uuid == PRODUCT_STATE_A else current

    async def write(uuid, data, *, response):
        nonlocal current
        assert uuid == PRODUCT_PARAM_B and response
        assert data[:2] == current[:2] and data[4:] == current[4:]
        current = data

    client.read_gatt_char.side_effect = read
    client.write_gatt_char.side_effect = write
    reader = TaelekClient(AsyncMock(return_value=client))
    assert (await reader.test_manual_eco_temperature(10.0))[:2] == (19.0, 10.0)
    assert (await reader.test_manual_eco_temperature(25.0))[:2] == (10.0, 25.0)
    assert (await reader.test_manual_eco_temperature(None))[:2] == (25.0, 19.0)
    assert current == raw
    assert client.write_gatt_char.await_count == 3


async def test_eco_target_pre_read_failure_blocks_write():
    client = AsyncMock()
    client.read_gatt_char.side_effect = [bytes(16), OSError("state unavailable")]
    with pytest.raises(OSError):
        await TaelekClient(AsyncMock(return_value=client)).test_manual_eco_temperature(10.0)
    client.write_gatt_char.assert_not_called()


async def test_eco_target_post_read_failure_keeps_backup_and_does_not_retry():
    client = AsyncMock()
    raw = bytearray(16)
    raw[2:4] = struct.pack("<H", 190)
    client.read_gatt_char.side_effect = [raw, STATE, OSError("readback failed")]
    reader = TaelekClient(AsyncMock(return_value=client))
    with pytest.raises(OSError):
        await reader.test_manual_eco_temperature(10.0)
    assert reader.original_manual_eco_c == 19.0
    client.write_gatt_char.assert_awaited_once()


async def test_eco_target_restore_without_backup_does_not_write():
    client = AsyncMock()
    client.read_gatt_char.side_effect = [bytes(16), STATE]
    with pytest.raises(ValueError, match="No original"):
        await TaelekClient(AsyncMock(return_value=client)).test_manual_eco_temperature(None)
    client.write_gatt_char.assert_not_called()
