# Curriculum contract authoring

The catalog source index owns every resource's title and private-source path.
`catalog/curriculum-manifest.json` owns only learner-contract state. Do not
copy titles into the manifest, add a record for a lab, or mark a resource
developed merely because a README or scaffold exists.

## Planned record

Until a resource is explicitly authorized for a learner contract, it has only
these fields:

```json
{
  "catalog_path": "content/articles/example.md",
  "kind": "article",
  "maturity": "mapped",
  "contract_status": "planned"
}
```

## Course contract

An authorized course contract documents audience, outcomes, prerequisites,
module sequence, lab/project map, assessment, safety/cost boundary, and
completion evidence. Its README must make the same boundary visible to a
learner. A lab is nested under the course and documents objective, setup,
commands, expected result, verification, rubric, failure modes, and
extensions.

## Article contract

An authorized article contract documents thesis, prerequisites,
demonstration/exercise route, fixtures, verification, and next learning step.
It is not permission to copy the article body or invent runnable code.

## Before proposing the next contract

1. Confirm the catalog path exists in the pinned source index.
2. Obtain scope and source/licensing authority for any new code or fixtures.
3. Keep the manifest JSON-only and run `python3 tools/validate_curriculum_manifest.py`.
4. Run `make verify-pr`; trusted source verification additionally needs
   `PROFROD_SITE_REPO`.
