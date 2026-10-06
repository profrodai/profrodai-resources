"""A repair must restore the causal boundary without replacing the model weights."""

from tinygpt_causality_v2 import probe


def test_future_token_intervention_and_repairs():
    rows = probe()["results"]
    assert [r["earlierLogitsChanged"] for r in rows] == [False, True, True]
    assert all(not r["afterRepairEarlierLogitsChanged"] for r in rows)
