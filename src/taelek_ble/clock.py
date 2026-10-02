"""MAI Smart's four-byte local weekly clock, not a Unix timestamp."""

from datetime import datetime


def encode_time(local_time: datetime) -> bytes:
    """Encode local hour/minute/second and ISO weekday (Monday=1, Sunday=7).

    Require an explicit timezone so the caller, rather than the host OS,
    determines the thermostat's local time. No date or UTC offset is transmitted.
    """
    if local_time.tzinfo is None or local_time.utcoffset() is None:
        raise ValueError("Thermostat clock requires timezone-aware local time")
    return bytes((local_time.hour, local_time.minute, local_time.second, local_time.isoweekday()))
