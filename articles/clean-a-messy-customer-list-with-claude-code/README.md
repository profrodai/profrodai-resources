# Clean a Messy Customer List With Claude Code — and Prove Nothing Was Lost — practice companion

**Teaching maturity:** mapped · **Companion contract:** complete · **Human review:** pending

## Practice objective
Deduplicate a synthetic customer list while proving every input row is accounted for.

## Prerequisites
Python 3 and basic JSON. No customer system or model access is needed.

## Exercise
Inspect `practice.json`. Explain why whitespace and case make `c2` a duplicate, then add a distinct record and update the accounting invariant.

## Run and verification
Run `python3 tools/run_article_practice.py articles/clean-a-messy-customer-list-with-claude-code/practice.json`.

## Completion evidence
`unique_count + duplicate_ids count == input_count`, with duplicate IDs preserved for review.

## Rubric
Pass when normalization is explicit and no row disappears. Revise if output cannot account for every input row.

## Accessibility
Reason through the three-row fixture in prose or a text table; no color is required.

## Safety and cost boundary
All names and `.test` addresses are synthetic. Never substitute live customer data. The baseline is offline.

## Provenance boundary
Identity source: `profrod-site/content/articles/clean-a-messy-customer-list-with-claude-code.md`. No article body, prompt, or customer record is copied.
