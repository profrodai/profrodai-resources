# Evidence gate guided practice

## Objective
Deny a synthetic claim when any named evidence ID is missing, name the gap, and explain why a score or
duplicate cannot replace it.

## Guided exercise
Run `fixtures/baseline.json`. Before you run it, predict the verdict and missing ID. Copy that fixture to
`learner-claim.json`, add `approval-v1`, and run your copy. Finally run the untouched acceptance fixture.

| Trace | Supplied IDs | Expected result |
|---|---|---|
| Before | `brief-v1`, `test-log-v1` | fail; `approval-v1` is missing |
| After | `brief-v1`, `test-log-v1`, `approval-v1` | pass; no IDs missing |

## Project
Add a duplicate `brief-v1` to your learner-owned file and prove it does not satisfy a different missing
requirement. Do not edit `fixtures/`: tests hash their bytes and assert fixed results.

## Evidence
Provide your before/after JSON traces, the named missing ID, a sentence explaining why duplicates do not
create evidence, and the `make verify` output.

## Rubric
Pass: every claim requirement maps to an observed evidence ID and your explanation cites `approval-v1`.
Revise: confidence, count, or duplicated evidence substitutes for the missing source.

## Accessibility
Compare the sets as plain text; no visual graph is required.

## Safety and cost
All claims and IDs are synthetic. No live model, private source, credential, or network is used.

## Verify
From the course directory run `make verify`.
