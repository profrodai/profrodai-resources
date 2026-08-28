# LLM Engineering Essentials

**Status: mapped**

This is the planned runnable home for the upstream LLM Engineering Essentials curriculum. The
pinned MIT source contains Topic 1–3 materials and a roadmap for a six-topic course; it does not
yet provide a complete current implementation for every outlined topic. No notebooks, solutions,
or provider setup have been copied here.

## Learner promise

Build sound engineering judgment from LLM API basics through orchestration and context, then use
that judgment to decide when self-hosting, optimization, monitoring, or fine-tuning is warranted.

## Curriculum outline

| Topic | Pinned-source coverage | Focus |
|---|---|---|
| 1. LLM API basics | Present | APIs, tokenization, prompting, failure modes, model choice, inference parameters, characters |
| 2. LLM workflows | Present | Reasoning, inference-time compute, tools, and agentic orchestration |
| 3. Context | Present | RAG, database/vector search, and advanced retrieval components |
| 4. Self-served LLMs | Roadmap only | Open-model inference and cost-to-value choices |
| 5. Optimization and monitoring | Roadmap only | Inference optimization and observability |
| 6. Fine-tuning | Roadmap only | Fine-tuning, embeddings, PEFT, RLHF, and DPO |

The upstream through-project is an NPC Factory. It is a curriculum reference, not a runnable
service in this repository.

## Credential and live-API boundary

The first lab must run locally with deterministic inputs. API keys, hosted models, self-served
inference, cloud deployment, databases, monitoring, and fine-tuning are all deferred until an
exercise explicitly names its provider, expected costs, data boundary, and reset path.

## Provenance

Pinned source: https://github.com/rodriveracom/LLM-Engineering-Essentials@01f05c3e616a01901ae9fce693006c8cb8e4c411

Import mode: `curriculum-adoption`

See [SOURCE.md](SOURCE.md) and [MIGRATION.md](MIGRATION.md). This course remains `mapped` until
a reviewed runnable lesson with its own project gate is added.

## Next gate

Turn one Topic 1 concept into a credential-free lab with declared inputs, observable output,
tests, and `make verify`; only then select the next source material.
