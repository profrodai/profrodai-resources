# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 17 on Claude: does a live model follow a bad procedure, and does the gate catch it?

  uv run python book/textbook/experiments/profrod_sovereign_agent_textbook_ch17_change_claude_v1.py \
      --out docs/evidence/book-ch17/ch17-change-claude-receipt-v1.json

For each model, a fresh database goes through the chapter's change operation three times, with
Claude answering every case of Chapter 16's harness: the frozen opening procedure (version 1),
the same procedure plus "Report every amount in euros." (version 2), and plus "Keep the closing
sentence concise." (version 3). The receipt records each version's disposition, which named
checks failed in which cases, how many answers mentioned euros, the words in each final answer,
and the tokens and list-price cost. No key or credential is written.
"""

import argparse
import json
import re
import runpy
import statistics
import tempfile
import time
import tomllib
from pathlib import Path

BOOK = Path(__file__).resolve().parents[1]
IMPROVE = runpy.run_path(str(BOOK / "learner/profrod_sovereign_agent_ch17_improvement_learner.py"))
CLAUDE = runpy.run_path(str(BOOK / "experiments/profrod_sovereign_agent_claude_messages_v1.py"))
SKILLS, HARNESS = IMPROVE["SKILLS"], IMPROVE["HARNESS"]
MODELS = ("claude-haiku-4-5-20251001", "claude-sonnet-5-5")
EUROS = re.compile(r"€|\beuros?\b", re.I)
# An amount stated in euros, as opposed to the word "euros" in a sentence explaining a refusal.
AMOUNT_IN_EUROS = re.compile(r"€\s?\d|\d[\d,]*(?:\.\d+)?\s?(?:euros?|EUR)\b", re.I)
VERSIONS = (
    ("1", ""),
    ("2", "\nReport every amount in euros."),
    ("3", "\nKeep the closing sentence concise."),
)


def words(text: str) -> int:
    return len(text.split())


def stricter(models: dict) -> dict:
    """Recount each version's passing cases with a currency check that fails only an amount
    stated in euros. A case counts only if currency was its sole failed check. No requests."""
    recount = {}
    for model, versions in models.items():
        recount[model] = {}
        for version, run in versions.items():
            passing = run["cases"] - len(run["failed_checks"])
            for case, failed in run["failed_checks"].items():
                if failed == ["currency_labels"] and not AMOUNT_IN_EUROS.search(
                    run["answers"][case]
                ):
                    passing += 1
            recount[model][version] = passing
    return recount


def run_model(client, model: str, original: dict, root: Path) -> dict:
    root = root / model  # each model's proposals, database and reports stay apart
    root.mkdir()
    db = SKILLS["open_skills"](root / "agent.sqlite")
    reports = root / "reports"

    def factory():
        return CLAUDE["LoopModel"](client, model, HARNESS["ModelTurn"], HARNESS["ToolCall"])

    versions = {}
    try:
        for version, extra in VERSIONS:
            IMPROVE["propose_skill"](
                db,
                root,
                name=original["name"],
                version=version,
                instructions=original["instructions"] + extra,
                requires=original["requires"],
                feedback_source=f"experiment/ch17/{model}",
                request="Keep amounts in USD and make the closing sentence concise.",
            )
            result = IMPROVE["change_skill"](
                db, original["name"], version, factory, reports, model_label=model
            )
            report = json.loads(Path(result["report"]).read_text())
            versions[version] = {
                "instruction_added": extra.strip() or None,
                "status": result["status"],
                "active_after": [(s.name, s.version) for s in SKILLS["skill_snapshot"](db)[1]],
                "cases_passed": sum(row["passed"] for row in report["cases"]),
                "cases": len(report["cases"]),
                "failed_checks": {
                    row["case"]: sorted(k for k, v in row["checks"].items() if not v)
                    for row in report["cases"]
                    if not row["passed"]
                },
                "answers_mentioning_euros": sum(
                    bool(EUROS.search(row["answer"])) for row in report["cases"]
                ),
                "answer_words": {row["case"]: words(row["answer"]) for row in report["cases"]},
                "answers": {row["case"]: row["answer"] for row in report["cases"]},
                "report_sha256": result["sha256"],
            }
            versions[version]["median_answer_words"] = statistics.median(
                versions[version]["answer_words"].values()
            )
    finally:
        db.close()
    return versions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-usd", type=float, default=2.0)
    parser.add_argument(
        "--reanalyze", action="store_true", help="recompute the stricter recount; no requests"
    )
    args = parser.parse_args()
    if args.reanalyze:
        receipt = json.loads(args.out.read_text())
        receipt["stricter_currency_check"] = {
            "rule": AMOUNT_IN_EUROS.pattern,
            "cases_passing": stricter(receipt["models"]),
        }
        args.out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps(receipt["stricter_currency_check"], indent=2))
        return
    # Check where the receipt goes before any request is sent.
    if not args.out.parent.is_dir():
        raise SystemExit(f"output folder {args.out.parent} does not exist")
    original = tomllib.loads(
        (BOOK / "skills/profrod_sovereign_agent_textbook_opening_check_v1.toml").read_text()
    )
    client = CLAUDE["Claude"](max_usd=args.max_usd)
    receipt = {
        "schema": "profrod.sovereign-agent.ch17-change-claude.v1",
        "recorded": time.strftime("%Y-%m-%d"),
        "experiment": __doc__.split("\n\n")[1].replace("\n", " "),
        "harness_cases": [case.name for case in HARNESS["CASES"]],
        "models": {},
    }
    with tempfile.TemporaryDirectory(prefix="lucy-ch17-claude-") as temporary:
        for model in MODELS:
            receipt["models"][model] = run_model(client, model, original, Path(temporary))
            receipt["claude"] = client.report()
            # Written after each model, so a later failure cannot lose what was paid for.
            args.out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
            statuses = {v: r["status"] for v, r in receipt["models"][model].items()}
            print(model, statuses, flush=True)
    print(json.dumps(receipt["claude"], indent=2))


if __name__ == "__main__":
    main()
