# Brief readiness guided practice

## Learn first

Read [Practice 01: Brief Before You Delegate](https://profrod.ai/courses/claude-code-for-business/lesson/05-practice-01-brief-before-you-delegate).

## Reinforcement contract

This practice makes a delegation brief concrete: confidence is not readiness unless the task has an accountable owner and named evidence.

## Baseline trace

Run `make run`. Compare the ready and blocked brief decisions before editing.

## Objective
Turn a delegation request into a brief whose objective, owner, and evidence are mechanically reviewable.

## Guided exercise
Run both fixtures, identify the missing evidence in the blocked case, and add one new required field without allowing an empty value.

## Project
Create a fictional compliance-sensitive brief with an explicit reviewer and evidence IDs; prove an incomplete version is denied.

## Evidence
Submit the two fixture decisions, the new negative test, and `make verify` output.

## Rubric
Pass: every decision cites visible fields and incomplete evidence blocks readiness. Revise: confidence or prose substitutes for a named owner/check.

## Accessibility
The brief may be completed as plain text or JSON. No timed or visual-only task is required.

## Safety and cost
Use fictional work and identifiers. Do not include company data, credentials, or a live Claude Code action.

## Debrief and return link

The gate proves fields are present, not that the business decision is wise. Return to the [Site lesson](https://profrod.ai/courses/claude-code-for-business/lesson/05-practice-01-brief-before-you-delegate) to evaluate the quality of a real brief.

## Troubleshooting

If a list looks populated but the gate blocks it, check that it is non-empty. Do not weaken a required field or invent real evidence to make the exercise green.

## Verify
From the course directory run `make verify`.
