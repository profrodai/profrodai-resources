# The 12-Week Transformation Tracker, Run on Claude Code

**Status:** scaffolded

## Learner promise

Measure a before-and-after minutes baseline and surface the delta without rewriting prior data.

## Source boundary and provenance

Source: [`profrod-site/content/courses/transformation-tracker-with-claude-code/_course.md`](https://github.com/rodriveracom/profrod-site/tree/main/content/courses/transformation-tracker-with-claude-code).
The existing public `profrodai/transformation-tracker-course` remains its live companion; this
small adapter-style lab does not replace, copy, or migrate that repository.

The approved companion is now mapped as this lab's canonical-import successor in
[`SOURCE.md`](SOURCE.md) and [`MIGRATION.md`](MIGRATION.md). It remains current for learners until
a reviewed replacement lands here.

## Module-to-lab roadmap

| Course module | Lab | Expected output |
|---|---|---|
| Measure and iterate | `labs/01-baseline-delta` | Minutes saved and the honest direction of change. |

## Prerequisites, runtime, safety, and cost

Python 3.10 or newer, standard library only; no Claude Code, credential, or provider spend is required.

## Run, verify, reset

Run `make run`, test via `make verify`, and reset changes with `git restore .`.

## Practice companion

The [`baseline-delta` guided practice](labs/01-baseline-delta/PRACTICE.md) preserves improvements and regressions, with explicit evidence, rubric, accessibility, and privacy limits.
