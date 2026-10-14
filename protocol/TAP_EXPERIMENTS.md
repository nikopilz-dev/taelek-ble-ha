# FW66-derived GATT Tap experiments

Version0.1.14 adds `operation: tap` to the existing opt-in `taelek.debug_gatt`
action. It never runs during polling. It is a research tool, not verified climate
control. E-2001 hardware1.6S, explicitly expected firmware54 or66 only. FW66 code
evidence does not establish that FW54 accepts the same cipher/profile.

Use `sync_time: false`. Default `dry_run: true` reads Info, ParamB, StateA and a
fresh16-byte nonce, then prepares a candidate ciphertext without writing anything.
The optional `cryptography` backend is required; HA Core supplies it. Standalone
users install the `crypto` extra. The protocol key is provided as `key_hex` by
the caller; firmware-derived keys are not included in this repository or logged.

```yaml
action: taelek.debug_gatt
data:
  config_entry_id: YOUR_ENTRY_ID
  sync_time: false
  steps:
    - operation: tap
      command: 1
      expected_firmware: 54
      key_hex: REPLACE_WITH_16_BYTE_PROTOCOL_KEY_HEX
      dry_run: true
```

`dry_run: false` explicitly sends one16-byte write to productPassword, with
response enabled, in the same serialized connection as the nonce read. No retry,
reconnect/replay, save opcode or automatic restore is added. The firmware-derived
identity gate rejects Info[16]==3. Clock sync must be disabled for the whole plan.

Candidate cipher: standard AES-CCM,13-byte nonce from nonce[:13],16-byte key in
supplied byte order, no AAD,4-byte tag computed but omitted from the write. FW66
passes a zero MIC and ignores crypto return status. Actual shared-stack crypto
code is outside the supplied image: cipher byte order is NOT device-validated.
Do not try a matrix of key/nonce orders or automatically retry alternate profiles.

|Command|FW66 local effect|
|---|---|
|1|No command-specific temperature/hold mutation; refreshes nonce|
|2|Writes External ECO/manualEco; `target_c` required,5..40C,0.1C steps; PWM mode rejected|
|3|Sets ECO hold counter2400 and a runtime flag|
|4|Sets ECO hold counter3; count duration is not established|

Tap writes do not select weekly/manual program or change wireless flags/group.
Nonce rotation alone does NOT demonstrate acceptance: FW66 refreshes after
invalid plaintext too. Transport success is never reported as heating success.

The separate passive `Wireless ECO hold raw` diagnostic is disabled by default.
It decodes Tae1 payload[4:6] only under company0x048a, exact18-byte length and a
recent verified ordinary thermostat frame. It neither renews thermostat identity
freshness nor reveals group bytes. Units and radio receiver effects remain
unverified. It is not a boolean relay/ECO state and not seconds.

For a device trial: record physical output plus fresh reads first, prepare the
command1 dry run, then one explicit command1 write. A later command3 trial needs
a bounded observation window and command4 release followed by physical verification.
Use a measured floor/ECO target combination where OFF is actually expected:
22C ECO still demands heat for a14C floor. Save pre-test settings privately and
restore any parameter/fixture changes explicitly. Leave ordinary polling enabled
only when it does not contend with the controlled experiment.
