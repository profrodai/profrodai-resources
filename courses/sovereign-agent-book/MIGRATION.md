# Migration: the book's course leaves sovereign-agent

Pinned source: https://github.com/profrodai/sovereign-agent@03b67411133409f6c897461639c704ec27264fa9

Import mode: `canonical-import`

The operator's direction (2026-09-28): the book lives only on profrod.ai; its exercises and
teaching material live here; sovereign-agent is the finished agent, the one repository that
collects stars.

| Step | Where | State |
|---|---|---|
| 1. Import the course with its chapter code and receipts; re-execute every notebook here | this repository | this change |
| 2. The site links every notebook and Colab badge here, and hosts the chapters itself | rodriveracom/profrod-site | follows step 1 |
| 3. sovereign-agent removes `book/` from its main branch and points learners here | profrodai/sovereign-agent | follows step 2 |
| 4. Pin a sovereign-agent release from PyPI instead of a commit | this folder's `pyproject.toml` | after the operator publishes 1.5.0 |

Learners who open an old link keep working until step 3: sovereign-agent's history is never
rewritten, and its README will send them here.
