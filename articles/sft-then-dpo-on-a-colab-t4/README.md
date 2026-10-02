# SFT, then DPO, on a 360M model on a free T4

The measured run behind https://profrod.ai/articles/sft-then-dpo-on-a-colab-t4, and feasibility pilot P2 for the course "Post-Training, Measured".

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/profrodai/profrodai-resources/blob/main/articles/sft-then-dpo-on-a-colab-t4/sftdpo_v1.ipynb)

The question: can a reader take a 360M model through SFT and then DPO on a free Colab T4 in one session, and is the measured gain real? Everything runs on an open model with no API key.

## What was run (2026-10-02, Apple M4 Pro GPU, MPS)

- **Model:** SmolLM2-360M, the base model (Apache 2.0), pinned in `data/revisions-v1.json`. Base rather than Instruct, because SmolLM2-360M-Instruct has already been through SFT and DPO. Starting from it would hide what our own SFT does, and its DPO reference would already be a DPO model.
- **Task:** short arithmetic with worked steps, such as `45 + 87 * 9`. The model is trained to answer one operation per line and end with `Answer: 828`. Grading is by exact match on the first `Answer:` line. `sftdpo_task_v1.py` generates every split from a seed, so the items are pinned by code (test sha256 `b4c582b1...` in the receipt), contamination-free by construction, and need no download or license.
- **Arms**, all on the same 1,000 test problems:
  - `base-fewshot`: three worked examples in plain text. This is the baseline.
  - `base-chatml`: zero-shot in the chat template.
  - `sft`: full fine-tuning, one epoch over 3,000 solutions, with the loss on the reply tokens only.
  - `dpo`: built on each SFT model. It samples 4 replies per problem at temperature 1 on 1,000 fresh problems, keeps one correct/incorrect pair per problem that has both, then trains 2 epochs with beta 0.1 against the SFT model.
- **Training code:** written by hand in PyTorch. transformers supplies the model, the tokenizer and `generate`; there is no Trainer and no TRL.
- **Seeds:** 3. The seed sets the SFT data order and DPO's sampling.
- **Precision:** float32 throughout (see "Why float32").
- **Learning rates:** chosen on a separate 300-item dev split with seed 0, before any test run (`results/calibration-v1.jsonl`). SFT: 1e-4. DPO: 3e-6.

## Results (local, MPS; accuracy on 1,000 test items)

| Arm | Seed 0 | Seed 1 | Seed 2 | Mean |
|---|---|---|---|---|
| base-fewshot | 27.5% | | | 27.5% |
| base-chatml | 0.0% | | | 0.0% |
| sft | 79.8% | 82.5% | 80.3% | 80.9% |
| dpo | 81.9% | 82.4% | 81.5% | 81.9% |
| trap-promptloss | 78.0% | 79.4% | 77.6% | 78.3% |
| trap-sysprompt | 79.6% | 81.8% | 80.5% | 80.6% |
| trap-nogenprompt | 79.6% | 81.9% | 80.9% | 80.8% |

How the comparisons are tested (`sftdpo_stats_v1.py`):
- Pairs are matched item by item. The interval is a paired bootstrap over items (10,000 resamples) of the accuracy difference, with each item's correctness averaged over its 3 seeds.
- Each seed also gets its own bootstrap interval and an exact McNemar test.
- **The rule:** a gain is "real" only if the seed-averaged interval excludes zero and so does every seed's own interval. With 3 seeds, an interval over seeds would be too wide to read.

| Comparison | Difference | 95% interval | Per seed (McNemar p) | Real? |
|---|---|---|---|---|
| sft vs base-fewshot | +53.4 pts | +50.4 to +56.4 | +52.3, +55.0, +52.8 (all p < 1e-6) | yes |
| dpo vs sft | +1.1 pts | +0.0 to +2.1 | +2.1 (0.069), -0.1 (1.0), +1.2 (0.18) | no |
| trap-promptloss vs sft | -2.5 pts | -4.0 to -1.1 | -1.8 (0.21), -3.1 (0.014), -2.7 (0.039) | no: seed 0's interval includes zero |
| trap-sysprompt vs sft | -0.2 pts | -0.8 to +0.3 | all intervals include zero | no |
| trap-nogenprompt vs sft | -0.1 pts | -0.6 to +0.4 | all intervals include zero | no |

What this says:
- **SFT works, by a wide margin.** It lifts exact match from 27.5% (few-shot base) to 80.9%. The base model's errors include ignoring precedence (it writes `75 - 65 * 2 = 15`, then `15 * 2 = 30`); SFT teaches the steps.
- **DPO's gain is not established at this size.** It added +1.1 points, with an interval that touches zero and one seed at -0.1. The seed-to-seed spread is as large as the effect:
  - Seed 1's DPO barely moved: its final loss was 0.690, against log 2 = 0.693.
  - The other two seeds pushed the rejected replies down by 1.3 and 2.1 nats.
  - At the observed per-item spread, an effect this size needs about 990 items for a normal-approximation interval to exclude zero. That is the n used here, so it is a coin flip. Several thousand items, or a stronger DPO setting, are needed to settle it.
- **Planted trap 1, loss on the prompt tokens, costs 2.5 points** (interval -4.0 to -1.1). It hurt in all three seeds, but seed 0's own interval includes zero, so by the rule above it is "likely, not proven". The errors are arithmetic slips: with the loss spread over the prompt's random digits, the reply gets a smaller share of the gradient.
- **Planted traps 2 and 3, template mismatches at eval, cost nothing here.** One adds a default system prompt the model never saw (SmolLM2-Instruct's template). The other drops the `<|im_start|>assistant` line. The intervals are tight around zero (about ±0.5 points).
  - This is a measured null, not a demonstration. On a narrow task with a fixed prompt, this model is robust to these two mismatches.
  - The course should not claim they always hurt. It should show the measurement and use a mismatch that does bite, such as training with the closing `<|im_end|>` missing (a candidate for the next run).
- **What failed in calibration:** DPO at lr 1e-5 collapsed from 79.7% to 60.7% on dev. The chosen replies' log-probability fell 4.4 nats while the rejected ones fell 10.6, so the margin grew while both likelihoods sank. This is the drift that Unit 7 of the syllabus names, recorded in `results/calibration-v1.jsonl`.
- **Reply length did not change:** 29.8 tokens on average for SFT and for DPO. Every reply ended with `<|im_end|>`, so there is no length exploitation at this size.

## Memory: why full fine-tuning, not LoRA

Full fine-tuning with AdamW in float32 needs 16 bytes per parameter for weights, gradients and the two moments. For 361,821,120 parameters that is 5.39 GiB.

Activations add about 17 float32 values of the hidden size per token per layer, plus the logits, which cost 12 bytes per vocabulary entry per token (`full_finetune_gib` in `sftdpo_stats_v1.py`).

| Phase | Tokens per step | Estimated total | Peak measured on MPS* |
|---|---|---|---|
| SFT, 16 sequences | about 1,100 | 8.1 GiB | 7.2 GiB |
| DPO, 16 pairs in one pass | up to about 3,200 | up to 13.4 GiB | 10.2 to 10.4 GiB |
| DPO, two micro-batches of 8 pairs (what the code now does) | up to about 1,600 | up to 9.4 GiB | 5.7 GiB in the check below |

\* MPS peaks are sampled after each forward and backward, so they are lower bounds. On CUDA the code records `max_memory_allocated`.

A T4 has 15 GiB, so full fine-tuning fits and LoRA is not needed. LoRA would save the 4.0 GiB of gradients and AdamW state, not the activations.

After the local run, DPO's 16-pair batch was split into two micro-batches of 8 with gradient accumulation, to leave headroom on the T4. `results/microbatch-check-v1.json` shows that the two give the same gradient: relative difference 1.7e-6, cosine 1.0. The local DPO numbers above come from the one-pass version.

## Why float32

The T4 has no fast bfloat16, and float16 is unsafe for this model (`results/activations-v1.json`, measured in float32):
- The largest MLP output on the training format is 20,560.
- While sampling from left-padded prompts it reaches 48,449, 74% of float16's 65,504.
- After four SFT steps under float16 autocast, it reached 72,781, and sampling under float16 failed with NaN probabilities.

So the default runs in float32 everywhere. `--precision fp16` and `bf16` remain as knobs.

## Timing

Local timings are indicative only: the machine was shared (1-minute load average 0.7 to 10.7 during the runs; per-run loads are in the receipt), and another pilot used the same GPU.

| Phase (local, MPS, float32) | Minutes |
|---|---|
| SFT, per seed | 7.9 to 10.0 |
| DPO, per seed (2.3 of it sampling pairs) | 5.2 to 5.4 |
| Eval of 1,000 items | 0.6 (trained models), 2.0 to 3.3 (base) |
| Whole default run, all recorded runs | 76.6 |

The expected T4 time is about 25 to 45 minutes for the whole notebook. This is an estimate, not a measurement; the operator's Colab receipt replaces it. The basis:
- **Training:** 6 × parameters × tokens, from the recorded token counts: 3.4e15 FLOP over 9 training runs. At 2 to 4 TFLOP/s achieved, out of the T4's 8.1 peak in float32, that is 14 to 29 minutes. The M4 Pro achieved about 0.8 TFLOP/s on SFT here.
- **Decoding:** about 10,000 decode steps over all evals and pair sampling, at 30 to 60 ms per step (1.45 GB of weights per step at 320 GB/s, plus 93 GFLOP for a batch of 128, plus Python overhead). That is 5 to 10 minutes.
- **Overhead:** about 5 minutes for install, the model download, and saving and loading checkpoints.

## Files

- `sftdpo_run_v1.py`: the experiment.
  - Notebook sections: `base`, `sft`, `eval-sft`, `dpo`, `eval-dpo`, `trap`, or `all`.
  - Pilot steps: `calibrate` (dev split only), `activations`, `check-microbatch`, `summarize`, `receipt`.
  - It resumes: finished runs are skipped.
- `sftdpo_task_v1.py`: the task generator and the grader.
- `sftdpo_stats_v1.py`: Wilson intervals, the paired bootstrap, exact McNemar, the items-needed estimate, the scalar DPO loss and the memory estimate.
- `test_sftdpo_v1.py`: tests for the task and the stats.
- `results/runs-v1.jsonl`: one row per run. It has per-item correctness, minutes, peak memory, the load average at start and end, and the training curves.
- `results/generations-v1.jsonl`: every reply.
- `results/summary-v1.json`: every number above.
- `results/calibration-v1.jsonl`: the dev-split learning-rate choice.
- `receipts/sftdpo-v1.json`: the model revision, data hashes, package versions, device, settings, minutes and load per run, notes, and the $0 cost.
- `sftdpo_v1.ipynb`: the Colab notebook. Its sections are setup, base eval, SFT, eval, DPO, eval, the traps and the receipt; it ends by downloading the receipt.

Run it yourself (Python 3.12):

    uv run --no-project --python 3.12 --with 'transformers==5.18.0' --with torch \
        python sftdpo_run_v1.py all --size default
    uv run --no-project --python 3.12 --with pytest pytest -q test_sftdpo_v1.py

`--size quick` is a smoke test of every code path; `--size large` uses 2,000 test items and 5 seeds.
