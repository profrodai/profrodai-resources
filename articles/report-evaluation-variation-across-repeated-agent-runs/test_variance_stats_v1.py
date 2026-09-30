"""Checks for variance_stats_v1 against values worked by hand."""

import math

import variance_stats_v1 as V


def close(a, b, tol=1e-9):
    return abs(a - b) < tol


def test_pass_at_k_and_hat_k():
    # 3 successes in 5 runs: pass@2 = 1 - C(2,2)/C(5,2) = 1 - 1/10; pass^2 = C(3,2)/C(5,2) = 3/10
    assert close(V.pass_at_k(3, 5, 2), 0.9)
    assert close(V.pass_hat_k(3, 5, 2), 0.3)
    assert V.pass_at_k(0, 5, 3) == 0.0 and V.pass_hat_k(5, 5, 3) == 1.0
    assert V.pass_at_k(4, 5, 2) == 1.0  # only one failure: any two attempts include a success


def test_standard_errors():
    # Two tasks, one always passes and one never: 20 attempts, p = .5
    data = [[1] * 10, [0] * 10]
    assert close(V.naive_se(data), math.sqrt(0.25 / 20))
    assert close(V.clustered_se(data), math.sqrt(0.5) / math.sqrt(2))  # stdev([1, 0]) = sqrt(.5)
    assert close(V.icc(data), 1.0)


def test_icc_zero_when_tasks_identical():
    data = [[1, 0, 1, 0], [1, 0, 1, 0], [0, 1, 0, 1]]
    assert V.icc(data) < 0.1


def test_paired_difference_and_mcnemar():
    a = [[1, 1], [0, 0], [1, 0]]
    b = [[1, 1], [1, 1], [1, 1]]
    d = V.paired_difference(a, b)
    assert close(d["mean"], (0 + 1 + 0.5) / 3)
    run0 = V.mcnemar_run(a, b, 0)
    assert (run0["onlyA"], run0["onlyB"]) == (0, 1)
    assert close(V.mcnemar_exact(1, 9), 22 / 1024)


def test_single_run_rates():
    assert V.single_run_rates([[1, 0], [1, 1]]) == [1.0, 0.5]
