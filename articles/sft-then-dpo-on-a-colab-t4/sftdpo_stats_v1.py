# Prof Rod | Post-Training, Measured: SFT Then DPO on a Colab T4
# Course: https://profrod.ai/courses
# Original source and updates: https://github.com/profrodai/profrodai-resources

"""The statistics behind "is the gain real?". Standard library only.

Every arm is graded on the same test items, so each comparison is paired: item i is scored under
arm A and under arm B. Two sources of variation are reported separately:
- sample variation: an interval over test items, from a paired bootstrap (items resampled, the
  per-item difference kept intact), plus the exact McNemar test on the discordant items;
- seed variation: the per-seed accuracies and their spread. With 3 seeds an interval over seeds
  would be too wide to say anything, so the rule is stated instead: a gain counts as real only if
  the seed-averaged interval excludes zero AND every seed's own paired interval does.
"""

from __future__ import annotations

import math
import random
from math import comb


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)


def sd(xs: list[float]) -> float:
    """Sample standard deviation (n - 1); 0.0 for a single value."""
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    """Wilson score interval for a proportion k / n."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


def item_means(rows: list[list[int]]) -> list[float]:
    """Per-item mean over seeds: rows[s][i] is 1 if seed s got item i right."""
    n = len(rows[0])
    assert all(len(r) == n for r in rows), "every seed must be graded on the same items"
    return [sum(r[i] for r in rows) / len(rows) for i in range(n)]


def paired_bootstrap(
    b_rows: list[list[int]], a_rows: list[list[int]], resamples: int = 10000, seed: int = 0, level: float = 0.95
) -> dict:
    """Accuracy of B minus accuracy of A, both averaged over their seeds, with a percentile
    bootstrap over items. A may have one row (a seed-free baseline such as the base model)."""
    d = [b - a for b, a in zip(item_means(b_rows), item_means(a_rows))]
    n = len(d)
    rng = random.Random(seed)
    stats = sorted(sum(d[rng.randrange(n)] for _ in range(n)) / n for _ in range(resamples))
    lo = stats[int((1 - level) / 2 * resamples)]
    hi = stats[min(resamples - 1, int((1 + level) / 2 * resamples))]
    return {"diff": mean(d), "lo": lo, "hi": hi, "items": n, "sdItem": sd(d)}


def mcnemar_exact(b_only: int, a_only: int) -> float:
    """Two-sided exact McNemar p-value: under no difference, the discordant items split 50/50."""
    n = b_only + a_only
    if n == 0:
        return 1.0
    k = min(b_only, a_only)
    tail = sum(comb(n, i) for i in range(k + 1)) / 2**n
    return min(1.0, 2 * tail)


def discordant(b: list[int], a: list[int]) -> tuple[int, int]:
    """(items only B got right, items only A got right)."""
    return sum(1 for x, y in zip(b, a) if x and not y), sum(1 for x, y in zip(b, a) if y and not x)


def items_needed(diff: float, sd_item: float, z: float = 1.959964) -> int | None:
    """Items for a normal-approximation interval of half-width |diff|, given the per-item standard
    deviation of the paired difference: the smallest n at which an effect this size excludes zero."""
    if diff == 0:
        return None
    return math.ceil((z * sd_item / abs(diff)) ** 2)


def compare(b_rows: list[list[int]], a_rows: list[list[int]], resamples: int = 10000, seed: int = 0) -> dict:
    """The full paired comparison of arm B against arm A: seed-averaged bootstrap interval,
    per-seed accuracies, per-seed bootstrap intervals and McNemar p-values, and the verdict."""
    pooled = paired_bootstrap(b_rows, a_rows, resamples, seed)
    per_seed = []
    for s, b in enumerate(b_rows):
        a = a_rows[s] if len(a_rows) == len(b_rows) else a_rows[0]
        one = paired_bootstrap([b], [a], resamples, seed + 1 + s)
        b_only, a_only = discordant(b, a)
        one.update(bOnly=b_only, aOnly=a_only, mcnemarP=mcnemar_exact(b_only, a_only))
        per_seed.append(one)
    seed_diffs = [p["diff"] for p in per_seed]
    if pooled["lo"] > 0:
        real = all(p["lo"] > 0 for p in per_seed)
    elif pooled["hi"] < 0:
        real = all(p["hi"] < 0 for p in per_seed)
    else:
        real = False
    return {
        "pooled": pooled,
        "perSeed": per_seed,
        "seedDiffMean": mean(seed_diffs),
        "seedDiffSd": sd(seed_diffs),
        "itemsNeeded": items_needed(pooled["diff"], pooled["sdItem"]),
        "real": real,
    }


def log_sigmoid(x: float) -> float:
    """log(1 / (1 + e^-x)) without overflow for large |x|."""
    return -math.log1p(math.exp(-x)) if x >= 0 else x - math.log1p(math.exp(x))


def dpo_loss(
    policy_chosen: float, policy_rejected: float, ref_chosen: float, ref_rejected: float, beta: float
) -> float:
    """The DPO loss for one pair, from summed reply log-probabilities: -log sigmoid(beta * margin),
    where margin = (log pi(c) - log ref(c)) - (log pi(r) - log ref(r)). At the start of training the
    policy is the reference, the margin is 0, and the loss is log 2."""
    margin = (policy_chosen - ref_chosen) - (policy_rejected - ref_rejected)
    return -log_sigmoid(beta * margin)


def full_finetune_gib(
    params: int, tokens: int, layers: int, hidden: int, vocab: int, activation_bytes: int = 4
) -> dict:
    """A memory estimate for full fine-tuning with AdamW, float32 weights and optimizer state.

    - weights, gradients: 4 bytes each per parameter; AdamW's two moments: 8 more. 16 bytes total.
    - activations kept for the backward pass: about 17 values of size `hidden` per token per layer,
      at `activation_bytes` each (4 in float32, 2 under 16-bit autocast). This is Korthikanti et al.
      (2022)'s 34 * hidden bytes in 16-bit, without the attention-score term, which
      memory-efficient attention does not store.
    - logits: per token, vocab * (activation_bytes for the logits + 4 for the float32 values the loss
      uses + 4 for their gradient).
    Returns GiB per component and the total. Allocator overhead and the CUDA context come on top.
    """
    gib = 2**30
    parts = {
        "weights": 4 * params / gib,
        "gradients": 4 * params / gib,
        "adamState": 8 * params / gib,
        "activations": 17 * activation_bytes * hidden * layers * tokens / gib,
        "logits": (activation_bytes + 8) * vocab * tokens / gib,
    }
    parts["total"] = sum(parts.values())
    return parts
