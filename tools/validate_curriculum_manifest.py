#!/usr/bin/env python3
"""Fail-closed validation for the 24-resource companion-practice contract."""

from __future__ import annotations

import argparse
from datetime import date
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / "catalog" / "profrod-site-source-index.json"
DEFAULT_MANIFEST = ROOT / "catalog" / "curriculum-manifest.json"
EXPECTED_SNAPSHOT = "fa07dee7feb55df59022c21ffb6b46352ae601b6"
DEVELOPED_COURSE_PATHS = {
    "content/courses/zeo-itam-autumn-2026/_course.md",
}
RECORD_KEYS = {
    "catalog_path",
    "kind",
    "maturity",
    "contract_status",
    "review_status",
    "exercise_path",
    "practice_guide",
    "verification",
    "last_verified",
}
COURSE_GUIDE_HEADINGS = {
    "Objective",
    "Guided exercise",
    "Project",
    "Evidence",
    "Rubric",
    "Accessibility",
    "Safety and cost",
    "Verify",
}
ARTICLE_GUIDE_HEADINGS = {
    "Practice objective",
    "Prerequisites",
    "Exercise",
    "Run and verification",
    "Completion evidence",
    "Rubric",
    "Accessibility",
    "Safety and cost boundary",
    "Provenance boundary",
}
H2_PATTERN = re.compile(r"^##[ \t]+(.+?)[ \t]*$")
FENCE_PATTERN = re.compile(r"^[ \t]*(`{3,}|~{3,})")


def fail(message: str) -> None:
    raise ValueError(message)


def read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        fail(f"missing {label}: {path}")
    except json.JSONDecodeError as error:
        fail(f"invalid {label} JSON: {error}")


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{label} must be a non-empty string")
    return value


def catalog_kinds(index: Any) -> dict[str, str]:
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
    if list(kinds.values()).count("course") != 11 or list(kinds.values()).count("article") != 13:
        fail("source index must contain 11 courses and 13 articles")
    return kinds


def markdown_h2_headings(text: str) -> set[str]:
    headings: set[str] = set()
    fence: str | None = None
    for line in text.splitlines():
        fence_match = FENCE_PATTERN.match(line)
        if fence_match:
            marker = fence_match.group(1)[0]
            fence = None if fence == marker else marker if fence is None else fence
            continue
        if fence is None:
            heading_match = H2_PATTERN.match(line)
            if heading_match:
                headings.add(heading_match.group(1))
    return headings


def require_headings(path: Path, required: set[str]) -> None:
    try:
        display_path = str(path.relative_to(ROOT))
    except ValueError:
        display_path = str(path)
    try:
        headings = markdown_h2_headings(path.read_text())
    except FileNotFoundError:
        fail(f"missing practice guide: {display_path}")
    missing = sorted(required - headings)
    if missing:
        fail(f"practice guide lacks required headings: {display_path} missing={missing}")


def repo_path(relative: str, label: str, *, directory: bool = False) -> Path:
    path = Path(require_string(relative, label))
    if path.is_absolute() or ".." in path.parts:
        fail(f"{label} must be a contained repository-relative path")
    resolved = (ROOT / path).resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError:
        fail(f"{label} escapes the repository")
    if directory and not resolved.is_dir():
        fail(f"{label} must resolve to an existing directory: {relative}")
    if not directory and not resolved.is_file():
        fail(f"{label} must resolve to an existing file: {relative}")
    return resolved


def slug_for(catalog_path: str) -> str:
    parts = catalog_path.split("/")
    return parts[2] if catalog_path.startswith("content/courses/") else Path(catalog_path).stem


def load_article_runner() -> Any:
    module_path = ROOT / "tools" / "run_article_practice.py"
    spec = importlib.util.spec_from_file_location("article_practice", module_path)
    if not spec or not spec.loader:
        fail("cannot load article practice runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def authored_paths() -> list[Path]:
    if (ROOT / ".git").exists() or subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    ).returncode == 0:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return [Path(path) for path in result.stdout.splitlines()]
    return [path.relative_to(ROOT) for path in ROOT.rglob("*")]


def reject_source_bodies() -> None:
    for path in authored_paths():
        if not path.parts or path.parts[0] not in {"courses", "articles"}:
            continue
        if "lessons" in path.parts:
            fail(f"source lesson directory is forbidden in Resources: {path}")
        if path.name.lower() in {"article.md", "article-body.md", "lesson.md"}:
            fail(f"source body filename is forbidden in Resources: {path}")


def validate(index_path: Path = DEFAULT_INDEX, manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, int]:
    catalog = catalog_kinds(read_json(index_path, "source index"))
    manifest = read_json(manifest_path, "curriculum manifest")
    if not isinstance(manifest, dict) or set(manifest) != {"schema_version", "catalog_snapshot", "records"}:
        fail("manifest must contain only schema_version, catalog_snapshot, and records")
    if manifest["schema_version"] != 2:
        fail("manifest schema_version must be 2")
    if manifest["catalog_snapshot"] != EXPECTED_SNAPSHOT:
        fail("manifest catalog_snapshot must equal merged Phase 1 main")
    records = manifest["records"]
    if not isinstance(records, list) or len(records) != 24:
        fail("manifest must contain exactly 24 records")

    seen: set[str] = set()
    counts = {"course": 0, "article": 0, "complete": 0, "developed": 0, "reviewed": 0}
    article_runner = load_article_runner()
    for record in records:
        if not isinstance(record, dict) or set(record) != RECORD_KEYS:
            fail("every manifest record must contain exactly the companion-contract fields")
        catalog_path = require_string(record["catalog_path"], "catalog_path")
        if catalog_path in seen:
            fail(f"manifest duplicates catalog_path: {catalog_path}")
        seen.add(catalog_path)
        if catalog_path not in catalog:
            fail(f"manifest path is absent from source index: {catalog_path}")
        kind = record["kind"]
        if kind != catalog[catalog_path]:
            fail(f"kind does not match source identity: {catalog_path}")
        expected_maturity = (
            "developed"
            if catalog_path in DEVELOPED_COURSE_PATHS
            else "scaffold"
            if kind == "course"
            else "mapped"
        )
        if record["maturity"] != expected_maturity:
            fail(f"maturity must remain {expected_maturity}: {catalog_path}")
        if record["contract_status"] != "complete":
            fail(f"all companion contracts must be complete: {catalog_path}")
        if record["review_status"] not in {"unreviewed", "operator-reviewed"}:
            fail(f"invalid review_status: {catalog_path}")
        try:
            verified_on = date.fromisoformat(require_string(record["last_verified"], "last_verified"))
        except ValueError:
            fail(f"last_verified must be an ISO date: {catalog_path}")
        if verified_on > date.today():
            fail(f"last_verified must not be in the future: {catalog_path}")

        exercise_path = repo_path(record["exercise_path"], "exercise_path", directory=True)
        guide_path = repo_path(record["practice_guide"], "practice_guide")
        slug = slug_for(catalog_path)
        if kind == "course":
            if record["verification"] != f"make -C courses/{slug} verify":
                fail(f"course verification must invoke its course gate: {catalog_path}")
            if exercise_path not in guide_path.parents:
                fail(f"course practice guide must live inside its exercise path: {catalog_path}")
            require_headings(guide_path, COURSE_GUIDE_HEADINGS)
        else:
            expected_dir = (ROOT / "articles" / slug).resolve()
            if exercise_path != expected_dir or guide_path != expected_dir / "README.md":
                fail(f"article paths must use their catalog slug: {catalog_path}")
            spec_path = expected_dir / "practice.json"
            if record["verification"] != f"python3 tools/run_article_practice.py articles/{slug}/practice.json":
                fail(f"article verification must invoke its exact practice spec: {catalog_path}")
            require_headings(guide_path, ARTICLE_GUIDE_HEADINGS)
            article_runner.verify_spec(spec_path)

        counts[kind] += 1
        counts["complete"] += 1
        counts["developed"] += record["maturity"] == "developed"
        counts["reviewed"] += record["review_status"] == "operator-reviewed"

    if seen != set(catalog):
        fail("manifest/source-index path sets differ")
    fixed_counts = {key: counts[key] for key in ("course", "article", "complete", "developed")}
    if fixed_counts != {"course": 11, "article": 13, "complete": 24, "developed": 1}:
        fail(f"unexpected curriculum coverage: {counts}")
    reject_source_bodies()
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    try:
        counts = validate(args.index, args.manifest)
    except ValueError as error:
        print(f"curriculum manifest validation failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    print(
        "curriculum companion coverage valid: "
        f"{counts['complete']} complete, {counts['course']} courses, "
        f"{counts['article']} articles, {counts['developed']} developed, "
        f"{counts['reviewed']} operator-reviewed"
    )


if __name__ == "__main__":
    main()
