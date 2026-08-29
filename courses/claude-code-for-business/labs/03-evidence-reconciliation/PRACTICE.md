# Evidence reconciliation practical

## Learn first

Read [Practice 03: Demand Evidence, Not Assurances](https://profrod.ai/courses/claude-code-for-business/lesson/07-practice-03-demand-evidence-not-assurances).

## Reinforcement contract

A reported business result earns acceptance only when a separate evidence record recomputes it.

## Baseline trace

Run `make run`; the claim is accepted because its count and total match the separate invoice rows.

## Guided variation

Change only the claimed total to `999.0`, predict `held`, then run the focused test.

## Transfer challenge

Invent a three-row expense reconciliation. State the claim and the independent rows that a reviewer would use to recompute it.

## Evidence

Submit the held variation, your evidence design, and `make verify` output.

## Rubric

Pass: claim and evidence are separate inputs and disagreement holds the claim. Revise: an expected value supplied next to the claim is treated as proof.

## Accessibility

The exercise uses small JSON-like records and text output; a learner may calculate the total by hand.

## Safety and cost

Use invented amounts only. Do not import invoices, financial records, credentials, or a live service.

## Debrief and return link

The check proves this arithmetic against these rows, not the validity of an organization’s books. Return to the [Site lesson](https://profrod.ai/courses/claude-code-for-business/lesson/07-practice-03-demand-evidence-not-assurances).

## Troubleshooting

If a total is held, compare the independently computed total before changing code. Never alter evidence to match an unsupported claim.
