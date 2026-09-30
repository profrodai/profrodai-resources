# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 17's controlled improvement: propose, evaluate, then activate or keep what works.

Every piece underneath is earlier learner code. Chapter 7 stages immutable skill versions, takes
the active-configuration snapshot and activates a version only if its evaluation passed and the
configuration it was evaluated against is still the active one. Chapter 16's harness evaluates a
candidate over its authored cases and writes the report. This file adds the path between them: a
proposal that records the feedback behind it, a change operation that saves the report before
anything switches, and a rollback that must re-earn its place under today's configuration.
"""

import hashlib
import json
import runpy
from collections.abc import Callable
from pathlib import Path
from typing import Any

LEARNER = Path(__file__).resolve().parent
SKILLS = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch07_skills_learner.py"))
HARNESS = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch16_harness_learner.py"))
MEMORY = SKILLS["MEMORY"]


def propose_skill(
    db,
    folder: Path,
    *,
    name: str,
    version: str,
    instructions: str,
    requires: list[str],
    feedback_source: str,
    request: str,
):
    """Write a new candidate file, stage it through Chapter 7, and record why it was proposed.

    The file is created exclusively, so an existing proposal is never overwritten; the staged row
    is the authority afterwards. The event names the feedback and the candidate's content hash:
    provenance, not authentication of text claiming to come from Lucy."""
    source = folder / f"{name}-{version}.toml"
    with source.open("x") as stream:
        stream.write(
            "name="
            + json.dumps(name)
            + "\nversion="
            + json.dumps(version)
            + "\ninstructions="
            + json.dumps(instructions)
            + "\nrequires="
            + json.dumps(requires)
            + "\n"
        )
    skill = SKILLS["stage_skill"](db, source)
    with db.immediate() as connection:
        MEMORY["record_event"](
            connection,
            "skill.proposed",
            {
                "name": skill.name,
                "version": skill.version,
                "candidate_sha256": hashlib.sha256(skill.model_dump_json().encode()).hexdigest(),
                "feedback_source": feedback_source,
                "request": request,
            },
        )
    return skill


def case_results(report: dict[str, Any]) -> dict[str, bool]:
    """Each case-run's verdict, named as Chapter 7's activation requires."""
    return {f"{row['case']}:{row['repetition']}": row["passed"] is True for row in report["cases"]}


def was_activated(db, name: str, version: str) -> bool:
    return (
        db.connection.execute(
            "SELECT 1 FROM memory_events WHERE kind='assistant.skill.activated' "
            "AND json_extract(payload,'$.name')=? AND json_extract(payload,'$.version')=? LIMIT 1",
            (name, version),
        ).fetchone()
        is not None
    )


def change_skill(
    db,
    name: str,
    version: str,
    model_factory: Callable[[], Any],
    report_root: Path,
    *,
    repeats: int = 1,
    rollback: bool = False,
    model_label: str = "offline fixture",
) -> dict[str, Any]:
    """Evaluate a staged version with the other active skills, save the report, then switch.

    Returns REJECTED (a named case failed), ACTIVATED, ROLLED_BACK (an earlier activated version
    passed again) or STALE (the active configuration changed during evaluation; evaluate again).
    The report is written before any switch, so every outcome has its evidence."""
    row = db.connection.execute(
        "SELECT content FROM assistant_skills WHERE name=? AND version=?", (name, version)
    ).fetchone()
    if row is None:
        raise ValueError("stage the exact candidate before requesting activation")
    if rollback and not was_activated(db, name, version):
        raise ValueError("rollback requires a previously activated version")
    skill = SKILLS["Skill"].model_validate_json(row[0])
    baseline, active = SKILLS["skill_snapshot"](db)
    report = HARNESS["evaluate"](model_factory, skill=skill, skills=active, repeats=repeats)
    report["active_skill_state"] = baseline
    report["model_label"] = model_label
    report["operation"] = "rollback" if rollback else "activation"
    path, digest = HARNESS["save_report"](report_root, report)
    results = case_results(report)
    required = frozenset(
        f"{case.name}:{repeat}" for case in HARNESS["CASES"] for repeat in range(repeats)
    )
    status = "REJECTED"
    if report["passed"]:
        try:
            SKILLS["activate_skill"](
                db,
                name,
                version,
                evaluate=lambda _: results,
                required_cases=required,
                expected_state=baseline,
            )
            status = "ROLLED_BACK" if rollback else "ACTIVATED"
        except PermissionError:
            status = "STALE"
    with db.immediate() as connection:
        MEMORY["record_event"](
            connection,
            "skill.evaluated",
            {
                "name": name,
                "version": version,
                "passed": report["passed"],
                "report": path.name,
                "sha256": digest,
                "rollback": rollback,
                "activation_status": status,
            },
        )
    return {
        "status": status,
        "passed": report["passed"],
        "name": name,
        "version": version,
        "report": str(path),
        "sha256": digest,
        "interpretation": "Passing named scenario checks is bounded evidence. "
        "STALE requires a new evaluation before activation. "
        "The offline model does not measure a skill's language-model quality.",
    }


class FollowsCandidate(HARNESS["OfflineShopModel"]):
    """A deterministic policy fixture, not a measure of language-model quality: it obeys one
    specific instruction in its context, so a known-bad candidate visibly changes its answers."""

    def complete(self, messages, *args, **kwargs):
        turn = super().complete(messages, *args, **kwargs)
        if "Report every amount in euros." in messages[0]["content"]:
            return HARNESS["ModelTurn"](
                turn.content.replace("cents USD", "euros"), turn.calls, turn.output_tokens
            )
        return turn
