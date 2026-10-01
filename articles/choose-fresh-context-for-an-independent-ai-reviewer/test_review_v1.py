"""Checks for the review items, the verdict parser and the statistics.
Run: uv run --no-project --python 3.12 --with pytest pytest -q"""

import json
from pathlib import Path

from review_run_v1 import ANCHOR, mcnemar_exact, request, verdict, wilson

ITEMS = [json.loads(x) for x in (Path(__file__).parent / "data" / "items-v1.jsonl").read_text().splitlines()]


def test_items_are_balanced_and_unique():
    assert sum(i["label"] == "buggy" for i in ITEMS) == 90
    assert sum(i["label"] == "correct" for i in ITEMS) == 90
    assert len({i["id"] for i in ITEMS}) == len(ITEMS)


def test_conditions_differ_by_one_line():
    item = ITEMS[0]
    clean = request(item, "clean")[1]["content"]
    for c in ("anchored-pass", "anchored-fail"):
        anchored = request(item, c)[1]["content"]
        assert anchored == clean + "\n\n" + ANCHOR[c]
    assert request(item, "clean")[0] == request(item, "anchored-pass")[0]


def test_verdict_parser_takes_the_last_verdict():
    assert verdict("Looks fine.\nVERDICT: PASS") == "PASS"
    assert verdict("VERDICT: PASS at first glance, but ... VERDICT: **FAIL**") == "FAIL"
    assert verdict("verdict: fail") == "FAIL"
    assert verdict("I think it is correct.") == "NONE"


def test_stats():
    lo, hi = wilson(45, 90)
    assert abs((lo + hi) / 2 - 0.5) < 1e-9
    assert abs(mcnemar_exact(3, 14) - 1668 / 131072) < 1e-12  # the article's worked example
