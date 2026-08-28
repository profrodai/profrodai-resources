# Agent Engineering Foundations

**Status: mapped**

This is the future runnable home for a five-week, 15-hour engineering-first course for mid-level
and senior software engineers. It adopts the upstream curriculum outline at the pinned source;
no upstream lab code has been imported and no runnable course is claimed yet.

## Learner promise

Learn to distinguish automation agents from autonomous digital co-workers, then engineer the
shared foundations: tools, orchestration, reasoning, grounding, evaluation, governance, and
deployment discipline.

## Curriculum outline

| Week | Theme | Paired application |
|---|---|---|
| 1 | Agent foundations | Research-pipeline automation; hello voice agent |
| 2 | Orchestration, tools, and MCP | Social-media automation; voice-agent tools |
| 3 | Reasoning and test-time compute | Research verifier; structured voice planning |
| 4 | Factuality, RAG, and attribution | Attributed research; context-aware voice interaction |
| 5 | Observability, governance, deployment | Production automation; production voice safeguards |

The source also describes a capstone choice between a deep-research automation agent and a
voice-first digital co-worker. That is an outline, not a promise that either system is present.

## Credential and live-API boundary

The first lab must be offline and deterministic. Search, model APIs, MCP servers, voice ASR/TTS,
RAG stores, deployment services, and observability platforms are not configured here. Each needs
an explicit later exercise with its own credentials, cost, data, and safety contract.

## Provenance

Pinned source: https://github.com/rodriveracom/agent-engineering-foundations@ec7bb274b9dae25b08d1ff58ff2db348855afe0a

Import mode: `curriculum-adoption`

See [SOURCE.md](SOURCE.md) and [MIGRATION.md](MIGRATION.md). The upstream source is MIT and its
commit pin is the review anchor; this course stays `mapped` until a reviewed runnable lab lands.

## Next gate

Write and test one credential-free Week 1 vertical slice, then add its `make run`, `make test`,
and `make verify` contract before adopting further content.
