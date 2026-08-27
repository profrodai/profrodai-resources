# Two Architectures: The 2x2 for Agent Design

**Status:** scaffolded

## Learner promise

Classify a task by uncertainty and side-effect risk before deciding whether it belongs in a
deterministic or stochastic workflow boundary.

## Source boundary and provenance

Source: [`profrod-site/content/courses/two-architectures/_course.md`](https://github.com/profrodai/profrod-site/tree/main/content/courses/two-architectures). The lab is a deterministic
classification exercise, not an implementation of either named architecture from the course.

## Module-to-lab roadmap

| Course module | Lab | Expected output |
|---|---|---|
| The 2x2 and handoff | `labs/01-boundary-classifier` | A named boundary and required review level. |

## Prerequisites, runtime, safety, and cost

Python 3.14.6 standard library only; offline and credential-free.

## Run, verify, reset

`make run` prints the two input cases; `make verify` runs their tests; `git restore .` resets.

## Practice companion

The [`boundary-classifier` guided practice](labs/01-boundary-classifier/PRACTICE.md) turns the 2x2 into a text table and makes high-side-effect review a hard gate.
