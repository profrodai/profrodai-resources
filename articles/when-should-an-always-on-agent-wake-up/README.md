# When should an always-on agent wake up?

Credential-free companion to the held article at https://www.profrod.ai/articles/when-should-an-always-on-agent-wake-up. The page remains unavailable until its publication review; this companion is independently runnable.

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/profrodai/profrodai-resources/blob/main/articles/when-should-an-always-on-agent-wake-up/jev_wake_gate_v7.ipynb)

## Start in Google Colab

Open the badge, connect a **CPU runtime**, and run the sections in order. **Runtime → Run all** also completes the default lab without prompts. Setup automatically downloads three small public source files from immutable commit `9c7a224f9ee334085e480911297276651c9cc18d` and verifies their SHA-256 hashes before importing code. No helper upload, pip installation, GPU, API key, model-service account or Drive mount is needed. A Google account is needed to connect to Colab's hosted runtime.

The notebook walks through prediction, tuning-only threshold selection, the missed test event, a threshold intervention, the Brier denominator, full workflow costs and a price intervention, malformed responses and trusted approval controls, a constructed Jev-style request, and SQLite journal observations. Finish with a short recommendation and download the results ZIP in the last section. It contains the canonical receipt, separate interventions, worksheet, source hashes, runtime information and synthetic journals. A fresh setup creates a new run; it does not overwrite earlier results or resume an interrupted run. Colab runtime files are temporary, so retain the ZIP outside the runtime.

The lab uses only Python's standard library, supports Python 3.10+, and also runs in local Jupyter. Its verified source cache can run offline after the initial download. If acquisition fails, reconnect and rerun setup; if hashes disagree, use a fresh cache path rather than disabling validation. In Colab, the Files sidebar is an alternative if the browser blocks the final download.

## Predict, then run

A constructed score of 0.08 defers an event that describes an unresolved failure. Would you let the agent sleep? Keep your answer before running:

```bash
python3 wake_gate_v3.py --out ./wake-gate-run-01
```

Run the CLI inside this folder with Python 3.10 or newer. The output directory must be new; earlier runs are never overwritten. Unlike notebook setup, the CLI makes no network request. The [notebook](jev_wake_gate_v7.ipynb) uses the same unchanged helper and [fixture](synthetic-events-v1.json), with eleven plain Python code cells and prediction/explanation sections. No model is called in either path.

## What the exercise establishes

All 40 events, labels, scores and USD unit costs are constructed. 16 tuning cases select the lower quiet threshold 0.20; 24 different test cases retain a deliberately hidden important miss. The upper investigation threshold 0.8 is fixed for the exercise. Neither threshold is a recommendation for real agents.

The test routes are 10 deferred, 2 investigation and 12 review, with 1 of 10 known-important cases wrongly deferred. There are 22 attempted scores; 18 valid attempted binary judgments enter Brier 0.1199875. Trusted bypasses, ambiguous labels and malformed responses remain in routing/cost reports.

At synthetic 1/25/50-cent prices, the modeled cascade costs USD 6.72 versus USD 6.00 for investigating all 24 cases. Quality is not matched. These figures are a constructed policy counterexample, not empirical results about Jev, NLI, GLiClass or Laya. Actual model/API charges are USD 0.00. The [reference receipt](offline-receipt-v3.json) is hash-bound to the unchanged helper and fixture.

The helper scores first and journals completed decisions afterward. Its SQLite restart/duplicate check covers that journal, not durable admission or survival of an interruption during scoring. No scheduler, lease, tool executor or production durability guarantee is provided. Its Jev request builder/parser are tested with constructed payloads; live service compatibility, authentication and billing remain untested.

## Verify the artifact

```bash
python3 verify_lab_v1.py
```

The verifier compares routes, counts, costs, keys and source hashes exactly. It permits at most 1e-12 floating-point rounding noise when comparing calculated scores across Python versions; a changed miss count, cost or materially different score fails its negative controls. The historical reference receipt remains unchanged.

This reruns the CLI, executes every notebook code cell in an empty working directory using mocked pinned downloads, checks the Colab file-download adapter with a stub, and inspects the exported JSON and SQLite files. It also tests offline cached and local-sibling replay, prior-run preservation, and failed/tampered acquisition. All canonical policy results are compared with the reference receipt. These are local contract checks, not an attended hosted-Colab browser observation.

For an additional **real public-download** smoke from an empty directory:

```bash
python3 verify_lab_v1.py --network
```

This fetches only the three pinned public teaching files and still makes zero model calls. Temporary verification output goes to your configured `TMPDIR`; the helper creates its explicit output only where requested. Current local/CI execution is evidence for Python and acquisition compatibility, not proof that a particular Google account has completed the hosted browser flow.

Lower the quiet threshold to 0.05 in the notebook and explain which routes change. After using test cases to revise a policy, use new held-out episodes before making a performance claim. Related-work citations and derivations belong to the article, which is not copied here. Original first-party code/data are covered by the repository MIT license.
