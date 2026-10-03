"""Checks for tinygpt_stats_v1.py. Standard library only.

Run: uv run --no-project --python 3.12 --with pytest pytest -q test_tinygpt_stats_v1.py
"""

import math
import random

import tinygpt_stats_v1 as S


def test_t_quantiles_match_published_tables():
    # Two-sided 95% critical values: df 2, 3, 4, 9, 30.
    for df, expected in ((2, 4.302653), (3, 3.182446), (4, 2.776445), (9, 2.262157), (30, 2.042272)):
        assert abs(S.t_quantile(0.975, df) - expected) < 1e-5
    assert abs(S.t_quantile(0.5, 4)) < 1e-6
    assert abs(S.t_cdf(0.0, 7) - 0.5) < 1e-12


def test_t_interval_by_hand():
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]  # mean 3, sd sqrt(2.5)
    m, lo, hi = S.t_interval(xs)
    half = 2.776445 * math.sqrt(2.5) / math.sqrt(5)
    assert m == 3.0 and abs(lo - (3 - half)) < 1e-5 and abs(hi - (3 + half)) < 1e-5


def test_prediction_interval_is_wider_by_sqrt_n_plus_one():
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    _, lo, hi = S.t_interval(xs)
    _, plo, phi = S.prediction_interval(xs)
    assert abs((phi - plo) / (hi - lo) - math.sqrt(5 + 1)) < 1e-9


def test_prediction_interval_covers_new_draws_at_its_level():
    rng = random.Random(0)
    hits, trials = 0, 4000
    for _ in range(trials):
        xs = [rng.gauss(2.0, 0.05) for _ in range(5)]
        _, lo, hi = S.prediction_interval(xs)
        hits += lo <= rng.gauss(2.0, 0.05) <= hi
    assert abs(hits / trials - 0.95) < 0.015


def test_band_is_per_step():
    curves = [[5.0, 3.0, 2.0], [5.0, 3.2, 2.1], [5.0, 2.8, 1.9]]
    b = S.band(curves)
    assert b["mean"] == [5.0, 3.0, 2.0]
    assert b["sd"][0] == 0.0 and b["piLow"][0] == b["piHigh"][0] == 5.0
    assert b["piLow"][1] < 3.0 < b["piHigh"][1]


def test_flag_needs_two_evaluations_in_a_row_on_one_side():
    steps = [0, 50, 100, 150, 200]
    low, high = [1.0] * 5, [2.0] * 5
    assert S.first_flag([1.5, 2.5, 1.5, 2.5, 1.5], low, high, steps) is None  # never twice in a row
    assert S.first_flag([1.5, 0.5, 2.5, 1.5, 1.5], low, high, steps) is None  # below then above: not one side
    assert S.first_flag([1.5, 0.5, 0.4, 1.5, 1.5], low, high, steps) == {"step": 100, "side": "below"}
    assert S.first_flag([1.5, 1.5, 1.5, 3.0, math.inf], low, high, steps) == {"step": 200, "side": "above"}


def test_initial_loss_is_ln_v_plus_half_the_logit_variance():
    assert S.initial_loss(4096) == math.log(4096)
    # Monte Carlo: cross-entropy of N(0, s^2) logits over V classes against a random target.
    rng = random.Random(1)
    V, s, trials, total = 4096, 0.4, 200, 0.0
    for _ in range(trials):
        z = [rng.gauss(0.0, s) for _ in range(V)]
        total += math.log(sum(math.exp(x) for x in z)) - z[0]
    assert abs(total / trials - S.initial_loss(V, s)) < 0.01
