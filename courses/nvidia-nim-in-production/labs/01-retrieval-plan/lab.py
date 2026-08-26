"""Compute a transparent batch plan from local input."""
from __future__ import annotations
import json

def plan(documents: int, batch_size: int) -> dict[str, int]:
    if documents < 0 or batch_size <= 0: raise ValueError("documents must be non-negative and batch_size positive")
    batches = (documents + batch_size - 1) // batch_size
    return {"batches": batches, "concurrency": min(4, batches) if batches else 0}

if __name__ == "__main__": print(json.dumps(plan(25, 8), sort_keys=True))
