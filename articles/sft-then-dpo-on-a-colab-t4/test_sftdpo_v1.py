"""Checks for the task and the statistics. Run: uv run --no-project --python 3.12 --with pytest pytest -q"""

import math
import random

import sftdpo_stats_v1 as S
import sftdpo_task_v1 as T


def test_solver_follows_precedence_and_shows_each_step():
    steps, answer = T.solve([45, "+", 87, "*", 9])
    assert steps == ["87 * 9 = 783", "45 + 783 = 828"] and answer == 828
    steps, answer = T.solve([20, "-", 30, "-", 5])
    assert steps == ["20 - 30 = -10", "-10 - 5 = -15"] and answer == -15
    for _ in range(200):
        p = T.make_problem(random.Random(_))
        assert p.answer == eval(p.expr)  # the expression is plain Python arithmetic


def test_grader_reads_the_first_answer_line():
    assert T.grade("87 * 9 = 783\n45 + 783 = 828\nAnswer: 828", 828)
    assert T.grade("Answer: -15", -15)
    assert not T.grade("45 + 783 = 828", 828)  # no answer line: wrong
    assert not T.grade("Answer: 827\nAnswer: 828", 828)  # first answer counts


def test_splits_are_disjoint_and_pinned():
    sizes = {"test": 300, "dev": 100, "sft": 500, "dpo": 200, "shots": 3}
    a = T.make_splits(sizes)
    exprs = [p.expr for split in a.values() for p in split]
    assert len(exprs) == len(set(exprs))
    bigger = T.make_splits(sizes | {"sft": 900})
    assert T.split_digest(a["test"]) == T.split_digest(bigger["test"])  # test does not move with train size


def test_wilson_matches_a_known_value():
    lo, hi = S.wilson(50, 100)
    assert abs(lo - 0.4038) < 1e-3 and abs(hi - 0.5962) < 1e-3


def test_mcnemar_exact():
    assert S.mcnemar_exact(0, 0) == 1.0
    assert abs(S.mcnemar_exact(10, 0) - 2 / 1024) < 1e-12
    assert abs(S.mcnemar_exact(3, 3) - 1.0) < 1e-12


def test_paired_bootstrap_sees_a_clear_gain_and_no_gain():
    rng = random.Random(1)
    base = [[int(rng.random() < 0.5) for _ in range(1000)]]
    better = [[1 if x or rng.random() < 0.3 else 0 for x in base[0]] for _ in range(3)]
    c = S.compare(better, base)
    assert c["pooled"]["lo"] > 0 and c["real"]
    same = S.compare([base[0], base[0], base[0]], base)
    assert same["pooled"]["diff"] == 0 and not same["real"]


def test_items_needed_shrinks_as_the_effect_grows():
    assert S.items_needed(0.1, 0.5) == math.ceil((1.959964 * 5) ** 2)
    assert S.items_needed(0.2, 0.5) < S.items_needed(0.1, 0.5)
    assert S.items_needed(0.0, 0.5) is None


def test_dpo_loss_starts_at_log_two_and_falls_with_the_margin():
    assert abs(S.dpo_loss(-5, -7, -5, -7, 0.1) - math.log(2)) < 1e-12
    assert S.dpo_loss(-4, -8, -5, -7, 0.1) < math.log(2) < S.dpo_loss(-6, -6, -5, -7, 0.1)
    assert abs(S.log_sigmoid(-800) + 800) < 1e-9 and S.log_sigmoid(800) == 0.0


def test_full_finetune_of_smollm2_360m_fits_a_t4():
    m = S.full_finetune_gib(params=361_821_120, tokens=16 * 64, layers=32, hidden=960, vocab=49152)
    assert abs(m["weights"] + m["gradients"] + m["adamState"] - 16 * 361_821_120 / 2**30) < 1e-9
    assert m["total"] < 15  # a T4 has 15 GiB usable
