# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 7: stage, evaluate, activate, and use one local opening procedure."""

import argparse
import json
import runpy
import statistics
import tempfile
from pathlib import Path

BOOK = Path(__file__).resolve().parents[1]
SENSITIVITY = runpy.run_path(
    str(BOOK / "learner/profrod_sovereign_agent_ch07_prompt_sensitivity_learner.py")
)
SKILLS = runpy.run_path(str(BOOK / "learner/profrod_sovereign_agent_ch07_skills_learner.py"))
MEMORY, LOOP = SKILLS["MEMORY"], SKILLS["LOOP"]
TOOLS = LOOP["shop_tools"]
ModelTurn, ToolCall, Replay = LOOP["ModelTurn"], LOOP["ToolCall"], LOOP["ReplayModel"]
SOURCE = BOOK / "skills/profrod_sovereign_agent_textbook_opening_check_v1.toml"


def prompt_sensitivity():
    """Part A's measures, checked by definition and against the receipt's retained answers."""
    label_of, spread = SENSITIVITY["label_of"], SENSITIVITY["spread"]
    assert label_of("Stock.") == "stock" and label_of("I would refuse this") == "refuse"
    assert label_of("pay") is None
    values = [0.25, 0.5, 0.75, 0.5]
    assert abs(spread(values)["sd"] - statistics.stdev(values)) < 1e-12
    assert SENSITIVITY["all_agree_share"]([[True, False, True], [True, True, True]]) == 2 / 3
    print("ok   labels, spread and agreement by their definitions")
    receipt = json.loads(
        (
            BOOK.parents[1] / "docs/evidence/book-ch07/ch07-prompt-sensitivity-receipt-v1.json"
        ).read_text()
    )
    for model in receipt["models"]:
        rows = {}
        for run in receipt["runs"]:
            if run["model"] == model["model"]:
                rows.setdefault(run["prompt"], []).append(
                    label_of(run["answer"]) == run["expected"]
                )
        recomputed = {name: round(sum(r) / len(r), 3) for name, r in rows.items()}
        assert recomputed == model["accuracy_by_prompt"], model["model"]
    print("ok   every prompt's accuracy recomputes from the retained answers")


def refused(error, action):
    try:
        action()
    except error:
        return True
    return False


def admission(root):
    """Bounded reads, strict records and immutable versions, refused before anything is stored."""
    read_skill, skill_model = SKILLS["read_skill"], SKILLS["Skill"]
    bounded = root / "bounded.toml"
    bounded.write_bytes(b"x" * 16_384)
    assert len(read_skill(bounded)) == 16_384
    bounded.write_bytes(b"x" * 16_385)
    assert refused(ValueError, lambda: read_skill(bounded))
    link = root / "link.toml"
    link.symlink_to(SOURCE.resolve())
    assert refused(ValueError, lambda: read_skill(link))
    assert refused(ValueError, lambda: skill_model.model_validate({"name": "x", "version": "1"}))
    db = SKILLS["open_skills"](root / "admission.sqlite")
    SKILLS["stage_skill"](db, SOURCE)
    SKILLS["stage_skill"](db, SOURCE)
    changed = root / "changed.toml"
    changed.write_text('name="opening_check"\nversion="1"\ninstructions="Summarize stock only"\n')
    assert refused(ValueError, lambda: SKILLS["stage_skill"](db, changed))
    row = db.connection.execute("SELECT count(*), sum(active) FROM assistant_skills").fetchone()
    assert tuple(row) == (1, 0)
    print("Bounded read, strict record and immutable version: refusals before storage")
    db.close()


def judged(root):
    """The evaluator judges tool observations, so a near miss fails its case."""
    stock = ModelTurn(calls=(ToolCall(id="s", name="list_stock", arguments={}),))

    def draft(identifier, sku, quantity):
        arguments = {"sku": sku, "quantity": quantity}
        return ToolCall(id=identifier, name="draft_order", arguments=arguments)

    skill = SKILLS["load_skill"](SOURCE)
    wrong_opening = {
        "only vanilla": [stock, ModelTurn(calls=(draft("v", "V", 6),)), ModelTurn("V 6, USD")],
        "prose only": [stock, ModelTurn("Vanilla 6 and strawberry 4 tubs, USD")],
        "refused then right": [
            stock,
            ModelTurn(calls=(draft("x", "V", 5),)),
            ModelTurn(calls=(draft("v", "V", 6), draft("strawberry", "S", 4))),
            ModelTurn("V 6 and S 4, USD"),
        ],
    }
    for turns in wrong_opening.values():
        models = iter([Replay(turns), SKILLS["OfflineShopModel"](), SKILLS["OfflineShopModel"]()])
        results = SKILLS["evaluate_opening"](lambda models=models: next(models), skill)
        assert results == {"opening": False, "at_threshold": True, "reserved_stock": True}
    tools = SKILLS["case_tools"](SKILLS["OPENING_CASES"][0])
    assert tools.invoke(draft("q", "V", 5)) == {"ok": False, "error": "tool_failed"}
    print("Evaluator fails a partial draft, prose without drafts and a refused tool call")


def activation(root, model_factory):
    """Evaluation gates activation; a stale baseline or a missing case refuses it."""
    activate, snapshot = SKILLS["activate_skill"], SKILLS["skill_snapshot"]
    required = frozenset(case.name for case in SKILLS["OPENING_CASES"])
    path = root / "agent.sqlite"
    db = SKILLS["open_skills"](path)
    MEMORY["remember"](db, "lucy", "format", "three bullets", "lucy/message/3")
    candidate = SKILLS["stage_skill"](db, SOURCE)
    print("Active before evaluation:", len(snapshot(db)[1]))
    assert refused(
        ValueError,
        lambda: activate(
            db, "opening_check", "1", evaluate=lambda s: {"opening": True}, required_cases=required
        ),
    )
    assert refused(
        ValueError,
        lambda: activate(
            db,
            "opening_check",
            "1",
            evaluate=lambda s: dict.fromkeys(required, 1),
            required_cases=required,
        ),
    )
    assert refused(
        ValueError, lambda: activate(db, "missing", "1", evaluate=dict, required_cases=required)
    )
    assert refused(
        ValueError,
        lambda: activate(
            db, "opening_check", "1", evaluate=lambda s: {}, required_cases=frozenset()
        ),
    )
    reports = []

    def check(skill):
        reports.append(SKILLS["evaluate_opening"](model_factory, skill))
        return reports[-1]

    stale = snapshot(db)[0]
    reporting = root / "reporting.toml"
    reporting.write_text('name="reporting"\nversion="1"\ninstructions="Use short headings"\n')
    SKILLS["stage_skill"](db, reporting)
    activate(
        db,
        "reporting",
        "1",
        evaluate=lambda s: {"probe": True},
        required_cases=frozenset({"probe"}),
    )
    assert refused(
        PermissionError,
        lambda: activate(
            db,
            candidate.name,
            candidate.version,
            evaluate=check,
            required_cases=required,
            expected_state=stale,
        ),
    )
    try:
        activate(db, candidate.name, candidate.version, evaluate=check, required_cases=required)
    except ValueError:
        print("Candidate activation: REFUSED", json.dumps(reports[-1]))
        db.close()
        return None
    print("Candidate cases:", len(reports[-1]), all(reports[-1].values()))
    second = root / "reporting-2.toml"
    second.write_text('name="reporting"\nversion="2"\ninstructions="Use one heading"\n')
    SKILLS["stage_skill"](db, second)
    activate(
        db,
        "reporting",
        "2",
        evaluate=lambda s: {"probe": True},
        required_cases=frozenset({"probe"}),
    )
    activate(
        db,
        "reporting",
        "1",
        evaluate=lambda s: {"probe": True},
        required_cases=frozenset({"probe"}),
    )
    db.close()
    return path


def main():
    prompt_sensitivity()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--model", default="qwen3")
    parser.add_argument("--transcript", action="store_true")
    args = parser.parse_args()
    model_factory = (
        (lambda: LOOP["HTTPModel"](model=args.model, reasoning_effort="none"))
        if args.live
        else SKILLS["OfflineShopModel"]
    )
    with tempfile.TemporaryDirectory(prefix="lucy-skills-") as temporary:
        root = Path(temporary)
        admission(root)
        judged(root)
        path = activation(root, model_factory)
        if path is None:
            return 1
        db = SKILLS["open_skills"](path)
        active = [(s.name, s.version) for s in SKILLS["skill_snapshot"](db)[1]]
        assert active == [("opening_check", "1"), ("reporting", "1")]
        print("Active after reopening:", active)
        dispatcher = TOOLS["build_tools"](TOOLS["SHOP"])
        prompt = LOOP["messages"][1]["content"]
        context = SKILLS["context"]
        denied = context(db, "lucy", prompt, allowed=frozenset({"list_stock"}))
        # The reporting skill needs no tools, so it stays; the opening procedure does not.
        assert '"opening_check"' not in denied[0]["content"]
        assert '"reporting"' in denied[0]["content"]
        assert "three bullets" in denied[0]["content"]
        print("Missing required tool excludes skill:", True)
        tight = context(db, "lucy", prompt, allowed=dispatcher.allowed, byte_budget=256)
        assert '"opening_check"' not in tight[0]["content"]
        messages = context(db, "lucy", prompt, allowed=dispatcher.allowed)
        assert '"opening_check"' in messages[0]["content"]
        assert "three bullets" in messages[0]["content"]
        purchase = dispatcher.invoke(TOOLS["ToolCall"](id="p", name="purchase", arguments={}))
        assert purchase == {"ok": False, "error": "tool_not_allowed"}
        result = LOOP["run_loop"](model_factory(), dispatcher, messages)
        passed = result.status == "COMPLETED" and LOOP["draft_evidence"](result)
        print("Draft evidence:", "PASS" if passed else "FAIL")
        print("Purchase tool: refused by the dispatcher")
        if args.transcript:
            print(json.dumps({"transcript": result.messages}, indent=2))
        db.close()
        return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
