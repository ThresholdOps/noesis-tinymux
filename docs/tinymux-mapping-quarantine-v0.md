# TinyMUX Mapping Quarantine Contract v0

## Status

Status: draft normative quarantine contract

This document defines `tinymux.mapping_quarantine.v0`.

It extends `docs/tinymux-to-noesis-telemetry-mapping-v0.md` for non-`MAPPED`
mapping outcomes and adapter-internal failures. It does not redefine the
existing `MAPPED`, `UNRESOLVED`, or `REJECTED` mapping outcomes, and it does not
modify the mapping fixture corpus or validator.

This document is documentation only. It does not implement quarantine storage,
runtime handling, fixtures, validation, or CI.

## Purpose

The purpose of `tinymux.mapping_quarantine.v0` is to make non-mapped processing
attempts observable and reviewable.

No-silent-drop is defined as follows: every input accepted for processing ends
in exactly one of a `noesis.telemetry.v0` record, a
`tinymux.mapping_quarantine.v0` record, or an explicit, non-swallowed failure
signal from the attempt to write the quarantine record itself. Declaring success
without producing one of the first two is prohibited.

## Scope

This contract covers:

- `UNRESOLVED` mapping outcomes;
- `REJECTED` mapping outcomes;
- adapter-internal failures unrelated to mapping classification.

This contract does not cover `MAPPED` outcomes. A `MAPPED` outcome produces a
`noesis.telemetry.v0` record, not a quarantine record.

## Outcome and Quarantine-Class Model

Every quarantine record has a `quarantine_class`.

Allowed values:

- `mapping_outcome`
- `adapter_error`

For `quarantine_class: "mapping_outcome"`:

- `outcome` is either `UNRESOLVED` or `REJECTED`;
- `reason_code` is one of the mapping fixture reason codes listed below;
- `rejection_category` is `null` for `UNRESOLVED`;
- `rejection_category` is mandatory for `REJECTED`.

For `quarantine_class: "adapter_error"`:

- `outcome` is `null`;
- `rejection_category` is `null`;
- `reason_code` is `adapter_error`;
- `diagnostic_details` carries the specific adapter failure information.

`REJECTED` uses this closed `rejection_category` assignment:

- `source_contract`: `unsupported_source_schema`, `invalid_source_record`
- `mapping_context`: `unsupported_mapping_version`, `missing_mapping_context`,
  `invalid_run_id`, `invalid_seq`

`UNRESOLVED` reason codes have `rejection_category: null`.

## Reason Code Vocabulary

The current reason-code vocabulary is derived directly from:

- `fixtures/mapping/tinymux_to_noesis/v0/unresolved.json`
- `fixtures/mapping/tinymux_to_noesis/v0/rejected.json`

Existing fixture reason codes:

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

| reason_code | quarantine_class | outcome | rejection_category | meaning |
| --- | --- | --- | --- | --- |
| `no_private_communication_event_type` | `mapping_outcome` | `UNRESOLVED` | `null` | Valid `page` source record, but telemetry v0 has no private communication event family. |
| `no_ooc_event_type` | `mapping_outcome` | `UNRESOLVED` | `null` | Valid `ooc` source record, but telemetry v0 has no explicit OOC event family. |
| `system_subtype_required` | `mapping_outcome` | `UNRESOLVED` | `null` | Valid `system` source record, but no explicit subtype safely selects a telemetry family. |
| `custom_subtype_required` | `mapping_outcome` | `UNRESOLVED` | `null` | Valid `custom` source record, but no documented subtype convention safely selects a telemetry family. |
| `unsupported_source_schema` | `mapping_outcome` | `REJECTED` | `source_contract` | Source record uses an unsupported `schema_version`. |
| `invalid_source_record` | `mapping_outcome` | `REJECTED` | `source_contract` | Source record violates `tinymux.log_event.v0` validation rules. |
| `unsupported_mapping_version` | `mapping_outcome` | `REJECTED` | `mapping_context` | Mapping context requested an unsupported mapping version. |
| `missing_mapping_context` | `mapping_outcome` | `REJECTED` | `mapping_context` | Adapter mapping context was absent. |
| `invalid_run_id` | `mapping_outcome` | `REJECTED` | `mapping_context` | Adapter mapping context had a missing, empty, or invalid `run_id`. |
| `invalid_seq` | `mapping_outcome` | `REJECTED` | `mapping_context` | Adapter mapping context had a missing, non-integer, or invalid `seq`. |
| `adapter_error` | `adapter_error` | `null` | `null` | Adapter-internal failure unrelated to mapping classification. |

Adding a new reason code requires a corresponding fixture case in the mapping
fixture corpus. If `adapter_error` is ever subdivided, each new adapter-error
variant requires a corresponding quarantine fixture in a future slice. This
vocabulary must never grow independently of fixtures that exercise it.

## Quarantine Record Contract (`tinymux.mapping_quarantine.v0`)

| Field | Type | Required | Rules |
| --- | --- | --- | --- |
| `schema_version` | string | yes | Fixed literal `tinymux.mapping_quarantine.v0`. |
| `quarantine_id` | string | yes | Non-empty stable identifier of one quarantine record. Unique within the adapter quarantine domain. Must not be synthesized by reusing `source_event_id`. Generation algorithm is not defined by v0. |
| `quarantine_class` | string | yes | Either `mapping_outcome` or `adapter_error`. |
| `outcome` | string or null | yes | `UNRESOLVED` or `REJECTED` for `mapping_outcome`; `null` for `adapter_error`. |
| `rejection_category` | string or null | yes | `null` for `UNRESOLVED` and `adapter_error`; `source_contract` or `mapping_context` for `REJECTED`. |
| `reason_code` | string | yes | One of the reason codes in the vocabulary table. |
| `source_record` | object or null | yes | Parsed source record when available. Exactly one of `source_record` or `source_record_raw` must be non-null. |
| `source_record_raw` | string or null | yes | Exact input text when the source line could not be parsed as JSON. Exactly one of `source_record` or `source_record_raw` must be non-null. |
| `source_event_id` | string or null | yes | Denormalized index field. When derivable from `source_record`, it must equal `source_record.event_id`; otherwise `null`. Never synthesize it. |
| `source_schema_version` | string or null | yes | Denormalized index field. When derivable from `source_record`, it must equal `source_record.schema_version`; otherwise `null`. Never synthesize it. |
| `mapping_context` | object or null | yes | Reflects exactly what adapter mapping context was available. It may be `null`, empty, missing `run_id`, missing `seq`, or contain invalid values for rejected context cases. |
| `mapping_contract_version` | string | yes | Fixed literal `tinymux-to-noesis-telemetry-mapping-v0` until a finer-grained versioning scheme exists. |
| `adapter_processing_timestamp` | string | yes | UTC ISO-8601 timestamp for adapter processing/quarantine creation. Distinct from any source timestamp inside `source_record`; adapter receipt or processing time must not overwrite source time. |
| `diagnostic_details` | string or object | yes | Non-empty diagnostic information for every record, including `adapter_error`. This is where adapter exception or failure details belong. |
| `content_hash` | string or null | no | Optional integrity aid. It must never substitute for `source_record` or `source_record_raw`. |

`quarantine_id` identifies the quarantine record, not the TinyMUX source event.
The same source record may produce separate quarantine records during separate
processing attempts, so `source_event_id` is not a quarantine-record identifier.

`mapping_context`, when present, preserves adapter-owned context fields as
observed:

- `run_id` may be a string, `null`, missing, empty, or invalid;
- `seq` may be an integer, `null`, missing, or invalid;
- `mapping_version`, when present, records the requested mapping version.

The quarantine record must not synthesize `mapping_context`, `run_id`, or `seq`.

`adapter_processing_timestamp` is the record-creation time for the quarantine
record. It is the v0 equivalent of a generic recorded-at timestamp. It must
remain distinct from the source event timestamp because source time is evidence
from the TinyMUX-side record, while adapter processing time is evidence about
the adapter's handling of that record.

If `content_hash` is included, the hashing input is the exact
`source_record_raw` string when `source_record_raw` is non-null. Otherwise the
hashing input is deterministic compact JSON serialization of `source_record`
using sorted keys and no insignificant whitespace. The hash algorithm must be
identified in the field value, for example `sha256:<hex-digest>`.

## Relationship to NOESIS Telemetry

Quarantine records are never emitted as `noesis.telemetry.v0`.

Quarantine records must not be represented as NOESIS `ERROR`, `REFUSAL`, or any
other telemetry event type. They are structurally separate records identified by
`schema_version: "tinymux.mapping_quarantine.v0"`.

`noesis.telemetry.v0` remains governed by `ThresholdOps/noesis`.
`tinymux.mapping_quarantine.v0` is adapter-owned and belongs in
`ThresholdOps/noesis-tinymux`.

## No-Silent-Drop Guarantee

Every input accepted for processing ends in exactly one of:

- a `noesis.telemetry.v0` record;
- a `tinymux.mapping_quarantine.v0` record;
- an explicit, non-swallowed failure signal from the attempt to write the
  quarantine record itself.

Declaring success without producing either telemetry or quarantine is
prohibited.

If the quarantine write itself fails, that failure must be surfaced explicitly.
It must not be swallowed, downgraded to success, or treated as a completed
processing attempt.

A failure to persist a quarantine record is not represented by another
`tinymux.mapping_quarantine.v0` record in the same required sink. It must be
surfaced through an explicit external failure signal and must not be treated as
successful processing.

## Retention and Integrity

Source content is mandatory. Exactly one of `source_record` or
`source_record_raw` must be present and non-null.

`content_hash` is optional and may support integrity checks, deduplication, or
external indexing. It is never a substitute for the actual source content.

This contract does not define retention duration, deletion policy, storage
backend, or replay policy.

## Non-Goals

This document does not:

- add quarantine fixtures;
- add a quarantine validator;
- add CI;
- implement a runtime mapper;
- implement a storage backend;
- implement retry or replay;
- define a retention policy duration;
- define a runtime API;
- define a queue;
- define a sink.

Quarantine fixtures, a quarantine validator, and CI are separate future slices,
following the same phased pattern already used for the source and mapping
contracts.

## Worked Examples

The first three examples are derived from committed mapping fixture cases. The
raw-input and adapter-error examples are illustrative because they do not yet
have mapping fixture precedent.

### `mapping_outcome` / `UNRESOLVED`

Derived from
`fixtures/mapping/tinymux_to_noesis/v0/unresolved.json` case
`tinymux-to-noesis-v0-page-unresolved`.

```json
{"schema_version":"tinymux.mapping_quarantine.v0","quarantine_id":"quarantine-fixture-0001","quarantine_class":"mapping_outcome","outcome":"UNRESOLVED","rejection_category":null,"reason_code":"no_private_communication_event_type","source_record":{"schema_version":"tinymux.log_event.v0","event_id":"source-fixture-page-0001","timestamp":"2026-07-10T12:00:25Z","source":"tinymux","world":"fixture-world","room":{"dbref":"#100","name":"Fixture Room"},"actor":{"dbref":"#200","name":"Fixture Actor"},"target":{"dbref":"#300","name":"Fixture Target"},"event_type":"page","text":"This is a synthetic private page.","visibility":{"scope":"private","audience":["#200","#300"],"realm":null},"channel":"page","raw":{"verb":"page","mapping_status":"unresolved"}},"source_record_raw":null,"source_event_id":"source-fixture-page-0001","source_schema_version":"tinymux.log_event.v0","mapping_context":{"run_id":"fixture-run-0001","seq":6},"mapping_contract_version":"tinymux-to-noesis-telemetry-mapping-v0","adapter_processing_timestamp":"2026-07-10T12:00:25.100Z","diagnostic_details":"Valid page source record, but telemetry v0 has no PAGE_ATTEMPT or private communication event family.","content_hash":null}
```

### `mapping_outcome` / `REJECTED` / `source_contract`

Derived from `fixtures/mapping/tinymux_to_noesis/v0/rejected.json` case
`tinymux-to-noesis-v0-invalid-source-record-rejected`.

```json
{"schema_version":"tinymux.mapping_quarantine.v0","quarantine_id":"quarantine-fixture-0002","quarantine_class":"mapping_outcome","outcome":"REJECTED","rejection_category":"source_contract","reason_code":"invalid_source_record","source_record":{"schema_version":"tinymux.log_event.v0","event_id":"source-fixture-rejected-invalid-0001","timestamp":"2026-07-10T12:01:05Z","source":"tinymux","world":"fixture-world","room":{"dbref":100,"name":"Fixture Room"},"actor":{"dbref":"#200","name":"Fixture Actor"},"event_type":"say","text":"This record has a numeric room dbref.","visibility":{"scope":"room","audience":["#100"],"realm":null}},"source_record_raw":null,"source_event_id":"source-fixture-rejected-invalid-0001","source_schema_version":"tinymux.log_event.v0","mapping_context":{"run_id":"fixture-run-0001","seq":11},"mapping_contract_version":"tinymux-to-noesis-telemetry-mapping-v0","adapter_processing_timestamp":"2026-07-10T12:01:05.100Z","diagnostic_details":"Source record rejected by tinymux.log_event.v0 validation: numeric room dbref.","content_hash":null}
```

### `mapping_outcome` / `REJECTED` / `mapping_context`

Derived from `fixtures/mapping/tinymux_to_noesis/v0/rejected.json` case
`tinymux-to-noesis-v0-missing-mapping-context-rejected`.

```json
{"schema_version":"tinymux.mapping_quarantine.v0","quarantine_id":"quarantine-fixture-0003","quarantine_class":"mapping_outcome","outcome":"REJECTED","rejection_category":"mapping_context","reason_code":"missing_mapping_context","source_record":{"schema_version":"tinymux.log_event.v0","event_id":"source-fixture-rejected-missing-context-0001","timestamp":"2026-07-10T12:01:15Z","source":"tinymux","world":"fixture-world","room":{"dbref":"#100","name":"Fixture Room"},"actor":{"dbref":"#200","name":"Fixture Actor"},"event_type":"say","text":"This record lacks adapter mapping context.","visibility":{"scope":"room","audience":["#100"],"realm":null}},"source_record_raw":null,"source_event_id":"source-fixture-rejected-missing-context-0001","source_schema_version":"tinymux.log_event.v0","mapping_context":{},"mapping_contract_version":"tinymux-to-noesis-telemetry-mapping-v0","adapter_processing_timestamp":"2026-07-10T12:01:15.100Z","diagnostic_details":"A valid source record could not produce telemetry because adapter mapping context was absent.","content_hash":null}
```

### Raw Input / Unparseable Source Record

Illustrative only. This example is not derived from a current mapping fixture.
It shows the fallback shape when the input accepted for processing could not be
parsed as JSON at all.

```json
{"schema_version":"tinymux.mapping_quarantine.v0","quarantine_id":"quarantine-fixture-0004","quarantine_class":"mapping_outcome","outcome":"REJECTED","rejection_category":"source_contract","reason_code":"invalid_source_record","source_record":null,"source_record_raw":"{\"schema_version\":\"tinymux.log_event.v0\",\"event_id\":\"source-fixture-malformed-0001\",\"text\":\"unterminated synthetic input\"","source_event_id":null,"source_schema_version":null,"mapping_context":{"run_id":"fixture-run-0001","seq":12},"mapping_contract_version":"tinymux-to-noesis-telemetry-mapping-v0","adapter_processing_timestamp":"2026-07-10T12:01:25.100Z","diagnostic_details":"Synthetic source input could not be parsed as one complete JSON object.","content_hash":null}
```

### `adapter_error`

Illustrative only. This example is not derived from a current fixture.

```json
{"schema_version":"tinymux.mapping_quarantine.v0","quarantine_id":"quarantine-fixture-0005","quarantine_class":"adapter_error","outcome":null,"rejection_category":null,"reason_code":"adapter_error","source_record":{"schema_version":"tinymux.log_event.v0","event_id":"source-fixture-say-0001","timestamp":"2026-07-10T12:00:00Z","source":"tinymux","world":"fixture-world","room":{"dbref":"#100","name":"Fixture Room"},"actor":{"dbref":"#200","name":"Fixture Actor"},"event_type":"say","text":"This is a synthetic room speech event.","visibility":{"scope":"room","audience":["#100"],"realm":null},"raw":{"verb":"say"}},"source_record_raw":null,"source_event_id":"source-fixture-say-0001","source_schema_version":"tinymux.log_event.v0","mapping_context":{"run_id":"fixture-run-0001","seq":1},"mapping_contract_version":"tinymux-to-noesis-telemetry-mapping-v0","adapter_processing_timestamp":"2026-07-10T12:00:00.100Z","diagnostic_details":{"error_type":"AdapterProcessingError","message":"Illustrative unexpected adapter failure before mapping classification completed."},"content_hash":null}
```

## Open Questions

- Whether `adapter_error` will need finer subcategorization.
- Which storage backend will hold quarantine records.
- What retention duration applies to quarantine records.
- Whether quarantine records need a replay protocol.
- Whether `content_hash` should become mandatory after fixture and validator
  coverage exists.
