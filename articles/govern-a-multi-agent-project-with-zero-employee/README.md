# Govern a Multi-Agent Project With Zero-Employee — practice companion

**Teaching maturity:** mapped · **Companion contract:** complete · **Human review:** pending

## Practice objective
Validate that every fictional handoff names an owner, state, and evidence pointer.

## Prerequisites
Python 3 and the idea of a task handoff. No Zeo installation is required.

## Exercise
Inspect `practice.json`. Repair the failure case by adding evidence, then create a task missing an owner and predict the denial list.

## Run and verification
Run `python3 tools/run_article_practice.py articles/govern-a-multi-agent-project-with-zero-employee/practice.json`.

## Completion evidence
The complete handoff passes and every absent field is reported as `task:field`.

## Rubric
Pass when the record is resumable by someone absent from the conversation. Revise if owner or evidence can be implicit.

## Accessibility
The fixture and result are plain text and may be reviewed without running code.

## Safety and cost boundary
The project record is fictional and contains no internal doctrine, personal data, credentials, or external effects.

## Provenance boundary
Identity source: `profrod-site/content/articles/govern-a-multi-agent-project-with-zero-employee.md`. No article body or real operating record is reproduced.
