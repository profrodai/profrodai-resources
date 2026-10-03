# Prof Rod | Train a Tiny GPT on Colab
# Article: https://profrod.ai/articles/train-a-tiny-gpt-on-colab
# Original source and updates: https://github.com/profrodai/profrodai-resources

"""The statistics the tiny-GPT article uses. Standard library only.

Two different intervals, for two different questions:
- `t_interval`: where is the MEAN healthy loss? A 95% confidence interval, mean +/- t * s / sqrt(n).
- `prediction_interval`: where will ONE NEW healthy run land? mean +/- t * s * sqrt(1 + 1/n). This is
  the band a single suspicious run is compared against, so it is the one the bug rule uses.

Both use Student's t with n - 1 degrees of freedom. At n = 5 the bootstrap has only 126 distinct
resamples and its percentile interval is known to be too narrow at small n, so it is not used.
The t intervals assume the final losses of independent seeds are roughly normal.
"""

from __future__ import annotations

import math


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)


def sd(xs: list[float]) -> float:
    """Sample standard deviation (n - 1 in the denominator)."""
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the regularized incomplete beta function (modified Lentz)."""
    tiny, qab, qap, qam = 1e-300, a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-15:
            break
    return h


def betainc(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    front = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x))
    if x < (a + 1) / (a + b + 2):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1 - x) / b


def t_cdf(t: float, df: float) -> float:
    """P(T <= t) for Student's t with df degrees of freedom."""
    tail = 0.5 * betainc(df / 2, 0.5, df / (df + t * t))
    return 1 - tail if t >= 0 else tail


def t_quantile(p: float, df: float) -> float:
    """The t with P(T <= t) = p, by bisection on the CDF."""
    lo, hi = -1e3, 1e3
    for _ in range(200):
        mid = (lo + hi) / 2
        if t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def t_interval(xs: list[float], level: float = 0.95) -> tuple[float, float, float]:
    """(mean, low, high): a t confidence interval for the mean of the population the xs came from."""
    n, m = len(xs), mean(xs)
    half = t_quantile(1 - (1 - level) / 2, n - 1) * sd(xs) / math.sqrt(n)
    return m, m - half, m + half


def prediction_interval(xs: list[float], level: float = 0.95) -> tuple[float, float, float]:
    """(mean, low, high): where one new draw from the same normal population lands, with the given
    probability, when its mean and spread are estimated from the xs."""
    n, m = len(xs), mean(xs)
    half = t_quantile(1 - (1 - level) / 2, n - 1) * sd(xs) * math.sqrt(1 + 1 / n)
    return m, m - half, m + half


def band(curves: list[list[float]], level: float = 0.95) -> dict[str, list[float]]:
    """Per evaluation step, across seeds: the mean, the t interval for the mean, and the
    prediction interval for one new run. Every curve must be evaluated at the same steps."""
    out: dict[str, list[float]] = {k: [] for k in ("mean", "sd", "ciLow", "ciHigh", "piLow", "piHigh")}
    for column in zip(*curves):
        xs = list(column)
        m, lo, hi = t_interval(xs, level)
        _, plo, phi = prediction_interval(xs, level)
        for k, v in zip(out, (m, sd(xs), lo, hi, plo, phi)):
            out[k].append(v)
    return out


def first_flag(values: list[float], low: list[float], high: list[float], steps: list[int], consecutive: int = 2) -> dict | None:
    """The rule: a run is flagged at the first evaluation where it has been outside the healthy
    prediction band, on the same side, for `consecutive` evaluations in a row. Returns the step
    the flag fires at (the last of the run of evaluations) and the side, or None."""
    streak, side = 0, None
    for v, lo, hi, step in zip(values, low, high, steps):
        now = "below" if v < lo else "above" if v > hi else None
        streak = streak + 1 if now is not None and now == side else (1 if now else 0)
        side = now
        if streak >= consecutive:
            return {"step": step, "side": side}
    return None


def initial_loss(vocab_size: int, logit_sd: float = 0.0) -> float:
    """Expected cross-entropy at initialization. With all logits equal the model predicts 1/V for
    every token, so the loss is -ln(1/V) = ln V. With small independent N(0, s^2) logits,
    E[log sum_j exp(z_j)] is about ln V + s^2 / 2 (because E[exp z] = exp(s^2 / 2)), and the target's
    own logit averages 0, so the loss is about ln V + s^2 / 2."""
    return math.log(vocab_size) + logit_sd**2 / 2
