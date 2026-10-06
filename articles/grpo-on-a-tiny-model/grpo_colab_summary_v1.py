# Prof Rod | GRPO on a Tiny Model
# Recompute the downloaded T4 receipt's count and seed statistics, without training.
"""Keep the original receipt intact; no raw item-bootstrap or rollout reconstruction is implied."""
from pathlib import Path
import hashlib
import json
import math
from grpo_stats_v1 import mcnemar_exact, t_interval


def summarize() -> dict:
    receipt = Path(__file__).parent / "receipts/colab/grpo-full-20261003.json"
    original = receipt.read_bytes()
    source_hash = hashlib.sha256(original).hexdigest()
    assert source_hash == json.loads(receipt.with_suffix(".provenance.json").read_text())["sha256"]
    data = json.loads(original)  # Original Python JSON uses NaN for an unavailable one-seed CI.
    assert data["environment"]["device"] == "Tesla T4"
    rows = data["summary"]["runs"]
    strict = [r for r in rows.values() if r["config"]["verifier"] == "strict"]
    planted = [r for r in rows.values() if r["config"]["verifier"] == "planted"]
    assert sorted(r["config"]["seed"] for r in strict) == [1, 2, 3, 4, 5]
    assert len(planted) == 1
    for row in rows.values():
        for scores in row["paired"].values():
            before, after = scores["base"], scores["trained"]
            assert before["n"] == after["n"] == 200
            for result in [before, after]:
                assert math.isclose(result["rate"], result["correct"] / result["n"], abs_tol=1e-12)
            assert scores["gained"] - scores["lost"] == after["correct"] - before["correct"]
            assert math.isclose(scores["diff"], (after["correct"] - before["correct"]) / 200, abs_tol=1e-12)
            assert math.isclose(scores["mcnemarP"], mcnemar_exact(scores["lost"], scores["gained"]), rel_tol=1e-12)
    intervals = {}
    recorded = data["summary"]["groups"]["qwen05-units-strict-lora16-n30-test"]
    for metric in ["strict", "content"]:
        rates = [r["paired"][metric]["trained"]["rate"] for r in strict]
        differences = [r["paired"][metric]["diff"] for r in strict]
        measured = {"trainedMeanT95": t_interval(rates), "diffMeanT95": t_interval(differences)}
        for field, values in measured.items():
            assert all(math.isclose(a, b, abs_tol=1e-12) for a, b in zip(values, recorded[metric][field]))
        intervals[metric] = measured
    return {
        "sourceSha256": hashlib.sha256(original).hexdigest(), "strictSeeds": len(strict), "plantedSeeds": len(planted),
        "recomputedSeedIntervals": intervals, "trainingMinutes": sum(r["trainMinutes"] for r in rows.values()),
        "sectionMinutes": data["minutesBySection"]["total"], "rawItemBootstrapRecomputed": False,
        "rawRolloutHistorySupplied": False, "singlePlantedSeedInterval": None,
    }


if __name__ == "__main__":
    print(json.dumps(summarize(), indent=2, allow_nan=False))
