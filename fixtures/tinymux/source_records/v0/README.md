# TinyMUX Source Record Fixtures v0

These fixtures exercise `tinymux.log_event.v0` for
`ThresholdOps/noesis-tinymux`.

They represent adapter input, not NOESIS telemetry output. They are synthetic
structured records, not player-visible transcript captures. They do not imply
live TinyMUX connectivity, do not establish a TinyMUX standard, and do not prove
`@log` suitable for production or high-frequency transport.

Validation will be added in a later slice.

References:

- `docs/tinymux-source-record-v0.md`
- `docs/artifact-ownership.md`

## Files

- `valid.jsonl` contains one valid JSON object per physical line. The corpus
  covers the current v0 source event vocabulary once: `say`, `pose`, `emit`,
  `enter`, `leave`, `page`, `ooc`, `system`, and `custom`.
- `invalid.jsonl` contains focused invalid cases for later validator coverage.
  It is not itself a valid JSONL record stream because it deliberately includes
  malformed and framing-error cases.

## Invalid Fixture Convention

Malformed JSON cannot carry fixture metadata inside the parsed object, so
`invalid.jsonl` uses a small line-oriented convention:

```text
# CASE: <stable_case_id> | <expected_reason>
<fixture line>
```

Rules:

- comment metadata lines begin exactly with `# CASE:`;
- each metadata line applies to the immediately following physical line only;
- blank lines may separate cases;
- validators added later must ignore blank lines and parse `# CASE:` metadata
  separately;
- the malformed record itself must remain on one physical line unless the case
  specifically tests raw multiline framing.

No separate manifest or expected-results file is provided in this slice.
