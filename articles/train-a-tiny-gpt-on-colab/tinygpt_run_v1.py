# Prof Rod | Train a Tiny GPT on Colab
# Article: https://profrod.ai/articles/train-a-tiny-gpt-on-colab
# Original source and updates: https://github.com/profrodai/profrodai-resources

"""Train a small GPT on TinyStories in plain PyTorch, measure what a healthy run looks like across
seeds, then plant one-line bugs and see which ones the healthy band catches, and how early.

Data: a pinned slice of TinyStoriesV2-GPT4 (roneneldan/TinyStories at a fixed revision; license
CDLA-Sharing-1.0). The first TRAIN_BYTES of the train file are fetched with an HTTP range request
and cut at the last story boundary; the validation file is fetched whole. Both are checked against
the SHA-256 hashes in data/dataset-v1.json. The tokenizer is a 4,096-token byte-level BPE trained on
the train slice and committed as data/tokenizer-v1.json (its hash is checked too).

Subcommands:
    prepare     download, verify and tokenize the data (cached under cache/)
    train       one run: --seed, --bug, --purpose, --steps, --device
    summarize   results/runs-v1.jsonl -> results/summary-v1.json
    receipt     -> receipts/tinygpt-v1.json

Run it (Python 3.12):
    uv run --no-project --python 3.12 --with 'torch==2.14.1' --with 'tokenizers==0.23.2' --with 'numpy==2.3.3' \\
        python tinygpt_run_v1.py prepare
    ... python tinygpt_run_v1.py train --seed 0
Timings need a quiet machine: run nothing else heavy at the same time.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import tinygpt_stats_v1 as S  # noqa: E402

DATASET = "roneneldan/TinyStories"
REVISION = "f54c09fd23315a6f9c86f9dc80f725de7d8f9c64"
LICENSE = "CDLA-Sharing-1.0"
TRAIN_FILE, VALID_FILE = "TinyStoriesV2-GPT4-train.txt", "TinyStoriesV2-GPT4-valid.txt"
TRAIN_BYTES = 100_000_000
# The validation file is fetched whole, so its hash must equal the one the Hub publishes for it (Git LFS oid).
VALID_SHA256 = "6874bae9a4c1a4e7edcf0e53b86c17817e9cf881fc75ff2368da457b80c0585d"
EOT = "<|endoftext|>"
VOCAB = 4096
DATA = HERE / "data"
CACHE = HERE / "cache"
RESULTS = HERE / "results"
RUNS = RESULTS / "runs-v1.jsonl"
SUMMARY = RESULTS / "summary-v1.json"
RECEIPT = HERE / "receipts" / "tinygpt-v1.json"
MANIFEST = DATA / "dataset-v1.json"
TOKENIZER = DATA / "tokenizer-v1.json"

# The run every number in the article comes from. Batch 32 x 256 tokens = 8,192 tokens per step,
# 1,000 steps = 8.2M tokens, about a third of the train slice. Sized so that 14 runs (5 healthy seeds,
# 3 bugs x 3 seeds) fit one free Colab session; see README.md for the basis of that estimate.
TRAIN = {
    "batch_size": 32,
    "steps": 1000,
    "max_lr": 1e-3,
    "min_lr": 1e-4,
    "warmup_steps": 100,
    "weight_decay": 0.1,
    "betas": (0.9, 0.95),
    "grad_clip": 1.0,
    "eval_every": 50,
    "eval_batches": 20,
}
# The knob for a larger run: `--preset long` trains 3 times as many steps (24.6M tokens, about one pass
# over the slice) and takes about 3 times as long. Its band is a different band: never mix presets.
PRESETS: dict[str, dict] = {"default": {}, "long": {"steps": 3000}}
HEALTHY_SEEDS = [0, 1, 2, 3, 4]
HELD_OUT_SEEDS = [10, 11, 12]  # bug runs and healthy controls: seeds the band never saw


def url(name: str) -> str:
    return f"https://huggingface.co/datasets/{DATASET}/resolve/{REVISION}/{name}"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(name: str, byte_range: tuple[int, int] | None = None) -> bytes:
    req = urllib.request.Request(url(name))
    if byte_range:
        req.add_header("Range", f"bytes={byte_range[0]}-{byte_range[1] - 1}")
    with urllib.request.urlopen(req) as r:
        return r.read()


def split_stories(text: str) -> list[str]:
    return [s.strip() for s in text.split(EOT) if s.strip()]


# --------------------------------------------------------------------------------------- data


def prepare(retrain_tokenizer: bool = False) -> dict:
    """Fetch, verify, tokenize. Writes data/dataset-v1.json the first time; verifies it after."""
    from tokenizers import Tokenizer, decoders, models, pre_tokenizers, trainers

    CACHE.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    pinned = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else None
    raw_train, raw_valid = CACHE / "train-slice.txt", CACHE / "valid.txt"
    if not raw_train.exists():
        print(f"fetching the first {TRAIN_BYTES:,} bytes of {TRAIN_FILE} @ {REVISION[:8]}", flush=True)
        blob = fetch(TRAIN_FILE, (0, TRAIN_BYTES))
        assert len(blob) == TRAIN_BYTES, f"range request returned {len(blob)} bytes"
        blob = blob[: blob.rfind(EOT.encode()) + len(EOT)]  # end on a whole story
        raw_train.write_bytes(blob)
    if not raw_valid.exists():
        print(f"fetching {VALID_FILE}", flush=True)
        raw_valid.write_bytes(fetch(VALID_FILE))
    train_bytes, valid_bytes = raw_train.read_bytes(), raw_valid.read_bytes()
    manifest = {
        "dataset": DATASET,
        "revision": REVISION,
        "license": LICENSE,
        "train": {
            "file": TRAIN_FILE,
            "bytesRequested": TRAIN_BYTES,
            "bytesKept": len(train_bytes),
            "sha256": sha256(train_bytes),
            "stories": len(split_stories(train_bytes.decode("utf-8"))),
        },
        "valid": {
            "file": VALID_FILE,
            "bytes": len(valid_bytes),
            "sha256": sha256(valid_bytes),
            "stories": len(split_stories(valid_bytes.decode("utf-8"))),
        },
    }
    assert manifest["valid"]["sha256"] == VALID_SHA256, "validation file does not match the Hub's published hash"
    if pinned:
        for part in ("train", "valid"):
            assert manifest[part]["sha256"] == pinned[part]["sha256"], f"{part} data does not match the pinned hash"
    if retrain_tokenizer or not TOKENIZER.exists():
        print(f"training a {VOCAB}-token byte-level BPE on the train slice", flush=True)
        tok = Tokenizer(models.BPE())
        tok.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
        tok.decoder = decoders.ByteLevel()
        trainer = trainers.BpeTrainer(
            vocab_size=VOCAB, special_tokens=[EOT], initial_alphabet=pre_tokenizers.ByteLevel.alphabet(), show_progress=False
        )
        tok.train_from_iterator(split_stories(train_bytes.decode("utf-8")), trainer=trainer)
        tok.save(str(TOKENIZER))
    tok_hash = sha256(TOKENIZER.read_bytes())
    if pinned:
        assert tok_hash == pinned["tokenizer"]["sha256"], "tokenizer does not match the pinned hash"
    tok = Tokenizer.from_file(str(TOKENIZER))
    eot = tok.token_to_id(EOT)
    for part, blob in (("train", train_bytes), ("valid", valid_bytes)):
        out = CACHE / f"{part}-v1.bin"
        if not out.exists():
            print(f"tokenizing {part}", flush=True)
            ids: list[int] = []
            for enc in tok.encode_batch(split_stories(blob.decode("utf-8"))):
                ids.extend(enc.ids)
                ids.append(eot)
            import array

            out.write_bytes(array.array("h", ids).tobytes())
        manifest[part]["tokens"] = out.stat().st_size // 2
    import tokenizers

    manifest["tokenizer"] = {
        "type": "byte-level BPE (Hugging Face tokenizers)",
        "vocabSize": tok.get_vocab_size(),
        "eotId": eot,
        "file": "data/tokenizer-v1.json",
        "sha256": tok_hash,
        "trainedOn": "the train slice above",
        "tokenizersVersion": tokenizers.__version__,
    }
    if pinned:
        for part in ("train", "valid"):
            assert manifest[part]["tokens"] == pinned[part]["tokens"], f"{part} token count differs from the pinned one"
    else:
        MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({p: {k: manifest[p][k] for k in ("stories", "tokens")} for p in ("train", "valid")}), flush=True)
    return manifest


def load_tokens(part: str):
    import torch

    blob = bytearray((CACHE / f"{part}-v1.bin").read_bytes())
    return torch.frombuffer(blob, dtype=torch.int16)


# --------------------------------------------------------------------------------------- device


def pick_device(name: str | None) -> str:
    import torch

    if name:
        return name
    return "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"


def device_name(device: str) -> str:
    import torch

    if device == "cuda":
        return torch.cuda.get_device_name(0)
    chip = platform.processor() or platform.machine()
    if platform.system() == "Darwin":
        chip = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True).stdout.strip() or chip
    return f"{chip} GPU (MPS)" if device == "mps" else f"{chip} CPU ({torch.get_num_threads()} threads)"


def sync(device: str) -> None:
    import torch

    if device == "cuda":
        torch.cuda.synchronize()
    elif device == "mps":
        torch.mps.synchronize()


def memory_bytes(device: str) -> int:
    """cuda: peak bytes allocated by tensors. mps: bytes the Metal driver holds for this process
    (includes the allocator's cache; sampled, so it is a high-water mark of the samples).
    cpu: peak resident memory of the whole process."""
    import torch

    if device == "cuda":
        return torch.cuda.max_memory_allocated()
    if device == "mps":
        return torch.mps.driver_allocated_memory()
    import resource

    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return rss if platform.system() == "Darwin" else rss * 1024


# --------------------------------------------------------------------------------------- train


def lr_at(step: int, steps: int, max_lr: float, min_lr: float, warmup: int) -> float:
    """Linear warmup to max_lr over `warmup` steps, then cosine decay to min_lr at the last step."""
    if step < warmup:
        return max_lr * (step + 1) / warmup
    progress = (step - warmup) / max(1, steps - 1 - warmup)
    return min_lr + 0.5 * (max_lr - min_lr) * (1 + math.cos(math.pi * min(1.0, progress)))


def train(
    seed: int,
    bug: str,
    purpose: str,
    steps: int | None = None,
    device: str | None = None,
    model_size: dict | None = None,
    batch_size: int | None = None,
    out: Path = RUNS,
    ckpt_every: int = 0,
    resume: bool = False,
    tag: str = "",
    stop_after: int | None = None,
    preset: str = "default",
) -> dict:
    import torch

    from tinygpt_model_v1 import BUGS, GPT, Config, flops_per_token, optimizer_groups

    assert bug in BUGS, bug
    hp = {**TRAIN, **PRESETS[preset]}
    hp["steps"] = steps or hp["steps"]
    hp["batch_size"] = batch_size or hp["batch_size"]
    dev = pick_device(device)
    cfg = Config(vocab_size=VOCAB, bug=bug, **(model_size or {}))
    B, T, n_steps = hp["batch_size"], cfg.block_size, hp["steps"]
    run_id = f"{purpose}-{bug}-s{seed}" + (f"-{tag}" if tag else "")

    train_ids, valid_ids = load_tokens("train"), load_tokens("valid")
    offsets = torch.arange(T + 1)
    # The validation set is the same fixed windows for every run, so seeds differ only in the model.
    n_eval = hp["eval_batches"] * B
    eval_starts = torch.arange(n_eval) * (T + 1)
    assert int(eval_starts[-1]) + T + 1 <= len(valid_ids)
    eval_windows = valid_ids[eval_starts[:, None] + offsets].long()

    torch.manual_seed(seed)  # seeds the CPU, CUDA and MPS generators: initialization
    gen = torch.Generator().manual_seed(seed)  # the order of training batches
    model = GPT(cfg).to(dev)
    opt = torch.optim.AdamW(optimizer_groups(model, hp["weight_decay"]), lr=hp["max_lr"], betas=hp["betas"])

    def batch():
        ix = torch.randint(len(train_ids) - T - 1, (B,), generator=gen)
        w = train_ids[ix[:, None] + offsets].long()
        return w[:, :-1].to(dev), w[:, 1:].to(dev)

    @torch.no_grad()
    def evaluate() -> float:
        model.eval()
        total = torch.zeros((), device=dev)
        for i in range(hp["eval_batches"]):
            w = eval_windows[i * B : (i + 1) * B].to(dev)
            total += model(w[:, :-1], w[:, 1:])[1]
        model.train()
        return float(total) / hp["eval_batches"]

    hist = {"evalSteps": [], "valLoss": [], "trainLoss": [], "gradNorm": [], "windowSeconds": [], "lr": []}
    start_step, train_s, eval_s, resumed, wall_prev, logit_sd = 0, 0.0, 0.0, False, 0.0, None
    ckpt = CACHE / "ckpt" / f"{run_id}.pt"
    if resume and ckpt.exists():
        state = torch.load(ckpt, map_location=dev, weights_only=False)
        model.load_state_dict(state["model"])
        opt.load_state_dict(state["opt"])
        gen.set_state(state["gen"])
        torch.set_rng_state(state["cpu_rng"])
        hist, start_step, train_s, eval_s = state["hist"], state["step"], state["train_s"], state["eval_s"]
        resumed, wall_prev, logit_sd = True, state["wall"], state["logit_sd"]
        print(f"resumed {run_id} at step {start_step}", flush=True)

    def save(step: int) -> None:
        ckpt.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "model": model.state_dict(),
                "opt": opt.state_dict(),
                "gen": gen.get_state(),
                "cpu_rng": torch.get_rng_state(),
                "hist": hist,
                "step": step,
                "train_s": train_s,
                "eval_s": eval_s,
                "config": cfg.as_dict(),
                "train": hp,
                "logit_sd": logit_sd,
                "wall": wall_prev + time.perf_counter() - wall0,
            },
            ckpt,
        )

    load_start = os.getloadavg()[0] if hasattr(os, "getloadavg") else None
    started = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    wall0 = time.perf_counter()
    if start_step == 0:
        with torch.no_grad():  # how spread out are the logits at initialization? (for the ln V check)
            w = eval_windows[:B].to(dev)
            logit_sd = float(model(w[:, :-1])[0].float().std())
    mem_peak = 0
    pending: list = []
    sync(dev)
    t_window = time.perf_counter()
    model.train()
    diverged_at = None
    for step in range(start_step, n_steps + 1):
        if (step % hp["eval_every"] == 0 or step == n_steps) and not (resumed and step == start_step):
            sync(dev)
            t0 = time.perf_counter()
            train_s += t0 - t_window
            v = evaluate()
            eval_s += time.perf_counter() - t0
            hist["evalSteps"].append(step)
            hist["valLoss"].append(v if math.isfinite(v) else None)
            print(f"  {run_id} step {step:5d}  val {v:.4f}  ({time.perf_counter() - wall0:.0f}s)", flush=True)
            if not math.isfinite(v):
                diverged_at = step
                break
            if ckpt_every and step and (step % ckpt_every == 0 or step == n_steps):
                save(step)
            if stop_after is not None and step >= stop_after and step < n_steps:
                save(step)  # a deliberate stop, as when a Colab session ends: rerun with resume to continue
                print(f"{run_id}: stopped at step {step}; checkpoint {ckpt}", flush=True)
                return {"runId": run_id, "stoppedAt": step, "checkpoint": str(ckpt)}
            t_window = time.perf_counter()
        if step == n_steps:
            break
        lr = lr_at(step, n_steps, hp["max_lr"], hp["min_lr"], hp["warmup_steps"])
        for g in opt.param_groups:
            g["lr"] = lr
        if bug != "no_zero_grad":
            opt.zero_grad(set_to_none=True)
        x, y = batch()
        _, loss = model(x, y)
        loss.backward()
        norm = torch.nn.utils.clip_grad_norm_(model.parameters(), hp["grad_clip"])
        opt.step()
        pending.append((loss.detach(), norm.detach(), lr))
        if len(pending) == 10 or step + 1 == n_steps or (step + 1) % hp["eval_every"] == 0:
            losses = torch.stack([p[0] for p in pending]).tolist()  # one device sync per window
            norms = torch.stack([p[1] for p in pending]).tolist()
            now = time.perf_counter()
            hist["windowSeconds"].append([len(pending), now - t_window])
            train_s += now - t_window
            t_window = now
            hist["trainLoss"] += [round(x_, 5) for x_ in losses]
            hist["gradNorm"] += [round(x_, 5) for x_ in norms]
            hist["lr"] += [p[2] for p in pending]
            pending = []
            mem_peak = max(mem_peak, memory_bytes(dev))
    sync(dev)
    wall = time.perf_counter() - wall0
    trained_steps = len(hist["trainLoss"])
    per_step = sorted(s / n for n, s in hist["windowSeconds"] if n)
    row = {
        "runId": run_id,
        "purpose": purpose,
        "bug": bug,
        "seed": seed,
        "device": dev,
        "deviceName": device_name(dev),
        "dtype": "float32",
        "torch": torch.__version__,
        "python": platform.python_version(),
        "config": cfg.as_dict(),
        "preset": preset,
        "train": {k: (list(v) if isinstance(v, tuple) else v) for k, v in hp.items()},
        "params": model.num_params(),
        "flopsPerToken": flops_per_token(cfg),
        "tokensPerStep": B * T,
        "started": started,
        "wallSeconds": wall_prev + wall,
        "trainSeconds": train_s,
        "evalSeconds": eval_s,
        "stepsDone": trained_steps,
        "divergedAtStep": diverged_at,
        "tokensPerSecond": trained_steps * B * T / train_s if train_s else None,
        "medianSecondsPerStep": per_step[len(per_step) // 2] if per_step else None,
        "memoryBytes": mem_peak,
        "memoryKind": {
            "cuda": "peak allocated by tensors",
            "mps": "Metal driver allocation, max of samples",
            "cpu": "peak resident set of the process",
        }[dev],
        "loadAverage": [load_start, os.getloadavg()[0] if hasattr(os, "getloadavg") else None],
        "lnV": math.log(VOCAB),
        "initLogitSd": logit_sd,
        "initValLoss": hist["valLoss"][0],
        "finalValLoss": hist["valLoss"][-1],
        **hist,
    }
    if out:
        out.parent.mkdir(exist_ok=True)
        with out.open("a") as f:
            f.write(json.dumps(row) + "\n")
    print(f"{run_id}: final val {row['finalValLoss']}, {row['tokensPerSecond'] or 0:,.0f} tokens/s, {wall / 60:.1f} min", flush=True)
    return row


# --------------------------------------------------------------------------------------- summary


def load_runs(path: Path = RUNS) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()] if path.exists() else []


def _padded(row: dict, n: int) -> list[float]:
    """A diverged run's missing evaluations count as infinitely bad."""
    vals = [math.inf if v is None else v for v in row["valLoss"]]
    return vals + [math.inf] * (n - len(vals))


def summarize(path: Path = RUNS, write: bool = True) -> dict:
    runs = load_runs(path)
    healthy = sorted((r for r in runs if r["purpose"] == "healthy"), key=lambda r: r["seed"])
    out: dict = {"source": path.name}
    if not healthy:
        return out
    h0 = healthy[0]
    steps = h0["evalSteps"]
    curves = [r["valLoss"] for r in healthy]
    b = S.band(curves)
    finals = [r["finalValLoss"] for r in healthy]
    m, lo, hi = S.t_interval(finals)
    _, plo, phi = S.prediction_interval(finals)
    mi = lambda xs: {"mean": S.mean(xs), "min": min(xs), "max": max(xs)}  # noqa: E731
    out["model"] = {"config": h0["config"], "params": h0["params"], "flopsPerToken": h0["flopsPerToken"], "train": h0["train"]}
    out["initialLoss"] = {
        "lnV": h0["lnV"],
        "measured": {r["seed"]: r["initValLoss"] for r in healthy},
        "logitSd": {r["seed"]: r["initLogitSd"] for r in healthy},
        "predicted": {r["seed"]: S.initial_loss(h0["config"]["vocab_size"], r["initLogitSd"]) for r in healthy},
    }
    out["healthy"] = {
        "device": h0["device"],
        "deviceName": h0["deviceName"],
        "seeds": [r["seed"] for r in healthy],
        "evalSteps": steps,
        "band": b,
        "finalValLoss": {
            "values": finals,
            "mean": m,
            "sd": S.sd(finals),
            "ci95": [lo, hi],
            "pi95": [plo, phi],
            "interval": "Student t, n - 1 = 4 degrees of freedom",
        },
        "minutes": mi([r["wallSeconds"] / 60 for r in healthy]),
        "trainMinutes": mi([r["trainSeconds"] / 60 for r in healthy]),
        "tokensPerSecond": mi([r["tokensPerSecond"] for r in healthy]),
        "medianSecondsPerStep": mi([r["medianSecondsPerStep"] for r in healthy]),
        "memoryBytes": mi([r["memoryBytes"] for r in healthy]),
        "memoryKind": h0["memoryKind"],
        "loadAverage": [r["loadAverage"] for r in healthy],
        "achievedTflops": mi([r["tokensPerSecond"] * r["flopsPerToken"] / 1e12 for r in healthy]),
    }
    # False alarms: healthy runs the band never saw. Each held-out healthy control against the
    # 5-seed band, and each healthy seed against the band of the other four (leave one out).
    controls = []
    for r in runs:
        if r["purpose"] == "control" and r["evalSteps"] == steps:
            controls.append(
                {
                    "seed": r["seed"],
                    "flag": S.first_flag(_padded(r, len(steps)), b["piLow"], b["piHigh"], steps),
                    "finalValLoss": r["finalValLoss"],
                    "finalOutsidePi": not plo <= r["finalValLoss"] <= phi,
                }
            )
    loo = []
    for i, r in enumerate(healthy):
        others = [c for j, c in enumerate(curves) if j != i]
        bo = S.band(others)
        loo.append({"seed": r["seed"], "flag": S.first_flag(r["valLoss"], bo["piLow"], bo["piHigh"], steps)})
    out["falseAlarms"] = {
        "rule": "flag a run once its validation loss is outside the healthy 95% prediction band, "
        "on the same side, at 2 evaluations in a row",
        "heldOutControls": controls,
        "leaveOneOut": loo,
    }
    bugs: dict = {}
    for r in runs:
        if r["purpose"] != "bug" or r["evalSteps"][: len(steps)] != steps[: len(r["evalSteps"])]:
            continue
        vals = _padded(r, len(steps))
        flag = S.first_flag(vals, b["piLow"], b["piHigh"], steps)
        bugs.setdefault(r["bug"], []).append(
            {
                "seed": r["seed"],
                "flag": flag,
                "finalValLoss": r["finalValLoss"],
                "divergedAtStep": r["divergedAtStep"],
                "finalOutsidePi": r["finalValLoss"] is None or not plo <= r["finalValLoss"] <= phi,
                "valLoss": r["valLoss"],
                "initValLoss": r["initValLoss"],
                "minutes": r["wallSeconds"] / 60,
            }
        )
    for name, rs in bugs.items():
        fired = [x["flag"]["step"] for x in rs if x["flag"]]
        bugs[name] = {
            "runs": sorted(rs, key=lambda x: x["seed"]),
            "caught": len(fired),
            "of": len(rs),
            "flagSteps": sorted(fired),
            "sides": sorted({x["flag"]["side"] for x in rs if x["flag"]}),
        }
    out["bugs"] = bugs
    reruns = [r for r in runs if r["purpose"] == "rerun"]
    if reruns:
        rr = reruns[0]
        orig = next(r for r in healthy if r["seed"] == rr["seed"])
        diffs = [abs(a - c) for a, c in zip(rr["valLoss"], orig["valLoss"])]
        out["sameSeedRerun"] = {
            "seed": rr["seed"],
            "device": rr["device"],
            "finalValLoss": [orig["finalValLoss"], rr["finalValLoss"]],
            "absFinalDiff": abs(rr["finalValLoss"] - orig["finalValLoss"]),
            "maxAbsDiffAlongCurve": max(diffs),
            "firstDifferentStep": next((s for s, d in zip(steps, diffs) if d > 0), None),
            "seedSdOfFinal": S.sd(finals),
        }
    timing = [r for r in runs if r["purpose"] == "timing"]
    out["timing"] = [
        {
            "device": r["device"],
            "deviceName": r["deviceName"],
            "steps": r["stepsDone"],
            "tokensPerSecond": r["tokensPerSecond"],
            "medianSecondsPerStep": r["medianSecondsPerStep"],
            "wallSeconds": r["wallSeconds"],
            "minutesForFullRunAtThisRate": TRAIN["steps"] * r["medianSecondsPerStep"] / 60 if r["medianSecondsPerStep"] else None,
            "memoryBytes": r["memoryBytes"],
            "memoryKind": r["memoryKind"],
            "loadAverage": r["loadAverage"],
        }
        for r in timing
    ]
    out["colab"] = "not yet run: submit receipts from train_tiny_gpt_v1.ipynb (T4 and L4) and add them under receipts/colab/"
    if write:
        SUMMARY.write_text(json.dumps(out, indent=1) + "\n")
    return out


def receipt() -> None:
    import importlib.metadata as md

    s = json.loads(SUMMARY.read_text())
    runs = load_runs()
    manifest = json.loads(MANIFEST.read_text())
    dates = sorted({r["started"][:10] for r in runs})
    rec = {
        "experiment": "train-a-tiny-gpt-on-colab v1 (feasibility pilot P1)",
        "ranOn": dates,
        "where": f"{platform.system()} {platform.machine()}, Python {platform.python_version()}",
        "devices": sorted({f"{r['deviceName']} [{r['device']}, {r['dtype']}]" for r in runs}),
        "packages": {p: md.version(p) for p in ("torch", "tokenizers", "numpy")},
        "dataset": manifest,
        "model": s["model"],
        "runs": {p: sum(r["purpose"] == p for r in runs) for p in sorted({r["purpose"] for r in runs})},
        "minutes": {r["runId"]: round(r["wallSeconds"] / 60, 2) for r in runs},
        "tokensPerSecond": {r["runId"]: round(r["tokensPerSecond"]) for r in runs},
        "loadAverage1minStartEnd": {r["runId"]: [round(x, 2) for x in r["loadAverage"]] for r in runs},
        "timings": "indicative only: a shared machine, with other sessions' test suites and browsers running; "
        "the 1-minute load average at the start and end of each run is above. Authoritative timings come from the Colab receipt.",
        "totalGpuMinutes": round(sum(r["wallSeconds"] for r in runs if r["device"] != "cpu") / 60, 1),
        "costUsd": 0.0,
        "colab": "slot: T4 and L4 receipts from train_tiny_gpt_v1.ipynb go in receipts/colab/; none recorded yet",
        "note": "Local hardware, no API, no paid compute. Timings depend on the machine and on what else runs on it; "
        "each run records the load average at its start and end.",
    }
    RECEIPT.parent.mkdir(exist_ok=True)
    RECEIPT.write_text(json.dumps(rec, indent=2) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prepare", "train", "summarize", "receipt"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--bug", default="none")
    ap.add_argument("--purpose", default="healthy", choices=["healthy", "control", "bug", "rerun", "timing", "trial"])
    ap.add_argument("--steps", type=int)
    ap.add_argument("--batch-size", type=int)
    ap.add_argument("--device")
    ap.add_argument("--out", default=str(RUNS))
    ap.add_argument("--ckpt-every", type=int, default=0)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--tag", default="")
    ap.add_argument("--preset", default="default", choices=sorted(PRESETS))
    ap.add_argument("--stop-after", type=int, help="checkpoint and stop at this evaluation step")
    ap.add_argument("--retrain-tokenizer", action="store_true")
    a = ap.parse_args()
    if a.cmd == "prepare":
        prepare(a.retrain_tokenizer)
    elif a.cmd == "train":
        train(
            a.seed,
            a.bug,
            a.purpose,
            a.steps,
            a.device,
            batch_size=a.batch_size,
            out=Path(a.out) if a.out else None,
            ckpt_every=a.ckpt_every,
            resume=a.resume,
            tag=a.tag,
            stop_after=a.stop_after,
            preset=a.preset,
        )
    elif a.cmd == "summarize":
        summarize()
    else:
        receipt()


if __name__ == "__main__":
    main()
