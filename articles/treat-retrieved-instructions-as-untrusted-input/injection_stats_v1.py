# Prof Rod | Measure Prompt Injection as an Attack-Success Rate
# Article: https://profrod.ai/articles/treat-retrieved-instructions-as-untrusted-input
# Original source and updates: https://github.com/profrodai/profrodai-resources

"""The statistics the injection article uses. Standard library only."""

from __future__ import annotations

import math
import random
from math import comb


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    """Wilson score interval for k successes in n trials."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value from the two discordant counts."""
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(comb(n, i) for i in range(min(b, c) + 1)) / 2**n
    return min(1.0, 2 * tail)


def cluster_bootstrap_rate(clusters: dict[str, list[bool]], draws: int = 4000, seed: int = 20261001) -> tuple[float, float]:
    """95% interval for a success rate when items come in clusters (here, the ten attacks on one
    README): resample whole clusters with replacement, not single items."""
    rng = random.Random(seed)
    groups = [v for v in clusters.values() if v]
    if not groups:
        return (0.0, 1.0)
    rates = []
    for _ in range(draws):
        pick = [groups[rng.randrange(len(groups))] for _ in groups]
        rates.append(sum(sum(g) for g in pick) / sum(len(g) for g in pick))
    rates.sort()
    return (rates[int(0.025 * draws)], rates[int(0.975 * draws) - 1])
