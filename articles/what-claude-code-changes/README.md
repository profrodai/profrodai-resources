# What Claude Code Actually Changes — and What It Doesn't — practice companion

**Teaching maturity:** mapped · **Companion contract:** complete · **Human review:** pending

## Practice objective
Classify a proposed change by files and side effects before accepting generated work.

## Prerequisites
Python 3 and familiarity with a code-review diff.

## Exercise
Inspect `practice.json`. Add a dependency action to a multi-file change and predict its risk and review requirement.

## Run and verification
Run `python3 tools/run_article_practice.py articles/what-claude-code-changes/practice.json`.

## Completion evidence
Low-risk documentation work and high-risk destructive work receive visibly different review decisions.

## Rubric
Pass when risk follows observable actions. Revise if deletion, permissions, dependencies, migrations, or external writes can be low risk.

## Accessibility
Inputs and outputs are text lists and may be classified in prose.

## Safety and cost boundary
The fixture describes changes but performs none. No repository mutation, provider call, credential, or personal data is involved.

## Provenance boundary
Identity source: `profrod-site/content/articles/what-claude-code-changes.md`. No article body or real diff is copied.
