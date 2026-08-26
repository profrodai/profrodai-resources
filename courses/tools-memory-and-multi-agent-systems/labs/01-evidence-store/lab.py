"""A minimal source-bearing store with observable duplicate protection."""
from __future__ import annotations
import json

def add(store: dict[str, str], record_id: str, source: str) -> dict[str, object]:
    if record_id in store: return {"stored": False, "reason": "duplicate", "count": len(store)}
    store[record_id] = source
    return {"stored": True, "reason": "new", "count": len(store)}

if __name__ == "__main__":
    records: dict[str, str] = {}
    print(json.dumps(add(records, "receipt-1", "fixture"), sort_keys=True))
    print(json.dumps(add(records, "receipt-1", "fixture"), sort_keys=True))
