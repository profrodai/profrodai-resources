# profrodai-resources

Companion code for courses at [profrod.ai](https://profrod.ai), organised by course. One repo
instead of one-per-course, so a reader taking two courses clones once, and a later course can
build on an earlier one's example instead of reinventing it.

## Bootstrap record

The published initial commit contains `README.md` and `LICENSE` only. It predates the clarified
repository-birth contract in RULING-216 Amendment A2. This PR introduces `.gitignore` as its first
content diff, before any course resource reaches `main`; the public history is not rewritten to
claim otherwise. Future resource repositories start with their required safety `.gitignore`.

## Courses

| Course | Directory | What's there |
|---|---|---|
| [Agentic Coding with Cursor](https://profrod.ai/courses/agentic-coding-with-cursor) | [`courses/agentic-coding-with-cursor/order-api/`](courses/agentic-coding-with-cursor/order-api/) | `order-api`, the small Node/Express/TypeScript order-lookup service the course runs against starting in lesson 4. |

More courses land here as they ship. Each gets its own directory under `courses/<course-slug>/`;
nothing here is shared across courses unless a later README says otherwise.

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
