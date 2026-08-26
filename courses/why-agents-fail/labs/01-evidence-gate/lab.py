"""Fail a claim closed when a named source is absent."""
from __future__ import annotations
import json

def verify(required: set[str], supplied: set[str]) -> dict[str, object]:
    missing = sorted(required - supplied)
    return {"verdict": "pass" if not missing else "fail", "missing": missing}

if __name__ == "__main__":
    print(json.dumps(verify({"receipt-a", "receipt-b"}, {"receipt-a"}), sort_keys=True))
