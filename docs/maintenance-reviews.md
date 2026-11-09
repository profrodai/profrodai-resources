# Curriculum maintenance reviews

Each entry records a review behind a date change in `catalog/curriculum-maintenance.json`: what was checked, what was found, and what follows. Mechanical green is not pedagogical approval (docs/curriculum-contract-authoring.md, step 5).

## 2026-10-03: catalog-provenance and locked-dependencies

These were overdue since 2026-09-27 and 2026-09-03, and `curriculum-maintenance` failed every pull request, including #52.

### catalog-provenance (owner: operator; checks run by PROFROD, accepted when the operator merges)
- **What ran:** `PROFROD_SITE_REPO=<profrod-site checkout> make verify`, which reported "catalog valid: 11 courses, 13 articles, 1 imported course" against the pinned source `db4dc3afb6`. Provenance against the pin holds.
- **Finding: the pin is stale against the site's current `main`.**
  - 22 of the 24 pinned source files have changed since the pin. The site repositioned its courses and articles for frontier-lab candidates (profrod-site #219–#224).
  - 2 no longer exist on the site:
    - `content/courses/transformation-tracker-with-claude-code/_course.md` (the course was retired);
    - `content/articles/the-content-kit.md` (unpublished on 2026-10-02 and kept as a lint fixture).
- **Follow-up, a separate pull request:**
  - repin the source index to the current site;
  - drop the two removed sources and their companions from the catalog, manifest and curriculum;
  - review the 22 changed companions against their new framing (the companion-accuracy area).

### locked-dependencies (owner: maintainer)
- `courses/sovereign-agent-book/uv.lock`: `uv lock --check` is current (51 packages, CPython 3.12.13).
- `courses/agentic-coding-with-cursor/order-api/package-lock.json`: `npm audit` found 3 moderate advisories (express 4.22.2, body-parser 1.20.5–1.20.6, qs 2.2.5–6.15.3). `npm audit fix` resolved all three within the declared ranges, and the lockfile is updated. `npm audit` now reports 0, and the service's tests pass (5 of 5).

## 2026-10-18: locked-dependencies (owner: maintainer)

The overdue review was performed under the explicit amendment of profrod-SOW-338.
[Commands, raw-output hashes, dependency-by-dependency decisions and limits](maintenance-evidence/2026-10-18.md) record the actual review. npm audit reports zero vulnerabilities, all five API tests and TypeScript pass, and `uv lock --check` passes using CPython 3.12.13. New releases were reviewed without changing either lockfile: retain the tested Express 4 / Node 24 / TypeScript 5 / Vitest 4 course baseline and the compatible Python graph, with no reported advisory requiring an emergency bump. Only this maintainer-owned review date is renewed to 2026-10-18, due 2026-10-25; this is not a claim that all dependencies are latest or that all notebooks have been executed.

## 2026-10-27: locked-dependencies (owner: maintainer)

The review was due 2026-10-25 and was performed by the maintainer seat under the Architect's approval `ans_0e1e3fffeb2fe928` (sow: profrod-ops-SOW-01).
[Commands, raw-output hashes, the one change and limits](maintenance-evidence/2026-10-27.md) record the actual review. **One package changed:** `qs` 6.16.0 to 6.16.1 in `courses/agentic-coding-with-cursor/order-api/package-lock.json` only, for GHSA-6pq8-jhm2-2vcw (published 2026-10-27, first patched 6.16.1), inside Express's declared `qs ~6.16.0` range; `package.json` and `uv.lock` are unchanged and 6.17.0 was not taken. After the change `npm audit` reports zero vulnerabilities, all five API tests and TypeScript pass, and `uv lock --check` passes using CPython 3.12.13; the exact-version PyPI metadata check reports no vulnerability and no yanked locked release. No other bump is proposed. Only this maintainer-owned review date is renewed to 2026-10-27, due 2026-11-03; this is not a claim that all dependencies are latest or that all notebooks have been executed.


## 2026-11-08: locked-dependencies and catalog-provenance evidence

sow: public. This maintenance review was assigned by the maintainer’s operator.

**Locked dependencies (maintainer decision):** [Review, targeted Tornado patch, tests and all dependency decisions](maintenance-evidence/2026-11-08.md). Tornado 6.5.10 has three reported advisories fixed in 6.6; only that package changes in uv.lock. All 5 npm tests, TypeScript, patched course gate/21 learner checkpoints and 66 Tornado header tests pass; exact patched metadata reports no advisories/yank. npm lock and dependency declarations are unchanged. Maintainer review November 8; next due November 15.

**Catalog provenance (operator acceptance pending):** [Actual current-main comparison and recommendation](maintenance-evidence/2026-11-08-catalog-provenance.md). The pinned catalog validates, but22 sources changed and 2 were removed against site main 2acd8964. The October 3 repin/remove/companion-framing follow-up remains uncompleted in reviewed main/open PRs. Operator dates stay unchanged until the operator answers. Full make verify stops at that existing overdue record; no waiver or complete gate pass is claimed.


## 2026-11-09: operator acceptance of the November 8 catalog review

sow: public. The operator accepted the [November 8 provenance review](maintenance-evidence/2026-11-08-catalog-provenance.md). [Acceptance and required separate correction](maintenance-evidence/2026-11-09-catalog-acceptance.md) record the boundary: review date November 8, next due December 9; repin the source index, remove the two retired sources and review the 22 changed pages in a separate pull request during the same week. The earlier pending entry and failed gate evidence remain historical records, not a claim that acceptance or the correction happened earlier.
