# Catalog provenance review: November 8, 2026

sow: public

Status: checks complete; operator acceptance pending. The operator-owned maintenance dates are unchanged until the operator answers.

## Evidence and findings

`PROFROD_SITE_REPO=<local-path> make catalog` passes: 11 courses, 13 articles, 1 imported course. The checkout is an independent canonical clone, clean on main 2acd8964de49b8ed49c09564d375864214591ec5, equal to gold's freshly advertised main. The validator reads the original pinned objects at db4dc3afb65aa402069d04533d4ce9766d7444e4; passing this proves pinned provenance, not current framing.

[Per-source drift and SHA256 evidence](2026-11-08/catalog-source-drift.json) covers all 24 pinned sources. 22 are changed; 2 are removed; 0 are unchanged. The missing sources remain `content/courses/transformation-tracker-with-claude-code/_course.md` and `content/articles/the-content-kit.md`. Current source bodies/descriptions are not copied into this public review.

The October 3 follow-up remains incomplete on reviewed resources main 8132ed0c597fd7abd7618003457a4861d61991b9: the source index still pins db4dc3af, the two removed paths remain in index/catalog/manifest, and there is no documented completion of the 22 companion-framing reviews. Relevant index/policy history and the current six open PRs show no repin/removal/companion-review follow-up PR. Companion-accuracy still records last review 2026-08-27. This is a bounded main/open-PR observation, not proof that no unpublished draft exists.

## Recommendation for one operator decision

Accept this completed evidence review, renew catalog-provenance to November 8 with next due December 9, and keep a separate, explicitly reviewed catalog correction: repin to current site; remove the two retired sources and companions coherently from catalog/manifest/curriculum; review the 22 changed companions against their current framing. Acceptance does not claim that follow-up is done, nor grant pedagogical acceptance of all companions.

The maintainer has not changed the operator's date. Full `make verify` currently stops at this overdue area after earlier source/curriculum stages pass. No validator exemption or changed cadence is proposed.
