# Confidence routing guided practice

## Objective
Make a typed routing boundary visible, explain every must-review decision, and prove the threshold without
using a live graph or model.

## Guided exercise
Read the decision table in `README.md`. Predict all four routes in `fixtures/routing-cases.json`, then run
`python3 lab.py fixtures/routing-cases.json`. Explain why `0.80` may use the tool but `0.79` must be reviewed.

| Case | Expected route | Why |
|---|---|---|
| High confidence | tool | valid and above threshold |
| Exact threshold | tool | equality is explicitly allowed |
| Below threshold | human-review | `below-threshold` |
| Out of range | human-review | `invalid-confidence` |

## Project
Copy the fixture to `learner-cases.json`; add one case with a quoted number or Boolean. Run it and explain the
`invalid-confidence` reason. Keep `fixtures/` unchanged: acceptance tests pin its bytes and full output.

## Evidence
Provide your predicted table, the JSON output, one learner-added invalid case, and `make verify` output.

## Rubric
Pass: tool use requires a valid threshold result and every review has a reason. Revise: invalid data falls
through to a tool, routing depends on hidden state, or a live model response is introduced.

## Accessibility
Use a written input/expected-route table; no graph visualization is required.

## Safety and cost
The exercise is an offline decision function. Do not add credentials, network calls, or claim it represents a production graph.

## Verify
From the course directory run `make verify`.
