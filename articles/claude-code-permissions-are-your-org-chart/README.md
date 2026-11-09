# Test What a Claude Code Permission Rule Actually Allows, in a Sandbox — practice companion

**Teaching maturity:** mapped · **Companion contract:** complete · **Human review:** pending

## Practice objective
Compare requested actions with explicit grants and route missing authority to review.

## Prerequisites
Python 3 and familiarity with read, write, and delete as abstract permissions.

## Exercise
Inspect `practice.json`. Add a synthetic `network` request without granting it and predict the missing-permission result.

## Run and verification
Run `python3 tools/run_article_practice.py articles/claude-code-permissions-are-your-org-chart/practice.json`.

## Completion evidence
The permitted case succeeds and the over-broad request fails with the exact missing grant.

## Rubric
Pass when decisions derive only from explicit grants. Revise if an unknown or dangerous action is implicitly allowed.

## Accessibility
Complete the set comparison as a written two-column list; no pointer interaction is required.

## Safety and cost boundary
The synthetic policy never changes Claude Code, repository, or host permissions. No credentials or network are used.

## Provenance boundary
Identity source: `profrod-site/content/articles/claude-code-permissions-are-your-org-chart.md`. No working agent configuration is copied.

## Current source scope

The current article tests permission matching and sandbox behavior with adversarial probes. This abstract grant comparison is a prerequisite exercise only; it does not emulate command-pattern matching or qualify an actual Claude Code sandbox.

Source identity was reviewed against the pinned snapshot on November 9, 2026. This mapping review does not grant human pedagogical or accessibility approval.
