# Prof Rod | Post-Training, Measured: SFT Then DPO on a Colab T4
# Course: https://profrod.ai/courses
# Original source and updates: https://github.com/profrodai/profrodai-resources

"""The task: short arithmetic with worked steps, graded by exact match. Standard library only.

A problem is an expression such as `45 + 87 * 9` with the usual precedence. The reply the model is
trained to give shows one operation per line and ends with the answer:

    87 * 9 = 783
    45 + 783 = 828
    Answer: 828

The grader reads the first `Answer: <integer>` in the reply and compares it with the true value.
Every split is generated from a fixed seed, so the eval items are pinned by this file alone, and the
splits are made disjoint by construction (no expression appears in two of them).
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from dataclasses import dataclass

INSTRUCTION = "Work one operation per line, then end with 'Answer: <number>'."
ANSWER = re.compile(r"Answer:\s*(-?\d+)")
SPLIT_ORDER = ("test", "dev", "sft", "dpo", "shots")


@dataclass(frozen=True)
class Problem:
    expr: str
    steps: tuple[str, ...]
    answer: int


def solve(tokens: list) -> tuple[list[str], int]:
    """Evaluate [n, op, n, op, n, ...] with * before + and -, left to right, one step per line."""
    toks = list(tokens)
    steps = []
    while "*" in toks:
        i = toks.index("*")
        a, b = toks[i - 1], toks[i + 1]
        steps.append(f"{a} * {b} = {a * b}")
        toks[i - 1 : i + 2] = [a * b]
    while len(toks) > 1:
        a, op, b = toks[0], toks[1], toks[2]
        value = a + b if op == "+" else a - b
        steps.append(f"{a} {op} {b} = {value}")
        toks[0:3] = [value]
    return steps, toks[0]


def make_problem(rng: random.Random, operands: int = 3) -> Problem:
    """Two-digit numbers, except that the right-hand factor of a product is a single digit."""
    ops = [rng.choice("+-*") for _ in range(operands - 1)]
    nums = [rng.randint(2, 9) if i > 0 and ops[i - 1] == "*" else rng.randint(10, 99) for i in range(operands)]
    tokens: list = [nums[0]]
    for op, n in zip(ops, nums[1:]):
        tokens += [op, n]
    steps, answer = solve(tokens)
    return Problem(" ".join(str(t) for t in tokens), tuple(steps), answer)


def make_splits(sizes: dict[str, int], operands: int = 3, seed: int = 20261002) -> dict[str, list[Problem]]:
    """Generate the splits in SPLIT_ORDER, each from its own seeded stream, skipping any expression
    already used, so the test split does not depend on the size of the training splits."""
    seen: set[str] = set()
    splits = {}
    for name in SPLIT_ORDER:
        rng = random.Random(f"{seed}-{operands}-{name}")
        items: list[Problem] = []
        while len(items) < sizes.get(name, 0):
            p = make_problem(rng, operands)
            if p.expr not in seen:
                seen.add(p.expr)
                items.append(p)
        splits[name] = items
    return splits


def prompt_text(p: Problem) -> str:
    return f"Compute {p.expr}. {INSTRUCTION}"


def solution_text(p: Problem) -> str:
    return "\n".join([*p.steps, f"Answer: {p.answer}"])


def extract_answer(text: str) -> int | None:
    m = ANSWER.search(text)
    return int(m.group(1)) if m else None


def grade(text: str, answer: int) -> bool:
    return extract_answer(text) == answer


def split_digest(items: list[Problem]) -> str:
    """sha256 of a split's expressions and answers, recorded in the receipt and checked on Colab."""
    payload = json.dumps([[p.expr, p.answer] for p in items], separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()
