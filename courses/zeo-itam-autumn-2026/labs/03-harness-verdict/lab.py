"""Recompute a synthetic check from evidence before accepting a claimed result."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


REQUIRED_CLAIM_FIELDS = ("claim_id", "owner", "check", "claimed_unmatched_ids")
CHECK_NAME = "invoice-receipt-reconciliation"


def text_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{field} must be a list of non-empty text IDs")
    normalized = [item.strip() for item in value]
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field} must not contain duplicate IDs")
    return normalized


def independently_observed_unmatched_ids(evidence: Any) -> list[str]:
    if not isinstance(evidence, dict) or set(evidence) != {"invoice_ids", "receipt_ids"}:
        raise ValueError("evidence must contain only invoice_ids and receipt_ids")
    invoice_ids = text_list(evidence["invoice_ids"], "invoice_ids")
    receipt_ids = text_list(evidence["receipt_ids"], "receipt_ids")
    return sorted(set(invoice_ids) - set(receipt_ids))


def verdict(claim: Any, evidence: Any) -> dict[str, object]:
    if not isinstance(claim, dict):
        raise ValueError("claim must be a JSON object")
    if set(claim) != set(REQUIRED_CLAIM_FIELDS):
        raise ValueError("claim must contain only claim_id, owner, check, and claimed_unmatched_ids")
    missing = [field for field in ("claim_id", "owner", "check") if not isinstance(claim.get(field), str) or not claim[field].strip()]
    if "claimed_unmatched_ids" not in claim or not isinstance(claim["claimed_unmatched_ids"], list):
        missing.append("claimed_unmatched_ids")
    if missing:
        return {"decision": "hold", "reason": "missing-evidence", "missing": missing}
    if claim["check"] != CHECK_NAME:
        return {"decision": "hold", "reason": "unrecognized-check", "missing": []}
    claimed_ids = text_list(claim["claimed_unmatched_ids"], "claimed_unmatched_ids")
    observed_ids = independently_observed_unmatched_ids(evidence)
    if claimed_ids != observed_ids:
        return {"decision": "hold", "reason": "check-disagrees", "missing": []}
    return {"decision": "accept", "reason": "check-agrees", "missing": []}


def main(claim_path: Path, evidence_path: Path) -> None:
    print(json.dumps(verdict(json.loads(claim_path.read_text()), json.loads(evidence_path.read_text())), sort_keys=True))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
