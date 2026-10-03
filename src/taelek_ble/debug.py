"""Validate an explicit GATT experiment before any connection is opened."""

import math
from uuid import UUID


def validate_steps(steps):
    if not isinstance(steps, list) or not 1 <= len(steps) <= 32:
        raise ValueError("Provide 1–32 GATT steps")
    validated = []
    total_delay = 0.0
    waits = 0
    for step in steps:
        if not isinstance(step, dict):
            raise ValueError("Each step must be an object")  # noqa: TRY004 -- uniform validation API
        op = step.get("operation")
        allowed = {
            "read": {"operation", "uuid"},
            "write": {"operation", "uuid", "hex", "response"},
            "patch": {"operation", "uuid", "hex", "offset", "response"},
            "delay": {"operation", "seconds"},
            "wait_for_continue": {"operation", "timeout"},
        }
        if not isinstance(op, str) or op not in allowed or set(step) - allowed[op]:
            raise ValueError("Invalid operation or unexpected step fields")
        out = {"operation": op}
        if op == "wait_for_continue":
            waits += 1
            timeout = step.get("timeout", 120)
            if (
                isinstance(timeout, bool)
                or not isinstance(timeout, (int, float))
                or not (math.isfinite(timeout) and 1 <= timeout <= 180)
            ):
                raise ValueError("Confirmation wait must be 1–180 seconds")
            if waits > 1:
                raise ValueError("Only one confirmation wait per sequence")
            out["timeout"] = timeout
        elif op == "delay":
            seconds = step.get("seconds")
            if (
                isinstance(seconds, bool)
                or not isinstance(seconds, (int, float))
                or not math.isfinite(seconds)
                or not 0 <= seconds <= 5
            ):
                raise ValueError("Delay must be 0–5 seconds")
            total_delay += seconds
            out["seconds"] = seconds
        else:
            try:
                out["uuid"] = str(UUID(step["uuid"]))
            except (KeyError, ValueError, TypeError, AttributeError) as err:
                raise ValueError("A full characteristic UUID is required") from err
            if op in ("write", "patch"):
                try:
                    out["data"] = bytes.fromhex(step["hex"])
                except (KeyError, TypeError, ValueError) as err:
                    raise ValueError("Payload must be a hex string with whole bytes") from err
                if len(out["data"]) > 512:
                    raise ValueError("GATT payload exceeds 512 bytes")
                response = step.get("response", True)
                if not isinstance(response, bool):
                    raise ValueError("response must be a boolean")
                out["response"] = response
            if op == "patch":
                offset = step.get("offset")
                if isinstance(offset, bool) or not isinstance(offset, int) or not 0 <= offset < 512:
                    raise ValueError("Patch offset must be 0–511")
                if offset + len(out["data"]) > 512:
                    raise ValueError("Patch exceeds 512 bytes")
                out["offset"] = offset
        validated.append(out)
    if total_delay > 20:
        raise ValueError("Total delay exceeds 20 seconds")
    return validated
