"""Preserve a manual-work baseline while measuring a later observation."""
from __future__ import annotations
import json

def measure(baseline: int, observed: int) -> dict[str, object]:
    if baseline <= 0 or observed < 0: raise ValueError("baseline must be positive and observed non-negative")
    return {"baseline_minutes":baseline, "observed_minutes":observed, "percent_change":round((baseline-observed)/baseline*100, 1)}

if __name__ == "__main__": print(json.dumps(measure(45, 30), sort_keys=True))
