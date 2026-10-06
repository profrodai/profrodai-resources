"""Change a future token, observe earlier logits, then repair the attention rule.

This CPU experiment needs no downloaded data or trained checkpoint. It tests the
architecture's causal boundary, not its language quality or the curve detector.
"""

from __future__ import annotations

import json
import time

import torch

from tinygpt_model_v1 import GPT, Config


def probe() -> dict:
    started = time.perf_counter()
    cfg = {"vocab_size": 64, "block_size": 16, "n_layer": 2, "n_head": 2, "n_embd": 32}
    tokens = torch.randint(0, 64, (1, 16), generator=torch.Generator().manual_seed(1))
    changed = tokens.clone()
    changed[0, -1] = (changed[0, -1] + 1) % 64
    rows = []
    for bug in ("none", "no_causal_mask", "softmax_wrong_dim"):
        torch.manual_seed(0)
        model = GPT(Config(**cfg, bug=bug)).eval()
        with torch.no_grad():
            before = model(tokens)[0]
            after = model(changed)[0]
            earlier_changed = not torch.allclose(before[:, :-1], after[:, :-1], atol=1e-6, rtol=0)
            delta = float((before[:, :-1] - after[:, :-1]).abs().max())
            # Keep every weight and input fixed; repair only each block's attention rule.
            for block in model.blocks:
                block.attn.bug = "none"
            repaired_before = model(tokens)[0]
            repaired_after = model(changed)[0]
            repaired_changed = not torch.allclose(repaired_before[:, :-1], repaired_after[:, :-1], atol=1e-6, rtol=0)
            repaired_delta = float((repaired_before[:, :-1] - repaired_after[:, :-1]).abs().max())
        rows.append(
            {
                "bug": bug,
                "earlierLogitsChanged": earlier_changed,
                "maxEarlierLogitChange": delta,
                "afterRepairEarlierLogitsChanged": repaired_changed,
                "afterRepairMaxChange": repaired_delta,
            }
        )
    return {
        "experiment": "future-token intervention and attention repair v2",
        "device": "cpu",
        "tolerance": {"atol": 1e-6, "rtol": 0.0},
        "torch": torch.__version__,
        "model": cfg,
        "seconds": time.perf_counter() - started,
        "results": rows,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2))
