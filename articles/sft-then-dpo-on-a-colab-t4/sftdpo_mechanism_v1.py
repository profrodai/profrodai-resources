"""Short P2 exercise: reply-only shifted targets and relative DPO margins; standard library only.

Synthetic token IDs/log-probabilities illustrate the mechanism. They are not T4 model outputs.
The recorded comparison is read verbatim; raw item-level T4 results are not available here.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import sftdpo_stats_v1 as S
import sftdpo_task_v1 as T

HERE = Path(__file__).resolve().parent
RECEIPT_SHA256 = "a32dfc7af44c70d627d83009fd5db2e9f90839a10ec5b5893130aa8b94b23ca7"


def shifted_reply_targets(prompt: list[int], reply: list[int], prompt_loss: bool = False) -> dict:
    """Token-ID analogue of Lab.example plus the explicit causal shift. No model needed."""
    if not prompt or not reply:
        raise ValueError("prompt and reply must be nonempty")
    ids = prompt + reply
    labels = (prompt if prompt_loss else [-100] * len(prompt)) + reply
    return {"inputIds": ids[:-1], "labels": labels[1:], "scoredPositions": [i for i, t in enumerate(labels[1:]) if t != -100]}


def margin_case(chosen_drift: float, rejected_drift: float, beta: float = 0.1) -> dict:
    """Synthetic reference log-probabilities -10/-12; reply likelihoods may both fall."""
    rc, rr = -10.0, -12.0
    return {"chosenDrift": chosen_drift, "rejectedDrift": rejected_drift,
            "scaledMargin": beta * (chosen_drift - rejected_drift),
            "loss": S.dpo_loss(rc + chosen_drift, rr + rejected_drift, rc, rr, beta),
            "chosenProbabilityRatio": math.exp(chosen_drift), "rejectedProbabilityRatio": math.exp(rejected_drift)}


def load_receipt(path: Path) -> dict:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != RECEIPT_SHA256:
        raise ValueError("receipt does not match the preserved operator bytes")
    r = json.loads(raw)
    splits = T.make_splits(r["data"]["sizes"], r["hyperparameters"]["operands"], r["data"]["seed"])
    for name, expected in r["data"]["sha256"].items():
        if T.split_digest(splits[name]) != expected:
            raise ValueError(f"task hash mismatch: {name}")
    for arm in r["results"]["arms"].values():
        if not math.isclose(S.mean(arm["accuracyPerSeed"]), arm["accuracyMean"], abs_tol=1e-12):
            raise ValueError("receipt mean inconsistent with per-seed accuracies")
    return r


def exercise(receipt: Path) -> dict:
    r = load_receipt(receipt)
    sft = r["results"]["arms"]["sft"]["accuracyPerSeed"]
    dpo = r["results"]["arms"]["dpo"]["accuracyPerSeed"]
    comparison = r["results"]["comparisons"]["dpo vs sft"]
    return {"syntheticMechanism": {"replyOnly": shifted_reply_targets([10, 11, 12], [20, 21, 2]),
            "promptLoss": shifted_reply_targets([10, 11, 12], [20, 21, 2], True),
            "initial": margin_case(0, 0), "bothFall": margin_case(-1, -3)},
            "recordedT4": {"receiptSha256": RECEIPT_SHA256, "trainingSeeds": r["seeds"], "testItems": r["data"]["sizes"]["test"],
                "sftAccuracy": sft, "dpoAccuracy": dpo, "seedGainsPp": [100 * (b-a) for b,a in zip(dpo,sft)],
                "gainPp": 100 * comparison["diff"], "itemBootstrap95Pp": [100*comparison[k] for k in ("lo", "hi")],
                "receiptReal": comparison["real"], "intervalPopulation": "test items, conditional on these fixed training seeds",
                "rawT4ItemsAvailable": False}}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--receipt", type=Path, default=HERE/"receipts/colab/sftdpo-full-20261003.json")
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    result = json.dumps(exercise(args.receipt), indent=2)+"\n"
    if args.output:
        args.output.write_text(result)
    print(result, end="")
