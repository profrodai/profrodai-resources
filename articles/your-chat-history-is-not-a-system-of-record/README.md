# Your Chat History Is Not a Lab Notebook: Make Agent Work Resumable — practice companion

**Teaching maturity:** mapped · **Companion contract:** complete · **Human review:** pending

## Practice objective
Replay an append-only event record and expose a missing sequence instead of guessing state from conversation.

## Prerequisites
Python 3 and familiarity with ordered events.

## Exercise
Inspect `practice.json`. Add an owner event, replay state, then remove one or more sequence numbers and predict every reported gap. Sequence numbers must be positive and strictly increasing; a duplicate or out-of-order event is denied rather than silently replayed.

## Run and verification
Run `python3 tools/run_article_practice.py articles/your-chat-history-is-not-a-system-of-record/practice.json`.

## Completion evidence
Final state derives from ordered events and any sequence gap makes `replayable` false.

## Rubric
Pass when every change has a durable ordered event. Revise if a missing event is filled from context or memory.

## Accessibility
Replay the plain-text sequence manually in a written field/value table.

## Safety and cost boundary
The events are fictional and contain no real chat, instructions, personal data, credentials, or external effects.

## Provenance boundary
Identity source: `profrod-site/content/articles/your-chat-history-is-not-a-system-of-record.md`. No article body or conversation is copied.

## Current source scope

The article now asks whether a fresh session can recover a research task from a lab notebook. This ordered-event replay demonstrates missing-sequence detection; it does not validate experiment provenance, intervals or a complete research handoff.

Source identity was reviewed against the pinned snapshot on November 9, 2026. This mapping review does not grant human pedagogical or accessibility approval.
