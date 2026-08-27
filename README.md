# profrodai-resources

Runnable companions for the courses and long-form articles at
[profrod.ai](https://profrod.ai), organised by source slug. One clone contains the index,
starter labs, and verification gates; it is not a copy of the teaching site.

## What this phase is

This is a top-down curriculum map and scaffold. Every catalogued course has one small,
credential-free vertical slice that accepts an input, emits an observable result, and proves it
with a test. Those slices establish the run/verify/reset contract for later labs; they are not
completed course material, nor a substitute for the lessons.

The catalog is the machine-readable inventory in
[`catalog/curriculum.json`](catalog/curriculum.json), with an evidence table of exact source paths
and titles pinned to `rodriveracom/profrod-site@db4dc3afb65aa402069d04533d4ce9766d7444e4` in
[`catalog/profrod-site-source-index.json`](catalog/profrod-site-source-index.json). It contains
the 11 confirmed courses and 13 confirmed long-form articles currently tracked in that snapshot.
Short Notes are deliberately
out of scope: they are neither represented as articles nor given code in this phase.

The Phase 1 [curriculum contract](catalog/curriculum-manifest.json) is separate
from that identity catalog: it has one title-free record for each of the same
24 source paths. Cursor and the ZeoCore article have explicit learner
contracts; Cursor's existing `order-api` is its one nested lab contract. The
other 22 records remain planned. See the
[authoring guide](docs/curriculum-contract-authoring.md) for the boundary.

## Start here

```bash
git clone https://github.com/profrodai/profrodai-resources.git
cd profrodai-resources
git clone https://github.com/rodriveracom/profrod-site.git ../profrod-site
PROFROD_SITE_REPO=../profrod-site make verify
```

To explore one course, read its `README.md`, then run its local gate:

```bash
make -C courses/why-agents-fail verify
make -C courses/why-agents-fail run
```

Each new standard-library lab pins its observed runtime in `runtime.txt`, declares an empty
third-party dependency lock in `requirements.lock`, and has no network or credential requirement.
The existing Cursor `order-api` retains its own locked Node dependencies and gate.

`make verify` deliberately fails closed without `PROFROD_SITE_REPO`: the catalog is proven against
the exact Git object named in `catalog/profrod-site-source-index.json`, not against a copied title
or a mutable checkout. The supplied repository must contain that commit; fetch it if its clone is
shallow or has moved past the pin.

## CI trust boundary

Pull requests run `make verify-pr`: all 11 course gates and local catalog structure checks, with
no source-read secret and no claim of private-source provenance. Pinned-source verification runs
only in the trusted `main`/manual workflow from an explicit `main` checkout. See
[`docs/ci-trust-boundary.md`](docs/ci-trust-boundary.md) for the bootstrap limitation and review
rule.

## Taxonomy and status

- `starter`: runnable teaching code already supports a lesson path.
- `scaffolded`: one functional vertical slice is present; additional labs are intentionally not
  authored yet.
- `mapped`: source and documentation are catalogued, but no runnable companion is claimed.

Course directories are `courses/<site-course-slug>/`; article mappings are
`articles/<site-article-slug>/`. A course may link an external, already-public companion rather
than duplicate or migrate it. Article code needs a separate source/licensing and demonstration
decision before it is added.

## Contributing a next lab

1. Add or amend a catalog entry and keep its source pointer truthful.
2. Create a course-local README and a self-contained lab with `make run`, `make test`, and
   `make verify`.
3. Keep the first run deterministic, offline, and credential-free. Put any live-provider setup
   behind a later, clearly labelled opt-in decision.
4. Run `make verify` from the repository root. The catalog validator fails closed if an entry,
   README, runtime contract, or course gate is missing.

## Bootstrap record

The published initial commit contains `README.md` and `LICENSE` only. It predates the clarified
repository-birth contract in RULING-216 Amendment A2. This PR introduces `.gitignore` as its first
content diff, before any course resource reaches `main`; the public history is not rewritten to
claim otherwise. Future resource repositories start with their required safety `.gitignore`.

## Current runnable course

| Course | Directory | What's there |
|---|---|---|
| [Agentic Coding with Cursor](https://profrod.ai/courses/agentic-coding-with-cursor) | [`courses/agentic-coding-with-cursor/order-api/`](courses/agentic-coding-with-cursor/order-api/) | `order-api`, the small Node/Express/TypeScript order-lookup service the course runs against starting in lesson 4. |

The complete map names all remaining source courses. Each gets its own directory under
`courses/<course-slug>/`; nothing is shared across courses unless a later README says otherwise.

## Using a course's code

Clone the whole repo, or just the one course you need:

```bash
git clone https://github.com/profrodai/profrodai-resources.git
cd profrodai-resources/courses/agentic-coding-with-cursor/order-api
npm install
npm test
```

From the repository root, run the project gate with `make verify`. It performs the locked install,
format check, tracked agent-exhaust boundary lint, test suite, TypeScript check, and high-severity
dependency audit.

Each course directory is self-contained: its own `package.json`, its own dependencies, runnable
on its own without anything else in this repo.

## What's not here

This repo does not host `transformation-tracker-with-claude-code`'s companion code. That course
already has its own public repo,
[`profrodai/transformation-tracker-course`](https://github.com/profrodai/transformation-tracker-course),
live and linked from shipped lessons. It stays where it is; nothing here replaces it.

## License

MIT.
