# MAI Smart 2.0.3 validation – 2026-10-02

APK and extracted bundle SHA-256 hashes match `../evidence/checksums.txt`.
The bundle is HBC v96, legacy layout, 14,080 functions and 1,752 Metro modules.
Local hermes-decomp v0.2.4 successfully produced a deep/stable decompilation and
instruction disassembly. Tool provenance is in `../evidence/hermes-tool.json`.

## Reproducible evidence

- `../evidence/v2-model-excerpts.txt`: compact excerpts with Metro module and line references.
- `../evidence/v2-selected-disassembly.txt`: selected instruction listings with function IDs/offsets.
- `../evidence/parser-v2.js`: targeted decompilation of F8411.
- `../evidence/settings-v2.js`: targeted decompilation of F8442.
- `../evidence/settings-read-v2.js`: targeted decompilation of F8415.

Whole-bundle output is retained locally but excluded from source distribution.
The CLI `xref --query productStateA` returned zero references despite its presence
in decompiled object literals. Model-module and disassembly inspection were used instead.
Some generator/iterator recovery is visibly incorrect; control-flow claims below
are limited accordingly. Instruction listings take precedence over misleading generated JS.

## Findings against the work-order invariants

1. **UUIDs:** Module 1350 retains the legacy info/settings services and characteristics.
   New UUIDs are mapped in the same model, see item 7.
2. **State A layout:** Module 1350 retains offsets/lengths: humidity 1, error 1,
   operation mode 1, valve 1, setpoint 2, air 2, floor 2, external 2.
   Temperature scale remains 0.1. Valve display values remain 0 balanced,
   1 warming, 2 cooling. **Signedness is not entirely unchanged:** F8411
   (bytecode offset `0x1cd816`, instructions `0x028d`–`0x02e0`) branches to
   `readRawDataInt` for both `setPoint` and `measuredFloor`, and to
   `readRawDataUint` for other numeric fields. Negative floor values below
   −60 or above +60 are coerced to zero in the app's display path; this implementation
   retains raw decoding and does not reproduce that coercion.
3. **Param A/B:** Module 1350 retains thermostat field order and lengths.
   Param A totals 10 bytes; Param B totals **16**, including ecoMode at byte 15.
   Module 1306 F7951/F7952 confirms `raw * 0.5 - 50` and its inverse.
   F8569/F8570 confirms calibration `(raw - 14) / 2` and `value * 2 + 14`.
   Wi-Fi/EcoPlug and 3phase have alternative parameter arrays; shared UUIDs
   do not imply identical layouts for every product class.
4. **Settings patching:** F8442 clones the settings model and patches characteristic
   `.data` buffers with `copy`, `writeUInt8`, `writeUInt16LE`, etc., before sending
   the buffers using `writeCharacteristicAsync`. This corroborates patching an
   existing snapshot, not constructing zero-filled settings. Generator recovery
   is poor, so exact transaction ordering and preservation of every bit are not
   claimed verified. The new library's pure patchers own only selected temperature
   and eco fields and preserve all other bytes; its transport has no write API.
5. **Save confirmation:** F8385 stores `CONFIRMATION_CODE = 131` (`0x83`) at
   instructions `0x024a`–`0x0253`. The Ble module's sendSaveConfirmation method
   sends that stored value through `_sendCommand`. Whether a physical control
   confirmation is necessary remains device-specific and untested.
6. **Password/nonce:** Module 1350 defines productPassword but has no visible
   named use outside that model in the whole decompilation. This does **not**
   prove there is no authentication. `nonce` is now a `wr` settings model:
   `noncePassword[13]`, lockdownMode[1], nonceReserved[1], invert[1].
   Its EcoPlug model instead holds WifiPasswordPart2[20]. F8418 explicitly
   skips noncePassword and nonceReserved in the settings merge loop. Generic
   settings-reading/writing paths consume model arrays, so nonce is no longer
   safely described as an unused read-only cryptographic nonce. No access to
   password, nonce or Wi-Fi fields is exposed by the new transport.
7. **New UUIDs:** In Module 1350:
   - `...5bd9-9e8d-6dfb16490000` = productButtons, rw; EcoPlug stores WifiPasswordPart3[20].
   - `...5bd0-0e8d-6dfb16490000` = productButtons2, rw; EcoPlug stores WifiPasswordPart4[4]
     followed by WifiSSIDPart2[16]. Meaning for ordinary BASE hardware remains unknown.
8. **Product classes:** Module 1308 F7964 identifies `0x55` as ECO_PLUG,
   `0x6A` as TSENSE_3PHASE, and high nibble `0x90` as MSC. These have
   distinct field interpretations. ABB (`0x2E`, FLAT_ABB) uses shared thermostat
   fields with presentation/capability changes. Exact POWER3 branding is not
   established merely from this type mapping. The HA integration excludes
   ECO_PLUG, TSENSE_3PHASE and MSC from thermostat temperatures and GATT reads.

## Advertisement change

Legacy JS around character offset 1,449,035 explicitly contains:

```javascript
u.state=(240&o[2])>>4; u.error=(12&o[2])>>2; u.relay=3&o[2];
```

Module Ble / F8565 (`0x1d2dfd`) uses different status interpretation in 2.0.3.
Disassembly instructions around `0x026c`–`0x029e` confirm:

```text
thermostat state = (status & 0x70) >> 4
thermostat error = (status & 0x0C) >> 2
thermostat relay = (status & 0x80) != 0
```

Plug/3phase paths use different flags and interpret bytes 0..1 as on-time.
The original 1.0.17 advertisement assumptions must therefore not be treated as
universally compatible. Neither parser establishes a hardware generation gate.
The earlier global legacy/v2 profile implementation and its v2 default were
incorrect and have been removed. APK version describes the evidence source,
not a device's wire capabilities. Exact branch evidence and implementation
consequences are recorded below.

Both apps read an int16 and compare it against 65535 for unavailable temperature.
That comparison appears unreachable for a signed int16. The library follows the
handoff's explicit `FF FF` unavailable rule; no hardware validation is claimed.

## Remaining validation

E-2001 applicability, manufacturer ID, exact device type, wire capabilities,
GATT sentinels, sensor units on real firmware, heating behavior, proxy support,
authentication requirements and write confirmation all remain unverified.
The current work is sufficient for an experimental read-only implementation;
it is not a claim that every work-order compatibility invariant passed.

## Branch audit: advertisement status is not a newer-thermostat type gate

**Evidence identity:** HBC v96, Metro **module 1349** (stable decompiler name
COMMAND_CLOSE / Ble implementation), **F8565**, function bytecode base
`0x1d2dfd`. The decompiler's `_parseSinglePeripheral` assignment is in the
same module; its type decoder is `_parseType`, **F8566**, which delegates to
module 1308 **F7964** (`parseType`). A class is selected from manufacturer byte 3.

Relevant F8565 instruction offsets (relative to its bytecode base):

```text
020d LoadConstUInt8 r5, 3
0210 GetByVal r10, r4, r5           ; manufacturer payload[3]
021b GetById r5, r7, ..., "_parseType"
0226 PutById r0, r5, ..., "type"
023a GetById r5, r5, ..., "ECO_PLUG"
0240 JStrictEqualLong L759, r7, r5
0255 GetById r5, r5, ..., "TSENSE_3PHASE"
025b JStrictEqualLong L759, r7, r5
0269 LoadConstUInt8 r7, 112         ; 0x70
026c BitAnd r11, r10, r7
0273 RShift r10, r11, r10          ; shift by 4
0277 PutById r0, r10, ..., "state"
0296 BitAnd r10, r10, r8           ; r8 = 128 loaded at 00bf
029a StrictNeq r10, r10, r3        ; r3 = 0
029e PutById r0, r10, ..., "relay"
```

Compact equivalent of the branch, verified against instructions rather than
the generated iterator/register names:

```javascript
type = parseType(payload[3]);
if (type !== ECO_PLUG && type !== TSENSE_3PHASE) {
    state = (payload[2] & 0x70) >> 4;
    error = (payload[2] & 0x0c) >> 2;
    relay = (payload[2] & 0x80) !== 0;
} else {
    // L759: error mask 0x0f, relay 0x80, green 0x40, red 0x20;
    // bytes 0..1 contain on-time, not thermostat temperature.
}
```

F7964 maps raw `0x55` to ECO_PLUG, `0x6a` to TSENSE_3PHASE and
`(raw & 0xf0) == 0x90` to MSC; unmapped values fall through to BASE.
**Scope:** The first branch includes BASE, original RADIATOR (`0x11`),
RADIATOR22 (`0x22`), RADIATOR3 (`0x33`), RADIATOR_EE (`0xee`), newer
recognized thermostat types, and MSC. There is **no check of deviceVersion,
hardwareNumber, productNumber or old/new thermostat generation here**.
The second branch is genuinely class-specific for plug/3phase semantics.
MSC is separately excluded from this integration because its model reuses
temperature/setpoint fields for motor control.

**Conclusion:** This shows what 2.0.3's parser does for a broad class group.
It does not prove that a legacy thermostat or E-2001 actually emits that bit
layout, nor that a newly named OLED/Radiator subclass implies it. No automatic
high-relay-bit capability is assigned to any thermostat from this evidence alone.

## Branch audit: signed measuredFloor is selected by field key

**Evidence identity:** HBC v96, **module 1349**, parser factory **F8410**
(`0x1cd7ff`) creates **F8411** (`0x1cd816`), the `_getParseFunction` callback.
State model: **module 1350**, **F8588 BleSpec** (`0x1d39a4`),
`productStateA`, UUID `2be32db1-5f6b-4cbd-8843-8d6dfb164900`.
Stable decompilation lines 121495–121568 list its sequential params;
measuredFloor is the two-byte field at offset 8 with scale 0.1.

F8411 first chooses a parameter array:

```text
0062 GetById ..., "_hasEcoPlugParams"
0073 GetByIdShort ..., "deviceType"
007e JmpTrue L180                   ; paramsEcoPlug at 00b8
0085 GetById ..., "_has3PhaseParams"
0093 GetByIdShort ..., "deviceType"
009e ...
00a5 GetByIdShort ..., "params"     ; ordinary model
00ac GetById ..., "params3Phase"    ; if helper says applicable
```

Helpers **F8408** (`0x1cd78d`) and **F8409** (`0x1cd7c6`) require both the
corresponding device class and existence of the alternative array. This is
a **model-array selection**, not a choice of floor signedness.
Inside the selected array, F8411 uses the following numeric-field dispatch:

```text
00cd LoadConstString r10, "measuredFloor"
00dd LoadConstString r5, "setPoint"
0288 GetByIdShort r25, r25, ..., "key"
028d JStrictEqual L705, r25, r5
0294 GetByIdShort r25, r25, ..., "key"
0299 JStrictEqual L705, r25, r10
02a1 GetById ..., "readRawDataUint"  ; other numeric keys
02bc JmpLong L871
02c5 GetById ..., "readRawDataInt"   ; L705, either key above
02d9 Call4 ...
```

The called helper is **module 1358** (bitFromBuffer), **F9131 readRawDataInt**
(`0x1e5f72`); its length-2 branch calls `readInt16LE` at instruction `0x00a9`.
The corresponding unsigned helper is F9130. Exact module identity is preserved
in the compact model/helper excerpts generated for this audit.

Equivalent dispatch:

```javascript
if (field.key === "setPoint" || field.key === "measuredFloor")
    value = readRawDataInt(offset, field.length, buffer);
else
    value = readRawDataUint(offset, field.length, buffer);
```

**Model scope:** Module 1350 F8588 lists measuredFloor in the ordinary
productStateA params. Its UI `excludeTypes` contains ECO_PLUG,
TSENSE_3PHASE and MSC (F8588 instructions `0x0235`–`0x027e`). No
device-version gate is attached to signedness for BASE, Radiator, OLED or
ABB thermostat models. The subsequent display guard in F8411
`0x03c2`–`0x03d4` coerces floor values **below −60 or above +60** to zero;
this is a display policy and is not reproduced as a sensor value.

**Conclusion:** Signed floor is a shared field-name policy in this app parser.
It cannot be advertised as a demonstrated device-specific newer wire format.
Positive raw values below `0x8000` have the same result in either encoding;
the automatic decoder accepts those. Higher raw values remain unknown unless
an independently verified floor capability is supplied. The earlier default
signed conversion for E-2001 has been removed.

## Sentinel and capability policy in the corrected implementation

- Raw `FFFF` is checked **before** signed conversion for all StateA temperatures.
  It is suppressed as a suspected missing/invalid value, not converted to −0.1 °C.
  This conservative suppression does not claim a confirmed sentinel meaning.
- `StateA.raw_data` preserves the complete characteristic for later captures.
- Advertisement encoding and floor encoding are independent capabilities.
  Candidate legacy/high-bit and unsigned/signed decoders are retained for
  evidence fixtures. They are not app-version profiles or user preferences.
- No proven mapping for these two capabilities exists yet. The automatic
  resolver leaves them unresolved for all thermostat types, including unknown
  E-2001 candidates. HA shows raw advertisement status and sign-unambiguous
  GATT temperatures; decoded advertisement state/relay remain unknown.
- Known plug/3phase/MSC classes are rejected by the thermostat config flow in
  both discovery and manual selection. Unknown types remain allowed for testing.
- The `Tael*` matcher follows HA's first-three-characters wildcard restriction.
  Source: [HA manifest documentation](https://developers.home-assistant.io/docs/creating_integration_manifest/#bluetooth).
