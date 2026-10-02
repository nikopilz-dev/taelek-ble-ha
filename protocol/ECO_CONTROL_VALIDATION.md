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
Selected complete instruction listings are preserved in
`../evidence/ecocontrol-selected-disassembly.txt`; regenerate them with
`python tools/record_ecocontrol_evidence.py` after extracting the same bundle.

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

### First CLOSE observation

The HA test on 2026-10-02 returned an acknowledged `0x73` write and successful
State A read-back in the same connection. OperationMode stayed 0 and setpoint
stayed 35.0 °C; the whole before/after State A payload was identical. Param B
was not written and no `0x83` confirmation was sent. No LED observation was
received during the experiment. The subsequent NORMAL restoration (`0x84`) was
acknowledged and its before/after payload was also identical:
`000000005e01d100a2000000`. OperationMode remained 0 and setpoint 35.0 °C.
An unchanged immediate read is not proof that a command is unsupported, nor
proof of an ECO transition; neither command's semantic effect is established.

## Clock and external wired input

### Observed command repeat with a person at the thermostat

On 2026-10-02 the user observed the LED while CLOSE and then NORMAL were
sent once each through HA. Blinking was reported before the first write.
After CLOSE, the user reported faster blinking followed by steady red.
After NORMAL, the user reported a relay click, then blinking,
bright red and blinking again. The user clarified that the child's report of
"clicking" meant a single click, not repeated chatter. These are user observations, not decoded relay
state or confirmed ECO transitions. NORMAL's immediate pre/post State A was
identical: `000000005e01d200a2000000`, with operationMode 0 and setpoint 35 °C.

No ECO temperature or other settings were written in this repeat. The installed
0.1.4 only provides the two command experiments. Further commands were stopped
and experimental GATT polling was temporarily disabled while the ambiguous report
was clarified. A single relay transition was confirmed by the user.
Do not describe CLOSE as an ECO command or the relay sound as proof of successful
temperature control.

Version 0.1.5 adds explicit manualEco experiments (10 / 25 °C and restore).
The client reads Param B and State A before writing, preserves every byte except
Param B offsets 2–3, writes once with response and reads Param B and State A back.
It sends no save confirmation and changes neither ecoMode nor wireless ECO flags.
The original target is retained for explicit restore, even on failed read-back,
only during the current integration load. This is not an ECO activation command.
Tests cover preserved bytes, restoration, pre-read failure preventing writes,
post-read failure retaining the backup, and setup never invoking writes.

During preparation, before any temperature write, the user also observed both
heating-on and heating-off using a multimeter. Natural switching is therefore
a confounder for interpreting a single LED or relay change.

### First manualEco target write on hardware

HA 0.1.5 (commit 703606c, CI passed, 104 local tests passed) was installed
through HACS and restarted. The first 10 °C experiment at 20:37 Helsinki time
read manualEco 19 °C both before and immediately after the acknowledged write.
State A also remained `000000005e01db00a3000000`: setpoint 35 °C, floor 16.3 °C,
operationMode 0. The user observed slow red pulsing, relay release, then steady
red and later relay engagement. Since neither manualEco nor active setpoint
changed, this is not proof of temperature control.

The 25 °C comparison was not executed after the first target failed read-back.
Explicit restoration wrote the original 19 °C once and read it back as 19 °C
at 20:38. State A before/after was `000000005e01de00a3000000` (35 °C setpoint,
16.3 °C floor, operationMode 0). The user reported another release afterward.
No save confirmation or additional runtime command was sent during this
temperature experiment. Whether a save/physical confirmation or another
write path is needed remains unresolved; do not infer that cause from an ACK.

Etherma's official E-2001-BLE manual (attachment fileID 183 on product 44371)
specifies external control as **230 V / 50 Hz** and shows the clock-symbol
terminal in the wiring diagram (page 1). It is not a low-voltage jumper input.
Page 2 requires correct time for the internal weekly program, says MAI Smart
updates it on connection, and gives less than two hours of power-loss retention.
Clock error 10 falls back to the knob's temperature. This does not establish
that forced BLE ECO requires the clock. At the time of those experiments the HA
client did not write Time or initialize commissioning parameters. Version 0.1.7
adds one Time write per active session; see `CLOCK_SYNC.md`. That change has not
yet been validated on the physical device and proves no ECO prerequisite.

Taelek's Homey guide instead disables the internal user program and uses forced
ECO with an ECO setpoint for displayless models. It contains no jumper step.

Sources checked 2026-10-02:
- https://etherma.fi/downloadAttachment.php?class=Tuote&classID=44371&fileID=183
- https://taelek.fi/Documents/easy_manual_homey.pdf
