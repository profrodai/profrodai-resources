#!/usr/bin/env python3
"""Fail-closed validation for the bounded Phase 1 curriculum contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / "catalog" / "profrod-site-source-index.json"
DEFAULT_MANIFEST = ROOT / "catalog" / "curriculum-manifest.json"
EXPECTED_SNAPSHOT = "7a4f77d705a2f51cc403c5889ef92e6359bfb82f"
CURSOR_PATH = "content/courses/agentic-coding-with-cursor/_course.md"
ZEOTOOL_PATH = "content/articles/build-your-first-zeocore-tool.md"
ORDER_API_PATH = "courses/agentic-coding-with-cursor/order-api"
STRUCTURAL_KEYS = {"catalog_path", "kind", "maturity", "contract_status"}
COURSE_CONTRACT_KEYS = {
    "audience",
    "outcomes",
    "prerequisites",
    "module_sequence",
    "lab_project_map",
    "assessment",
    "safety_cost_boundary",
    "completion_evidence",
}
ARTICLE_CONTRACT_KEYS = {
    "thesis",
    "prerequisites",
    "demonstration_exercise_route",
    "fixtures",
    "verification",
    "next_learning_step",
}
LAB_KEYS = {
    "parent_catalog_path",
    "resource_path",
    "objective",
    "setup",
    "commands",
    "expected_result",
    "verification",
    "rubric",
    "failure_modes",
    "extensions",
}


def fail(message: str) -> None:
    raise ValueError(message)


def read_json(path: Path, label: str) -> object:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        fail(f"missing {label}: {path}")
    except json.JSONDecodeError as error:
        fail(f"invalid {label} JSON: {error}")


def require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{label} must be a non-empty string")
    return value


def require_string_list(value: object, label: str) -> None:
    if not isinstance(value, list) or not value:
        fail(f"{label} must be a non-empty list")
    for item in value:
        require_string(item, label)


def validate_contract(contract: object, required: set[str], label: str) -> None:
    if not isinstance(contract, dict) or set(contract) != required:
        fail(f"{label} must contain exactly: {', '.join(sorted(required))}")
    for key, value in contract.items():
        if key in {"outcomes", "prerequisites", "module_sequence", "lab_project_map"}:
            require_string_list(value, f"{label}.{key}")
        else:
            require_string(value, f"{label}.{key}")


H2_PATTERN = re.compile(r"^##[ \t]+(.+?)[ \t]*$")
FENCE_PATTERN = re.compile(r"^[ \t]*(`{3,}|~{3,})")


def markdown_h2_headings(text: str) -> set[str]:
    """Return literal H2 text, excluding fenced-code lookalikes."""
    headings: set[str] = set()
    fence: str | None = None
    for line in text.splitlines():
        fence_match = FENCE_PATTERN.match(line)
        if fence_match:
            marker = fence_match.group(1)
            if fence is None:
                fence = marker[0]
            elif marker[0] == fence:
                fence = None
            continue
        if fence is not None:
            continue
        heading_match = H2_PATTERN.match(line)
        if heading_match:
            headings.add(heading_match.group(1))
    return headings


def require_readme_headings(path: Path, headings: tuple[str, ...]) -> None:
    try:
        text = path.read_text()
    except FileNotFoundError:
        fail(f"missing contract README: {path.relative_to(ROOT)}")
    parsed_headings = markdown_h2_headings(text)
    missing = [heading for heading in headings if heading not in parsed_headings]
    if missing:
        fail(f"contract README lacks required headings: {', '.join(missing)}")


def catalog_kinds(index: object) -> dict[str, str]:
    if not isinstance(index, dict) or set(index) != {"repository", "commit", "capturedFrom", "entries"}:
        fail("source index has an unexpected shape")
    entries = index["entries"]
    if not isinstance(entries, list) or len(entries) != 24:
        fail("source index must contain exactly 24 entries")
    kinds: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"path", "title"}:
            fail("source index entry has an unexpected shape")
        path = require_string(entry["path"], "source index path")
        require_string(entry["title"], "source index title")
        if path in kinds:
            fail(f"source index duplicates {path}")
        if path.startswith("content/courses/") and path.endswith("/_course.md"):
            kinds[path] = "course"
        elif path.startswith("content/articles/") and path.endswith(".md"):
            kinds[path] = "article"
        else:
            fail(f"source index path has unknown kind: {path}")
    if sum(kind == "course" for kind in kinds.values()) != 11 or sum(kind == "article" for kind in kinds.values()) != 13:
        fail("source index must contain 11 courses and 13 articles")
    return kinds


def validate_lab_contract(lab: object) -> None:
    if not isinstance(lab, dict) or set(lab) != LAB_KEYS:
        fail("Cursor lab contract has an unexpected shape")
    if lab["parent_catalog_path"] != CURSOR_PATH:
        fail("Cursor lab parent_catalog_path must equal the Cursor record")
    if lab["resource_path"] != ORDER_API_PATH:
        fail("Cursor lab resource_path must equal the existing order-api directory")
    resolved = (ROOT / lab["resource_path"]).resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError:
        fail("Cursor lab resource path escapes the repository")
    if not resolved.is_dir():
        fail("Cursor lab resource path must be an existing directory")
    for key, value in lab.items():
        if key in {"setup", "commands", "failure_modes", "extensions"}:
            require_string_list(value, f"Cursor lab.{key}")
        else:
            require_string(value, f"Cursor lab.{key}")


def validate(index_path: Path = DEFAULT_INDEX, manifest_path: Path = DEFAULT_MANIFEST) -> None:
    catalog = catalog_kinds(read_json(index_path, "source index"))
    manifest = read_json(manifest_path, "curriculum manifest")
    if not isinstance(manifest, dict) or set(manifest) != {"schema_version", "catalog_snapshot", "records"}:
        fail("manifest must contain only schema_version, catalog_snapshot, and records")
    if manifest["schema_version"] != 1:
        fail("manifest schema_version must be 1")
    if manifest["catalog_snapshot"] != EXPECTED_SNAPSHOT:
        fail("manifest catalog_snapshot must equal the measured Resources main SHA")
    records = manifest["records"]
    if not isinstance(records, list) or len(records) != 24:
        fail("manifest must contain exactly 24 top-level records")

    seen: set[str] = set()
    complete: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            fail("manifest record must be an object")
        path = require_string(record.get("catalog_path"), "record catalog_path")
        if path in seen:
            fail(f"manifest duplicates catalog_path: {path}")
        seen.add(path)
        if path not in catalog:
            fail(f"manifest path is absent from source index: {path}")
        kind = record.get("kind")
        if kind != catalog[path]:
            fail(f"record kind must match source index path: {path}")
        expected_maturity = "scaffold" if kind == "course" else "mapped"
        if record.get("maturity") != expected_maturity:
            fail(f"record maturity must be {expected_maturity}: {path}")
        status = record.get("contract_status")
        if status not in {"planned", "complete"}:
            fail(f"record contract_status must be planned or complete: {path}")
        if "title" in record:
            fail("manifest must not duplicate source-index titles")

        if status == "planned":
            if set(record) != STRUCTURAL_KEYS:
                fail(f"planned record must contain only structural fields: {path}")
            continue

        complete.add(path)
        if path == CURSOR_PATH:
            if set(record) != STRUCTURAL_KEYS | {"readme_contract", "lab_contracts"}:
                fail("completed Cursor record has an unexpected shape")
            validate_contract(record["readme_contract"], COURSE_CONTRACT_KEYS, "Cursor readme_contract")
            labs = record["lab_contracts"]
            if not isinstance(labs, list) or len(labs) != 1:
                fail("Cursor record must contain exactly one nested lab contract")
            validate_lab_contract(labs[0])
            require_readme_headings(
                ROOT / "courses/agentic-coding-with-cursor/README.md",
                ("Audience", "Outcomes", "Prerequisites", "Module sequence", "Assessment", "Safety and cost boundary", "Completion evidence"),
            )
            require_readme_headings(
                ROOT / "courses/agentic-coding-with-cursor/order-api/README.md",
                ("Objective", "Setup", "Commands", "Expected result", "Verification", "Rubric", "Failure modes", "Extensions"),
            )
        elif path == ZEOTOOL_PATH:
            if set(record) != STRUCTURAL_KEYS | {"readme_contract"}:
                fail("completed ZeoCore article record has an unexpected shape")
            validate_contract(record["readme_contract"], ARTICLE_CONTRACT_KEYS, "ZeoCore article readme_contract")
            require_readme_headings(
                ROOT / "articles/build-your-first-zeocore-tool/README.md",
                ("Thesis", "Prerequisites", "Demonstration and exercise route", "Fixtures", "Verification", "Next learning step"),
            )
        else:
            fail(f"only the approved records may be complete: {path}")

    if seen != set(catalog):
        missing = sorted(set(catalog) - seen)
        foreign = sorted(seen - set(catalog))
        fail(f"manifest/source-index paths differ; missing={missing}, foreign={foreign}")
    if complete != {CURSOR_PATH, ZEOTOOL_PATH}:
        fail("completed record set must equal the approved Cursor course and ZeoCore article")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    try:
        validate(args.index, args.manifest)
    except ValueError as error:
        print(f"curriculum manifest validation failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    print("curriculum manifest valid: 24 records, 2 complete, 22 planned")


if __name__ == "__main__":
    main()
