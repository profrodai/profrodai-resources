"""Classify a task boundary from explicit input axes."""
from __future__ import annotations
import json

def classify(uncertainty: str, side_effect: str) -> dict[str, object]:
    if uncertainty not in {"low", "high"} or side_effect not in {"low", "high"}: raise ValueError("axes are low or high")
    return {"boundary": "stochastic" if uncertainty == "high" else "deterministic", "human_review": side_effect == "high"}

if __name__ == "__main__":
    for pair in (("low", "low"), ("high", "high")): print(json.dumps(classify(*pair), sort_keys=True))
