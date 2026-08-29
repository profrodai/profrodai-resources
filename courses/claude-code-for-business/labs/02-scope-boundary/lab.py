"""Fail-closed scope gate for a fictional business delegation."""
from __future__ import annotations
import json

REQUIRED = ("objective", "allowed_paths", "forbidden_actions", "acceptance_checks")


def assess(request: dict[str, object]) -> dict[str, object]:
    missing = [key for key in REQUIRED if not request.get(key)]
    return {"status": "ready" if not missing else "blocked", "missing": missing}


if __name__ == "__main__":
    print(json.dumps(assess({"objective": "summarize", "allowed_paths": ["fixtures/contracts"], "forbidden_actions": ["send"], "acceptance_checks": ["three rows"]}), sort_keys=True))
