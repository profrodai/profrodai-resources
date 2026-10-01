# Prof Rod | Test Whether a Prior Verdict Anchors Your AI Reviewer
# Article: https://profrod.ai/articles/choose-fresh-context-for-an-independent-ai-reviewer
# Original source and updates: https://github.com/profrodai/profrodai-resources

"""The review items: implementations whose correctness is known, because a sandboxed test says so.

For each of the 30 tasks in review_tasks_v1.py there is a correct implementation (REFERENCE,
below). From it the builder makes:
- correct items: the reference, and two copies with the local names changed, so the reviewer
  cannot match an item by its surface;
- buggy items: the three seeded bugs per task in review_bugs_v1.py (sorting forgotten, n - 1 for
  n, a window one short). A seeded bug becomes an item only if the held-out tests, run in the
  operating-system sandbox, fail on it with a wrong answer.
Every item is checked: correct items must pass every held-out test, buggy items must fail one.

    uv run --no-project --python 3.12 python review_items_v1.py   # writes data/items-v1.jsonl
"""

from __future__ import annotations

import ast
import hashlib
import json
import random
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import review_sandbox_v1 as X  # noqa: E402
import review_tasks_v1 as T  # noqa: E402
from review_bugs_v1 import ALTERNATIVES, BUGS  # noqa: E402

SEED = 20261001
SCRATCH = Path(tempfile.gettempdir()) / "profrod-review-scratch"

REFERENCE = {
    "clamp": "def clamp(x, lo, hi):\n    if x < lo:\n        return lo\n    if x > hi:\n        return hi\n    return x\n",
    "mean": "def mean(xs):\n    total = 0\n    for x in xs:\n        total += x\n    return total / len(xs)\n",
    "median": "def median(xs):\n    s = sorted(xs)\n    n = len(s)\n    if n % 2 == 1:\n        return s[n // 2]\n    return (s[n // 2 - 1] + s[n // 2]) / 2\n",
    "variance": "def variance(xs):\n    m = sum(xs) / len(xs)\n    total = 0\n    for x in xs:\n        total += (x - m) ** 2\n    return total / len(xs)\n",
    "moving_average": "def moving_average(xs, k):\n    out = []\n    for i in range(len(xs) - k + 1):\n        out.append(sum(xs[i:i + k]) / k)\n    return out\n",
    "normalize": "def normalize(xs):\n    total = sum(xs)\n    return [x / total for x in xs]\n",
    "softmax": "import math\n\n\ndef softmax(xs):\n    exps = [math.exp(x) for x in xs]\n    total = sum(exps)\n    return [e / total for e in exps]\n",
    "argmax": "def argmax(xs):\n    best = 0\n    for i in range(1, len(xs)):\n        if xs[i] > xs[best]:\n            best = i\n    return best\n",
    "precision_at_k": "def precision_at_k(ranked, relevant, k):\n    hits = 0\n    for item in ranked[:k]:\n        if item in relevant:\n            hits += 1\n    return hits / k\n",
    "recall_at_k": "def recall_at_k(ranked, relevant, k):\n    hits = 0\n    for item in ranked[:k]:\n        if item in relevant:\n            hits += 1\n    return hits / len(relevant)\n",
    "f1_score": "def f1_score(precision, recall):\n    if precision + recall == 0:\n        return 0.0\n    return 2 * precision * recall / (precision + recall)\n",
    "accuracy": "def accuracy(preds, labels):\n    correct = 0\n    for p, y in zip(preds, labels):\n        if p == y:\n            correct += 1\n    return correct / len(labels)\n",
    "dot": "def dot(a, b):\n    total = 0\n    for x, y in zip(a, b):\n        total += x * y\n    return total\n",
    "cosine_similarity": "import math\n\n\ndef cosine_similarity(a, b):\n    num = sum(x * y for x, y in zip(a, b))\n    na = math.sqrt(sum(x * x for x in a))\n    nb = math.sqrt(sum(y * y for y in b))\n    return num / (na * nb)\n",
    "l2_norm": "import math\n\n\ndef l2_norm(xs):\n    return math.sqrt(sum(x * x for x in xs))\n",
    "word_count": "def word_count(text):\n    return len(text.split())\n",
    "first_words": "def first_words(text, n):\n    words = text.split()\n    return ' '.join(words[:n])\n",
    "is_palindrome": "def is_palindrome(s):\n    chars = [c.lower() for c in s if c.isalnum()]\n    return chars == chars[::-1]\n",
    "dedupe": "def dedupe(xs):\n    seen = set()\n    out = []\n    for x in xs:\n        if x not in seen:\n            seen.add(x)\n            out.append(x)\n    return out\n",
    "chunk": "def chunk(xs, n):\n    out = []\n    for i in range(0, len(xs), n):\n        out.append(xs[i:i + n])\n    return out\n",
    "flatten": "def flatten(xss):\n    out = []\n    for xs in xss:\n        out.extend(xs)\n    return out\n",
    "running_max": "def running_max(xs):\n    out = []\n    best = None\n    for x in xs:\n        if best is None or x > best:\n            best = x\n        out.append(best)\n    return out\n",
    "nearest_rank_percentile": "import math\n\n\ndef nearest_rank_percentile(xs, q):\n    s = sorted(xs)\n    rank = math.ceil(q / 100 * len(s))\n    return s[max(rank, 1) - 1]\n",
    "exponential_moving_average": "def exponential_moving_average(xs, alpha):\n    out = []\n    for i, x in enumerate(xs):\n        if i == 0:\n            out.append(x)\n        else:\n            out.append(alpha * x + (1 - alpha) * out[-1])\n    return out\n",
    "safe_divide": "def safe_divide(a, b):\n    if b == 0:\n        return 0.0\n    return a / b\n",
    "top_k_indices": "def top_k_indices(xs, k):\n    order = sorted(range(len(xs)), key=lambda i: (-xs[i], i))\n    return order[:k]\n",
    "cumulative_sum": "def cumulative_sum(xs):\n    out = []\n    total = 0\n    for x in xs:\n        total += x\n        out.append(total)\n    return out\n",
    "mode": "def mode(xs):\n    counts = {}\n    for x in xs:\n        counts[x] = counts.get(x, 0) + 1\n    best = max(counts.values())\n    return min(x for x in counts if counts[x] == best)\n",
    "brier_score": "def brier_score(probs, outcomes):\n    total = 0.0\n    for p, o in zip(probs, outcomes):\n        total += (p - o) ** 2\n    return total / len(outcomes)\n",
    "pass_at_k": "import math\n\n\ndef pass_at_k(n, c, k):\n    if n - c < k:\n        return 1.0\n    return 1 - math.comb(n - c, k) / math.comb(n, k)\n",
}

def renamed(source: str, salt: int) -> str:
    """The same function with its local variable names changed (arguments and the function name stay)."""
    tree = ast.parse(source)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef))
    keep = {a.arg for a in fn.args.args} | {fn.name, "math", "sum", "len", "range", "sorted", "zip", "max", "min", "enumerate", "set"}
    locals_ = sorted({n.id for n in ast.walk(fn) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)} - keep)
    names = ["acc", "value", "result", "count", "idx", "item", "buf", "cur", "tmp", "run"]
    rng = random.Random(SEED + salt)
    rng.shuffle(names)
    mapping = {old: f"{names[i % len(names)]}{salt}" for i, old in enumerate(locals_)}
    for node in ast.walk(fn):
        if isinstance(node, ast.Name) and node.id in mapping:
            node.id = mapping[node.id]
    return ast.unparse(tree) + "\n"


def held_out_result(task: T.Task, source: str) -> dict:
    return X.run_tests({"solution.py": source, "test_held_out.py": T.test_file(task, task.held_out, strict=True)}, "test_held_out", scratch=SCRATCH)


def build() -> list[dict]:
    items = []
    for task in T.TASKS:
        ref = REFERENCE[task.name]
        variants = [ref, renamed(ref, 1), renamed(ref, 2)]
        if len(set(variants)) < 3:
            variants = [ref, *ALTERNATIVES[task.name]]
        for k, source in enumerate(variants):
            r = held_out_result(task, source)
            if not r["tests"] or any(v != "pass" for v in r["tests"].values()):
                raise ValueError(f"{task.name}: correct item {k} fails its held-out tests: {r}")
            change = "none" if k == 0 else ("rewritten equivalently" if task.name in ALTERNATIVES else "renamed locals")
            items.append({"task": task.name, "label": "correct", "change": change, "source": source})
        for what, source in BUGS[task.name]:
            r = held_out_result(task, source)
            tests = r["tests"]
            # Usable: the module imports and at least one held-out test fails on a wrong answer.
            wrong = [v for v in tests.values() if v.startswith("fail")]
            if not wrong or "__import__" in tests:
                raise ValueError(f"{task.name}: seeded bug '{what}' is not caught by the held-out tests: {tests}")
            items.append({"task": task.name, "label": "buggy", "change": what, "source": source, "failing": len(wrong)})
    if len({it["source"] for it in items}) != len(items):
        raise ValueError("duplicate item sources")
    for it in items:
        it["id"] = hashlib.sha256((it["task"] + it["source"]).encode()).hexdigest()[:12]
        it["doc"] = next(t.doc for t in T.TASKS if t.name == it["task"])
    return items


if __name__ == "__main__":
    rows = build()
    path = HERE / "data" / "items-v1.jsonl"
    path.parent.mkdir(exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(f"{len(rows)} items ({sum(r['label'] == 'buggy' for r in rows)} buggy) -> {path}")
