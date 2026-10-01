# Prof Rod | Measure the Latency Your User Experiences
# Article: https://profrod.ai/articles/measure-the-latency-your-user-experiences
# Original source and updates: https://github.com/profrodai/profrodai-resources

"""Where the wait goes, measured on small open models: prefill, decode, a prefix cache, and a queue.

Models: Qwen2.5-Instruct at 0.5B and 1.5B parameters, pinned to the revisions in
data/revisions-v1.json, run in float16 on a GPU (CUDA on Colab, MPS on a Mac). The model runs in a
hand-written greedy loop rather than `generate`, so every phase is timed on its own, with the device
synchronized before each clock read.

Four experiments (all interleave their conditions, after warm-up runs that are not recorded):
- `prefill`: time to first token for prompts of 64 to 4,096 tokens, 20 trials each. Fit
  T(P) = a + bP + cP^2.
- `decode`: 256 greedy tokens after prompts of 128 and 2,048 tokens, 10 trials each; the time of
  every decode step.
- `cache`: a 2,048-token shared prefix and a 32-token question. `cold` prefills all of it; `warm`
  reuses the prefix's KV cache and prefills only the question; `changed` alters the prefix's first
  token, so the exact-prefix lookup misses and it prefills everything. 200 trials each.
- `queue`: one worker serves requests (256-token prompt, 32 generated tokens) in arrival order.
  Arrivals are Poisson at utilizations 0.3 to 0.9 of the measured service rate, 200 requests each.
  The run checks Little's law and the Pollaczek-Khinchine mean wait against what it measured.

Run it (Python 3.12):
    uv run --no-project --python 3.12 --with 'transformers==5.18.0' --with torch --with accelerate \\
        python latency_run_v1.py all --model Qwen/Qwen2.5-0.5B-Instruct
    ... python latency_run_v1.py summarize
Timing needs a quiet machine: run nothing else heavy at the same time. `--quick` runs a tenth of
the trials, for a first look on Colab.
"""

from __future__ import annotations

import argparse
import json
import platform
import queue as queue_mod
import random
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import latency_stats_v1 as S  # noqa: E402

MODELS = ["Qwen/Qwen2.5-0.5B-Instruct", "Qwen/Qwen2.5-1.5B-Instruct"]
REVISIONS: dict[str, str] = json.loads((HERE / "data" / "revisions-v1.json").read_text()) if (HERE / "data" / "revisions-v1.json").exists() else {}
RESULTS = HERE / "results"
RECEIPT = HERE / "receipts" / "latency-v1.json"
SEED = 20261001
PREFILL_LENGTHS = [64, 128, 256, 512, 1024, 2048, 4096]
PREFIX, QUESTION = 2048, 32
UTILIZATIONS = [0.3, 0.5, 0.7, 0.8, 0.9]
WORDS = ("the model reads every token of the prompt before it writes the first word of its reply and then it writes "
         "one token at a time each step reading the weights again from memory while the cache holds keys and values "
         "for every earlier position so a long shared prefix can be computed once and reused by every request that "
         "starts with exactly the same tokens a queue forms when requests arrive faster than one worker can serve them").split()


class Bench:
    """One model on one device, with a timed greedy loop."""

    def __init__(self, model_id: str, device: str | None):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.torch = torch
        self.device = device or ("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
        self.dtype = torch.float16 if self.device in ("cuda", "mps") else torch.float32
        self.model_id, self.revision = model_id, REVISIONS.get(model_id)
        self.tok = AutoTokenizer.from_pretrained(model_id, revision=self.revision)
        self.model = AutoModelForCausalLM.from_pretrained(model_id, revision=self.revision, dtype=self.dtype).to(self.device).eval()
        rng = random.Random(SEED)
        text = " ".join(rng.choice(WORDS) for _ in range(12000))
        self.pool = self.tok(text, return_tensors="pt")["input_ids"][0]

    def sync(self) -> None:
        if self.device == "cuda":
            self.torch.cuda.synchronize()
        elif self.device == "mps":
            self.torch.mps.synchronize()

    def ids(self, n: int, offset: int = 0):
        return self.pool[offset : offset + n].unsqueeze(0).to(self.device)

    def step(self, ids, cache=None):
        """One forward pass; returns the greedy next token and the cache, after the device is idle."""
        with self.torch.no_grad():
            out = self.model(input_ids=ids, past_key_values=cache, use_cache=True)
        nxt = out.logits[:, -1:, :].argmax(-1)
        self.sync()
        return nxt, out.past_key_values

    def timed_prefill(self, ids, cache=None):
        self.sync()
        t0 = time.perf_counter()
        nxt, cache = self.step(ids, cache)
        return time.perf_counter() - t0, nxt, cache

    def timed_decode(self, nxt, cache, m: int) -> list[float]:
        times = []
        for _ in range(m):
            t0 = time.perf_counter()
            nxt, cache = self.step(nxt, cache)
            times.append(time.perf_counter() - t0)
        return times

    def meta(self) -> dict:
        return {"model": self.model_id, "revision": self.revision, "device": self.device, "dtype": str(self.dtype).replace("torch.", "")}


def warm_up(b: Bench, rounds: int = 3) -> None:
    for _ in range(rounds):
        _, nxt, cache = b.timed_prefill(b.ids(512))
        b.timed_decode(nxt, cache, 8)


def write(name: str, b: Bench, rows: list[dict]) -> None:
    RESULTS.mkdir(exist_ok=True)
    path = RESULTS / f"{name}-v1.jsonl"
    keep = [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []
    keep = [r for r in keep if r["model"] != b.model_id]
    path.write_text("".join(json.dumps(r) + "\n" for r in keep + [{**b.meta(), **r} for r in rows]))
    print(f"  {name}: {len(rows)} rows", flush=True)


def run_prefill(b: Bench, reps: int) -> None:
    order = [p for p in PREFILL_LENGTHS for _ in range(reps)]
    random.Random(SEED).shuffle(order)
    rows = []
    for i, p in enumerate(order):
        t, _, _ = b.timed_prefill(b.ids(p, offset=(i * 7) % 512))
        rows.append({"promptTokens": p, "seconds": t})
    write("prefill", b, rows)


def run_decode(b: Bench, reps: int, m: int = 256) -> None:
    rows = []
    for rep in range(reps):
        for p in (128, 2048):
            ttft, nxt, cache = b.timed_prefill(b.ids(p, offset=rep * 11))
            steps = b.timed_decode(nxt, cache, m)
            rows.append({"promptTokens": p, "rep": rep, "ttft": ttft, "steps": steps})
    write("decode", b, rows)


def run_cache(b: Bench, reps: int) -> None:
    prefix = b.ids(PREFIX)
    changed = prefix.clone()
    changed[0, 0] = (int(changed[0, 0]) + 1) % b.tok.vocab_size
    # A server hashes the token ids it already holds on the CPU; so does this lookup.
    key = {"prefix": tuple(prefix[0].tolist()), "changed": tuple(changed[0].tolist())}
    # The cache store: exact token prefix -> its KV cache. Built once, outside the timed trials.
    _, _, stored = b.timed_prefill(prefix)
    store = {key["prefix"]: stored}
    order = [c for c in ("cold", "warm", "changed") for _ in range(reps)]
    random.Random(SEED).shuffle(order)
    rows = []
    for i, cond in enumerate(order):
        question = b.ids(QUESTION, offset=PREFIX + 64 + (i % 200) * QUESTION)
        head = changed if cond == "changed" else prefix
        b.sync()
        t0 = time.perf_counter()
        hit = store.get(key["changed" if cond == "changed" else "prefix"]) if cond != "cold" else None
        if hit is not None:
            hit.crop(PREFIX)  # drop the previous question's positions; keep the prefix
            b.step(question, hit)
        else:
            b.step(b.torch.cat([head, question], dim=1))
        rows.append({"condition": cond, "seconds": time.perf_counter() - t0, "hit": hit is not None})
    write("cache", b, rows)
    write("cache-check", b, [cache_agreement(b, prefix, stored)])


def cache_agreement(b: Bench, prefix, stored, questions: int = 20) -> dict:
    """On the same questions, does reusing the prefix cache give the same next-token logits as a full prefill?"""
    torch = b.torch
    same, diffs = 0, []
    for q in range(questions):
        question = b.ids(QUESTION, offset=PREFIX + 64 + q * QUESTION)
        with torch.no_grad():
            full = b.model(input_ids=torch.cat([prefix, question], dim=1)).logits[0, -1].float()
            stored.crop(PREFIX)
            warm = b.model(input_ids=question, past_key_values=stored, use_cache=True).logits[0, -1].float()
        same += int(full.argmax() == warm.argmax())
        diffs.append(float((full - warm).abs().max()))
    return {"questions": questions, "sameNextToken": same, "maxLogitDiff": max(diffs)}


def run_queue(b: Bench, requests: int) -> None:
    prompt = b.ids(256, offset=1000)

    def serve() -> float:
        t0 = time.perf_counter()
        _, nxt, cache = b.timed_prefill(prompt)
        b.timed_decode(nxt, cache, 31)
        return time.perf_counter() - t0

    # The first calls on a new prompt shape include one-off GPU warm-up; keep them out of the calibration.
    for _ in range(5):
        serve()
    calib = [serve() for _ in range(30)]
    mean_s = sum(calib) / len(calib)
    rows = []
    for rho in UTILIZATIONS:
        lam = rho / mean_s
        rng = random.Random(SEED + int(rho * 100))
        gaps = [rng.expovariate(lam) for _ in range(requests)]
        inbox: queue_mod.Queue = queue_mod.Queue()
        done: list[dict] = []
        # An independent instrument for L: a monitor samples the number in the system every 5 ms.
        # (L computed from the arrival and departure times themselves equals lambda * W by
        # construction, so it cannot test the law.)
        count = [0]
        lock = threading.Lock()
        samples: list[tuple[float, int]] = []
        stop = threading.Event()

        def monitor() -> None:
            while not stop.is_set():
                with lock:
                    samples.append((time.perf_counter(), count[0]))
                time.sleep(0.005)

        def worker() -> None:
            while True:
                item = inbox.get()
                if item is None:
                    return
                start = time.perf_counter()
                serve()
                end = time.perf_counter()
                with lock:
                    count[0] -= 1
                done.append({"arrival": item, "start": start, "end": end})

        th = threading.Thread(target=worker)
        mon = threading.Thread(target=monitor)
        th.start()
        mon.start()
        t = time.perf_counter()
        for g in gaps:
            t += g
            while (now := time.perf_counter()) < t:
                time.sleep(min(0.002, t - now))
            with lock:
                count[0] += 1
            inbox.put(t)
        inbox.put(None)
        th.join()
        stop.set()
        mon.join()
        t0 = done[0]["arrival"]
        window = [c for ts, c in samples if t0 <= ts <= done[-1]["end"]]
        rows.append({"rho": rho, "sampledL": sum(window) / len(window), "samples": len(window)})
        for d in done:
            rows.append({"rho": rho, "lambda": lam, "arrival": d["arrival"] - t0, "start": d["start"] - t0, "end": d["end"] - t0})
        print(f"    rho {rho}: mean wait {sum(d['end'] - d['arrival'] for d in done) / len(done):.3f}s", flush=True)
    write("queue", b, [{"calibrationServiceSeconds": calib}] + rows)


def summarize() -> dict:
    load = lambda name: [json.loads(x) for x in (RESULTS / f"{name}-v1.jsonl").read_text().splitlines()] if (RESULTS / f"{name}-v1.jsonl").exists() else []  # noqa: E731
    prefill, decode, cache, check, queue = (load(n) for n in ("prefill", "decode", "cache", "cache-check", "queue"))
    out: dict = {"models": {}}
    for m in MODELS:
        pr = [r for r in prefill if r["model"] == m]
        if not pr:
            continue
        row: dict = {"revision": REVISIONS.get(m), "device": pr[0]["device"], "dtype": pr[0]["dtype"]}
        med = {p: S.percentile([r["seconds"] for r in pr if r["promptTokens"] == p], 0.5) for p in PREFILL_LENGTHS}
        a, bb, c = S.fit_quadratic([float(r["promptTokens"]) for r in pr], [r["seconds"] for r in pr])
        row["prefill"] = {"medianSeconds": med, "fit": {"a": a, "b": bb, "c": c},
                          "p95Seconds": {p: S.percentile([r["seconds"] for r in pr if r["promptTokens"] == p], 0.95) for p in PREFILL_LENGTHS}}
        de = [r for r in decode if r["model"] == m]
        row["decode"] = {}
        for p in (128, 2048):
            steps = [s for r in de if r["promptTokens"] == p for s in r["steps"]]
            per_pos = [S.percentile([r["steps"][i] for r in de if r["promptTokens"] == p], 0.5) for i in range(len(de[0]["steps"]))]
            row["decode"][str(p)] = {"medianStepSeconds": S.percentile(steps, 0.5), "p95StepSeconds": S.percentile(steps, 0.95),
                                     "tokensPerSecond": 1 / S.percentile(steps, 0.5), "medianByStep": per_pos}
        ca = [r for r in cache if r["model"] == m]
        row["cache"] = {}
        for cond in ("cold", "warm", "changed"):
            xs = [r["seconds"] for r in ca if r["condition"] == cond]
            row["cache"][cond] = {"n": len(xs), "p50": S.percentile(xs, 0.5), "p95": S.percentile(xs, 0.95),
                                  "p50Interval": S.percentile_interval(xs, 0.5), "p95Interval": S.percentile_interval(xs, 0.95),
                                  "hits": sum(r["hit"] for r in ca if r["condition"] == cond), "values": xs}
        row["cacheCheck"] = next((r for r in check if r["model"] == m), None)
        qu = [r for r in queue if r["model"] == m]
        calib = next(r["calibrationServiceSeconds"] for r in qu if "calibrationServiceSeconds" in r)
        row["queue"] = {"calibrationMeanServiceSeconds": sum(calib) / len(calib), "levels": []}
        for rho in UTILIZATIONS:
            rs = [r for r in qu if r.get("rho") == rho and "arrival" in r]
            sampled = next(r for r in qu if r.get("rho") == rho and "sampledL" in r)
            if not rs:
                continue
            service = [r["end"] - r["start"] for r in rs]
            waits = [r["end"] - r["arrival"] for r in rs]
            _, span = S.time_average_in_system([r["arrival"] for r in rs], [r["end"] for r in rs])
            lam_hat = len(rs) / span
            es, es2 = sum(service) / len(service), sum(x * x for x in service) / len(service)
            row["queue"]["levels"].append({
                "rho": rho, "lambdaTarget": rs[0]["lambda"], "lambdaMeasured": lam_hat, "rhoMeasured": lam_hat * es,
                "meanService": es, "secondMomentService": es2, "meanWait": sum(waits) / len(waits), "p95Wait": S.percentile(waits, 0.95),
                "L": sampled["sampledL"], "samples": sampled["samples"], "lambdaW": lam_hat * sum(waits) / len(waits),
                "pkWait": S.pollaczek_khinchine_wait(lam_hat, es, es2), "requests": len(rs),
            })
        out["models"][m] = row
    (RESULTS / "summary-v1.json").write_text(json.dumps(out, indent=1) + "\n")
    return out


def receipt(wall: dict | None = None) -> None:
    import importlib.metadata as md

    s = json.loads((RESULTS / "summary-v1.json").read_text())
    rec = {
        "experiment": "measure-the-latency-your-user-experiences v1",
        "ranOn": time.strftime("%Y-%m-%d"),
        "where": f"{platform.system()} {platform.machine()}, Python {platform.python_version()}",
        "devices": sorted({f"{v['device']} ({v['dtype']})" for v in s["models"].values()}),
        "packages": {p: md.version(p) for p in ("transformers", "torch")},
        "models": {m: REVISIONS.get(m) for m in s["models"]},
        "settings": {"prefillLengths": PREFILL_LENGTHS, "prefixTokens": PREFIX, "questionTokens": QUESTION,
                     "utilizations": UTILIZATIONS, "seed": SEED, "decoding": "greedy, hand-written loop"},
        "costUsd": 0.0,
        "note": "Open weights run locally; no API was called. Timings depend on the machine; rerun on yours.",
    }
    RECEIPT.parent.mkdir(exist_ok=True)
    RECEIPT.write_text(json.dumps(rec, indent=2) + "\n")


def revisions() -> None:
    from huggingface_hub import HfApi

    revs = {m: HfApi().model_info(m).sha for m in MODELS}
    (HERE / "data").mkdir(exist_ok=True)
    (HERE / "data" / "revisions-v1.json").write_text(json.dumps(revs, indent=2) + "\n")
    print(json.dumps(revs, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prefill", "decode", "cache", "queue", "all", "summarize", "receipt", "revisions"])
    ap.add_argument("--model", choices=MODELS, default=MODELS[0])
    ap.add_argument("--device")
    ap.add_argument("--quick", action="store_true", help="a tenth of the trials")
    args = ap.parse_args()
    if args.cmd == "summarize":
        summarize()
        return
    if args.cmd == "receipt":
        receipt()
        return
    if args.cmd == "revisions":
        revisions()
        return
    k = 10 if args.quick else 1
    b = Bench(args.model, args.device)
    print(f"{args.model} on {b.device} ({b.dtype})", flush=True)
    warm_up(b)
    if args.cmd in ("prefill", "all"):
        run_prefill(b, max(2, 20 // k))
    if args.cmd in ("decode", "all"):
        run_decode(b, max(2, 10 // k))
    if args.cmd in ("cache", "all"):
        run_cache(b, max(20, 200 // k))
    if args.cmd in ("queue", "all"):
        run_queue(b, max(20, 200 // k))


if __name__ == "__main__":
    main()
