"""Read-only sessions over a caller-supplied, connected Bleak-compatible client."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Protocol

from .codec import decode_param_a, decode_param_b, decode_state_a
from .const import PRODUCT_PARAM_A, PRODUCT_PARAM_B, PRODUCT_STATE_A
from .models import ParamA, ParamB, StateA

_LOGGER = logging.getLogger(__name__)


class ReadTransport(Protocol):
    async def read_gatt_char(self, characteristic: str) -> bytearray: ...
    async def disconnect(self) -> bool: ...


class TaelekClient:
    """The connector must create a fresh connected client for each session.

    No scanner and no write API. Read errors and cancellation propagate to the
    caller; cleanup must not hide them. The deadline covers connection and reads.
    """

    def __init__(
        self,
        connector: Callable[[], Awaitable[ReadTransport]],
        *,
        timeout: float = 45,
    ):
        if timeout < 10:
            raise ValueError("Session timeout must be at least 10 seconds")
        self._connector = connector
        self._timeout = timeout
        self._lock = asyncio.Lock()

    async def _read(self, *characteristics: str) -> list[bytes]:
        async with self._lock:
            client = None
            try:
                async with asyncio.timeout(self._timeout):
                    client = await self._connector()
                    return [bytes(await client.read_gatt_char(uuid)) for uuid in characteristics]
            finally:
                if client is not None:
                    try:
                        async with asyncio.timeout(10):
                            await client.disconnect()
                    except Exception:
                        _LOGGER.debug("BLE disconnect failed", exc_info=True)

    async def read_state(self, *, device_type: int | None = None) -> StateA:
        return decode_state_a((await self._read(PRODUCT_STATE_A))[0], device_type=device_type)

    async def read_settings(self) -> tuple[ParamA, ParamB]:
        a, b = await self._read(PRODUCT_PARAM_A, PRODUCT_PARAM_B)
        return decode_param_a(a), decode_param_b(b)
