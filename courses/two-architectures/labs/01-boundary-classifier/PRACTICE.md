# Boundary classifier guided practice

## Objective
Classify uncertainty and side-effect risk before choosing a deterministic or stochastic boundary.

## Guided exercise
Predict the four low/high combinations, then compare the required review level with the tests.

## Project
Add a hard rule that any high side effect requires human review, regardless of uncertainty.

## Evidence
Provide the 2x2 input table, observed routes, hard-rule test, and course gate output.

## Rubric
Pass: side-effect risk cannot be averaged away. Revise: a high-impact action becomes autonomous because uncertainty is low.

## Accessibility
Use a four-row text table instead of a visual quadrant.

## Safety and cost
The classifier is synthetic and performs no action. Do not connect it to a live agent, credential, or external system.

## Verify
From the course directory run `make verify`.
