# Draft release practical

## Learn first

Read [Practice 05: Drafted, Not Sent](https://profrod.ai/courses/claude-code-for-business/lesson/09-practice-05-drafted-not-sent).

## Reinforcement contract

An agent-assisted external message remains a draft until a named human approves it; an approval does not turn the companion into a sending tool.

## Baseline trace

Run `make run`. The invented message is ready only as a draft.

## Guided variation

Change `delivery` to `send`, predict `held`, then run the focused test.

## Transfer challenge

Define a fictional customer-update draft with recipient, body, reviewer, approval state, and a draft-only delivery mode.

## Evidence

Submit the held send variation, your draft contract, and `make verify` output.

## Rubric

Pass: a named reviewer and draft-only boundary are visible. Revise: a delivery action is treated as safe merely because content looks complete.

## Accessibility

The example is text/JSON and can be reviewed without a mail client or time-sensitive action.

## Safety and cost

Use `example.test` and fictional content only. This lab never sends, contacts, or stores anything externally.

## Debrief and return link

The gate proves a local release boundary, not authorization to communicate. Return to the [Site lesson](https://profrod.ai/courses/claude-code-for-business/lesson/09-practice-05-drafted-not-sent).

## Troubleshooting

If a draft is held, check recipient/body/reviewer and keep delivery at `draft-only`. Do not add an outbound integration to resolve the exercise.
