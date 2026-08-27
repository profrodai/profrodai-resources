# ZEO ITAM · Autumn 2026

**Status:** scaffolded

## Learner promise

Compute a repeatable minutes baseline before and after a workflow change, keeping the original
measurement visible.

## Source boundary and provenance

Source: [`profrod-site/content/courses/zeo-itam-autumn-2026/_course.md`](https://github.com/rodriveracom/profrod-site/tree/main/content/courses/zeo-itam-autumn-2026). The site calls this a live
serial; this local slice is a stable scaffold, not a replacement for scheduled classes.

## Module-to-lab roadmap

| Course module | Lab | Expected output |
|---|---|---|
| Class 1 baseline | `labs/01-minutes-baseline` | Baseline, observed minutes, and percentage change. |

## Prerequisites, runtime, safety, and cost

Python 3.10 or newer, standard library only; offline and credential-free.

## Run, verify, reset

Run `make run`, check it with `make verify`, and restore experimentation using `git restore .`.

## Practice companion

The [`minutes-baseline` guided practice](labs/01-minutes-baseline/PRACTICE.md) preserves regression evidence, adds invalid-input work, and supplies a text-only review path.
