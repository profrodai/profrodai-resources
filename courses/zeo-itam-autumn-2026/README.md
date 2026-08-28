# ZEO ITAM · Autumn 2026 — practical track

Status: flagship companion track · **Runtime:** Python 3.10+ · **Cost:** free and offline

The live course at profrod.ai explains the ideas. This directory is where you make those ideas
observable: predict a result, change synthetic bytes, run a verifier, and explain what the result
proves. It is not a replacement for class, lecture notes, or the semester's real case-study work.

## Learner promise

Build a measured ZEO loop: retain a minutes baseline, turn a request into a reviewable brief,
hold an unverified result, and name a bounded ledger integrity gap.

## Source boundary and provenance

The live teaching source is the [ZEO ITAM course on profrod.ai](https://profrod.ai/courses/zeo-itam-autumn-2026).
The links below are learner-facing routes into that course. Resources contains original synthetic
practice only and does not copy lesson bodies.

## Module-to-lab roadmap

Read the linked lesson first, then use the matching practical. Each practical uses invented data;
do not add employer data, credentials, student records, or a live model/API.

| Live class | Learn first on profrod.ai | Practical | You will prove |
|---|---|---|---|
| Class 1 | [Instrument a minutes baseline](https://profrod.ai/courses/zeo-itam-autumn-2026/lesson/03-lab-minutes-baseline) | [01 minutes baseline](labs/01-minutes-baseline/PRACTICE.md) | A slowdown is retained rather than erased. |
| Class 2 | [Prompting is briefing](https://profrod.ai/courses/zeo-itam-autumn-2026/lesson/02-prompting-is-briefing) | [02 brief contract](labs/02-brief-contract/PRACTICE.md) | A request cannot proceed without scope, owner, evidence, and escalation. |
| Class 3 | [The harness at work](https://profrod.ai/courses/zeo-itam-autumn-2026/lesson/04-the-harness-at-work) | [03 harness verdict](labs/03-harness-verdict/PRACTICE.md) | A claimed result is held when its independent check disagrees. |
| Class 4 | [Needle in Xolo's ledger](https://profrod.ai/courses/zeo-itam-autumn-2026/lesson/03-lab-the-needle-in-xolos-ledger) | [04 ledger investigation](labs/04-ledger-investigation/PRACTICE.md) | A transfer exercise: a bounded investigation names a missing receipt or duplicate record. |

## Prerequisites, runtime, safety, and cost

Python 3.10+ and a terminal are enough. Every exercise is text/JSON, offline, free, synthetic,
and credential-free.

## Run, verify, reset

1. Read the linked Site lesson.
2. Run the unchanged baseline: `make run`.
3. Make the guided change in a `learner-*.json` copy, never in `fixtures/`.
4. Run that lab's command and write down your predicted and observed result.
5. Run `make verify`. The supplied fixtures and expected outputs are independently pinned by tests.
6. Return to the linked lesson and explain which rule the practice made concrete.

Run all four baseline demonstrations with `make run`; run every acceptance check with `make verify`.

## Accessibility and safety

Every result is text/JSON, untimed, and reproducible. A learner may explain a result in prose or a
table. The invented Xolo scenarios are exercises in reasoning, not permission to automate a real
workflow, inspect real ledgers, or expose personal data.
