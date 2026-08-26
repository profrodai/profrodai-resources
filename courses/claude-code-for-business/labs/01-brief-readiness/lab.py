"""A deterministic readiness gate for a delegation brief."""
from __future__ import annotations
import json

REQUIRED = ("objective", "owner", "evidence")

def assess(brief: dict[str, object]) -> dict[str, object]:
    missing = [key for key in REQUIRED if not brief.get(key)]
    return {"status": "ready" if not missing else "blocked", "missing": missing}

if __name__ == "__main__":
    for brief in ({"objective": "reconcile", "owner": "student", "evidence": ["ledger-1"]}, {"objective": "reconcile", "owner": "student", "evidence": []}):
        print(json.dumps(assess(brief), sort_keys=True))
