# Claude Code for Business

**Status:** scaffolded

## Learner promise

Practice turning a proposed delegation into a reviewable brief with explicit evidence, rather
than treating a confident draft as a completed business task.

## Source boundary and provenance

Source: [`profrod-site/content/courses/claude-code-for-business/_course.md`](https://github.com/rodriveracom/profrod-site/tree/main/content/courses/claude-code-for-business). This is a
small deterministic teaching slice, not copied course content or a live Claude Code integration.

The pinned Claude Code 101 course is a legacy-modernization source, and the fictional Xolo
template is a separately mapped future template import. Their provenance, licence boundary, and
next gates are in [SOURCE.md](SOURCE.md), [MIGRATION.md](MIGRATION.md), and
[`template/xolo-consulting/`](template/xolo-consulting/).

## Module-to-lab roadmap

| Course module | Lab | Expected output |
|---|---|---|
| Practices and compliance | `labs/01-brief-readiness` | A JSON readiness decision with missing evidence named. |

## Prerequisites, runtime, safety, and cost

Python 3.10 or newer, standard library only; no network, credentials, or provider cost.

## Run, verify, reset

Run `make run`, prove it with `make verify`, and reset edits with `git restore .`. The lab tests
both a ready brief and a blocked brief.

## Practice companion

The [`brief-readiness` guided practice](labs/01-brief-readiness/PRACTICE.md) adds a bounded project, evidence, rubric, accessibility alternative, and safety boundary without copying course lessons.
