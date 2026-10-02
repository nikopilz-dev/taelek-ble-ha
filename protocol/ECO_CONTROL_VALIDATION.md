# ecoControl 3.0.11 command investigation — 2026-10-02

Input provided locally by the user: `ecoControl_3.0.11_APKPure.xapk`.
The XAPK manifest identifies `com.taelek.termos`, version 3.0.11, code 109.
Only `assets/index.android.bundle` from the nested `com.taelek.termos.apk`
was extracted. No application was installed, run, or connected to the device.

| Artifact | SHA-256 |
| --- | --- |
| XAPK | `65bd22c325f6c6ad9459d3ebdfdcce1d658f753ee7af11736e0795e7c79b2092` |
| Hermes bundle | `6c44b75f7b962612e76dd673636c472b5058352119289195f101841e4db48cb9` |

Hermes-decomp v0.2.4 identifies HBC v98, Modern12 layout, 15,404 functions,
27,855 strings and 1,643 detected Metro modules. Deep/stable output has
365,602 lines. Full output and bytecode are ignored by Git. Modern closure
recovery contains wrong variable references, so disassembly takes precedence.

## Confirmed command sender

Metro module **1292**, initialization **F1294** exports the same command names.
Its relative instruction offsets are:

```text
0502 LoadConstUInt8 ..., 81   # WINK 0x51
0509 LoadConstUInt8 ..., 98   # OPEN 0x62
0510 LoadConstUInt8 ..., 115  # CLOSE 0x73
0517 LoadConstUInt8 ..., 132  # NORMAL 0x84
051e LoadConstUInt8 ..., 149  # FACTORY_RESET 0x95
0525 LoadConstUInt8 ..., 166  # COUNTER_RESET 0xA6
052c LoadConstUInt8 ..., 131  # save confirmation 0x83
```

**F7451 (Ble)** creates `_sendCommand` as **F11329** at `0x01a2–0x01a7`.
F11329 (bytecode base `0x26f124`) captures argument 1 and constructs a
promise with **F13718** (base `0x2adea1`). Relevant F13718 instructions:

```text
0021–0024 Load captured command argument
0045 NewArray ..., 1
0049 DefineOwnInDenseArray ..., captured_command, 0
0051 LoadConstString ..., "hex"
005b Construct Buffer.from with that array
007a GetById ..., "_writeChar"
0080 GetById ..., "commandCharacteristic"
0086 Call3 _writeChar(buffer, commandCharacteristic)
```

The model's `productCommands` UUID remains
`2be32db1-5f6b-5bd8-8A38-d6dfb1649000` (stable output line 151342).
This confirms one-byte command encoding, **not that CLOSE means forced ECO**.

## ECO indicator is not a runtime button

Metro module **1424**, **F8129 (StateToggleButton)** uses advertisement-derived
state: ECO is selected for 2, 4 or 6; COM for 1 or 3; AUTO for 3 or 4.
F8129's `0x0088–0x00c2` tests ECO and those values. Its render returns View/Text
and gradient views; neither source nor disassembly contains an `onPress`
handler. Stable output lines 319430–319579 show the entire component.

The Param B `ecoMode` picker remains `[1, 2]` (line 151328). The new settings
code explicitly calls it the User Program dropdown (line 295779), and sets
it to 1/OFF when enabling Matter (lines 296112–296115). This does not provide
the Homey forced-ECO command. `manualEco` is still a separate temperature field.

The inspected command exports and their references did not identify a forced
ECO payload. This is a bounded negative finding, not proof that no private or
dynamic route exists elsewhere. No runtime capability is inferred from the
app version, and no global protocol profile is introduced.

## HA experiment

The user authorized writes on a mains-powered test unit with floor sensor
attached and no heating load. Version 0.1.4 offers disabled-by-default CLOSE
and NORMAL diagnostic experiments. Each performs a mandatory State A pre-read,
one acknowledged command write and a post-read, under the same session lock
as ordinary reads. No settings writes, save confirmation or automatic retries
occur. An ACK is not treated as semantic success. CLOSE is not exposed as an
ECO switch. Hardware results will be recorded separately after the experiment.
