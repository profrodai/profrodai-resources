"""Mechanism and evidence checks, without model loading or synthetic T4 reconstruction."""
import json
import math
from pathlib import Path
import pytest
import sftdpo_mechanism_v1 as M
import sftdpo_stats_v1 as S


def test_first_reply_target_is_predicted_by_last_prompt_position():
    good = M.shifted_reply_targets([10, 11, 12], [20, 21, 2])
    assert good["labels"] == [-100, -100, 20, 21, 2]
    assert good["inputIds"][good["scoredPositions"][0]] == 12
    trap = M.shifted_reply_targets([10, 11, 12], [20, 21, 2], True)
    assert trap["labels"][:2] == [11, 12]
    with pytest.raises(ValueError):
        M.shifted_reply_targets([], [20])


def test_preference_loss_can_fall_while_both_reply_probabilities_fall():
    initial, changed = M.margin_case(0, 0), M.margin_case(-1, -3)
    assert initial["loss"] == pytest.approx(math.log(2))
    assert changed["scaledMargin"] == pytest.approx(0.2)
    assert changed["loss"] < initial["loss"]
    assert changed["chosenProbabilityRatio"] < 1
    assert changed["rejectedProbabilityRatio"] < changed["chosenProbabilityRatio"]


def test_item_average_interval_does_not_resample_training_seeds():
    # Synthetic six-item illustration; deliberately NOT measured T4 correctness.
    rows = [[1]*6, [0]*6, [1]*6]
    band = S.paired_bootstrap(rows, [[0]*6], resamples=100)
    assert band["lo"] == pytest.approx(2/3)
    assert band["hi"] == pytest.approx(2/3)
    verdict = S.compare(rows, [[0]*6], resamples=100)
    assert verdict["pooled"]["lo"] > 0
    assert verdict["perSeed"][1]["lo"] == 0
    assert verdict["real"] is False


def test_negative_pooled_interval_can_fail_the_seed_agreement_rule():
    baseline = [[1]*6]*3
    result = S.compare([[0]*6, [1]*6, [0]*6], baseline, resamples=100)
    assert result["pooled"]["hi"] < 0
    assert result["perSeed"][1]["hi"] == 0
    assert result["real"] is False


def test_original_receipt_hash_task_hashes_means_and_units(tmp_path: Path):
    receipt = M.HERE/"receipts/colab/sftdpo-full-20261003.json"
    result = M.exercise(receipt)
    assert result["recordedT4"]["gainPp"] == pytest.approx(0.4666666667)
    assert result["recordedT4"]["itemBootstrap95Pp"] == pytest.approx([-0.6333333333, 1.5666666667])
    changed = tmp_path/"changed.json"
    changed.write_text(json.dumps(json.loads(receipt.read_text())))
    with pytest.raises(ValueError, match="operator bytes"):
        M.load_receipt(changed)
