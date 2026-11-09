# What an Agent Loop Costs: Quadratic Resend, Cache Reads and Cost per Solved Task — practice companion

**Teaching maturity:** mapped · **Companion contract:** complete · **Human review:** pending

## Practice objective
Calculate scenario cost from explicit token volumes and fixture rates without presenting them as current pricing.

## Prerequisites
Python 3 and understanding that one million tokens is the rate denominator.

## Exercise
Inspect `practice.json`. Double output tokens, predict the total, and name the assumption that must be refreshed for a real provider.

## Run and verification
Run `python3 tools/run_article_practice.py articles/what-claude-code-actually-costs/practice.json`.

## Completion evidence
Input and output costs sum to the total and a zero-usage case remains zero.

## Rubric
Pass when rates, units, and arithmetic are explicit. Revise if fixture rates are described as current provider prices.

## Accessibility
The exercise is plain-text arithmetic and requires no chart or timed interaction.

## Safety and cost boundary
Rates are synthetic examples, not live pricing or financial advice. No provider API, account, or spend is involved.

## Provenance boundary
Identity source: `profrod-site/content/articles/what-claude-code-actually-costs.md`. No article body or price feed is copied.

## Current source scope

The current article derives quadratic context resend, cache reads and cost per solved task. This linear token-volume fixture is a unit-cost prerequisite only; it does not model cache expiry, repeated context or solve-rate uncertainty.

Source identity was reviewed against the pinned snapshot on November 9, 2026. This mapping review does not grant human pedagogical or accessibility approval.
