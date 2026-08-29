"""Verify a reported total against separate synthetic invoice evidence."""
from __future__ import annotations
import json
import math


def verify(claim: dict[str, object], invoices: list[dict[str, object]]) -> dict[str, object]:
    invalid_rows = [
        index
        for index, row in enumerate(invoices)
        if not isinstance(row, dict)
        or isinstance(row.get("amount"), bool)
        or not isinstance(row.get("amount"), (int, float))
        or not math.isfinite(row["amount"])
    ]
    if invalid_rows:
        return {"status": "held", "reason": "invalid-evidence", "invalid_rows": invalid_rows}
    total = sum(row["amount"] for row in invoices)
    count = len(invoices)
    matches = claim.get("invoice_count") == count and claim.get("invoice_total") == total
    return {"status": "accepted" if matches else "held", "computed_count": count, "computed_total": total}


if __name__ == "__main__":
    evidence = [{"amount": 40.0}, {"amount": 12.5}]
    print(json.dumps(verify({"invoice_count": 2, "invoice_total": 52.5}, evidence), sort_keys=True))
