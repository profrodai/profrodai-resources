# Prof Rod | Measure Whether a Coding Agent Weakens Tests Under Pressure
# Article: https://profrod.ai/articles/dark-software-factory-test-authority
# Original source and updates: https://github.com/profrodai/profrodai-resources

"""The statistics the test-authority article uses. Standard library only."""

from __future__ import annotations

import math
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
    return min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2**n)
