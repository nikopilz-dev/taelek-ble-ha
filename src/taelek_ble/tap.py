"""Explicit FW66-derived Tap experiments; cipher profile awaits device validation."""

import math
import struct


def validate_tap(step):
    command = step.get("command")
    if isinstance(command, bool) or not isinstance(command, int) or command not in (1, 2, 3, 4):
        raise ValueError("Tap command must be 1, 2, 3 or 4")
    firmware = step.get("expected_firmware")
    if isinstance(firmware, bool) or not isinstance(firmware, int) or firmware not in (54, 66):
        raise ValueError("Tap experiments require expected_firmware 54 or 66")
    try:
        key = bytes.fromhex(step["key_hex"])
    except (KeyError, TypeError, ValueError) as err:
        raise ValueError("Tap key_hex must contain 16 bytes") from err
    if len(key) != 16:
        raise ValueError("Tap key_hex must contain 16 bytes")
    dry_run = step.get("dry_run", True)
    if not isinstance(dry_run, bool):
        raise ValueError("Tap dry_run must be a boolean")  # noqa: TRY004 -- debug validation API
    target = step.get("target_c")
    if command == 2:
        if (
            isinstance(target, bool)
            or not isinstance(target, (int, float))
            or not math.isfinite(target)
            or not 5 <= target <= 40
            or abs(target * 10 - round(target * 10)) > 1e-8
        ):
            raise ValueError("Tap target_c must be 5–40 Celsius in 0.1 degree steps")
    elif "target_c" in step:
        raise ValueError("Only Tap command 2 takes target_c")
    # Fail before connecting if the optional backend is unavailable.
    crypto_backend()
    return {
        "operation": "tap",
        "command": command,
        "expected_firmware": firmware,
        "key": key,
        "dry_run": dry_run,
        "target_c": target,
    }


def crypto_backend():
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESCCM
    except ImportError as err:
        raise ValueError("Tap experiments require the cryptography backend") from err
    return AESCCM


def encode_tap(command, nonce, key, *, target_c=None):
    """Candidate standard CCM profile, direct key/nonce byte order, no AAD.

    FW66 passes 16 ciphertext bytes and a zero MIC to its decrypt function.
    Its caller ignores the crypto result. We send only ciphertext, never the
    computed MIC; this does not claim authenticated or device-verified control.
    """
    if len(nonce) != 13 or len(key) != 16:
        raise ValueError("Tap requires a 13-byte nonce and a 16-byte key")
    if command not in (1, 2, 3, 4):
        raise ValueError("Invalid Tap command")
    plain = bytearray(16)
    plain[4:7] = b"Tap"
    plain[7] = command
    if command == 2:
        if target_c is None or not math.isfinite(target_c) or not 5 <= target_c <= 40:
            raise ValueError("Tap command 2 requires a bounded target")
        if abs(target_c * 10 - round(target_c * 10)) > 1e-8:
            raise ValueError("Tap temperature requires 0.1 degree steps")
        struct.pack_into("<h", plain, 8, round(target_c * 10))
    elif target_c is not None:
        raise ValueError("Only Tap command 2 takes a temperature")
    encrypted = crypto_backend()(key, tag_length=4).encrypt(nonce, bytes(plain), None)
    return encrypted[:16]
