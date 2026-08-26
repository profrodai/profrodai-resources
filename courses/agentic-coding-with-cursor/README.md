# Agentic Coding with Cursor

**Status:** starter

## Learner promise

Use a small, real order service to practice reviewing an agent edit as you would a teammate's
pull request. The course site supplies the teaching sequence; this repository supplies the
starting state used from lesson 4 onward.

## Source boundary and provenance

Source: [`profrod-site/content/courses/agentic-coding-with-cursor/_course.md`](https://github.com/profrodai/profrod-site/tree/main/content/courses/agentic-coding-with-cursor).
This directory preserves the runnable `order-api` companion. It does not duplicate lesson prose
or pre-apply the edits students are expected to make.

## Module-to-lab roadmap

| Course module | Lab | What can be explored now |
|---|---|---|
| Core practices | [`order-api`](order-api/) | Run and test the service, then make and review an agent-assisted change. |

## Prerequisites, runtime, safety, and cost

Node and npm are required. `order-api/package-lock.json` pins dependencies. The baseline is
credential-free, uses in-memory data, and makes no network calls. Any Cursor or model usage is
an optional student action and may have provider cost.

## Run, verify, reset, expected output

`make run` starts the local service; `make verify` installs locked dependencies, typechecks,
tests, and audits it. Expect deterministic order lookup responses and four passing tests. Reset
your own exploration with `git restore .` and remove ignored dependencies with `npm ci`.
