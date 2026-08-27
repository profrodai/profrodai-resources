<!-- DOC-DATE: 2026-08-27 · LAST-REVIEWED: 2026-08-27 · Rev 2 -->

# Practice-companion contract authoring

The catalog source index owns every resource's title and private-source path.
`catalog/curriculum-manifest.json` owns only practice-companion state. Do not
copy titles into the manifest, add a record for a lab, publish lesson or
article prose, scrape source bodies, or mark a resource developed merely
because a README, exercise, or scaffold exists.

## Record shape

Every catalogued resource has exactly one record. The course or article owns its
practice guide and exercise path; a nested lab never becomes a phantom catalog
record.

```json
{
  "catalog_path": "content/articles/example.md",
  "kind": "article",
  "maturity": "mapped",
  "contract_status": "complete",
  "review_status": "unreviewed",
  "exercise_path": "articles/example",
  "practice_guide": "articles/example/README.md",
  "verification": "python3 tools/run_article_practice.py articles/example/practice.json",
  "last_verified": "2026-08-27"
}
```

`contract_status` proves the companion package is structurally and behaviorally
complete. It does not promote `maturity`. `review_status` changes to
`operator-reviewed` only after an independent human pedagogical and accessibility
review; no gate infers that judgment.

## Course companion

A course companion documents an objective, guided exercise, project, evidence,
rubric, accessibility route, safety/cost boundary, and exact verification
command. It uses the existing runnable lab to reinforce the source course. It
does not reproduce the course's modules or explanations.

## Article companion

An article companion documents a practice objective, prerequisites, exercise,
verification, evidence, rubric, accessibility route, safety/cost boundary, and
provenance boundary. Its `practice.json` contains exactly one positive and one
failure case using original synthetic fixtures. It is not permission to copy or
scrape the article body.

## Maintenance and verification

1. Confirm the catalog path exists in the pinned source index and preserve the
   exact 24-record set unless the site catalog changes under separate review.
2. Keep fixtures synthetic, deterministic, offline, credential-free, and safe
   to rerun.
3. Update `last_verified` and the owned cadence record when a companion is
   reviewed or its dependencies, links, provenance, or concepts change.
4. Run `python3 tools/validate_curriculum_manifest.py`, then `make verify-pr`.
   Trusted source verification additionally needs `PROFROD_SITE_REPO`.
5. Record human review explicitly; mechanical green is not pedagogical approval.
