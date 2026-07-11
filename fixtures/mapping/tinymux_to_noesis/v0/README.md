# TinyMUX to NOESIS Telemetry Mapping Fixtures v0

These fixtures exercise the adapter-owned mapping from
`tinymux.log_event.v0` source records to `noesis.telemetry.v0` telemetry
records.

They belong to `ThresholdOps/noesis-tinymux`. They do not redefine the NOESIS
telemetry contract, which remains authoritative in
`ThresholdOps/noesis/docs/telemetry-contract.md`.

All records are synthetic. They do not imply runtime mapper implementation,
live TinyMUX connectivity, production transport readiness, or any TinyMUX
standard.

Validation for this corpus will be added in a later slice.

References:

- `docs/tinymux-source-record-v0.md`
- `docs/tinymux-to-noesis-telemetry-mapping-v0.md`
- `docs/artifact-ownership.md`
- `ThresholdOps/noesis/docs/telemetry-contract.md`

## Files

- `mapped.json` contains deterministic successful mappings.
- `unresolved.json` contains valid source records that do not yet have a safe
  telemetry v0 mapping.
- `rejected.json` contains source or mapping admission failures.

Each file contains one top-level JSON array.

## Fixture Object Shape

Each fixture has this shape:

```json
{
  "case_id": "stable-case-id",
  "outcome": "MAPPED",
  "source_record": {},
  "mapping_context": {
    "run_id": "fixture-run-0001",
    "seq": 1
  },
  "expected_telemetry": {},
  "expected_reason": null,
  "notes": "Synthetic fixture."
}
```

`case_id` values are globally unique across all files.

`outcome` is one of:

- `MAPPED`: deterministic `noesis.telemetry.v0` output is asserted.
- `UNRESOLVED`: the source record is valid, but telemetry v0 lacks a safe
  mapping without inventing semantics.
- `REJECTED`: the source record, source version, mapping version, or adapter
  mapping context is invalid or unsupported.

For `MAPPED`, `expected_telemetry` is an object and `expected_reason` is
`null`.

For `UNRESOLVED` and `REJECTED`, `expected_telemetry` is `null` and
`expected_reason` is a stable non-empty reason code.
