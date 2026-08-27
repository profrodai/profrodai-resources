# Evidence store guided practice

## Objective
Store source-tagged evidence while making duplicate denial and no-mutation behavior observable.

## Guided exercise
Insert a new record, attempt the same ID again, and compare the store before and after the denial.

## Project
Add a conflicting-duplicate case where the same ID carries different text; deny it without overwriting the original.

## Evidence
Provide before/after state, the denial result, regression tests, and the course gate output.

## Rubric
Pass: IDs and sources are explicit and denial has no effect. Revise: duplicate input mutates or silently replaces evidence.

## Accessibility
Represent state as a text list or JSON; no graph or vector interface is required.

## Safety and cost
Use synthetic, in-memory records. Do not add personal data, embeddings, external storage, credentials, or network calls.

## Verify
From the course directory run `make verify`.
