# TinyMUX to NOESIS Telemetry Mapping v0

## Status

Status: migration-stage normative adapter mapping

This document is authoritative for new mapping development in
`noesis-tinymux`.

The older mapping document remains temporarily present in `ThresholdOps/noesis`
during migration. Behavioral parity must be proven through adapter-owned mapping
fixtures and validation before the NOESIS copy is deprecated.

This document does not implement the mapping.

## Purpose

This document defines the planned adapter mapping:

```text
tinymux.log_event.v0
-> noesis.telemetry.v0
```

TinyMUX source records are adapter input. NOESIS telemetry records are adapter
output.

The adapter must preserve factual source evidence without inventing world truth.
The mapping is deterministic wherever the source and output contracts permit it.
Unresolved mappings must be rejected, quarantined, or explicitly marked
unresolved rather than guessed.

## Authority Boundary

```text
TinyMUX source record
  governed by ThresholdOps/noesis-tinymux

TinyMUX-to-NOESIS mapping
  governed by ThresholdOps/noesis-tinymux

NOESIS telemetry output
  governed by ThresholdOps/noesis
```

`noesis-tinymux` must not redefine `noesis.telemetry.v0`.

`ThresholdOps/noesis` must not remain the long-term authority for
TinyMUX-specific mapping rules.

Mapping fixtures will belong to the adapter repository in a later slice.

## Inputs

Input records use `tinymux.log_event.v0`, defined by
`docs/tinymux-source-record-v0.md`.

Required source fields:

- `schema_version`
- `event_id`
- `timestamp`
- `source`
- `world`
- `room`
- `actor`
- `event_type`
- `text`
- `visibility`

Optional source fields:

- `target`
- `channel`
- `softcode`
- `raw`

This document does not expand the TinyMUX source contract.

## Outputs

Output records use `noesis.telemetry.v0`, defined by
`ThresholdOps/noesis/docs/telemetry-contract.md`.

Required telemetry fields:

- `schema_version`
- `event_id`
- `ts_utc`
- `run_id`
- `seq`
- `event_type`
- `event_phase`
- `producer`
- `actor`
- `location`
- `raw`

Optional NOESIS enrichment fields such as `perception`, `realms`, `observers`,
`render_hints`, and `resolved` remain downstream and non-authoritative. This
adapter mapping does not produce authoritative enrichment unless a later
document explicitly defines it.

This document does not copy or redefine the NOESIS telemetry contract.

## Mapping Principles

- Source classification occurs inside TinyMUX before prose scraping.
- Player-visible output is not canonical adapter input.
- Source event identity must be preserved diagnostically.
- Source timestamp must not be overwritten by adapter receipt time.
- Visibility is source evidence, not resolved perception.
- Mapping must not manufacture `perceived_by`, observers, realms, or
  authorization conclusions.
- Raw source content must be preserved where the telemetry contract allows.
- Unresolved source event types must not silently map to unrelated telemetry
  families.
- No mapping rule may depend on production-specific names or DBREFs.
- Adapters must fail closed on unsupported source contract versions.

## Field Mapping

| TinyMUX source field | NOESIS telemetry destination | Mapping rule | Lossiness | Open question |
|---|---|---|---|---|
| `schema_version` | `schema_version`; `raw.realm_tx_raw` | Output `schema_version` must be exactly `noesis.telemetry.v0`. Preserve source `tinymux.log_event.v0` diagnostically in source metadata under `raw.realm_tx_raw`. Do not overwrite output schema identity with input schema identity. | No loss for source schema if raw metadata is preserved. | Whether `raw.realm_tx_raw` should remain structured or become canonical serialized text is still contract-bound. |
| `event_id` | `event_id`; `raw.realm_tx_raw.event_id` | Source event ID and telemetry event ID are distinct concepts. Current migration fixtures generate a telemetry `event_id` and preserve source `event_id` under `raw.realm_tx_raw.event_id`; this is the v0 fixture-compatibility rule for examples. | No source ID loss if raw metadata is preserved. | Final production ID policy remains open: reuse source ID or generate telemetry ID with source reference. |
| `timestamp` | `ts_utc` | Validate source timestamp as UTC and map it to telemetry `ts_utc`. Adapter receipt time must remain separate. Do not generate a replacement timestamp merely because parsing occurred later. | No intended loss. | None for current fixture-compatible UTC values. |
| `source` | `producer` and raw metadata | Preserve original source system `tinymux` as source evidence. The telemetry producer describes the normalized telemetry producer. Recommended v0 values: `producer.kind = "mux_emitter"`, `producer.source = "tinymux"` for source-emitter-compatible fixtures or a later explicit adapter value such as `noesis-tinymux.adapter`, and `producer.authoritative = true` for accepted MUX-side emitted records. | Potential ambiguity between source system and adapter component unless producer convention is tightened. | Whether `producer.source` should name the source system or adapter component in production remains to be finalized. |
| `world` | `raw.realm_context_raw`; `raw.realm_tx_raw.world` | Preserve world as raw source context unless the NOESIS telemetry contract defines a normalized authoritative world destination. Do not claim adapter ownership of canonical world state. | No intended loss if both raw fields are retained. | Whether world should also map to a future normalized realm/world field is open. |
| `room` | `location`; raw metadata | Map `room.dbref` to `location.dbref` and `room.name` to `location.name_raw`. Preserve additional room fields diagnostically if compatible. | Additional room fields may be lossy unless serialized in raw metadata. | None for current `dbref`/`name` fixture shape. |
| `actor` | `actor`; raw metadata | Map `actor.dbref` to `actor.dbref` and `actor.name` to `actor.name_raw`. If source `actor` is `null`, output `actor` must remain `null` unless an explicit mapping rule says otherwise. Do not synthesize an actor from room, source, or text. | Additional actor fields may be lossy unless serialized in raw metadata. | None for current `dbref`/`name` fixture shape. |
| `event_type` | `event_type`; `event_phase`; `raw.verb_raw` when available | Map through the event-type table below. `event_type` must not be overridden by `channel` or free text. | No loss for defined event types. | `page`, `ooc`, `system`, and `custom` remain partly or fully unresolved. |
| `text` | `raw.content_raw` | Preserve original event content as `raw.content_raw`. Do not normalize, rewrite, summarize, or render the text. | No intended loss. | None; old open question about text placement is resolved for current telemetry v0 by `raw.content_raw`. |
| `visibility` | `raw.perception_context_raw` | Preserve visibility as source evidence under `raw.perception_context_raw`. Do not emit final perception sets. | No intended loss if structured raw representation remains accepted. | Whether visibility should also become a normalized visibility hint remains open. |
| `target` | `raw.target_raw`; `raw.to_dbref`; source metadata | Preserve target evidence under `raw.target_raw` and, when the semantics clearly indicate a destination object, `raw.to_dbref`. Do not infer destination semantics when target meaning is ambiguous. | May be lossy if target has name or extra fields and only DBREF/string is preserved. | Exact representation for page recipient versus movement destination remains mapping-specific. |
| `channel` | `raw.command_raw`, `raw.verb_raw`, or source metadata | Preserve channel as raw routing/source metadata. Do not let `channel` override `event_type`. | No intended loss if source metadata retained. | Whether channel deserves a canonical raw slot is open. |
| `softcode` | `raw.realm_tx_raw` source metadata | Preserve only as diagnostic source metadata. Do not make relay implementation metadata part of normalized world truth. | No intended loss if source metadata retained. | Structured source metadata representation remains open. |
| `raw` | reserved `raw.*` fields and `raw.realm_tx_raw` metadata | Preserve source diagnostic metadata without allowing it to overwrite normalized telemetry fields. Collision rule: normalized telemetry fields win; source `raw` remains nested or serialized as source evidence. | Potential loss if the telemetry raw field representation is later restricted. | Whether nested structured raw metadata is officially allowed by `noesis.telemetry.v0` remains open. |

## Raw Metadata Representation

The current NOESIS telemetry contract reserves these raw fields:

- `command_raw`
- `content_raw`
- `verb_raw`
- `from_dbref`
- `to_dbref`
- `realm_tx_raw`
- `realm_rx_raw`
- `realm_context_raw`
- `perception_context_raw`
- `target_raw`
- `error_raw`

It does not define a general top-level `source_event` field.

The existing NOESIS mapping fixtures preserve structured source metadata under
`raw.realm_tx_raw` and structured visibility under `raw.perception_context_raw`.
The existing mapping fixture validator accepts that shape. The generic telemetry
fixtures commonly use scalar strings or `null` in the reserved raw fields, and
the telemetry validator checks field presence rather than enforcing scalar-only
values.

The narrowest migration-compatible representation is therefore:

- put event content in `raw.content_raw`;
- put local verb or command hint in `raw.verb_raw` or `raw.command_raw` when
  available;
- put source schema, source event ID, world, and source diagnostic metadata in
  `raw.realm_tx_raw`;
- put source visibility evidence in `raw.perception_context_raw`;
- put movement or target DBREFs in `raw.from_dbref`, `raw.to_dbref`, and
  `raw.target_raw` only when semantically justified;
- fill other reserved raw fields with `null` when unavailable.

If future NOESIS validation requires raw fields to be scalar strings, structured
source metadata must be serialized deterministically as compact JSON with sorted
keys and no insignificant whitespace. Until that is decided, structured raw
objects remain a migration-compatibility shape rather than a new telemetry
contract.

This document does not introduce a new telemetry field.

## Event-Type Mapping

| TinyMUX `event_type` | NOESIS `event_type` | `event_phase` | Mapping status | Notes |
|---|---|---|---|---|
| `say` | `SAY_ATTEMPT` | `attempt` | DEFINED | Room speech observation. Preserve original text in `raw.content_raw`; preserve visibility as source evidence. |
| `pose` | `POSE_ATTEMPT` | `attempt` | DEFINED | Character pose/action observation. Preserve pose text in `raw.content_raw`. |
| `emit` | `ROOM_EMIT` | `emit` | DEFINED | Room-visible emit when explicitly classified as `emit`. Do not infer emit from arbitrary text. |
| `enter` | `MOVE_ATTEMPT` | `attempt` | DEFINED | Arrival/movement observation. Current room maps to `location`; origin evidence is preserved only when supplied. |
| `leave` | `MOVE_ATTEMPT` | `attempt` | DEFINED | Departure/movement observation. Current room maps to `location`; destination evidence is preserved only when supplied. |
| `page` | none in v0 | none | UNRESOLVED | Telemetry v0 does not define `PAGE_ATTEMPT`. Do not map private communication to public room speech merely because `SAY_ATTEMPT` exists. |
| `ooc` | none by default | none | UNRESOLVED | Do not automatically treat OOC as `ROOM_EMIT`. A deliberate compatibility mapping or telemetry event family is required. |
| `system` | conditional: `ROOM_EMIT`, `ERROR`, or `REFUSAL` | conditional | CONDITIONAL | Requires explicit source classification or subtype. Do not infer error/refusal from arbitrary text. |
| `custom` | none by default | none | REQUIRES_SUBTYPE | Requires a documented subtype convention. Unknown custom subtypes must not map automatically. |

## Movement Semantics

For `enter` and `leave`, the current room may map to telemetry `location`.

Origin and destination evidence may appear in source `target`, source `raw`, or
other source fields. The adapter must not invent missing origin or destination
DBREFs.

When source evidence is present and unambiguous:

- source origin may map to `raw.from_dbref`;
- source destination may map to `raw.to_dbref`;
- movement target or exit label may map to `raw.target_raw`.

Mapping fixtures must expose insufficient-evidence cases before runtime mapping
uses them.

## Error and Refusal Semantics

TinyMUX `system` or `custom` source records are not automatically NOESIS
`ERROR` or `REFUSAL`.

Adapter parsing failures may produce telemetry `ERROR` events only under a
separately defined runtime error policy.

World action refusals require explicit classification evidence from the source
record or adapter policy.

Arbitrary text matching is prohibited.

This slice does not define runtime error generation.

## Sequence and Run Identity

The source record contract does not currently provide:

- `run_id`
- `seq`

These are adapter/output responsibilities.

Requirements:

- `run_id` identifies one adapter capture or replay run;
- `seq` is monotonic within that run;
- ordering follows accepted source-record processing order;
- source `event_id` must not substitute for `seq`;
- replay and live ingestion should use the same deterministic ordering semantics
  where practical.

This document does not prescribe a storage backend.

## Mapping Outcomes

Each mapping attempt has one of three outcomes:

- `MAPPED`: deterministic valid telemetry output exists.
- `UNRESOLVED`: the source record is valid, but telemetry v0 lacks a safe
  mapping.
- `REJECTED`: the source record or source version is invalid or unsupported.

Unresolved records must not disappear silently.

A later fixture slice should encode these outcomes.

## Worked Examples

### Fully Mapped `say`

Source record:

```json
{"schema_version":"tinymux.log_event.v0","event_id":"source-example-say-0001","timestamp":"2026-07-10T12:00:00Z","source":"tinymux","world":"fixture-world","room":{"dbref":"#100","name":"Fixture Room"},"actor":{"dbref":"#200","name":"Fixture Actor"},"event_type":"say","text":"This is a synthetic room speech event.","visibility":{"scope":"room","audience":["#100"],"realm":null},"raw":{"verb":"say"}}
```

Expected telemetry record:

```json
{"schema_version":"noesis.telemetry.v0","event_id":"telemetry-example-say-0001","ts_utc":"2026-07-10T12:00:00Z","run_id":"mapping-example-run-0001","seq":1,"event_type":"SAY_ATTEMPT","event_phase":"attempt","producer":{"kind":"mux_emitter","source":"tinymux","authoritative":true},"actor":{"dbref":"#200","name_raw":"Fixture Actor"},"location":{"dbref":"#100","name_raw":"Fixture Room"},"raw":{"command_raw":null,"content_raw":"This is a synthetic room speech event.","verb_raw":"say","from_dbref":null,"to_dbref":null,"realm_tx_raw":{"schema_version":"tinymux.log_event.v0","event_id":"source-example-say-0001","world":"fixture-world","raw":{"verb":"say"}},"realm_rx_raw":null,"realm_context_raw":"fixture-world","perception_context_raw":{"scope":"room","audience":["#100"],"realm":null},"target_raw":null,"error_raw":null}}
```

### Fully Mapped Movement

Source record:

```json
{"schema_version":"tinymux.log_event.v0","event_id":"source-example-enter-0001","timestamp":"2026-07-10T12:00:05Z","source":"tinymux","world":"fixture-world","room":{"dbref":"#101","name":"Arrival Room"},"actor":{"dbref":"#200","name":"Fixture Actor"},"event_type":"enter","text":"","visibility":{"scope":"room","audience":["#101"],"realm":null},"raw":{"from_dbref":"#100","to_dbref":"#101","target_raw":"north"}}
```

Expected telemetry record:

```json
{"schema_version":"noesis.telemetry.v0","event_id":"telemetry-example-enter-0001","ts_utc":"2026-07-10T12:00:05Z","run_id":"mapping-example-run-0001","seq":2,"event_type":"MOVE_ATTEMPT","event_phase":"attempt","producer":{"kind":"mux_emitter","source":"tinymux","authoritative":true},"actor":{"dbref":"#200","name_raw":"Fixture Actor"},"location":{"dbref":"#101","name_raw":"Arrival Room"},"raw":{"command_raw":null,"content_raw":"","verb_raw":"enter","from_dbref":"#100","to_dbref":"#101","realm_tx_raw":{"schema_version":"tinymux.log_event.v0","event_id":"source-example-enter-0001","world":"fixture-world","raw":{"from_dbref":"#100","to_dbref":"#101","target_raw":"north"}},"realm_rx_raw":null,"realm_context_raw":"fixture-world","perception_context_raw":{"scope":"room","audience":["#101"],"realm":null},"target_raw":"north","error_raw":null}}
```

### Unresolved `page`

Source record:

```json
{"schema_version":"tinymux.log_event.v0","event_id":"source-example-page-0001","timestamp":"2026-07-10T12:00:10Z","source":"tinymux","world":"fixture-world","room":{"dbref":"#100","name":"Fixture Room"},"actor":{"dbref":"#200","name":"Fixture Actor"},"target":{"dbref":"#300","name":"Fixture Target"},"event_type":"page","text":"This is a synthetic private page.","visibility":{"scope":"private","audience":["#200","#300"],"realm":null},"channel":"page","raw":{"verb":"page"}}
```

Expected mapping outcome: `UNRESOLVED`.

No final telemetry record is asserted because `noesis.telemetry.v0` does not
currently define `PAGE_ATTEMPT`, and private communication must not be silently
mapped to public room speech.

## Compatibility and Versioning

This mapping version is tied to both:

- `tinymux.log_event.v0`
- `noesis.telemetry.v0`

Unsupported source versions are rejected.

Incompatible telemetry contract changes require a new mapping version or an
explicit compatibility update.

Additive source fields may be preserved diagnostically. Source semantics must
not be altered silently.

Fixture parity must be maintained during migration.

`compatibility/noesis-telemetry-v0.json` pins the exact `ThresholdOps/noesis`
commit used as the compatible `noesis.telemetry.v0` contract and fixture
reference for this mapping document and its fixtures. Updating that reference
is a deliberate compatibility review step, not an automatic branch-tracking
operation.

## Migration Note

This document follows `docs/artifact-ownership.md` and is Phase 2 documentation.

Mapping fixtures remain temporarily in NOESIS. The old NOESIS mapping document
also remains temporarily present.

The next slices will migrate mapping fixtures, validation, and CI.

NOESIS artifacts must not be deprecated until adapter-side parity is proven.

The source-fixture CI slice is still pending and should be completed before
switching responsibility or removing anything from `ThresholdOps/noesis`.

## Open Questions

- Should telemetry `event_id` reuse source `event_id`, or should telemetry
  generate a new ID while preserving source `event_id` in raw metadata?
- Does `noesis.telemetry.v0` need `PAGE_ATTEMPT`?
- Does `noesis.telemetry.v0` need `OOC_ATTEMPT`?
- How should `custom` source event subtypes be declared?
- Should structured source metadata remain valid in reserved raw fields, or
  should it become deterministic compact JSON strings?
- Should `visibility.scope` remain only `raw.perception_context_raw`, or also
  become a normalized visibility hint?
- How should movement records represent insufficient origin or destination
  evidence?
- Should `producer.source` identify `tinymux`, `noesis-tinymux.adapter`, or both
  through separate fields in a later contract revision?

## Non-Goals

This slice does not:

- add mapping fixtures;
- add mapping validators;
- add CI;
- implement parser or mapper code;
- modify source fixtures;
- modify telemetry fixtures;
- modify NOESIS;
- modify TinyMUX;
- define production transport;
- implement replay;
- implement file tailing;
- implement softcode;
- implement live connectivity;
- implement perception;
- implement write-back.
