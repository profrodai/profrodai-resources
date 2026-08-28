#!/usr/bin/env python3
"""Run deterministic supplementary exercises for mapped article concepts."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path, PurePosixPath
import sys
from typing import Any, Callable


def evidence_chain(data: dict[str, Any]) -> dict[str, Any]:
    required = set(data["required"])
    observed = set(data["observed"])
    missing = sorted(required - observed)
    return {"ready": not missing, "missing": missing}


def failure_boundary(data: dict[str, Any]) -> dict[str, Any]:
    target = PurePosixPath(data["target"])
    root = PurePosixPath(data["allowed_root"])
    traversal = ".." in target.parts
    contained = not traversal and (target == root or root in target.parents)
    allowed = contained and not data.get("overwrite", False)
    reason = "allowed"
    if traversal or not contained:
        reason = "outside-root"
    elif data.get("overwrite", False):
        reason = "overwrite-denied"
    return {"allowed": allowed, "reason": reason}


def permission_boundary(data: dict[str, Any]) -> dict[str, Any]:
    grants = set(data["grants"])
    requested = set(data["requested"])
    missing = sorted(requested - grants)
    return {"allowed": not missing, "missing": missing}


def deduplicate_customers(data: dict[str, Any]) -> dict[str, Any]:
    seen: dict[str, str] = {}
    duplicates: list[str] = []
    for record in data["records"]:
        normalized = record["email"].strip().lower()
        if normalized in seen:
            duplicates.append(record["id"])
        else:
            seen[normalized] = record["id"]
    return {
        "input_count": len(data["records"]),
        "unique_count": len(seen),
        "duplicate_ids": sorted(duplicates),
        "accounted_count": len(seen) + len(duplicates),
    }


def handoff_state(data: dict[str, Any]) -> dict[str, Any]:
    missing: list[str] = []
    for task in data["tasks"]:
        for field in ("owner", "status", "evidence"):
            if not task.get(field):
                missing.append(f"{task['id']}:{field}")
    return {"valid": not missing, "missing": sorted(missing)}


def content_block(data: dict[str, Any]) -> dict[str, Any]:
    mapping = {
        "compare": "comparison-table",
        "sequence": "steps",
        "decision": "decision-tree",
        "warning": "callout",
    }
    intent = data["intent"]
    return {"block": mapping.get(intent, "paragraph"), "known_intent": intent in mapping}


def verification_margin(data: dict[str, Any]) -> dict[str, Any]:
    expected_loss = data["failure_probability"] * data["failure_cost"]
    without = data["revenue"] - expected_loss
    with_verification = data["revenue"] - data["verification_cost"]
    return {
        "without_verification": round(without, 2),
        "with_verification": round(with_verification, 2),
        "verification_improves_margin": with_verification > without,
    }


def usage_cost(data: dict[str, Any]) -> dict[str, Any]:
    input_cost = data["input_tokens"] / 1_000_000 * data["input_rate_per_million"]
    output_cost = data["output_tokens"] / 1_000_000 * data["output_rate_per_million"]
    return {
        "input_cost": round(input_cost, 4),
        "output_cost": round(output_cost, 4),
        "total_cost": round(input_cost + output_cost, 4),
    }


def diff_impact(data: dict[str, Any]) -> dict[str, Any]:
    risky = {"delete", "permission", "dependency", "migration", "external-write"}
    hits = sorted(risky.intersection(data["actions"]))
    level = "high" if hits else ("medium" if len(data["files"]) > 3 else "low")
    return {"risk": level, "review_required": level != "low", "risk_actions": hits}


def role_routing(data: dict[str, Any]) -> dict[str, Any]:
    routes = {
        "scope": "operator",
        "architecture": "master",
        "implementation": "stream",
        "strategy-review": "sparring",
    }
    decision = data["decision_type"]
    return {"route": routes.get(decision, "operator"), "known_type": decision in routes}


AUTONOMY_CONTROLS = ("bounded_scope", "rollback", "verification", "no_live_pii", "escalation")
AUTONOMY_SCORE_MINIMUM = 0
AUTONOMY_SCORE_MAXIMUM = 100


def validated_autonomy_controls(data: Any) -> dict[str, bool]:
    """Accept only the complete, typed hard-control checklist."""
    if not isinstance(data, dict):
        raise ValueError("autonomy controls must be a JSON object")
    if set(data) != set(AUTONOMY_CONTROLS):
        raise ValueError("autonomy controls must contain exactly the five hard controls")
    if any(type(data[field]) is not bool for field in AUTONOMY_CONTROLS):
        raise ValueError("autonomy control values must be Boolean")
    return data


def autonomy_readiness(data: Any) -> dict[str, Any]:
    controls = validated_autonomy_controls(data)
    missing = [field for field in AUTONOMY_CONTROLS if not controls[field]]
    return {"ready": not missing, "missing": missing}


def assess_autonomy_proposals(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Assess synthetic automation proposals with hard controls before weighted signals."""
    proposals = data.get("proposals")
    if not isinstance(proposals, list) or len(proposals) != 3:
        raise ValueError("autonomy proposals must contain exactly three proposals")
    results: list[dict[str, Any]] = []
    proposal_ids: set[str] = set()
    for proposal in proposals:
        if not isinstance(proposal, dict) or set(proposal) != {"id", "controls", "readiness_score"}:
            raise ValueError("each autonomy proposal must contain only id, controls, and readiness_score")
        proposal_id = proposal["id"]
        score = proposal["readiness_score"]
        if not isinstance(proposal_id, str) or not proposal_id.strip():
            raise ValueError("proposal id must be a non-empty string")
        proposal_id = proposal_id.strip()
        if proposal_id in proposal_ids:
            raise ValueError("proposal ids must be unique after trimming whitespace")
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise ValueError("readiness_score must be a finite number from 0 through 100")
        if isinstance(score, float) and not math.isfinite(score):
            raise ValueError("readiness_score must be a finite number from 0 through 100")
        if not AUTONOMY_SCORE_MINIMUM <= score <= AUTONOMY_SCORE_MAXIMUM:
            raise ValueError("readiness_score must be from 0 through 100")
        proposal_ids.add(proposal_id)
        readiness = autonomy_readiness(proposal["controls"])
        results.append(
            {
                "id": proposal_id,
                "hard_gates_pass": readiness["ready"],
                "missing_hard_controls": readiness["missing"],
                "readiness_score": score,
                "decision": "ready" if readiness["ready"] else "must-review",
            }
        )
    return results


def transaction_cost(data: dict[str, Any]) -> dict[str, Any]:
    firm = sum(data["firm_costs"].values())
    market = sum(data["market_costs"].values())
    recommendation = "firm" if firm < market else ("market" if market < firm else "equal")
    return {"firm_total": firm, "market_total": market, "recommendation": recommendation}


def event_replay(data: dict[str, Any]) -> dict[str, Any]:
    state: dict[str, Any] = {}
    gaps: list[int] = []
    previous_sequence = 0
    for event in data["events"]:
        sequence = event["sequence"]
        if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence <= 0:
            raise ValueError("event sequence must be a positive integer")
        if sequence <= previous_sequence:
            raise ValueError("event sequences must be strictly increasing")
        gaps.extend(range(previous_sequence + 1, sequence))
        state[event["field"]] = event["value"]
        previous_sequence = sequence
    return {"state": state, "sequence_gaps": gaps, "replayable": not gaps}


EXERCISES: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "evidence-chain": evidence_chain,
    "failure-boundary": failure_boundary,
    "permission-boundary": permission_boundary,
    "deduplicate-customers": deduplicate_customers,
    "handoff-state": handoff_state,
    "content-block": content_block,
    "verification-margin": verification_margin,
    "usage-cost": usage_cost,
    "diff-impact": diff_impact,
    "role-routing": role_routing,
    "autonomy-readiness": autonomy_readiness,
    "transaction-cost": transaction_cost,
    "event-replay": event_replay,
}


def load_spec(path: Path) -> dict[str, Any]:
    try:
        spec = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read practice spec {path}: {error}") from error
    if not isinstance(spec, dict) or set(spec) != {"schema_version", "exercise_type", "cases"}:
        raise ValueError("practice spec must contain schema_version, exercise_type, and cases")
    if spec["schema_version"] != 1 or spec["exercise_type"] not in EXERCISES:
        raise ValueError("unsupported practice schema or exercise_type")
    if not isinstance(spec["cases"], dict) or set(spec["cases"]) != {"positive", "failure"}:
        raise ValueError("practice spec must define positive and failure cases")
    return spec


def run_case(spec: dict[str, Any], case_name: str) -> dict[str, Any]:
    case = spec["cases"][case_name]
    if not isinstance(case, dict) or set(case) != {"input", "expected"}:
        raise ValueError(f"{case_name} case must contain input and expected")
    if not isinstance(case["input"], dict) or not isinstance(case["expected"], dict):
        raise ValueError(f"{case_name} input and expected must be objects")
    try:
        observed = EXERCISES[spec["exercise_type"]](case["input"])
    except (IndexError, KeyError, TypeError, ValueError) as error:
        raise ValueError(f"{case_name} input is invalid: {error}") from error
    if observed != case["expected"]:
        raise ValueError(f"{case_name} mismatch: expected={case['expected']} observed={observed}")
    return observed


def verify_spec(path: Path) -> dict[str, dict[str, Any]]:
    spec = load_spec(path)
    return {name: run_case(spec, name) for name in ("positive", "failure")}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    parser.add_argument("--case", choices=("positive", "failure"))
    args = parser.parse_args()
    try:
        spec = load_spec(args.spec)
        if args.case:
            result: Any = run_case(spec, args.case)
        else:
            result = {name: run_case(spec, name) for name in ("positive", "failure")}
    except ValueError as error:
        print(f"article practice failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
