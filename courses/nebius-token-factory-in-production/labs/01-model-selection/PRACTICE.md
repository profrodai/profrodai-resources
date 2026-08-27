# Model selection guided practice

## Objective
Select an eligible synthetic model from explicit latency and cost limits while preserving a no-match result.

## Guided exercise
Trace which fixture fails each constraint, then tighten one budget until no record is eligible.

## Project
Add a throughput constraint and a tie-break rule, with tests for an eligible winner and no eligible fixture.

## Evidence
Provide the constraint table, both results, new tests, and `make verify` output.

## Rubric
Pass: all assumptions are fixture fields and no-match remains first-class. Revise: invented numbers are presented as a current provider catalog.

## Accessibility
Complete the comparison as a text table; no chart is required.

## Safety and cost
All model names and values are invented. No Nebius API, key, network, or billed inference is used.

## Verify
From the course directory run `make verify`.
