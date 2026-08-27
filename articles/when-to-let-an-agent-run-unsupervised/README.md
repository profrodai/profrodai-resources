# When Can You Actually Walk Away? — practice companion

**Teaching maturity:** mapped · **Companion contract:** complete · **Human review:** pending

## Practice objective
Require bounded scope, rollback, verification, no live PII, and escalation before an unattended run.

## Prerequisites
Python 3 and basic risk-review vocabulary.

## Exercise
Inspect `practice.json`. Toggle one readiness condition at a time and explain why a score cannot compensate for a missing hard gate.

## Run and verification
Run `python3 tools/run_article_practice.py articles/when-to-let-an-agent-run-unsupervised/practice.json`.

## Completion evidence
Readiness is true only when every hard condition is true; missing controls are named.

## Rubric
Pass when absence of any hard gate blocks autonomy. Revise if controls are averaged into confidence.

## Accessibility
The Boolean fixture is readable as a checklist and requires no timed or visual-only interaction.

## Safety and cost boundary
This synthetic exercise is not permission to run a real agent unattended or bypass system controls.

## Provenance boundary
Identity source: `profrod-site/content/articles/when-to-let-an-agent-run-unsupervised.md`. No article body or real risk record is copied.
