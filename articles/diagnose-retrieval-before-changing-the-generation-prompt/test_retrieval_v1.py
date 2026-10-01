"""Checks for stage attribution and BM25. Run: uv run --no-project --python 3.12 --with pytest pytest -q"""

import retrieval_stats_v1 as S
from retrieval_run_v1 import bm25

# The article's hand-labeled fixture: d2 is the one relevant abstract.
CASES = {
    "A": ({"retrieved": ["d1", "d3"], "reranked": [], "prompt": [], "correct": False}, "retrieval"),
    "B": ({"retrieved": ["d1", "d2"], "reranked": ["d1"], "prompt": ["d1"], "correct": False}, "reranking"),
    "C": ({"retrieved": ["d1", "d2"], "reranked": ["d1", "d2"], "prompt": ["d1", "d2"], "correct": False}, "generation"),
    "D": ({"retrieved": ["d1", "d2"], "reranked": ["d1", "d2"], "prompt": ["d1"], "correct": False}, "prompt_assembly"),
    "E": ({"retrieved": ["d1", "d2"], "reranked": ["d1", "d2"], "prompt": ["d1", "d2"], "correct": True}, "none"),
}


def test_article_fixture():
    for name, (case, stage) in CASES.items():
        assert S.diagnose(case, {"d2"}) == stage, name


def test_any_relevant_document_keeps_the_query_alive():
    case = {"retrieved": ["d1", "d5"], "reranked": ["d5"], "prompt": ["d5"], "correct": True}
    assert S.diagnose(case, {"d2", "d5"}) == "none"
    assert S.diagnose(case, set()) == "label_missing"


def test_bm25_ranks_the_matching_document_first():
    corpus = {"1": {"title": "Vitamin D", "text": "vitamin D lowers fracture risk in older adults"},
              "2": {"title": "Sleep", "text": "sleep duration and memory consolidation"},
              "3": {"title": "Exercise", "text": "exercise improves bone density"}}
    ranked = bm25(corpus, {"q": "Does vitamin D reduce fractures?"})
    assert ranked["q"][0] == "1"


def test_wilson_matches_the_article():
    lo, hi = S.wilson(11, 15)
    assert round(lo, 3) == 0.480 and round(hi, 3) == 0.891
