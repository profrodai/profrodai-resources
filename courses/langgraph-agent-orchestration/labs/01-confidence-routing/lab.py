"""A typed-state-inspired route decision without a live graph dependency."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

THRESHOLD = 0.8


def route(confidence: object) -> dict[str, object]:
    """Use a safe must-review route whenever the confidence cannot be trusted."""
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        return {"route": "human-review", "review_reason": "invalid-confidence", "threshold": THRESHOLD}
    if not 0 <= confidence <= 1:
        return {"route": "human-review", "review_reason": "invalid-confidence", "threshold": THRESHOLD}
    if confidence < THRESHOLD:
        return {"route": "human-review", "review_reason": "below-threshold", "threshold": THRESHOLD}
    return {"route": "tool", "review_reason": None, "threshold": THRESHOLD}


def assess_cases(data: dict[str, object]) -> list[dict[str, object]]:
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("routing fixture must contain a non-empty cases list")
    result: list[dict[str, object]] = []
    case_ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"id", "confidence"} or not isinstance(case["id"], str):
            raise ValueError("each routing case must contain only id and confidence")
        case_id = case["id"].strip()
        if not case_id:
            raise ValueError("routing case id must be a non-empty string")
        if case_id in case_ids:
            raise ValueError("routing case ids must be unique after trimming whitespace")
        case_ids.add(case_id)
        result.append({"id": case_id, **route(case["confidence"])})
    return result


def load_cases(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read routing fixture: {error}") from error
    if not isinstance(data, dict):
        raise ValueError("routing fixture must be a JSON object")
    return data

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Route synthetic confidence signals safely.")
    parser.add_argument("fixture", nargs="?", type=Path, default=Path("fixtures/routing-cases.json"))
    args = parser.parse_args()
    try:
        result = assess_cases(load_cases(args.fixture))
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    print(json.dumps(result, indent=2, sort_keys=True))
