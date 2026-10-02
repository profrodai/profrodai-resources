# Prof Rod | Post-Training, Measured: SFT Then DPO on a Colab T4
# Article: https://profrod.ai/articles/sft-then-dpo-on-a-colab-t4
# Original source and updates: https://github.com/profrodai/profrodai-resources

"""SFT, then DPO, on SmolLM2-360M (the base model), measured against the base model on the same
items. Written to run on a free Colab T4 in one session; validated on an Apple GPU (MPS).

The training code is ours, in plain PyTorch: transformers supplies the model, the tokenizer and
`generate` for decoding, and nothing else (no Trainer, no TRL).

The arms, all graded on the same test items (sftdpo_task_v1.py):
- `base-fewshot`: the base model with three worked examples in plain text. The fair baseline.
- `base-chatml`: the base model zero-shot in the chat template it has never seen.
- `sft`: full fine-tuning on worked solutions, loss on the assistant's tokens only.
- `dpo`: from each SFT checkpoint, 4 samples per fresh problem at temperature 1; a correct and an
  incorrect sample make a pair; DPO with beta 0.1 against the SFT model as the reference.
- The traps, each against `sft` with the same seed:
  - `trap-promptloss`: SFT with the loss on every token, prompt included.
  - `trap-sysprompt`: the SFT model, evaluated through SmolLM2-Instruct's chat template, which adds
    a default system prompt the model never saw in training.
  - `trap-nogenprompt`: the SFT model, evaluated without the `<|im_start|>assistant` line that
    starts its turn (`add_generation_prompt=False`).

Run it (Python 3.12):
    uv run --no-project --python 3.12 --with 'transformers==5.18.0' --with torch \\
        python sftdpo_run_v1.py all --size default
    uv run --no-project --python 3.12 python sftdpo_run_v1.py summarize
`--size quick` is a smoke test. Every finished run is appended to results/runs-v1.jsonl, and a
rerun skips it, so a stopped run resumes where it stopped.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import json
import math
import os
import platform
import random
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sftdpo_stats_v1 as S  # noqa: E402
import sftdpo_task_v1 as T  # noqa: E402

MODEL = "HuggingFaceTB/SmolLM2-360M"
REVISIONS: dict[str, str] = json.loads((HERE / "data" / "revisions-v1.json").read_text())
IM_START, IM_END, EOT = 1, 2, 0  # <|im_start|>, <|im_end|>, <|endoftext|> in SmolLM2's vocabulary
SMOL_SYSTEM = "You are a helpful AI assistant named SmolLM, trained by Hugging Face"
DATA_SEED = 20261002
PRECISIONS = {
    "fp32": "float32 weights, activations and AdamW state",
    "fp16": "float32 weights and AdamW state, float16 autocast with loss scaling",
    "bf16": "float32 weights and AdamW state, bfloat16 autocast",
}

SIZES = {
    # quick: a smoke test of every code path, minutes on any GPU.
    "quick": {"test": 100, "dev": 100, "sft": 400, "dpo": 160, "seeds": [0]},
    # default: what the article reports; sized for one free T4 session.
    "default": {"test": 1000, "dev": 300, "sft": 3000, "dpo": 1000, "seeds": [0, 1, 2]},
    # large: more items and seeds, for an L4 or a long session.
    "large": {"test": 2000, "dev": 300, "sft": 3000, "dpo": 2000, "seeds": [0, 1, 2, 3, 4]},
}
HP = {
    "operands": 3,
    "shots": 3,
    "maxNewTokens": 64,
    "evalBatch": 128,
    "sft": {"lr": 1e-4, "batch": 16, "epochs": 1, "warmup": 0.05, "clip": 1.0, "weightDecay": 0.0},
    "dpo": {
        "lr": 3e-6,
        "beta": 0.1,
        "batch": 16,
        "micro": 8,
        "epochs": 2,
        "warmup": 0.1,
        "clip": 1.0,
        "samples": 4,
        "temperature": 1.0,
    },
}


def load_average() -> list[float] | None:
    try:
        return [round(x, 2) for x in os.getloadavg()]
    except OSError:
        return None


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


class Lab:
    """One device, one tokenizer, the splits, and the results files. Every section method skips
    runs that are already recorded."""

    def __init__(
        self,
        size: str = "default",
        out: Path | str = HERE,
        device: str | None = None,
        ckpt: Path | str | None = None,
        mirror: Path | str | None = None,
        hp: dict | None = None,
        precision: str = "fp32",
    ):
        import torch
        from transformers import AutoTokenizer

        self.torch = torch
        self.size, self.cfg = size, SIZES[size]
        self.hp = json.loads(json.dumps(hp or HP))
        self.out = Path(out)
        self.results = self.out / "results"
        self.results.mkdir(parents=True, exist_ok=True)
        self.ckpt = Path(ckpt) if ckpt else self.out / "ckpt"
        self.mirror = Path(mirror) if mirror else None
        self.runs_path = self.results / "runs-v1.jsonl"
        self.gens_path = self.results / "generations-v1.jsonl"
        self._restore_from_mirror()
        self.device = device or (
            "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        )
        # Default: float32 everywhere. A T4 has no fast bfloat16, and float16 is unsafe for this
        # model: SmolLM2-360M's largest MLP outputs reach about 20,000 (`activations` measures it),
        # a third of float16's 65,504, and sampling under float16 autocast overflowed into NaN.
        # `fp16` (autocast with loss scaling) and `bf16` (autocast, Ampere or newer) are knobs.
        if precision not in PRECISIONS:
            raise ValueError(f"precision must be one of {sorted(PRECISIONS)}")
        self.precision = precision
        self.amp_dtype = {"fp32": None, "fp16": torch.float16, "bf16": torch.bfloat16}[precision]
        self.scale = precision == "fp16"
        self.revision = REVISIONS[MODEL]
        self.tok = AutoTokenizer.from_pretrained(MODEL, revision=self.revision)
        sizes = {k: self.cfg[k] for k in ("test", "dev", "sft", "dpo")} | {"shots": self.hp["shots"]}
        self.splits = T.make_splits(sizes, self.hp["operands"], DATA_SEED)
        self.eval_split = "test"
        self.started = time.perf_counter()
        self._peak = 0
        self._load_start = load_average()

    # ---------- bookkeeping ----------

    def records(self) -> dict[str, dict]:
        if not self.runs_path.exists():
            return {}
        return {r["id"]: r for r in map(json.loads, self.runs_path.read_text().splitlines())}

    def done(self, run_id: str) -> bool:
        return run_id in self.records()

    def save(self, record: dict, generations: list[dict] | None = None) -> None:
        # Load averages (1, 5, 15 min) at the start and end of the run: on a shared machine they
        # say how much the timing can be trusted. Accuracy does not depend on them.
        record |= {
            "size": self.size,
            "device": self.device,
            "finishedAt": now(),
            "loadStart": self._load_start,
            "loadEnd": load_average(),
        }
        with self.runs_path.open("a") as f:
            f.write(json.dumps(record) + "\n")
        if generations:
            with self.gens_path.open("a") as f:
                for g in generations:
                    f.write(json.dumps(g) + "\n")
        if self.mirror:
            self.mirror.mkdir(parents=True, exist_ok=True)
            for p in (self.runs_path, self.gens_path):
                if p.exists():
                    shutil.copy(p, self.mirror / p.name)
        print(
            f"[{self.minutes():6.1f} min total] {record['id']}: {record.get('accuracy', '')} ({record['minutes']:.2f} min)"
        )

    def _restore_from_mirror(self) -> None:
        if self.mirror and (self.mirror / self.runs_path.name).exists() and not self.runs_path.exists():
            for name in (self.runs_path.name, self.gens_path.name):
                if (self.mirror / name).exists():
                    shutil.copy(self.mirror / name, self.results / name)
            print("restored finished runs from", self.mirror)

    def minutes(self) -> float:
        return (time.perf_counter() - self.started) / 60

    def sync(self) -> None:
        if self.device == "cuda":
            self.torch.cuda.synchronize()
        elif self.device == "mps":
            self.torch.mps.synchronize()

    def reset_peak(self) -> None:
        """Called at the start of every timed run: resets the memory peak and notes the load."""
        self._peak = 0
        self._load_start = load_average()
        if self.device == "cuda":
            self.torch.cuda.reset_peak_memory_stats()

    def note_memory(self) -> None:
        if self.device == "mps":
            self._peak = max(self._peak, self.torch.mps.current_allocated_memory())

    def peak_gib(self) -> float:
        if self.device == "cuda":
            return self.torch.cuda.max_memory_allocated() / 2**30
        return self._peak / 2**30

    def autocast(self):
        if self.amp_dtype is None:
            return contextlib.nullcontext()
        return self.torch.autocast(device_type=self.device, dtype=self.amp_dtype)

    # ---------- model and formats ----------

    def load(self, path: Path | None = None):
        from transformers import AutoModelForCausalLM

        src = str(path) if path else MODEL
        rev = None if path else self.revision
        model = AutoModelForCausalLM.from_pretrained(src, revision=rev, dtype=self.torch.float32)
        return model.to(self.device)

    def ids(self, text: str) -> list[int]:
        return self.tok(text, add_special_tokens=False)["input_ids"]

    def render(self, p: T.Problem, template: str) -> list[int]:
        """The prompt as token ids. `chatml` is the contract used in training; the others are the
        eval-time mismatches the traps measure, and the base model's few-shot format."""
        user = [IM_START] + self.ids("user\n" + T.prompt_text(p)) + [IM_END] + self.ids("\n")
        turn = [IM_START] + self.ids("assistant\n")
        if template == "chatml":
            return user + turn
        if template == "sysprompt":
            return [IM_START] + self.ids("system\n" + SMOL_SYSTEM) + [IM_END] + self.ids("\n") + user + turn
        if template == "nogenprompt":
            return user
        if template == "fewshot":
            shots = "".join(f"{T.prompt_text(s)}\n{T.solution_text(s)}\n\n" for s in self.splits["shots"])
            return self.ids(shots + T.prompt_text(p) + "\n")
        raise ValueError(template)

    def example(self, p: T.Problem, prompt_loss: bool = False) -> tuple[list[int], list[int]]:
        """One SFT sequence and its labels. -100 marks tokens with no loss."""
        prompt = self.render(p, "chatml")
        reply = self.ids(T.solution_text(p)) + [IM_END]
        labels = (prompt if prompt_loss else [-100] * len(prompt)) + reply
        return prompt + reply, labels

    def pad_right(self, seqs: list[list[int]], fill: int):
        n = max(map(len, seqs))
        return self.torch.tensor([s + [fill] * (n - len(s)) for s in seqs], device=self.device)

    # ---------- decoding and grading ----------

    def generate(
        self, model, prompts: list[list[int]], sample: bool = False, k: int = 1, seed: int = 0
    ) -> list[list[dict]]:
        """Greedy (or sampled) replies for each prompt, k per prompt, as token ids cut at the first
        end-of-turn. Prompts are batched by length and left-padded."""
        torch = self.torch
        model.eval()
        order = sorted(range(len(prompts)), key=lambda i: len(prompts[i]))
        out: list[list[dict]] = [[] for _ in prompts]
        batch = max(1, self.hp["evalBatch"] // k)
        torch.manual_seed(seed)
        for start in range(0, len(order), batch):
            idx = order[start : start + batch]
            n = max(len(prompts[i]) for i in idx)
            ids = torch.tensor([[EOT] * (n - len(prompts[i])) + prompts[i] for i in idx], device=self.device)
            mask = torch.tensor([[0] * (n - len(prompts[i])) + [1] * len(prompts[i]) for i in idx], device=self.device)
            kw = (
                {"do_sample": True, "temperature": self.hp["dpo"]["temperature"], "top_k": 0, "top_p": 1.0}
                if sample
                else {"do_sample": False}
            )
            with torch.no_grad(), self.autocast():
                gen = model.generate(
                    input_ids=ids,
                    attention_mask=mask,
                    max_new_tokens=self.hp["maxNewTokens"],
                    num_return_sequences=k,
                    eos_token_id=[IM_END, EOT],
                    pad_token_id=EOT,
                    **kw,
                )
            self.note_memory()
            for row, seq in enumerate(gen[:, n:].tolist()):
                ended = next((j for j, t in enumerate(seq) if t in (IM_END, EOT)), None)
                reply = seq[: ended + 1] if ended is not None else seq
                text = self.tok.decode(reply[:-1] if ended is not None else reply)
                out[idx[row // k]].append({"ids": reply, "text": text, "ended": ended is not None})
        return out

    def evaluate(self, run_id: str, model, template: str, extra: dict | None = None, t0: float | None = None) -> dict:
        items = self.splits[self.eval_split]
        t0 = t0 if t0 is not None else time.perf_counter()
        replies = [r[0] for r in self.generate(model, [self.render(p, template) for p in items])]
        texts = [r["text"].split("\n\n")[0] if template == "fewshot" else r["text"] for r in replies]
        correct = [int(T.grade(t, p.answer)) for t, p in zip(texts, items)]
        self.sync()
        arm, _, seed = run_id.removeprefix("eval:").partition(":s")
        record = {
            "id": run_id,
            "kind": "eval",
            "arm": arm,
            "seed": int(seed) if seed else None,
            "template": template,
            "split": self.eval_split,
            "n": len(items),
            "accuracy": sum(correct) / len(items),
            "correct": "".join(map(str, correct)),
            "endedFraction": sum(r["ended"] for r in replies) / len(items),
            "meanReplyTokens": sum(len(r["ids"]) for r in replies) / len(items),
            "minutes": (time.perf_counter() - t0) / 60,
            "peakGiB": self.peak_gib(),
        } | (extra or {})
        gens = [{"id": run_id, "i": i, "text": t, "ok": c} for i, (t, c) in enumerate(zip(texts, correct))]
        self.save(record, gens)
        return record

    # ---------- training ----------

    def _optimizer(self, model, hp: dict, steps: int):
        torch = self.torch
        opt = torch.optim.AdamW(
            model.parameters(), lr=hp["lr"], weight_decay=hp.get("weightDecay", 0.0), betas=(0.9, 0.95)
        )
        warm = max(1, int(hp["warmup"] * steps))
        sched = torch.optim.lr_scheduler.LambdaLR(
            opt, lambda s: min((s + 1) / warm, max(0.0, (steps - s) / max(1, steps - warm)))
        )
        scaler = torch.amp.GradScaler(self.device, init_scale=2.0**12, enabled=self.scale)
        return opt, sched, scaler

    def _step(self, model, loss, opt, sched, scaler, clip: float) -> float:
        """Backward (unless loss is None: the caller already accumulated gradients), clip, update."""
        if loss is not None:
            scaler.scale(loss).backward()
        self.note_memory()  # activations are freed by now, gradients are live
        scaler.unscale_(opt)
        norm = self.torch.nn.utils.clip_grad_norm_(model.parameters(), clip)
        scaler.step(opt)
        scaler.update()
        sched.step()
        self.note_memory()  # gradients and optimizer state both live
        opt.zero_grad(set_to_none=True)
        return float(norm)

    def train_sft(self, seed: int, prompt_loss: bool = False):
        """Full fine-tuning on the sft split. The loss is the mean cross-entropy over the reply's
        tokens (and its closing <|im_end|>); with prompt_loss it also covers the prompt (the trap)."""
        torch = self.torch
        hp = self.hp["sft"]
        torch.manual_seed(seed)
        model = self.load()
        model.train()
        data = [self.example(p, prompt_loss) for p in self.splits["sft"]]
        rng = random.Random(seed)
        steps = hp["epochs"] * math.ceil(len(data) / hp["batch"])
        opt, sched, scaler = self._optimizer(model, hp, steps)
        curve, tokens, step = [], 0, 0
        for _ in range(hp["epochs"]):
            order = list(range(len(data)))
            rng.shuffle(order)
            for start in range(0, len(order), hp["batch"]):
                batch = [data[i] for i in order[start : start + hp["batch"]]]
                ids = self.pad_right([b[0] for b in batch], EOT)
                labels = self.pad_right([b[1] for b in batch], -100)
                mask = self.pad_right([[1] * len(b[0]) for b in batch], 0)
                with self.autocast():
                    logits = model(input_ids=ids, attention_mask=mask).logits
                self.note_memory()
                loss = torch.nn.functional.cross_entropy(
                    logits[:, :-1].float().reshape(-1, logits.size(-1)), labels[:, 1:].reshape(-1), ignore_index=-100
                )
                norm = self._step(model, loss, opt, sched, scaler, hp["clip"])
                tokens += int(mask.sum())
                if step % 10 == 0 or step == steps - 1:
                    curve.append([step, round(float(loss.detach()), 4), round(norm, 3)])
                step += 1
        self.sync()
        return model, {"steps": steps, "tokens": tokens, "curve": curve}

    def seq_logps(self, model, seqs: list[tuple[list[int], list[int]]]):
        """Summed log-probability of each reply given its prompt: seqs is [(prompt, reply), ...]."""
        torch = self.torch
        ids = self.pad_right([p + r for p, r in seqs], EOT)
        mask = self.pad_right([[1] * (len(p) + len(r)) for p, r in seqs], 0)
        scored = self.pad_right([[0] * len(p) + [1] * len(r) for p, r in seqs], 0)
        with self.autocast():
            logits = model(input_ids=ids, attention_mask=mask).logits
        self.note_memory()
        tok = -torch.nn.functional.cross_entropy(logits[:, :-1].float().transpose(1, 2), ids[:, 1:], reduction="none")
        return (tok * scored[:, 1:]).sum(-1)

    def make_pairs(self, model, seed: int) -> tuple[list[dict], dict]:
        """Sample from the SFT model on the dpo split and keep one (correct, incorrect) pair per
        problem that has both. Reply ids are kept as sampled, never re-tokenized from text."""
        items = self.splits["dpo"]
        k = self.hp["dpo"]["samples"]
        prompts = [self.render(p, "chatml") for p in items]
        samples = self.generate(model, prompts, sample=True, k=k, seed=seed)
        rng = random.Random(seed)
        pairs, solved = [], 0
        for p, prompt, group in zip(items, prompts, samples):
            good = [s for s in group if T.grade(s["text"], p.answer)]
            bad = [s for s in group if not T.grade(s["text"], p.answer)]
            solved += len(good)
            if good and bad:
                pairs.append({"prompt": prompt, "chosen": rng.choice(good)["ids"], "rejected": rng.choice(bad)["ids"]})
        stats = {
            "problems": len(items),
            "samplesPerProblem": k,
            "sampleAccuracy": solved / (len(items) * k),
            "pairs": len(pairs),
        }
        return pairs, stats

    def train_dpo(self, model, pairs: list[dict], seed: int):
        """DPO: loss = -log sigmoid(beta * [(log pi(c) - log ref(c)) - (log pi(r) - log ref(r))]).
        The reference is the SFT model itself, scored once before training, so only one model is in
        memory."""
        torch = self.torch
        hp = self.hp["dpo"]
        model.eval()
        micro = hp.get("micro", hp["batch"])
        with torch.no_grad():
            for start in range(0, len(pairs), micro):
                chunk = pairs[start : start + micro]
                lp = (
                    self.seq_logps(
                        model,
                        [(q["prompt"], q["chosen"]) for q in chunk] + [(q["prompt"], q["rejected"]) for q in chunk],
                    )
                    .float()
                    .tolist()
                )
                for j, q in enumerate(chunk):
                    q["refChosen"], q["refRejected"] = lp[j], lp[len(chunk) + j]
        model.train()
        torch.manual_seed(seed)
        rng = random.Random(seed)
        steps = hp["epochs"] * math.ceil(len(pairs) / hp["batch"])
        opt, sched, scaler = self._optimizer(model, hp, steps)
        curve, step, tokens = [], 0, 0
        for _ in range(hp["epochs"]):
            order = list(range(len(pairs)))
            rng.shuffle(order)
            for start in range(0, len(order), hp["batch"]):
                chunk = [pairs[i] for i in order[start : start + hp["batch"]]]
                # The batch's mean loss, accumulated over micro-batches of `micro` pairs so that the
                # chosen and rejected sequences of 16 pairs never sit in memory at once.
                parts = []
                for m in range(0, len(chunk), micro):
                    sub = chunk[m : m + micro]
                    lp = self.seq_logps(
                        model, [(q["prompt"], q["chosen"]) for q in sub] + [(q["prompt"], q["rejected"]) for q in sub]
                    )
                    pc, pr = lp[: len(sub)], lp[len(sub) :]
                    rc = torch.tensor([q["refChosen"] for q in sub], device=self.device)
                    rr = torch.tensor([q["refRejected"] for q in sub], device=self.device)
                    margin = hp["beta"] * ((pc - rc) - (pr - rr))
                    part = -torch.nn.functional.logsigmoid(margin).sum() / len(chunk)
                    scaler.scale(part).backward()
                    parts.append((part.detach(), margin.detach(), (pc - rc).detach(), (pr - rr).detach()))
                loss = sum(x[0] for x in parts)
                margin = torch.cat([x[1] for x in parts])
                dc, dr = torch.cat([x[2] for x in parts]), torch.cat([x[3] for x in parts])
                norm = self._step(model, None, opt, sched, scaler, hp["clip"])
                tokens += sum(len(q["prompt"]) * 2 + len(q["chosen"]) + len(q["rejected"]) for q in chunk)
                if step % 5 == 0 or step == steps - 1:
                    curve.append(
                        {
                            "step": step,
                            "loss": round(float(loss), 4),
                            "rewardAccuracy": round(float((margin > 0).float().mean()), 3),
                            "chosenDrift": round(float(dc.mean()), 3),
                            "rejectedDrift": round(float(dr.mean()), 3),
                            "gradNorm": round(norm, 3),
                        }
                    )
                step += 1
        self.sync()
        return model, {"steps": steps, "tokens": tokens, "curve": curve}

    # ---------- checkpoints ----------

    def ckpt_path(self, arm: str, seed: int) -> Path:
        return self.ckpt / f"{arm}-s{seed}"

    def save_ckpt(self, model, arm: str, seed: int) -> None:
        path = self.ckpt_path(arm, seed)
        model.save_pretrained(path)
        (path / "DONE").write_text(now())

    def have_ckpt(self, arm: str, seed: int) -> bool:
        return (self.ckpt_path(arm, seed) / "DONE").exists()

    def sft_model(self, seed: int):
        """The SFT checkpoint for a seed; retrained (and recorded as such) if this runtime lost it."""
        if not self.have_ckpt("sft", seed):
            print(f"SFT checkpoint for seed {seed} missing; retraining it")
            self._train_and_save_sft(seed, f"train:sft:s{seed}:retrain@{now()}")
        return self.load(self.ckpt_path("sft", seed))

    def _train_and_save_sft(self, seed: int, run_id: str) -> None:
        self.reset_peak()
        t0 = time.perf_counter()
        model, info = self.train_sft(seed)
        minutes = (time.perf_counter() - t0) / 60
        self.save_ckpt(model, "sft", seed)
        self.save(
            {
                "id": run_id,
                "kind": "train",
                "arm": "sft",
                "seed": seed,
                "minutes": minutes,
                "peakGiB": self.peak_gib(),
                "hp": self.hp["sft"],
            }
            | info
        )
        del model
        self.free()

    def free(self) -> None:
        import gc

        gc.collect()
        if self.device == "cuda":
            self.torch.cuda.empty_cache()
        elif self.device == "mps":
            self.torch.mps.empty_cache()

    # ---------- the notebook's sections ----------

    def section_base(self) -> None:
        todo = [
            (a, t) for a, t in (("base-fewshot", "fewshot"), ("base-chatml", "chatml")) if not self.done(f"eval:{a}")
        ]
        if not todo:
            return
        model = self.load()
        for arm, template in todo:
            self.reset_peak()
            self.evaluate(f"eval:{arm}", model, template)
        del model
        self.free()

    def section_sft(self) -> None:
        for seed in self.cfg["seeds"]:
            if not self.done(f"train:sft:s{seed}"):
                self._train_and_save_sft(seed, f"train:sft:s{seed}")

    def section_eval_sft(self) -> None:
        for seed in self.cfg["seeds"]:
            if not self.done(f"eval:sft:s{seed}"):
                model = self.sft_model(seed)
                self.reset_peak()
                self.evaluate(f"eval:sft:s{seed}", model, "chatml")
                del model
                self.free()

    def section_dpo(self) -> None:
        for seed in self.cfg["seeds"]:
            if self.done(f"train:dpo:s{seed}") and self.have_ckpt("dpo", seed):
                continue
            model = self.sft_model(seed)
            self.reset_peak()
            t0 = time.perf_counter()
            pairs, pair_stats = self.make_pairs(model, seed)
            t_pairs = (time.perf_counter() - t0) / 60
            model, info = self.train_dpo(model, pairs, seed)
            minutes = (time.perf_counter() - t0) / 60
            self.save_ckpt(model, "dpo", seed)
            run_id = (
                f"train:dpo:s{seed}" if not self.done(f"train:dpo:s{seed}") else f"train:dpo:s{seed}:retrain@{now()}"
            )
            self.save(
                {
                    "id": run_id,
                    "kind": "train",
                    "arm": "dpo",
                    "seed": seed,
                    "minutes": minutes,
                    "pairMinutes": t_pairs,
                    "peakGiB": self.peak_gib(),
                    "hp": self.hp["dpo"],
                    "pairStats": pair_stats,
                }
                | info
            )
            del model
            self.free()

    def section_eval_dpo(self) -> None:
        for seed in self.cfg["seeds"]:
            if self.done(f"eval:dpo:s{seed}"):
                continue
            if not self.have_ckpt("dpo", seed):
                self.section_dpo()
            model = self.load(self.ckpt_path("dpo", seed))
            self.reset_peak()
            self.evaluate(f"eval:dpo:s{seed}", model, "chatml")
            del model
            self.free()

    def section_trap(self) -> None:
        for seed in self.cfg["seeds"]:
            todo = [t for t in ("sysprompt", "nogenprompt") if not self.done(f"eval:trap-{t}:s{seed}")]
            if todo:
                model = self.sft_model(seed)
                for t in todo:
                    self.reset_peak()
                    self.evaluate(f"eval:trap-{t}:s{seed}", model, t)
                del model
                self.free()
            if not self.done(f"eval:trap-promptloss:s{seed}"):
                self.reset_peak()
                t0 = time.perf_counter()
                model, info = self.train_sft(seed, prompt_loss=True)
                train = {
                    "trainMinutes": (time.perf_counter() - t0) / 60,
                    "trainPeakGiB": self.peak_gib(),
                    "trainSteps": info["steps"],
                    "trainTokens": info["tokens"],
                    "curve": info["curve"],
                }
                self.evaluate(f"eval:trap-promptloss:s{seed}", model, "chatml", extra=train, t0=t0)
                del model
                self.free()

    def probe_activations(self, checkpoints: dict[str, str] | None = None) -> dict:
        """Why the default is float32. For the base model (and any checkpoints given as
        {label: path}): the largest output of any linear layer, measured in float32, (a) on the
        training format, right-padded, and (b) while sampling replies to left-padded prompts, as
        DPO's pair generation does; then (c) the same sampling under float16 autocast."""
        torch = self.torch
        report = {"id": "probe:activations", "device": self.device, "float16Max": 65504.0, "models": {}}
        for label, path in {"base": None, **(checkpoints or {})}.items():
            model = self.load(Path(path) if path else None).eval()
            peak: dict[str, float] = {}

            def hook(name):
                def record(_mod, _inp, out):
                    peak[name] = max(peak.get(name, 0.0), float(out.detach().abs().max()))

                return record

            handles = [
                m.register_forward_hook(hook(n)) for n, m in model.named_modules() if isinstance(m, torch.nn.Linear)
            ]
            seqs = [self.example(p)[0] for p in self.splits["sft"][:64]]
            with torch.no_grad():
                model(
                    input_ids=self.pad_right(seqs, EOT), attention_mask=self.pad_right([[1] * len(x) for x in seqs], 0)
                )
            train_format = sorted(peak.items(), key=lambda kv: -kv[1])[:3]
            peak.clear()
            prompts = [self.render(p, "chatml") for p in self.splits["dpo"][:32]]
            saved = self.amp_dtype
            self.amp_dtype = None
            self.generate(model, prompts, sample=True, k=4, seed=0)
            sampling = sorted(peak.items(), key=lambda kv: -kv[1])[:3]
            for h in handles:
                h.remove()
            self.amp_dtype = torch.float16
            try:
                self.generate(model, prompts, sample=True, k=4, seed=0)
                self.sync()
                fp16 = "ok"
            except Exception as e:  # noqa: BLE001 - the failure is the measurement
                fp16 = f"failed: {type(e).__name__}: {str(e)[:100]}"
            finally:
                self.amp_dtype = saved
            report["models"][label] = {
                "checkpoint": Path(path).name if path else None,
                "trainFormatFp32": [[n, round(v, 1)] for n, v in train_format],
                "leftPaddedSamplingFp32": [[n, round(v, 1)] for n, v in sampling],
                "fp16Sampling": fp16,
            }
            del model
            self.free()
        (self.results / "activations-v1.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
        return report

    def check_microbatch(self, micros=(16, 8), seed: int = 0) -> dict:
        """One DPO step's gradient computed with all 16 pairs in one pass and in micro-batches:
        the gradients must agree to float rounding. Also records the peak memory of each. The
        pairs are the reference solutions (chosen) against the same steps with an answer off by one
        (rejected), on 16 dpo-split problems, scored by the base model."""
        torch = self.torch
        model = self.load()
        pairs = []
        for p in self.splits["dpo"][:16]:
            wrong = T.solution_text(p).rsplit("Answer: ", 1)[0] + f"Answer: {p.answer + 1}"
            pairs.append(
                {
                    "prompt": self.render(p, "chatml"),
                    "chosen": self.ids(T.solution_text(p)) + [IM_END],
                    "rejected": self.ids(wrong) + [IM_END],
                }
            )
        with torch.no_grad():
            lp = self.seq_logps(
                model, [(q["prompt"], q["chosen"]) for q in pairs] + [(q["prompt"], q["rejected"]) for q in pairs]
            )
        for j, q in enumerate(pairs):
            q["refChosen"], q["refRejected"] = float(lp[j]) - 1.0, float(lp[16 + j])  # a nonzero margin
        grads, peaks = {}, {}
        for micro in micros:
            model.zero_grad(set_to_none=True)
            self.free()
            self.reset_peak()
            for m in range(0, 16, micro):
                sub = pairs[m : m + micro]
                lp = self.seq_logps(
                    model, [(q["prompt"], q["chosen"]) for q in sub] + [(q["prompt"], q["rejected"]) for q in sub]
                )
                rc = torch.tensor([q["refChosen"] for q in sub], device=self.device)
                rr = torch.tensor([q["refRejected"] for q in sub], device=self.device)
                margin = self.hp["dpo"]["beta"] * ((lp[: len(sub)] - rc) - (lp[len(sub) :] - rr))
                (-torch.nn.functional.logsigmoid(margin).sum() / 16).backward()
                self.note_memory()
            grads[micro] = torch.cat([p.grad.flatten() for p in model.parameters()]).cpu()
            peaks[micro] = self.peak_gib()
        a, b = grads[micros[0]].double(), grads[micros[1]].double()
        result = {
            "id": "check:microbatch",
            "device": self.device,
            "precision": self.precision,
            "micros": list(micros),
            "relativeDifference": float((a - b).norm() / a.norm()),
            "cosine": float(torch.nn.functional.cosine_similarity(a, b, dim=0)),
            "peakGiB": {str(k): round(v, 2) for k, v in peaks.items()},
            "peakNote": "CUDA: max_memory_allocated; MPS: current_allocated_memory sampled after each backward",
            "loadAverage": load_average(),
        }
        (self.results / "microbatch-check-v1.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        del model
        self.free()
        return result

    def calibrate(self, sft_lrs=(1e-5, 3e-5, 1e-4), dpo_lrs=(1e-6, 3e-6, 1e-5), seed: int = 0) -> dict:
        """Choose the learning rates on the dev split, never on test. Seed 0 only. Recorded in
        results/calibration-v1.jsonl; the chosen values are written into HP by hand afterwards."""
        self.eval_split = "dev"
        self.runs_path = self.results / "calibration-v1.jsonl"
        self.gens_path = self.results / "calibration-generations-v1.jsonl"
        if not self.done("eval:base-fewshot"):
            model = self.load()
            self.reset_peak()
            self.evaluate("eval:base-fewshot", model, "fewshot")
            del model
            self.free()
        base_sft = dict(self.hp["sft"])
        for lr in sft_lrs:
            run_id = f"eval:sft-lr{lr:g}:s{seed}"
            if self.done(run_id):
                continue
            self.hp["sft"] = base_sft | {"lr": lr}
            self.reset_peak()
            t0 = time.perf_counter()
            model, info = self.train_sft(seed)
            extra = {
                "lr": lr,
                "trainMinutes": (time.perf_counter() - t0) / 60,
                "trainPeakGiB": self.peak_gib(),
                "trainSteps": info["steps"],
                "curve": info["curve"],
            }
            self.save_ckpt(model, f"cal-sft-lr{lr:g}", seed)
            self.evaluate(run_id, model, "chatml", extra=extra, t0=t0)
            del model
            self.free()
        self.hp["sft"] = base_sft
        recs = self.records()
        best = max(sft_lrs, key=lambda lr: recs[f"eval:sft-lr{lr:g}:s{seed}"]["accuracy"])
        base_dpo = dict(self.hp["dpo"])
        for lr in dpo_lrs:
            run_id = f"eval:dpo-lr{lr:g}-from-sft-lr{best:g}:s{seed}"
            if self.done(run_id):
                continue
            self.hp["dpo"] = base_dpo | {"lr": lr}
            model = self.load(self.ckpt_path(f"cal-sft-lr{best:g}", seed))
            self.reset_peak()
            t0 = time.perf_counter()
            pairs, pair_stats = self.make_pairs(model, seed)
            model, info = self.train_dpo(model, pairs, seed)
            extra = {
                "lr": lr,
                "sftLr": best,
                "trainMinutes": (time.perf_counter() - t0) / 60,
                "trainPeakGiB": self.peak_gib(),
                "pairStats": pair_stats,
                "curve": info["curve"],
            }
            self.evaluate(run_id, model, "chatml", extra=extra, t0=t0)
            del model
            self.free()
        self.hp["dpo"] = base_dpo
        out = {k: v["accuracy"] for k, v in self.records().items()}
        print(json.dumps(out, indent=2))
        return out

    def run_all(self) -> None:
        self.section_base()
        self.section_sft()
        self.section_eval_sft()
        self.section_dpo()
        self.section_eval_dpo()
        self.section_trap()

    # ---------- summary and receipt ----------

    def show(self, arms: tuple = (), comparisons: tuple = ()) -> None:
        """Print accuracies (Wilson 95% interval per seed) and paired comparisons for a section."""
        if not self.runs_path.exists():
            print("no finished runs yet")
            return
        s = self.summarize()
        for a in arms:
            if a in s["arms"]:
                v = s["arms"][a]
                per = ", ".join(
                    f"{x:.1%} [{lo:.1%}, {hi:.1%}]" for x, (lo, hi) in zip(v["accuracyPerSeed"], v["wilsonPerSeed"])
                )
                print(
                    f"{a:18s} n={v['n']}  {per}  mean {v['accuracyMean']:.1%}  reply {v['meanReplyTokens']:.0f} tokens, ended {v['endedFraction']:.0%}"
                )
        for c in comparisons:
            if c in s["comparisons"]:
                v = s["comparisons"][c]
                pooled = v["pooled"]
                seeds = "; ".join(
                    f"{p['diff']:+.1%} [{p['lo']:+.1%}, {p['hi']:+.1%}] McNemar p={p['mcnemarP']:.2g}"
                    for p in v["perSeed"]
                )
                print(
                    f"{c}: {pooled['diff']:+.1%} (95% item-bootstrap interval {pooled['lo']:+.1%} to {pooled['hi']:+.1%}); per seed: {seeds}; real: {v['real']}"
                )
        print(f"[{self.minutes():.1f} min in this session; {s['totalMinutes']:.1f} min of recorded runs]")

    def summarize(self) -> dict:
        return summarize(self.out, self.size)

    def receipt(self, path: Path | None = None) -> dict:
        return write_receipt(self, path)


def rows(evals: dict[str, dict], arm: str) -> list[list[int]]:
    found = sorted((r for r in evals.values() if r["arm"] == arm), key=lambda r: (r["seed"] is None, r["seed"]))
    return [[int(c) for c in r["correct"]] for r in found]


def summarize(out: Path | str = HERE, size: str | None = None) -> dict:
    """Every number the README reports, recomputed from results/runs-v1.jsonl."""
    out = Path(out)
    records = [json.loads(line) for line in (out / "results" / "runs-v1.jsonl").read_text().splitlines()]
    if size:
        records = [r for r in records if r.get("size") == size]
    evals = {r["id"]: r for r in records if r["kind"] == "eval"}
    trains = [r for r in records if r["kind"] == "train"]
    arms = {}
    for arm in sorted({r["arm"] for r in evals.values()}):
        accs = [sum(x) / len(x) for x in rows(evals, arm)]
        recs = [r for r in evals.values() if r["arm"] == arm]
        n = recs[0]["n"]
        arms[arm] = {
            "seeds": len(accs),
            "accuracyPerSeed": accs,
            "wilsonPerSeed": [S.wilson(round(a * n), n) for a in accs],
            "accuracyMean": S.mean(accs),
            "accuracySeedSd": S.sd(accs),
            "meanReplyTokens": S.mean([r["meanReplyTokens"] for r in recs]),
            "endedFraction": S.mean([r["endedFraction"] for r in recs]),
            "n": n,
        }
    comparisons = {}
    for name, b, a in (
        ("sft vs base-fewshot", "sft", "base-fewshot"),
        ("dpo vs sft", "dpo", "sft"),
        ("dpo vs base-fewshot", "dpo", "base-fewshot"),
        ("trap-promptloss vs sft", "trap-promptloss", "sft"),
        ("trap-sysprompt vs sft", "trap-sysprompt", "sft"),
        ("trap-nogenprompt vs sft", "trap-nogenprompt", "sft"),
    ):
        if a in arms and b in arms:
            br, ar = rows(evals, b), rows(evals, a)
            if len(ar) not in (1, len(br)):
                continue
            comparisons[name] = S.compare(br, ar)
    training = {}
    for r in trains:
        key = f"{r['arm']}:s{r['seed']}"
        entry = {"minutes": r["minutes"], "peakGiB": r["peakGiB"], "steps": r["steps"], "tokens": r["tokens"]}
        if r["arm"] == "dpo":
            last = r["curve"][-1]
            entry |= {"pairMinutes": r["pairMinutes"], "pairStats": r["pairStats"], "final": last}
        else:
            entry |= {"firstLoss": r["curve"][0][1], "finalLoss": r["curve"][-1][1]}
        training[key] = entry
    summary = {
        "experiment": "sft-then-dpo-on-a-colab-t4 v1",
        "size": size,
        "devices": sorted({r["device"] for r in records}),
        "arms": arms,
        "comparisons": comparisons,
        "training": training,
        "minutesByRun": {r["id"]: round(r["minutes"], 3) for r in records},
        "totalMinutes": sum(r["minutes"] for r in records),
    }
    (out / "results" / "summary-v1.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def packages() -> dict:
    from importlib import metadata

    names = ["torch", "transformers", "tokenizers", "safetensors", "huggingface-hub", "numpy", "accelerate"]
    found = {}
    for n in names:
        try:
            found[n] = metadata.version(n)
        except metadata.PackageNotFoundError:
            pass
    return found


def device_info(device: str) -> dict:
    import torch

    info = {"type": device, "torch": torch.__version__}
    if device == "cuda":
        props = torch.cuda.get_device_properties(0)
        info |= {
            "name": props.name,
            "memoryGiB": round(props.total_memory / 2**30, 2),
            "capability": list(torch.cuda.get_device_capability()),
            "cuda": torch.version.cuda,
        }
        try:
            info["driver"] = subprocess.run(
                ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=20,
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            info["driver"] = None
    elif device == "mps":
        try:
            info["name"] = (
                subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True, timeout=20
                ).stdout.strip()
                + " GPU (MPS)"
            )
        except (OSError, subprocess.SubprocessError):
            info["name"] = "Apple GPU (MPS)"
    return info


def write_receipt(lab: Lab, path: Path | None = None) -> dict:
    summary = lab.summarize()
    records = list(lab.records().values())
    receipt = {
        "experiment": "sft-then-dpo-on-a-colab-t4 v1",
        "ranOn": dt.date.today().isoformat(),
        "where": f"{platform.system()} {platform.machine()}, Python {platform.python_version()}",
        "colab": "COLAB_RELEASE_TAG" in os.environ or "COLAB_GPU" in os.environ,
        "device": device_info(lab.device),
        "precision": PRECISIONS[lab.precision],
        "packages": packages(),
        "model": {"id": MODEL, "revision": lab.revision, "license": "apache-2.0"},
        "data": {
            "source": "generated by sftdpo_task_v1.py (MIT, this repository); no download",
            "seed": DATA_SEED,
            "operands": lab.hp["operands"],
            "sizes": {k: len(v) for k, v in lab.splits.items()},
            "sha256": {k: T.split_digest(v) for k, v in lab.splits.items()},
        },
        "size": lab.size,
        "seeds": lab.cfg["seeds"],
        "hyperparameters": lab.hp,
        "minutesByRun": {r["id"]: round(r["minutes"], 3) for r in records},
        "peakGiBByRun": {r["id"]: round(r.get("trainPeakGiB", r.get("peakGiB", 0.0)), 2) for r in records},
        "totalMinutes": round(sum(r["minutes"] for r in records), 2),
        "loadAverageByRun": {r["id"]: {"start": r.get("loadStart"), "end": r.get("loadEnd")} for r in records},
        "results": {
            "arms": {
                a: {"accuracyPerSeed": v["accuracyPerSeed"], "accuracyMean": v["accuracyMean"]}
                for a, v in summary["arms"].items()
            },
            "comparisons": {
                k: {"diff": v["pooled"]["diff"], "lo": v["pooled"]["lo"], "hi": v["pooled"]["hi"], "real": v["real"]}
                for k, v in summary["comparisons"].items()
            },
        },
        "costUsd": 0.0,
        "note": "Open weights on a local or free Colab GPU; no API was called.",
    }
    path = path or lab.out / "receipts" / "sftdpo-v1.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2) + "\n")
    if lab.mirror:
        shutil.copy(path, lab.mirror / path.name)
    return receipt


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        "command",
        choices=[
            "all",
            "base",
            "sft",
            "eval-sft",
            "dpo",
            "eval-dpo",
            "trap",
            "activations",
            "calibrate",
            "check-microbatch",
            "summarize",
            "receipt",
        ],
    )
    ap.add_argument("--size", default="default", choices=sorted(SIZES))
    ap.add_argument("--out", default=str(HERE))
    ap.add_argument("--ckpt", default=None, help="checkpoint directory (default OUT/ckpt)")
    ap.add_argument("--device", default=None)
    ap.add_argument("--precision", default="fp32", choices=sorted(PRECISIONS))
    args = ap.parse_args()
    if args.command == "summarize":
        print(json.dumps(summarize(args.out, args.size)["arms"], indent=2))
        return
    lab = Lab(args.size, args.out, args.device, args.ckpt, precision=args.precision)
    steps = {
        "all": lab.run_all,
        "base": lab.section_base,
        "sft": lab.section_sft,
        "eval-sft": lab.section_eval_sft,
        "dpo": lab.section_dpo,
        "eval-dpo": lab.section_eval_dpo,
        "trap": lab.section_trap,
        "receipt": lab.receipt,
        "activations": lab.probe_activations,
        "calibrate": lab.calibrate,
        "check-microbatch": lab.check_microbatch,
    }
    steps[args.command]()
    if args.command == "all":
        lab.receipt()


if __name__ == "__main__":
    main()
