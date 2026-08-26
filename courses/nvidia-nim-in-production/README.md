# NVIDIA NIM in Production

**Status:** scaffolded

## Learner promise

Turn an explicit retrieval workload into a deployment plan rather than inferring production
capacity from a model name.

## Source boundary and provenance

Source: [`profrod-site/content/courses/nvidia-nim-in-production/_course.md`](https://github.com/profrodai/profrod-site/tree/main/content/courses/nvidia-nim-in-production). The lab is a
fixture-based planning exercise, not an NVIDIA service client or hardware sizing claim.

## Module-to-lab roadmap

| Course module | Lab | Expected output |
|---|---|---|
| Retrieval and deployment | `labs/01-retrieval-plan` | A deterministic batch/concurrency plan. |

## Prerequisites, runtime, safety, and cost

Python 3.14.6 standard library only; no container, GPU, network, credential, or cost.

## Run, verify, reset

Use `make run`, `make verify`, then `git restore .` to discard exploration.
