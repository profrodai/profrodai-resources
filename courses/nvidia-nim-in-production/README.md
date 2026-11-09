# Inference Economics on NVIDIA NIM: Latency, Throughput and Cost per Token

**Status:** scaffolded

## Learner promise

Turn an explicit retrieval workload into a deployment plan rather than inferring production
capacity from a model name.

## Source boundary and provenance

Source: [`profrod-site/content/courses/nvidia-nim-in-production/_course.md`](https://github.com/rodriveracom/profrod-site/tree/main/content/courses/nvidia-nim-in-production). The lab is a
fixture-based planning exercise, not an NVIDIA service client or hardware sizing claim.

## Module-to-lab roadmap

| Course module | Lab | Expected output |
|---|---|---|
| Retrieval and deployment | `labs/01-retrieval-plan` | A deterministic batch/concurrency plan. |

## Prerequisites, runtime, safety, and cost

Python 3.10 or newer, standard library only; no container, GPU, network, credential, or cost.

## Run, verify, reset

Use `make run`, `make verify`, then `git restore .` to discard exploration.

## Practice companion

The [`retrieval-plan` guided practice](labs/01-retrieval-plan/PRACTICE.md) covers rounding, zero input, concurrency constraints, evidence, and review without making hardware claims.

## Current source scope

The course covers prefill, decode, batching and cost per token. This deterministic retrieval batch planner covers planning arithmetic only; it does not benchmark NVIDIA NIM or implement the full inference-economics course.

Source identity was reviewed against the pinned snapshot on November 9, 2026. This mapping review does not grant human pedagogical or accessibility approval.
