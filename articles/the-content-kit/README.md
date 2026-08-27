# The Content Kit: Every Block, and When to Use It — practice companion

**Teaching maturity:** mapped · **Companion contract:** complete · **Human review:** pending

## Practice objective
Choose a content structure from communicative intent rather than decoration.

## Prerequisites
Python 3 and familiarity with comparisons, sequences, decisions, and warnings.

## Exercise
Inspect `practice.json`. Add a `sequence` case and explain why an unknown decorative intent falls back to a paragraph.

## Run and verification
Run `python3 tools/run_article_practice.py articles/the-content-kit/practice.json`.

## Completion evidence
Known intent maps deterministically; unknown intent is surfaced with `known_intent: false`.

## Rubric
Pass when the selected block aids the relationship being communicated. Revise if style alone determines structure.

## Accessibility
All choices are text labels and can be completed as a written mapping table.

## Safety and cost boundary
The grammar is a synthetic public exercise, not internal site machinery. It is offline and credential-free.

## Provenance boundary
Identity source: `profrod-site/content/articles/the-content-kit.md`. No article body or site block implementation is copied.
