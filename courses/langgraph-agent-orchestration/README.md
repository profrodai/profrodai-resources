# LangGraph Agent Orchestration

**Status:** scaffolded

## Learner promise

Make a routing decision from an explicit confidence signal, the kind of typed, inspectable state
decision the course teaches before a graph invokes a tool.

## Source boundary and provenance

Source: [`profrod-site/content/courses/langgraph-agent-orchestration/_course.md`](https://github.com/profrodai/profrod-site/tree/main/content/courses/langgraph-agent-orchestration). This
credential-free slice models a decision only; it does not bundle LangGraph or copy the course.

## Module-to-lab roadmap

| Course module | Lab | Expected output |
|---|---|---|
| State and routing | `labs/01-confidence-routing` | A route of `tool` or `human-review` with its threshold. |

## Prerequisites, runtime, safety, and cost

Python 3.14.6 standard library only; deterministic and offline. A later live graph needs its own
LangGraph version, provider, and credential decision.

The approved `langgraph-nebius` source is historical and must not be treated as current setup
guidance. [SOURCE.md](SOURCE.md) and [MIGRATION.md](MIGRATION.md) pin it and require a dependency
and credential audit before any exercise is modernized.

## Run, verify, reset

`make run` prints two routing outcomes; `make verify` runs unit tests. Reset local changes with
`git restore .`.
