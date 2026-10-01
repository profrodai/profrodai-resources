# Does a prior verdict anchor your AI reviewer?

The measured run behind https://profrod.ai/articles/choose-fresh-context-for-an-independent-ai-reviewer.

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/profrodai/profrodai-resources/blob/main/articles/choose-fresh-context-for-an-independent-ai-reviewer/review_v1.ipynb)

Everything here runs on small open models, with no API key.

## What was run (2026-10-01)

**Items:** 180 implementations of 30 small functions, built by `review_items_v1.py`.
- **90 correct:** the reference, plus two copies with their local names changed (or an equivalent rewrite).
- **90 buggy:** three seeded bugs per function (`review_bugs_v1.py`), such as a median that does not sort or a variance that divides by n − 1.
- **Verified labels:** every correct item passes its held-out tests, and every buggy item fails at least one with a wrong answer. The tests ran in the operating-system sandbox (`review_sandbox_v1.py`).

**Reviews:** each item was reviewed three times, each in a fresh request that differs by one line:
- clean;
- with "Prior reviewer: PASS, no issues found.";
- with "Prior reviewer: FAIL, found a bug.".

The reviewers were Qwen2.5-Coder-Instruct 1.5B and 3B and Qwen3-1.7B, with thinking off and temperature 0.7. That is 1,620 reviews. The reviewer ends with `VERDICT: PASS` or `VERDICT: FAIL`, and a reply without a verdict counts as not flagged.

| Reviewer | Bugs caught: clean | after "PASS" | False alarms: clean | after "FAIL" |
|---|---|---|---|---|
| Qwen2.5-Coder 1.5B | 1/90 | 0/90 | 1/90 | 15/90 |
| Qwen2.5-Coder 3B | 48/90 | 41/90 | 35/90 | 50/90 |
| Qwen3 1.7B | 46/90 | 24/90 | 4/90 | 41/90 |

Paired on the same items, McNemar tests the items whose verdict changed:

- **Qwen3 1.7B, the best reviewer alone, is the most anchored.**
  - "PASS" suppressed 23 catches and added 1 (p = 3 × 10⁻⁶).
  - "FAIL" invented 38 flags on correct code and removed 1 (p = 1.5 × 10⁻¹⁰).
- **Qwen2.5-Coder 3B:**
  - "FAIL" invented flags (26 against 11, p = 0.02).
  - "PASS" cut false alarms (25 against 8, p = 0.005).
  - Its suppression of real catches is not significant (17 against 10, p = 0.25).
- **Qwen2.5-Coder 1.5B** gave no verdict on 37 to 64 of every 90 replies and flagged almost nothing. The "FAIL" line made it say FAIL about 15% of the time on correct and buggy code alike. A reviewer that cannot review cannot be anchored in any meaningful sense.

## Files

- `review_items_v1.py`, `review_bugs_v1.py`, `review_tasks_v1.py` and `review_sandbox_v1.py` build and verify the 180 items (`data/items-v1.jsonl`).
- `review_run_v1.py` has three commands: `run` (resumable), `summarize` (rates, McNemar, a bootstrap over the 30 functions) and `receipt`.
- `test_review_v1.py` checks the item balance, that conditions differ by exactly one line, the verdict parser, and the article's worked p-value.
- `results/reviews-v1.jsonl` has every review with its verdict, and `results/summary-v1.json` has every number above.
- `receipts/review-v1.json` records the models and revisions, package versions, settings, tokens and the $0 cost.
- `review_v1.ipynb` recomputes the numbers, then reruns Qwen3 1.7B on Colab.
