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
            "read": {"operation", "uuid", "expected_hex", "expected_length"},
            "write": {"operation", "uuid", "hex", "response"},
            "patch": {"operation", "uuid", "hex", "offset", "response"},
            "write_cached": {"operation", "uuid", "source_step", "hex", "offset", "response"},
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
            if op == "read":
                if "expected_length" in step:
                    length = step["expected_length"]
                    if (
                        isinstance(length, bool)
                        or not isinstance(length, int)
                        or not 0 <= length <= 512
                    ):
                        raise ValueError("Expected length must be 0–512 bytes")
                    out["expected_length"] = length
                if "expected_hex" in step:
                    try:
                        out["expected_data"] = bytes.fromhex(step["expected_hex"])
                    except (TypeError, ValueError) as err:
                        raise ValueError("Expected payload must be a hex string") from err
                    if len(out["expected_data"]) > 512:
                        raise ValueError("Expected payload exceeds 512 bytes")
                    if (
                        "expected_length" in out
                        and len(out["expected_data"]) != out["expected_length"]
                    ):
                        raise ValueError("Expected payload and length disagree")
            if op == "write_cached":
                source = step.get("source_step")
                if (
                    isinstance(source, bool)
                    or not isinstance(source, int)
                    or not 0 <= source < len(validated)
                    or validated[source]["operation"] != "read"
                    or validated[source]["uuid"] != out["uuid"]
                ):
                    raise ValueError("Cached source must be an earlier read of the same UUID")
                if ("hex" in step) != ("offset" in step):
                    raise ValueError("Cached patch requires both hex and offset")
                out["source_step"] = source
            if op in ("write", "patch", "write_cached"):
                try:
                    out["data"] = bytes.fromhex(
                        step.get("hex", "") if op == "write_cached" else step["hex"]
                    )
                except (KeyError, TypeError, ValueError) as err:
                    raise ValueError("Payload must be a hex string with whole bytes") from err
                if len(out["data"]) > 512:
                    raise ValueError("GATT payload exceeds 512 bytes")
                response = step.get("response", True)
                if not isinstance(response, bool):
                    raise ValueError("response must be a boolean")
                out["response"] = response
            if op in ("patch", "write_cached"):
                offset = step.get("offset", 0) if op == "write_cached" else step.get("offset")
                if isinstance(offset, bool) or not isinstance(offset, int) or not 0 <= offset < 512:
                    raise ValueError("Patch offset must be 0–511")
                if offset + len(out["data"]) > 512:
                    raise ValueError("Patch exceeds 512 bytes")
                out["offset"] = offset
        validated.append(out)
    if total_delay > 20:
        raise ValueError("Total delay exceeds 20 seconds")
    return validated
