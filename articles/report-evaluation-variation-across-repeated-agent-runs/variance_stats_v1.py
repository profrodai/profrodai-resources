# Prof Rod | Did A Really Beat B? Eval Variance Across Repeated Runs
# Article: https://profrod.ai/articles/report-evaluation-variation-across-repeated-agent-runs
# Original source and updates: https://github.com/profrodai/profrodai-resources

"""Statistics for an evaluation run many times over the same tasks, in the standard library only.

Data shape throughout: for each system, a list of tasks, and for each task a list of 0/1 outcomes,
one per run (every task has the same number of runs n). Each function is derived on the article
page; test_variance_stats_v1.py checks them against hand-computed values.
"""

from __future__ import annotations

import math
import random
from statistics import fmean, pstdev, stdev

Outcomes = list[list[int]]  # outcomes[task][run] in {0, 1}


def pass_at_k(c: int, n: int, k: int) -> float:
    """Unbiased estimate of P(at least one of k attempts succeeds) from c successes in n runs:
    1 - C(n - c, k) / C(n, k)."""
    if n - c < k:
        return 1.0
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)


def pass_hat_k(c: int, n: int, k: int) -> float:
    """Unbiased estimate of P(all k attempts succeed) from c successes in n runs: C(c, k) / C(n, k)."""
    return math.comb(c, k) / math.comb(n, k)


def mean_curve(outcomes: Outcomes, k: int, estimator) -> float:
    n = len(outcomes[0])
    return fmean(estimator(sum(task), n, k) for task in outcomes)


def task_means(outcomes: Outcomes) -> list[float]:
    return [fmean(task) for task in outcomes]


def naive_se(outcomes: Outcomes) -> float:
    """The standard error if every attempt were independent: sqrt(p(1-p)/(T·n))."""
    attempts = [x for task in outcomes for x in task]
    p = fmean(attempts)
    return math.sqrt(p * (1 - p) / len(attempts))


def clustered_se(outcomes: Outcomes) -> float:
    """The standard error that treats tasks, not attempts, as the independent units: the spread of
    per-task means over sqrt(T). With equal runs per task this is the cluster-robust SE."""
    means = task_means(outcomes)
    return stdev(means) / math.sqrt(len(means))


def icc(outcomes: Outcomes) -> float:
    """Intraclass correlation from a one-way ANOVA: the share of attempt variance that lies
    between tasks. Near 1 means a task's runs mostly agree with each other."""
    t, n = len(outcomes), len(outcomes[0])
    grand = fmean(x for task in outcomes for x in task)
    means = task_means(outcomes)
    msb = n * sum((m - grand) ** 2 for m in means) / (t - 1)
    msw = sum((x - m) ** 2 for task, m in zip(outcomes, means) for x in task) / (t * (n - 1))
    return (msb - msw) / (msb + (n - 1) * msw) if msb + (n - 1) * msw > 0 else 0.0


def design_effect(n: int, rho: float) -> float:
    """How much repeated runs inflate the variance of the mean: 1 + (n - 1)·ICC."""
    return 1 + (n - 1) * rho


def paired_difference(a: Outcomes, b: Outcomes) -> dict:
    """B minus A on the same tasks: the mean per-task difference and its standard error."""
    diffs = [fmean(tb) - fmean(ta) for ta, tb in zip(a, b)]
    return {"mean": fmean(diffs), "se": stdev(diffs) / math.sqrt(len(diffs)), "tasks": len(diffs)}


def bootstrap_difference(a: Outcomes, b: Outcomes, draws: int = 4000, seed: int = 20261001) -> tuple[float, float]:
    """Percentile interval for B minus A, resampling tasks (the clusters), keeping each task's runs."""
    rng = random.Random(seed)
    diffs = [fmean(tb) - fmean(ta) for ta, tb in zip(a, b)]
    t = len(diffs)
    values = sorted(fmean(diffs[rng.randrange(t)] for _ in range(t)) for _ in range(draws))
    return values[int(0.025 * draws)], values[int(0.975 * draws) - 1]


def single_run_rates(outcomes: Outcomes) -> list[float]:
    """The pass rate each run would have reported on its own."""
    n = len(outcomes[0])
    return [fmean(task[r] for task in outcomes) for r in range(n)]


def mcnemar_exact(b: int, c: int) -> float:
    m = b + c
    if m == 0:
        return 1.0
    tail = sum(math.comb(m, i) for i in range(min(b, c) + 1)) / 2**m
    return min(1.0, 2 * tail)


def mcnemar_run(a: Outcomes, b: Outcomes, run: int) -> dict:
    """One run of A against the same-numbered run of B, paired by task."""
    only_a = sum(1 for ta, tb in zip(a, b) if ta[run] and not tb[run])
    only_b = sum(1 for ta, tb in zip(a, b) if tb[run] and not ta[run])
    return {"onlyA": only_a, "onlyB": only_b, "p": mcnemar_exact(only_a, only_b)}


def spread(values: list[float]) -> dict:
    return {"min": min(values), "max": max(values), "sd": pstdev(values)}
