"""Prevent a second spoken turn after an explicit terminal state."""
from __future__ import annotations
import json

def next_action(state: str) -> dict[str, str]:
    if state not in {"open", "completed", "handoff"}: raise ValueError("unknown call state")
    return {"action": "speak", "reason": "call-open"} if state == "open" else {"action": "hold", "reason": f"call-{state}"}

if __name__ == "__main__":
    for state in ("open", "completed"): print(json.dumps(next_action(state), sort_keys=True))
