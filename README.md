# noesis-tinymux

## Summary

`noesis-tinymux` is an independent adapter and integration laboratory for
translating site-defined TinyMUX event records into NOESIS-compatible telemetry.

It is separate from both TinyMUX core and the tool-neutral NOESIS core. Its role
is to explore and define the TinyMUX-specific side of an integration boundary
without presenting that work as a TinyMUX standard or embedding TinyMUX-specific
payload assumptions into the generic NOESIS project.

## Project Boundaries

This project:

- is not part of the TinyMUX project;
- is not an official TinyMUX integration;
- does not define a TinyMUX event standard;
- does not define a built-in TinyMUX structured event API;
- does not belong in the tool-neutral NOESIS core;
- does not provide remote control, command submission, or write-back
  functionality;
- does not treat ordinary player-visible TinyMUX output as a stable
  machine-readable contract.

## Architectural Boundary

```text
TinyMUX
  classifies and emits site-defined records

noesis-tinymux
  reads, validates, and translates those records

NOESIS
  consumes tool-neutral telemetry
```

TinyMUX-specific payload shapes belong in this repository. Generic telemetry
contracts belong in `ThresholdOps/noesis`.

## Initial Integration Direction

The current working direction is:

```text
TinyMUX softcode classification
→ caller-controlled structured record
→ narrow delivery surface such as @log
→ noesis-tinymux adapter
→ NOESIS-compatible telemetry
```

`@log` is suitable for deterministic fixtures, replay, and early integration
experiments. Its suitability for sustained live or high-frequency production
transport has not yet been established.

No production transport decision has been made. Any payload schema used here is
NOESIS-specific and must not be presented as a TinyMUX standard. Upstream
TinyMUX examples must not copy the NOESIS payload schema in a way that could
create a quasi-standard.

## Current Status

Status: pre-implementation / contract and fixture phase

The next work will establish deterministic fixtures and contract boundaries
before runtime integration.

## Repository Safety Rules

This repository must not contain:

- credentials or secrets;
- private server addresses or deployment inventory;
- production TinyMUX logs;
- player data;
- private transcripts;
- private world content;
- game-specific proprietary softcode;
- copied TinyMUX engine code without preserving applicable licensing and
  attribution.

Synthetic fixtures and independently written softcode prototypes are acceptable.

## Related Projects

- <https://github.com/ThresholdOps/noesis>
- <https://github.com/brazilofmux/tinymux>

This repository is independently maintained and is not endorsed by the TinyMUX
maintainers.

## License

Original code and documentation in this repository are licensed under the
Mozilla Public License 2.0 unless otherwise noted.

Copied or derived third-party material retains its original license and notices.
