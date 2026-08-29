"""Check whether a fictional reusable workflow instruction is executable by review."""
from __future__ import annotations
import json

REQUIRED = ("trigger", "steps", "output", "verification")


def assess(instruction: dict[str, object]) -> dict[str, object]:
    missing = [key for key in REQUIRED if not instruction.get(key)]
    return {"status": "usable" if not missing else "incomplete", "missing": missing}


if __name__ == "__main__":
    print(json.dumps(assess({"trigger": "month-end", "steps": ["read fixtures", "draft report"], "output": "draft.md", "verification": "three sections"}), sort_keys=True))
