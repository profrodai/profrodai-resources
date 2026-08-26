# Tools, Memory, and Multi-Agent Systems

**Status:** scaffolded

## Learner promise

Store evidence with an explicit source and observe duplicate handling, rather than calling a
memory system correct because it accepted text.

## Source boundary and provenance

Source: [`profrod-site/content/courses/tools-memory-and-multi-agent-systems/_course.md`](https://github.com/profrodai/profrod-site/tree/main/content/courses/tools-memory-and-multi-agent-systems). The
lab is a tiny local analogue, not a copy of a production memory implementation.

## Module-to-lab roadmap

| Course module | Lab | Expected output |
|---|---|---|
| Tools and memory | `labs/01-evidence-store` | Stored record count and duplicate result. |

## Prerequisites, runtime, safety, and cost

Python 3.14.6 standard library only. It is offline, in-memory, and credential-free.

## Run, verify, reset

Use `make run` for the sample trace, `make verify` for tests, and `git restore .` to reset.

[ZeoTool](https://github.com/profrodai/zeotool) is the canonical public repository. Resources
will not import it until a merged MIT ZeoTool commit is pinned and reviewed. The
[legacy QuackTool record](legacy/quacktool/SOURCE.md) preserves the prior GPL-3.0 source only as
historical provenance; [its migration record](legacy/quacktool/MIGRATION.md) prohibits copying
or relicensing those historical source bytes.
