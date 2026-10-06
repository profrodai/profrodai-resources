# When should an always-on agent wake up?

Credential-free companion to the held article at https://www.profrod.ai/articles/when-should-an-always-on-agent-wake-up. The page remains unavailable until its publication review; this companion is independently runnable.

## Predict, then run

A constructed score of 0.08 defers an event that describes an unresolved failure. Would you let the agent sleep? Keep your answer before running:

```bash
python3 wake_gate_v3.py --out ./wake-gate-run-01
```

Run inside this folder with Python 3.10 or newer. The output directory must be new; earlier runs are never overwritten. Open [jev_wake_gate_v7.ipynb](jev_wake_gate_v7.ipynb) beside the helper and [fixture](synthetic-events-v1.json) for the same five plain Python cells. No pip, GPU, API key, download, account or model call. Jupyter/Colab browser interaction is not part of the recorded execution.

## What the exercise establishes

All 40 events, labels, scores and USD unit costs are constructed. 16 tuning cases select the lower quiet threshold 0.20; 24 different test cases retain a deliberately hidden important miss. The upper investigation threshold 0.8 is fixed for the exercise. Neither threshold is a recommendation for real agents.

The test routes are 10 deferred, 2 investigation and 12 review, with 1 of 10 known-important cases wrongly deferred. There are 22 attempted scores; 18 valid attempted binary judgments enter Brier 0.1199875. Trusted bypasses, ambiguous labels and malformed responses remain in routing/cost reports.

At synthetic 1/25/50-cent prices, the modeled cascade costs USD 6.72 versus USD 6.00 for investigating all 24 cases. Quality is not matched. These figures are a constructed policy counterexample, not empirical results about Jev, NLI, GLiClass or Laya. Actual model/API charges are USD 0.00. The [reference receipt](offline-receipt-v3.json) is hash-bound to the unchanged helper and fixture.

The helper scores first and journals completed decisions afterward. Its SQLite restart/duplicate check covers that journal, not durable admission or survival of an interruption during scoring. No scheduler, lease, tool executor or production durability guarantee is provided. Its Jev request builder/parser are tested with constructed payloads; live service compatibility, authentication and billing remain untested.

## Verify the artifact

```bash
python3 verify_lab_v1.py
```

This reruns the CLI in a new temporary directory, executes all notebook code cells, checks source hashes and compares policy results with the reference receipt. Temporary execution output goes to your configured `TMPDIR`; the helper creates its explicit output only where requested.

Lower the quiet threshold to 0.05 in the notebook and explain which routes change. After using test cases to revise a policy, use new held-out episodes before making a performance claim. Related-work citations and derivations belong to the article, which is not copied here. Original first-party code/data are covered by the repository MIT license.
