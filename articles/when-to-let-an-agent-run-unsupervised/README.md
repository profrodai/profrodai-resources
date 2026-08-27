# When Can You Actually Walk Away? — practice companion

**Teaching maturity:** mapped · **Companion contract:** complete · **Human review:** pending

## Practice objective
Require bounded scope, rollback, verification, no live PII, and escalation before an unattended run.

## Prerequisites
Python 3 and basic risk-review vocabulary.

## Exercise
Inspect `proposals.json`. It contains three synthetic automation proposals: one ready, one missing exactly
one hard control, and one missing several. Predict each decision before running the assessment.

Use the checklist for every proposal:

| Hard control | What it protects |
|---|---|
| Bounded scope | The run cannot expand into unrelated work. |
| Rollback | A bad result has a defined recovery path. |
| Verification | A result is checked before it is trusted. |
| No live PII | The exercise never exposes real personal data. |
| Escalation | A person receives cases outside the safe boundary. |

## Run and verification
From the repository root, run these commands one line at a time:

```bash
python3 tools/run_article_practice.py articles/when-to-let-an-agent-run-unsupervised/practice.json
python3 tools/run_autonomy_assessment.py articles/when-to-let-an-agent-run-unsupervised/proposals.json
python3 -m unittest -v tests/test_article_practice.py
```

The generated assessment marks the proposal with score `96` as `must-review`, because its missing rollback
is a hard gate. Tests pin the synthetic proposal bytes and expected decisions; do not edit the checked-in
fixture to claim a passing result.

## Completion evidence
Readiness is true only when every hard condition is true; missing controls and the decision are named.

## Rubric
Pass when absence of any hard gate blocks autonomy, including a proposal with a high readiness score. Revise
if weighted score, confidence, or optimism can compensate for a missing control.

## Accessibility
The Boolean fixture is readable as a checklist and requires no timed or visual-only interaction.

## Safety and cost boundary
This synthetic exercise is not permission to run a real agent unattended or bypass system controls.

## Debrief

The numeric score is context, not authority. A weighted score can help a reviewer prioritize work only after
every hard control is present. Missing rollback, verification, PII protection, or escalation changes the
decision to `must-review`; it is not a small deduction from a score.

## Provenance boundary
Identity source: `profrod-site/content/articles/when-to-let-an-agent-run-unsupervised.md`. No article body or real risk record is copied.
