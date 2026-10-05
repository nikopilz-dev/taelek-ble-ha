"""GATT reads and explicit, bounded command experiments."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import replace
from datetime import UTC, datetime
from typing import Protocol

from .clock import encode_time
from .codec import decode_param_a, decode_param_b, decode_state_a, patch_param_b
from .const import (
    COMMAND_CLOSE,
    COMMAND_NORMAL,
    PRODUCT_BUTTONS,
    PRODUCT_BUTTONS_2,
    PRODUCT_COMMANDS,
    PRODUCT_INFO,
    PRODUCT_PARAM_A,
    PRODUCT_PARAM_B,
    PRODUCT_STATE_A,
    TIME,
)
from .debug import validate_steps
from .models import ParamA, ParamB, StateA

_LOGGER = logging.getLogger(__name__)


class ReadTransport(Protocol):
    async def read_gatt_char(self, characteristic: str) -> bytearray: ...
    async def write_gatt_char(
        self, characteristic: str, data: bytes, *, response: bool
    ) -> None: ...
    async def disconnect(self) -> bool: ...


class TaelekClient:
    """The connector must create a fresh connected client for each session.

    No scanner. A supplied local clock enables one clock write per session;
    without it, reads remain read-only. Errors and cancellation propagate to the
    caller; cleanup must not hide them. The deadline covers the whole session.
    """

    def __init__(
        self,
        connector: Callable[[], Awaitable[ReadTransport]],
        *,
        timeout: float = 45,
        clock: Callable[[], datetime] | None = None,
    ):
        if timeout < 10:
            raise ValueError("Session timeout must be at least 10 seconds")
        self._connector = connector
        self._timeout = timeout
        self._clock = clock
        self._lock = asyncio.Lock()
        self.original_manual_eco_c = None

    async def debug_gatt(self, steps, *, sync_time: bool = True, pause=None):
        """Execute user-provided steps once in one serialized connection.

        Report partial results on failure. Never retry or infer a save command.
        The clock prelude is reported separately and can be skipped for A/B tests.
        Raw reads are returned only to the caller, never logged or published.
        """
        steps = validate_steps(steps)
        if not isinstance(sync_time, bool):
            raise TypeError("sync_time must be a boolean")
        wait_budget = sum(s["timeout"] for s in steps if s["operation"] == "wait_for_continue")
        if wait_budget and not callable(pause):
            raise ValueError("A confirmation callback is required before connecting")
        result = {"success": False, "steps": [], "clock_sync": {"status": "not started"}}
        cached_reads = {}
        try:
            async with self._session(
                sync_time=sync_time,
                clock_result=result["clock_sync"],
                timeout=self._timeout + wait_budget,
            ) as client:
                for index, step in enumerate(steps):
                    op = step["operation"]
                    observed = {
                        "index": index,
                        "operation": op,
                        "status": "started",
                        "started_at": datetime.now(UTC).isoformat(),
                    }
                    result["steps"].append(observed)
                    if op == "wait_for_continue":
                        observed["status"] = "waiting for explicit continuation"
                        async with asyncio.timeout(step["timeout"]):
                            await pause(result)
                    elif op == "delay":
                        await asyncio.sleep(step["seconds"])
                    else:
                        uuid = step["uuid"]
                        observed["uuid"] = uuid
                        if op == "read":
                            raw = bytes(await client.read_gatt_char(uuid))
                            observed["hex"] = raw.hex()
                            if "expected_length" in step and len(raw) != step["expected_length"]:
                                raise ValueError("Read length did not match expected length")
                            if "expected_data" in step and raw != step["expected_data"]:
                                raise ValueError("Read buffer did not match expected bytes")
                            cached_reads[index] = raw
                        else:
                            payload = step["data"]
                            if op in ("patch", "write_cached"):
                                if op == "write_cached":
                                    original = cached_reads[step["source_step"]]
                                    observed["source_step"] = step["source_step"]
                                    if len(original) > 512:
                                        raise ValueError("Cached buffer exceeds 512 bytes")
                                else:
                                    original = bytes(await client.read_gatt_char(uuid))
                                observed["original_hex"] = original.hex()
                                offset = step["offset"]
                                if offset + len(payload) > len(original):
                                    raise ValueError("Patch exceeds characteristic length")
                                updated = bytearray(original)
                                updated[offset : offset + len(payload)] = payload
                                payload = bytes(updated)
                            observed["written_hex"] = payload.hex()
                            observed["status"] = "write attempted; effect may be unknown"
                            await client.write_gatt_char(uuid, payload, response=step["response"])
                            observed["bytes_written"] = len(payload)
                            observed["response"] = step["response"]
                    observed["status"] = "completed"
                    observed["completed_at"] = datetime.now(UTC).isoformat()
            result["success"] = True
        except Exception as err:  # noqa: BLE001 -- return partial raw-transport results
            result["error_type"] = type(err).__name__
            result["error"] = str(err)
            result["retry"] = "none"
        return result

    async def test_manual_eco_temperature(self, target, *, device_type=None):
        """Patch only manualEco; no mode switch, commit, retry or automatic restore.

        None explicitly restores the first value read during this client lifetime.
        Keep that backup even if the write or subsequent read fails.
        """
        if target is not None and target not in (10.0, 25.0):
            raise ValueError("Experiment targets are 10 or 25 Celsius")
        async with self._session() as client:
            raw = bytes(await client.read_gatt_char(PRODUCT_PARAM_B))
            before = decode_param_b(raw)
            state_before = decode_state_a(
                bytes(await client.read_gatt_char(PRODUCT_STATE_A)), device_type=device_type
            )
            if target is None:
                if self.original_manual_eco_c is None:
                    raise ValueError("No original ECO target recorded in this session")
                target = self.original_manual_eco_c
            elif self.original_manual_eco_c is None:
                self.original_manual_eco_c = before.manual_eco_c
            payload = patch_param_b(raw, manual_eco_c=target)
            await client.write_gatt_char(PRODUCT_PARAM_B, payload, response=True)
            after = decode_param_b(bytes(await client.read_gatt_char(PRODUCT_PARAM_B)))
            state_after = decode_state_a(
                bytes(await client.read_gatt_char(PRODUCT_STATE_A)), device_type=device_type
            )
            return before.manual_eco_c, after.manual_eco_c, state_before, state_after

    @asynccontextmanager
    async def _session(self, *, sync_time=True, clock_result=None, timeout=None):
        async with self._lock:
            client = None
            try:
                async with asyncio.timeout(self._timeout if timeout is None else timeout):
                    client = await self._connector()
                    if clock_result is None:
                        clock_result = {}
                    if sync_time and self._clock is not None:
                        clock_result.update(uuid=TIME, status="preparing")
                        try:
                            local_time = self._clock()
                            payload = encode_time(local_time)
                            clock_result.update(
                                status="write attempted; effect may be unknown",
                                hex=payload.hex(),
                                local_time=local_time.isoformat(),
                                response=True,
                            )
                            await client.write_gatt_char(TIME, payload, response=True)
                        except Exception as err:
                            clock_result["error"] = str(err)
                            raise OSError(f"Taelek clock synchronization failed: {err}") from err
                        clock_result["status"] = "completed; device clock not read back"
                    else:
                        clock_result["status"] = (
                            "skipped by request"
                            if not sync_time
                            else "no clock provider configured"
                        )
                    yield client
            finally:
                if client is not None:
                    try:
                        async with asyncio.timeout(10):
                            await client.disconnect()
                    except Exception:
                        _LOGGER.debug("BLE disconnect failed", exc_info=True)

    async def _read(self, *characteristics: str) -> list[bytes]:
        async with self._session() as client:
            return [bytes(await client.read_gatt_char(uuid)) for uuid in characteristics]

    async def read_state_with_details(self, *, device_type: int | None = None) -> StateA:
        """Read state and optional ECO/button evidence after the clock prelude.

        Optional characteristic failures leave the successfully read state usable.
        Network-key bytes from Param B are never returned in diagnostic fields.
        """
        async with self._session() as client:
            state = decode_state_a(
                bytes(await client.read_gatt_char(PRODUCT_STATE_A)), device_type=device_type
            )
            details = {}
            for uuid, field in (
                (PRODUCT_PARAM_B, "eco_program_mode"),
                (PRODUCT_BUTTONS, "buttons_raw"),
                (PRODUCT_BUTTONS_2, "buttons2_raw"),
                (PRODUCT_INFO, "device_version"),
            ):
                try:
                    data = bytes(await client.read_gatt_char(uuid))
                    if uuid == PRODUCT_PARAM_B:
                        details[field] = decode_param_b(data).eco_mode
                    elif uuid == PRODUCT_INFO:
                        if len(data) < 17:
                            raise ValueError("productInfo too short")
                        details[field] = data[14]
                    else:
                        details[field] = data.hex()
                except Exception:
                    _LOGGER.debug("Optional Taelek detail read failed: %s", uuid, exc_info=True)
            return replace(state, **details)

    async def read_state(self, *, device_type: int | None = None) -> StateA:
        return decode_state_a((await self._read(PRODUCT_STATE_A))[0], device_type=device_type)

    async def test_runtime_command(
        self, command: int, *, device_type: int | None = None
    ) -> tuple[StateA, StateA]:
        """Send documented CLOSE or NORMAL once; ECO semantics are unverified.

        A successful pre-read is required. Never retry a write, send save
        confirmation, or replay the command after an ambiguous failure.
        The returned states are observations, not proof of semantic success.
        """
        if command not in (COMMAND_CLOSE, COMMAND_NORMAL):
            raise ValueError("Only CLOSE and NORMAL are allowed in command experiments")
        async with self._session() as client:
            before = decode_state_a(
                bytes(await client.read_gatt_char(PRODUCT_STATE_A)), device_type=device_type
            )
            await client.write_gatt_char(PRODUCT_COMMANDS, bytes([command]), response=True)
            await asyncio.sleep(0.5)
            after = decode_state_a(
                bytes(await client.read_gatt_char(PRODUCT_STATE_A)), device_type=device_type
            )
            return before, after

    async def read_settings(self) -> tuple[ParamA, ParamB]:
        a, b = await self._read(PRODUCT_PARAM_A, PRODUCT_PARAM_B)
        return decode_param_a(a), decode_param_b(b)
