"""Hold a fictional external draft until a named reviewer approves it."""
from __future__ import annotations
import json


def assess(draft: dict[str, object]) -> dict[str, object]:
    missing = [key for key in ("recipient", "body", "reviewer") if not draft.get(key)]
    approved = draft.get("review_approved") is True
    delivery = draft.get("delivery")
    status = "draft-ready" if not missing and approved and delivery == "draft-only" else "held"
    return {"status": status, "missing": missing}


if __name__ == "__main__":
    print(json.dumps(assess({"recipient": "supplier@example.test", "body": "Draft renewal note", "reviewer": "student", "review_approved": True, "delivery": "draft-only"}), sort_keys=True))
