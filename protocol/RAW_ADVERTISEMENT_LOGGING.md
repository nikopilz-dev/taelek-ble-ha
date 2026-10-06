# Passive raw advertisement logging

Version0.1.12 logs observations for each configured device before discovery/layout
filtering, including ignored `Tae1` frames. Enable only the dedicated logger:

```yaml
action: logger.set_level
data:
  custom_components.taelek.advertisements: debug
```

Disable after capture by setting the same logger to `warning`. Runtime levels
are reset by HA restart; set again after restarting. No GATT connection, clock
write or configuration write is caused by this logger.

Each `raw_advertisement` line preserves UTC callback time, HA service-info time,
address, local name, proxy/source, RSSI, manufacturer payloads keyed by company
ID, service data and UUIDs. Version0.1.13 additionally preserves `raw` AD bytes,
connectable and tx_power. `raw=None` means that backend did not supply raw bytes.
Manufacturer bytes exclude the company ID itself.
`cached=True` identifies startup-cache processing rather than a fresh callback.
Do not convert HA's `ha_time` into wall time without checking its clock domain;
the explicit `utc` is the integration's processing time, not radio transmit time.

This is a log of observations delivered to the integration by HA. HA, proxies
or scanners may deduplicate/filter packets, and multiple sources may deliver an
observation. It is not an over-air packet sniffer. Absence of a record cannot
prove absence of a transmission. Logging does not recover packets from before
it was enabled, and rotation/storage retention depends on HA's logger setup.

Only `raw` is per-packet; manufacturer/service fields and UUIDs may be merged
across packets. Classify packet names and payloads from AD structures in `raw`
where available, rather than assuming all merged fields belong to the same
packet. The current HA documentation provides an every-advertisement API, but
it is absent from HA Core2026.9.4's exported Bluetooth APIs. This integration
uses the change/discovery callback and does not claim to record every packet.
References: [Bluetooth API](https://developers.home-assistant.io/docs/core/bluetooth/api/),
[2026.9.4 API source](https://github.com/home-assistant/core/blob/2026.9.4/homeassistant/components/bluetooth/api.py),
[2026.9.4 raw serialization](https://github.com/home-assistant/core/blob/2026.9.4/homeassistant/components/bluetooth/websocket_api.py).

Raw frames can expose network/group keys and device identifiers. Keep original
logs private; sanitize selected evidence before sharing or publishing. A `Tae1`
layout resemblance is not enough to label its bytes as ECO commands or enable
transmission. Current thermostat discovery/identity rules remain in force.
