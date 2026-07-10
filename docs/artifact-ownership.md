# Artifact Ownership and Migration Plan

## Purpose

This document defines artifact ownership boundaries between:

- `ThresholdOps/noesis`
- `ThresholdOps/noesis-tinymux`

It is a planning snapshot based on the current default branches. It is not an
implementation change and does not move, copy, delete, rename, or deprecate any
existing artifact by itself.

## Ownership Principles

- NOESIS remains tool-neutral.
- TinyMUX-specific source contracts, fixtures, mappings, parsers, and transport
  experiments belong in `noesis-tinymux`.
- Generic telemetry contracts remain authoritative in NOESIS.
- `noesis-tinymux` may reference or consume generic NOESIS contracts but must
  not redefine them independently.
- Migration must preserve validation coverage before old artifacts are
  deprecated.
- No artifact should exist as an independently editable authoritative copy in
  both repositories.

## Current Artifact Inventory

| Artifact | Current repository | Current role | Recommended status | Target authority | Reasoning | Migration dependency |
|---|---|---|---|---|---|---|
| `README.md` | `ThresholdOps/noesis` | Public project overview and current integration-boundary note. | KEEP_IN_NOESIS | `ThresholdOps/noesis` | The file defines NOESIS project scope and points to contract docs; it is not a TinyMUX source-record contract. | Later update links after TinyMUX-specific authority exists in `noesis-tinymux`. |
| `PROJECT.md` | `ThresholdOps/noesis` | NOESIS source-of-truth hierarchy and responsibility split. | KEEP_IN_NOESIS | `ThresholdOps/noesis` | It states TinyMUX world state is authoritative while telemetry belongs to NOESIS observability; this is core NOESIS governance. | None. |
| `LAYERS.md` | `ThresholdOps/noesis` | NOESIS 32 REALMS governance on top of TinyMUX Reality Levels. | KEEP_IN_NOESIS | `ThresholdOps/noesis` | It defines NOESIS semantic governance while treating TinyMUX Reality Levels as mechanism. | None. |
| `docs/telemetry-contract.md` | `ThresholdOps/noesis` | `noesis.telemetry.v0` contract, required fields, event families, and raw/enrichment distinction. | REFERENCE_FROM_NOESIS_TINYMUX | `ThresholdOps/noesis` | This is the tool-neutral output contract that adapters must produce; `noesis-tinymux` should validate against it, not redefine it. | `noesis-tinymux` must reference this contract before adding adapter output fixtures. |
| `fixtures/telemetry/v0/README.md` and `fixtures/telemetry/v0/*.jsonl` | `ThresholdOps/noesis` | Sample `noesis.telemetry.v0` fixture records for SAY, MOVE, REFUSAL, and ERROR. | REFERENCE_FROM_NOESIS_TINYMUX | `ThresholdOps/noesis` | The fixtures describe NOESIS telemetry output shape, even though their current README mentions bridge migration context. | Adapter mapping tests should consume or mirror expectations from these fixtures without becoming a second telemetry authority. |
| `tests/test_telemetry_v0_fixtures.py` | `ThresholdOps/noesis` | Standard-library validator for telemetry v0 fixture shape. | REFERENCE_FROM_NOESIS_TINYMUX | `ThresholdOps/noesis` | The validator checks generic telemetry fields, producer fields, reserved raw fields, event types, and phases. | `noesis-tinymux` should validate mapped output against the same contract semantics. |
| `tests/check_python_syntax.py` | `ThresholdOps/noesis` | Generic repository Python syntax check. | KEEP_IN_NOESIS | `ThresholdOps/noesis` | It is repository hygiene and does not encode TinyMUX source semantics. | None. |
| `.github/workflows/ci.yml` | `ThresholdOps/noesis` | CI currently runs TinyMUX log fixture validation, telemetry fixture validation, TinyMUX-to-telemetry mapping validation, and Python syntax checks. | NEEDS_REVIEW | Split authority | The workflow mixes generic NOESIS checks with TinyMUX-specific validators that should move with their fixtures. | After migration, keep telemetry and syntax checks in NOESIS; move TinyMUX source and mapping checks to `noesis-tinymux`. |
| `.github/workflows/deploy.yml` | `ThresholdOps/noesis` | NOESIS VPS deploy workflow. | KEEP_IN_NOESIS | `ThresholdOps/noesis` | It is operational deployment for NOESIS and does not define TinyMUX source payloads. | None. |
| `docs/adr/ADR-0001-tinymux-read-side-integration-softcode-log.md` | `ThresholdOps/noesis` | Accepted ADR for TinyMUX softcode relay plus caller-controlled `@log` read-side boundary. | MOVE_TO_NOESIS_TINYMUX | `ThresholdOps/noesis-tinymux` | Its primary subject is TinyMUX-specific read-side integration, `@log`, softcode relay behavior, and replay input direction. | Add equivalent adapter-side decision record or source-boundary document before deprecating the NOESIS copy. |
| `docs/adr-0001-tinymux-read-side-integration.md` | `ThresholdOps/noesis` | Deprecated pointer to the canonical TinyMUX ADR. | DEPRECATE_AFTER_MIGRATION | `ThresholdOps/noesis` | It is already a compatibility pointer and should not become a second authority after the TinyMUX ADR moves. | Remove or replace after the adapter repository contains the authoritative TinyMUX boundary document. |
| `docs/adr/README.md` | `ThresholdOps/noesis` | ADR index currently listing only the TinyMUX read-side ADR. | DEPRECATE_AFTER_MIGRATION | `ThresholdOps/noesis` | The index itself can remain a NOESIS artifact, but the TinyMUX-specific ADR entry should not remain authoritative after migration. | Update after the ADR/boundary content is established in `noesis-tinymux`. |
| `docs/tinymux/event-schema-v0.md` | `ThresholdOps/noesis` | TinyMUX softcode-emitted `@log` JSONL source record contract. | MOVE_TO_NOESIS_TINYMUX | `ThresholdOps/noesis-tinymux` | It defines TinyMUX-specific source payload fields, event types, visibility hints, and replay fixture expectations. | Establish this source contract in `noesis-tinymux` before moving fixtures or validators. |
| `fixtures/tinymux/log_events/v0/README.md` and `fixtures/tinymux/log_events/v0/*.jsonl` | `ThresholdOps/noesis` | TinyMUX `@log` source-record replay fixtures. | MOVE_TO_NOESIS_TINYMUX | `ThresholdOps/noesis-tinymux` | These are TinyMUX-specific source inputs and explicitly not player-visible transcript captures. | Move only after `noesis-tinymux` has the source record contract and local validation. |
| `tests/test_tinymux_log_event_fixtures.py` | `ThresholdOps/noesis` | Validator for TinyMUX `tinymux.log_event.v0` JSONL fixtures. | MOVE_TO_NOESIS_TINYMUX | `ThresholdOps/noesis-tinymux` | It validates TinyMUX source fields, event vocabulary, visibility scopes, and identity object shape. | Move with source fixtures and keep CI coverage active during the transition. |
| `docs/tinymux/tinymux-log-to-telemetry-mapping-v0.md` | `ThresholdOps/noesis` | Mapping specification from TinyMUX `@log` records to NOESIS telemetry v0. | MOVE_TO_NOESIS_TINYMUX | `ThresholdOps/noesis-tinymux` | Mapping from a TinyMUX source format to generic telemetry belongs with the adapter that owns the source semantics. | Requires the TinyMUX source contract and reference to `docs/telemetry-contract.md`. |
| `fixtures/mapping/tinymux_log_to_telemetry/v0/README.md` and `fixtures/mapping/tinymux_log_to_telemetry/v0/*.json` | `ThresholdOps/noesis` | TinyMUX-to-telemetry mapping examples, including unresolved PAGE mapping. | MOVE_TO_NOESIS_TINYMUX | `ThresholdOps/noesis-tinymux` | These fixtures combine TinyMUX source input with expected NOESIS telemetry output and are adapter conformance material. | Move after both source fixtures and telemetry references are in place. |
| `tests/test_tinymux_to_telemetry_mapping_fixtures.py` | `ThresholdOps/noesis` | Validator for TinyMUX-to-telemetry mapping fixture shape. | MOVE_TO_NOESIS_TINYMUX | `ThresholdOps/noesis-tinymux` | It checks TinyMUX input shape, mapped NOESIS output shape, open-question cases, and absence of computed `perceived_by`. | Move with mapping fixtures and preserve CI before deprecating the NOESIS copy. |
| `docs/telemetry-migration-plan.md` | `ThresholdOps/noesis` | Plan for moving current prototype bridge telemetry toward `noesis.telemetry.v0`. | DEPRECATE_AFTER_MIGRATION | `ThresholdOps/noesis` | It is a NOESIS bridge migration snapshot that references TinyMUX `@log` as source, but it should not remain the adapter-source authority. | Replace active TinyMUX-source steps with `noesis-tinymux` references after migration. |
| `docs/audits/2026-07-09-contract-implementation-gap.md` | `ThresholdOps/noesis` | Historical audit of NOESIS contract-vs-implementation gaps. | KEEP_IN_NOESIS | `ThresholdOps/noesis` | It audits NOESIS service and documentation gaps; it is historical evidence, not an active TinyMUX payload authority. | None; later audits may reference adapter ownership. |
| `docs/runtime/prototype-status.md` | `ThresholdOps/noesis` | Classification of NOESIS runtime/service files as prototype or fallback. | KEEP_IN_NOESIS | `ThresholdOps/noesis` | It documents NOESIS runtime status and warns contributors not to treat prototype bridge files as canonical. | Update references after TinyMUX adapter authority exists. |
| `docs/ops/deploy-risk-and-gating.md` | `ThresholdOps/noesis` | NOESIS deploy risk and current validation gate note. | KEEP_IN_NOESIS | `ThresholdOps/noesis` | It is operational guidance for the NOESIS repository, not a TinyMUX source contract. | Update CI references after TinyMUX-specific validators move. |
| `docs/MANIFEST.md` | `ThresholdOps/noesis` | Older TinyMUX-oriented runtime manifest with `/opt/tinymux` paths and bridge/replay layout. | NEEDS_REVIEW | Unresolved | Current audit content identifies it as a source-of-truth conflict with root `MANIFEST.md`. | Decide whether to mark it historical in NOESIS or split any adapter-relevant content into `noesis-tinymux`. |
| `docs/LAYERS-ATTRS.md` | `ThresholdOps/noesis` | Attribute-level reality-layer contract using TinyMUX-specific nomenclature and absent `BITMASKS.md` reference. | NEEDS_REVIEW | Unresolved | It mixes NOESIS layer semantics with TinyMUX implementation attributes and is already flagged for reconciliation. | Reconcile with canonical `LAYERS.md` before deciding whether any TinyMUX attribute material belongs in `noesis-tinymux`. |
| `services/noesis-bridge/src/bridge.py` | `ThresholdOps/noesis` | Prototype bridge that logs into TinyMUX, parses `NOESIS:` lines from a raw stream, and writes ad hoc SAY/MOVE JSONL events. | DEPRECATE_AFTER_MIGRATION | `ThresholdOps/noesis` | It is a transitional runtime parser, not the canonical TinyMUX `@log` adapter and not suitable to move as-is. | Deprecate only after adapter-side source validation and NOESIS telemetry output validation exist. |
| `services/noesis-bridge/src/writer.py` | `ThresholdOps/noesis` | Generic append-only JSONL writer used by the prototype bridge. | KEEP_IN_NOESIS | `ThresholdOps/noesis` | It does not encode TinyMUX source semantics; it is part of NOESIS prototype runtime plumbing. | None. |
| `services/noesis-bridge/config.example.yaml` | `ThresholdOps/noesis` | Prototype TinyMUX connection/output config with host, port, auth placeholders, and `/opt/tinymux/out`. | DEPRECATE_AFTER_MIGRATION | `ThresholdOps/noesis` | It belongs to the current runtime bridge prototype and should not become adapter transport authority. | Revisit after runtime ownership and transport boundaries are defined. |
| `services/noesis-bridge/src/renderer_v0.py` | `ThresholdOps/noesis` | Prototype renderer for ad hoc bridge event shape. | KEEP_IN_NOESIS | `ThresholdOps/noesis` | It consumes NOESIS-side event output and is not a TinyMUX source-record contract. | May need later refactor if telemetry v0 replaces the ad hoc event shape. |
| `services/elias-bot/elias_mux_bot.py` | `ThresholdOps/noesis` | Incomplete TinyMUX/OpenAI bot prototype with direct socket and response behavior. | DEPRECATE_AFTER_MIGRATION | `ThresholdOps/noesis` | It is neither tool-neutral telemetry nor a bounded adapter source contract; `noesis-tinymux` must not own remote control/write-back behavior. | Quarantine or deprecate separately from adapter migration. |

## Recommended Authority Model

```text
ThresholdOps/noesis
  authoritative for tool-neutral telemetry contracts and generic conformance rules

ThresholdOps/noesis-tinymux
  authoritative for TinyMUX source records, TinyMUX-specific mapping, fixtures, parser behavior, relay experiments, and transport probes
```

`noesis-tinymux` should validate against NOESIS contracts. NOESIS should not
validate TinyMUX-specific source formats after migration. Mapping fixtures belong
with the adapter that owns the source semantics.

## Migration Phases

### Phase 0 — inventory and confirmation

- confirm ownership decisions;
- resolve `NEEDS_REVIEW` items;
- make no file moves.

### Phase 1 — establish TinyMUX source authority

- add TinyMUX source record contract to `noesis-tinymux`;
- add source fixtures;
- add local validation;
- add CI in the adapter repository;
- preserve existing NOESIS copies temporarily.

### Phase 2 — establish mapping authority

- add TinyMUX-to-NOESIS mapping specification;
- add mapping fixtures;
- validate output against authoritative NOESIS telemetry contracts;
- confirm behavioral parity with existing NOESIS validation.

### Phase 3 — switch references

- update documentation and CI references;
- ensure `noesis-tinymux` is the only authority for TinyMUX-specific artifacts;
- retain only tool-neutral contracts in NOESIS.

### Phase 4 — deprecate old copies

- mark old TinyMUX-specific NOESIS artifacts as deprecated;
- remove them only after equivalent adapter validation is active;
- preserve migration notes and historical audit references where useful.

### Phase 5 — runtime implementation

Only after ownership migration is stable:

- parser;
- replay adapter;
- bounded reader;
- softcode relay fixture;
- `@log` suitability probes;
- live integration proof.

## Non-Goals

This audit does not:

- change runtime behavior;
- move files;
- change CI;
- create schemas;
- create fixtures;
- implement an adapter;
- modify TinyMUX;
- define a production transport;
- declare `@log` production-ready.

## Open Decisions

- `.github/workflows/ci.yml` is mixed: it runs both generic NOESIS telemetry
  validation and TinyMUX-specific source/mapping validation. The split should be
  decided when equivalent `noesis-tinymux` validation exists.
- `docs/LAYERS-ATTRS.md` needs ownership review because it mixes NOESIS layer
  semantics with TinyMUX attribute-level implementation detail.
- `docs/MANIFEST.md` needs ownership review because current audit content
  identifies it as an older TinyMUX-oriented runtime manifest that conflicts
  with root `MANIFEST.md`.

## Recommended Next Slice

`docs: add TinyMUX source record contract`

The audit confirms that `docs/tinymux/event-schema-v0.md` is TinyMUX-specific
and suitable for migration into `noesis-tinymux`. The next slice should recreate
that source-record contract as adapter-owned documentation without moving or
deleting the NOESIS copy, then follow with fixtures and validation in later
slices.
