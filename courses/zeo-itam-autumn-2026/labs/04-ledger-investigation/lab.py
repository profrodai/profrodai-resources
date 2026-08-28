"""Find concrete integrity gaps in a bounded fictional ledger."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


def investigate(records: Any) -> dict[str, object]:
    if not isinstance(records, list):
        raise ValueError("ledger must be a JSON list")
    seen: set[str] = set()
    duplicate_ids: list[str] = []
    missing_receipts: list[str] = []
    for record in records:
        if not isinstance(record, dict) or set(record) != {"id", "amount", "receipt"}:
            raise ValueError("each record must contain only id, amount, and receipt")
        record_id = record["id"]
        if not isinstance(record_id, str) or not record_id.strip():
            raise ValueError("record id must be non-empty text")
        record_id = record_id.strip()
        if record_id in seen:
            duplicate_ids.append(record_id)
        seen.add(record_id)
        if type(record["receipt"]) is not bool or type(record["amount"]) not in (int, float):
            raise ValueError("amount must be numeric and receipt must be Boolean")
        if not record["receipt"]:
            missing_receipts.append(record_id)
    return {"review_required": bool(duplicate_ids or missing_receipts), "duplicate_ids": sorted(duplicate_ids), "missing_receipts": sorted(missing_receipts)}


def main(path: Path) -> None:
    print(json.dumps(investigate(json.loads(path.read_text())), sort_keys=True))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
