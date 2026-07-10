# TinyMUX Source Record Contract v0

## Status

Status: migration-stage normative source contract

This document is authoritative for new development in `noesis-tinymux`.

The corresponding document in `ThresholdOps/noesis` remains temporarily present
during migration. It must not yet be removed or marked deprecated. Behavioral
parity must be maintained until fixtures and validation are migrated.

## Scope

This contract describes one site-defined structured record:

- classified inside a TinyMUX world using softcode;
- emitted through a caller-controlled delivery surface such as `@log`;
- consumed by `noesis-tinymux`;
- translated later into tool-neutral NOESIS telemetry.

This contract:

- is not a TinyMUX standard;
- is not part of TinyMUX core;
- is not endorsed by TinyMUX maintainers;
- does not define a built-in TinyMUX event API;
- does not make player-visible TinyMUX output a stable machine-readable
  contract;
- does not define command submission, remote control, reactions, or write-back.

## Transport-Independent Record Model

The logical record is independent of a specific transport. The current working
serialization is one JSON object per line.

Rules:

- UTF-8 is required.
- Each physical line represents exactly one complete record.
- Records must not contain raw literal line breaks inside string values.
- JSON escaping must be used for embedded newline content.
- ANSI and presentation color sequences must not appear in the structured
  payload.
- Transport framing is not part of the semantic event model.
- `@log` is an early delivery candidate, not a proven production transport.

## Required Fields

The source contract identifier is `tinymux.log_event.v0`.

| Field | JSON type | Required | Allowed values | Semantic meaning | Validation constraints |
|---|---|---:|---|---|---|
| `schema_version` | string | yes | `tinymux.log_event.v0` | Contract identifier for this TinyMUX source record. | Must match exactly. Unknown identifiers must be rejected or quarantined. |
| `event_id` | string | yes | non-empty string | Source event identifier unique within the producing log stream or replay fixture. | Must be present and non-empty. Generation authority remains an open question. |
| `timestamp` | string | yes | UTC ISO-8601-like text | Source-side event timestamp emitted with the record. | Must include UTC timezone; trailing `Z` is accepted. |
| `source` | string | yes | currently `tinymux` | Source producer identifier. | Current migrated fixtures and validator expect `tinymux`. |
| `world` | string | yes | non-empty string | World or runtime identifier from the source environment. | Must be present. Exact configuration authority remains an open question. |
| `room` | object | yes | identity object | Observed room/location identity at the TinyMUX source boundary. | Must include string `dbref` or `id`; current fixtures use `dbref`. Current validation also requires string `name`. |
| `actor` | object or null | yes | identity object or `null` | Actor identity when the event has one. | If present, must include string `dbref` or `id`; current fixtures use `dbref`. Current validation also requires string `name`. `null` is currently valid only for `system` and `custom` records. |
| `event_type` | string | yes | `say`, `pose`, `emit`, `enter`, `leave`, `page`, `ooc`, `system`, `custom` | TinyMUX-side event vocabulary value. | Must be one of the v0 values. Unknown event types must not silently map to known types. |
| `text` | string | yes | any JSON string | Event text emitted by the softcode boundary. | Must be a string. Current validation expects non-empty text except for `enter`, `leave`, `system`, and `custom`. |
| `visibility` | object | yes | visibility object | Initial visibility context known at the TinyMUX softcode boundary. | Must be an object. Current validation accepts `visibility.scope` values `room`, `private`, `system`, and `custom`. |

## Optional Fields

### Stable Optional Fields

| Field | JSON type | Required | Semantic meaning | Validation constraints |
|---|---|---:|---|---|
| `target` | object or null | no | Direct target when the event has one, for example page recipient or movement target. | When present as an object, should follow the same identity representation as `actor` and `room`. |
| `channel` | string | no | Local channel or routing hint such as `room`, `page`, or `ooc`. | Advisory only; must not replace `event_type`. |

### Advisory Hints

| Field | JSON type | Required | Semantic meaning | Validation constraints |
|---|---|---:|---|---|
| `softcode` | object | no | Relay, listener, or softcode metadata. | Advisory; consumers must not require it for basic v0 parsing. |

### Reserved for Later Enrichment or Diagnostics

| Field | JSON type | Required | Semantic meaning | Validation constraints |
|---|---|---:|---|---|
| `raw` | object | no | Source-specific metadata preserved for diagnostics. | Optional and non-authoritative. It must not become the primary contract. |

Unknown optional fields must be tolerated unless they conflict with reserved
names or alter required-field semantics.

## Event Vocabulary

| `event_type` | TinyMUX-side activity | Meaningful fields | Mapping status |
|---|---|---|---|
| `say` | Room speech or speech-like activity classified by site softcode. | `actor`, `room`, `text`, `visibility`; `raw.verb` may identify the local command. | Expected to map later to a NOESIS speech attempt family, but mapping is not defined here. |
| `pose` | Character pose or action text classified by site softcode. | `actor`, `room`, `text`, `visibility`; `raw.verb` may identify the local command. | Expected to map later to a NOESIS pose attempt family, but mapping is not defined here. |
| `emit` | Room-visible emit or system-visible text classified as an event. | `room`, `text`, `visibility`; `actor` may depend on source. | Mapping details remain adapter work. |
| `enter` | Arrival or movement observation. | `actor`, `room`, `text`, `visibility`; `raw` may preserve origin/target hints. | Mapping details remain adapter work. |
| `leave` | Departure or movement observation. | `actor`, `room`, `text`, `visibility`; `raw` may preserve destination/target hints. | Mapping details remain adapter work. |
| `page` | Private or page-like communication observed by site-defined relay rules. | `actor`, `target`, `channel`, `text`, `visibility`. | Mapping remains unresolved; do not silently treat it as public room speech. |
| `ooc` | Out-of-character communication classified by site softcode. | `actor`, `channel`, `text`, `visibility`. | Mapping remains unresolved. |
| `system` | Softcode or system event such as relay checkpoint or heartbeat. | `actor` may be `null`; `raw` may carry relay metadata. | Mapping depends on explicit adapter classification. |
| `custom` | Site-defined event outside the fixed vocabulary. | `actor` may be `null`; `raw` or `softcode` should identify subtype. | Requires explicit subtype convention before normative mapping. |

This document preserves current v0 vocabulary. It does not broaden the event
set.

## Identity Representation

TinyMUX object and player identifiers are strings. Source records should
preserve TinyMUX forms such as:

```text
#123
```

TinyMUX database references must not be modeled as JSON integers.

Reasons:

- the `#` form is part of the source representation;
- string representation avoids accidental numeric coercion;
- later adapters may enrich identities without changing raw source identity.

Current source fixtures use identity objects shaped like:

```json
{"dbref":"#123","name":"Synthetic Actor"}
```

The current migrated validator also accepts `id` as a possible stable
identifier key, but existing v0 fixtures use `dbref`. Whether future v0 records
should require both `dbref` and `name`, or only a stable identifier, remains an
open compatibility question inherited from the NOESIS-side source contract.

## Time Semantics

The current source record requires `timestamp`.

For this source contract, `timestamp` is the time observed or emitted by the
TinyMUX-side source record. The exact timestamp generator may be site softcode,
the relay boundary, or another local source-side mechanism; that authority
remains an open question.

Adapter receipt time is separate and must not overwrite `timestamp`.

NOESIS telemetry normalization time is also separate. The NOESIS telemetry
contract defines its own timestamp field, `ts_utc`, in
`ThresholdOps/noesis/docs/telemetry-contract.md`.

## Compatibility Rules

- Unknown optional fields must be tolerated unless they conflict with reserved
  names.
- Unknown contract identifiers must be rejected or quarantined.
- Missing required fields must fail validation.
- Invalid JSON must fail framing or parsing.
- Unknown event types must not silently map to a different known event type.
- Adapters must preserve the original source record or sanitized raw evidence
  where the NOESIS telemetry contract permits it.
- Additive changes within v0 must not alter existing field semantics.
- Incompatible changes require a new contract version.

## Privacy and Visibility

`visibility` is source-side evidence, not proof of authorization.

Current visibility metadata is an object whose `scope` is validated against:

- `room`
- `private`
- `system`
- `custom`

The older NOESIS-side draft also mentioned `global` as an example, but current
fixtures and validation do not accept it. Treat `global` as unresolved until a
later contract revision explicitly decides it.

The adapter must not infer omniscient visibility. Private or restricted content
must not be emitted merely because a relay can technically access it. Synthetic
public fixtures must not contain real player data or private world content.

This document does not introduce a new permissions model.

## Valid Examples

Ordinary speech-like event:

```json
{"schema_version":"tinymux.log_event.v0","event_id":"synthetic-say-0001","timestamp":"2026-07-10T12:00:00Z","source":"tinymux","world":"synthetic-world","room":{"dbref":"#100","name":"Test Room"},"actor":{"dbref":"#200","name":"Test Speaker"},"event_type":"say","text":"This is a synthetic test line.","visibility":{"scope":"room","audience":["#100"],"realm":null},"raw":{"verb":"+say"}}
```

Non-speech event:

```json
{"schema_version":"tinymux.log_event.v0","event_id":"synthetic-pose-0001","timestamp":"2026-07-10T12:00:05Z","source":"tinymux","world":"synthetic-world","room":{"dbref":"#100","name":"Test Room"},"actor":{"dbref":"#200","name":"Test Speaker"},"event_type":"pose","text":"Test Speaker checks the synthetic door.","visibility":{"scope":"room","audience":["#100"],"realm":null},"raw":{"verb":"+pose"}}
```

## Invalid Examples

Malformed JSON:

```text
{"schema_version":"tinymux.log_event.v0","event_id":"bad"
```

Invalid because each physical line must be one complete JSON object.

Missing contract identifier:

```json
{"event_id":"bad-missing-schema","timestamp":"2026-07-10T12:00:00Z","source":"tinymux","world":"synthetic-world","room":{"dbref":"#100","name":"Test Room"},"actor":{"dbref":"#200","name":"Test Speaker"},"event_type":"say","text":"Missing schema.","visibility":{"scope":"room"}}
```

Invalid because `schema_version` is required.

Unsupported contract version:

```json
{"schema_version":"tinymux.log_event.v9","event_id":"bad-version","timestamp":"2026-07-10T12:00:00Z","source":"tinymux","world":"synthetic-world","room":{"dbref":"#100","name":"Test Room"},"actor":{"dbref":"#200","name":"Test Speaker"},"event_type":"say","text":"Wrong version.","visibility":{"scope":"room"}}
```

Invalid because the v0 identifier must be exactly `tinymux.log_event.v0`.

Missing required identity field:

```json
{"schema_version":"tinymux.log_event.v0","event_id":"bad-identity","timestamp":"2026-07-10T12:00:00Z","source":"tinymux","world":"synthetic-world","room":{"name":"Test Room"},"actor":{"dbref":"#200","name":"Test Speaker"},"event_type":"say","text":"Bad room identity.","visibility":{"scope":"room"}}
```

Invalid because `room` lacks a stable string identifier such as `dbref`.

Numeric TinyMUX object reference:

```json
{"schema_version":"tinymux.log_event.v0","event_id":"bad-numeric-dbref","timestamp":"2026-07-10T12:00:00Z","source":"tinymux","world":"synthetic-world","room":{"dbref":100,"name":"Test Room"},"actor":{"dbref":"#200","name":"Test Speaker"},"event_type":"say","text":"Numeric dbref.","visibility":{"scope":"room"}}
```

Invalid because TinyMUX object references must be strings, not JSON numbers.

Raw multiline framing:

```text
{"schema_version":"tinymux.log_event.v0","event_id":"bad-multiline","timestamp":"2026-07-10T12:00:00Z","source":"tinymux","world":"synthetic-world","room":{"dbref":"#100","name":"Test Room"},"actor":{"dbref":"#200","name":"Test Speaker"},"event_type":"say","text":"first line
second line","visibility":{"scope":"room"}}
```

Invalid because raw literal line breaks are not allowed inside a physical JSONL
record. Embedded newline content must be JSON-escaped.

Raw ANSI sequence in payload:

```json
{"schema_version":"tinymux.log_event.v0","event_id":"bad-ansi","timestamp":"2026-07-10T12:00:00Z","source":"tinymux","world":"synthetic-world","room":{"dbref":"#100","name":"Test Room"},"actor":{"dbref":"#200","name":"Test Speaker"},"event_type":"say","text":"\\u001b[31mred presentation text\\u001b[0m","visibility":{"scope":"room"}}
```

Invalid because ANSI and presentation color sequences must not appear in the
structured payload.

## Relationship to NOESIS Telemetry

```text
TinyMUX source record
  governed by ThresholdOps/noesis-tinymux

TinyMUX-to-NOESIS mapping
  governed by ThresholdOps/noesis-tinymux

NOESIS telemetry output
  governed by ThresholdOps/noesis
```

The TinyMUX source record is adapter input. The NOESIS telemetry record is
normalized adapter output and remains governed by the authoritative NOESIS
telemetry contract in `ThresholdOps/noesis/docs/telemetry-contract.md`.

The mapping specification and mapping fixtures will be migrated in later
slices. This document does not define the full mapping.

## Migration Note

This document follows `docs/artifact-ownership.md` and is Phase 1 of the
migration.

Source fixtures remain temporarily in NOESIS. Validation remains temporarily in
NOESIS. Migration coverage must be established in `noesis-tinymux` before old
copies are deprecated.

This document must remain behaviorally compatible with the current NOESIS-side
source contract during that transition.

## Non-Goals

This slice does not:

- add schemas;
- add fixtures;
- add validators;
- add CI;
- implement a parser;
- implement replay;
- implement file tailing;
- implement softcode;
- modify TinyMUX;
- modify NOESIS;
- select a production transport;
- declare `@log` proven for production transport;
- implement write-back.
