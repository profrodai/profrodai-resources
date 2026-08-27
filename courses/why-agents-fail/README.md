# Why Agents Fail: Harness Engineering for AI Projects

**Status:** scaffolded

## Learner promise

Gate a claim on directly named evidence and see a missing source fail visibly instead of allowing
a plausible but unsupported result through.

## Source boundary and provenance

Source: [`profrod-site/content/courses/why-agents-fail/_course.md`](https://github.com/profrodai/profrod-site/tree/main/content/courses/why-agents-fail). This is a local evidence-gate
exercise, not a claim to evaluate a real model.

## Module-to-lab roadmap

| Course module | Lab | Expected output |
|---|---|---|
| Harness engineering | `labs/01-evidence-gate` | A pass/fail verdict with missing source IDs. |

## Prerequisites, runtime, safety, and cost

Python 3.14.6 standard library only; no live model, credential, network, or spend.

## Run, verify, reset

Use `make run`, then `make verify`; discard local experiments with `git restore .`.

## Practice companion

The [`evidence-gate` guided practice](labs/01-evidence-gate/PRACTICE.md) exercises missing and duplicate evidence while keeping claims and sources synthetic.
