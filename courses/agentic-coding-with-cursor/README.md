# Agentic Coding with Cursor

**Status:** practical track · **Runtime:** Node 20+ · **Cost:** free and offline

## Learner promise

Use a small order service to practice reviewing an agent edit as you would a teammate's pull
request. The course site supplies the teaching sequence; this repository supplies original,
synthetic exercises that make the review habits observable.

## Audience

Developers who can read TypeScript and want a bounded environment for reviewing
an agent-assisted change.

## Outcomes

- Run and inspect the deterministic order service.
- Make a bounded change and review its diff.
- Use the local verification gate before accepting the change.

## Source boundary and provenance

Source: [`profrod-site/content/courses/agentic-coding-with-cursor/_course.md`](https://github.com/rodriveracom/profrod-site/tree/main/content/courses/agentic-coding-with-cursor).
This directory preserves the runnable `order-api` companion. It does not duplicate lesson prose
or pre-apply the edits students are expected to make.

## Module-to-lab roadmap

Read the linked lesson before each practice. The order data, rules, and index boundary below are
invented for this companion; they do not reproduce the Site's lesson bodies.

| Practice | Learn first on profrod.ai | You will demonstrate |
|---|---|---|
| [01 · durable context](order-api/practices/01-durable-context.md) | [Cursor rules](https://profrod.ai/courses/agentic-coding-with-cursor/lesson/04-cursor-rules-durable-context) | A local rule constrains an edit without needing a live agent. |
| [02 · scoped change](order-api/practices/02-scoped-change.md) | [Right-size an agent request](https://profrod.ai/courses/agentic-coding-with-cursor/lesson/05-right-size-the-agent-request) | A request names behavior, boundaries, and evidence before code changes. |
| [03 · behavioral review](order-api/practices/03-behavioral-review.md) | [When the agent gets it wrong](https://profrod.ai/courses/agentic-coding-with-cursor/lesson/08-when-the-agent-gets-it-wrong) | A plausible cache edit is rejected by an independent behavior test. |
| [04 · index boundary](order-api/practices/04-index-boundary.md) | [Cursorignore and team rules](https://profrod.ai/courses/agentic-coding-with-cursor/lesson/09-cursorignore-and-team-rules) | Sensitive-pattern paths are excluded from the companion's agent context. |

## Module sequence

Orient in the service, inspect the durable local context, write a bounded request, and use the
behavioral tests to review an intentionally tempting cache variation before accepting any change.

## Assessment

A learner explains the observed behavior and submits a verified, reviewable change. The baseline
does not assess model prompting or provider-specific use.

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
tests, and audits it. Expect deterministic order lookup responses and passing behavior checks.
Reset
your own exploration with `git restore .` and remove ignored dependencies with `npm ci`.

## Practice companion

Start with the [`order-api` practice overview](order-api/PRACTICE.md), then complete the four
linked practicals in order. They reinforce the course through runnable bytes and do not reproduce
lesson prose.
