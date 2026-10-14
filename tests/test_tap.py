"""FW66-derived explicit experiments: cipher vector, gates, ordering and no replay."""

import struct
from unittest.mock import AsyncMock

import pytest

from taelek_ble.client import TaelekClient
from taelek_ble.const import NONCE, PRODUCT_INFO, PRODUCT_PARAM_B, PRODUCT_PASSWORD, PRODUCT_STATE_A
from taelek_ble.debug import validate_steps
from taelek_ble.tap import encode_tap

KEY = bytes(range(16))
NONCE_VALUE = bytes(range(16))
INFO = bytes(10) + b"1.6S" + bytes([54, 14, 10])
PARAMS = struct.pack("<HHBBB8sB", 250, 220, 0, 0, 1, b"GROUP123", 2)
STATE = bytes(12)


def step(**changes):
    return {
        "operation": "tap", "command": 1, "expected_firmware": 54,
        "key_hex": KEY.hex(), **changes,
    }


def transport(reads=None):
    client = AsyncMock()
    client.read_gatt_char.side_effect = reads or [INFO, PARAMS, STATE, NONCE_VALUE]
    return client


def test_ciphertext_matches_independent_ctr_block_vector():
    # CCM L=2 -> CTR block 01 || nonce13 || counter0001. Ciphertext is plaintext
    # XOR AES(block). This checks actual wire bytes independently of CCM tags.
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    nonce = NONCE_VALUE[:13]
    encryptor = Cipher(algorithms.AES(KEY), modes.ECB()).encryptor()
    stream = encryptor.update(b"\x01" + nonce + b"\x00\x01") + encryptor.finalize()
    plain = bytearray(16)
    plain[4:7] = b"Tap"
    plain[7] = 2
    struct.pack_into("<h", plain, 8, 215)
    assert encode_tap(2, nonce, KEY, target_c=21.5) == bytes(
        left ^ right for left, right in zip(plain, stream, strict=True)
    )


@pytest.mark.parametrize("changes", [
    {"command": True}, {"command": 0}, {"command": 5}, {"key_hex": "00"},
    {"expected_firmware": 55}, {"expected_firmware": 54.0},
    {"dry_run": "false"}, {"target_c": 22},
    {"command": 2}, {"command": 2, "target_c": float("nan")},
    {"command": 2, "target_c": 21.55}, {"command": 2, "target_c": 41},
    {"unexpected": True},
])
def test_invalid_plan_rejected(changes):
    with pytest.raises(ValueError):
        validate_steps([step(**changes)])


async def test_dry_run_reads_fresh_context_without_any_writes():
    t = transport()
    result = await TaelekClient(AsyncMock(return_value=t)).debug_gatt(
        [step()], sync_time=False
    )
    assert result["success"]
    assert [a.args[0] for a in t.read_gatt_char.await_args_list] == [
        PRODUCT_INFO, PRODUCT_PARAM_B, PRODUCT_STATE_A, NONCE
    ]
    t.write_gatt_char.assert_not_awaited()
    t.disconnect.assert_awaited_once()
    assert result["steps"][0]["outcome"] == "prepared only; no Tap write"
    assert "key_hex" not in str(result) and "'key':" not in str(result)


async def test_tap_requires_clock_disabled_before_connection():
    connector = AsyncMock()
    with pytest.raises(ValueError, match="sync_time"):
        await TaelekClient(connector).debug_gatt([step()])
    connector.assert_not_awaited()


@pytest.mark.parametrize("info", [INFO[:16], INFO[:14] + bytes([66, 14, 10]),
    bytes(10) + b"1.7S" + INFO[14:], INFO[:16] + b"\x03"])
async def test_identity_gate_stops_before_nonce_or_write(info):
    t = transport([info])
    result = await TaelekClient(AsyncMock(return_value=t)).debug_gatt(
        [step(dry_run=False)], sync_time=False
    )
    assert not result["success"]
    t.read_gatt_char.assert_awaited_once_with(PRODUCT_INFO)
    t.write_gatt_char.assert_not_awaited()


async def test_pwm_temperature_is_rejected():
    params = bytearray(PARAMS)
    params[4] = 4
    t = transport([INFO, bytes(params)])
    result = await TaelekClient(AsyncMock(return_value=t)).debug_gatt(
        [step(command=2, target_c=21.5, dry_run=False)], sync_time=False
    )
    assert not result["success"]
    t.write_gatt_char.assert_not_awaited()


@pytest.mark.parametrize("nonce", [bytes(13), bytes(15), bytes(17)])
async def test_nonce_length_must_match_wire_context(nonce):
    t = transport([INFO, PARAMS, STATE, nonce])
    result = await TaelekClient(AsyncMock(return_value=t)).debug_gatt(
        [step(dry_run=False)], sync_time=False
    )
    assert not result["success"]
    t.write_gatt_char.assert_not_awaited()


async def test_explicit_write_uses_only_password_with_prewrite_nonce():
    t = transport([INFO, PARAMS, STATE, NONCE_VALUE, bytes(16), STATE, PARAMS])
    result = await TaelekClient(AsyncMock(return_value=t)).debug_gatt(
        [step(command=3, dry_run=False)], sync_time=False
    )
    assert result["success"]
    t.write_gatt_char.assert_awaited_once_with(
        PRODUCT_PASSWORD, encode_tap(3, NONCE_VALUE[:13], KEY), response=True
    )
    calls = t.method_calls
    assert calls[3].args == (NONCE,)
    assert calls[4].args[0] == PRODUCT_PASSWORD
    assert "unverified" in result["steps"][0]["outcome"]


@pytest.mark.parametrize("failure", ["write", "readback"])
async def test_ambiguous_failure_never_replays(failure):
    t = transport([INFO, PARAMS, STATE, NONCE_VALUE, OSError("lost connection")])
    if failure == "write":
        t.write_gatt_char.side_effect = OSError("lost connection")
    result = await TaelekClient(AsyncMock(return_value=t)).debug_gatt(
        [step(command=3, dry_run=False)], sync_time=False
    )
    assert not result["success"] and result["retry"] == "none"
    assert t.write_gatt_char.await_count == 1
    t.disconnect.assert_awaited_once()
