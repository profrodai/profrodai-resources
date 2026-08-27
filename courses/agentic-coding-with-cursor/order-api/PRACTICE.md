# Order API guided practice

## Objective
Make one bounded TypeScript change and review it as a pull request rather than accepting generated output on trust.

## Guided exercise
Run the baseline, trace `getOrder`, and add a test for an unknown order before changing behavior. Keep the diff limited to the behavior and its test.

## Project
Define a deterministic not-found contract, implement it, and explain the observable before/after behavior in the diff.

## Evidence
Provide the focused diff, the new failing-then-passing test, and the final course `make verify` output.

## Rubric
Pass: bounded diff, named behavior, regression test, locked install, typecheck, tests, and audit all pass. Revise: unrelated edits, untested behavior, or assurance-only review.

## Accessibility
The review can be submitted as a text diff walkthrough. Cursor use is optional; no timed interaction is required.

## Safety and cost
Use only in-memory fixture data. Do not add secrets, live orders, network calls, or a paid-provider requirement.

## Verify
From the course directory run `make verify`.
