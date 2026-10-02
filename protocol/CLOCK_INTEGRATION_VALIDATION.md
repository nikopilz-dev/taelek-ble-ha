# Clock integration review — remote HEAD audit, 2026-10-03

The review was checked against GitHub's fetched `main`, not just a working tree:
`02b7bf553efe8f03fe7928b3b247d3cb0e5124e9` (version 0.1.7). The follow-up commit
adds stronger service-chain/package tests and corrects the README ZIP filename.
It does not change the clock placement documented in `CLOCK_SYNC.md`.

## Findings against that published commit

| Review item | Published commit evidence | Resolution |
| --- | --- | --- |
| Vendored client lacks clock sync | Both client paths have Git blob `92965a2859151d11030c34843b7965ce975c1bfc` | Already byte-identical; rerun vendor tool and final consistency checks |
| HA supplies no clock | `ActiveCoordinator`: `TaelekClient(self._connect, clock=dt_util.now)` | Already present; strengthen test using non-UTC HA local time through normal connector |
| Service drops sync_time | Schema defaults bool to true; handler forwards to coordinator; coordinator forwards to client | Already present; exercise registered schema, handler and actual vendored client together |
| Manifest remains 0.1.6 | Published manifest contains `"version": "0.1.7"` | Already correct |
| README ZIP remains 0.1.6 | Manual installation example still names old ZIP | Corrected to 0.1.7; package regression test checks versioned filename |
| Integration-level coverage | Previous service test used a mocked active coordinator; library tests alone did not exercise that whole chain | Added default/false/failure service-chain tests with real coordinator/client code and HA boundary doubles |
| Final vendor/package consistency | Published source and vendor objects match; stronger archive verification is useful | Rerun vendor after changes; build/read archive and compare runtime files against source |

The clock module also matches across paths: Git blob
`f97a86e24f64542237ce3fa7587133f0649476ae` in both source and vendor directories.
The cause of the review's different file contents is unknown without the exact
commit/files it examined. The first four claims do not describe the fetched
commit above. Do not infer a cache error or a missing push without evidence.

## Reproduce the source comparison

```text
git fetch origin main
git rev-parse origin/main
git rev-parse 02b7bf5:src/taelek_ble/client.py
git rev-parse 02b7bf5:custom_components/taelek/taelek_ble/client.py
git show 02b7bf5:custom_components/taelek/coordinator.py
git show 02b7bf5:custom_components/taelek/services.py
git show 02b7bf5:custom_components/taelek/manifest.json
```

The first two client object IDs are identical, which establishes exact byte
identity in that published tree. The vendor tool was run before the original
133-test run and package build; no difference between those client objects was
introduced before publication. The new checks run again after all follow-up edits.

## Test boundaries and acceptance criteria

- Normal HA active refresh traverses the real coordinator connector and vendored
  client. Only HA/Bluetooth boundaries are stubbed. A configured +03:00 local
  time `2026-10-03 01:02:03` yields exactly one TIME write `01 02 03 06`, before
  reads, rather than the corresponding Friday UTC time.
- Registered debug schema defaults sync_time to true; explicit false passes
  unchanged through handler/coordinator/client and yields zero automatic TIME
  writes while requested operations still execute.
- A TIME-write failure returns a visible clock error, starts no requested debug
  steps, disconnects and does not retry.
- Source/vendor Python module sets and bytes match. A freshly built ZIP's
  vendored library bytes, coordinator, services, service YAML and manifest match
  the checkout. README installation filename matches the manifest version.

These tests do **not** establish actual HA event-loop/loading behavior or
physical device acceptance. The real-HA `tests_ha` suite has not been run in this
Windows environment. No HA update, thermostat connection or hardware experiment
is part of this validation follow-up.
