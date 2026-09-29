# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 17: evaluated procedure changes, preserved reports, rollback and stale guards.

Every function it calls is the learner's own: Chapter 17's change operation on Chapter 16's
harness and Chapter 7's skills, and the chapters beneath them.
"""

import hashlib
import json
import math
import random
import runpy
import tempfile
import tomllib
from pathlib import Path

BOOK = Path(__file__).resolve().parents[1]
OPTIMIZATION = runpy.run_path(
    str(BOOK / "learner/profrod_sovereign_agent_ch17_optimization_learner.py")
)
IMPROVE = runpy.run_path(str(BOOK / "learner/profrod_sovereign_agent_ch17_improvement_learner.py"))
SKILLS, HARNESS = IMPROVE["SKILLS"], IMPROVE["HARNESS"]
FollowsCandidate, change_skill = IMPROVE["FollowsCandidate"], IMPROVE["change_skill"]


def active(db):
    return [(s.name, s.version) for s in SKILLS["skill_snapshot"](db)[1]]


def refused(error, action):
    try:
        action()
    except error:
        return True
    return False


def optimization():
    """Part A's functions, each checked against an independent computation."""
    expected_max = OPTIMIZATION["expected_max_normal"]
    assert math.isclose(expected_max(2), 1 / math.sqrt(math.pi), abs_tol=1e-6)
    rng = random.Random(16)
    draws = [max(rng.gauss(0, 1) for _ in range(8)) for _ in range(40_000)]
    assert abs(sum(draws) / len(draws) - expected_max(8)) < 0.02
    print("ok   E[max of 2 normals] = 1/sqrt(pi); E[max of 8] agrees with simulation")

    single = OPTIMIZATION["winners_curse"]([0.5], 6, 20_000, seed=1)
    assert abs(single["optimism"]) < 0.01
    print("ok   with one candidate there is no selection, and no optimism")

    bt, loglik = OPTIMIZATION["bradley_terry"], OPTIMIZATION["log_likelihood"]
    assert bt(0.3, 0.3) == 0.5 and math.isclose(bt(1.0, -0.5) + bt(-0.5, 1.0), 1.0)
    lab = runpy.run_path(
        str(BOOK / "experiments/profrod_sovereign_agent_textbook_ch17_optimization_v1.py")
    )
    receipt = json.loads(
        (BOOK.parents[1] / "docs/evidence/book-ch17/ch17-optimization-receipt-v1.json").read_text()
    )
    assert json.loads(json.dumps(lab["offline"]())) == receipt["offline"]
    rng = random.Random(3)
    comparisons = [(0, 1)] * 30 + [(1, 0)] * 10 + [(1, 2)] * 25 + [(2, 1)] * 15
    fitted = OPTIMIZATION["fit_bradley_terry"](comparisons, 3)
    for i in range(3):
        bumped = list(fitted)
        bumped[i] += 1e-5
        assert abs(loglik(comparisons, bumped) - loglik(comparisons, fitted)) < 1e-6
    print("ok   the receipt's offline section recomputes exactly; the BT fit is a stationary point")


def claude_receipt():
    """The recorded Claude runs of the change operation: dispositions follow from the named
    checks, the counts and the stricter recount recompute from the retained answers, and the
    cost from the token counts."""
    lab = runpy.run_path(
        str(BOOK / "experiments/profrod_sovereign_agent_textbook_ch17_change_claude_v1.py")
    )
    receipt = json.loads(
        (BOOK.parents[1] / "docs/evidence/book-ch17/ch17-change-claude-receipt-v1.json").read_text()
    )
    for versions in receipt["models"].values():
        for run in versions.values():
            assert run["cases_passed"] == run["cases"] - len(run["failed_checks"])
            assert (run["status"] == "ACTIVATED") == (run["cases_passed"] == run["cases"])
            assert run["answers_mentioning_euros"] == sum(
                bool(lab["EUROS"].search(answer)) for answer in run["answers"].values()
            )
            assert run["answer_words"] == {c: lab["words"](a) for c, a in run["answers"].items()}
    assert receipt["stricter_currency_check"]["cases_passing"] == lab["stricter"](receipt["models"])
    haiku, sonnet = (
        receipt["models"]["claude-haiku-4-5-20251001"],
        receipt["models"]["claude-sonnet-5-5"],
    )
    assert haiku["2"]["status"] == "ACTIVATED" and haiku["2"]["answers_mentioning_euros"] == 0
    assert sonnet["2"]["status"] == "REJECTED" and sonnet["2"]["answers_mentioning_euros"] == 8
    prices = runpy.run_path(
        str(BOOK / "experiments/profrod_sovereign_agent_claude_messages_v1.py")
    )["PRICES"]
    usage = receipt["claude"]
    cost = sum(
        (
            used["input_tokens"] * prices[model][0]
            + used["output_tokens"] * prices[model][1]
            + used["cache_creation_input_tokens"] * prices[model][2]
            + used["cache_read_input_tokens"] * prices[model][3]
        )
        / 1_000_000
        for model, used in usage["usage"].items()
    )
    assert usage["costUsd"] == round(cost, 4) <= usage["ceilingUsd"]
    print(
        "ok   on Claude, Haiku activated the euros guidance it ignored; Sonnet's rejection came from"
        f" explaining it; {usage['costUsd']:.2f} USD"
    )


def main():
    optimization()
    claude_receipt()
    original = tomllib.loads(
        (BOOK / "skills/profrod_sovereign_agent_textbook_opening_check_v1.toml").read_text()
    )
    name = original["name"]
    with tempfile.TemporaryDirectory(prefix="lucy-improvement-") as temporary:
        root = Path(temporary)
        db = SKILLS["open_skills"](root / "agent.sqlite")
        reports = root / "reports"

        def propose(version, instructions, skill=name):
            return IMPROVE["propose_skill"](
                db,
                root,
                name=skill,
                version=version,
                instructions=instructions,
                requires=original["requires"],
                feedback_source="fixture/lucy/brief-1",
                request="Keep amounts in USD and make the closing sentence concise.",
            )

        propose("1", original["instructions"])
        assert active(db) == []
        assert refused(FileExistsError, lambda: propose("1", original["instructions"]))
        assert refused(ValueError, lambda: change_skill(db, name, "9", FollowsCandidate, reports))
        assert refused(
            ValueError,
            lambda: change_skill(db, name, "1", FollowsCandidate, reports, rollback=True),
        )
        print("ok   proposals stage inactive; unstaged or never-activated versions are refused")
        initial = change_skill(db, name, "1", FollowsCandidate, reports)
        assert initial["status"] == "ACTIVATED" and active(db) == [(name, "1")]
        propose("2", original["instructions"] + "\nReport every amount in euros.")
        bad = change_skill(db, name, "2", FollowsCandidate, reports)
        report = json.loads(Path(bad["report"]).read_text())
        failures = sum(not row["checks"]["currency_labels"] for row in report["cases"])
        assert bad["status"] == "REJECTED" and failures == 6 and active(db) == [(name, "1")]
        assert all(
            row["checks"]["quantities"] for row in report["cases"]
        )  # only the currency changed
        print("Regressing guidance:", bad["status"], "currency failures", failures)
        # A rejected version was never activated, so it cannot be "rolled back" to.
        assert refused(
            ValueError,
            lambda: change_skill(db, name, "2", FollowsCandidate, reports, rollback=True),
        )
        propose("3", original["instructions"] + "\nKeep the closing sentence concise.")
        good = change_skill(db, name, "3", FollowsCandidate, reports)
        assert good["status"] == "ACTIVATED" and active(db) == [(name, "3")]
        print("Passing candidate:", good["status"])
        rolled = change_skill(db, name, "1", FollowsCandidate, reports, rollback=True)
        assert rolled["status"] == "ROLLED_BACK" and active(db) == [(name, "1")]
        print("Earlier activated version:", rolled["status"])
        propose("4", original["instructions"] + "\nRetain source names in explanations.")
        propose("1", "Keep reports concise.", skill="reporting")
        other = SKILLS["open_skills"](root / "agent.sqlite")

        class ConcurrentChange(FollowsCandidate):
            changed = False

            def complete(self, *args, **kwargs):
                if not ConcurrentChange.changed:
                    ConcurrentChange.changed = True
                    result = change_skill(other, "reporting", "1", FollowsCandidate, reports)
                    assert result["status"] == "ACTIVATED"
                return super().complete(*args, **kwargs)

        stale = change_skill(db, name, "4", ConcurrentChange, reports)
        assert stale["status"] == "STALE" and stale["passed"]
        print("Configuration changes during evaluation:", stale["status"])
        assert active(db) == [(name, "1"), ("reporting", "1")]
        results = (initial, bad, good, rolled, stale)
        for result in results:
            raw = Path(result["report"]).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == result["sha256"]
            assert json.loads(raw)["acceptance"]["status"] in {"REVIEW_REQUIRED", "REJECTED"}
        rows = db.connection.execute("SELECT count(*) FROM assistant_skills").fetchone()[0]
        assert rows == 5
        print("Retained version rows:", rows)
        saved = len(list(reports.glob("*.json")))
        assert saved == 6  # five here, and the reporting activation during the race
        print("Retained evaluation reports:", saved)
        # The reporting skill was evaluated with the active opening procedure beside it.
        race = [
            json.loads(path.read_text())
            for path in reports.glob("*.json")
            if json.loads(path.read_text())["candidate"]["name"] == "reporting"
        ]
        assert [(s["name"], s["version"]) for s in race[0]["skills"]] == [
            (name, "1"),
            ("reporting", "1"),
        ]
        events = {
            kind: count
            for kind, count in db.connection.execute(
                "SELECT kind, count(*) FROM memory_events GROUP BY kind"
            )
        }
        assert events["skill.proposed"] == 5 and events["skill.evaluated"] == 6
        assert events["assistant.skill.activated"] == 4
        print("Proposals retain feedback provenance:", events["skill.proposed"])
        other.close()
        db.close()
        reopened = SKILLS["open_skills"](root / "agent.sqlite")
        assert active(reopened) == [(name, "1"), ("reporting", "1")]
        print("Active configuration survives reopen:", True)
        reopened.close()


if __name__ == "__main__":
    main()
