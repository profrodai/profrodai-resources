# Class 4 — ledger investigation practice

## Learn first

[Lab: The Needle in Xolo's Ledger](https://profrod.ai/courses/zeo-itam-autumn-2026/lesson/03-lab-the-needle-in-xolos-ledger)

## Objective

Find concrete integrity gaps in a bounded fictional ledger without silently repairing the evidence.

## Guided exercise

Run `make -C labs/04-ledger-investigation run`. Predict which record requires review and why before looking at the output.

## Project

Copy `fixtures/baseline.json` to `learner-ledger.json`. Add a second record with ID `xolo-101`; run `python3 lab.py learner-ledger.json` and explain why a duplicate does not disappear simply because its amount looks plausible.

## Transfer challenge

Create a five-record fictional ledger with one missing receipt and one duplicate ID. Write the smallest review note that names each problem and the evidence needed before correcting it. Do not edit `fixtures/`.

## Evidence

Submit your predicted issue, JSON output, review note, and `make verify` output. A passing result proves that this bounded checker names two integrity classes; it does not prove a real financial ledger is correct.

## Debrief

The correct next step for a duplicate or missing receipt is review with named evidence, not an invented correction.

## Rubric

Pass when both integrity gaps are named and the review note requests evidence. Revise if a record is silently deleted or assumed correct.

## Accessibility

The ledger is a short text/JSON list. A learner may make the review note as prose or a table.

## Safety and cost

Keep every record invented and aggregate. Do not use financial, customer, or personal data.

## Troubleshooting

- Records must have exactly `id`, `amount`, and `receipt`.
- A missing receipt or duplicate requires review; the lab deliberately does not auto-correct either.
- Keep every record invented and aggregate; do not use financial or personal data.

## Verify

From the course directory run `make verify`.
