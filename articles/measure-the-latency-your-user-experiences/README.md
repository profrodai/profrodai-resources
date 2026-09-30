# Where the wait goes: prefill, decode, a prefix cache and a queue

The measured run behind https://profrod.ai/articles/measure-the-latency-your-user-experiences.

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/profrodai/profrodai-resources/blob/main/articles/measure-the-latency-your-user-experiences/latency_v1.ipynb)

Everything here runs on small open models, with no API key: on a free Colab T4 GPU, or on a laptop GPU.

## What was run (2026-09-30, with one rerun on 2026-10-01)

Two models were used: Qwen2.5-Instruct at 0.5B and at 1.5B parameters. Both are pinned by revision in `data/revisions-v1.json` and run in float16 on an Apple M4 Pro GPU (MPS). A hand-written greedy loop times each phase separately, synchronizing the GPU before every clock read. Warm-up calls run first and are not recorded.

| Experiment | What it does | 1.5B result |
|---|---|---|
| `prefill` | Time to first token for 64 to 4,096 tokens, 20 trials each; fitted a + bP + cP² | 1.29 s at 2,048 tokens, 2.71 s at 4,096; the quadratic term is 10% of prefill at 4,096 |
| `decode` | 256 greedy tokens after 128 and 2,048 tokens of context | 22 ms per step at either context length (about 45 tokens/s) |
| `cache` | 2,048-token prefix plus a 32-token question, 200 trials each of cold, warm (prefix KV cache reused) and changed (first prefix token altered) | p50 1,368 ms cold, 62 ms warm, 1,352 ms changed. Warm and cold agree on the next token 20 of 20 times |
| `queue` | One worker; Poisson arrivals at five utilizations; 200 requests each. L is sampled every 5 ms | Mean time in system 1.26 to 2.42 s up to ρ ≈ 0.8, within 7% of Pollaczek–Khinchine. At ρ = 0.95 it was 5.5 s against a predicted 10.2 (not yet in steady state). L and λW agree within 1.6% |

**The rerun:** the 0.5B model's first queue calibration included one-off GPU warm-up (0.89 s measured, against about 0.5 s served), so its utilization levels missed their targets. The rerun adds five untimed warm-up calls; the receipt records it.

## Files

- `latency_run_v1.py` runs `prefill`, `decode`, `cache`, `queue` and `all` with `--quick`, then `summarize`, `receipt` and `revisions`.
- `latency_stats_v1.py` and `test_latency_stats_v1.py` hold the percentile, the order-statistic interval for a quantile, the quadratic fit, the time-average L and the Pollaczek–Khinchine wait.
- `results/*.jsonl` has every timing, and `results/summary-v1.json` has every number above.
- `receipts/latency-v1.json` records the models, revisions, package versions, device, settings, dates and the $0 cost.
- `latency_v1.ipynb` recomputes the numbers from the recorded timings, then reruns a quick version on the runtime's own GPU.

Run it yourself (Python 3.12). Timings need a quiet machine, so run nothing else heavy alongside:

    uv run --no-project --python 3.12 --with 'transformers==5.18.0' --with torch --with accelerate \
        python latency_run_v1.py all --model Qwen/Qwen2.5-0.5B-Instruct
    uv run --no-project --python 3.12 python latency_run_v1.py summarize
