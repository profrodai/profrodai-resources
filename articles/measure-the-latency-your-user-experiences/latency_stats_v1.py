# Prof Rod | Measure the Latency Your User Experiences
# Article: https://profrod.ai/articles/measure-the-latency-your-user-experiences
# Original source and updates: https://github.com/profrodai/profrodai-resources

"""The statistics the latency article uses. Standard library only."""

from __future__ import annotations

import math
from math import comb


def percentile(values: list[float], q: float) -> float:
    """The smallest observed value that at least q (0 to 1) of the observations do not exceed."""
    xs = sorted(values)
    rank = max(1, math.ceil(q * len(xs)))
    return xs[rank - 1]


def binom_cdf(k: int, n: int, p: float) -> float:
    return sum(comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k + 1))


def percentile_interval(values: list[float], q: float, level: float = 0.95) -> tuple[float, float] | None:
    """Distribution-free interval for the true q-quantile from order statistics.

    The number of observations below the true quantile is Binomial(n, q). Choose ranks l < u, as
    symmetric as possible, with P(l <= B < u) >= level; the interval is [x_(l), x_(u)]. Returns None
    when no pair of ranks inside the sample reaches the level (too few observations in the tail).
    """
    xs = sorted(values)
    n = len(xs)
    alpha = (1 - level) / 2
    lower = None
    for rank in range(n, 0, -1):  # largest l with P(B < l) <= alpha
        if binom_cdf(rank - 1, n, q) <= alpha:
            lower = rank
            break
    upper = None
    for rank in range(1, n + 1):  # smallest u with P(B >= u) <= alpha
        if 1 - binom_cdf(rank - 1, n, q) <= alpha:
            upper = rank
            break
    if lower is None or upper is None:
        return None
    return (xs[lower - 1], xs[upper - 1])


def fit_quadratic(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
    """Least-squares a, b, c for y = a + b x + c x^2, by the normal equations."""
    s = [sum(x**k for x in xs) for k in range(5)]
    t = [sum(y * x**k for x, y in zip(xs, ys)) for k in range(3)]
    m = [[s[0], s[1], s[2]], [s[1], s[2], s[3]], [s[2], s[3], s[4]]]
    return tuple(_solve(m, t))  # type: ignore[return-value]


def _solve(m: list[list[float]], v: list[float]) -> list[float]:
    n = len(v)
    a = [row[:] + [v[i]] for i, row in enumerate(m)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(a[r][col]))
        a[col], a[pivot] = a[pivot], a[col]
        for r in range(n):
            if r != col:
                f = a[r][col] / a[col][col]
                a[r] = [x - f * y for x, y in zip(a[r], a[col])]
    return [a[i][n] / a[i][i] for i in range(n)]


def time_average_in_system(arrivals: list[float], departures: list[float]) -> tuple[float, float]:
    """L, the time-average number of requests in the system, over [first arrival, last departure],
    and the length of that window."""
    events = sorted([(t, 1) for t in arrivals] + [(t, -1) for t in departures])
    start, end = events[0][0], events[-1][0]
    area, count, last = 0.0, 0, start
    for t, step in events:
        area += count * (t - last)
        count += step
        last = t
    return area / (end - start), end - start


def pollaczek_khinchine_wait(lam: float, mean_s: float, second_moment_s: float) -> float:
    """Mean time in system for an M/G/1 queue: W = E[S] + lambda E[S^2] / (2 (1 - rho))."""
    rho = lam * mean_s
    if rho >= 1:
        return math.inf
    return mean_s + lam * second_moment_s / (2 * (1 - rho))
