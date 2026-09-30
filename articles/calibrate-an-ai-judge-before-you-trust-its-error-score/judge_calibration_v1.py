# Prof Rod | Calibrate an LLM Judge Before You Trust Its Score
# Article: https://profrod.ai/articles/calibrate-an-ai-judge-before-you-trust-its-error-score
# Original source and updates: https://github.com/profrodai/profrodai-resources

"""How often does an LLM judge catch a wrong answer? A measured run on Claude.

The setup, end to end:
1. Sample N problems from the GSM8K test set (grade-school math, MIT licence), seeded.
2. Candidate answers: Claude Haiku 4.5 answers each problem with a bare number and no working.
   Some answers are wrong, and whether each is wrong is known exactly: it either equals the
   GSM8K reference answer or it does not. That is the ground truth no judge sees.
3. Judges: Haiku 4.5 and Sonnet 5.5 each grade every (problem, answer) pair without the reference,
   in two conditions: `direct` (one word, CORRECT or INCORRECT) and `reasoned` (work the problem,
   then give a verdict).
4. Statistics (judge_stats_v1.py): confusion matrices, recall on wrong answers and on right ones,
   Cohen's kappa, Wilson and Clopper-Pearson intervals, a bootstrap interval for kappa, and exact
   McNemar tests between conditions on the same items.

Run it (Python 3.12, standard library only):
    uv run --no-project --python 3.12 python judge_calibration_v1.py all --n 300 --max-usd 8
The key comes from ANTHROPIC_API_KEY, else from the .env file named by ANTHROPIC_ENV_FILE. It is
never printed or written anywhere. Receipts record model ids, settings, tokens and cost only.
"""

from __future__ import annotations

import argparse
import hashlib
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

import judge_stats_v1 as S

HERE = Path(__file__).resolve().parent
GSM8K_URL = "https://raw.githubusercontent.com/openai/grade-school-math/master/grade_school_math/data/test.jsonl"
SEED = 20260930
API = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")

HAIKU, SONNET = "claude-haiku-4-5-20251001", "claude-sonnet-5-5"
# USD per million tokens (input, output), platform.claude.com pricing page, read 2026-09-29.
PRICES = {HAIKU: (1.00, 5.00), SONNET: (2.00, 10.00)}
# Haiku 4.5 takes temperature 0. Sonnet 5.5 rejects temperature; "between_tools" keeps up-front
# thinking off, so any reasoning a judge does is the visible text the prompt asks for.
SETTINGS = {HAIKU: {"temperature": 0}, SONNET: {"thinking": {"type": "between_tools"}}}

CANDIDATE_PROMPT = (
    "Solve this problem. Reply with only the final numeric answer, no words, no units, no working.\n\n{question}"
)
JUDGE_DIRECT = (
    "A student answered this math word problem.\n\nProblem: {question}\n\nStudent's final answer: {answer}\n\n"
    "Is the student's final answer correct? Reply with exactly one word: CORRECT or INCORRECT."
)
JUDGE_REASONED = (
    "A student answered this math word problem.\n\nProblem: {question}\n\nStudent's final answer: {answer}\n\n"
    "Work the problem yourself, step by step. Then end with one final line, exactly "
    "'VERDICT: CORRECT' or 'VERDICT: INCORRECT', saying whether the student's final answer is correct."
)
# Sonnet 5.5 rejects a forced tool choice (tool_choice "tool"/"any", checked 2026-09-30), so the direct
# condition cannot force a bare verdict. It asks for one word, allows room to disobey, takes the last
# standalone verdict, and records whether the judge actually answered in one word.
CONDITIONS = {"direct": (JUDGE_DIRECT, 600), "reasoned": (JUDGE_REASONED, 1500)}
JUDGES = [HAIKU, SONNET]


def api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key and os.environ.get("ANTHROPIC_ENV_FILE"):
        env = Path(os.environ["ANTHROPIC_ENV_FILE"]).expanduser()
        for line in env.read_text().splitlines():
            name, _, value = line.strip().partition("=")
            if name == "ANTHROPIC_API_KEY":
                key = value.strip().strip('"').strip("'")
    if not key:
        raise RuntimeError("No Claude key: set ANTHROPIC_API_KEY (on Colab, from the Secrets panel)")
    return key


class Claude:
    """Messages API with retries, thread-safe token accounting and a spending ceiling."""

    def __init__(self, max_usd: float):
        self.max_usd, self._key, self._lock = max_usd, api_key(), threading.Lock()
        self.usage = {m: {"input_tokens": 0, "output_tokens": 0} for m in PRICES}
        self.requests = 0

    def cost(self) -> float:
        return (
            sum(u["input_tokens"] * PRICES[m][0] + u["output_tokens"] * PRICES[m][1] for m, u in self.usage.items())
            / 1e6
        )

    def text(self, model: str, prompt: str, max_tokens: int) -> tuple[str, int]:
        """The reply's text and its output-token count."""
        with self._lock:
            if self.cost() >= self.max_usd:
                raise RuntimeError(f"spending ceiling reached: {self.cost():.2f} of {self.max_usd:.2f} USD")
        body = json.dumps(
            {
                "model": model,
                "max_tokens": max_tokens,
                **SETTINGS[model],
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode()
        headers = {"content-type": "application/json", "anthropic-version": "2023-06-01", "x-api-key": self._key}
        for attempt in range(8):
            try:
                with urlopen(Request(f"{API}/v1/messages", data=body, headers=headers), timeout=300) as r:
                    reply = json.loads(r.read())
                break
            except HTTPError as error:
                if error.code not in (408, 429, 500, 502, 503, 504, 529) or attempt == 7:
                    raise RuntimeError(
                        f"Claude API {error.code}: {error.read().decode(errors='replace')[:300]}"
                    ) from None
                time.sleep(min(float(error.headers.get("retry-after") or 2**attempt), 60))
            except (URLError, TimeoutError):
                if attempt == 7:
                    raise
                time.sleep(min(2**attempt, 60))
        with self._lock:
            self.requests += 1
            for field in ("input_tokens", "output_tokens"):
                self.usage[model][field] += int(reply.get("usage", {}).get(field, 0))
        out = int(reply.get("usage", {}).get("output_tokens", 0))
        return "".join(block.get("text", "") for block in reply.get("content", [])), out

    def receipt(self) -> dict:
        return {
            "provider": "anthropic",
            "requests": self.requests,
            "usage": {m: u for m, u in self.usage.items() if u["input_tokens"]},
            "costUsd": round(self.cost(), 4),
            "ceilingUsd": self.max_usd,
            "prices": "USD per million tokens (input, output), platform.claude.com pricing page, 2026-09-29",
            "settings": SETTINGS,
        }


NUMBER = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def to_number(text: str) -> float | None:
    found = NUMBER.findall(text.replace("$", ""))
    if not found:
        return None
    try:
        return float(found[-1].replace(",", ""))
    except ValueError:
        return None


def verdict(text: str, condition: str) -> str | None:
    if condition == "reasoned":
        found = re.findall(r"VERDICT:\s*(CORRECT|INCORRECT)", text.upper())
        return found[-1] if found else None
    found = re.findall(r"\b(INCORRECT|CORRECT)\b", text.upper())
    return found[-1] if found else None


def one_word(text: str) -> bool:
    return text.strip().upper().strip(".*") in ("CORRECT", "INCORRECT")


def jsonl_write(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


def jsonl_read(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def sample(n: int, source: Path | None) -> dict:
    raw = source.read_bytes() if source else urlopen(GSM8K_URL, timeout=60).read()
    lines = raw.decode().splitlines()
    chosen = sorted(random.Random(SEED).sample(range(len(lines)), n))
    rows = []
    for i in chosen:
        item = json.loads(lines[i])
        rows.append(
            {
                "id": f"gsm8k-test-{i}",
                "line": i,
                "question": item["question"],
                "gold": float(item["answer"].split("####")[-1].strip().replace(",", "")),
            }
        )
    jsonl_write(HERE / "data/gsm8k-test-sample-v1.jsonl", rows)
    return {
        "source": GSM8K_URL,
        "sourceSha256": hashlib.sha256(raw).hexdigest(),
        "sourceLines": len(lines),
        "seed": SEED,
        "n": n,
        "licence": "MIT (openai/grade-school-math)",
    }


def candidates(claude: Claude, workers: int) -> None:
    items = jsonl_read(HERE / "data/gsm8k-test-sample-v1.jsonl")

    def one(item):
        text, _ = claude.text(HAIKU, CANDIDATE_PROMPT.format(question=item["question"]), 32)
        value = to_number(text)
        return {
            "id": item["id"],
            "model": HAIKU,
            "raw": text.strip(),
            "answer": value,
            "truthWrong": value is None or abs(value - item["gold"]) > 1e-6,
        }

    with ThreadPoolExecutor(workers) as pool:
        jsonl_write(HERE / "results/candidates-v1.jsonl", list(pool.map(one, items)))


def judge(claude: Claude, workers: int) -> None:
    items = {i["id"]: i for i in jsonl_read(HERE / "data/gsm8k-test-sample-v1.jsonl")}
    cands = jsonl_read(HERE / "results/candidates-v1.jsonl")
    jobs = [(m, c, cand) for m in JUDGES for c in CONDITIONS for cand in cands]

    def one(job):
        model, condition, cand = job
        template, max_tokens = CONDITIONS[condition]
        shown = cand["raw"] if cand["raw"] else "(no answer)"
        text, out = claude.text(
            model, template.format(question=items[cand["id"]]["question"], answer=shown), max_tokens
        )
        return {
            "id": cand["id"],
            "judge": model,
            "condition": condition,
            "verdict": verdict(text, condition),
            "outputTokens": out,
            "oneWord": one_word(text),
            "tail": text.strip()[-160:],
        }

    with ThreadPoolExecutor(workers) as pool:
        jsonl_write(HERE / "results/judgments-v1.jsonl", list(pool.map(one, jobs)))


def summarize() -> dict:
    cands = {c["id"]: c for c in jsonl_read(HERE / "results/candidates-v1.jsonl")}
    judgments = jsonl_read(HERE / "results/judgments-v1.jsonl")
    ids = sorted(cands)
    truth = [cands[i]["truthWrong"] for i in ids]
    summary = {
        "n": len(ids),
        "wrongAnswers": sum(truth),
        "rightAnswers": len(ids) - sum(truth),
        "candidateAccuracy": {
            "k": len(ids) - sum(truth),
            "n": len(ids),
            "wilson95": S.wilson(len(ids) - sum(truth), len(ids)),
        },
        "judges": {},
    }
    correct_by = {}
    for model in JUDGES:
        for condition in CONDITIONS:
            got = {j["id"]: j["verdict"] for j in judgments if j["judge"] == model and j["condition"] == condition}
            unparsed = [i for i in ids if got.get(i) is None]
            keep = [i for i in ids if got.get(i) is not None]
            t = [cands[i]["truthWrong"] for i in keep]
            j = [got[i] == "INCORRECT" for i in keep]
            c = S.confusion(t, j)
            correct_by[(model, condition)] = {i: (got[i] == "INCORRECT") == cands[i]["truthWrong"] for i in keep}
            summary["judges"][f"{model}/{condition}"] = {
                "confusion": {"tp": c.tp, "fn": c.fn, "fp": c.fp, "tn": c.tn},
                "unparsed": len(unparsed),
                "meanOutputTokens": sum(
                    x["outputTokens"] for x in judgments if x["judge"] == model and x["condition"] == condition
                )
                / len(ids),
                "oneWordReplies": sum(
                    1 for x in judgments if x["judge"] == model and x["condition"] == condition and x.get("oneWord")
                ),
                "accuracy": {"value": c.accuracy(), "wilson95": S.wilson(c.tp + c.tn, c.n)},
                "recallWrong": {
                    "k": c.tp,
                    "n": c.tp + c.fn,
                    "wilson95": S.wilson(c.tp, c.tp + c.fn),
                    "clopperPearson95": S.clopper_pearson(c.tp, c.tp + c.fn),
                },
                "recallRight": {"k": c.tn, "n": c.tn + c.fp, "wilson95": S.wilson(c.tn, c.tn + c.fp)},
                "kappa": {"value": c.kappa(), "bootstrap95": S.kappa_bootstrap(t, j)},
            }
    tests = {}
    for model in JUDGES:
        a, b = correct_by[(model, "direct")], correct_by[(model, "reasoned")]
        both = [i for i in ids if i in a and i in b]
        only_direct = sum(a[i] and not b[i] for i in both)
        only_reasoned = sum(b[i] and not a[i] for i in both)
        tests[f"{model}: direct vs reasoned"] = {
            "pairs": len(both),
            "onlyDirectRight": only_direct,
            "onlyReasonedRight": only_reasoned,
            "mcnemarExactP": S.mcnemar_exact(only_direct, only_reasoned),
        }
    summary["pairedTests"] = tests
    # The Rogan-Gladen correction, out of sample: measure a judge's two recalls on a seeded half of
    # the items, then correct the error rate it reports on the other half. (On the same items it is
    # an identity, so only a held-out half shows whether it works.)
    order = ids[:]
    random.Random(SEED + 1).shuffle(order)
    calib, held = order[: len(order) // 2], order[len(order) // 2 :]
    correction = {}
    for model in JUDGES:
        for condition in CONDITIONS:
            got = {j["id"]: j["verdict"] for j in judgments if j["judge"] == model and j["condition"] == condition}
            a = S.confusion([cands[i]["truthWrong"] for i in calib], [got[i] == "INCORRECT" for i in calib])
            b = S.confusion([cands[i]["truthWrong"] for i in held], [got[i] == "INCORRECT" for i in held])
            se, sp = a.recall_wrong(), a.recall_right()
            reported = (b.tp + b.fp) / b.n
            youden = se + sp - 1
            correction[f"{model}/{condition}"] = {
                "calibrationItems": a.n,
                "heldOutItems": b.n,
                "calibratedCatchWrong": se,
                "calibratedPassRight": sp,
                "heldOutTruth": (b.tp + b.fn) / b.n,
                "heldOutReported": reported,
                "heldOutCorrected": None if youden <= 0 else min(1.0, max(0.0, (reported + sp - 1) / youden)),
            }
    summary["correctionOutOfSample"] = correction
    (HERE / "results/summary-v1.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=["sample", "candidates", "judge", "summarize", "all"])
    parser.add_argument("--n", type=int, default=300)
    parser.add_argument("--max-usd", type=float, default=8.0)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--source", type=Path, default=None, help="a local copy of GSM8K test.jsonl")
    args = parser.parse_args()
    receipt_path = HERE / "receipts/judge-calibration-v1.json"
    receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if args.step in ("sample", "all"):
        receipt["data"] = sample(args.n, args.source)
    if args.step in ("candidates", "judge", "all"):
        claude = Claude(args.max_usd)
        if args.step in ("candidates", "all"):
            candidates(claude, args.workers)
        if args.step in ("judge", "all"):
            judge(claude, args.workers)
        receipt.setdefault("runs", []).append(
            {
                "step": args.step,
                "started": started,
                "finished": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                **claude.receipt(),
            }
        )
    if args.step in ("summarize", "all"):
        summary = summarize()
        print(json.dumps({k: v for k, v in summary.items() if k != "judges"}, indent=2))
        for name, row in summary["judges"].items():
            print(
                f"{name:40s} acc={row['accuracy']['value']:.3f} recallWrong={row['recallWrong']['k']}/{row['recallWrong']['n']}"
                f" recallRight={row['recallRight']['k']}/{row['recallRight']['n']} kappa={row['kappa']['value']:.3f} unparsed={row['unparsed']}"
            )
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
