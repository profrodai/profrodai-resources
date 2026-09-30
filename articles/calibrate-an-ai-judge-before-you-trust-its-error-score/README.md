# Calibrate an LLM judge before you trust its error score

The measured run behind the article at
https://profrod.ai/articles/calibrate-an-ai-judge-before-you-trust-its-error-score.

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/profrodai/profrodai-resources/blob/main/articles/calibrate-an-ai-judge-before-you-trust-its-error-score/judge_calibration_v1.ipynb)

## What was run (2026-09-30)

1. **Items.** 500 problems sampled (seed 20260930) from the GSM8K test set,
   `openai/grade-school-math` (MIT licence; file SHA-256 recorded in the receipt).
2. **Answers to judge.** Claude Haiku 4.5 answered each problem with a bare number and no
   working. 241 answers were right and 259 wrong. Ground truth is exact: an answer is wrong unless
   it equals the GSM8K reference answer.
3. **Judges.** Claude Haiku 4.5 and Claude Sonnet 5.5 graded every answer without the reference,
   in two conditions: `direct` (asked for one word) and `reasoned` (asked to work the problem, then
   give a verdict). Sonnet 5.5 rejects a forced tool choice, so `direct` cannot force a bare verdict;
   the run records how often each judge actually replied in one word.
4. **Statistics.** `judge_stats_v1.py`, standard library only: confusion matrices, recall on wrong
   and on right answers, Cohen's kappa with a bootstrap interval, Wilson and Clopper–Pearson
   intervals, exact McNemar tests, and the Rogan–Gladen correction tested out of sample.

| Judge | Catches wrong | Passes right | κ | One-word replies | Mean output tokens |
|---|---|---|---|---|---|
| Haiku 4.5, direct | 221/259 | 91/241 | 0.235 | 462/500 | 18.1 |
| Haiku 4.5, reasoned | 254/259 | 240/241 | 0.976 | 0/500 | 231.9 |
| Sonnet 5.5, direct | 254/259 | 239/241 | 0.972 | 8/500 | 79.2 |
| Sonnet 5.5, reasoned | 256/259 | 239/241 | 0.980 | 0/500 | 157.2 |

2,500 requests; USD 2.34 at the list prices recorded in the receipt.

## Files

- `judge_calibration_v1.py`: the run (`sample`, `candidates`, `judge`, `summarize`, `all`).
- `judge_stats_v1.py` and `test_judge_stats_v1.py`: the statistics and their checks against
  statsmodels and scipy.
- `data/gsm8k-test-sample-v1.jsonl`: the 500 sampled problems with their reference answers.
- `results/candidates-v1.jsonl`, `results/judgments-v1.jsonl`, `results/summary-v1.json`: every
  answer, every verdict (with the tail of the judge's reply) and the summary.
- `receipts/judge-calibration-v1.json`: models, settings, tokens, cost and the data source hash.
  Never the key.
- `judge_calibration_v1.ipynb`: recomputes every number from the recorded results; optionally
  reruns a small version on your own key (Colab Secrets panel).

## Reproduce

```bash
uv run --no-project --python 3.12 python judge_calibration_v1.py summarize   # from the recorded results
ANTHROPIC_API_KEY=... uv run --no-project --python 3.12 python judge_calibration_v1.py all --n 500 --max-usd 6
```

A rerun will differ from these numbers by sampling noise in the models' replies; the intervals
in `summary-v1.json` say by how much to expect.
