# Class 3 — harness verdict practice

## Learn first

[The Harness at Work: Verification, MCP, and a New Trade Learned Live](https://profrod.ai/courses/zeo-itam-autumn-2026/lesson/04-the-harness-at-work)

## Objective

Separate a claimed result from the independent observation that must support it.

## Guided exercise

Run `make -C labs/03-harness-verdict run`. Predict the verdict before reading the JSON output: the claimed and observed synthetic reconciliation results agree.

## Project

Copy `fixtures/baseline.json` to `learner-claim.json`. Change only `observed` to a different result and run `python3 lab.py learner-claim.json`. Then blank `check`. Compare the two hold reasons.

## Transfer challenge

Create a fictional claim for a document-classification task. Name the owner and independent check, then make one version where the check disagrees. Explain why a plausible answer still cannot be accepted.

## Evidence

Submit both hold outputs and `make verify` output. An accept verdict proves agreement between the supplied claim and check; it does not prove a real-world outcome, completeness, or safety.

## Debrief

The harness holds disagreements because a plausible claim is not evidence.

## Rubric

Pass when a missing check and a conflicting check both hold the claim with distinct reasons.

## Accessibility

All inputs and outputs are short JSON/text. A learner may describe the reasoning in prose.

## Safety and cost

Use fictional claims only. This is not a production approvals system and must not be connected to an external action.

## Troubleshooting

- Every required value must be non-empty text.
- `check-disagrees` is an instruction to investigate, not a failed exercise.
- Keep all examples fictional; this practical is not a production approvals system.

## Verify

From the course directory run `make verify`.
