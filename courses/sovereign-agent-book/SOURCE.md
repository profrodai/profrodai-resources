# Source: Build Your Always-On AI Agent From Scratch, the course

Pinned source: https://github.com/profrodai/sovereign-agent@03b67411133409f6c897461639c704ec27264fa9

Import mode: `canonical-import`

## What was imported

From that commit, with its relative layout kept so every path the code computes still resolves:

- `book/exercises/`, `book/solutions/`, `book/educator/`: the 38 units, their solutions, and the
  educator guides and teaching copies. The three committed ZIP builds were not imported.
- `book/textbook/BOOK.json`, `checkpoints/`, `learner/`, `experiments/`, `skills/`, and the two
  appendix programs: the chapter code. The chapter prose, front matter and appendix prose were not
  imported; they live only on https://profrod.ai/book.
- `docs/evidence/book-chNN/`: the receipts the checkpoints read, and
  `docs/evidence/book-four-assets/verification-v2.json`, the receipt of the source commit's bytes.
- `scripts/book_distribution_v1.py` and `scripts/verify_practical_course_v1.py`, unchanged, and
  `scripts/verify_course_v1.py`, ported from `scripts/verify_book_assets_v2.py`.

## What changed on import

- Each exercise's Colab badge opens its notebook here instead of in sovereign-agent (152 links).
- Each audience's "start here" page downloads this repository's ZIP instead of a committed build.
- The learner guide links two book pages on profrod.ai instead of files that stayed behind.
- Because notebook bytes changed, every notebook and handoff was executed again here; the receipt
  is `docs/evidence/book-four-assets/verification-v3.json`.

## After import

- 2026-09-28: Chapter 14 (external tools with MCP) was written here, not imported: two units, their
  solutions and educator copies, a learner file, a scripted teaching server, a checkpoint and an
  experiment with its receipt in `docs/evidence/book-ch14/`. All 80 notebooks and 20 handoffs were
  executed again; the receipt is `docs/evidence/book-four-assets/verification-v4.json`.
- 2026-09-29: Chapter 21 (context engineering) was written here: two units, their solutions and
  educator copies, a learner file, a checkpoint and an experiment with its receipt in
  `docs/evidence/book-ch21/`. The edition's reader-facing label became "construction edition",
  so it no longer counts chapters. All 84 notebooks and 21 handoffs were executed again; the
  receipt is `docs/evidence/book-four-assets/verification-v5.json`.

- 2026-10-06: Chapter14 alone received a Colab usability and completeness revision.
  `verification-v7.json` records the first revision; the append-only successor
  `verification-v8.json` records the strict UTF-8/JSON follow-up and fresh/replayed execution of its four notebooks and its handoff,
  and explicitly inherits the unchanged80 notebook and20 handoff records from immutable v6.
  Student/solution and educator copies remain byte-identical. The stdlib Chapter14 gate also
  exercises repaired student cells, invalid imports, exports and failure controls in PR CI.

## License

The source is Apache-2.0 at the pin. On 2026-09-28 the operator, Rod Rivera, as copyright holder,
authorized the migrated course material to be published here under this repository's MIT license
(recorded as `operator-authorized-mit-grant-pending-record` in `catalog/consolidation-sources.json`).
The sovereign-agent package the chapter code imports remains Apache-2.0 and is installed from its
own repository, not copied.
