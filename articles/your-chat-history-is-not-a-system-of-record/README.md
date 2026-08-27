# Your Chat History Is Not a System of Record — practice companion

**Teaching maturity:** mapped · **Companion contract:** complete · **Human review:** pending

## Practice objective
Replay an append-only event record and expose a missing sequence instead of guessing state from conversation.

## Prerequisites
Python 3 and familiarity with ordered events.

## Exercise
Inspect `practice.json`. Add an owner event, replay state, then remove a sequence and predict the reported gap.

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
