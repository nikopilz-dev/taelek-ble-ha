# Confidence / open questions

## High confidence — directly visible in MAI Smart 1.0.17 JS

- Service and characteristic UUIDs listed in `PROTOCOL.md`.
- Little-endian integer parsing.
- Advertisement layout used by old Android app.
- `productStateA` field order and scaling.
- `productParamA/B` field order and scaling.
- 8-bit min/max temperature encoding.
- Calibration encoding.
- wireless sensor / wireless eco tests used by UI.
- command byte values including `0x83` save confirmation.
- device type mapping used by old scanner.
- MAI Smart scanner checked for local name containing `Tael`.

## Medium confidence — corroborated by 2.0.3 strings/UUIDs but not yet decompiled

- Legacy protocol remains wire-compatible in 2.0.3.
- E-2001-era BASE thermostat support still uses the same structures.
- Password/nonce remain optional for legacy thermostat settings.

## Unconfirmed until physical E-2001 BLE test

- E-2001 raw device type.
- Exact advertised local name.
- Whether E-2001 uses Bluetooth company ID `0x048A` in actual manufacturer advertisements.
- Whether advertisement temperature equals floor temperature in Floor mode.
- Sentinel values for measuredAir/Floor/External in GATT state.
- Whether state/relay bit values have additional semantics beyond what old UI exposes.
- GATT write confirmation flow for E-2001 firmware currently sold.
- Whether floor min/max changes require knob rotation confirmation and exact sequence.
- Whether an active GATT connection works through the user's current HA BLE gateway/proxy.

## Unknown protocol areas

- Two new UUIDs in MAI Smart 2.0.3.
- Wireless eco broadcast packet format / mesh-like forwarding.
- Schedule characteristic structure beyond old app's split handling.
- Password/nonce usage in newer device classes.
