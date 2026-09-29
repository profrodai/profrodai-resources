# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 2: typed shop tools over the same in-memory fixture.

Everything here is the learner's own: the tool call, the dispatcher and the shop tools come from
the Chapter 2 learner file, and the checkpoint checks them.
"""

import json
import math
import random
import runpy
from pathlib import Path

BOOK = Path(__file__).resolve().parents[1]
SHOP = runpy.run_path(
    str(Path(__file__).with_name("profrod_sovereign_agent_ch01_first_model_call_checkpoint.py"))
)["SHOP"]
LEARNER = runpy.run_path(
    str(BOOK / "learner/profrod_sovereign_agent_ch02_pydantic_shop_tools_learner.py")
)
ToolCall, build_tools = LEARNER["ToolCall"], LEARNER["build_tools"]
DECODE = runpy.run_path(
    str(BOOK / "learner/profrod_sovereign_agent_ch02_constrained_decoding_learner.py")
)


def refusals():
    """The learner's dispatcher refuses before a handler runs, and bounds what it returns."""
    tool, dispatcher = LEARNER["ExecutableTool"], LEARNER["Dispatcher"]
    ran = []

    def write(args):
        ran.append(args)
        return {"written": True}

    def huge(_):
        return "x" * 1000

    empty = LEARNER["NoArguments"]
    tools = [
        tool("write_order", "Consequential.", empty, write, consequential=True),
        tool("huge", "Returns too much.", empty, huge),
    ]
    guarded = dispatcher(tools, allowed=frozenset({"write_order", "huge"}), max_result_bytes=128)
    call = lambda name, arguments: guarded.invoke(ToolCall(id="c", name=name, arguments=arguments))  # noqa: E731
    assert call("write_order", {})["error"] == "write_authority_required" and not ran
    assert call("delete_all", {})["error"] == "tool_not_allowed"
    assert call("huge", {"extra": 1})["error"] == "invalid_arguments"
    assert call("huge", {})["error"] == "result_too_large"
    shop = build_tools(SHOP)
    for arguments in ({"sku": "SKU-VANILLA", "quantity": "6"}, {"sku": "SKU-VANILLA"}):
        assert shop.invoke(ToolCall(id="d", name="draft_order", arguments=arguments)) == {
            "ok": False,
            "error": "invalid_arguments",
        }
    wrong = ToolCall(id="d", name="draft_order", arguments={"sku": "SKU-VANILLA", "quantity": 5})
    assert shop.invoke(wrong) == {"ok": False, "error": "tool_failed"}
    print("ok   refused: missing authority, unknown tool, bad arguments, oversized result")


def structured():
    """Part A's decoding functions, each checked against an independent computation."""
    assert math.isclose(DECODE["stays_valid"](0.01, 100), 0.99**100)
    logits = [2.0, 1.0, 0.5, -1.0]
    full = DECODE["softmax"](logits)
    kept = DECODE["softmax"](DECODE["mask"](logits, {1, 3}))
    assert kept[0] == kept[2] == 0.0
    assert math.isclose(kept[1], full[1] / (full[1] + full[3]))
    print("ok   masking renormalizes the allowed tokens and zeroes the rest")

    lab = runpy.run_path(
        str(BOOK / "experiments/profrod_sovereign_agent_textbook_ch02_structured_v1.py")
    )
    toy, valid = lab["TOY"], lab["VALID"]
    rng = random.Random(2)

    def viable(prefix, token):
        if token == lab["END"]:
            return prefix in valid
        return any(v[: len(prefix) + 1] == prefix + (token,) for v in valid)

    def draw(allowed=None):
        prefix = ()
        while True:
            options = [
                (t, p) for t, p in toy[prefix].items() if allowed is None or allowed(prefix, t)
            ]
            tokens, weights = zip(*options, strict=True)
            token = rng.choices(tokens, weights)[0]
            if token == lab["END"]:
                return prefix
            prefix = prefix + (token,)

    kept_samples = [s for s in (draw() for _ in range(200_000)) if s in valid]
    rejection = sum(s == ("a", "y") for s in kept_samples) / len(kept_samples)
    masked_draws = [draw(allowed=viable) for _ in range(20_000)]
    masking = sum(s == ("a", "y") for s in masked_draws) / len(masked_draws)
    comparison = lab["toy_comparison"]()
    assert abs(rejection - comparison["conditioned"]["ay"]) < 0.01
    assert abs(masking - comparison["masked"]["ay"]) < 0.01
    print(f"ok   rejection sampling gives P(ay) {rejection:.3f}; masked sampling {masking:.3f}")


def main():
    structured()
    refusals()
    tools = build_tools(SHOP)
    stock = tools.invoke(ToolCall(id="stock", name="list_stock", arguments={}))
    print([(row["sku"], row["needed"]) for row in stock["value"]])
    good = tools.invoke(
        ToolCall(id="draft", name="draft_order", arguments={"sku": "SKU-VANILLA", "quantity": 6})
    )
    print(json.dumps(good, sort_keys=True))
    bad = tools.invoke(
        ToolCall(id="bad", name="draft_order", arguments={"sku": "SKU-VANILLA", "quantity": True})
    )
    print(json.dumps(bad, sort_keys=True))


if __name__ == "__main__":
    main()
