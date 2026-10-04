# SFT improved this model. Did DPO add anything?

Companion to https://profrod.ai/articles/sft-then-dpo-on-a-colab-t4 and feasibility pilot P2 for Post-Training, Measured. The original PyTorch experiment is retained; this revision supplies a short CPU route and the recorded October 3 T4 comparison. No new training was run for the article checkpoint.

[Open notebook v2 in Colab](https://colab.research.google.com/github/profrodai/profrodai-resources/blob/main/articles/sft-then-dpo-on-a-colab-t4/sftdpo_v2.ipynb). Start with its standard-library CPU cells; GPU reproduction is optional and later in the notebook. Original notebook v1 remains unchanged.

## Run the short route

```bash
python sftdpo_mechanism_v1.py
```

It verifies the preserved operator receipt's byte hash, regenerates all five task split hashes and checks recorded means. Synthetic token IDs show the shifted reply boundary; synthetic log-probabilities show why DPO loss can fall while both reply probabilities fall. These are not T4 model outputs. No pip install, model download, GPU or API key is required.

Write 200–400 words explaining the target boundary, reference-relative margin, measured difference in percentage points, resampling unit and limits. The article/notebook contain the same exercise and conclusion boundaries.

## Recorded T4 comparison — October 3, 2026

SmolLM2-360M **base**, revision `f8027fd0eaeea54caa13c31d31b9fdc459c38b49`, Apache-2.0. Full fine-tuning in float32; three seeds; same 1,000 test problems. Split expression strings are disjoint by construction, which does not prove absence of similar arithmetic in pretraining. The grader extracts the first integer after `Answer:`; it does not validate the worked trace.

| Condition | Seed 0 | Seed 1 | Seed 2 | Mean |
| --- | --- | --- | --- | --- |
| Base, three examples/plain text | 27.5% | — | — | 27.5% |
| Base, zero-shot ChatML | 0.0% | — | — | 0.0% |
| Reply-only SFT | 79.2% | 81.9% | 80.2% | 80.43% |
| DPO after SFT | 79.9% | 82.0% | 80.8% | 80.90% |
| Prompt targets included in SFT | 77.5% | 78.9% | 76.9% | 77.77% |
| Added system prompt at eval | 78.8% | 81.9% | 80.3% | 80.33% |
| Assistant opening removed at eval | 78.9% | 82.8% | 80.6% | 80.77% |

| Comparison | Difference (percentage points) | Recorded 95% item interval | Receipt `real` |
| --- | --- | --- | --- |
| SFT − three-example base | +52.93 | +49.87 to +56.00 | true |
| DPO − SFT | +0.47 | −0.63 to +1.57 | false |
| Prompt-loss SFT − SFT | −2.67 | −4.07 to −1.33 | false |
| Added system prompt − SFT | −0.10 | −0.70 to +0.50 | false |
| Removed assistant opening − SFT | +0.33 | −0.10 to +0.77 | false |

The paired bootstrap resamples **items**, retaining each item's paired correctness difference averaged across these fixed three seeds. It does not resample training seeds. The 3,000 seed-item evaluations are not 3,000 independent test problems. `real` additionally requires every seed's own paired interval to exclude zero in the pooled direction. This explains how prompt loss can have a negative pooled interval yet `real: false`; the aggregate T4 receipt omits the individual endpoints, so it cannot identify the failing seed interval.

DPO's incremental gain remains unresolved. Intervals including zero do not establish equivalence or robustness to arbitrary template changes. No new tuning or expanded experiment is authorized by this checkpoint.

The original T4 receipt is preserved unchanged in `receipts/colab/sftdpo-full-20261003.json`, SHA-256 `a32dfc7af44c70d627d83009fd5db2e9f90839a10ec5b5893130aa8b94b23ca7`. Its adjacent provenance record describes missing raw correctness, generations, sampled pairs and training curves. Never use earlier MPS raw outputs to reconstruct missing T4 observations.

## Implementation and reproduction

`sftdpo_run_v1.py` supplies explicit PyTorch training loops. transformers supplies model, tokenizer and generation; there is no Trainer or TRL. SFT: 3,000 examples, one epoch, batch 16, lr 1e-4. DPO: four sampled replies per problem, one correct/incorrect pair when both exist; two epochs, batch 16, micro-batch eight, lr 3e-6, beta 0.1. The SFT reference scores are computed once and held fixed; sampled IDs are preserved, never re-tokenized. Pair counts are absent from the aggregate T4 receipt.

Earlier local MPS dev calibration (`results/calibration-v1.jsonl`) chose settings before the test comparisons. `results/runs-v1.jsonl`, `results/generations-v1.jsonl`, `results/summary-v1.json` and `receipts/sftdpo-v1.json` are **October 2 MPS evidence**, kept intact. Their DPO gain was also unresolved under the per-seed rule. Activation and micro-batch checks are local MPS diagnostics, not new T4 precision experiments.

T4 recorded sections total 41.42 minutes, excluding setup/notebook overhead. SFT took about 3.23 minutes per seed; DPO recorded sections 3.83–4.00. SFT allocated peaks: 7.62–7.63 GiB; largest DPO peak: 9.71 GiB. USD $0 and no API calls are operator-reported in the receipt; no guarantee of GPU availability, pricing or timings elsewhere.

Optional full route (downloads weights, trains and evaluates):

```bash
uv run --no-project --python 3.13 --with 'transformers==5.18.0' --with torch \
    python sftdpo_run_v1.py all --size default
```

Use the notebook for guided full reproduction. Retain raw run/generation files as well as its receipt. `--size quick` is a smoke test, not evidence for the published measurements.

## Figures and focused checks

`figures-v1/` contains standalone SVG/PNG/WebP exports. `sftdpo_figures_v1.py` reads the hash-checked T4 aggregate receipt and plots recorded per-seed accuracies and pooled item intervals, without invented raw rows or seed intervals:

```bash
uv run --no-project --with matplotlib --with Pillow \
    python sftdpo_figures_v1.py --output figures-v1
uv run --no-project --with pytest pytest -q \
    test_sftdpo_v1.py test_sftdpo_mechanism_v1.py
```

The focused checks cover the causal target boundary, relative likelihood counterexample, conditional item bootstrap, negative pooled interval with failed seed agreement, and unchanged receipt/data hashes. Original scripts and consumed notebooks remain unchanged.

## Historical SVG candidate, superseded October 4, 2026

The article now uses the site's actual native chalkboard components. `figures-v2/` contains their source-bound SVGs, 2× PNG exports and HTML context with legends/tables. Expand all four tiny-GPT curve panels when reading the HTML. These figures use the unchanged T4 receipt; they do not reconstruct unavailable observations or strengthen the conclusions above. Older paper-style figure versions and their consumed generators are retained as historical artifacts after the operator rejected their visual style.

To reproduce these historical exports from their recorded site checkout, with Node 24, installed site dependencies and Chromium:

```bash
CHROME_PATH=/path/to/chromium node tools/export_house_figures_v1.mjs --site /path/to/profrod-site
```

The command writes the two article figure directories together and records the exact site commit, component/shared-source hashes, receipt hashes, embedded-font license and output hashes. No training or model download is required. Read each plotted board with its adjacent HTML context. The site enforces its figure-brand gate before builds, verification and normal pushes; maintainer/operator visual review still applies.

## Responsive house WebPs, October 4, 2026

`figures-v3/` is the current review candidate. It copies the site's exact WebP bytes at 320, 640, 960 and 1520 pixels, with descriptive HTML, legends, tables and editable `.source.svg` authoring files. These SVGs are not the website delivery format. The manifest binds every image and receipt hash to the exact committed site tree. All four tiny-GPT panels are expanded in the exported context.

Reproduce both article exports from a clean, committed site checkout with Node 24 and installed site dependencies:

```bash
node tools/export_house_figures_v2.mjs --site /path/to/profrod-site
```

This version replaces the rejected paper-style and SVG delivery candidates. Original exports, consumed generators, notebooks and the operator's T4 receipt bytes remain intact. No training, model download or new measurement is performed. Mechanical validation does not establish operator or council aesthetic acceptance; the website publication holds remain in force.
