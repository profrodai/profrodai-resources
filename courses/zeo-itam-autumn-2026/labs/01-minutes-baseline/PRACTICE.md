# Class 1 — minutes baseline practice

## Learn first

[Lab: Instrument One Manual Workflow, Your Minutes Baseline](https://profrod.ai/courses/zeo-itam-autumn-2026/lesson/03-lab-minutes-baseline)

## Objective

Measure the original workflow before claiming an intervention made it faster.

## Guided exercise

Run `make -C labs/01-minutes-baseline run`. It compares 45 baseline minutes with 30 observed minutes.
Predict the percentage before running it. Then use Python to call `measure(20, 25)` and explain why the
negative result is evidence rather than a reason to rewrite the baseline.

## Project

Call `measure(45, 45)`, then call `measure(0, 20)`. Record the valid no-change result and the invalid-input
error separately. A valid measurement does not have to show a saving.

## Transfer challenge

Invent three aggregate observations for one fictional workflow. Keep its original baseline fixed, include one
regression, and write one sentence describing the next investigation you would request. Do not use personal or employer data.

## Evidence

Submit your prediction, the saving, the regression, the invalid-input error, and `make verify` output.

## Debrief

A passing result proves only that this calculation preserved its inputs and percentage; it does not prove that an AI system improved a real workflow.

## Rubric

Pass when a saving and regression remain visible and an invalid input is named instead of hidden.

## Accessibility

Use a text table or spoken explanation; no dashboard, chart, or timed task is required.

## Safety and cost

Use invented aggregate minutes only. Do not include employer data, personal productivity data, credentials, or provider access.

## Troubleshooting

- `baseline must be positive` means a zero/negative baseline is not a meaningful denominator.
- A negative percentage means observed minutes exceeded baseline; retain it.
- Use a text table if a calculator or chart is inaccessible.

## Verify

From the course directory run `make verify`.
