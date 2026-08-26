# One-repository consolidation map

**Status:** mapped · **Scope:** approved public ProfRod teaching companions

`profrodai-resources` is the learning home for maintained, runnable course materials. The
registry in [`catalog/consolidation-sources.json`](../catalog/consolidation-sources.json) is the
machine-checked migration map; this document is its human-readable operating policy.

## Policy

1. Capture an approved source as an explicit URL and commit pin before any import.
2. Preserve provenance in a course-scoped `SOURCE.md` and a staged `MIGRATION.md`.
3. Do not rewrite an upstream Git history. After a replacement has landed and learners have a
   documented destination, the old repository may be archived and turned into a redirect shell.
4. A pin is evidence, not a relicensing grant. Licence compatibility and copyright scope are
   reviewed before copying any source bytes.
5. Every runnable replacement gets an offline, credential-free first gate before an opt-in
   live-provider exercise is designed.

## Migration status

| Source | Pinned commit | Mode | Target | Status |
|---|---|---|---|---|
| Transformation Tracker | `0b3452e` | canonical import | `courses/transformation-tracker-with-claude-code` | mapped; successor lab already exists |
| Claude Code 101 | `d3b2a6b` | legacy modernization | `courses/claude-code-for-business` | mapped |
| LangGraph Nebius | `78eeb32` | legacy modernization | `courses/langgraph-agent-orchestration` | mapped; deprecated patterns warning |
| Xolo Consulting | `bc4d20e` | template import | `courses/claude-code-for-business/template/xolo-consulting` | mapped; fictional-data and licence record required |
| QuackTool | `2a69d2e` | clean-room rebuild | `courses/tools-memory-and-multi-agent-systems/legacy/quacktool` | mapped; GPL source is not copied |
| Agent Engineering Foundations | `ec7bb27` | curriculum adoption | `courses/agent-engineering-foundations` | mapped |
| LLM Engineering Essentials | `01f05c3` | curriculum adoption | `courses/llm-engineering-essentials` | mapped |

No source code, notebooks, slides, data, or Git history is imported by this mapping commit.

## Gates before content lands

For each row: confirm the pin against the upstream source, review licence and copyright scope,
record a selected lesson or exercise, build a deterministic local first run, then add it to
`make verify`. A live API, model provider, or paid service is an explicit optional follow-on with
its own credential, cost, and data-handling instructions.
