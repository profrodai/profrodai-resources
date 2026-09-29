# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 21: the context manager keeps its budget, its order and the records it must not lose.

Every check runs without a model. Compaction is tested with a deterministic summarizer, including
one that forgets everything, which is the failure pinned records exist to survive.
"""

import json
import runpy
import statistics
import tempfile
from pathlib import Path

BOOK = Path(__file__).resolve().parents[1]
CTX = runpy.run_path(str(BOOK / "learner/profrod_sovereign_agent_ch21_context_learner.py"))
EXPERIMENT = runpy.run_path(
    str(BOOK / "experiments/profrod_sovereign_agent_textbook_ch21_context_v1.py")
)
Layers = CTX["Layers"]
Overflow = CTX["ContextOverflowError"]


def shortening():
    estimate = CTX["estimate_tokens"]
    assert estimate("") == 0 and estimate("abcd") == 1 and estimate("abcde") == 2
    filler = [f"line {i}" for i in range(10)]
    assert CTX["place_at_depth"](filler, ["FACT"], 0.0)[0] == "FACT"
    assert CTX["place_at_depth"](filler, ["FACT"], 1.0)[-1] == "FACT"
    assert CTX["place_at_depth"](filler, ["FACT"], 0.5)[5] == "FACT"
    text = "\n".join(f"row {i:03d} " + "x" * 30 for i in range(200))
    for cut in (CTX["head"](text, 300), CTX["head_and_tail"](text, 300)):
        assert estimate(cut) <= 320, estimate(cut)
    both = CTX["head_and_tail"](text, 300)
    assert both.startswith("row 000") and both.endswith("x" * 30) and "lines omitted" in both
    assert "row 199" in both
    print("ok   estimates, depths and both cuts stay inside their budgets")


def spilling():
    with tempfile.TemporaryDirectory() as folder:
        small = CTX["spill_tool_result"]("tiny", 100, Path(folder), "t1")
        assert small.path is None and small.text == "tiny"
        big_text = "\n".join(f"sale {i} | vanilla | 2 tubs" for i in range(2000))
        big = CTX["spill_tool_result"](big_text, 400, Path(folder), "sales")
        assert big.path is not None and big.path.read_text() == big_text
        assert str(big.path) in big.text and big.original_tokens > 400
        assert CTX["estimate_tokens"](big.text) <= 400
    print("ok   an oversized tool result is saved whole and replaced by a pointer that fits")


def layers_and_budget():
    layers = Layers(
        "You are Lucy's assistant.",
        ["Never order mango from Frostline."],
        [{"role": "user", "content": "hello"}],
    )
    messages = layers.messages()
    assert messages[0]["role"] == "system" and "Never order mango" in messages[0]["content"]
    assert messages[1] == {"role": "user", "content": "hello"}
    report = CTX["budget_report"](layers)
    assert report["total"] == report["system"] + report["pinned"] + report["conversation"]
    print("ok   stable layers come first, and every token is accounted to a layer")


def conversation(turns: int) -> list[dict]:
    messages = []
    for i in range(turns):
        messages.append({"role": "user", "content": f"Question {i}: check the freezer."})
        messages.append(CTX["tool_message"]("stock_level", {"rows": ["vanilla 12"] * 60}))
        messages.append({"role": "assistant", "content": f"Answer {i}."})
    return messages


def compaction():
    rule = "Never order mango from Frostline."
    base = conversation(12)
    base.insert(0, {"role": "user", "content": rule})
    layers = Layers("You are Lucy's assistant.", [], base)
    cleared = CTX["clear_old_tool_results"](base, 2)
    tools = [m for m in cleared if m["role"] == "tool"]
    assert len(tools) == 12 and all("cleared" in m["content"] for m in tools[:-2])
    assert all("cleared" not in m["content"] for m in tools[-2:])

    same, report = CTX["compact"](layers, 100_000, lambda older: "unused")
    assert same.conversation == base and report["steps"] == []

    total = CTX["budget_report"](Layers(layers.system, [], cleared))["total"]
    one, report = CTX["compact"](layers, total, lambda older: "unused")
    assert [s["step"] for s in report["steps"]] == ["clear-tool-results"]

    forgetful = lambda older: "(nothing)"  # noqa: E731
    two, report = CTX["compact"](layers, 300, forgetful)
    assert [s["step"] for s in report["steps"]] == ["clear-tool-results", "summarize"]
    assert two.conversation[-3]["content"] == "Question 11: check the freezer."
    assert all(rule not in m["content"] for m in two.messages()), "a transcript-only rule survived"

    pinned, _ = CTX["compact"](Layers(layers.system, [rule], base), 300, forgetful)
    assert rule in pinned.messages()[0]["content"]
    print("ok   compaction clears tool results first, then summarizes; only pinned rules survive a")
    print("     summarizer that forgets everything")


def overflow():
    huge = ["x" * 4000]
    try:
        CTX["compact"](Layers("s", huge, []), 500, lambda older: "")
        raise AssertionError("pinned records larger than the budget were accepted")
    except Overflow:
        pass
    latest = [{"role": "user", "content": "y" * 8000}]
    try:
        CTX["compact"](Layers("s", [], latest), 500, lambda older: "")
        raise AssertionError("a latest turn larger than the budget was accepted")
    except Overflow:
        pass
    print("ok   a context that cannot fit is refused, never cut silently")


def recomputed(receipt):
    """One receipt's tables, recomputed from its own rows."""
    for entry in receipt["depthTable"]:
        rows = [
            r
            for r in receipt["depth"][entry["model"]]
            if r["length"] == entry["length"] and r["depth"] == entry["depth"]
        ]
        assert entry["n"] == len(rows) and entry["correct"] == sum(r["correct"] for r in rows)
        tokens = statistics.median(r["promptTokens"] or 0 for r in rows)
        assert entry["medianPromptTokens"] == tokens
    for results in receipt["compaction"].values():
        scored = [results["full"]] + [
            result
            for budget, strategies in results.items()
            if budget.isdigit()
            for result in strategies.values()
        ]
        for result in scored:
            assert result["correct"] == sum(r["correct"] for r in result["rows"])
    text, truth = EXPERIMENT["sales_log"]()
    assert truth == receipt["truncation"][receipt["models"][0]]["_truth"]
    digest = EXPERIMENT["digest"](text)
    assert f"pistachio {truth['pistachio']}" in digest and f"{truth['count']} sales" in digest
    estimates = receipt["estimate"]
    for row in estimates if isinstance(estimates, list) else sum(estimates.values(), []):
        assert row["estimateError"] == round(row["estimate"] / row["actual"] - 1, 3)


def claude_cost(usage):
    """List-price cost from token counts, with the client's own price table."""
    prices = EXPERIMENT["CLAUDE"]["PRICES"]
    total = 0.0
    for model, used in usage["usage"].items():
        price_in, price_out, price_write, price_read = prices[model]
        total += (
            used["input_tokens"] * price_in
            + used["output_tokens"] * price_out
            + used["cache_creation_input_tokens"] * price_write
            + used["cache_read_input_tokens"] * price_read
        ) / 1_000_000
    return round(total, 4)


def measured_context():
    """Both receipts' tables recomputed from their rows, and their inputs regenerated here."""
    evidence = BOOK.parents[1] / "docs/evidence/book-ch21"
    recomputed(json.loads((evidence / "ch21-context-receipt-v1.json").read_text()))
    raw = (evidence / "ch21-context-claude-receipt-v1.json").read_text()
    assert "sk-ant" not in raw and "x-api-key" not in raw, "a receipt must never hold a key"
    claude = json.loads(raw)
    recomputed(claude)
    runs = [claude["usage"], *(run["usage"] for run in claude.get("additionalRuns", []))]
    for usage in runs:
        assert usage["costUsd"] == claude_cost(usage) <= usage["ceilingUsd"]
    for layouts in claude["layout"].values():
        for layout in layouts.values():
            later = layout["turns"][1:]
            share = sum(r["cacheReadTokens"] for r in later) / sum(r["promptTokens"] for r in later)
            assert layout["cacheReadShareAfterFirst"] == round(share, 3)
    spent = sum(usage["costUsd"] for usage in runs)
    print(
        "ok   both receipts' tables recompute from their rows; inputs regenerate identically; "
        f"the Claude runs cost {spent:.2f} USD at list price"
    )


def main():
    shortening()
    spilling()
    layers_and_budget()
    compaction()
    overflow()
    measured_context()


if __name__ == "__main__":
    main()
