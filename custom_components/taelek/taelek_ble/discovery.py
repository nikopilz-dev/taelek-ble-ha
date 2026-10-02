"""Conservative, dependency-free selection and stable identity helpers."""

from collections.abc import Mapping

from .advertisement import decode_manufacturer_payload
from .const import TAELEK_COMPANY_ID
from .models import Advertisement


def parse_discovery(
    local_name: str | None, manufacturer_data: Mapping[int, bytes]
) -> Advertisement | None:
    """Prefer known company ID; accept one exact-layout payload under a Tael name.

    The fallback supports unverified company IDs without guessing between multiple
    manufacturer records. Both matchers remain hypotheses for E-2001 hardware.
    """
    payload = manufacturer_data.get(TAELEK_COMPANY_ID)
    if payload is None and local_name and local_name.startswith("Tael"):
        candidates = [data for data in manufacturer_data.values() if len(data) == 18]
        if len(candidates) == 1:
            payload = candidates[0]
    if payload is None:
        return None
    try:
        return decode_manufacturer_payload(payload)
    except (ValueError, TypeError):
        return None


def device_unique_id(advertisement: Advertisement, address: str) -> str:
    if advertisement.serial not in (0, 0xFFFFFFFF):
        return f"serial_{advertisement.serial:08x}"
    return f"address_{address.lower()}"
