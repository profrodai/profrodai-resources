"""Fail a synthetic claim closed when a named evidence ID is absent."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def verify(required: set[str], supplied: set[str]) -> dict[str, object]:
    """Return a deterministic verdict without treating duplicates as new evidence."""
    for name, evidence_ids, allow_empty in (
        ("required", required, False),
        ("supplied", supplied, True),
    ):
        if not isinstance(evidence_ids, set) or (not allow_empty and not evidence_ids):
            raise ValueError(f"{name} evidence IDs must be a {'non-empty ' if not allow_empty else ''}set of non-empty strings")
        if any(not isinstance(evidence_id, str) or not evidence_id for evidence_id in evidence_ids):
            raise ValueError(f"{name} evidence IDs must be a {'non-empty ' if not allow_empty else ''}set of non-empty strings")
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
    try:
        result = assess_claim(load_claim(args.fixture))
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2, sort_keys=True))
