# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 18 experiment: do parallel subagents pay on a local model, and how do their errors add?

  uv run python book/textbook/experiments/profrod_sovereign_agent_textbook_ch18_delegation_v1.py \
      --out ch18-delegation-receipt.json [--model qwen2.5:0.5b]

A real model (served by Ollama on localhost) answers Chapter 5's twelve direct questions about
Lucy's forty notes, each question as one "subagent" task with every note in context.
  - Parallelism: four subagent tasks run one after another, then all four at once, three times
    each; the receipt compares wall times with Amdahl's law.
  - Composition: every question is answered ten times at temperature 0.7. A composed task needs
    four subagents right at once; the receipt compares the measured joint success with the product
    of the four accuracies.
  - Voting: for each question, three samples vote; the receipt compares how often at least two of
    three are right with the independent-errors prediction.
Answers are graded by Chapter 5's whole-word grader.

On Claude, the same parts run against the Messages API, and two more measure Part B's worker:

  uv run python book/textbook/experiments/profrod_sovereign_agent_textbook_ch18_delegation_v1.py \
      --out ch18-delegation-claude-receipt.json \
      --models claude-haiku-4-5-20251001 claude-sonnet-5-5 --budget 5

  - Research: the learner's research_once runs each of 24 catering inquiries through Claude, on
    a fresh shop, and records whether the checked quote matched the function, the calls, tokens,
    cost and time, and whether the model's own sentence names the right total.
  - Schema: the first turn of each inquiry against a quote tool that takes no arguments, the
    schema that failed on a local model, counting calls that strict dispatch would refuse.
Haiku samples at temperature 0.7 as the local model does; Sonnet 5.5 takes no temperature, so its
samples use the API's default. Neither takes a seed.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import platform
import runpy
import statistics
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[3]
DELEGATE = runpy.run_path(
    str(ROOT / "book/textbook/learner/profrod_sovereign_agent_ch18_delegation_learner.py")
)
MEMORY = runpy.run_path(
    str(ROOT / "book/textbook/experiments/profrod_sovereign_agent_textbook_ch05_retrieval_v1.py")
)
CLAUDE = runpy.run_path(
    str(ROOT / "book/textbook/experiments/profrod_sovereign_agent_claude_messages_v1.py")
)
MODEL = "qwen2.5:0.5b"  # replaced by --model; the small model makes errors worth composing
CLIENT = None  # a Claude client when --models names Claude models
NOTES = "\n".join(f"- {note}" for note in MEMORY["NOTES"])
QUESTIONS = MEMORY["QUESTIONS"][:12]
GROUPS = [range(0, 4), range(4, 8), range(8, 12)]


def ask(question, temperature, seed):
    if CLIENT is not None:
        request = {
            "max_tokens": 60,
            "system": "Answer the question from the shop notes, in one short sentence.",
            "messages": [
                {"role": "user", "content": f"Shop notes:\n{NOTES}\n\nQuestion: {question}"}
            ],
        }
        if "temperature" in CLAUDE["SETTINGS"][MODEL]:
            request["temperature"] = temperature
        reply = CLIENT.messages(MODEL, **request)
        return {"message": {"content": CLAUDE["text_of"](reply)}}
    body = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Answer the question from the shop notes, in one short sentence.",
            },
            {"role": "user", "content": f"Shop notes:\n{NOTES}\n\nQuestion: {question}"},
        ],
        "stream": False,
        "options": {"temperature": temperature, "seed": seed, "num_predict": 60, "num_ctx": 4096},
    }
    request = Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=120) as response:
        return json.loads(response.read())


def parallelism():
    tasks = [q for q, _, _ in QUESTIONS[:4]]
    ask(tasks[0], 0, 1)  # load the model before timing
    rows = []
    for repeat in range(3):
        started = time.perf_counter()
        for i, question in enumerate(tasks):
            ask(question, 0, 100 * repeat + i)
        sequential = time.perf_counter() - started
        started = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(4) as pool:
            seeds = [200 + 100 * repeat + i for i in range(len(tasks))]
            list(pool.map(lambda question, seed: ask(question, 0, seed), tasks, seeds))
        parallel = time.perf_counter() - started
        rows.append(
            {"sequential_seconds": round(sequential, 3), "parallel_seconds": round(parallel, 3)}
        )
    speedup = statistics.median(r["sequential_seconds"] / r["parallel_seconds"] for r in rows)
    # Solve Amdahl for the parallel fraction that explains the measured speedup with 4 workers.
    fraction = (1 - 1 / speedup) / (1 - 1 / 4)
    return {
        "subagents": 4,
        "rows": rows,
        "median_speedup": round(speedup, 3),
        "implied_parallel_fraction": round(fraction, 3),
        "amdahl_if_fully_parallel": DELEGATE["amdahl_speedup"](1.0, 4),
    }


def sampling(runs):
    correct = []
    for index, (question, _, expected) in enumerate(QUESTIONS):
        row = []
        for sample in range(10):
            answer = ask(question, 0.7, 1 + sample)["message"]["content"]
            ok = MEMORY["graded"](answer, expected)
            row.append(ok)
            runs.append({"question": index, "sample": sample, "answer": answer, "correct": ok})
        correct.append(row)
    accuracy = [sum(r) / len(r) for r in correct]
    composed = []
    for group in GROUPS:
        predicted = DELEGATE["all_correct"]([accuracy[i] for i in group])
        measured = sum(all(correct[i][s] for i in group) for s in range(10)) / 10
        composed.append(
            {
                "questions": list(group),
                "predicted_product": round(predicted, 3),
                "measured": measured,
            }
        )
    votes = []
    for index, row in enumerate(correct):
        triples = [row[0:3], row[3:6], row[6:9]]
        measured = sum(sum(t) >= 2 for t in triples) / 3
        votes.append(
            {
                "question": index,
                "single_accuracy": round(accuracy[index], 2),
                "predicted_majority_of_3": round(
                    DELEGATE["majority_accuracy"](accuracy[index], 3), 3
                ),
                "measured_majority_of_3": round(measured, 3),
            }
        )
    return {"accuracy": [round(a, 2) for a in accuracy], "composed": composed, "votes": votes}


INQUIRIES = [
    (sku, guests)
    for sku in ("SKU-VANILLA", "SKU-CHOCOLATE", "SKU-STRAWBERRY")
    for guests in (1, 9, 10, 11, 41, 99, 150, 200)
]


def states_total(answer, cents):
    """Whether the model's own sentence names the checked total, in any usual form. Descriptive:
    Lucy is never shown this sentence; the worker states the total from the checked quote."""
    forms = (
        f"{cents / 100:,.2f}",
        f"${cents // 100:,}",
        f"{cents // 100:,} dollars",
        f"{cents:,} cents",
        f"{cents} cents",
    )
    return any(form in answer for form in forms)


def usage_now():
    return {model: dict(used) for model, used in CLIENT.usage.items()}, CLIENT.cost()


def research(model):
    """Part B's worker on Claude: one fresh shop, parent and contract per inquiry."""
    adapter = CLAUDE["LoopModel"](CLIENT, model, DELEGATE["ModelTurn"], DELEGATE["ToolCall"])
    rows = []
    for index, (sku, guests) in enumerate(INQUIRIES):
        with tempfile.TemporaryDirectory(prefix="ch18-claude-") as temporary:
            db, queue = DELEGATE["open_delegation_shop"](Path(temporary) / "agent.sqlite")
            parent = DELEGATE["WORKER"]["enqueue"](queue, f"parent:{index}", "lucy", "Brief.")
            inquiry = DELEGATE["Inquiry"](sku=sku, guests=guests)
            child = DELEGATE["delegate"](
                queue, parent, inquiry, deadline=time.time() + 600, estimated_call_cents=1
            )
            (before, spent), started = usage_now(), time.perf_counter()
            result = DELEGATE["research_once"](db, adapter, work_id=child)
            seconds = time.perf_counter() - started
            (after, now) = usage_now()
            db.close()
        report = result.get("report", {})
        loop = report.get("loop", {})
        expected = DELEGATE["quote"](inquiry)
        used = {k: after[model][k] - before.get(model, {}).get(k, 0) for k in after[model]}
        rows.append(
            {
                "sku": sku,
                "guests": guests,
                "status": result["status"],
                "passed": report.get("passed", False),
                "loop_status": loop.get("status"),
                "model_calls": loop.get("model_calls"),
                "tool_calls": loop.get("tool_calls"),
                "tokens": used,
                "cost_usd": round(now - spent, 6),
                "seconds": round(seconds, 3),
                "answer": report.get("model_answer", ""),
                "answer_states_total": states_total(
                    report.get("model_answer", ""), expected["total_cents"]
                ),
            }
        )
    return rows


def schema_probe(model):
    """The first turn against a tool with no arguments: does the model add arguments anyway?"""
    adapter = CLAUDE["LoopModel"](CLIENT, model, DELEGATE["ModelTurn"], DELEGATE["ToolCall"])
    empty = {
        "type": "function",
        "function": {
            "name": "catering_quote",
            "description": "Calculate this assignment's read-only draft quote.",
            "parameters": DELEGATE["NoArguments"].model_json_schema(),
        },
    }
    rows = []
    for sku, guests in INQUIRIES:
        inquiry = DELEGATE["Inquiry"](sku=sku, guests=guests).model_dump_json()
        messages = [
            {"role": "system", "content": DELEGATE["RESEARCH_PROMPT"]},
            {"role": "user", "content": inquiry},
        ]
        turn = adapter.complete(messages, [empty], timeout=120, max_output_tokens=512)
        arguments = [call.arguments for call in turn.calls]
        rows.append(
            {
                "sku": sku,
                "guests": guests,
                "called": bool(turn.calls),
                "arguments": arguments,
                "refused_by_strict_dispatch": any(bool(a) for a in arguments),
            }
        )
    return rows


def summary(rows):
    n = len(rows)
    return {
        "inquiries": n,
        "verified": sum(r["passed"] for r in rows),
        "statuses": {
            s: sum(r["status"] == s for r in rows) for s in sorted({r["status"] for r in rows})
        },
        "mean_model_calls": round(statistics.mean(r["model_calls"] or 0 for r in rows), 2),
        "mean_seconds": round(statistics.mean(r["seconds"] for r in rows), 3),
        "median_seconds": round(statistics.median(r["seconds"] for r in rows), 3),
        "cost_usd_total": round(sum(r["cost_usd"] for r in rows), 4),
        "answer_states_total": sum(r["answer_states_total"] for r in rows),
    }


def claude_main(args):
    global CLIENT, MODEL
    CLIENT = CLAUDE["Claude"](args.budget)
    started = time.time()
    receipt = {
        "schema": 1,
        "experiment": "ch18-delegation-claude-v1",
        "recorded": time.strftime("%Y-%m-%d"),
        "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "api": f"Messages API, anthropic-version {CLAUDE['VERSION']}",
        "models": {},
        "runs": [],
    }
    for model in args.models:
        MODEL = model
        runs = []
        measured = {
            "parallelism": parallelism(),
            "sampling": sampling(runs),
            "research": research(model),
            "schema_probe": schema_probe(model),
        }
        measured["research_summary"] = summary(measured["research"])
        measured["schema_summary"] = {
            "inquiries": len(measured["schema_probe"]),
            "called": sum(r["called"] for r in measured["schema_probe"]),
            "refused_by_strict_dispatch": sum(
                r["refused_by_strict_dispatch"] for r in measured["schema_probe"]
            ),
        }
        receipt["models"][model] = measured
        receipt["runs"].extend({"model": model, **run} for run in runs)
        print(model, json.dumps({k: measured[k] for k in ("research_summary", "schema_summary")}))
        print(model, json.dumps(measured["parallelism"]), flush=True)
    receipt["seconds"] = round(time.time() - started, 1)
    receipt["usage"] = CLIENT.report()
    args.out.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt["usage"], indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--model", default="qwen2.5:0.5b")
    parser.add_argument("--models", nargs="+", help="Claude model ids; runs on the Messages API")
    parser.add_argument("--budget", type=float, default=5.0, help="Claude spending ceiling, USD")
    args = parser.parse_args()
    if not args.out.parent.is_dir():
        # Checked before any request: a paid run must not end unable to save its receipt.
        parser.error(f"no folder for --out: {args.out.parent}")
    if args.models:
        return claude_main(args)
    global MODEL
    MODEL = args.model
    started = time.time()
    runs = []
    receipt = {
        "schema": 1,
        "experiment": "ch18-delegation-v1",
        "recorded": time.strftime("%Y-%m-%d"),
        "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "model": MODEL,
        "parallelism": parallelism(),
        "sampling": sampling(runs),
        "tokens_example": DELEGATE["delegation_tokens"](600, [30, 30, 30, 30], 200),
    }
    receipt["seconds"] = round(time.time() - started, 1)
    receipt["runs"] = runs
    args.out.write_text(json.dumps(receipt, indent=2) + "\n")
    json.dump({k: v for k, v in receipt.items() if k != "runs"}, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
