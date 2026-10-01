# Prof Rod | Find the Failing RAG Stage Before You Change the Prompt
# Article: https://profrod.ai/articles/diagnose-retrieval-before-changing-the-generation-prompt
# Original source and updates: https://github.com/profrodai/profrodai-resources

"""Stage attribution and the statistics the retrieval article uses. Standard library only."""

from __future__ import annotations

import math
from math import comb


def diagnose(case: dict, relevant: set[str] | None) -> str:
    """Name the first stage at which every relevant abstract was lost (the article's function,
    for queries with one or more relevant abstracts: a stage keeps the query alive if any
    relevant abstract survives it)."""
    if not relevant:
        return "label_missing"
    if case.get("endpoint_error"):
        return "endpoint_unavailable"
    if not relevant & set(case["retrieved"]):
        return "retrieval"
    if not relevant & set(case["reranked"]):
        return "reranking"
    if not relevant & set(case["prompt"]):
        return "prompt_assembly"
    return "none" if case["correct"] else "generation"


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


def mcnemar_exact(b: int, c: int) -> float:
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2**n)
