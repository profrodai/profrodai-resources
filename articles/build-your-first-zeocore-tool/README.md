# Build Your First ZeoCore Tool, Then Watch It Fail Twice — practice companion

**Teaching maturity:** mapped · **Companion contract:** complete · **Human review:** pending

## Practice objective
Design a tool boundary that proves a valid write and visibly denies traversal or overwrite attempts.

## Prerequisites
Python 3 and basic familiarity with repository-relative paths. ZeoTool is not required.

## Exercise
Inspect `practice.json`. Add an overwrite-denial case on paper, then explain which check must run before any filesystem effect.

## Run and verification
Run `python3 tools/run_article_practice.py articles/build-your-first-zeocore-tool/practice.json`.

## Completion evidence
Both cases pass and the learner states the must-NOT: a denied operation has no outside or overwrite effect.

## Rubric
Pass when containment is decided before action and failure has a named reason. Revise if an outside path can be allowed.

## Accessibility
Trace path components in a written table; no timed or visual-only interaction is required.

## Safety and cost boundary
No filesystem mutation, credential, network, internal tool byte, or provider cost occurs; the runner evaluates strings only.

## Provenance boundary
Identity source: `profrod-site/content/articles/build-your-first-zeocore-tool.md`. No article body or internal ZeoCore implementation is present.
