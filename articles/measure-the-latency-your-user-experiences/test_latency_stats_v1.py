"""Checks for latency_stats_v1.py. Run: uv run --no-project --python 3.12 --with pytest pytest -q"""

import latency_stats_v1 as S


def test_percentile_is_an_observed_value():
    xs = list(range(1, 101))
    assert S.percentile(xs, 0.95) == 95
    assert S.percentile(xs, 0.5) == 50
    assert S.percentile([3.0], 0.95) == 3.0


def test_p95_interval_needs_enough_trials():
    assert S.percentile_interval(list(range(30)), 0.95) is None  # 30 trials cannot bound a p95
    lo, hi = S.percentile_interval([float(i) for i in range(1, 201)], 0.95)
    assert 180 <= lo < 190 < hi <= 200  # near the article's ranks 184 to 196


def test_quadratic_fit_recovers_coefficients():
    xs = [64, 128, 256, 512, 1024, 2048, 4096]
    ys = [0.01 + 2e-5 * x + 3e-9 * x * x for x in xs]
    a, b, c = S.fit_quadratic(xs, ys)
    assert abs(a - 0.01) < 1e-9 and abs(b - 2e-5) < 1e-12 and abs(c - 3e-9) < 1e-15


def test_littles_law_on_a_hand_computed_trace():
    # Two requests: [0, 2] and [1, 4]. Area = 2 + 3 = 5 over a window of 4, so L = 1.25.
    L, span = S.time_average_in_system([0.0, 1.0], [2.0, 4.0])
    assert span == 4.0 and abs(L - 1.25) < 1e-12
    # lambda = 2 / 4, W = (2 + 3) / 2: lambda * W = 1.25 as well.
    assert abs((2 / 4) * (5 / 2) - L) < 1e-12


def test_pollaczek_khinchine_reduces_to_mm1():
    # Exponential service with mean 1: E[S^2] = 2, so W = 1 / (1 - rho).
    for rho in (0.3, 0.5, 0.9):
        assert abs(S.pollaczek_khinchine_wait(rho, 1.0, 2.0) - 1 / (1 - rho)) < 1e-12
