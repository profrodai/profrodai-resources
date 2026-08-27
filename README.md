<p align="center">
  <a href="https://profrod.ai">
    <img src="https://www.profrod.ai/og-image.webp" width="900" alt="Prof Rod teaching real-world AI automation with illustrated companions">
  </a>
</p>

<h1 align="center">Practice AI Engineering. Prove What Works.</h1>

<p align="center">
  <strong>24 small, runnable companions for the courses and articles at <a href="https://profrod.ai">profrod.ai</a>.</strong><br>
  Learn with real files, visible failures, and tests you can run on your own computer.
</p>

<p align="center">
  <a href="https://github.com/profrodai/profrodai-resources/actions/workflows/verify.yml"><img src="https://github.com/profrodai/profrodai-resources/actions/workflows/verify.yml/badge.svg" alt="Repository checks"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2f855a" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/beginner_path-Python_3.10%2B-3776ab" alt="Beginner path uses Python 3.10 or newer">
</p>

<p align="center">
  <a href="#start-here-your-first-exercise-in-five-minutes"><strong>Run your first exercise</strong></a>
  · <a href="#what-should-i-practise-next">Choose a practice</a>
  · <a href="#common-problems">Fix a problem</a>
  · <a href="#for-contributors-and-maintainers">Contribute</a>
</p>

---

**The learning loop:** read the teaching material → predict what should happen →
change the bytes → run the check → explain the evidence.

The Python beginner path makes no network calls after you clone the repository.
Every baseline uses invented data, and no exercise requires an API key, paid
call, or live AI service. The optional Node.js exercise downloads its locked
packages before it runs.

> **Companion boundary:** this repository contains practice material, not the
> courses or articles themselves. It never copies or republishes the teaching
> material from profrod.ai.

## Start here: your first exercise in five minutes

### What you need

- A computer with a terminal.
- [Git](https://git-scm.com/downloads).
- Python 3.10 or newer. Check with `python3 --version`.

On Windows, these instructions are easiest in
[Windows Subsystem for Linux](https://learn.microsoft.com/windows/wsl/install).
If your computer uses `python` instead of `python3`, substitute `python` in the
commands below.

You do **not** need Node.js for the first exercise. Node.js is only required for
the Cursor `order-api` exercise.

### 1. Download the exercises

Copy and paste these commands into your terminal one line at a time:

```bash
git clone --depth 1 https://github.com/profrodai/profrodai-resources.git
cd profrodai-resources
```

You should now be inside a folder named `profrodai-resources`.

Prefer buttons to Git commands? [Download the repository as a ZIP file](https://github.com/profrodai/profrodai-resources/archive/refs/heads/main.zip),
unzip it, and open your terminal in the new folder.

### 2. Run a ready-made example

```bash
python3 tools/run_article_practice.py \
  articles/build-a-working-agent-with-sovereign-agent/practice.json
```

You should see this result:

```json
{
  "failure": {
    "missing": [
      "check"
    ],
    "ready": false
  },
  "positive": {
    "missing": [],
    "ready": true
  }
}
```

That output proves two things:

- the complete example is allowed to continue; and
- the incomplete example stops and names the missing check.

If you see that output, congratulations: you have run your first verified
practice exercise.

**What just happened?** You did not ask an AI to tell you it succeeded. You ran
a deterministic check that proved one example complete and denied another
example because evidence was missing. That difference is the central habit
these companions teach.

### 3. Make a small change

Open these two files in any text editor:

- [the instructions](articles/build-a-working-agent-with-sovereign-agent/README.md)
- [the example data](articles/build-a-working-agent-with-sovereign-agent/practice.json)

Follow the README exercise. Run the same command again after every change. A
failure is useful: it means the checker found a difference between the result
you produced and the result the fixture says is correct.

## What should I practise next?

There are two kinds of companion:

- **Course practices** are small projects built around a runnable lab. Choose
  one when you want to edit code, add a test, and produce evidence.
- **Article practices** are short JSON exercises. Choose one when you want to
  explore a single idea in roughly 10–20 minutes.

You do not need to complete them in order.

### Course practices

Every course practice has a `PRACTICE.md` file with an objective, guided task,
project, evidence checklist, rubric, accessibility option, safety boundary, and
verification command.

Choose the description that sounds most useful. Each link opens the matching
practice guide; its final word tells you which runtime you need.

- **Change and test a small order API** — [Agentic Coding with Cursor](courses/agentic-coding-with-cursor/order-api/PRACTICE.md) *(Node.js)*
- **Check whether a business brief has enough evidence** — [Claude Code for Business](courses/claude-code-for-business/labs/01-brief-readiness/PRACTICE.md) *(Python)*
- **Route uncertain work to human review** — [LangGraph Agent Orchestration](courses/langgraph-agent-orchestration/labs/01-confidence-routing/PRACTICE.md) *(Python)*
- **Choose an eligible model without hiding cost or latency** — [Nebius Token Factory in Production](courses/nebius-token-factory-in-production/labs/01-model-selection/PRACTICE.md) *(Python)*
- **Turn retrieval inputs into a bounded deployment plan** — [NVIDIA NIM in Production](courses/nvidia-nim-in-production/labs/01-retrieval-plan/PRACTICE.md) *(Python)*
- **Store evidence without accepting duplicates** — [Tools, Memory, and Multi-Agent Systems](courses/tools-memory-and-multi-agent-systems/labs/01-evidence-store/PRACTICE.md) *(Python)*
- **Measure a before-and-after time saving honestly** — [Transformation Tracker with Claude Code](courses/transformation-tracker-with-claude-code/labs/01-baseline-delta/PRACTICE.md) *(Python)*
- **Separate deterministic code from uncertain agent work** — [Two Architectures](courses/two-architectures/labs/01-boundary-classifier/PRACTICE.md) *(Python)*
- **Prevent a voice agent from speaking after a call ends** — [Voice Agents, Not Chatbots](courses/voice-agents-not-chatbots/labs/01-turn-guard/PRACTICE.md) *(Python)*
- **Reject an answer that lacks required evidence** — [Why Agents Fail](courses/why-agents-fail/labs/01-evidence-gate/PRACTICE.md) *(Python)*
- **Measure operator minutes saved without hiding regressions** — [ZEO ITAM Autumn 2026](courses/zeo-itam-autumn-2026/labs/01-minutes-baseline/PRACTICE.md) *(Python)*

The **Why Agents Fail** exercise is a good first course practice. Run it from
the repository root:

```bash
make -C courses/why-agents-fail run
make -C courses/why-agents-fail verify
```

The first command prints a result. The second runs the tests. Success ends with
`OK`.

### Article practices

Each article folder contains:

- `README.md` — what to practise and how to know you succeeded;
- `practice.json` — one successful case and one failure case; and
- an exact command that checks both cases.

Choose one idea to explore. Every link opens a short, offline JSON exercise;
you only need Python to run it.

- **Prove an agent result has evidence and an owner** — [Build a Working Agent with sovereign-agent](articles/build-a-working-agent-with-sovereign-agent/README.md)
- **Deny unsafe file targets and overwrites** — [Build Your First ZeoCore Tool](articles/build-your-first-zeocore-tool/README.md)
- **Compare requested permissions with granted permissions** — [Claude Code Permissions Are Your Org Chart](articles/claude-code-permissions-are-your-org-chart/README.md)
- **Deduplicate customer data without silently losing records** — [Clean a Messy Customer List](articles/clean-a-messy-customer-list-with-claude-code/README.md)
- **Check whether every task handoff has an owner and evidence** — [Govern a Multi-Agent Project](articles/govern-a-multi-agent-project-with-zero-employee/README.md)
- **Choose a content block for a communication goal** — [The Content Kit](articles/the-content-kit/README.md)
- **Compare verification cost with expected failure loss** — [Unverified Output Has a Negative Margin](articles/unverified-output-has-a-negative-margin/README.md)
- **Calculate a synthetic token-usage cost** — [What Claude Code Actually Costs](articles/what-claude-code-actually-costs/README.md)
- **Decide whether a proposed change needs review** — [What Claude Code Actually Changes](articles/what-claude-code-changes/README.md)
- **Route decisions to operator, Master, stream, or Sparring** — [What Is a Zero-Employee Organization?](articles/what-is-a-zero-employee-organization/README.md)
- **Check whether a task is safe to run unsupervised** — [When Can You Actually Walk Away?](articles/when-to-let-an-agent-run-unsupervised/README.md)
- **Compare the transaction cost of a firm and a market** — [Why AI Agents Don't Dissolve the Firm](articles/why-ai-agents-dont-dissolve-the-firm/README.md)
- **Rebuild state from an ordered event record** — [Your Chat History Is Not a System of Record](articles/your-chat-history-is-not-a-system-of-record/README.md)

## A simple way to work through any exercise

Use the same loop every time:

1. **Read** the exercise README or `PRACTICE.md` from top to bottom.
2. **Run** the unchanged example once. This proves your setup works.
3. **Predict** what a small change will do before editing the file.
4. **Change one thing.** Small edits make failures easier to understand.
5. **Run the verification command again.**
6. **Explain the result** in your own words.
7. **Save evidence:** the command, its output, and the change you made.

Do not aim only for a green check. The useful part is being able to explain why
the successful case passed and why the failure case was denied.

## Folder map

```text
profrodai-resources/
├── courses/       runnable course labs and guided practice files
├── articles/      short article exercises with synthetic JSON data
├── catalog/       the machine-readable list of tracked companions
├── docs/          contributor and CI documentation
├── tests/         tests for the repository-wide checks
└── tools/         local exercise runners and validators
```

The teaching material stays on profrod.ai. This repository deliberately does
not contain copied lesson prose or article bodies.

## Common problems

### `git: command not found`

Install [Git](https://git-scm.com/downloads), close and reopen your terminal,
then try the clone command again.

### `python3: command not found`

Try:

```bash
python --version
```

If that prints Python 3.10 or newer, replace `python3` with `python` in the
exercise command. Otherwise install Python 3 before continuing.

### `destination path 'profrodai-resources' already exists`

You already have a folder with that name. Do not overwrite it. Either enter the
existing clone with `cd profrodai-resources`, or choose a different name for a
fresh copy:

```bash
git clone https://github.com/profrodai/profrodai-resources.git profrodai-resources-fresh
cd profrodai-resources-fresh
```

### `make: command not found`

The article exercises do not require `make`; run their `python3
tools/run_article_practice.py ...` command directly. For course practices,
install Make or use WSL on Windows.

### `No such file or directory`

You are probably in the wrong folder. Run:

```bash
pwd
ls
```

The `ls` output should include `articles`, `courses`, `catalog`, `tools`, and
`Makefile`. If it does not, return to the cloned repository with:

```bash
cd profrodai-resources
```

### `mismatch: expected=... observed=...`

The runner is working: your edited fixture no longer describes the result the
code produced. Compare `expected` with `observed`, decide which one should
change, and rerun the command.

### `cannot read practice spec` or `invalid ... JSON`

JSON punctuation is strict. Check for a missing quote, comma, brace, or square
bracket. A common mistake is leaving a comma after the final item. Your text
editor may highlight the exact line containing the error.

### `set PROFROD_SITE_REPO ...`

You ran the maintainer-only full repository gate. Beginners do not need that
gate. Use the verification command in the exercise README, or run the
repository's public checks with:

```bash
make verify-pr
```

### I changed too much and want to start again

First run `git diff` so you can see and learn from the changes. The simplest
safe reset is to make a new clone in a different folder; your original work
will remain available for comparison.

## Safety and cost

The baseline exercises are designed to be:

- offline;
- credential-free;
- deterministic;
- based on synthetic data;
- safe to rerun; and
- free of paid-provider calls.

Never paste real customer data, credentials, API keys, or private company
records into an exercise. If you later connect an exercise to a live service,
that is a separate project with its own cost, privacy, and permission review.

## Questions and feedback

If an instruction is unclear or an example behaves differently on your
computer, [open an issue](https://github.com/profrodai/profrodai-resources/issues).
Include the exercise path, the command you ran, and the error text. Remove all
credentials, private data, and identifying customer information before posting.

## For contributors and maintainers

The learner path above is intentionally simple. The repository-wide provenance,
maintenance, and contribution machinery is available below without interrupting
that path.

<details>
<summary><strong>Open maintainer verification and catalog details</strong></summary>

<br>

### Public pull-request gate

```bash
make verify-pr
```

This runs all 11 course gates, all 13 article exercise specifications, the
repository tests, manifest checks, maintenance checks, and local-link checks.
It does not need access to the teaching-site repository.

The whole-repository gate requires Git, Make, Python, Node.js, and npm because
it also tests the Cursor `order-api`. A learner running one Python exercise does
not need that full toolchain.

### Source-backed maintainer gate

```bash
git clone https://github.com/rodriveracom/profrod-site.git ../profrod-site
PROFROD_SITE_REPO=../profrod-site make verify
```

This additionally proves the catalog against the pinned profrod-site Git
object. It deliberately fails when `PROFROD_SITE_REPO` is missing. Pinned-source
verification runs only from trusted `main` or manual CI contexts; pull requests
never receive the private-source credential. See the
[CI trust-boundary documentation](docs/ci-trust-boundary.md).

### Catalog and status language

- [`catalog/curriculum.json`](catalog/curriculum.json) lists the 11 courses and
  13 long-form articles.
- [`catalog/profrod-site-source-index.json`](catalog/profrod-site-source-index.json)
  pins their exact source paths and titles.
- [`catalog/curriculum-manifest.json`](catalog/curriculum-manifest.json) connects
  each source item to its local practice guide and verification command.
- [`catalog/curriculum-maintenance.json`](catalog/curriculum-maintenance.json)
  records review ownership and due dates.

`contract_status: complete` means the companion package and its mechanical
checks exist. It does not mean the source course or article is reproduced or
finished here. `maturity` describes teaching maturity, while `review_status`
records independent human pedagogical and accessibility review. The current
manifest truthfully claims 11 scaffold courses, 13 mapped articles, zero
developed resources, and zero operator-reviewed resources.

### Contributing practice material

1. Keep source identity and provenance truthful.
2. Add a course-local guided practice and runnable lab, or an article-local
   exercise with synthetic positive and failure cases.
3. Keep the baseline deterministic, offline, credential-free, and safe to
   rerun.
4. Include an objective, evidence, rubric, accessibility route, safety/cost
   boundary, and exact verification command.
5. Run `make verify-pr`, then the source-backed `make verify` before requesting
   review.

Detailed contract rules live in the
[practice-companion authoring guide](docs/curriculum-contract-authoring.md).
The Transformation Tracker course also has a separate public companion at
[`profrodai/transformation-tracker-course`](https://github.com/profrodai/transformation-tracker-course);
the small local lab here does not replace it.

</details>

## License

The repository is licensed under the [MIT License](LICENSE).
