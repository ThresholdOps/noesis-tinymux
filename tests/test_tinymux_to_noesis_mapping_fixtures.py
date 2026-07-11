#!/usr/bin/env python3
"""Validate TinyMUX-to-NOESIS mapping fixtures.

Level 1 always validates the adapter-owned mapping fixture corpus and reuses
the local ``tinymux.log_event.v0`` source validator.

Level 2 conditionally validates mapped telemetry output against a local checkout
of the pinned ``ThresholdOps/noesis`` reference. The checkout is consumed when
available; this script does not clone or fetch it.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from test_tinymux_source_record_fixtures import ValidationError, validate_record


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "fixtures" / "mapping" / "tinymux_to_noesis" / "v0"
COMPATIBILITY_PIN = REPO_ROOT / "compatibility" / "noesis-telemetry-v0.json"

FIXTURE_FILES = {
    "mapped.json": "MAPPED",
    "unresolved.json": "UNRESOLVED",
    "rejected.json": "REJECTED",
}

REQUIRED_FIXTURE_FIELDS = {
    "case_id",
    "outcome",
    "source_record",
    "mapping_context",
    "expected_telemetry",
    "expected_reason",
    "notes",
}

EXPECTED_MAPPED_SOURCE_EVENTS = {
    "say",
    "pose",
    "emit",
    "enter",
    "leave",
}

EXPECTED_UNRESOLVED_SOURCE_EVENTS = {
    "page",
    "ooc",
    "system",
    "custom",
}

SOURCE_CONTRACT_REJECTION_REASONS = {
    "unsupported_source_schema",
    "invalid_source_record",
}

MAPPING_CONTEXT_REJECTION_REASONS = {
    "missing_mapping_context",
    "invalid_run_id",
    "invalid_seq",
}


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path}: invalid JSON: {exc}")


def load_fixtures() -> list[dict[str, Any]]:
    fixtures: list[dict[str, Any]] = []
    seen_case_ids: set[str] = set()

    for filename, expected_outcome in FIXTURE_FILES.items():
        path = FIXTURE_DIR / filename
        data = load_json(path)
        if not isinstance(data, list):
            fail(f"{path}: top-level JSON value must be an array")

        for index, fixture in enumerate(data, start=1):
            location = f"{path}:{index}"
            if not isinstance(fixture, dict):
                fail(f"{location}: fixture must be an object")

            missing = REQUIRED_FIXTURE_FIELDS - set(fixture)
            if missing:
                fail(f"{location}: missing fixture fields {sorted(missing)}")

            case_id = fixture["case_id"]
            if not isinstance(case_id, str) or not case_id:
                fail(f"{location}: case_id must be a non-empty string")
            if case_id in seen_case_ids:
                fail(f"{location}: duplicate case_id {case_id}")
            seen_case_ids.add(case_id)

            outcome = fixture["outcome"]
            if outcome != expected_outcome:
                fail(f"{location}: outcome {outcome!r} does not match {filename}")

            notes = fixture["notes"]
            if not isinstance(notes, str) or not notes:
                fail(f"{location}: notes must be a non-empty string")

            if not isinstance(fixture["source_record"], dict):
                fail(f"{location}: source_record must be an object")

            validate_expected_result_shape(fixture, location)
            validate_mapping_context(fixture, location)
            validate_source_record_expectation(fixture, location)

            fixtures.append(fixture)

    return fixtures


def validate_expected_result_shape(fixture: dict[str, Any], location: str) -> None:
    outcome = fixture["outcome"]

    if outcome == "MAPPED":
        if not isinstance(fixture["expected_telemetry"], dict):
            fail(f"{location}: MAPPED expected_telemetry must be an object")
        if fixture["expected_reason"] is not None:
            fail(f"{location}: MAPPED expected_reason must be null")
        return

    if fixture["expected_telemetry"] is not None:
        fail(f"{location}: {outcome} expected_telemetry must be null")
    if not isinstance(fixture["expected_reason"], str) or not fixture["expected_reason"]:
        fail(f"{location}: {outcome} expected_reason must be a non-empty string")


def validate_mapping_context(fixture: dict[str, Any], location: str) -> None:
    context = fixture["mapping_context"]
    if not isinstance(context, dict):
        fail(f"{location}: mapping_context must be an object")

    reason = fixture["expected_reason"]
    if reason == "missing_mapping_context":
        if context:
            fail(f"{location}: missing_mapping_context case must have empty mapping_context")
        return

    run_id = context.get("run_id")
    seq = context.get("seq")
    mapping_version = context.get("mapping_version")

    if reason == "invalid_run_id":
        if isinstance(run_id, str) and run_id:
            fail(f"{location}: invalid_run_id case unexpectedly has valid run_id")
    elif not isinstance(run_id, str) or not run_id:
        fail(f"{location}: mapping_context.run_id must be a non-empty string")

    if reason == "invalid_seq":
        if isinstance(seq, int) and seq > 0:
            fail(f"{location}: invalid_seq case unexpectedly has valid positive seq")
    elif not isinstance(seq, int):
        fail(f"{location}: mapping_context.seq must be an int")

    if mapping_version is not None and not isinstance(mapping_version, str):
        fail(f"{location}: mapping_context.mapping_version must be a string when present")


def validate_source_record_expectation(fixture: dict[str, Any], location: str) -> None:
    reason = fixture["expected_reason"]
    source_record = fixture["source_record"]

    if reason in SOURCE_CONTRACT_REJECTION_REASONS:
        try:
            validate_record(source_record)
        except ValidationError:
            return
        fail(f"{location}: expected source validator rejection for {reason}")

    try:
        validate_record(source_record)
    except ValidationError as exc:
        fail(f"{location}: source_record unexpectedly rejected: {exc.reason}: {exc.detail}")


def validate_coverage(fixtures: list[dict[str, Any]]) -> tuple[set[str], set[str], int]:
    mapped_events = {
        fixture["source_record"]["event_type"]
        for fixture in fixtures
        if fixture["outcome"] == "MAPPED"
    }
    unresolved_events = {
        fixture["source_record"]["event_type"]
        for fixture in fixtures
        if fixture["outcome"] == "UNRESOLVED"
    }
    rejected_count = sum(1 for fixture in fixtures if fixture["outcome"] == "REJECTED")

    if mapped_events != EXPECTED_MAPPED_SOURCE_EVENTS:
        fail(f"{FIXTURE_DIR}: MAPPED event coverage mismatch: {sorted(mapped_events)}")
    if unresolved_events != EXPECTED_UNRESOLVED_SOURCE_EVENTS:
        fail(f"{FIXTURE_DIR}: UNRESOLVED event coverage mismatch: {sorted(unresolved_events)}")

    return mapped_events, unresolved_events, rejected_count


def load_compatibility_pin() -> dict[str, Any]:
    pin = load_json(COMPATIBILITY_PIN)
    if not isinstance(pin, dict):
        fail(f"{COMPATIBILITY_PIN}: compatibility pin must be an object")

    for field in ("repository", "ref", "contract", "schema_version"):
        value = pin.get(field)
        if not isinstance(value, str) or not value:
            fail(f"{COMPATIBILITY_PIN}: {field} must be a non-empty string")

    if pin["repository"] != "ThresholdOps/noesis":
        fail(f"{COMPATIBILITY_PIN}: repository must be ThresholdOps/noesis")
    if len(pin["ref"]) != 40:
        fail(f"{COMPATIBILITY_PIN}: ref must be a 40-character commit SHA")
    if pin["contract"] != "docs/telemetry-contract.md":
        fail(f"{COMPATIBILITY_PIN}: contract must be docs/telemetry-contract.md")
    if pin["schema_version"] != "noesis.telemetry.v0":
        fail(f"{COMPATIBILITY_PIN}: schema_version must be noesis.telemetry.v0")

    return pin


def resolve_noesis_checkout(pin: dict[str, Any]) -> tuple[Path | None, str]:
    raw_path = os.environ.get("NOESIS_CHECKOUT_PATH")
    if raw_path:
        checkout = Path(raw_path).expanduser()
        source = "NOESIS_CHECKOUT_PATH"
    else:
        checkout = (REPO_ROOT / ".." / "noesis").resolve()
        source = "default ../noesis"

    if not checkout.is_dir():
        return None, f"NOESIS conformance check SKIPPED: no local checkout at {checkout} ({source})"

    try:
        result = subprocess.run(
            ["git", "-C", str(checkout), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        return None, f"NOESIS conformance check SKIPPED: {checkout} is not a readable git checkout ({exc})"

    head = result.stdout.strip()
    if head != pin["ref"]:
        return (
            None,
            "NOESIS conformance check SKIPPED: "
            f"{checkout} is at {head}, expected pinned ref {pin['ref']}",
        )

    return checkout, f"NOESIS conformance checkout: {checkout} @ {head}"


def load_noesis_telemetry_validator(checkout: Path) -> ModuleType:
    path = checkout / "tests" / "test_telemetry_v0_fixtures.py"
    if not path.is_file():
        fail(f"{path}: pinned NOESIS telemetry validator not found")

    spec = importlib.util.spec_from_file_location("pinned_noesis_telemetry_v0_fixtures", path)
    if spec is None or spec.loader is None:
        fail(f"{path}: could not load pinned NOESIS telemetry validator")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_expected_telemetry_with_noesis(
    fixtures: list[dict[str, Any]],
    noesis_validator: ModuleType,
) -> int:
    count = 0
    for fixture in fixtures:
        if fixture["outcome"] != "MAPPED":
            continue

        location = f"{fixture['case_id']}: expected_telemetry"
        record = fixture["expected_telemetry"]

        missing = noesis_validator.REQUIRED_TOP_LEVEL_FIELDS - set(record)
        if missing:
            fail(f"{location}: missing required fields {sorted(missing)}")

        if record["schema_version"] != "noesis.telemetry.v0":
            fail(f"{location}: schema_version mismatch")
        if not isinstance(record["event_id"], str) or not record["event_id"]:
            fail(f"{location}: empty event_id")
        if not isinstance(record["run_id"], str) or not record["run_id"]:
            fail(f"{location}: empty run_id")
        if not isinstance(record["seq"], int):
            fail(f"{location}: seq must be an integer")
        try:
            noesis_validator._assert_utc_iso8601_like(record["ts_utc"], location)
        except AssertionError as exc:
            fail(f"{location}: {exc}")

        if record["event_type"] not in noesis_validator.SUPPORTED_EVENT_TYPES:
            fail(f"{location}: unsupported event_type {record['event_type']}")
        if record["event_phase"] not in noesis_validator.SUPPORTED_PHASES:
            fail(f"{location}: unsupported event_phase {record['event_phase']}")
        if not isinstance(record["event_phase"], str) or not record["event_phase"]:
            fail(f"{location}: empty event_phase")

        producer = record["producer"]
        if not isinstance(producer, dict):
            fail(f"{location}: producer must be an object")
        missing_producer = noesis_validator.REQUIRED_PRODUCER_FIELDS - set(producer)
        if missing_producer:
            fail(f"{location}: missing producer fields {sorted(missing_producer)}")
        if not isinstance(producer["kind"], str) or not producer["kind"]:
            fail(f"{location}: empty producer.kind")
        if not isinstance(producer["source"], str) or not producer["source"]:
            fail(f"{location}: empty producer.source")
        if not isinstance(producer["authoritative"], bool):
            fail(f"{location}: producer.authoritative must be boolean")

        try:
            noesis_validator._assert_identity_or_null(record["actor"], f"{location}: actor")
            noesis_validator._assert_identity_or_null(record["location"], f"{location}: location")
        except AssertionError as exc:
            fail(f"{location}: {exc}")

        raw = record["raw"]
        if not isinstance(raw, dict):
            fail(f"{location}: raw must be an object")
        missing_raw = noesis_validator.REQUIRED_RAW_FIELDS - set(raw)
        if missing_raw:
            fail(f"{location}: missing raw fields {sorted(missing_raw)}")

        count += 1

    return count


def run() -> None:
    fixtures = load_fixtures()
    mapped_events, unresolved_events, rejected_count = validate_coverage(fixtures)
    pin = load_compatibility_pin()

    print("TinyMUX to NOESIS mapping fixtures: Level 1 OK")
    print(f"Total fixtures: {len(fixtures)}")
    print(f"Mapped event types: {', '.join(sorted(mapped_events))}")
    print(f"Unresolved event types: {', '.join(sorted(unresolved_events))}")
    print(f"Rejected cases: {rejected_count}")

    checkout, message = resolve_noesis_checkout(pin)
    print(message)
    if checkout is None:
        return

    noesis_validator = load_noesis_telemetry_validator(checkout)
    conformance_count = validate_expected_telemetry_with_noesis(fixtures, noesis_validator)
    print("NOESIS conformance check: Level 2 OK")
    print(f"Mapped telemetry records validated: {conformance_count}")


if __name__ == "__main__":
    run()
