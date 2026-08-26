"""A typed-state-inspired route decision without a live graph dependency."""
from __future__ import annotations
import json

THRESHOLD = 0.8

def route(confidence: float) -> dict[str, object]:
    if not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    return {"route": "tool" if confidence >= THRESHOLD else "human-review", "threshold": THRESHOLD}

if __name__ == "__main__":
    for value in (0.74, 0.8): print(json.dumps(route(value), sort_keys=True))
