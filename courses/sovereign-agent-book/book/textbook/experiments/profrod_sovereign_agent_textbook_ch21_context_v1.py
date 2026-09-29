# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 21 experiment: what a model does with a long context, and what compaction keeps.

Five measurements, all on deterministic inputs, on local models through Ollama at temperature
zero, or on Claude through the Messages API with --provider anthropic:

1. depth: find one delivery among near-identical records, by context length and position;
2. compaction: answer questions about a long session after five ways of fitting it in a budget;
3. truncation: answer questions about a 480-line sales log sent whole, cut, or digested;
4. layout: prefill per turn when volatile state sits before or after the stable prompt;
5. estimate: how far four characters per token is from the tokenizer's count, by kind of text.

Run from the course folder with Ollama serving the models:
    uv run python book/textbook/experiments/profrod_sovereign_agent_textbook_ch21_context_v1.py \\
        --out docs/evidence/book-ch21/ch21-context-receipt-v1.json

With --provider anthropic, the key is read from ANTHROPIC_API_KEY or the course folder's .env,
contexts run to 150,000 tokens, and the receipt records every token and its cost. The run stops
at --max-usd:
    uv run python book/textbook/experiments/profrod_sovereign_agent_textbook_ch21_context_v1.py \\
        --provider anthropic --max-usd 12 \\
        --out docs/evidence/book-ch21/ch21-context-claude-receipt-v1.json
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
CLAUDE = runpy.run_path(
    str(Path(__file__).with_name("profrod_sovereign_agent_claude_messages_v1.py"))
)
OLLAMA = "http://localhost:11434"
MODELS = ("qwen2.5:0.5b", "qwen2.5:1.5b", "qwen3:0.6b")
CLAUDE_MODELS = ("claude-haiku-4-5-20251001", "claude-sonnet-5-5")
# Set by main(): the provider, and the Claude connection that counts tokens and cost.
RUN: dict = {"provider": "ollama", "claude": None}
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


def claude_chat(model: str, messages: list[dict], predict: int, **extra) -> dict:
    """One Messages API call; `turns` replaces the converted conversation when a caller builds
    content blocks itself. promptTokens counts cached and uncached input alike."""
    system, turns = CLAUDE["to_claude"](messages)
    turns = extra.pop("turns", turns)
    if system:
        extra["system"] = system
    started = time.perf_counter()
    reply = RUN["claude"].messages(model, max_tokens=predict, messages=turns, **extra)
    usage = reply.get("usage", {})
    read = usage.get("cache_read_input_tokens") or 0
    written = usage.get("cache_creation_input_tokens") or 0
    return {
        "text": CLAUDE["text_of"](reply).strip(),
        "promptTokens": usage.get("input_tokens", 0) + read + written,
        "cacheReadTokens": read,
        "cacheWriteTokens": written,
        "wallMs": round((time.perf_counter() - started) * 1000, 1),
        "prefillMs": None,
    }


def chat(model: str, messages: list[dict], predict: int = 64, num_ctx: int = NUM_CTX) -> dict:
    if RUN["provider"] == "anthropic":
        return claude_chat(model, messages, predict)
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
    if RUN["provider"] == "anthropic":
        return  # the API caches only what a request marks, and reports what it read
    post("/api/generate", {"model": model, "keep_alive": 0})
    chat(model, [{"role": "user", "content": "hi"}], predict=1)


def count_tokens(model: str, text: str) -> int:
    """The model's own tokenizer count for raw text (no chat template)."""
    if RUN["provider"] == "anthropic":
        # The counting endpoint counts a whole request; subtract a one-token message's overhead.
        count = RUN["claude"].count_tokens
        base = count(model, messages=[{"role": "user", "content": "."}]) - 1
        return count(model, messages=[{"role": "user", "content": text}]) - base
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
CLAUDE_LENGTHS = (1000, 16000, 64000, 150000)
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
        if RUN["provider"] == "anthropic":
            # The log is the same for all eight questions: cache it once, then read it.
            log_block = {
                "type": "text",
                "text": f"Delivery log:\n{log}",
                "cache_control": {"type": "ephemeral"},
            }
            asked = {"type": "text", "text": f"\n\n{question}"}
            turn = {"role": "user", "content": [log_block, asked]}
            reply = claude_chat(model, [{"role": "system", "content": SYSTEM}], 40, turns=[turn])
        else:
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
    claude = RUN["provider"] == "anthropic"
    if claude:
        # Longer logs need more deliveries; the first 2,400 stay the same, and no order repeats.
        seen = {d["order"] for d in pool}
        more = deliveries(random.Random(SEED + 9), 9000)
        pool += [d for d in more if d["order"] not in seen]
    targets, filler_pool = pool[:8], pool[8:]
    sample = "\n".join(json.dumps(d, separators=(",", ":")) for d in filler_pool[:200])
    tokens_per_line = count_tokens(model, sample) / 200
    rows = []
    for length in RUN.get("lengths") or (CLAUDE_LENGTHS if claude else LENGTHS):
        lines = round(length / tokens_per_line)
        for depth in DEPTHS:
            log = haystack(filler_pool, targets, lines, depth)
            for row in ask_orders(model, log, targets):
                rows.append({"length": length, "depth": depth, **row})
    if claude:
        return rows, {
            "tokensPerLine": round(tokens_per_line, 2),
            "poolSize": len(pool),
            "overflow": claude_overflow(model, filler_pool, targets, tokens_per_line),
        }
    # One deliberate overflow: a 16,000-token log sent with an 8,192-token window.
    log = haystack(filler_pool, targets, round(16000 / tokens_per_line), 0.0)
    overflow = {
        "numCtx": OVERFLOW_CTX,
        "intendedTokens": 16000,
        "estimatedTokens": CTX["estimate_tokens"](log),
        "rows": ask_orders(model, log, targets, num_ctx=OVERFLOW_CTX),
    }
    return rows, {"tokensPerLine": round(tokens_per_line, 2), "overflow": overflow}


def claude_overflow(model: str, pool: list[dict], targets: list[dict], per_line: float) -> dict:
    """Send a log larger than the model's window, and record what the API does with it."""
    window = CLAUDE["WINDOW"][model]
    lines = round(window * 1.05 / per_line)
    if lines > len(pool) + len(targets):
        return {"window": window, "skipped": f"the pool holds too few deliveries for {window:,}"}
    log = haystack(pool, targets, lines, 0.0)
    counted = count_tokens(model, f"Delivery log:\n{log}")
    record = {"window": window, "countedTokens": counted}
    if counted <= window:
        return {**record, "skipped": "the log fits the window; nothing was sent"}
    question = f"How many tubs arrived with order {targets[0]['order']}?"
    try:
        asked = f"Delivery log:\n{log}\n\n{question}"
        reply = chat(model, [{"role": "user", "content": asked}], 40)
        return {**record, "error": None, "answer": reply["text"][:80]}
    except RuntimeError as error:
        return {**record, "error": str(error)[:200]}


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

def stable_rules(count: int) -> str:
    return "\n".join(
        ["You are the assistant for Lucy's ice cream shop. Follow these rules exactly."]
        + [
            f"Rule {i}: " + "Prices are in USD cents; round nothing; confirm every order with Lucy "
            "before it is placed, and never order from a supplier she has ruled out."
            for i in range(count)
        ]
    )


STABLE = stable_rules(40)
# Claude caches a prefix only from 4,096 tokens on Haiku 4.5, so its run carries more rules.
CLAUDE_STABLE = stable_rules(160)


def layout_experiment(model: str) -> dict:
    rng = random.Random(SEED + 3)
    snapshots = [
        f"Current time 10:{turn:02d}. Freezer: "
        + ", ".join(f"{f} {rng.randint(0, 40)}" for f in FLAVORS)
        + "."
        for turn in range(10)
    ]
    asks = [f"Question {turn}: is any flavor below 5 tubs?" for turn in range(10)]
    claude = RUN["provider"] == "anthropic"
    stable = CLAUDE_STABLE if claude else STABLE
    out = {}
    for layout in ("volatile-first", "stable-first"):
        cold(model)
        history: list[dict] = []
        rows = []
        for turn in range(10):
            if layout == "volatile-first":
                messages = [
                    {"role": "system", "content": snapshots[turn] + "\n\n" + stable},
                    *history,
                    {"role": "user", "content": asks[turn]},
                ]
            else:
                messages = [
                    {"role": "system", "content": stable},
                    *history,
                    {"role": "user", "content": snapshots[turn] + "\n" + asks[turn]},
                ]
            if claude:
                # A top-level breakpoint caches the whole request, so the next turn can read it.
                reply = claude_chat(model, messages, 1, cache_control={"type": "ephemeral"})
                row = {
                    "turn": turn,
                    "promptTokens": reply["promptTokens"],
                    "cacheReadTokens": reply["cacheReadTokens"],
                    "cacheWriteTokens": reply["cacheWriteTokens"],
                    "wallMs": reply["wallMs"],
                }
            else:
                reply = chat(model, messages, predict=1)
                row = {
                    "turn": turn,
                    "promptTokens": reply["promptTokens"],
                    "prefillMs": reply["prefillMs"],
                }
            rows.append(row)
            history += [
                {"role": "user", "content": messages[-1]["content"]},
                {"role": "assistant", "content": "Checked."},
            ]
        if claude:
            out[layout] = {
                "turns": rows,
                "cacheReadShareAfterFirst": round(
                    sum(r["cacheReadTokens"] for r in rows[1:])
                    / sum(r["promptTokens"] for r in rows[1:]),
                    3,
                ),
                "medianWallMsAfterFirst": statistics.median(r["wallMs"] for r in rows[1:]),
            }
        else:
            out[layout] = {
                "turns": rows,
                "medianPrefillMsAfterFirst": statistics.median(r["prefillMs"] for r in rows[1:]),
            }
    return out


# ---------------------------------------------------------------- 5. the estimate


def estimate_experiment(model: str = "qwen2.5:1.5b") -> list[dict]:
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
        actual = count_tokens(model, sample)
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


def depth_table(depth: dict) -> list[dict]:
    table = []
    for model, rows in depth.items():
        for length in sorted({r["length"] for r in rows}):
            for depth_at in DEPTHS:
                picked = [r for r in rows if r["length"] == length and r["depth"] == depth_at]
                table.append(
                    {
                        "model": model,
                        "length": length,
                        "depth": depth_at,
                        "n": len(picked),
                        "correct": sum(r["correct"] for r in picked),
                        "medianPromptTokens": statistics.median(
                            r["promptTokens"] or 0 for r in picked
                        ),
                    }
                )
    return table


def merged(base: dict, run: dict, args) -> dict:
    """The earlier receipt plus this run: new depth lengths join the old rows, other measurements
    this run made replace the old ones, and the run itself is listed with its own usage."""
    for model, rows in run["depth"].items():
        lengths = {r["length"] for r in rows}
        kept = [r for r in base["depth"].get(model, []) if r["length"] not in lengths]
        base["depth"][model] = sorted([*kept, *rows], key=lambda r: (r["length"], r["depth"]))
        base["depthMeta"].setdefault(model, run["depthMeta"][model])
    for part in ("compaction", "truncation", "layout"):
        base[part] |= run[part]
    if "estimate" in run:
        base["estimate"] = run["estimate"]
    base.setdefault("additionalRuns", []).append(
        {
            "created": run["created"],
            "models": run["models"],
            "only": args.only,
            "lengths": args.lengths,
        }
    )
    return base


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--models", nargs="*")
    parser.add_argument("--provider", choices=("ollama", "anthropic"), default="ollama")
    parser.add_argument("--max-usd", type=float, default=12.0, help="Claude spending ceiling")
    parser.add_argument(
        "--only",
        nargs="*",
        default=["depth", "compaction", "truncation", "layout", "estimate"],
        help="run only these measurements",
    )
    parser.add_argument("--lengths", nargs="*", type=int, help="override the depth lengths")
    parser.add_argument(
        "--merge",
        action="store_true",
        help="add this run's measurements to the receipt at --out, recording the run separately",
    )
    args = parser.parse_args()
    claude = args.provider == "anthropic"
    RUN.update(provider=args.provider, lengths=args.lengths)
    if claude:
        RUN["claude"] = CLAUDE["Claude"](max_usd=args.max_usd)
    models = args.models or list(CLAUDE_MODELS if claude else MODELS)
    receipt: dict = {
        "schemaVersion": 1,
        "chapter": 21,
        "created": time.strftime("%Y-%m-%d"),
        "python": platform.python_version(),
        "provider": args.provider,
        "models": models,
        "seed": SEED,
    }
    if claude:
        receipt |= {
            "api": f"Messages API, anthropic-version {CLAUDE['VERSION']}",
            "settings": {m: CLAUDE["SETTINGS"][m] for m in models},
            "windows": {m: CLAUDE["WINDOW"][m] for m in models},
            "caching": "the depth log and the layout request are marked for caching; "
            "the receipt records the tokens read from and written to the cache",
        }
    else:
        receipt |= {
            "ollama": ollama_version(),
            "temperature": 0,
            "numCtx": NUM_CTX,
            "coldStart": "each model is unloaded, then loaded once, before each measurement",
        }
    receipt |= {
        "depth": {},
        "depthMeta": {},
        "compaction": {},
        "truncation": {},
        "layout": {},
    }
    spent = lambda: f" ({RUN['claude'].cost():.2f} USD so far)" if claude else ""  # noqa: E731
    for model in models:
        if "depth" in args.only:
            cold(model)
            receipt["depth"][model], receipt["depthMeta"][model] = depth_experiment(model)
            print(model, "depth done" + spent(), flush=True)
        if "compaction" in args.only:
            cold(model)
            receipt["compaction"][model] = compaction_experiment(model)
            print(model, "compaction done" + spent(), flush=True)
        if "truncation" in args.only:
            cold(model)
            receipt["truncation"][model] = truncation_experiment(model)
            print(model, "truncation done" + spent(), flush=True)
        if "layout" in args.only:
            receipt["layout"][model] = layout_experiment(model)
            print(model, "layout done" + spent(), flush=True)
    if "estimate" in args.only:
        if claude:
            receipt["estimate"] = {m: estimate_experiment(m) for m in models}
        else:
            receipt["estimate"] = estimate_experiment()
    if args.merge:
        receipt = merged(json.loads(Path(args.out).read_text()), receipt, args)
    receipt["depthTable"] = depth_table(receipt["depth"])
    receipt["limits"] = [
        "Small local models at temperature zero; larger models hold longer contexts better, but "
        "the ways a context is shortened behave the same way for any model.",
        "Eight questions per depth cell and ten per compaction strategy: read differences as "
        "patterns across cells, not as single-cell results.",
    ]
    if claude:
        receipt["limits"] = [
            "Two Claude models through the API. Haiku 4.5 ran at temperature 0; Sonnet 5.5 "
            "accepts no temperature setting, so a rerun can differ by a question in a cell.",
            "Eight questions per depth cell and ten per compaction strategy: read differences as "
            "patterns across cells, not as single-cell results.",
            "Wall-clock times include the network and the API's queue; the cache token counts "
            "are what the layout measurement compares.",
        ]
        if args.merge:
            receipt["additionalRuns"][-1]["usage"] = RUN["claude"].report()
        else:
            receipt["usage"] = RUN["claude"].report()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(receipt, indent=1) + "\n")
    print("wrote", args.out, spent(), file=sys.stderr)


if __name__ == "__main__":
    main()
