# Build a Working Agent with sovereign-agent — practice companion

**Teaching maturity:** mapped · **Companion contract:** complete · **Human review:** pending

## Practice objective
Turn a claimed agent result into an explicit evidence chain with a source, behavioral check, and owner.

## Prerequisites
Python 3 and the ability to read a small JSON fixture. Installing sovereign-agent is not required.

## Exercise
Open `practice.json`. Explain why the positive case is ready and the failure case is blocked. Add one required evidence ID and update both expected results without weakening the denial path.

## Run and verification
Run `python3 tools/run_article_practice.py articles/build-a-working-agent-with-sovereign-agent/practice.json` from the repository root.

## Completion evidence
A changed fixture that still passes, plus an explanation of which missing evidence prevents readiness.

## Rubric
Pass when every requirement is named and missing evidence fails visibly. Revise if confidence substitutes for evidence.

## Accessibility
The task is text-only and untimed. The set difference may be described in prose instead of edited in JSON.

## Safety and cost boundary
The fixture is synthetic, offline, credential-free, and makes no claim about the external project's current API.

## Provenance boundary
Identity source: `profrod-site/content/articles/build-a-working-agent-with-sovereign-agent.md`. No article body or external project source is copied.
