# Agentic Coding with Cursor

**Status:** starter

## Learner promise

Use a small, real order service to practice reviewing an agent edit as you would a teammate's
pull request. The course site supplies the teaching sequence; this repository supplies the
starting state used from lesson 4 onward.

## Audience

Developers who can read TypeScript and want a bounded environment for reviewing
an agent-assisted change.

## Outcomes

- Run and inspect the deterministic order service.
- Make a bounded change and review its diff.
- Use the local verification gate before accepting the change.

## Source boundary and provenance

Source: [`profrod-site/content/courses/agentic-coding-with-cursor/_course.md`](https://github.com/profrodai/profrod-site/tree/main/content/courses/agentic-coding-with-cursor).
This directory preserves the runnable `order-api` companion. It does not duplicate lesson prose
or pre-apply the edits students are expected to make.

## Module-to-lab roadmap

| Course module | Lab | What can be explored now |
|---|---|---|
| Core practices | [`order-api`](order-api/) | Run and test the service, then make and review an agent-assisted change. |

## Module sequence

Orient in the service, run the known-good baseline, then make and review one
bounded change before accepting it.

## Assessment

A learner explains the observed behavior and submits a verified, reviewable
change. The baseline does not assess model prompting or provider-specific use.

## Completion evidence

The learner can run `make verify` and explain which passing checks establish
the behavior of the change they reviewed.

## Prerequisites

Node and npm are required. `order-api/package-lock.json` pins dependencies. The baseline is
credential-free, uses in-memory data, and makes no network calls. Any Cursor or model usage is
an optional student action and may have provider cost.

## Safety and cost boundary

The baseline is offline and credential-free. Any Cursor or model use is an
optional student action and may have provider cost; do not put secrets in the
repository or its fixtures.

## Run, verify, reset, expected output

`make run` starts the local service; `make verify` installs locked dependencies, typechecks,
tests, and audits it. Expect deterministic order lookup responses and four passing tests. Reset
your own exploration with `git restore .` and remove ignored dependencies with `npm ci`.

## Practice companion

Use the [`order-api` guided practice](order-api/PRACTICE.md) for the bounded project, evidence requirements, rubric, accessibility alternative, and safety boundary. It reinforces the course through runnable bytes and does not reproduce lesson prose.
