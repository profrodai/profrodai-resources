# Why Agent Systems Fail, and How a Lab Would Find Out

**Status:** scaffolded

## Learner promise

Gate a claim on directly named evidence and see a missing source fail visibly instead of allowing
a plausible but unsupported result through.

## Source boundary and provenance

Source: [`profrod-site/content/courses/why-agents-fail/_course.md`](https://github.com/rodriveracom/profrod-site/tree/main/content/courses/why-agents-fail). This is a local evidence-gate
exercise, not a claim to evaluate a real model.

## Module-to-lab roadmap

| Course module | Lab | Expected output |
|---|---|---|
| Harness engineering | `labs/01-evidence-gate` | A pass/fail verdict with missing source IDs. |

## Prerequisites, runtime, safety, and cost

Python 3.10 or newer, standard library only; no live model, credential, network, or spend.

## Run, verify, reset

Use `make run`, then `make verify`; discard local experiments with `git restore .`.

## Practice companion

The [`evidence-gate` guided practice](labs/01-evidence-gate/PRACTICE.md) exercises missing and duplicate evidence while keeping claims and sources synthetic.

## Current source scope

The course combines failure analysis, reliability arithmetic, evaluation and evidence gates. This fixture practices only the evidence-gate part; a passing local verdict does not measure a real agent success rate or grader calibration.

Source identity was reviewed against the pinned snapshot on November 9, 2026. This mapping review does not grant human pedagogical or accessibility approval.
