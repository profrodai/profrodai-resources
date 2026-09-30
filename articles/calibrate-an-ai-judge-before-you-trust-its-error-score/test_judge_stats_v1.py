"""Checks for judge_stats_v1 against values computed by hand or by scipy/statsmodels (quoted)."""

import math

from judge_stats_v1 import Confusion, clopper_pearson, confusion, mcnemar_exact, wald, wilson


def close(a, b, tol=1e-4):
    return abs(a - b) < tol


def test_wilson_matches_reference():
    # statsmodels proportion_confint(8, 10, method="wilson") = (0.4902, 0.9433)
    lo, hi = wilson(8, 10)
    assert close(lo, 0.4902) and close(hi, 0.9433)


def test_wald_collapses_at_zero():
    assert wald(0, 20) == (0.0, 0.0)
    lo, hi = wilson(0, 20)
    assert lo == 0.0 and close(hi, 0.1611)


def test_clopper_pearson_matches_reference():
    # scipy.stats.binomtest(8, 10).proportion_ci(method="exact") = (0.4439, 0.9748)
    lo, hi = clopper_pearson(8, 10)
    assert close(lo, 0.4439) and close(hi, 0.9748)
    assert clopper_pearson(0, 20)[0] == 0.0 and close(clopper_pearson(0, 20)[1], 0.1684)


def test_kappa_hand_example():
    # 40 agree-wrong, 10 miss, 5 false alarm, 45 agree-right: po = .85, pe = .45*.5 + .55*.5 = .5
    c = Confusion(tp=40, fn=10, fp=5, tn=45)
    assert close(c.kappa(), 0.7)
    assert close(c.recall_wrong(), 0.8) and close(c.recall_right(), 0.9)


def test_confusion_counts():
    c = confusion([True, True, False, False], [True, False, True, False])
    assert (c.tp, c.fn, c.fp, c.tn) == (1, 1, 1, 1)


def test_mcnemar_exact():
    # b=1, c=9: 2 * P(X <= 1 | 10, .5) = 2 * 11/1024
    assert close(mcnemar_exact(1, 9), 22 / 1024)
    assert mcnemar_exact(0, 0) == 1.0
    assert math.isclose(mcnemar_exact(5, 5), 1.0)
