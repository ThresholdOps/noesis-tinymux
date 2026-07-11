# TinyMUX Mapping Quarantine Fixtures v0

These fixtures exercise the adapter-owned quarantine contract
`tinymux.mapping_quarantine.v0` for the mapping contract
`tinymux-to-noesis-telemetry-mapping-v0`.

They are synthetic quarantine records for adapter diagnostics. They are never
`noesis.telemetry.v0` records, do not contain telemetry output, and do not
implement a runtime quarantine sink.

Authoritative references:

- `docs/tinymux-mapping-quarantine-v0.md`
- `docs/tinymux-to-noesis-telemetry-mapping-v0.md`
- `fixtures/mapping/tinymux_to_noesis/v0/unresolved.json`
- `fixtures/mapping/tinymux_to_noesis/v0/rejected.json`

## Directory Contents

- `unresolved.json`: 4 quarantine records derived one-to-one from unresolved
  mapping fixture cases.
- `rejected.json`: 7 quarantine records, including 6 mapping-derived rejected
  cases and 1 illustrative raw/unparseable input case.
- `adapter_errors.json`: 1 illustrative adapter-internal failure case.

Exact corpus size:

- unresolved: 4 cases
- rejected: 7 cases
- adapter errors: 1 case
- total: 12 cases

## Wrapper Structure

Each file contains one top-level JSON array. Each array entry has exactly these
wrapper fields:

```json
{
  "case_id": "stable-unique-case-id",
  "origin_mapping_case_id": "existing-mapping-case-id-or-null",
  "quarantine_record": {},
  "notes": "Synthetic fixture."
}
```

`case_id` is unique across all quarantine fixture files.

`origin_mapping_case_id` is the exact mapping fixture `case_id` for derived
cases. It is `null` for illustrative cases that are not present in the current
mapping fixture corpus.

## Derived and Illustrative Cases

Ten cases are derived from the existing mapping fixture corpus:

- 4 unresolved mapping outcomes from `unresolved.json`;
- 6 rejected mapping outcomes from `rejected.json`.

Two cases are illustrative policy coverage:

- one raw/unparseable `REJECTED` input;
- one `adapter_error` record.

The illustrative cases use `origin_mapping_case_id: null`.

## Reason-Code Coverage

The corpus covers all ten existing mapping reason codes:

- `no_private_communication_event_type`
- `no_ooc_event_type`
- `system_subtype_required`
- `custom_subtype_required`
- `unsupported_source_schema`
- `invalid_source_record`
- `unsupported_mapping_version`
- `missing_mapping_context`
- `invalid_run_id`
- `invalid_seq`

It also covers the reserved adapter-internal code:

- `adapter_error`

`invalid_source_record` appears twice: once for a parsed but contract-invalid
source object, and once for unparseable raw input. This duplication is
intentional.

## Rejection Categories

`UNRESOLVED` records use `rejection_category: null`.

`REJECTED` records use the closed category mapping from the quarantine
contract:

- `source_contract`: `unsupported_source_schema`, `invalid_source_record`
- `mapping_context`: `unsupported_mapping_version`, `missing_mapping_context`,
  `invalid_run_id`, `invalid_seq`

`adapter_error` records use `outcome: null` and `rejection_category: null`.

## Source Preservation

Every quarantine record follows the source-preservation XOR rule:

- parsed source input uses `source_record` and `source_record_raw: null`;
- unparseable raw input uses `source_record: null` and `source_record_raw`.

When `source_record` is present, denormalized fields match it exactly:

- `source_event_id == source_record.event_id`
- `source_schema_version == source_record.schema_version`

When raw input is used, both denormalized fields are `null`.

## Hashes

All records use `content_hash: null`.

Hash calculation is intentionally not implemented in this fixture slice.

## Non-Goals

These fixtures do not implement:

- validation;
- CI;
- storage;
- runtime handling;
- sink behavior;
- retry or replay;
- retention policy.

A quarantine fixture validator will be added in a later slice.
