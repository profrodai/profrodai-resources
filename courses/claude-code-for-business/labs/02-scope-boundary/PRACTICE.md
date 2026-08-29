# Scope boundary practical

## Learn first

Read [Practice 02: Right-Size the Task](https://profrod.ai/courses/claude-code-for-business/lesson/06-practice-02-right-size-the-task).

## Reinforcement contract

A request is reviewable only when it names what may change, what must not happen, and how success will be observed.

## Baseline trace

Run `make run`, then `make verify`.

## Guided variation

Remove `forbidden_actions` from the ready fixture in a throwaway edit. Predict and observe the blocked result.

## Transfer challenge

Write a fictional request to classify supplier contracts. Name one allowed path, one forbidden action, and one acceptance check.

## Evidence

Submit the blocked variation, your bounded request, and the final verification output.

## Rubric

Pass: the request has a concrete objective, scope, prohibition, and observable check. Revise: vague “improve” language or a request that permits sending externally.

## Accessibility

All fixtures and output are plain text/JSON. You may supply the request as a table.

## Safety and cost

Use only fictional paths and records. No provider account, real contract, or external action is required.

## Debrief and return link

The gate verifies completeness, not whether a requested action is appropriate. Return to the [Site lesson](https://profrod.ai/courses/claude-code-for-business/lesson/06-practice-02-right-size-the-task).

## Troubleshooting

If the request blocks unexpectedly, inspect each list for emptiness. Do not remove the boundary to force readiness.
