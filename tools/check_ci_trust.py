#!/usr/bin/env python3
"""Static regression checks for CI trust separation; standard library only."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PR_WORKFLOW = ROOT / ".github" / "workflows" / "verify.yml"
TRUSTED_WORKFLOW = ROOT / ".github" / "workflows" / "trusted-provenance.yml"
MAKEFILE = ROOT / "Makefile"
VALIDATOR = ROOT / "tools" / "validate_catalog.py"
CATALOG = ROOT / "catalog" / "curriculum.json"
CONSOLIDATION = ROOT / "catalog" / "consolidation-sources.json"


def fail(message: str) -> None:
    print(f"CI trust check failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(text: str, fragment: str, context: str) -> None:
    if fragment not in text:
        fail(f"{context} lacks {fragment!r}")


def main() -> None:
    pr = PR_WORKFLOW.read_text()
    trusted = TRUSTED_WORKFLOW.read_text()
    makefile = MAKEFILE.read_text()
    validator = VALIDATOR.read_text()
    catalog = json.loads(CATALOG.read_text())
    consolidation = json.loads(CONSOLIDATION.read_text())

    require(pr, "pull_request:", "PR-safe workflow")
    require(pr, "make verify-pr", "PR-safe workflow")
    for forbidden in ("PROFROD_SITE_READ_TOKEN", "secrets.", "x-access-token", "make verify\n"):
        if forbidden in pr:
            fail(f"PR-safe workflow contains forbidden trusted-source reference {forbidden!r}")

    for required in ("push:", "branches: [main]", "workflow_dispatch:", "ref: main", "PROFROD_SITE_READ_TOKEN", "make verify"):
        require(trusted, required, "trusted provenance workflow")
    if "pull_request:" in trusted:
        fail("trusted provenance workflow must not run for pull requests")

    for required in ("verify-pr:", "catalog-structure:", "curriculum-pr:", "--structure-only --course-makefiles", "ci-trust-check:"):
        require(makefile, required, "Makefile")
    if len(catalog.get("courses", [])) != 11:
        fail("catalog must enumerate exactly 11 course gates")
    if len(catalog.get("adoptedCourses", [])) != 2:
        fail("catalog must enumerate exactly two mapped adopted courses")
    if len(consolidation.get("sources", [])) != 7:
        fail("consolidation registry must enumerate exactly seven approved sources")
    if "consolidation:" not in makefile:
        fail("Makefile must validate the consolidation registry")
    require(validator, 'git_output(source_repo, "cat-file", "-e"', "source validator")
    require(validator, 'git_output(source_repo, "show", f"{commit}:{path}")', "source validator")
    require(validator, "--structure-only", "source validator")
    print("CI trust boundary valid: PR-safe gate has no source token; trusted provenance runs from main")


if __name__ == "__main__":
    main()
