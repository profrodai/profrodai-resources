# Voice Agents, Not Chatbots

**Status:** scaffolded

## Learner promise

Observe a deterministic guard that prevents an agent from speaking a second response after a
conversation has already been marked complete.

## Source boundary and provenance

Source: [`profrod-site/content/courses/voice-agents-not-chatbots/_course.md`](https://github.com/profrodai/profrod-site/tree/main/content/courses/voice-agents-not-chatbots). This is a
text-only state-machine slice, not a telephony integration or voice-quality claim.

## Module-to-lab roadmap

| Course module | Lab | Expected output |
|---|---|---|
| Failure modes and hardening | `labs/01-turn-guard` | `speak` or `hold` plus its reason. |

## Prerequisites, runtime, safety, and cost

Python 3.14.6 standard library only. No microphone, phone number, network, or credentials.

## Run, verify, reset

Run `make run`, prove the guard with `make verify`, reset with `git restore .`.

## Practice companion

The [`turn-guard` guided practice](labs/01-turn-guard/PRACTICE.md) adds a transferred-state project, evidence, rubric, and non-audio accessibility path.
