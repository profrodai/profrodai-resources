"""Checks for the model, the planted bugs and the training loop, on the CPU with a tiny model.

Run: uv run --no-project --python 3.12 --with 'torch==2.14.1' --with 'tokenizers==0.23.2' --with 'numpy==2.3.3' \\
         --with pytest pytest -q test_tinygpt_model_v1.py
"""

import math

import pytest
import torch

import tinygpt_run_v1 as R
from tinygpt_model_v1 import GPT, Config, flops_per_token

TINY = {"vocab_size": 64, "block_size": 16, "n_layer": 2, "n_head": 2, "n_embd": 32}


def logits_for(bug: str, idx: torch.Tensor) -> torch.Tensor:
    torch.manual_seed(0)
    model = GPT(Config(**TINY, bug=bug)).eval()
    with torch.no_grad():
        return model(idx)[0]


def test_parameter_count_by_hand():
    d, L, V, T = 32, 2, 64, 16
    per_block = 4 * d * d + 4 * d + 8 * d * d + 5 * d + 4 * d  # attention, MLP, two LayerNorms
    expected = V * d + T * d + L * per_block + 2 * d  # the tied head adds nothing
    assert GPT(Config(**TINY)).num_params() == expected
    assert flops_per_token(Config(**TINY)) == 6 * (L * 12 * d * d + V * d) + 6 * L * 2 * T * d


@pytest.mark.parametrize("bug,leaks", [("none", False), ("no_causal_mask", True), ("softmax_wrong_dim", True)])
def test_future_tokens_leak_only_with_the_attention_bugs(bug, leaks):
    idx = torch.randint(0, 64, (1, 16), generator=torch.Generator().manual_seed(1))
    changed = idx.clone()
    changed[0, -1] = (changed[0, -1] + 1) % 64  # change only the last token
    a, b = logits_for(bug, idx), logits_for(bug, changed)
    earlier_moved = not torch.allclose(a[0, :-1], b[0, :-1], atol=1e-6)
    assert earlier_moved == leaks


def test_initial_loss_is_near_ln_v():
    torch.manual_seed(0)
    model = GPT(Config(**TINY))
    idx = torch.randint(0, 64, (8, 17))
    with torch.no_grad():
        logits, loss = model(idx[:, :-1], idx[:, 1:])
    predicted = math.log(64) + float(logits.std()) ** 2 / 2
    assert abs(float(loss) - predicted) < 0.05


def test_schedule_warms_up_then_decays_to_the_floor():
    assert R.lr_at(0, 100, 1.0, 0.1, 10) == pytest.approx(0.1)
    assert R.lr_at(9, 100, 1.0, 0.1, 10) == pytest.approx(1.0)
    assert R.lr_at(10, 100, 1.0, 0.1, 10) == pytest.approx(1.0)
    assert R.lr_at(99, 100, 1.0, 0.1, 10) == pytest.approx(0.1)


@pytest.fixture
def fake_data(monkeypatch, tmp_path):
    tokens = torch.randint(0, 64, (20_000,), generator=torch.Generator().manual_seed(2)).to(torch.int16)
    monkeypatch.setattr(R, "load_tokens", lambda part: tokens)
    monkeypatch.setattr(R, "CACHE", tmp_path)
    monkeypatch.setattr(R, "VOCAB", 64)
    monkeypatch.setitem(R.TRAIN, "eval_every", 2)
    monkeypatch.setitem(R.TRAIN, "eval_batches", 2)
    monkeypatch.setitem(R.TRAIN, "warmup_steps", 2)
    return {k: v for k, v in TINY.items() if k != "vocab_size"}


def test_resume_from_a_checkpoint_matches_an_uninterrupted_run(fake_data):
    kw = {"steps": 6, "device": "cpu", "model_size": fake_data, "batch_size": 4, "out": None}
    whole = R.train(0, "none", "trial", ckpt_every=2, tag="whole", **kw)
    stopped = R.train(0, "none", "trial", ckpt_every=2, tag="split", stop_after=4, **kw)
    assert stopped["stoppedAt"] == 4
    resumed = R.train(0, "none", "trial", ckpt_every=2, tag="split", resume=True, **kw)
    assert resumed["evalSteps"] == whole["evalSteps"] == [0, 2, 4, 6]
    assert resumed["trainLoss"] == whole["trainLoss"] and resumed["valLoss"] == whole["valLoss"]


def test_without_zero_grad_the_gradients_pile_up(fake_data):
    kw = {"steps": 6, "device": "cpu", "model_size": fake_data, "batch_size": 4, "out": None}
    healthy = R.train(0, "none", "trial", **kw)
    buggy = R.train(0, "no_zero_grad", "trial", **kw)
    assert buggy["trainLoss"][0] == healthy["trainLoss"][0]  # the first step is identical
    assert buggy["gradNorm"][1] != healthy["gradNorm"][1]  # the second step sees two steps of gradient
