#!/usr/bin/env python3
"""Validate adapter-owned TinyMUX source record fixtures.

This is a fixture-contract check for ``tinymux.log_event.v0`` only. It does not
parse runtime streams, map TinyMUX records to NOESIS telemetry, or validate
``noesis.telemetry.v0`` output.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "fixtures" / "tinymux" / "source_records" / "v0"
VALID_FIXTURE = FIXTURE_DIR / "valid.jsonl"
INVALID_FIXTURE = FIXTURE_DIR / "invalid.jsonl"

SCHEMA_VERSION = "tinymux.log_event.v0"
SOURCE = "tinymux"

REQUIRED_FIELDS = {
    "schema_version",
    "event_id",
    "timestamp",
    "source",
    "world",
    "room",
    "actor",
    "event_type",
    "text",
    "visibility",
}

EVENT_TYPES = {
    "say",
    "pose",
    "emit",
    "enter",
    "leave",
    "page",
    "ooc",
    "system",
    "custom",
}

EXPECTED_EVENT_TYPES = {
    "say",
    "pose",
    "emit",
    "enter",
    "leave",
    "page",
    "ooc",
    "system",
    "custom",
}

VISIBILITY_SCOPES = {
    "room",
    "private",
    "system",
    "custom",
}

EMPTY_TEXT_ALLOWED = {
    "enter",
    "leave",
    "system",
    "custom",
}

NULL_ACTOR_ALLOWED = {
    "system",
    "custom",
}

REQUIRED_OPTIONAL_COVERAGE = {
    "target",
    "channel",
    "softcode",
    "raw",
}

EXPECTED_INVALID_CASES = [
    "malformed_json",
    "missing_schema_version",
    "unsupported_schema_version",
    "missing_event_id",
    "empty_event_id",
    "invalid_source",
    "missing_world",
    "invalid_room_type",
    "missing_room_identifier",
    "numeric_room_dbref",
    "missing_actor_identifier",
    "numeric_actor_dbref",
    "null_actor_for_say",
    "unsupported_event_type",
    "missing_text",
    "non_string_text",
    "empty_text_for_say",
    "missing_visibility",
    "invalid_visibility_type",
    "unsupported_visibility_scope",
    "raw_ansi_text",
    "raw_multiline_framing",
]


class ValidationError(Exception):
    """Structured validation failure with a stable reason code."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class InvalidCase:
    case_id: str
    expected_reason: str
    start_line: int
    payload_lines: tuple[str, ...]


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def load_json_object_from_line(path: Path, line_number: int, line: str) -> dict[str, Any]:
    try:
        value = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValidationError("malformed_json", f"{path}:{line_number}: {exc}") from exc

    if not isinstance(value, dict):
        raise ValidationError("non_object_record", f"{path}:{line_number}: top-level JSON value is not an object")
    return value


def assert_utc_timestamp(value: Any) -> None:
    if not isinstance(value, str):
        raise ValidationError("invalid_timestamp", "timestamp must be a string")

    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValidationError("invalid_timestamp", "timestamp is not ISO-8601-like text") from exc

    if parsed.tzinfo is None:
        raise ValidationError("invalid_timestamp", "timestamp must include UTC timezone information")
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValidationError("invalid_timestamp", "timestamp must be UTC")


def validate_identity(value: Any, *, role: str) -> None:
    if role == "room":
        type_reason = "invalid_room_type"
        missing_reason = "missing_room_identifier"
        numeric_reason = "numeric_room_dbref"
    elif role in {"actor", "target"}:
        type_reason = f"invalid_{role}_type"
        missing_reason = f"missing_{role}_identifier"
        numeric_reason = f"numeric_{role}_dbref"
    else:
        raise AssertionError(f"unsupported identity role {role!r}")

    if not isinstance(value, dict):
        raise ValidationError(type_reason, f"{role} identity must be an object")

    if "dbref" in value:
        identifier = value["dbref"]
        if not isinstance(identifier, str):
            raise ValidationError(numeric_reason, f"{role}.dbref must be a string")
        if not identifier:
            raise ValidationError(missing_reason, f"{role}.dbref must be non-empty")
        if not identifier.startswith("#"):
            raise ValidationError(numeric_reason, f"{role}.dbref must preserve TinyMUX #dbref form")
    elif "id" in value:
        identifier = value["id"]
        if not isinstance(identifier, str):
            raise ValidationError(numeric_reason, f"{role}.id must be a string")
        if not identifier:
            raise ValidationError(missing_reason, f"{role}.id must be non-empty")
    else:
        raise ValidationError(missing_reason, f"{role} must include dbref or id")

    name = value.get("name")
    if not isinstance(name, str) or not name:
        raise ValidationError(f"missing_{role}_name", f"{role} must include non-empty name")


def iter_strings(value: Any) -> Any:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item)


def validate_record(record: dict[str, Any]) -> None:
    if "schema_version" not in record:
        raise ValidationError("missing_schema_version", "schema_version is required")
    if record["schema_version"] != SCHEMA_VERSION:
        raise ValidationError("unsupported_schema_version", "schema_version is not tinymux.log_event.v0")

    if "event_id" not in record:
        raise ValidationError("missing_event_id", "event_id is required")
    if not isinstance(record["event_id"], str) or not record["event_id"]:
        raise ValidationError("empty_event_id", "event_id must be a non-empty string")

    if record.get("source") != SOURCE:
        raise ValidationError("invalid_source", "source must be tinymux")

    if "world" not in record or not isinstance(record["world"], str) or not record["world"]:
        raise ValidationError("missing_world", "world must be a non-empty string")

    if "timestamp" not in record:
        raise ValidationError("invalid_timestamp", "timestamp is required")
    assert_utc_timestamp(record["timestamp"])

    if "room" not in record:
        raise ValidationError("invalid_room_type", "room is required")
    validate_identity(record["room"], role="room")

    if "event_type" not in record or record["event_type"] not in EVENT_TYPES:
        raise ValidationError("unsupported_event_type", "event_type is not in v0 vocabulary")
    event_type = record["event_type"]

    if "actor" not in record:
        raise ValidationError("missing_actor_identifier", "actor is required")
    if record["actor"] is None:
        if event_type not in NULL_ACTOR_ALLOWED:
            if event_type == "say":
                raise ValidationError("null_actor_for_say", "say records require an actor")
            raise ValidationError(f"null_actor_for_{event_type}", f"{event_type} records require an actor")
    else:
        validate_identity(record["actor"], role="actor")

    if event_type == "page":
        if "target" not in record:
            raise ValidationError("missing_target_identifier", "page records require target")
        if record["target"] is not None:
            validate_identity(record["target"], role="target")
        else:
            raise ValidationError("missing_target_identifier", "page target cannot be null")

    if "text" not in record:
        raise ValidationError("missing_text", "text is required")
    if not isinstance(record["text"], str):
        raise ValidationError("non_string_text", "text must be a string")
    if event_type not in EMPTY_TEXT_ALLOWED and not record["text"]:
        if event_type == "say":
            raise ValidationError("empty_text_for_say", "say text must be non-empty")
        raise ValidationError(f"empty_text_for_{event_type}", f"{event_type} text must be non-empty")

    if "visibility" not in record:
        raise ValidationError("missing_visibility", "visibility is required")
    if not isinstance(record["visibility"], dict):
        raise ValidationError("invalid_visibility_type", "visibility must be an object")
    if record["visibility"].get("scope") not in VISIBILITY_SCOPES:
        raise ValidationError("unsupported_visibility_scope", "visibility.scope is not supported")
    if event_type == "page" and record["visibility"].get("scope") != "private":
        raise ValidationError("unsupported_visibility_scope", "page records require private visibility")

    for field in ("raw", "softcode"):
        if field in record and not isinstance(record[field], dict):
            raise ValidationError(f"invalid_{field}_type", f"{field} must be an object when present")
    if "target" in record and record["target"] is not None:
        validate_identity(record["target"], role="target")

    if any("\x1b" in text for text in iter_strings(record)):
        raise ValidationError("raw_ansi_text", "decoded ESC is not allowed anywhere in a source record")


def parse_valid_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(VALID_FIXTURE.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            fail(f"{VALID_FIXTURE}:{line_number}: valid fixture contains a blank physical line")
        try:
            records.append(load_json_object_from_line(VALID_FIXTURE, line_number, line))
        except ValidationError as exc:
            fail(f"{VALID_FIXTURE}:{line_number}: valid fixture parse failed: {exc.reason}: {exc.detail}")
    return records


def parse_invalid_cases() -> list[InvalidCase]:
    lines = INVALID_FIXTURE.read_text(encoding="utf-8").splitlines()
    cases: list[InvalidCase] = []
    seen: set[str] = set()
    index = 0

    while index < len(lines):
        line = lines[index]
        line_number = index + 1
        if not line.strip():
            index += 1
            continue
        if not line.startswith("# CASE: "):
            fail(f"{INVALID_FIXTURE}:{line_number}: orphan payload or malformed metadata line")

        metadata = line[len("# CASE: ") :]
        if " | " not in metadata:
            fail(f"{INVALID_FIXTURE}:{line_number}: metadata must be '<case_id> | <expected_reason>'")
        case_id, expected_reason = metadata.split(" | ", 1)
        if not case_id:
            fail(f"{INVALID_FIXTURE}:{line_number}: case identifier is empty")
        if not expected_reason:
            fail(f"{INVALID_FIXTURE}:{line_number}: expected reason is empty")
        if case_id in seen:
            fail(f"{INVALID_FIXTURE}:{line_number}: duplicate case identifier {case_id}")
        seen.add(case_id)

        index += 1
        payload_start = index + 1
        payload: list[str] = []
        while index < len(lines) and not lines[index].startswith("# CASE: "):
            if lines[index].strip() or payload:
                payload.append(lines[index])
            index += 1
        while payload and not payload[-1].strip():
            payload.pop()
        if not payload:
            fail(f"{INVALID_FIXTURE}:{line_number}: metadata without payload for {case_id}")

        cases.append(
            InvalidCase(
                case_id=case_id,
                expected_reason=expected_reason,
                start_line=payload_start,
                payload_lines=tuple(payload),
            )
        )

    return cases


def validate_valid_fixture() -> tuple[int, set[str], set[str]]:
    records = parse_valid_records()
    seen_event_ids: set[str] = set()
    event_types: set[str] = set()
    optional_fields: set[str] = set()

    for index, record in enumerate(records, start=1):
        try:
            validate_record(record)
        except ValidationError as exc:
            fail(f"{VALID_FIXTURE}:{index}: valid fixture rejected: {exc.reason}: {exc.detail}")

        event_id = record["event_id"]
        if event_id in seen_event_ids:
            fail(f"{VALID_FIXTURE}:{index}: duplicate event_id {event_id}")
        seen_event_ids.add(event_id)
        event_types.add(record["event_type"])
        optional_fields.update(REQUIRED_OPTIONAL_COVERAGE.intersection(record))

    if len(records) != 9:
        fail(f"{VALID_FIXTURE}: expected 9 valid records, found {len(records)}")
    if event_types != EXPECTED_EVENT_TYPES:
        fail(f"{VALID_FIXTURE}: event type coverage mismatch: {sorted(event_types)}")
    if optional_fields != REQUIRED_OPTIONAL_COVERAGE:
        fail(f"{VALID_FIXTURE}: optional field coverage mismatch: {sorted(optional_fields)}")

    return len(records), event_types, optional_fields


def validate_invalid_fixture() -> int:
    cases = parse_invalid_cases()
    case_ids = [case.case_id for case in cases]
    if case_ids != EXPECTED_INVALID_CASES:
        fail(f"{INVALID_FIXTURE}: invalid case list mismatch: {case_ids}")

    for case in cases:
        actual_reason: str | None = None

        if case.case_id == "raw_multiline_framing" or len(case.payload_lines) > 1:
            actual_reason = "raw_multiline_framing"
        else:
            payload = case.payload_lines[0]
            try:
                record = load_json_object_from_line(INVALID_FIXTURE, case.start_line, payload)
                validate_record(record)
            except ValidationError as exc:
                actual_reason = exc.reason

        if actual_reason is None:
            fail(f"{INVALID_FIXTURE}:{case.case_id}: invalid fixture was accepted")
        if actual_reason != case.expected_reason:
            fail(
                f"{INVALID_FIXTURE}:{case.case_id}: expected {case.expected_reason}, "
                f"got {actual_reason}"
            )

    return len(cases)


def run() -> None:
    valid_count, event_types, optional_fields = validate_valid_fixture()
    invalid_count = validate_invalid_fixture()

    print("TinyMUX source record fixtures: OK")
    print(f"Valid records: {valid_count}")
    print(f"Event types covered: {len(event_types)}/{len(EXPECTED_EVENT_TYPES)}")
    print(f"Invalid cases: {invalid_count}")
    print(f"Optional fields covered: {', '.join(sorted(optional_fields))}")


if __name__ == "__main__":
    run()
