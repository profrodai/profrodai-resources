# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 21 experiment: what a model does with a long context, and what compaction keeps.

Five measurements on local models through Ollama, all deterministic inputs at temperature zero:

1. depth: find one delivery among near-identical records, by context length and position;
2. compaction: answer questions about a long session after five ways of fitting it in a budget;
3. truncation: answer questions about a 480-line sales log sent whole, cut, or digested;
4. layout: prefill per turn when volatile state sits before or after the stable prompt;
5. estimate: how far four characters per token is from the tokenizer's count, by kind of text.

Run from the course folder with Ollama serving the models:
    uv run python book/textbook/experiments/profrod_sovereign_agent_textbook_ch21_context_v1.py \\
        --out docs/evidence/book-ch21/ch21-context-receipt-v1.json
"""

from __future__ import annotations

import argparse
import json
import platform
import random
import re
import runpy
import statistics
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[3]
LEARNER = ROOT / "book/textbook/learner"
CTX = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch21_context_learner.py"))
STATS = runpy.run_path(
    str(LEARNER / "profrod_sovereign_agent_ch16_evaluation_statistics_learner.py")
)
OLLAMA = "http://localhost:11434"
MODELS = ("qwen2.5:0.5b", "qwen2.5:1.5b", "qwen3:0.6b")
SEED = 7
NUM_CTX = 32768
OVERFLOW_CTX = 8192
FLAVORS = (
    "vanilla chocolate strawberry pistachio mango mint coffee caramel "
    "lemon raspberry hazelnut coconut"
).split()


def post(path: str, payload: dict) -> dict:
    request = Request(
        f"{OLLAMA}{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=900) as response:
        return json.loads(response.read())


def chat(model: str, messages: list[dict], predict: int = 64, num_ctx: int = NUM_CTX) -> dict:
    reply = post(
        "/api/chat",
        {
            "model": model,
            "messages": messages,
            "stream": False,
            "think": False,
            "options": {"temperature": 0, "seed": SEED, "num_ctx": num_ctx, "num_predict": predict},
        },
    )
    return {
        "text": reply.get("message", {}).get("content", "").strip(),
        "promptTokens": reply.get("prompt_eval_count"),
        "prefillMs": round(reply.get("prompt_eval_duration", 0) / 1e6, 1),
    }


def ollama_version() -> str:
    with urlopen(f"{OLLAMA}/api/version", timeout=30) as response:
        return json.loads(response.read()).get("version", "")


def cold(model: str) -> None:
    """Unload the model, then load it once, so no prompt is served from an earlier run's cache."""
    post("/api/generate", {"model": model, "keep_alive": 0})
    chat(model, [{"role": "user", "content": "hi"}], predict=1)


def count_tokens(model: str, text: str) -> int:
    """The model's own tokenizer count for raw text (no chat template)."""
    reply = post(
        "/api/generate",
        {
            "model": model,
            "prompt": text,
            "raw": True,
            "stream": False,
            "options": {"num_predict": 1, "num_ctx": NUM_CTX},
        },
    )
    return reply["prompt_eval_count"]


def first_int(text: str) -> int | None:
    """The first whole number in a reply, ignoring order ids such as A-6305 that it may echo."""
    match = re.search(r"\d+", re.sub(r"[A-Z]-\d+", "", text.replace(",", "")))
    return int(match.group()) if match else None


def wilson(correct: int, n: int) -> list[float]:
    low, high = STATS["wilson_interval"](correct, n)
    return [round(low, 3), round(high, 3)]


# ---------------------------------------------------------------- 1. depth and length

LENGTHS = (1000, 4000, 8000, 16000)
DEPTHS = (0.0, 0.25, 0.5, 0.75, 1.0)
SYSTEM = "You are the assistant for Lucy's ice cream shop. Answer with the number only."


def deliveries(rng: random.Random, count: int) -> list[dict]:
    ids = rng.sample(range(1000, 10000), count)
    return [
        {
            "tool": "record_delivery",
            "order": f"A-{order}",
            "flavor": rng.choice(FLAVORS),
            "tubs": rng.randint(4, 40),
            "at": f"{rng.randint(7, 18):02d}:{rng.randint(0, 59):02d}",
        }
        for order in ids
    ]


def haystack(filler_pool: list[dict], targets: list[dict], lines: int, depth: float) -> str:
    line = lambda d: json.dumps(d, separators=(",", ":"))  # noqa: E731
    filler = [line(d) for d in filler_pool[: max(lines - len(targets), 0)]]
    return "\n".join(CTX["place_at_depth"](filler, [line(t) for t in targets], depth))


def ask_orders(model: str, log: str, targets: list[dict], num_ctx: int = NUM_CTX) -> list[dict]:
    rows = []
    for target in targets:
        question = f"How many tubs arrived with order {target['order']}?"
        reply = chat(
            model,
            [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"Delivery log:\n{log}\n\n{question}"},
            ],
            predict=40,
            num_ctx=num_ctx,
        )
        rows.append(
            {
                "order": target["order"],
                "expected": target["tubs"],
                "answer": reply["text"][:40],
                "correct": first_int(reply["text"]) == target["tubs"],
                "promptTokens": reply["promptTokens"],
            }
        )
    return rows


def depth_experiment(model: str) -> tuple[list[dict], dict]:
    """Accuracy by length and depth, with lengths set by the model's own token count."""
    rng = random.Random(SEED)
    pool = deliveries(rng, 2400)
    targets, filler_pool = pool[:8], pool[8:]
    sample = "\n".join(json.dumps(d, separators=(",", ":")) for d in filler_pool[:200])
    tokens_per_line = count_tokens(model, sample) / 200
    rows = []
    for length in LENGTHS:
        lines = round(length / tokens_per_line)
        for depth in DEPTHS:
            log = haystack(filler_pool, targets, lines, depth)
            for row in ask_orders(model, log, targets):
                rows.append({"length": length, "depth": depth, **row})
    # One deliberate overflow: a 16,000-token log sent with an 8,192-token window.
    log = haystack(filler_pool, targets, round(16000 / tokens_per_line), 0.0)
    overflow = {
        "numCtx": OVERFLOW_CTX,
        "intendedTokens": 16000,
        "estimatedTokens": CTX["estimate_tokens"](log),
        "rows": ask_orders(model, log, targets, num_ctx=OVERFLOW_CTX),
    }
    return rows, {"tokensPerLine": round(tokens_per_line, 2), "overflow": overflow}


# ---------------------------------------------------------------- 2. compaction

BUDGETS = (1500, 600)
QUESTIONS = [
    ("What is the shop called?", "lucy's scoops", "pinned-note"),
    ("Which flavor must never be ordered from Frostline?", "mango", "pinned-note"),
    ("What time does the shop close today? Give the hour only.", 7, "superseded"),
    ("How many tubs of chocolate has Lucy approved? Number only.", 15, "superseded"),
    ("Which supplier do we order vanilla from now?", "polar dairy", "pinned-note"),
    ("How many tubs arrived with order A-4817? Number only.", 20, "old-tool-result"),
    (
        "How many tubs of strawberry were in the freezer at the last check? Number only.",
        7,
        "old-tool-result",
    ),
    ("What is the health inspector's name?", "ortiz", "pinned-note"),
    ("Where should the sign-up sheet go?", "till", "recent"),
    ("How many tubs of mango have sold today? Number only.", 11, "recent-tool-result"),
]
PINNED = [
    "The shop is Lucy's Scoops.",
    "Never order mango from Frostline.",
    "Today the shop closes at 7 pm (changed from 6 pm).",
    "Approved: 15 tubs of chocolate from Frostline (changed from 12).",
    "Vanilla is ordered from Polar Dairy.",
    "The health inspector is Dana Ortiz.",
]


def session() -> list[dict]:
    """A long day of Lucy's: decisions early, some changed later, bulky tool results between."""
    rng = random.Random(SEED + 1)
    tool = CTX["tool_message"]

    # The bulk tables leave out strawberry and mango, so each of those questions has one answer.
    others = [f for f in FLAVORS if f not in ("strawberry", "mango")]

    def stock_table() -> dict:
        return {"tool": "stock_level", "freezer": {f: rng.randint(0, 40) for f in others}}

    def sales(n: int) -> dict:
        return {
            "tool": "sales_today",
            "rows": [
                {
                    "at": f"{rng.randint(10, 17):02d}:{rng.randint(0, 59):02d}",
                    "flavor": rng.choice(others),
                    "tubs": rng.randint(1, 3),
                }
                for _ in range(n)
            ],
        }

    said = [
        "Good morning. For the record, my name is Lucy and the shop is Lucy's Scoops.",
        "Never order mango from Frostline again; they were late twice.",
        "We close at 6 pm today.",
        "Check the whole freezer, please.",
        "Approve 12 tubs of chocolate from Frostline.",
        "What sold this morning?",
        "From now on, order vanilla from Polar Dairy.",
        "Record the delivery that just came in.",
        "Check the freezer again.",
        "What have we sold so far?",
        "Make that 15 tubs of chocolate instead of 12.",
        "Check the freezer.",
        "How much strawberry is left?",
        "Sales so far?",
        "The health inspector coming Friday is Dana Ortiz.",
        "Check the freezer.",
        "Sales update, please.",
        "Change of plan: we close at 7 pm today.",
        "Check the freezer.",
        "Put the sign-up sheet by the till.",
        "Sales update.",
        "How much mango have we sold?",
    ]
    messages: list[dict] = []
    for i, text in enumerate(said):
        messages.append({"role": "user", "content": text})
        if "freezer" in text:
            messages.append(tool("stock_level", stock_table()))
            messages.append({"role": "assistant", "content": "Here is the freezer as it stands."})
        elif "strawberry" in text:
            messages.append(
                tool("stock_level", {"tool": "stock_level", "flavor": "strawberry", "tubs": 7})
            )
            messages.append({"role": "assistant", "content": "There are 7 tubs of strawberry."})
        elif "delivery" in text:
            messages.append(
                tool(
                    "record_delivery",
                    {
                        "tool": "record_delivery",
                        "order": "A-4817",
                        "flavor": "pistachio",
                        "tubs": 20,
                    },
                )
            )
            messages.append({"role": "assistant", "content": "Recorded."})
        elif "mango have we sold" in text:
            messages.append(
                tool("sales_today", {"tool": "sales_today", "flavor": "mango", "tubs": 11})
            )
            messages.append({"role": "assistant", "content": "Eleven tubs of mango so far."})
        elif "sold" in text or "ales" in text:
            messages.append(tool("sales_today", sales(40 + 5 * i)))
            messages.append({"role": "assistant", "content": "Those are today's sales so far."})
        else:
            messages.append({"role": "assistant", "content": "Noted."})
    return messages


def window(system: str, messages: list[dict], budget: int) -> list[dict]:
    """Keep the most recent messages that fit beside the system text."""
    used = CTX["estimate_tokens"](system)
    kept: list[dict] = []
    for message in reversed(messages):
        cost = CTX["message_tokens"](message)
        if used + cost > budget:
            break
        kept.insert(0, message)
        used += cost
    return kept


def as_chat(layers: dict) -> list[dict]:
    """Ollama's chat takes tool results as role "tool"; everything else passes through."""
    return [{"role": m["role"], "content": m["content"]} for m in layers]


def compaction_experiment(model: str) -> dict:
    base = session()
    system = "You are the assistant for Lucy's ice cream shop. Answer in a few words."
    full_tokens = CTX["budget_report"](CTX["Layers"](system, [], base))["total"]

    def summarize(older: list[dict]) -> str:
        text = "\n".join(f"{m['role']}: {m['content']}" for m in older)
        return chat(
            model,
            [
                {"role": "system", "content": "You compress conversations for later use."},
                {
                    "role": "user",
                    "content": (
                        "Summarize this conversation for yourself in at most 200 words. Keep every "
                        "rule, decision, name and number Lucy stated; where she changed something, "
                        f"keep only the latest value.\n\n{text}"
                    ),
                },
            ],
            predict=320,
        )["text"]

    def score(messages: list[dict]) -> dict:
        rows = []
        for question, expected, kind in QUESTIONS:
            reply = chat(
                model, [*as_chat(messages), {"role": "user", "content": question}], predict=40
            )
            if isinstance(expected, int):
                ok = first_int(reply["text"]) == expected
            else:
                ok = expected in reply["text"].lower()
            rows.append(
                {"question": question, "kind": kind, "answer": reply["text"][:80], "correct": ok}
            )
        right = sum(r["correct"] for r in rows)
        return {
            "estimatedTokens": sum(CTX["message_tokens"](m) for m in messages),
            "correct": right,
            "n": len(rows),
            "wilson95": wilson(right, len(rows)),
            "rows": rows,
        }

    cleared = CTX["clear_old_tool_results"](base, 1)
    pinned_system = CTX["Layers"](system, PINNED, []).messages()[0]["content"]
    results: dict = {"full": score([{"role": "system", "content": system}, *base])}
    sessions = {}
    for budget in BUDGETS:
        try:
            compacted, report = CTX["compact"](
                CTX["Layers"](system, [], base), budget, summarize, keep_tool_results=1
            )
            summary = next(
                (m["content"] for m in compacted.conversation if m["content"].startswith("Summ")),
                None,
            )
            summarized = compacted.messages()
        except CTX["ContextOverflowError"] as error:
            report, summary, summarized = {"overflow": str(error)}, None, None
        strategies = {
            "window": [{"role": "system", "content": system}, *window(system, base, budget)],
            "clear-then-window": [
                {"role": "system", "content": system},
                *window(system, cleared, budget),
            ],
            "clear-then-summary": summarized,
            "pinned-clear-window": [
                {"role": "system", "content": pinned_system},
                *window(pinned_system, cleared, budget),
            ],
        }
        results[str(budget)] = {
            name: score(messages) for name, messages in strategies.items() if messages
        }
        sessions[str(budget)] = {"compactReport": report, "summary": summary}
    results["_session"] = {"fullEstimatedTokens": full_tokens, "budgets": sessions}
    return results


# ---------------------------------------------------------------- 3. tool-result truncation

LIMIT = 1500


def sales_log() -> tuple[str, dict]:
    rng = random.Random(SEED + 2)
    minutes = sorted(rng.sample(range(10 * 60, 18 * 60), 480))
    rows = [
        (f"{m // 60:02d}:{m % 60:02d}", rng.choice(FLAVORS), rng.randint(1, 3)) for m in minutes
    ]
    text = "\n".join(f"{t} | {f} | {n} tubs | ${3.5 * n:.2f}" for t, f, n in rows)
    middle = rows[len(rows) // 2 + 7]
    truth = {
        "pistachio": sum(n for _, f, n in rows if f == "pistachio"),
        "first": rows[0][1],
        "last": rows[-1][1],
        "middle_time": middle[0],
        "middle": middle[1],
        "count": len(rows),
    }
    return text, truth


def digest(text: str) -> str:
    """What a program can compute from the whole output, instead of sending it."""
    rows = [line.split(" | ") for line in text.splitlines()]
    totals: dict[str, int] = {}
    for _, flavor, tubs, _ in rows:
        totals[flavor] = totals.get(flavor, 0) + int(tubs.split()[0])
    lines = [
        f"{len(rows)} sales. Tubs by flavor: "
        + ", ".join(f"{f} {n}" for f, n in sorted(totals.items()))
        + ".",
        f"First sale: {' | '.join(rows[0])}",
        f"Last sale: {' | '.join(rows[-1])}",
    ]
    return "\n".join(lines)


def truncation_experiment(model: str) -> dict:
    text, truth = sales_log()
    shown = {
        "full": text,
        "head": CTX["head"](text, LIMIT),
        "head-and-tail": CTX["head_and_tail"](text, LIMIT),
        "digest": digest(text),
    }
    questions = [
        ("How many tubs of pistachio were sold in total? Number only.", truth["pistachio"]),
        ("What flavor was the first sale of the day? One word.", truth["first"]),
        ("What flavor was the last sale of the day? One word.", truth["last"]),
        (f"What flavor was sold at {truth['middle_time']}? One word.", truth["middle"]),
        ("How many sales are in the log? Number only.", truth["count"]),
    ]
    results = {}
    for name, body in shown.items():
        rows = []
        for question, expected in questions:
            reply = chat(
                model,
                [
                    {
                        "role": "system",
                        "content": "You are the assistant for Lucy's ice cream shop. "
                        "Answer with one word or one number only.",
                    },
                    {
                        "role": "user",
                        "content": f"Today's sales log (from the sales_today tool):\n"
                        f"{body}\n\n{question}",
                    },
                ],
                predict=48,
            )
            ok = (
                first_int(reply["text"]) == expected
                if isinstance(expected, int)
                else expected in reply["text"].lower()
            )
            rows.append(
                {
                    "question": question,
                    "expected": expected,
                    "answer": reply["text"][:40],
                    "correct": ok,
                }
            )
        results[name] = {
            "estimatedTokens": CTX["estimate_tokens"](body),
            "correct": sum(r["correct"] for r in rows),
            "rows": rows,
        }
    results["_truth"] = truth
    return results


# ---------------------------------------------------------------- 4. layout and the prefix cache

STABLE = "\n".join(
    ["You are the assistant for Lucy's ice cream shop. Follow these rules exactly."]
    + [
        f"Rule {i}: " + "Prices are in USD cents; round nothing; confirm every order with Lucy "
        "before it is placed, and never order from a supplier she has ruled out."
        for i in range(40)
    ]
)


def layout_experiment(model: str) -> dict:
    rng = random.Random(SEED + 3)
    snapshots = [
        f"Current time 10:{turn:02d}. Freezer: "
        + ", ".join(f"{f} {rng.randint(0, 40)}" for f in FLAVORS)
        + "."
        for turn in range(10)
    ]
    asks = [f"Question {turn}: is any flavor below 5 tubs?" for turn in range(10)]
    out = {}
    for layout in ("volatile-first", "stable-first"):
        cold(model)
        history: list[dict] = []
        rows = []
        for turn in range(10):
            if layout == "volatile-first":
                messages = [
                    {"role": "system", "content": snapshots[turn] + "\n\n" + STABLE},
                    *history,
                    {"role": "user", "content": asks[turn]},
                ]
            else:
                messages = [
                    {"role": "system", "content": STABLE},
                    *history,
                    {"role": "user", "content": snapshots[turn] + "\n" + asks[turn]},
                ]
            reply = chat(model, messages, predict=1)
            rows.append(
                {
                    "turn": turn,
                    "promptTokens": reply["promptTokens"],
                    "prefillMs": reply["prefillMs"],
                }
            )
            history += [
                {"role": "user", "content": messages[-1]["content"]},
                {"role": "assistant", "content": "Checked."},
            ]
        out[layout] = {
            "turns": rows,
            "medianPrefillMsAfterFirst": statistics.median(r["prefillMs"] for r in rows[1:]),
        }
    return out


# ---------------------------------------------------------------- 5. the estimate


def estimate_experiment() -> list[dict]:
    text, _ = sales_log()
    samples = {
        "prose": " ".join(
            [
                "Lucy opens the shop at nine and checks the freezer before the first customer.",
                "She keeps a note of every delivery and every change a supplier makes.",
            ]
            * 12
        ),
        "json": "\n".join(
            json.dumps(d, separators=(",", ":")) for d in deliveries(random.Random(SEED), 30)
        ),
        "numbers": "\n".join(text.splitlines()[:60]),
        "python": (LEARNER / "profrod_sovereign_agent_ch21_context_learner.py").read_text()[:2400],
    }
    rows = []
    for kind, sample in samples.items():
        reply = post(
            "/api/generate",
            {
                "model": "qwen2.5:1.5b",
                "prompt": sample,
                "raw": True,
                "stream": False,
                "options": {"num_predict": 1, "num_ctx": NUM_CTX},
            },
        )
        actual = reply.get("prompt_eval_count")
        estimate = CTX["estimate_tokens"](sample)
        rows.append(
            {
                "kind": kind,
                "chars": len(sample),
                "estimate": estimate,
                "actual": actual,
                "charsPerToken": round(len(sample) / actual, 2),
                "estimateError": round(estimate / actual - 1, 3),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--models", nargs="*", default=list(MODELS))
    args = parser.parse_args()
    receipt: dict = {
        "schemaVersion": 1,
        "chapter": 21,
        "created": time.strftime("%Y-%m-%d"),
        "python": platform.python_version(),
        "ollama": ollama_version(),
        "models": args.models,
        "seed": SEED,
        "temperature": 0,
        "numCtx": NUM_CTX,
        "coldStart": "each model is unloaded, then loaded once, before each measurement",
        "depth": {},
        "depthMeta": {},
        "compaction": {},
        "truncation": {},
        "layout": {},
    }
    for model in args.models:
        cold(model)
        receipt["depth"][model], receipt["depthMeta"][model] = depth_experiment(model)
        print(model, "depth done", flush=True)
        cold(model)
        receipt["compaction"][model] = compaction_experiment(model)
        print(model, "compaction done", flush=True)
        cold(model)
        receipt["truncation"][model] = truncation_experiment(model)
        print(model, "truncation done", flush=True)
        receipt["layout"][model] = layout_experiment(model)
        print(model, "layout done", flush=True)
    receipt["estimate"] = estimate_experiment()
    table = []
    for model, rows in receipt["depth"].items():
        for length in LENGTHS:
            for depth in DEPTHS:
                picked = [r for r in rows if r["length"] == length and r["depth"] == depth]
                right = sum(r["correct"] for r in picked)
                table.append(
                    {
                        "model": model,
                        "length": length,
                        "depth": depth,
                        "n": len(picked),
                        "correct": right,
                        "medianPromptTokens": statistics.median(
                            r["promptTokens"] or 0 for r in picked
                        ),
                    }
                )
    receipt["depthTable"] = table
    receipt["limits"] = [
        "Small local models at temperature zero; larger models hold longer contexts better, but "
        "the ways a context is shortened behave the same way for any model.",
        "Eight questions per depth cell and ten per compaction strategy: read differences as "
        "patterns across cells, not as single-cell results.",
    ]
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(receipt, indent=1) + "\n")
    print("wrote", args.out, file=sys.stderr)


if __name__ == "__main__":
    main()
