#!/usr/bin/env python3
"""Validate TinyMUX mapping quarantine fixtures.

This is a fixture-contract check for ``tinymux.mapping_quarantine.v0`` only.
It does not validate quarantine records as NOESIS telemetry, implement a
runtime mapper, or model quarantine persistence.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from test_tinymux_source_record_fixtures import (
    ValidationError,
    assert_utc_timestamp,
    validate_record,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
QUARANTINE_FIXTURE_DIR = REPO_ROOT / "fixtures" / "quarantine" / "tinymux_mapping" / "v0"
MAPPING_FIXTURE_DIR = REPO_ROOT / "fixtures" / "mapping" / "tinymux_to_noesis" / "v0"

QUARANTINE_FILES = {
    "unresolved.json": "UNRESOLVED",
    "rejected.json": "REJECTED",
    "adapter_errors.json": "ADAPTER_ERROR",
}

EXPECTED_COUNTS = {
    "unresolved.json": 4,
    "rejected.json": 7,
    "adapter_errors.json": 1,
}

WRAPPER_FIELDS = {
    "case_id",
    "origin_mapping_case_id",
    "quarantine_record",
    "notes",
}

QUARANTINE_RECORD_FIELDS = {
    "schema_version",
    "quarantine_id",
    "quarantine_class",
    "outcome",
    "rejection_category",
    "reason_code",
    "source_record",
    "source_record_raw",
    "source_event_id",
    "source_schema_version",
    "mapping_context",
    "mapping_contract_version",
    "adapter_processing_timestamp",
    "diagnostic_details",
    "content_hash",
}

SCHEMA_VERSION = "tinymux.mapping_quarantine.v0"
MAPPING_CONTRACT_VERSION = "tinymux-to-noesis-telemetry-mapping-v0"

UNRESOLVED_REASONS = {
    "no_private_communication_event_type",
    "no_ooc_event_type",
    "system_subtype_required",
    "custom_subtype_required",
}

REJECTED_REASON_MULTIPLICITY = {
    "unsupported_source_schema": 1,
    "invalid_source_record": 2,
    "unsupported_mapping_version": 1,
    "missing_mapping_context": 1,
    "invalid_run_id": 1,
    "invalid_seq": 1,
}

REJECTION_CATEGORIES = {
    "unsupported_source_schema": "source_contract",
    "invalid_source_record": "source_contract",
    "unsupported_mapping_version": "mapping_context",
    "missing_mapping_context": "mapping_context",
    "invalid_run_id": "mapping_context",
    "invalid_seq": "mapping_context",
}

SOURCE_CONTRACT_REASONS = {
    "unsupported_source_schema",
    "invalid_source_record",
}

TELEMETRY_ENVELOPE_FIELDS = {
    "schema_version",
    "event_id",
    "ts_utc",
    "run_id",
    "seq",
    "event_type",
    "event_phase",
    "producer",
    "actor",
    "location",
    "raw",
}


class FixtureError(Exception):
    """Fixture validation failure."""


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FixtureError(f"{path}: invalid JSON: {exc}") from exc


def load_json_array(path: Path) -> list[Any]:
    data = load_json(path)
    if not isinstance(data, list):
        raise FixtureError(f"{path}: top-level JSON value must be an array")
    return data


def load_mapping_index() -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for filename in ("unresolved.json", "rejected.json"):
        path = MAPPING_FIXTURE_DIR / filename
        for item in load_json_array(path):
            if not isinstance(item, dict):
                raise FixtureError(f"{path}: mapping fixture entry must be an object")
            case_id = item.get("case_id")
            if not isinstance(case_id, str) or not case_id:
                raise FixtureError(f"{path}: mapping fixture case_id must be a non-empty string")
            if case_id in index:
                raise FixtureError(f"{path}: duplicate mapping fixture case_id {case_id}")
            index[case_id] = item
    return index


def iter_values(value: Any) -> Any:
    yield value
    if isinstance(value, dict):
        for item in value.values():
            yield from iter_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_values(item)


def reject_forbidden_content(fixture: dict[str, Any], location: str) -> None:
    for value in iter_values(fixture):
        if isinstance(value, dict):
            if value.get("schema_version") == "noesis.telemetry.v0":
                raise FixtureError(f"{location}: quarantine fixtures must not contain noesis.telemetry.v0 records")
            if "expected_telemetry" in value:
                raise FixtureError(f"{location}: quarantine fixtures must not contain expected_telemetry")
            if TELEMETRY_ENVELOPE_FIELDS <= set(value):
                raise FixtureError(f"{location}: quarantine fixtures must not contain telemetry output envelopes")
        elif isinstance(value, str) and "QuarantineWriteError" in value:
            raise FixtureError(f"{location}: QuarantineWriteError must not appear in fixture records")


def validate_wrapper(fixture: Any, location: str) -> dict[str, Any]:
    if not isinstance(fixture, dict):
        raise FixtureError(f"{location}: fixture entry must be an object")

    if set(fixture) != WRAPPER_FIELDS:
        raise FixtureError(f"{location}: wrapper fields must be exactly {sorted(WRAPPER_FIELDS)}")

    case_id = fixture["case_id"]
    if not isinstance(case_id, str) or not case_id:
        raise FixtureError(f"{location}: case_id must be a non-empty string")

    origin = fixture["origin_mapping_case_id"]
    if origin is not None and (not isinstance(origin, str) or not origin):
        raise FixtureError(f"{case_id}: origin_mapping_case_id must be null or a non-empty string")

    if not isinstance(fixture["notes"], str) or not fixture["notes"]:
        raise FixtureError(f"{case_id}: notes must be a non-empty string")

    if not isinstance(fixture["quarantine_record"], dict):
        raise FixtureError(f"{case_id}: quarantine_record must be an object")

    reject_forbidden_content(fixture, case_id)
    return fixture


def validate_quarantine_record(fixture: dict[str, Any]) -> dict[str, Any]:
    case_id = fixture["case_id"]
    origin = fixture["origin_mapping_case_id"]
    record = fixture["quarantine_record"]

    if set(record) != QUARANTINE_RECORD_FIELDS:
        raise FixtureError(f"{case_id}: quarantine_record fields must be exactly {sorted(QUARANTINE_RECORD_FIELDS)}")

    if record["schema_version"] != SCHEMA_VERSION:
        raise FixtureError(f"{case_id}: schema_version must be {SCHEMA_VERSION}")
    if record["schema_version"] == "noesis.telemetry.v0":
        raise FixtureError(f"{case_id}: quarantine record must not be NOESIS telemetry")
    if record["mapping_contract_version"] != MAPPING_CONTRACT_VERSION:
        raise FixtureError(f"{case_id}: mapping_contract_version must be {MAPPING_CONTRACT_VERSION}")

    quarantine_id = record["quarantine_id"]
    if not isinstance(quarantine_id, str) or not quarantine_id:
        raise FixtureError(f"{case_id}: quarantine_id must be a non-empty string")
    for label, value in (
        ("source_event_id", record["source_event_id"]),
        ("case_id", case_id),
        ("origin_mapping_case_id", origin),
    ):
        if value is not None and quarantine_id == value:
            raise FixtureError(f"{case_id}: quarantine_id must not equal {label}")

    validate_source_preservation(fixture)
    validate_timestamp(record["adapter_processing_timestamp"], case_id)
    validate_diagnostic_details(fixture)

    if record["content_hash"] is not None:
        raise FixtureError(f"{case_id}: content_hash must be null in this fixture corpus")

    context = record["mapping_context"]
    if context is not None and not isinstance(context, dict):
        raise FixtureError(f"{case_id}: mapping_context must be an object or null")

    return record


def validate_source_preservation(fixture: dict[str, Any]) -> None:
    case_id = fixture["case_id"]
    record = fixture["quarantine_record"]
    source_record = record["source_record"]
    source_record_raw = record["source_record_raw"]

    has_record = source_record is not None
    has_raw = source_record_raw is not None
    if has_record == has_raw:
        raise FixtureError(f"{case_id}: exactly one of source_record and source_record_raw must be non-null")

    if has_record:
        if not isinstance(source_record, dict):
            raise FixtureError(f"{case_id}: source_record must be an object when present")
        if record["source_event_id"] != source_record.get("event_id"):
            raise FixtureError(f"{case_id}: source_event_id must match source_record.event_id")
        if record["source_schema_version"] != source_record.get("schema_version"):
            raise FixtureError(f"{case_id}: source_schema_version must match source_record.schema_version")
        return

    if not isinstance(source_record_raw, str) or not source_record_raw:
        raise FixtureError(f"{case_id}: source_record_raw must be a non-empty string when present")
    if record["source_event_id"] is not None:
        raise FixtureError(f"{case_id}: raw-input source_event_id must be null")
    if record["source_schema_version"] is not None:
        raise FixtureError(f"{case_id}: raw-input source_schema_version must be null")

    try:
        json.loads(source_record_raw)
    except json.JSONDecodeError:
        return
    raise FixtureError(f"{case_id}: source_record_raw must contain malformed JSON text")


def validate_timestamp(value: Any, case_id: str) -> None:
    try:
        assert_utc_timestamp(value)
    except ValidationError as exc:
        raise FixtureError(f"{case_id}: adapter_processing_timestamp invalid: {exc.reason}: {exc.detail}") from exc


def validate_diagnostic_details(fixture: dict[str, Any]) -> None:
    case_id = fixture["case_id"]
    record = fixture["quarantine_record"]
    details = record["diagnostic_details"]

    if isinstance(details, str):
        if not details:
            raise FixtureError(f"{case_id}: diagnostic_details string must be non-empty")
    elif isinstance(details, dict):
        if not details:
            raise FixtureError(f"{case_id}: diagnostic_details object must be non-empty")
    else:
        raise FixtureError(f"{case_id}: diagnostic_details must be a non-empty string or object")

    if record["quarantine_class"] == "adapter_error":
        if not isinstance(details, dict):
            raise FixtureError(f"{case_id}: adapter_error diagnostic_details must be an object")
        if details.get("error_type") != "AdapterProcessingError":
            raise FixtureError(f"{case_id}: adapter_error error_type must be AdapterProcessingError")
        message = details.get("message")
        if not isinstance(message, str) or not message:
            raise FixtureError(f"{case_id}: adapter_error message must be a non-empty string")


def validate_outcome_shape(filename: str, fixture: dict[str, Any]) -> None:
    case_id = fixture["case_id"]
    record = fixture["quarantine_record"]
    reason = record["reason_code"]

    if filename == "unresolved.json":
        if record["quarantine_class"] != "mapping_outcome":
            raise FixtureError(f"{case_id}: unresolved quarantine_class must be mapping_outcome")
        if record["outcome"] != "UNRESOLVED":
            raise FixtureError(f"{case_id}: unresolved outcome must be UNRESOLVED")
        if record["rejection_category"] is not None:
            raise FixtureError(f"{case_id}: unresolved rejection_category must be null")
        if reason not in UNRESOLVED_REASONS:
            raise FixtureError(f"{case_id}: unexpected unresolved reason_code {reason!r}")
        return

    if filename == "rejected.json":
        if record["quarantine_class"] != "mapping_outcome":
            raise FixtureError(f"{case_id}: rejected quarantine_class must be mapping_outcome")
        if record["outcome"] != "REJECTED":
            raise FixtureError(f"{case_id}: rejected outcome must be REJECTED")
        expected_category = REJECTION_CATEGORIES.get(reason)
        if expected_category is None:
            raise FixtureError(f"{case_id}: unexpected rejected reason_code {reason!r}")
        if record["rejection_category"] != expected_category:
            raise FixtureError(f"{case_id}: rejection_category must be {expected_category} for {reason}")
        return

    if filename == "adapter_errors.json":
        if fixture["origin_mapping_case_id"] is not None:
            raise FixtureError(f"{case_id}: adapter_error origin_mapping_case_id must be null")
        if record["quarantine_class"] != "adapter_error":
            raise FixtureError(f"{case_id}: adapter_error quarantine_class must be adapter_error")
        if record["outcome"] is not None:
            raise FixtureError(f"{case_id}: adapter_error outcome must be null")
        if record["rejection_category"] is not None:
            raise FixtureError(f"{case_id}: adapter_error rejection_category must be null")
        if reason != "adapter_error":
            raise FixtureError(f"{case_id}: adapter_error reason_code must be adapter_error")


def validate_source_expectation(fixture: dict[str, Any]) -> None:
    case_id = fixture["case_id"]
    record = fixture["quarantine_record"]
    source_record = record["source_record"]
    if source_record is None:
        return

    reason = record["reason_code"]
    category = record["rejection_category"]

    if record["outcome"] == "REJECTED" and category == "source_contract" and reason in SOURCE_CONTRACT_REASONS:
        try:
            validate_record(source_record)
        except ValidationError:
            return
        raise FixtureError(f"{case_id}: expected source validator failure for {reason}")

    try:
        validate_record(source_record)
    except ValidationError as exc:
        raise FixtureError(f"{case_id}: source_record unexpectedly failed validation: {exc.reason}: {exc.detail}") from exc


def validate_origin_correlation(
    fixture: dict[str, Any],
    mapping_index: dict[str, dict[str, Any]],
    used_origins: set[str],
) -> None:
    case_id = fixture["case_id"]
    origin_id = fixture["origin_mapping_case_id"]
    record = fixture["quarantine_record"]

    if origin_id is None:
        return
    if origin_id not in mapping_index:
        raise FixtureError(f"{case_id}: origin_mapping_case_id {origin_id!r} does not exist")
    if origin_id in used_origins:
        raise FixtureError(f"{case_id}: origin_mapping_case_id {origin_id!r} is referenced more than once")
    used_origins.add(origin_id)

    origin = mapping_index[origin_id]
    if record["source_record"] != origin["source_record"]:
        raise FixtureError(f"{case_id}: source_record does not match origin mapping fixture")
    if record["mapping_context"] != origin["mapping_context"]:
        raise FixtureError(f"{case_id}: mapping_context does not match origin mapping fixture")
    if record["reason_code"] != origin["expected_reason"]:
        raise FixtureError(f"{case_id}: reason_code does not match origin expected_reason")
    if record["outcome"] != origin["outcome"]:
        raise FixtureError(f"{case_id}: quarantine outcome does not match origin mapping outcome")


def validate_fixture_corpus() -> tuple[Counter[str], int, int]:
    mapping_index = load_mapping_index()
    case_ids: set[str] = set()
    quarantine_ids: set[str] = set()
    used_origins: set[str] = set()
    reason_counts: Counter[str] = Counter()
    outcome_counts: Counter[str] = Counter()
    illustrative_count = 0

    for filename, display_outcome in QUARANTINE_FILES.items():
        path = QUARANTINE_FIXTURE_DIR / filename
        entries = load_json_array(path)
        expected_count = EXPECTED_COUNTS[filename]
        if len(entries) != expected_count:
            raise FixtureError(f"{path}: expected {expected_count} entries, found {len(entries)}")

        for index, item in enumerate(entries, start=1):
            fixture = validate_wrapper(item, f"{path}:{index}")
            case_id = fixture["case_id"]
            if case_id in case_ids:
                raise FixtureError(f"{case_id}: duplicate case_id")
            case_ids.add(case_id)

            record = validate_quarantine_record(fixture)
            quarantine_id = record["quarantine_id"]
            if quarantine_id in quarantine_ids:
                raise FixtureError(f"{case_id}: duplicate quarantine_id {quarantine_id}")
            quarantine_ids.add(quarantine_id)

            validate_outcome_shape(filename, fixture)
            validate_source_expectation(fixture)
            validate_origin_correlation(fixture, mapping_index, used_origins)

            if fixture["origin_mapping_case_id"] is None:
                illustrative_count += 1
            reason_counts[record["reason_code"]] += 1
            outcome_counts[display_outcome] += 1

    if used_origins != set(mapping_index):
        missing = sorted(set(mapping_index) - used_origins)
        extra = sorted(used_origins - set(mapping_index))
        raise FixtureError(f"{MAPPING_FIXTURE_DIR}: origin coverage mismatch missing={missing} extra={extra}")
    if len(used_origins) != 10:
        raise FixtureError(f"{MAPPING_FIXTURE_DIR}: expected 10 mapping-derived fixtures, found {len(used_origins)}")
    if illustrative_count != 2:
        raise FixtureError(f"{QUARANTINE_FIXTURE_DIR}: expected 2 illustrative fixtures, found {illustrative_count}")

    for reason in UNRESOLVED_REASONS:
        if reason_counts[reason] != 1:
            raise FixtureError(f"{QUARANTINE_FIXTURE_DIR}: reason {reason} must occur exactly once")
    for reason, expected in REJECTED_REASON_MULTIPLICITY.items():
        if reason_counts[reason] != expected:
            raise FixtureError(f"{QUARANTINE_FIXTURE_DIR}: reason {reason} must occur {expected} times")
    if reason_counts["adapter_error"] != 1:
        raise FixtureError(f"{QUARANTINE_FIXTURE_DIR}: adapter_error must occur exactly once")

    expected_total = sum(EXPECTED_COUNTS.values())
    if sum(outcome_counts.values()) != expected_total:
        raise FixtureError(f"{QUARANTINE_FIXTURE_DIR}: total count mismatch")

    return outcome_counts, len(used_origins), illustrative_count


def main() -> None:
    try:
        outcome_counts, mapping_derived, illustrative = validate_fixture_corpus()
    except FixtureError as exc:
        fail(str(exc))

    total = sum(outcome_counts.values())
    print("TinyMUX mapping quarantine fixtures: OK")
    print(f"UNRESOLVED: {outcome_counts['UNRESOLVED']}")
    print(f"REJECTED: {outcome_counts['REJECTED']}")
    print(f"ADAPTER_ERROR: {outcome_counts['ADAPTER_ERROR']}")
    print(f"Mapping-derived: {mapping_derived}")
    print(f"Illustrative: {illustrative}")
    print(f"Total: {total}")


if __name__ == "__main__":
    main()
