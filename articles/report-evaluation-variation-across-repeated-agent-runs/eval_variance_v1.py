# Prof Rod | Did A Really Beat B? Eval Variance Across Repeated Runs
# Article: https://profrod.ai/articles/report-evaluation-variation-across-repeated-agent-runs
# Original source and updates: https://github.com/profrodai/profrodai-resources

"""Run one evaluation ten times and see what a single run can and cannot tell you. Measured on
OpenAI's GPT-6 Luna and GPT-5.6 Luna at medium reasoning effort.

1. Tasks: 100 AIME problems (numbers 6 to 15 of each exam, the harder half), sampled with a fixed
   seed from `di-zhang-fdu/AIME_1983_2024` on Hugging Face (MIT licence tag), pinned to one
   revision. Answers are integers from 0 to 999, so correctness is exact. The repository keeps
   only problem ids and answers; the problem text is fetched from the pinned revision at run time.
2. Systems, all at reasoning effort `medium`, capped at 8,000 output tokens:
   - `gpt-6-luna`: the prompt below.
   - `gpt-6-luna-reworded`: the same model with the instruction in other words. Against
     `gpt-6-luna` the true difference should be near zero, so any "win" it shows is noise.
   - `gpt-5.6-luna`: the previous model with the same prompt. Against `gpt-6-luna` it is the
     question every model upgrade raises: did the new one really beat the old one?
3. Every system runs every task 10 times. A reply that runs out of tokens counts as wrong.
4. Statistics (variance_stats_v1.py): per-run spread, naive vs clustered standard errors, the
   intraclass correlation and design effect, paired differences with a task-level bootstrap,
   McNemar per run, and pass@k and pass^k from per-task success counts.

Run it (Python 3.12, standard library only):
    uv run --no-project --python 3.12 python eval_variance_v1.py all --max-usd 8
The key comes from OPENAI_API_KEY, else from the .env file named by OPENAI_ENV_FILE. It is never
printed or written anywhere. Receipts record model ids, settings, tokens and cost only. Attempts are
appended as they finish, so a stopped run resumes where it stopped.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import random
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import variance_stats_v1 as V

HERE = Path(__file__).resolve().parent
DATASET = "di-zhang-fdu/AIME_1983_2024"
REVISION = "3e2cc86390666c5c756622afc0eeb9e6194496bc"
SOURCE_URL = f"https://huggingface.co/datasets/{DATASET}/resolve/{REVISION}/AIME_Dataset_1983_2024.csv"
SEED = 20261001
TASKS, RUNS = 100, 10
API = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com").rstrip("/")
EFFORT = "medium"
MAX_OUTPUT = 8000
# USD per million tokens (input, output), developers.openai.com pricing page, standard tier, read
# 2026-09-30. Reasoning tokens are counted in the Responses API's output_tokens.
PRICES = {"gpt-6-luna": (0.10, 0.50), "gpt-5.6-luna": (0.20, 1.20)}

PROMPT = "Solve this problem. The answer is an integer from 0 to 999. Reply with only the final integer.\n\n{q}"
REWORDED = "Work out the following competition problem and give just the resulting whole number (0 to 999).\n\n{q}"
SYSTEMS = {
    "gpt-6-luna": ("gpt-6-luna", PROMPT),
    "gpt-6-luna-reworded": ("gpt-6-luna", REWORDED),
    "gpt-5.6-luna": ("gpt-5.6-luna", PROMPT),
}
COMPARISONS = [("gpt-6-luna", "gpt-6-luna-reworded"), ("gpt-5.6-luna", "gpt-6-luna")]


def api_key() -> str:
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key and os.environ.get("OPENAI_ENV_FILE"):
        for line in Path(os.environ["OPENAI_ENV_FILE"]).expanduser().read_text().splitlines():
            name, _, value = line.strip().removeprefix("export ").partition("=")
            if name.strip() == "OPENAI_API_KEY" and value.strip():
                key = value.strip().strip('"').strip("'")
    if not key:
        raise RuntimeError("No OpenAI key: set OPENAI_API_KEY (on Colab, from the Secrets panel)")
    return key


class OpenAI:
    """Responses API with retries, thread-safe token accounting per model and a spending ceiling."""

    def __init__(self, max_usd: float):
        self.max_usd, self._key, self._lock = max_usd, api_key(), threading.Lock()
        self.usage = {m: {"input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0} for m in PRICES}
        self.requests = 0

    def cost(self) -> float:
        return (
            sum(u["input_tokens"] * PRICES[m][0] + u["output_tokens"] * PRICES[m][1] for m, u in self.usage.items())
            / 1e6
        )

    def text(self, model: str, prompt: str) -> tuple[str, dict, str]:
        """The reply text, its usage and its status ("completed" or "incomplete")."""
        with self._lock:
            if self.cost() >= self.max_usd:
                raise RuntimeError(f"spending ceiling reached: {self.cost():.2f} of {self.max_usd:.2f} USD")
        body = json.dumps(
            {"model": model, "reasoning": {"effort": EFFORT}, "max_output_tokens": MAX_OUTPUT, "input": prompt}
        ).encode()
        headers = {"content-type": "application/json", "authorization": f"Bearer {self._key}"}
        for attempt in range(10):
            try:
                with urlopen(Request(f"{API}/v1/responses", data=body, headers=headers), timeout=600) as r:
                    reply = json.loads(r.read())
                break
            except HTTPError as error:
                # 429 also covers a quota that is still settling after credit is added.
                if error.code not in (408, 429, 500, 502, 503, 504) or attempt == 9:
                    detail = error.read().decode(errors="replace")[:300]
                    raise RuntimeError(f"OpenAI API {error.code}: {detail}") from None
                time.sleep(min(float(error.headers.get("retry-after") or 2**attempt), 60))
            except (URLError, TimeoutError):
                if attempt == 9:
                    raise
                time.sleep(min(2**attempt, 60))
        usage = reply.get("usage", {})
        with self._lock:
            self.requests += 1
            u = self.usage[model]
            u["input_tokens"] += int(usage.get("input_tokens", 0))
            u["output_tokens"] += int(usage.get("output_tokens", 0))
            u["reasoning_tokens"] += int(usage.get("output_tokens_details", {}).get("reasoning_tokens", 0))
        text = "".join(
            part.get("text", "")
            for item in reply.get("output", [])
            if item.get("type") == "message"
            for part in item.get("content", [])
        )
        return text, usage, reply.get("status", "")

    def receipt(self) -> dict:
        return {
            "provider": "openai",
            "endpoint": "/v1/responses",
            "reasoningEffort": EFFORT,
            "maxOutputTokens": MAX_OUTPUT,
            "requests": self.requests,
            "usage": {m: u for m, u in self.usage.items() if u["input_tokens"]},
            "costUsd": round(self.cost(), 4),
            "ceilingUsd": self.max_usd,
            "prices": "USD per million tokens (input, output): gpt-6-luna 0.10/0.50, gpt-5.6-luna 0.20/1.20; "
            "developers.openai.com pricing page, standard tier, 2026-09-30",
        }


def final_integer(text: str) -> int | None:
    found = re.findall(r"\d+", text.replace(",", ""))
    return int(found[-1]) if found else None


def jsonl_write(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


def jsonl_read(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def source_rows(source: Path | None) -> tuple[list[dict], str]:
    raw = source.read_bytes() if source else urlopen(SOURCE_URL, timeout=60).read()
    return list(csv.DictReader(io.StringIO(raw.decode()))), hashlib.sha256(raw).hexdigest()


def sample(source: Path | None) -> dict:
    """Keep only ids and answers; the problem text stays in the source dataset."""
    rows, digest = source_rows(source)
    pool = [r for r in rows if 6 <= int(r["Problem Number"]) <= 15]
    chosen = sorted(random.Random(SEED).sample(pool, TASKS), key=lambda r: r["ID"])
    jsonl_write(HERE / "data/aime-tasks-v1.jsonl", [{"id": r["ID"], "answer": int(r["Answer"])} for r in chosen])
    return {
        "dataset": DATASET,
        "revision": REVISION,
        "source": SOURCE_URL,
        "sourceSha256": digest,
        "seed": SEED,
        "tasks": TASKS,
        "pool": f"{len(pool)} problems numbered 6 to 15",
        "licence": "MIT (dataset card tag); problem text not redistributed here",
    }


def run(client: OpenAI, workers: int, source: Path | None) -> None:
    """Every attempt is appended to results/attempts-v1.jsonl as it finishes, so a run that stops
    (a spending ceiling, a network failure, an empty account) resumes where it stopped."""
    tasks = jsonl_read(HERE / "data/aime-tasks-v1.jsonl")
    rows, digest = source_rows(source)
    expected = json.loads((HERE / "receipts/eval-variance-v1.json").read_text())["data"]["sourceSha256"]
    if digest != expected:
        raise RuntimeError("the source dataset changed since sampling")
    text_of = {r["ID"]: r["Question"] for r in rows}
    path = HERE / "results/attempts-v1.jsonl"
    done = {(a["system"], a["task"], a["run"]) for a in jsonl_read(path)} if path.exists() else set()
    jobs = [(s, t, r) for s in SYSTEMS for t in tasks for r in range(RUNS) if (s, t["id"], r) not in done]
    lock = threading.Lock()
    print(f"{len(done)} attempts already recorded; {len(jobs)} to run")

    def one(job):
        system, task, r = job
        model, template = SYSTEMS[system]
        text, usage, status = client.text(model, template.format(q=text_of[task["id"]]))
        value = final_integer(text) if status == "completed" else None
        row = {
            "task": task["id"],
            "system": system,
            "run": r,
            "answer": value,
            "correct": int(value == task["answer"]),
            "status": status,
            "outputTokens": int(usage.get("output_tokens", 0)),
        }
        with lock, path.open("a") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    with ThreadPoolExecutor(workers) as pool:
        for future in [pool.submit(one, job) for job in jobs]:
            future.result()


def outcomes_by_system() -> dict[str, V.Outcomes]:
    tasks = [t["id"] for t in jsonl_read(HERE / "data/aime-tasks-v1.jsonl")]
    grid = {s: {t: [0] * RUNS for t in tasks} for s in SYSTEMS}
    for a in jsonl_read(HERE / "results/attempts-v1.jsonl"):
        grid[a["system"]][a["task"]][a["run"]] = a["correct"]
    return {s: [grid[s][t] for t in tasks] for s in SYSTEMS}


def summarize() -> dict:
    data = outcomes_by_system()
    attempts = jsonl_read(HERE / "results/attempts-v1.jsonl")
    if len(attempts) != len(SYSTEMS) * TASKS * RUNS:
        raise RuntimeError(f"{len(attempts)} attempts recorded; the run is not complete")
    systems = {}
    for name, outcomes in data.items():
        rates = V.single_run_rates(outcomes)
        rho = V.icc(outcomes)
        counts = [sum(task) for task in outcomes]
        mine = [a for a in attempts if a["system"] == name]
        systems[name] = {
            "model": SYSTEMS[name][0],
            "passRate": sum(counts) / (TASKS * RUNS),
            "singleRunRates": rates,
            "singleRunSpread": V.spread(rates),
            "naiveSe": V.naive_se(outcomes),
            "clusteredSe": V.clustered_se(outcomes),
            "icc": rho,
            "designEffect": V.design_effect(RUNS, rho),
            "taskSuccessCounts": counts,
            "histogram": [counts.count(c) for c in range(RUNS + 1)],
            "passAtK": [V.mean_curve(outcomes, k, V.pass_at_k) for k in range(1, RUNS + 1)],
            "passHatK": [V.mean_curve(outcomes, k, V.pass_hat_k) for k in range(1, RUNS + 1)],
            "meanOutputTokens": sum(a["outputTokens"] for a in mine) / len(mine),
            "incomplete": sum(1 for a in mine if a["status"] != "completed"),
        }
    comparisons = {}
    for base, other in COMPARISONS:
        a, b = data[base], data[other]
        pairs = [(x, y) for x in systems[base]["singleRunRates"] for y in systems[other]["singleRunRates"]]
        comparisons[f"{other} vs {base}"] = {
            "paired": V.paired_difference(a, b),
            "bootstrap95": V.bootstrap_difference(a, b),
            "singleRunPairs": len(pairs),
            "singleRunPairsOtherAhead": sum(1 for x, y in pairs if y > x),
            "singleRunPairsBaseAhead": sum(1 for x, y in pairs if x > y),
            "mcnemarByRun": [V.mcnemar_run(a, b, r) for r in range(RUNS)],
        }
    summary = {"tasks": TASKS, "runs": RUNS, "reasoningEffort": EFFORT, "systems": systems, "comparisons": comparisons}
    (HERE / "results/summary-v1.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=["sample", "run", "summarize", "all"])
    parser.add_argument("--max-usd", type=float, default=8.0)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--source", type=Path, default=None, help="a local copy of the pinned dataset CSV")
    args = parser.parse_args()
    receipt_path = HERE / "receipts/eval-variance-v1.json"
    receipt_path.parent.mkdir(exist_ok=True)
    receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if args.step in ("sample", "all"):
        receipt["data"] = sample(args.source)
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    if args.step in ("run", "all"):
        client = OpenAI(args.max_usd)
        try:
            run(client, args.workers, args.source)
        finally:
            receipt.setdefault("runs", []).append(
                {"started": started, "finished": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **client.receipt()}
            )
            receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    if args.step in ("summarize", "all"):
        s = summarize()
        for name, row in s["systems"].items():
            spread = row["singleRunSpread"]
            print(
                f"{name:20s} pass {row['passRate']:.3f}  runs {spread['min']:.2f}-{spread['max']:.2f}  "
                f"naiveSE {row['naiveSe']:.4f} clusterSE {row['clusteredSe']:.4f} ICC {row['icc']:.2f} "
                f"pass@10 {row['passAtK'][-1]:.3f} pass^10 {row['passHatK'][-1]:.3f} tokens {row['meanOutputTokens']:.0f}"
            )
        for name, row in s["comparisons"].items():
            p = row["paired"]
            print(
                f"{name:34s} diff {p['mean']:+.3f} ± {1.96 * p['se']:.3f}  boot {row['bootstrap95']}  "
                f"single-run pairs other ahead {row['singleRunPairsOtherAhead']}/{row['singleRunPairs']}"
            )


if __name__ == "__main__":
    main()
