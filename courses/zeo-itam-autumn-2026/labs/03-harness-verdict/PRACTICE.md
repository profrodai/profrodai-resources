# Class 3 — harness verdict practice

## Learn first

[The Harness at Work: Verification, MCP, and a New Trade Learned Live](https://profrod.ai/courses/zeo-itam-autumn-2026/lesson/04-the-harness-at-work)

## Objective

Separate a claimed result from the independent observation that must support it.

## Guided exercise

Run `make -C labs/03-harness-verdict run`. Predict the verdict before reading the JSON output. The lab derives unmatched invoice IDs from `fixtures/evidence.json`, then compares that derived result with the claim in `fixtures/claim.json`.

## Project

Copy both fixture files to `learner-claim.json` and `learner-evidence.json`. Change only `claimed_unmatched_ids` in your claim, then run `python3 lab.py learner-claim.json learner-evidence.json`. Next change `check` to `never-executed`. Compare the two hold reasons.

## Transfer challenge

Create a fictional claim for a document-classification task plus a separate evidence file from which its result can be computed. Make one claim disagree with that evidence. Explain why a plausible answer still cannot be accepted.

## Evidence

Submit both hold outputs and `make verify` output. An accept verdict proves agreement between a supplied claim and a result recomputed from separate supplied evidence; it does not prove a real-world outcome, completeness, or safety.

## Debrief

The harness holds disagreements because a plausible claim is not evidence. Naming a check is also insufficient: the approved check must actually derive an observation from distinct evidence bytes.

## Rubric

Pass when a missing, unrecognized, or conflicting check all hold the claim with distinct reasons.

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
