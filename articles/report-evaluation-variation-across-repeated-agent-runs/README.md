# Did A really beat B? Eval variance across repeated runs

The measured run behind https://profrod.ai/articles/report-evaluation-variation-across-repeated-agent-runs.

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/profrodai/profrodai-resources/blob/main/articles/report-evaluation-variation-across-repeated-agent-runs/eval_variance_v1.ipynb)

## What was run (2026-09-30)

- 100 AIME problems (numbers 6 to 15 of each exam), sampled with seed 20261001 from
  `di-zhang-fdu/AIME_1983_2024` at revision `3e2cc86`. Answers are integers, so grading is exact.
  Only ids and answers are stored here; the problem text is fetched from the pinned revision.
- Three systems at OpenAI reasoning effort `medium`, capped at 8,000 output tokens:
  - GPT-6 Luna;
  - GPT-6 Luna with the instruction reworded;
  - GPT-5.6 Luna with the original instruction.
- Each system ran every problem 10 times: 3,000 requests, USD 3.06 at list price.

| System | Pass rate | Single runs | Clustered SE | ICC | pass@10 | pass^10 |
|---|---|---|---|---|---|---|
| GPT-6 Luna | 91.8% | 88% to 98% | 1.7 pts | 0.31 | 99.0% | 66.0% |
| GPT-6 Luna, reworded | 89.5% | 87% to 94% | 1.8 pts | 0.28 | 98.0% | 53.0% |
| GPT-5.6 Luna | 87.2% | 84% to 91% | 1.8 pts | 0.20 | 99.0% | 49.0% |

Paired by problem, with a bootstrap over problems:
- **GPT-6 Luna minus GPT-5.6 Luna:** +4.6 points (95% interval +1.5 to +7.7).
- **The reworded prompt minus the original:** −2.3 points (−4.3 to −0.3).

We expected the rewording to change nothing. It did not come out that way.

## Files

- `eval_variance_v1.py`: the run (`sample`, `run`, `summarize`, `all`). It is resumable, because attempts are appended as they finish.
- `variance_stats_v1.py` and `test_variance_stats_v1.py`: the statistics and their checks.
- `data/aime-tasks-v1.jsonl`: the 100 problem ids and answers.
- `results/attempts-v1.jsonl`: all 3,000 attempts (answer, correct, status, output tokens).
- `results/summary-v1.json`: every number above.
- `receipts/eval-variance-v1.json`: models, settings, tokens, cost and the dataset hash. It never contains the key.
- `eval_variance_v1.ipynb`: recomputes every number from the recorded attempts. It can also rerun a smaller version on your own OpenAI key.
