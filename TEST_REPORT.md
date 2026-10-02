# Verification – 2026-10-02

## Clock synchronization update — 2026-10-03, version 0.1.7

- `python -m pytest tests -q`: **133 passed**. Existing read-only standalone
  coverage retained; new tests cover exact local clock bytes and ISO weekdays,
  midnight rollover versus UTC, one write per session, debug opt-out, visible
  failure/no retries, cancellation cleanup and HA passive independence.
- Ruff lint and formatting: passed. Bundled source consistency is covered by
  the existing distribution test. Installable 0.1.7 ZIP built successfully;
  package now includes service YAML as well as Python and JSON.
- The HA coordinator always supplies HA's configured local clock. Standalone
  clients without a clock provider retain their previous read-only behavior.
- No physical device connection or clock write was performed for this change.
  Actual HA loading and clock-write/readback validation remain pending; HA
  integration tests here use boundary doubles, not the real HA runtime.

The older verification entries below describe previous versions.

Executed locally with Python 3.12.14 in the project's Windows virtual environment.

| Check | Result |
|---|---|
| `python -m pytest tests -q` | 88 passed, including optional GATT failure isolation and no network-key exposure |
| Ruff checks and formatting | Passed |
| Python compilation of library, integration, tools and HA test sources | Passed |
| Bundled library equals standalone source | Passed in distribution test |
| Manifest and translation JSON checks | Passed in distribution test |
| Installable ZIP construction | Passed |
| APK and extracted bundle checksums | Match supplied references |
| Hermes v96 decompilation/disassembly using hermes-decomp v0.2.4 | Completed; differences documented |
| `tests_ha` with the actual HA framework | Not executed |
| HA component loading and entity registration | 0.1.1 installed through HACS, HA restarted, Bluetooth discovery and device creation succeeded; passive temperature shown |
| HA scheduling and unloading | Not validated |
| Physical E-2001 / Bluetooth proxy / GATT / heating validation | Passive and GATT floor/setpoint readings displayed in HA through proxy; writes and heating remain unvalidated |

Twenty integration logic test cases run against explicit HA boundary doubles. They do not
substitute for the real HA tests. Other tests exercise codecs, transport cleanup,
classification, stable identity and distribution consistency. Synthetic payloads
come from documented APK layouts; they are not captures from a real thermostat.

The ZIP is an experimental read-only development artifact. No BLE scanner was
started by the library, no GATT connection was made to hardware, and no thermostat settings were written.

Added regression coverage for the legal `Tael*` matcher, removal of profile UI/options,
all non-thermostat discovery classes including the MSC range, unknown-type admission,
independent status/floor capability combinations, unresolved automatic decoding,
signed/unsigned `FFFF` suppression before conversion and the HA entity value.
Existing codec/transport/config-flow tests were retained and adapted to the explicit
capability API; legacy fixtures still exercise their original wire expectations.

Real HA config-flow tests also include class rejection, but remain unexecuted on
this Windows/Python 3.12 environment. No hardware-specific capability mapping has
been established, and no such mapping is inferred from app version.
