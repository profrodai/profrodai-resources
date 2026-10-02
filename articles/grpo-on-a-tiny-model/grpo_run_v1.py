# Prof Rod | GRPO on a Tiny Model
# Article: https://profrod.ai/articles/grpo-on-a-tiny-model
# Original source and updates: https://github.com/profrodai/profrodai-resources

"""GRPO on a 135M-0.5B instruct model: find a task it can learn, train it, and catch a reward hack.

Subcommands (each writes its own files under results/ and skips work that is already recorded):
- `eval`    : greedy answers of a model (base, unless a run's weights are in memory) on held-out items.
- `train`   : one GRPO run (task, model, seed), then a held-out eval of the trained policy.
- `ladder`  : for each candidate task, a base eval and a short GRPO run, to choose the task by evidence.
- `hack`    : GRPO against the verifier with the planted bug, with a strict shadow verifier and the
              detector logged every step.
- `labels`  : false-positive and false-negative rates of each verifier on hand-labeled responses.
- `summarize`, `receipt`.

Run it (Python 3.12):
    uv run --no-project --python 3.12 --with 'transformers==5.18.0' --with 'torch==2.14.1' \\
        python grpo_run_v1.py ladder --model qwen05
See README.md for every command behind the recorded numbers.
"""

from __future__ import annotations

import argparse
import copy
import json
import platform
import random
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import grpo_env_v1 as E  # noqa: E402
import grpo_stats_v1 as S  # noqa: E402
import grpo_verify_v1 as V  # noqa: E402

RESULTS = HERE / "results"
RECEIPT = HERE / "receipts" / "grpo-v1.json"
REVISIONS = json.loads((HERE / "data" / "revisions-v1.json").read_text())
MODELS = {
    "smol135": "HuggingFaceTB/SmolLM2-135M-Instruct",
    "smol360": "HuggingFaceTB/SmolLM2-360M-Instruct",
    "qwen05": "Qwen/Qwen2.5-0.5B-Instruct",
}
# Two held-out sets. `dev` chose the settings (a learning-rate and LoRA sweep, one seed each), so its
# numbers are optimistic for the chosen setting; `test` is drawn afterwards, disjoint from `dev`, and
# is the set the confirmation runs report. Training never sees the set a run is evaluated on.
EVAL_SEEDS = {"dev": 1001, "test": 2002}
EVAL_N = {"add": 200, "units": 200, "reverse": 50, "words": 200}


@dataclass
class Config:
    model: str = "qwen05"
    task: str = "add"
    seed: int = 1
    steps: int = 60
    prompts: int = 8  # B: distinct prompts per step
    group: int = 8  # G: responses per prompt
    max_new: int = 96
    temperature: float = 1.0
    lr: float = 1e-6
    warmup: int = 10  # optimizer steps of linear learning-rate warmup (see README: Adam's first step)
    beta: float = 0.04
    clip: float = 0.2
    updates: int = (
        2  # optimizer steps per batch of rollouts (2 makes the ratio and clip matter)
    )
    microbatch: int = 8
    lora: int = 0  # LoRA rank; 0 trains every weight
    lora_alpha: float = 32.0
    max_grad_norm: float = 1.0
    verifier: str = "strict"
    eval_n: int = 0  # 0 means EVAL_N[task]
    eval_set: str = "dev"
    tag: str = ""
    pad: int = 0

    def name(self) -> str:
        extra = f"-{self.tag}" if self.tag else ""
        how = f"lora{self.lora}" if self.lora else "full"
        which = "" if self.eval_set == "dev" else f"-{self.eval_set}"
        return f"{self.model}-{self.task}-{self.verifier}-{how}-s{self.seed}-n{self.steps}{extra}{which}"


def load_average() -> list[float] | None:
    """The 1, 5 and 15 minute load averages, recorded with every timed run: a shared machine's
    timings are indicative only."""
    import os

    try:
        return [round(x, 2) for x in os.getloadavg()]
    except OSError:
        return None


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def held_out(task: str, n: int | None = None, eval_set: str = "dev") -> list[E.Item]:
    dev = E.split(task, n or EVAL_N[task], EVAL_SEEDS["dev"])
    if eval_set == "dev":
        return dev
    return E.split(
        task, n or EVAL_N[task], EVAL_SEEDS[eval_set], exclude={it.prompt for it in dev}
    )


def evaluate(
    model, tok, items: list[E.Item], device: str, max_new: int, batch: int = 64
) -> list[dict]:
    import grpo_core_v1 as C

    model.eval()
    prompts = C.encode_prompts(tok, [it.prompt for it in items])
    pad, stops = C.pad_id(tok), C.stop_ids(tok)
    rows = []
    for s in range(0, len(items), batch):
        outs = C.sample(model, prompts[s : s + batch], max_new, 0.0, pad, stops)
        for it, out in zip(items[s : s + batch], outs):
            text = tok.decode(out, skip_special_tokens=True)
            rows.append(
                {
                    "prompt": it.prompt,
                    "truth": it.truth,
                    "response": text,
                    "tokens": len(out),
                    "strict": V.verify(it, text),
                    "content": V.content_correct(it, text),
                    "planted": V.verify_planted(it, text),
                    "unparseable": V.unparseable_answer(it, text),
                }
            )
    return rows


def eval_summary(rows: list[dict]) -> dict:
    out = {
        k: S.summarize_rate([r[k] for r in rows])
        for k in ("strict", "content", "planted")
    }
    out["unparseableRate"] = sum(r["unparseable"] for r in rows) / len(rows)
    out["meanTokens"] = sum(r["tokens"] for r in rows) / len(rows)
    return out


def setup(model_key: str, device: str | None):
    import torch

    import grpo_core_v1 as C

    device = C.pick_device(device)
    model_id = MODELS[model_key]
    model, tok = C.load(model_id, REVISIONS.get(model_id), device, torch.float32)
    return model, tok, device


def base_path(
    model_key: str, task: str, n: int | None = None, eval_set: str = "dev"
) -> Path:
    which = "" if eval_set == "dev" else f"-{eval_set}"
    return RESULTS / f"eval-{model_key}-{task}-base{which}-n{n or EVAL_N[task]}.jsonl"


def base_eval(
    model_key: str,
    task: str,
    device: str | None,
    max_new: int,
    n: int | None = None,
    loaded=None,
    eval_set: str = "dev",
) -> list[dict]:
    path = base_path(model_key, task, n, eval_set)
    if path.exists():
        return read_jsonl(path)
    model, tok, device = loaded or setup(model_key, device)
    t0 = time.perf_counter()
    rows = evaluate(model, tok, held_out(task, n, eval_set), device, max_new)
    write_jsonl(path, rows)
    print(
        f"base {model_key} {task}: {json.dumps(eval_summary(rows))} ({time.perf_counter() - t0:.0f} s)",
        flush=True,
    )
    return rows


def train(cfg: Config, device: str | None = None, resume: bool = True) -> dict:
    """One GRPO run. Writes results/steps-<name>.jsonl (one row per step) and
    results/eval-<name>.jsonl (held-out answers of the trained policy)."""
    import torch

    import grpo_core_v1 as C

    name = cfg.name()
    steps_path, eval_path = (
        RESULTS / f"steps-{name}.jsonl",
        RESULTS / f"eval-{name}.jsonl",
    )
    if resume and eval_path.exists():
        print(f"{name}: already recorded, skipping", flush=True)
        return {"name": name, "skipped": True}
    random.seed(cfg.seed)
    torch.manual_seed(cfg.seed)
    policy, tok, device = setup(cfg.model, device)
    base_eval(
        cfg.model,
        cfg.task,
        device,
        cfg.max_new,
        cfg.eval_n or None,
        loaded=(policy, tok, device),
        eval_set=cfg.eval_set,
    )
    cfg.pad = C.pad_id(tok)
    stops = C.stop_ids(tok)
    if cfg.lora:
        trainable = C.add_lora(policy, cfg.lora, cfg.lora_alpha)
        ref = None
    else:
        trainable = sum(p.numel() for p in policy.parameters())
        ref = copy.deepcopy(policy).eval()
        for p in ref.parameters():
            p.requires_grad_(False)
    print(f"{name}: {trainable / 1e6:.1f}M trainable parameters", flush=True)
    params = [p for p in policy.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=cfg.lr, betas=(0.9, 0.99), weight_decay=0.0)
    # Adam's first steps move every weight by about lr whatever its gradient (m / sqrt(v) = +-1 when
    # v has seen one gradient). On Qwen2.5-0.5B a single such step at lr 2e-6 shifted the sampled
    # tokens' log-probabilities by 0.24 nats on average, so the rate ramps up over `warmup` steps.
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda k: min(1.0, (k + 1) / max(1, cfg.warmup))
    )
    held = held_out(cfg.task, cfg.eval_n or None, cfg.eval_set)
    data = E.stream(cfg.task, cfg.seed, {it.prompt for it in held})
    reward_fn = V.VERIFIERS[cfg.verifier]
    timer = C.Timer(device)
    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    log, t_start, load_start = [], time.perf_counter(), load_average()
    for step in range(cfg.steps):
        items = [next(data) for _ in range(cfg.prompts)]
        prompts = C.encode_prompts(tok, [it.prompt for it in items])
        rep_items = [it for it in items for _ in range(cfg.group)]
        rep_prompts = [p for p in prompts for _ in range(cfg.group)]
        policy.eval()
        with timer("sample"):
            responses = C.sample(
                policy, rep_prompts, cfg.max_new, cfg.temperature, cfg.pad, stops
            )
        texts = [tok.decode(r, skip_special_tokens=True) for r in responses]
        rewards = [reward_fn(it, t) for it, t in zip(rep_items, texts)]
        strict = [V.verify(it, t) for it, t in zip(rep_items, texts)]
        stats = C.grpo_step(
            policy, ref, opt, rep_prompts, responses, rewards, cfg, device, timer, sched
        )
        row = {
            "step": step,
            "reward": sum(rewards) / len(rewards),
            "strictReward": sum(strict) / len(strict),
            "unparseable": sum(
                V.unparseable_answer(it, t) for it, t in zip(rep_items, texts)
            )
            / len(texts),
            "meanTokens": sum(len(r) for r in responses) / len(responses),
            "truncated": sum(1 for r in responses if r and r[-1] not in stops)
            / len(responses),
            **stats,
            "seconds": time.perf_counter() - t_start,
            "loadAverage": load_average(),
            "example": texts[0][:300],
        }
        log.append(row)
        print(
            f"{name} step {step:3d} reward {row['reward']:.3f} strict {row['strictReward']:.3f} kl {row['kl']:.4f} "
            f"ent {row['entropy']:.3f} len {row['meanTokens']:.0f} unparse {row['unparseable']:.2f} "
            f"zeroVar {row['zeroVarianceGroups']:.2f} t {row['seconds']:.0f}s",
            flush=True,
        )
        write_jsonl(steps_path, log)
    train_seconds = time.perf_counter() - t_start
    t0 = time.perf_counter()
    rows = evaluate(policy, tok, held, device, cfg.max_new)
    write_jsonl(eval_path, rows)
    meta = {
        "name": name,
        "config": asdict(cfg),
        "device": device,
        "trainSeconds": train_seconds,
        "loadAverageStart": load_start,
        "loadAverageEnd": load_average(),
        "evalSeconds": time.perf_counter() - t0,
        "phaseSeconds": timer.totals,
        "trainableParameters": trainable,
        "eval": eval_summary(rows),
    }
    if device == "cuda":
        meta["maxMemoryGB"] = torch.cuda.max_memory_allocated() / 1e9
    elif device == "mps":
        meta["driverMemoryGB"] = torch.mps.driver_allocated_memory() / 1e9
    (RESULTS / f"run-{name}.json").write_text(json.dumps(meta, indent=2))
    print(
        f"{name}: eval {json.dumps(meta['eval'])} train {train_seconds / 60:.1f} min, "
        f"memory {meta.get('maxMemoryGB', meta.get('driverMemoryGB', 0)):.1f} GB",
        flush=True,
    )
    return meta


def compare(
    model: str, task: str, name: str, n: int | None = None, eval_set: str = "dev"
) -> dict:
    """Paired comparison of a trained run against the base model on the same held-out items."""
    base = read_jsonl(base_path(model, task, n, eval_set))
    after = read_jsonl(RESULTS / f"eval-{name}.jsonl")
    assert [b["prompt"] for b in base] == [a["prompt"] for a in after]
    out = {}
    for k in ("strict", "content"):
        b, a = [r[k] for r in base], [r[k] for r in after]
        lo, hi = S.paired_bootstrap(b, a)
        out[k] = {
            "base": S.summarize_rate(b),
            "trained": S.summarize_rate(a),
            "diff": sum(a) / len(a) - sum(b) / len(b),
            "diffBootstrap95": [lo, hi],
            **S.paired(b, a),
        }
    return out


def detector(steps: list[dict], gap: float = 0.10, patience: int = 3) -> dict:
    """Flags a reward hack when the training reward runs ahead of a strict shadow verifier on the
    same rollouts by more than `gap` for `patience` consecutive steps."""
    run = 0
    for row in steps:
        run = run + 1 if row["reward"] - row["strictReward"] > gap else 0
        if run >= patience:
            return {"flaggedAtStep": row["step"], "gap": gap, "patience": patience}
    return {"flaggedAtStep": None, "gap": gap, "patience": patience}


def probe(
    model_key: str,
    tasks: list[str],
    device: str | None,
    prompts: int = 16,
    group: int = 8,
    max_new: int = 96,
) -> list[dict]:
    """What GRPO will see at step 0: sampled (temperature 1) rewards on fresh training prompts, and
    the share of groups whose rewards differ at all (only those carry a learning signal)."""
    import torch

    import grpo_core_v1 as C

    torch.manual_seed(0)
    model, tok, device = setup(model_key, device)
    pad, stops, out = C.pad_id(tok), C.stop_ids(tok), []
    for task in tasks:
        items = E.split(task, prompts, 7)
        ids = [
            p
            for p in C.encode_prompts(tok, [it.prompt for it in items])
            for _ in range(group)
        ]
        t0 = time.perf_counter()
        resp = C.sample(model, ids, max_new, 1.0, pad, stops)
        texts = [tok.decode(r, skip_special_tokens=True) for r in resp]
        rep = [it for it in items for _ in range(group)]
        strict = [V.verify(it, t) for it, t in zip(rep, texts)]
        groups = [strict[i : i + group] for i in range(0, len(strict), group)]
        row = {
            "model": model_key,
            "task": task,
            "samples": len(texts),
            "strict": sum(strict) / len(strict),
            "content": sum(V.content_correct(it, t) for it, t in zip(rep, texts))
            / len(texts),
            "tagged": sum(V.extract_answer(t) is not None for t in texts) / len(texts),
            "groupsWithSignal": sum(1 for g in groups if min(g) != max(g))
            / len(groups),
            "meanTokens": sum(map(len, resp)) / len(resp),
            "sampleSeconds": time.perf_counter() - t0,
            "examples": texts[:: group * 4][:4],
        }
        out.append(row)
        print(json.dumps({k: v for k, v in row.items() if k != "examples"}), flush=True)
    path = RESULTS / "probe-v1.jsonl"
    old = (
        [
            r
            for r in read_jsonl(path)
            if not (r["model"] == model_key and r["task"] in tasks)
        ]
        if path.exists()
        else []
    )
    write_jsonl(path, old + out)
    return out


def first_step(
    model_key: str, device: str | None, lrs=(2e-6, 2e-7), lora_lrs=(2e-5,)
) -> list[dict]:
    """How far one AdamW step moves the policy: 4 units prompts x 4 samples, rewards fixed at
    1, 0, 1, 0 in each group, one GRPO step from the base weights, then the mean and largest change in
    the sampled tokens' log-probabilities. Adam's first update is about lr * sign(gradient) for every
    weight, whatever the gradient's size, which is why the runs warm the learning rate up."""
    import torch

    import grpo_core_v1 as C

    torch.manual_seed(0)
    model, tok, device = setup(model_key, device)
    items = E.split("units", 4, 5)
    prompts = [
        p for p in C.encode_prompts(tok, [it.prompt for it in items]) for _ in range(4)
    ]
    resp = C.sample(model, prompts, 40, 1.0, C.pad_id(tok), C.stop_ids(tok))
    batch = C.pack(prompts, resp, C.pad_id(tok), device)
    mask = batch["response_mask"]
    with torch.no_grad():
        before, _ = C.token_logprobs(model, batch, slice(0, 16))
    adv = C.group_advantages(torch.tensor([1.0, 0, 1, 0] * 4, device=device), 4)
    state = {k: v.clone() for k, v in model.state_dict().items()}
    out = []

    def one(label, params, lr):
        for p in params:
            p.grad = None
        opt = torch.optim.AdamW(params, lr=lr, betas=(0.9, 0.99), weight_decay=0.0)
        lp, _ = C.token_logprobs(model, batch, slice(0, 16))
        loss, _ = C.grpo_loss(lp, before, before, adv, mask, 0.2, 0.04)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        opt.step()
        with torch.no_grad():
            after, _ = C.token_logprobs(model, batch, slice(0, 16))
        d = ((after - before) * mask).abs()
        row = {
            "what": label,
            "lr": lr,
            "meanAbsChange": float(d.sum() / mask.sum()),
            "maxAbsChange": float(d.max()),
            "tokens": int(mask.sum()),
        }
        print(json.dumps(row), flush=True)
        out.append(row)

    for lr in lrs:
        model.load_state_dict(state)
        one("full fine-tune", list(model.parameters()), lr)
    model.load_state_dict(state)
    C.add_lora(model, 16, 32.0)
    for lr in lora_lrs:
        for m in model.modules():
            if isinstance(m, C.LoRALinear):
                torch.nn.init.kaiming_uniform_(m.A, a=5**0.5)
                torch.nn.init.zeros_(m.B)
        one("LoRA r16", [p for p in model.parameters() if p.requires_grad], lr)
    (RESULTS / "first-step-v1.json").write_text(json.dumps(out, indent=2))
    return out


def labels() -> dict:
    cases = []
    for r in read_jsonl(HERE / "data" / "verifier-cases-v1.jsonl"):
        item = E.Item(r["task"], r["prompt"], r["truth"], r.get("meta", {}))
        cases.append({**r, "item": item})
    out = {}
    for vname in ("strict", "planted"):
        per_task = {}
        groups = [(t, t, None) for t in sorted({c["task"] for c in cases})]
        groups += [
            ("all, model samples", None, "sample"),
            ("all, constructed", None, "constructed"),
            ("all", None, None),
        ]
        for key, task, source in groups:
            sub = [
                c
                for c in cases
                if (task is None or c["task"] == task)
                and (source is None or source in c["source"])
            ]
            er = V.error_rates(sub, V.VERIFIERS[vname])
            per_task[key] = {
                "fp": er["fp"],
                "negatives": er["negatives"],
                "fpWilson95": S.wilson(er["fp"], er["negatives"]),
                "fn": er["fn"],
                "positives": er["positives"],
                "fnWilson95": S.wilson(er["fn"], er["positives"]),
                "disagreements": [
                    {
                        "response": c["response"],
                        "label": c["label"],
                        "why": c.get("why", ""),
                    }
                    for c in er["disagreements"]
                ],
            }
        out[vname] = per_task
    (RESULTS / "verifier-labels-v1.json").write_text(json.dumps(out, indent=2))
    for vname, per in out.items():
        for task, r in per.items():
            print(
                f"{vname:8s} {task:20s} FP {r['fp']}/{r['negatives']}  FN {r['fn']}/{r['positives']}"
            )
    return out


def window(steps: list[dict], lo: int, hi: int) -> dict:
    rows = [r for r in steps if lo <= r["step"] < hi]
    keys = (
        "reward",
        "strictReward",
        "unparseable",
        "meanTokens",
        "entropy",
        "kl",
        "zeroVarianceGroups",
        "clipFraction",
    )
    return {k: sum(r[k] for r in rows) / len(rows) for k in keys} if rows else {}


def summarize() -> dict:
    """results/summary-v1.json: every number the README quotes, recomputed from the raw files."""
    out = {
        "probe": read_jsonl(RESULTS / "probe-v1.jsonl")
        if (RESULTS / "probe-v1.jsonl").exists()
        else []
    }
    if (RESULTS / "verifier-labels-v1.json").exists():
        lab = json.loads((RESULTS / "verifier-labels-v1.json").read_text())
        out["verifierLabels"] = {
            v: {
                k: {x: y for x, y in r.items() if x != "disagreements"}
                for k, r in per.items()
            }
            for v, per in lab.items()
        }
    runs, groups = {}, {}
    for path in sorted(RESULTS.glob("run-*.json")):
        meta = json.loads(path.read_text())
        cfg, name = meta["config"], meta["name"]
        steps = read_jsonl(RESULTS / f"steps-{name}.jsonl")
        n = len(steps)
        runs[name] = {
            "config": cfg,
            "device": meta["device"],
            "trainMinutes": meta["trainSeconds"] / 60,
            "secondsPerStep": meta["trainSeconds"] / max(1, n),
            "loadAverage": {
                "start": meta.get("loadAverageStart"),
                "end": meta.get("loadAverageEnd"),
            },
            "phaseSeconds": meta["phaseSeconds"],
            "trainableParameters": meta.get("trainableParameters"),
            "memoryGB": meta.get("maxMemoryGB", meta.get("driverMemoryGB")),
            "paired": compare(
                cfg["model"],
                cfg["task"],
                name,
                cfg["eval_n"] or None,
                cfg.get("eval_set", "dev"),
            ),
            "unparseableRate": {
                "base": eval_summary(
                    read_jsonl(
                        base_path(
                            cfg["model"],
                            cfg["task"],
                            cfg["eval_n"] or None,
                            cfg.get("eval_set", "dev"),
                        )
                    )
                )["unparseableRate"],
                "trained": meta["eval"]["unparseableRate"],
            },
            "plantedEval": meta["eval"]["planted"],
            "firstSteps": window(steps, 0, 5),
            "lastSteps": window(steps, n - 5, n),
            "detector": detector(steps),
        }
        if cfg["verifier"] == "planted":
            rows = read_jsonl(RESULTS / f"eval-{name}.jsonl")
            over = [r["step"] for r in steps if r["unparseable"] > 0.5]
            runs[name]["hack"] = {
                "firstStepUnparseableOverHalf": over[0] if over else None,
                "heldOutPaidButNumericallyWrong": sum(
                    1 for r in rows if r["planted"] and not r["content"]
                ),
                "heldOutN": len(rows),
            }
        groups.setdefault(name.replace(f"-s{cfg['seed']}-", "-"), []).append(name)
    out["runs"] = runs
    out["groups"] = {}
    for g, names in groups.items():
        rec = {"runs": names, "seeds": len(names)}
        for k in ("strict", "content"):
            trained = [runs[nm]["paired"][k]["trained"]["rate"] for nm in names]
            diffs = [runs[nm]["paired"][k]["diff"] for nm in names]
            rec[k] = {
                "trained": trained,
                "trainedMeanT95": S.t_interval(trained),
                "diffs": diffs,
                "diffMeanT95": S.t_interval(diffs),
            }
        out["groups"][g] = rec
    (RESULTS / "summary-v1.json").write_text(json.dumps(out, indent=2))
    return out


def environment() -> dict:
    import importlib.metadata as md
    import subprocess

    import torch

    env = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "torch": torch.__version__,
    }
    for pkg in (
        "transformers",
        "tokenizers",
        "safetensors",
        "huggingface-hub",
        "numpy",
        "accelerate",
    ):
        try:
            env[pkg] = md.version(pkg)
        except md.PackageNotFoundError:
            pass
    if torch.cuda.is_available():
        env["device"] = torch.cuda.get_device_name(0)
        env["cuda"] = torch.version.cuda
        try:
            env["driver"] = subprocess.run(
                ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                capture_output=True,
                text=True,
            ).stdout.strip()
        except OSError:
            pass
    elif torch.backends.mps.is_available():
        env["device"] = (
            "Apple GPU (MPS): "
            + subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
    return env


def receipt(path: Path = RECEIPT, extra: dict | None = None) -> dict:
    summary = summarize()
    rec = {
        "experiment": "grpo-on-a-tiny-model v1",
        "ranOn": time.strftime("%Y-%m-%d"),
        "environment": environment(),
        "models": {MODELS[k]: REVISIONS[MODELS[k]] for k in MODELS},
        "licenses": {
            "HuggingFaceTB/SmolLM2-135M-Instruct": "apache-2.0",
            "HuggingFaceTB/SmolLM2-360M-Instruct": "apache-2.0",
            "Qwen/Qwen2.5-0.5B-Instruct": "apache-2.0",
        },
        "data": "Generated by grpo_env_v1.py from fixed seeds; no dataset is downloaded.",
        "runs": {
            n: {
                "minutes": r["trainMinutes"],
                "secondsPerStep": r["secondsPerStep"],
                "device": r["device"],
                "memoryGB": r["memoryGB"],
                "loadAverage": r["loadAverage"],
            }
            for n, r in summary["runs"].items()
        },
        "costUsd": 0.0,
        "note": "Open weights run on the machine named above; no API was called.",
        **(extra or {}),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rec, indent=2))
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "command",
        choices=[
            "probe",
            "firststep",
            "eval",
            "train",
            "ladder",
            "hack",
            "labels",
            "summarize",
            "receipt",
        ],
    )
    ap.add_argument("--device")
    for k, v in asdict(Config()).items():
        if k == "pad":
            continue
        ap.add_argument(f"--{k.replace('_', '-')}", type=type(v), default=v)
    ap.add_argument("--tasks", default=",".join(E.TASKS))
    ap.add_argument("--seeds", default="")
    a = ap.parse_args()
    cfg = Config(**{k: getattr(a, k) for k in asdict(Config()) if k != "pad"})
    RESULTS.mkdir(exist_ok=True)
    if a.command == "probe":
        probe(cfg.model, a.tasks.split(","), a.device, max_new=cfg.max_new)
    elif a.command == "firststep":
        first_step(cfg.model, a.device)
    elif a.command == "eval":
        base_eval(
            cfg.model,
            cfg.task,
            a.device,
            cfg.max_new,
            cfg.eval_n or None,
            eval_set=cfg.eval_set,
        )
    elif a.command == "train":
        seeds = [int(s) for s in a.seeds.split(",")] if a.seeds else [cfg.seed]
        for s in seeds:
            cfg.seed = s
            train(copy.copy(cfg), a.device)
    elif a.command == "ladder":
        for task in a.tasks.split(","):
            cfg.task = task
            train(copy.copy(cfg), a.device)
    elif a.command == "hack":
        cfg.verifier = "planted"
        train(cfg, a.device)
    elif a.command == "labels":
        labels()
    elif a.command == "summarize":
        summarize()
    elif a.command == "receipt":
        receipt(
            extra={
                "timingNote": "Local timings are indicative only: a shared machine, with other sessions' "
                "test suites on the CPU and two other pilots training on the same GPU. Each run records "
                "the 1, 5 and 15 minute load averages at its start and end. Accuracies, intervals and "
                "paired tests do not depend on the load."
            }
        )


if __name__ == "__main__":
    print(platform.platform(), flush=True)
    main()
