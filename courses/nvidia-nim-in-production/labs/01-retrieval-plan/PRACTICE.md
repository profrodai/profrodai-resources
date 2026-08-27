# Retrieval plan guided practice

## Objective
Convert a synthetic retrieval workload into explicit batches and concurrency without implying hardware sizing.

## Guided exercise
Calculate an exact-multiple case and a remainder case by hand, then compare with the runner.

## Project
Add a maximum-concurrency constraint and tests for empty input, rounding, and a capped plan.

## Evidence
Provide the arithmetic, observed plans, negative/edge tests, and course gate output.

## Rubric
Pass: zero and range edges are explicit and rounding is reproducible. Revise: fixture arithmetic is described as deployment advice.

## Accessibility
Use written arithmetic or a calculator; no GPU, container, or visual dashboard is required.

## Safety and cost
The workload is synthetic and offline. No NVIDIA service, GPU, credential, network, or cost is required.

## Verify
From the course directory run `make verify`.
