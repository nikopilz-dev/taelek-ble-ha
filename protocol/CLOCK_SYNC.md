# Clock synchronization — APK evidence and HA implementation

Version 0.1.7, 2026-10-03. This adds a known app operation; it does not establish
that the clock is required for authorization, parameter acceptance or wireless
message freshness. Physical clock-write/readback validation is pending.

## Evidence

- MAI Smart 1.0.17, BLE Metro module 1090: `this.writeTimeData` at Unicode
  character offset 1447315 uses `moment.utc().local()`, then hours, minutes,
  seconds, `isoWeekday()`, `Buffer.from`, `writeCharacteristicAsync`.
- MAI Smart 2.0.3, BLE module 1349: **F8549**, bytecode offset `0x1d27dc`;
  instructions `0x000c`–`0x0044` obtain UTC then convert to local and read the
  four fields; `0x0051`–`0x006f` push them in that order; `0x00c3`–`0x00c9`
  write the buffer to `timeCharacteristic`.
- Model UUID: `2be32db1-5f6b-5bd8-8c38-d6dfb1649000` (Time).
- The 2.0.3 initial request worker **F13887**, instructions `0x042c`–`0x045e`,
  calls `writeTimeData` then `readPrettyTimeData`. It does this after initial
  information/settings/schedule reads on the successful path. Other refresh
  worker call sites are retained in the selected evidence. This is not proof
  of an unconditional low-level connect callback.
- No preceding comparison with the current clock is visible in the writer.
  No `0x83` or physical confirmation is sent by the writer itself.

Selected source and disassembly: `../evidence/clock-sync-excerpts.txt`.
APK/bundle checksums: `../evidence/checksums.txt`.

## Runtime behavior

HA provides timezone-aware `homeassistant.util.dt.now` to the shared client.
After every successful active connect, before yielding the client to reads or
experiments, one write with response is sent: `[hour, minute, second, weekday]`.
Weekday is ISO Monday=1 through Sunday=7. No date, offset, timestamp, nonce,
save confirmation or thermostat parameter is appended. Each session samples
the time anew after connection establishment. Passive reception does not connect
or write. Standalone clients without an explicit clock provider stay read-only.

**Deliberate HA placement:** the write is moved to the session prelude instead
of reproducing the app's entire initial read/settings/schedule transaction.
The bytes and once-per-session policy match the selected app behavior; the
complete commissioning transaction is not claimed reproduced. Unlike the app
worker, HA does not automatically read Time back; a transport acknowledgment is
reported as such, not proof of an accurate device clock.

Failure stops the session, disconnects and propagates visibly. No clock retry,
silent fallback or automatic save is performed. Passive availability is
independent. This means enabled GATT polling now performs one clock write on
each polling connection, rather than being entirely read-only.

## Controlled debugging

`taelek.debug_gatt` defaults to `sync_time: true`. Set `sync_time: false` to
omit the clock prelude for that debug session. This does not disable ordinary
coordinator polling; disable GATT entities/polling separately before claiming
a clock-write-free observation interval.

```yaml
action: taelek.debug_gatt
data:
  config_entry_id: YOUR_ENTRY_ID
  sync_time: false
  steps:
    - operation: read
      uuid: 2be32db1-5f6b-5bd8-8c38-d6dfb1649000
```

Debug responses contain `clock_sync` separately from user steps: status, UUID,
sent bytes and local time including offset when attempted. A failure before
user steps yields an empty `steps` list with the clock error. Step indices
continue to refer only to the requested sequence. This preserves A/B testing.
