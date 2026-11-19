# 12 · Agentic observability (edition 5): see what happened before deciding why

Two class notebooks for Lucy's agentic ERP, edition 5:

1. `ITAM-Agentic-Observability-01-2026.ipynb`: record one agent run as spans and events, read a trace, and tell a green call from good information.
2. `ITAM-Agentic-Observability-02-2026.ipynb`: turn evidence into diagnosis: a failure matrix, an incident note, an outcome check against a trajectory check, a challenged judge, and a policy change compared fairly.

## Two ways to run them

- **Live (the course path).** Open in Google Colab or Jupyter (Python 3.10+) and run `connect()` with your own OpenAI API key. Every decision is a live call billed to your account; each agent trial allows at most six calls and the kernel at most 100.
- **Test double (no key, no cost).** Set `USE_TEST_DOUBLE = True` in the first code cell. A scripted, rule-based stand-in answers each model call. It is **not a language model**: use it to check that the notebook runs, not to learn anything about a model. Its evidence file is named `...-test-double.json`.

The only installed dependency is Pydantic, pinned to 2.11.7. The live path is unchanged from the class copies.

## What was checked

Nothing has been run by an agent on the live path, and no key or paid call was used. The test-double path is run on a clean machine by the zeoconnect gate; see the pull request for the receipt once it exists. These notebooks are not part of `make verify`'s offline practicals.

## Provenance

The class copies are in the zeo-evidence intake with these sha256 values: `ITAM-Agentic-Observability-01-2026.ipynb` 49dffc38a924db18e60a3d797dc2967082d65efa7143d0f7824126f5003fa31f; `ITAM-Agentic-Observability-02-2026.ipynb` 277e71260422adb86490250066a5d78452bf0120471c112528980c5f3f8bb201. The only differences are the "Two ways to run" cell, the `USE_TEST_DOUBLE` switch, the test-double cell, the pinned install line, and the evidence file name under the test double.
