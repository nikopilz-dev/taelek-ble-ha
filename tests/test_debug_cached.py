"""Cached experiments retain immutable session reads, never add hidden reads."""

from unittest.mock import AsyncMock

import pytest

from taelek_ble.client import TaelekClient
from taelek_ble.const import PRODUCT_COMMANDS, PRODUCT_PARAM_A, PRODUCT_PARAM_B

NONCE = "2be32db1-5f6b-5bd8-8e8d-6dfb16490000"
LOCATION = "2be32db1-5f6b-4cbd-8833-8d6dfb164900"


async def test_cached_transaction_uses_initial_buffers_without_intervening_reads():
    raw = {
        PRODUCT_PARAM_A: bytes(10),
        PRODUCT_PARAM_B: bytes(range(16)),
        NONCE: bytes(range(16)),
        LOCATION: bytes(range(19)),
    }
    io = []
    transport = AsyncMock()

    async def read(uuid):
        io.append(("read", uuid))
        return bytearray(raw[uuid])

    async def write(uuid, payload, *, response):
        io.append(("write", uuid, payload))

    transport.read_gatt_char.side_effect = read
    transport.write_gatt_char.side_effect = write
    steps = [
        {"operation": "read", "uuid": u, "expected_length": len(value)} for u, value in raw.items()
    ]
    steps += [{"operation": "write_cached", "uuid": u, "source_step": i} for i, u in enumerate(raw)]
    steps[5].update(offset=2, hex="6400")
    steps.append({"operation": "write", "uuid": PRODUCT_COMMANDS, "hex": "83"})
    result = await TaelekClient(AsyncMock(return_value=transport)).debug_gatt(steps)
    assert result["success"]
    assert [operation[0] for operation in io] == ["read"] * 4 + ["write"] * 5
    assert io[6][2] == raw[NONCE]
    assert io[5][2] == raw[PRODUCT_PARAM_B][:2] + b"\x64\x00" + raw[PRODUCT_PARAM_B][4:]
    transport.disconnect.assert_awaited_once()


async def test_cache_is_snapshot_and_scoped_to_each_session():
    transport = AsyncMock()
    mutable = bytearray(b"\x01\x02")

    async def read(uuid):
        if transport.read_gatt_char.await_count == 2:
            mutable[:] = b"\x03\x04"
        return mutable

    transport.read_gatt_char.side_effect = read
    client = TaelekClient(AsyncMock(return_value=transport))
    result = await client.debug_gatt(
        [
            {"operation": "read", "uuid": NONCE},
            {"operation": "read", "uuid": NONCE},
            {"operation": "write_cached", "uuid": NONCE, "source_step": 0},
        ]
    )
    assert result["success"]
    transport.write_gatt_char.assert_awaited_once_with(NONCE, b"\x01\x02", response=True)
    transport.read_gatt_char.side_effect = None
    transport.read_gatt_char.return_value = b"\x05\x06"
    await client.debug_gatt(
        [
            {"operation": "read", "uuid": NONCE},
            {"operation": "write_cached", "uuid": NONCE, "source_step": 0},
        ]
    )
    assert transport.write_gatt_char.await_args.args[1] == b"\x05\x06"


@pytest.mark.parametrize(
    "bad",
    [
        {"source_step": -1},
        {"source_step": 2},
        {"source_step": True},
        {"source_step": "0"},
        {"source_step": 0, "uuid": PRODUCT_PARAM_B},
        {"source_step": 0, "hex": "64"},
        {"source_step": 0, "offset": 2},
    ],
)
async def test_invalid_reference_or_patch_prevents_connection(bad):
    connector = AsyncMock()
    with pytest.raises(ValueError):
        await TaelekClient(connector).debug_gatt(
            [
                {"operation": "read", "uuid": NONCE},
                {"operation": "write_cached", "uuid": NONCE, **bad},
            ]
        )
    connector.assert_not_called()


@pytest.mark.parametrize("guard", [{"expected_length": 16}, {"expected_hex": "0102"}])
async def test_read_guard_mismatch_blocks_all_following_settings_writes(guard):
    transport = AsyncMock()
    transport.read_gatt_char.return_value = b"\x01"
    result = await TaelekClient(AsyncMock(return_value=transport)).debug_gatt(
        [
            {"operation": "read", "uuid": NONCE, **guard},
            {"operation": "write_cached", "uuid": NONCE, "source_step": 0},
            {"operation": "write", "uuid": PRODUCT_COMMANDS, "hex": "83"},
        ]
    )
    assert not result["success"] and len(result["steps"]) == 1
    transport.write_gatt_char.assert_not_called()
    transport.disconnect.assert_awaited_once()


async def test_failed_cached_write_stops_before_confirmation_without_retry():
    transport = AsyncMock()
    transport.read_gatt_char.return_value = bytes(16)
    transport.write_gatt_char.side_effect = OSError("ACK lost")
    result = await TaelekClient(AsyncMock(return_value=transport)).debug_gatt(
        [
            {"operation": "read", "uuid": NONCE},
            {"operation": "write_cached", "uuid": NONCE, "source_step": 0},
            {"operation": "write", "uuid": PRODUCT_COMMANDS, "hex": "83"},
        ]
    )
    assert not result["success"] and len(result["steps"]) == 2
    assert result["steps"][1]["status"] == "write attempted; effect may be unknown"
    transport.read_gatt_char.assert_awaited_once()
    transport.write_gatt_char.assert_awaited_once()
    transport.disconnect.assert_awaited_once()
