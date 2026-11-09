# In a Dark Factory, Checking Is the Real Price of an Answer — practice companion

**Teaching maturity:** mapped · **Companion contract:** complete · **Human review:** pending

## Practice objective
Compare expected failure loss with verification cost using explicit assumptions.

## Prerequisites
Python 3 and basic multiplication. The numbers are teaching fixtures, not business forecasts.

## Exercise
Inspect `practice.json`. Find the break-even failure probability, then create a case where verification neither improves nor reduces margin.

## Run and verification
Run `python3 tools/run_article_practice.py articles/unverified-output-has-a-negative-margin/practice.json`.

## Completion evidence
Both margin calculations are visible and the fixture states whether verification improves expected margin.

## Rubric
Pass when every assumption is visible and arithmetic is reproducible. Revise if the result is presented as empirical evidence.

## Accessibility
Use a text expression or calculator; no chart is required.

## Safety and cost boundary
All monetary values and probabilities are invented. This is not financial advice and uses no real loss data.

## Provenance boundary
Identity source: `profrod-site/content/articles/unverified-output-has-a-negative-margin.md`. No article prose is included.

## Current source scope

The current article prices accepted output including review cost and uncertainty in acceptance rate. This expected-loss exercise uses a different simplified model; it does not implement the article's accepted-output cost estimator or its error bars.

Source identity was reviewed against the pinned snapshot on November 9, 2026. This mapping review does not grant human pedagogical or accessibility approval.
