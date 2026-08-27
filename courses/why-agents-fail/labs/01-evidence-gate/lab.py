"""Fail a synthetic claim closed when a named evidence ID is absent."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def verify(required: set[str], supplied: set[str]) -> dict[str, object]:
    """Return a deterministic verdict without treating duplicates as new evidence."""
    missing = sorted(required - supplied)
    return {"verdict": "pass" if not missing else "fail", "missing": missing}


def assess_claim(claim: dict[str, object]) -> dict[str, object]:
    """Assess one synthetic claim fixture and retain the evidence trail in the output."""
    claim_id = claim.get("claim_id")
    required = claim.get("required")
    supplied = claim.get("supplied")
    if not isinstance(claim_id, str) or not claim_id:
        raise ValueError("claim_id must be a non-empty string")
    if not all(isinstance(value, list) and all(isinstance(item, str) and item for item in value) for value in (required, supplied)):
        raise ValueError("required and supplied must be lists of non-empty evidence IDs")
    result = verify(set(required), set(supplied))
    return {
        "claim_id": claim_id,
        "evidence_supplied": len(set(supplied)),
        "missing": result["missing"],
        "verdict": result["verdict"],
    }


def load_claim(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read claim fixture: {error}") from error
    if not isinstance(data, dict):
        raise ValueError("claim fixture must be a JSON object")
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check a synthetic claim against named evidence IDs.")
    parser.add_argument("fixture", nargs="?", type=Path, default=Path("fixtures/baseline.json"))
    args = parser.parse_args()
    print(json.dumps(assess_claim(load_claim(args.fixture)), indent=2, sort_keys=True))
