# Prof Rod | GRPO on a Tiny Model
# Article: https://profrod.ai/articles/grpo-on-a-tiny-model
# Original source and updates: https://github.com/profrodai/profrodai-resources

"""The statistics behind every number the GRPO article reports. Standard library only.

Two kinds of variation, reported separately:
- sample variation: the held-out items are a sample of the task, so an accuracy carries an interval
  over items (Wilson for one rate; a paired bootstrap for a before/after difference);
- seed variation: an RL run is itself random (sampling, data order), so the same recipe gives
  different policies. Each seed is one draw; the t interval over seed means covers that.

The before/after comparison is paired: base and trained policy answer the same items, so the test
looks only at the items where they disagree (exact McNemar), and the bootstrap resamples items.
"""

from __future__ import annotations

import math
import random
from math import comb
from statistics import fmean, stdev

Z95 = 1.959963984540054
# Two-sided 95% t critical values by degrees of freedom (seed counts are small).
T95 = {
    1: 12.706,
    2: 4.303,
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
    10: 2.228,
}


def wilson(successes: int, n: int, z: float = Z95) -> tuple[float, float]:
    """Wilson score interval for a binomial rate. Better than p +/- z*se near 0 and 1."""
    if n == 0:
        return (0.0, 1.0)
    p = successes / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


def mcnemar_exact(only_a: int, only_b: int) -> float:
    """Two-sided exact McNemar p-value: under no difference, each discordant item is a fair coin."""
    n = only_a + only_b
    if n == 0:
        return 1.0
    k = min(only_a, only_b)
    tail = sum(comb(n, i) for i in range(k + 1)) / 2**n
    return min(1.0, 2 * tail)


def paired(before: list[float], after: list[float]) -> dict:
    """Discordant counts and the exact McNemar p for 0/1 outcomes on the same items."""
    assert len(before) == len(after)
    gained = sum(1 for b, a in zip(before, after) if a and not b)
    lost = sum(1 for b, a in zip(before, after) if b and not a)
    return {"gained": gained, "lost": lost, "mcnemarP": mcnemar_exact(gained, lost)}


def paired_bootstrap(
    before: list[float], after: list[float], reps: int = 10000, seed: int = 0
) -> tuple[float, float]:
    """95% percentile interval for mean(after - before), resampling items with replacement."""
    rng = random.Random(seed)
    diffs = [a - b for b, a in zip(before, after)]
    n = len(diffs)
    means = sorted(fmean(rng.choices(diffs, k=n)) for _ in range(reps))
    return (means[int(0.025 * reps)], means[int(0.975 * reps) - 1])


def t_interval(values: list[float]) -> tuple[float, float, float]:
    """Mean and 95% t interval over independent runs (seeds). Needs at least two values."""
    m = fmean(values)
    if len(values) < 2:
        return (m, float("nan"), float("nan"))
    half = T95.get(len(values) - 1, Z95) * stdev(values) / math.sqrt(len(values))
    return (m, m - half, m + half)


def summarize_rate(outcomes: list[float]) -> dict:
    k, n = int(sum(outcomes)), len(outcomes)
    lo, hi = wilson(k, n)
    return {
        "correct": k,
        "n": n,
        "rate": k / n if n else float("nan"),
        "wilson95": [lo, hi],
    }
