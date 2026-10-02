# Taelek BLE protocol notes (APK-derived)

## Evidence basis

### MAI Smart 1.0.17

The Android bundle is plain/minified JavaScript and directly exposes protocol models, UUIDs and parsers.

### MAI Smart 2.0.3

The Android bundle is Hermes HBC v96. String-table inspection confirms all 18 legacy Taelek UUIDs remain present and adds two new UUIDs. Semantic strings such as `productStateA`, `productParamA`, `measuredFloor`, `networkKey`, `manualEco`, `productPassword`, and `nonce` remain present. Full control-flow validation is still required via Hermes decompilation.

## Bluetooth company identifier

Taelek Oy has Bluetooth SIG Company Identifier `0x048A` (1162 decimal). Confirm that E-2001 advertisements actually use it before hard-coding discovery solely to this ID.

## Discovery behavior in MAI Smart 1.0.17

The app accepts a peripheral when:

- `advertisement.localName` contains `Tael`
- RSSI is >= -90 dBm

The RSSI gate is app UX logic and should not be copied into HA discovery.

## Advertisement payload

In the old Android app the manufacturer payload is parsed directly. On non-Android the app strips the first two bytes first, consistent with platform-specific handling of company ID.

Payload after company ID removal:

| Offset | Length | Meaning | Encoding |
|---:|---:|---|---|
| 0 | 2 | temperature | signed int16 LE, ×0.1 °C; `FF FF` => unavailable |
| 2 | 1 | state/error/relay | high nibble state; bits 2–3 error; bits 0–1 relay |
| 3 | 1 | device type | see below |
| 4 | 4 | serial | uint32 LE |
| 8 | 10 | name | ASCII, padded |

Status byte:

```text
state = (b & 0xF0) >> 4
error = (b & 0x0C) >> 2
relay = b & 0x03
```

Device type mapping in 1.0.17:

```text
0x11 RADIATOR
0x22 RADIATOR2
0x33 RADIATOR3
0xEE RADIATOR_EE
else BASE
```

Do not yet assume which raw type E-2001 uses.

## Service UUIDs

### Info service

`2be32db1-5f6b-4cbd-8803-38d6dfb16490`

| Characteristic | UUID | Access |
|---|---|---|
| productInfo | `2be32db1-5f6b-4cbd-8813-8d6dfb164900` | R |
| productName | `2be32db1-5f6b-4cbd-8823-8d6dfb164900` | R |
| productLocation | `2be32db1-5f6b-4cbd-8833-8d6dfb164900` | RW |
| productStateA | `2be32db1-5f6b-4cbd-8843-8d6dfb164900` | R |
| productStateB | `2be32db1-5f6b-4cbd-8853-8d6dfb164900` | R |
| productCountersA | `2be32db1-5f6b-4cbd-8863-8d6dfb164900` | R |
| productCounterB | `2be32db1-5f6b-4cbd-8873-8d6dfb164900` | R |
| productCounterC | `2be32db1-5f6b-4cbd-8883-8d6dfb164900` | R |

### Settings service

`2be32db1-5f6b-5bd8-8033-8d6dfb164900`

| Characteristic | UUID | Access |
|---|---|---|
| productParamA | `2be32db1-5f6b-5bd8-8138-d6dfb1649000` | WR |
| productParamB | `2be32db1-5f6b-5bd8-8238-d6dfb1649000` | WR |
| productParamC | `2be32db1-5f6b-5bd8-8338-d6dfb1649000` | WR |
| productCommands | `2be32db1-5f6b-5bd8-8a38-d6dfb1649000` | W |
| productPassword | `2be32db1-5f6b-5bd8-8b38-d6dfb1649000` | RW |
| time | `2be32db1-5f6b-5bd8-8c38-d6dfb1649000` | WR |
| schedule | `2be32db1-5f6b-5bd8-8d8d-6dfb16490000` | unknown/model-specific |
| nonce | `2be32db1-5f6b-5bd8-8e8d-6dfb16490000` | R |

## productInfo

Sequential fields:

| Offset | Length | Field |
|---:|---:|---|
| 0 | 10 | productNumber (string) |
| 10 | 4 | hardwareNumber (string) |
| 14 | 1 | deviceVersion |
| 15 | 1 | bootloaderVersion |
| 16 | 1 | deviceType |

## productName

| Offset | Length | Field |
|---:|---:|---|
| 0 | 4 | serialNumber, uint32 LE |
| 4 | 15 | productName string |

## productStateA

12 bytes minimum:

| Offset | Len | Field | Encoding |
|---:|---:|---|---|
| 0 | 1 | humidity | uint8 |
| 1 | 1 | sensorErrorFlag | uint8; UI treats 0 as no error |
| 2 | 1 | operationMode | uint8 |
| 3 | 1 | valveState | 0 balanced, 1 heating, 2 cooling |
| 4 | 2 | setPoint | signed int16 LE ×0.1 °C |
| 6 | 2 | measuredAir | uint16 LE ×0.1 °C |
| 8 | 2 | measuredFloor | uint16 LE ×0.1 °C |
| 10 | 2 | measuredExternal | uint16 LE ×0.1 °C |

## productStateB

| Offset | Len | Field | Encoding |
|---:|---:|---|---|
| 0 | 2 | rawAir | uint16 LE ×0.1 |
| 2 | 2 | rawFloor | uint16 LE ×0.1 |

## productParamA

10 bytes in 1.0.17:

| Offset | Len | Field | Encoding |
|---:|---:|---|---|
| 0 | 2 | tempAir min/max | each byte: `T = raw*0.5 - 50` |
| 2 | 2 | tempFloor min/max | each byte: `T = raw*0.5 - 50` |
| 4 | 2 | PWM min/max | uint8 each, percent |
| 6 | 1 | floorCalib | `(raw - 14)/2` °C |
| 7 | 1 | airCalib | `(raw - 14)/2` °C |
| 8 | 1 | ledBrightness | uint8 percent |
| 9 | 1 | wirelessSensorAndWirelessEco | bit field |

8-bit temperature codec:

```text
decode: T = raw * 0.5 - 50
encode: raw = (T + 50) / 0.5
```

UI detection in 1.0.17:

```text
wireless temperature sensor enabled if (raw & 0x0F) == 0x04
wireless eco enabled               if (raw & 0xF0) == 0x40
```

When writing this byte, preserve all other bits.

## productParamB

15 bytes in 1.0.17:

| Offset | Len | Field | Encoding |
|---:|---:|---|---|
| 0 | 2 | autoEco | uint16 LE ×0.1 °C |
| 2 | 2 | manualEco | uint16 LE ×0.1 °C |
| 4 | 1 | mode | uint8 |
| 5 | 1 | valveProtection | uint8 |
| 6 | 1 | sensorType | uint8 |
| 7 | 8 | networkKey | raw 8 bytes |
| 15 | 1 | ecoMode | NOTE: model definition implies byte 15; total is therefore 16 bytes, not 15 |

Important correction: summing model lengths gives 16 bytes total. Do not hard-code 15. Validate on device and 2.0.3 decompilation.

Known mode values used by BASE/default UI:

```text
0 Floor
1 Air
3 Dual
4 PWM
6 Snow melting (offered on selected variants/firmware)
```

Sensor types:

```text
0 2 kΩ
1 10 kΩ
2 12.5 kΩ
3 15 kΩ
4 33 kΩ
```

Eco mode picker values:

```text
1 OFF
2 AUTO
```

## Settings write behavior

The 1.0.17 implementation reads the existing characteristic into a buffer, patches only selected fields, then writes the whole buffer back. Replicate this behavior. Never generate a settings blob from zeroes.

Multi-byte integers are little-endian.

## Commands

One-byte writes to `productCommands`:

| Command | Value |
|---|---:|
| disconnect | `0x55` |
| wink | `0x51` |
| open | `0x62` |
| close | `0x73` |
| normal | `0x84` |
| factory reset | `0x95` |
| counter reset | `0xA6` |
| save confirmation | `0x83` |

Do not expose destructive commands in the first HA version.

## Time

The old app writes four bytes:

```text
hour, minute, second, ISO weekday
```

Local wall time, not UTC or a Unix timestamp. ISO weekday is Monday=1 through
Sunday=7. MAI Smart 2.0.3 F8549 confirms the same order. HA 0.1.7 sends this
once per active session using HA's configured timezone; see `CLOCK_SYNC.md`.

## Authentication / nonce

`productPassword` and `nonce` are present in the old model. Old 1.0.17 protocol paths used for ordinary settings do not obviously require them. This must be explicitly rechecked in 2.0.3 and on hardware before claiming that writes are unauthenticated.

## MAI Smart 2.0.3 UUID delta

All 18 UUIDs above remain present in HBC v96. Two additional Taelek-pattern UUIDs were found:

```text
2be32db1-5f6b-5bd0-0e8d-6dfb16490000
2be32db1-5f6b-5bd9-9e8d-6dfb16490000
```

Meaning unknown until HBC decompilation.
