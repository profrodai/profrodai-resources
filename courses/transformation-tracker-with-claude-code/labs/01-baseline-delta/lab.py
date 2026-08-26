"""Report an honest minutes delta without hiding the baseline."""
from __future__ import annotations
import json

def compare(baseline: int, observed: int) -> dict[str, object]:
    if baseline <= 0 or observed < 0: raise ValueError("baseline must be positive and observed non-negative")
    delta = baseline - observed
    return {"baseline_minutes": baseline, "observed_minutes": observed, "minutes_saved": delta, "percent_change": round(delta / baseline * 100, 1)}

if __name__ == "__main__": print(json.dumps(compare(60, 42), sort_keys=True))
