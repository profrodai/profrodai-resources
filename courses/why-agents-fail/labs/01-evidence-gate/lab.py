"""Fail a synthetic claim closed when a named evidence ID is absent."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def canonicalize_evidence_ids(name: str, evidence_ids: set[str], *, allow_empty: bool) -> set[str]:
    """Return trimmed evidence IDs while rejecting blank or visually duplicate IDs."""
    if not isinstance(evidence_ids, set) or (not allow_empty and not evidence_ids):
        raise ValueError(f"{name} evidence IDs must be a {'non-empty ' if not allow_empty else ''}set of non-empty strings")
    if any(not isinstance(evidence_id, str) or not evidence_id.strip() for evidence_id in evidence_ids):
        raise ValueError(f"{name} evidence IDs must be a {'non-empty ' if not allow_empty else ''}set of non-empty strings")
    canonical_ids = {evidence_id.strip() for evidence_id in evidence_ids}
    if len(canonical_ids) != len(evidence_ids):
        raise ValueError(f"{name} evidence IDs must be unique after trimming whitespace")
    return canonical_ids


def verify(required: set[str], supplied: set[str]) -> dict[str, object]:
    """Return a deterministic verdict without treating duplicates as new evidence."""
    canonical_required = canonicalize_evidence_ids("required", required, allow_empty=False)
    canonical_supplied = canonicalize_evidence_ids("supplied", supplied, allow_empty=True)
    missing = sorted(canonical_required - canonical_supplied)
    return {"verdict": "pass" if not missing else "fail", "missing": missing}


def assess_claim(claim: dict[str, object]) -> dict[str, object]:
    """Assess one synthetic claim fixture and retain the evidence trail in the output."""
    claim_id = claim.get("claim_id")
    required = claim.get("required")
    supplied = claim.get("supplied")
    if not isinstance(claim_id, str) or not claim_id.strip():
        raise ValueError("claim_id must be a non-empty string")
    canonical_claim_id = claim_id.strip()
    if not all(isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value) for value in (required, supplied)):
        raise ValueError("required and supplied must be lists of non-empty evidence IDs")
    canonical_required = {item.strip() for item in required}
    canonical_supplied = {item.strip() for item in supplied}
    if len(canonical_required) != len(required) or len(canonical_supplied) != len(supplied):
        raise ValueError("required and supplied evidence IDs must be unique after trimming whitespace")
    result = verify(canonical_required, canonical_supplied)
    return {
        "claim_id": canonical_claim_id,
        "evidence_supplied": len(canonical_supplied),
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
