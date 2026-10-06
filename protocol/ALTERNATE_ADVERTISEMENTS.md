# Alternate advertisements

## Tae1 (0.1.11)

Field observation on an E-2001/type 0x22/fw54 after enabling wireless ECO reception:
the same Bluetooth address advertises both `Tael` and `Tae1`, with company ID1162
and18-byte manufacturer payloads. `Tae1` is not the normal thermostat layout.
Its bytes6..13 matched the device's configured eight-byte network key. The meaning
of the other bytes and its control/relay semantics remain unverified.

The ordinary `Tael` frame retains its four-byte serial at offset4 and advertised
name at offset8. Decoding `Tae1` with that layout creates a false serial and name,
causing duplicate discoveries and active-connection identity failures.

Discovery therefore ignores local name `Tae1` as thermostat data. When HA's latest
record is `Tae1`, active operations require a matching ordinary frame received by
the passive coordinator within90seconds, plus HA address availability. Startup
cache alone is insufficient. Unavailability or an ordinary serial mismatch
invalidates the fallback. Ordinary mismatched serials still reject connections.
No network key is used as device identity or exposed by these sensor paths.

Captured Android service discovery before/after enabling reception had the same
six services, characteristic handles, UUIDs and properties. That is evidence
against a newly advertised GATT endpoint in those sessions, not proof that all
firmware behavior remained unchanged. Original captures and keys stay private.
