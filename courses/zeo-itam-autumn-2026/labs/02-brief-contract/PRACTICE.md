# Class 2 — brief contract practice

## Learn first

[Prompting Is Briefing, Not Incantation](https://profrod.ai/courses/zeo-itam-autumn-2026/lesson/02-prompting-is-briefing)

## Objective

Turn a fictional request into a reviewable work order before any agent or person begins work.

## Guided exercise

Run `make -C labs/02-brief-contract run`. Predict whether the fictional Xolo brief can begin and name the five fields that make it reviewable.

## Project

Copy `fixtures/baseline.json` to `learner-brief.json`. Blank `scope`, run `python3 lab.py learner-brief.json`, and explain why a confident objective cannot compensate for an unbounded task.

## Transfer challenge

Write a new fictional brief for sorting inbound support requests. It must name a human owner, a bounded input set, observable evidence, and a case that must escalate. Do not alter `fixtures/`.

## Evidence

Submit the missing-field output, your revised brief, and `make verify` output. A ready result proves the request is sufficiently specified for review; it does not authorize an external action.

## Debrief

A complete brief reduces ambiguity; it does not make a risky action safe by itself.

## Rubric

Pass when every required field is visible and a missing scope is held. Revise when confidence is used instead of evidence or escalation.

## Accessibility

The brief may be read or composed as plain text or JSON. No visual-only or timed task is required.

## Safety and cost

Use fictional work, people, and records. Do not connect the exercise to a live tool, customer, or credential.

## Troubleshooting

- A whitespace-only value is missing.
- This lab intentionally treats every field as text; keep the exercise small and inspectable.
- If your request has no escalation, its safe boundary is unknown.

## Verify

From the course directory run `make verify`.
