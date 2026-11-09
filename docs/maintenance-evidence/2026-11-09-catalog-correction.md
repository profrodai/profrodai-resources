# Catalog source correction: November 9, 2026

sow: public

The catalog now pins site main `2acd8964de49b8ed49c09564d375864214591ec5` instead of the August snapshot. It contains 10 courses and 12 articles. Transformation Tracker and The Content Kit and their runnable companions are removed. Historical source and license records remain; no import is promised.

## Review of the 22 changed sources

This is a source-framing, stated-outcomes and companion-coverage review. It does not claim a full technical re-audit of every source body, course lesson, vendor statement or statistical result. No source prose is copied. The [per-source findings and SHA-256 bindings](2026-11-09-catalog-correction.json) identify each reviewed input. Companion README files now state their narrower coverage; human review and maturity labels are unchanged.

Important differences include the Python research-code courses versus the legacy TypeScript/business exercises, different axes in the current 2x2, and simple cost/grant fixtures versus measured caching and sandbox experiments. No small fixture is promoted to coverage of these missing capabilities.

The snapshot identifies repository source, not a new deployment or an observation that every public route currently serves these bytes.

## Verification checkpoint

- Source-backed catalog check: 10 courses, 12 articles, one imported course.
- All 10 current course gates pass, including TypeScript, five API tests and npm audit with zero vulnerabilities; the remaining course exercises run offline.
- Companion contract: 22 complete records, two existing developed flags, zero operator-reviewed records; 40 repository unit tests pass, including denial of retired records.
- Colab compatibility, consolidation provenance, CI trust separation, local Markdown links, routing and Chapter 14 notebook checks pass.
- The initial course gate caught a removed draft-release lesson URL. That practice is now explicitly standalone, and a regression test rejects the obsolete current URL.
- All blocks of changed/new Markdown pass the site's byte-matched U.S. convention rules: 40 blocks, zero findings. The first attempt could not load packages in the new clone; the successful check used an installed copy of the identical checker. This is a scoped Resources check, not the full site's `npm run content:market` corpus audit.
- Full `make verify` passed (exit 0) after integrating PR90's actual merge `effe7ebb867deea58486864d316ac48805c76b9b`. The earlier draft smoke failure and partial checks remain historical evidence; no gate was waived. This result preceded this documentation-only update. Uncompressed full-gate stdout SHA-256: `16f12dee079b76b02beb632823f4c777f1d3dd75603f3af8da61a4a06e9b5dc4`; stderr: `4a70dc3a5c0f8c9e04095a7052b1ab413338c9ac9a41c4376fd2ccc7597651c0`.

Raw logs stay private. The repaired curriculum/contract/routing/notebook run exited 0; uncompressed stdout SHA-256 is `ee8bfe50767c7a71bf62d8f05b8631254a79021ca9a056aafeee5e3dc4b62e49`, stderr `9a6299d8ff38cda3d89d9e2dc7450d0c98ffe78e8968d8a756ee7706a7fefe35`. Verification dates identify these mechanical runs; they do not change human-review status.

| Work item | Current delivery stage | Evidence | Remaining action | Owner/dependency |
|---|---|---|---|---|
| Catalog acceptance | Merged | [PR90](https://github.com/profrodai/profrodai-resources/pull/90) | Complete | Repository merger |
| Separate catalog correction | Implemented; full gate passed on accepted main | This report and per-source findings | Exact-head smoke, source review and authorized merge | Repository maintainer and reviewers |

Next action: complete exact-head smoke and the correction's normal source review, then authorized merge. Existing message wake is the continuation route; no timed job is registered. Nothing here claims an installed change or a new site deployment.
