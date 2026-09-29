# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 3: the reliability arithmetic, then the owned loop with replayable responses or a live
local model."""

import argparse
import json
import math
import random
import runpy
from pathlib import Path

LEARNER = runpy.run_path(
    str(
        Path(__file__).resolve().parents[1]
        / "learner/profrod_sovereign_agent_ch03_agent_loop_learner.py"
    )
)
Limits, run_loop = LEARNER["Limits"], LEARNER["run_loop"]
HTTPModel, ModelError = LEARNER["HTTPModel"], LEARNER["ModelError"]
ModelTurn, ToolCall = LEARNER["ModelTurn"], LEARNER["ToolCall"]

SHOP_TOOLS = LEARNER["shop_tools"]
MESSAGES = [
    {
        "role": "system",
        "content": "Help Lucy prepare replenishment drafts. First call list_stock. "
        "For each product with needed > 0, call draft_order with exactly that quantity. "
        "Do not draft products with needed = 0. Summarize the tool results in USD cents. "
        "A verbal recommendation does not replace creating the draft through the tool. "
        "Drafts are proposals, never purchases.",
    },
    {
        "role": "user",
        "content": "Prepare replenishment drafts from current stock. State USD amounts.",
    },
]


class ReplayModel:
    """Authored responses test control flow; they do not test model decisions."""

    def __init__(self, turns):
        self.turns = iter(turns)

    def complete(self, messages, tools, *, timeout, max_output_tokens):
        try:
            return next(self.turns)
        except StopIteration:
            raise ModelError("response fixture exhausted") from None


def opening_turns():
    return [
        ModelTurn(calls=(ToolCall(id="stock-1", name="list_stock", arguments={}),)),
        ModelTurn(
            calls=(
                ToolCall(
                    id="draft-v",
                    name="draft_order",
                    arguments={"sku": "SKU-VANILLA", "quantity": 6},
                ),
                ToolCall(
                    id="draft-s",
                    name="draft_order",
                    arguments={"sku": "SKU-STRAWBERRY", "quantity": 4},
                ),
            ),
        ),
        ModelTurn("Drafts: vanilla 6 tubs, strawberry 4 tubs; total 2600 cents USD. No purchase."),
    ]


def draft_evidence(result):
    """Authored answers for this fixture; not a general explanation evaluator."""
    names = {
        call["id"]: call["function"]["name"]
        for message in result.messages
        for call in message.get("tool_calls", [])
    }
    observed = []
    for message in result.messages:
        if message["role"] != "tool":
            continue
        value = json.loads(message["content"])
        if value.get("ok") is not True:
            return False
        if names.get(message["tool_call_id"]) == "draft_order":
            draft = value["value"]
            observed.append(
                (draft["sku"], draft["quantity"], draft["total_cents"], draft["currency"])
            )
    return sorted(observed) == [
        ("SKU-STRAWBERRY", 4, 1100, "USD"),
        ("SKU-VANILLA", 6, 1500, "USD"),
    ]


def reliability():
    """The chapter's formulas, checked against the processes they describe."""
    chain, recovery = LEARNER["chain_success"], LEARNER["success_with_recovery"]
    retry, within = LEARNER["retry_success"], LEARNER["finish_within"]
    assert math.isclose(chain(0.95, 20), 0.95**20) and round(chain(0.95, 20), 3) == 0.358
    half_life = math.log(2) / -math.log(0.95)
    assert 13 < half_life < 14 and math.isclose(chain(0.95, half_life), 0.5)
    print("ok   p ** n, and a half-life of about 0.69 / (1 - p) steps")

    for p, r in ((0.95, 0.0), (0.95, 0.3), (0.8, 0.6)):
        on_track = 1.0
        for n in range(1, 41):
            on_track = r + (p - r) * on_track
            assert math.isclose(recovery(p, r, n), on_track)
    assert math.isclose(recovery(0.95, 0.0, 50), chain(0.95, 50))
    print("ok   the recovery formula equals iterating the two-state chain")

    rng = random.Random(5)
    hard, q, tasks = 0.3, 0.6, 20_000
    solved = [0] * 4
    for _ in range(tasks):
        is_hard = rng.random() < hard
        first = next((k for k in range(4) if not is_hard and rng.random() < q), None)
        for k in range(4):
            solved[k] += first is not None and first <= k
    for k in range(4):
        assert abs(solved[k] / tasks - retry(q, k + 1, hard)) < 0.015
    print("ok   simulated retries plateau at 1 - hard, as derived")

    needed = math.ceil(math.log(0.01) / math.log(1 - 0.3))
    assert within(needed, 0.3) >= 0.99 > within(needed - 1, 0.3)
    print("ok   the budget formula gives the smallest budget reaching 99%")


class CountingTools:
    """The shop's dispatcher, counting what the loop actually invokes."""

    def __init__(self):
        self.inner = SHOP_TOOLS["build_tools"](SHOP_TOOLS["SHOP"])
        self.invoked = []

    def schemas(self):
        return self.inner.schemas()

    def invoke(self, call):
        self.invoked.append(call.id)
        return self.inner.invoke(call)


def boundaries():
    """The loop's limits, each checked against the learner's run_loop with authored turns."""

    def run(turns, **limits):
        tools = CountingTools()
        return run_loop(ReplayModel(turns), tools, MESSAGES, limits=Limits(**limits)), tools

    stock = ToolCall(id="stock-1", name="list_stock", arguments={})
    before = json.dumps(MESSAGES)

    # A reply that arrives after the deadline is discarded, and none of its calls run.
    now = [0.0]

    class LateModel:
        def complete(self, messages, tools, *, timeout, max_output_tokens):
            messages.append({"role": "user", "content": "the model edits its copy"})
            now[0] += 61
            return ModelTurn(calls=(stock,))

    tools = CountingTools()
    late = run_loop(LateModel(), tools, MESSAGES, limits=Limits(), clock=lambda: now[0])
    assert late.status == "TIME_LIMIT" and tools.invoked == [] and len(late.messages) == 2

    again = ModelTurn(calls=(stock,))
    result, tools = run([ModelTurn(calls=(stock,)), again])
    assert result.status == "REPEATED_CALL_ID" and tools.invoked == ["stock-1"]
    result, tools = run([ModelTurn(calls=(stock, stock))])
    assert result.status == "REPEATED_CALL_ID" and tools.invoked == []

    # A five-cent budget admits one three-cent call, then refuses the next before sending it.
    second = ToolCall(id="stock-2", name="list_stock", arguments={})
    turns = [ModelTurn(calls=(stock,)), ModelTurn(calls=(second,))]
    result, _ = run(turns, estimated_call_cents=3, model_budget_cents=5)
    assert result.status == "MODEL_COST_LIMIT" and result.model_calls == 1

    three = tuple(ToolCall(id=f"s{i}", name="list_stock", arguments={}) for i in range(3))
    result, tools = run([ModelTurn(calls=three)], tool_calls=2)
    assert result.status == "TOOL_LIMIT" and tools.invoked == []

    result, _ = run([ModelTurn(content="done", output_tokens=2_000)])
    assert result.status == "INVALID_USAGE"
    result, _ = run([ModelTurn(content="   ")])
    assert result.status == "EMPTY_REPLY"
    result, _ = run([])
    assert result.status == "MODEL_FAILED"
    result, _ = run([ModelTurn(calls=(stock,))] * 3, model_calls=1)
    assert result.status == "MODEL_CALL_LIMIT"
    assert json.dumps(MESSAGES) == before, "the loop changed the caller's messages"
    print(
        "ok   boundaries: late reply, repeated ids, cost and tool limits before sending, "
        "bad usage, empty reply, model failure, call limit; caller's messages unchanged"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--model", default="qwen3")
    parser.add_argument("--transcript", action="store_true")
    args = parser.parse_args()
    reliability()
    boundaries()
    model = HTTPModel(model=args.model) if args.live else ReplayModel(opening_turns())
    dispatcher = SHOP_TOOLS["build_tools"](SHOP_TOOLS["SHOP"])
    result = run_loop(model, dispatcher, MESSAGES, limits=Limits())
    print(result.status, result.model_calls, result.tool_calls)
    print(result.answer)
    passed = draft_evidence(result)
    print("draft evidence", "PASS" if passed else "FAIL")
    if args.transcript:
        print(json.dumps(result.messages, indent=2))
    return 0 if result.status == "COMPLETED" and passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
