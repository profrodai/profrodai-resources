# Prof Rod | Calibrate an LLM Judge Before You Trust Its Score
# Article: https://profrod.ai/articles/calibrate-an-ai-judge-before-you-trust-its-error-score
# Original source and updates: https://github.com/profrodai/profrodai-resources

"""The statistics the article derives, in the standard library only (so it runs as-is on Colab).

Every function here has a derivation on the article page; the tests in test_judge_stats_v1.py
check each against a value computed by hand or by a reference implementation.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

Z95 = 1.959963984540054  # the 0.975 quantile of the standard normal


def wald(k: int, n: int, z: float = Z95) -> tuple[float, float]:
    """The textbook interval p ± z·sqrt(p(1-p)/n). Shown in the article to fail near 0 and 1."""
    p = k / n
    half = z * math.sqrt(p * (1 - p) / n)
    return max(0.0, p - half), min(1.0, p + half)


def wilson(k: int, n: int, z: float = Z95) -> tuple[float, float]:
    """Wilson score interval: the p for which |p̂ - p| ≤ z·sqrt(p(1-p)/n), solved for p."""
    if n == 0:
        return 0.0, 1.0
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def _binom_cdf(k: int, n: int, p: float) -> float:
    """P(X ≤ k) for X ~ Binomial(n, p), summed in log space for stability."""
    if p <= 0:
        return 1.0
    if p >= 1:
        return 1.0 if k >= n else 0.0
    total = 0.0
    log_p, log_q = math.log(p), math.log1p(-p)
    for i in range(k + 1):
        total += math.exp(
            math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1) + i * log_p + (n - i) * log_q
        )
    return min(1.0, total)


def clopper_pearson(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """The exact interval: the p whose binomial tails put k at probability alpha/2, by bisection."""
    lower = 0.0
    if k > 0:
        # lower: P(X ≥ k | p) = alpha/2; P(X ≥ k) grows with p
        lo, hi = 0.0, 1.0
        for _ in range(100):
            mid = (lo + hi) / 2
            if 1 - _binom_cdf(k - 1, n, mid) < alpha / 2:
                lo = mid
            else:
                hi = mid
        lower = (lo + hi) / 2
    upper = 1.0
    if k < n:
        # upper: P(X ≤ k | p) = alpha/2; P(X ≤ k) falls with p
        lo, hi = 0.0, 1.0
        for _ in range(100):
            mid = (lo + hi) / 2
            if _binom_cdf(k, n, mid) > alpha / 2:
                lo = mid
            else:
                hi = mid
        upper = (lo + hi) / 2
    return lower, upper


@dataclass(frozen=True)
class Confusion:
    """Judge verdicts against ground truth. Positive = the answer is wrong (what a judge must catch)."""

    tp: int  # wrong answer, judge says INCORRECT
    fn: int  # wrong answer, judge says CORRECT (the dangerous miss)
    fp: int  # right answer, judge says INCORRECT
    tn: int  # right answer, judge says CORRECT

    @property
    def n(self) -> int:
        return self.tp + self.fn + self.fp + self.tn

    def accuracy(self) -> float:
        return (self.tp + self.tn) / self.n

    def recall_wrong(self) -> float:
        """Of the wrong answers, the share the judge caught."""
        return self.tp / (self.tp + self.fn) if self.tp + self.fn else float("nan")

    def recall_right(self) -> float:
        """Of the right answers, the share the judge passed."""
        return self.tn / (self.tn + self.fp) if self.tn + self.fp else float("nan")

    def kappa(self) -> float:
        """Cohen's kappa: observed agreement corrected for the agreement two independent raters
        with these marginals would reach by chance."""
        n = self.n
        po = (self.tp + self.tn) / n
        judge_wrong = (self.tp + self.fp) / n
        truth_wrong = (self.tp + self.fn) / n
        pe = judge_wrong * truth_wrong + (1 - judge_wrong) * (1 - truth_wrong)
        return (po - pe) / (1 - pe) if pe < 1 else float("nan")


def confusion(truth_wrong: list[bool], judge_wrong: list[bool]) -> Confusion:
    tp = sum(t and j for t, j in zip(truth_wrong, judge_wrong))
    fn = sum(t and not j for t, j in zip(truth_wrong, judge_wrong))
    fp = sum((not t) and j for t, j in zip(truth_wrong, judge_wrong))
    tn = sum((not t) and (not j) for t, j in zip(truth_wrong, judge_wrong))
    return Confusion(tp, fn, fp, tn)


def kappa_bootstrap(
    truth_wrong: list[bool], judge_wrong: list[bool], draws: int = 2000, seed: int = 20260930
) -> tuple[float, float]:
    """Percentile bootstrap interval for kappa, resampling items with replacement."""
    rng = random.Random(seed)
    n = len(truth_wrong)
    values = []
    for _ in range(draws):
        idx = [rng.randrange(n) for _ in range(n)]
        k = confusion([truth_wrong[i] for i in idx], [judge_wrong[i] for i in idx]).kappa()
        if not math.isnan(k):
            values.append(k)
    values.sort()
    return values[int(0.025 * len(values))], values[int(0.975 * len(values)) - 1]


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value: under H0 the b + c discordant pairs split as Binomial(b+c, 1/2)."""
    m = b + c
    if m == 0:
        return 1.0
    tail = _binom_cdf(min(b, c), m, 0.5)
    return min(1.0, 2 * tail)
