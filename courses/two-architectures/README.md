# The 2x2 for Agent Design: Workflows, Agents, and Per-Layer Evals

**Status:** scaffolded

## Learner promise

Classify a task by uncertainty and side-effect risk before deciding whether it belongs in a
deterministic or stochastic workflow boundary.

## Source boundary and provenance

Source: [`profrod-site/content/courses/two-architectures/_course.md`](https://github.com/rodriveracom/profrod-site/tree/main/content/courses/two-architectures). The lab is a deterministic
classification exercise, not an implementation of either named architecture from the course.

## Module-to-lab roadmap

| Course module | Lab | Expected output |
|---|---|---|
| Legacy risk boundary and handoff | `labs/01-boundary-classifier` | A named boundary and required review level. |

## Prerequisites, runtime, safety, and cost

Python 3.10 or newer, standard library only; offline and credential-free.

## Run, verify, reset

`make run` prints the two input cases; `make verify` runs their tests; `git restore .` resets.

## Practice companion

The [`boundary-classifier` guided practice](labs/01-boundary-classifier/PRACTICE.md) turns the legacy risk boundary into a text table and makes high-side-effect review a hard gate.

## Current source scope

The current 2x2 crosses who waits with who decides, then evaluates each layer. This legacy classifier uses uncertainty and side effects; those are different axes. Treat it as a separate risk-boundary exercise, not an implementation of the current course diagram.

Source identity was reviewed against the pinned snapshot on November 9, 2026. This mapping review does not grant human pedagogical or accessibility approval.
