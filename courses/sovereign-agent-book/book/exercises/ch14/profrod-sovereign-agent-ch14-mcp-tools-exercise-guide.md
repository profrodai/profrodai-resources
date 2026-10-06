# Chapter 14: External tools with MCP

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Available draft · two ninety-minute units · construction edition**

Attempt the student work before consulting the solutions. Untouched exercises intentionally report NEEDS_WORK.

| Session | Notebook | Matching text | Purpose |
|---|---|---|---|
| A · 90 minutes | [A: build and connect a bounded MCP client](profrod-sovereign-agent-ch14-a-bounded-mcp-client-exercise.ipynb) | [Markdown](profrod-sovereign-agent-ch14-a-bounded-mcp-client-exercise.md) | Construct, connect and explain |
| B · 90 minutes | [B: break the connection, repair and transfer](profrod-sovereign-agent-ch14-b-mcp-repair-transfer-exercise.ipynb) | [Markdown](profrod-sovereign-agent-ch14-b-mcp-repair-transfer-exercise.md) | Diagnose, repair and transfer |

Each notebook includes its own setup, first-principles introductions and supplied data, and needs only Python's standard library: no model, network or key. Each notebook writes the scripted teaching server to a temporary folder and starts it as a child process, so it needs a POSIX system (Colab, Linux or macOS). Open either notebook in Google Colab with its badge (a current Colab CPU runtime), or use a local Python 3.12+ Jupyter kernel. No repository checkout, previous notebook kernel or live account is needed. Unit B can use an explicitly selected successful Unit A handoff; an invalid selected file refuses rather than substituting an answer.

Ninety minutes is the planned work allowance per unit. Actual completion time and understanding require classroom observation.

[Setup](../profrod-sovereign-agent-exercises-setup.md) · [Back to this asset](../profrod-sovereign-agent-exercises-start-here.md)

## Colab workflow and completion checklist

Use a CPU runtime; no install, API key, GPU, Drive mount or repository checkout is required.
Click the notebook's badge, save a copy, and run the three setup code cells in order. The long
`SERVER_SOURCE` cell is executable Python assigning source text for the child server; its comments
are part of that server, not disabled learner functions. Edit the later cells tagged as exercises.

Run all on an untouched student notebook should finish with **NEEDS_WORK**. That confirms setup,
not completion. Repair the learner definitions and rerun their assessments and downstream cells.
Worked solutions remain separate. Each Run all creates a new `attempt-*` folder; rerunning a later
cell updates that attempt, so export before experimenting further.

For A → B across separate Colab runtimes:

1. Complete A's core connection, then download its evidence ZIP and the edited notebook.
2. Extract `ch14-unit-a-handoff-v1.json` from the ZIP on your computer.
3. In B set `UPLOAD_HANDOFF = True`, run the selection/import cells and upload that JSON alone.
   Alternatively set `LEARNER_HANDOFF` to a local absolute path. Relative paths start from the
   notebook's initial working directory. The default `None` uses a labeled reference without
   asking for an upload. Missing, malformed or incompatible selected evidence stops execution.
4. Finish B, download its evidence ZIP and save the edited notebook before the runtime disconnects.

The final ZIP keeps the submission, independent server logs, actual runtime, server source and
learner function source where introspection is available. It is not a standalone replacement for
saving the edited notebook. Colab files are temporary: [Colab FAQ](https://research.google.com/colaboratory/faq.html).

| Mechanism | Unit and executable evidence | Ready when |
|---|---|---|
| Host, client and server roles; request identity | A's examples, learner `answer_for` and malformed-envelope cases | Own reply accepted; wrong/string/float/bool id and mixed/error envelopes refused |
| Stdio framing and diagnostics | A's split-read/echo examples; B's learner `split_frames` | Complete and unterminated frames bounded before parsing; stdout logs refused |
| Version and capability agreement | A's real server wire log and old-version refusal | initialize → initialized notification → discovery → call, with unique request ids |
| Discovery versus permission | A's `authorize`/offer transfer; B's negative control | Forbidden purchase absent from permitted log and present only in negative control |
| Failure reporting and liveness | B's normal/stale/wrong-id/oversized/endless/hang/EOF/notification-flood cases | Declared exception, deadline and independent call count observed; failed stream discarded |
| Protocol error versus tool failure | B's `rpc-error` and `tool-error` | Both fail without turning failure into a count; learner explains the different envelopes |
| Argument validation | B's flat-scalar schema transfer and stderr integration | Missing/extra/type errors refused; unsupported schemas and non-JSON values rejected |
| Cleanup | B's healthy/hung/lingering processes | Only processes started by the exercise ended; grandchild reaped, including on Linux |
| Always-on handoff and side effects | A → B import; B's lost-reply prediction | Provenance retained; timeout/EOF not mistaken for no side effect or permission to retry |
| Explanation and novel transfer | Both prediction, counterexample and submission cells | Human review of causal explanation, failed hypothesis and remaining limit |

## Scope and primary references

This is the authoritative **course exercise for the pinned MCP2025-06-18 stdio teaching subset**,
not the normative MCP specification or a production SDK. It teaches one request at a time,
integer ids, fixed bounded tool lists and text results. Full JSON Schema, Streamable HTTP and its
authorization, concurrent requests, resources/prompts, sampling, progress/cancellation,
pagination and changing tool lists are outside these two units. The scalar checker refuses
unsupported constraints; it must never be presented as a full validator.

Read the [pinned lifecycle](https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle),
[stdio transport](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports) and
[tools specification](https://modelcontextprotocol.io/specification/2025-06-18/server/tools).
A different protocol version is not intrinsically wrong: this client simply does not implement it.
Before connecting a real server, use a maintained SDK for the negotiated version, a full schema
validator and Chapter15's OS boundary. Keep Chapter11's approval and Chapter12's durable intent,
idempotency and reconciliation: JSON-RPC ids correlate replies, not business side effects.

## Troubleshooting

- **Setup appears to be comments:** expand the `SERVER_SOURCE` code cell and run it. Python stores
  it as a string; the next executable cell writes the child script. Later `def` cells are yours.
- **NEEDS_WORK / CONNECTION_NOT_READY:** expected before repair; inspect the printed failing case,
  edit its learner definition, and rerun that assessment and later cells. Run all uses your saved
  definitions, so save edits first.
- **NameError:** run setup and the earlier learner definitions in order after a kernel restart.
- **Selected handoff fails:** select the actual successful A JSON, not the ZIP or submission JSON.
  The unit intentionally refuses an expanded allowlist or missing independent observations.
- **Unexpected TimeoutError on healthy mode:** check runtime load and restart/retry the read-only
  teaching case. Do not turn a live side-effect timeout into an automatic retry.
- **Child processes prohibited:** use Colab, Linux or macOS with POSIX subprocess support.
- **Runtime disconnected:** recover the downloaded ZIP and edited notebook; runtime files alone
  are not durable storage. Never add real secrets to predictions, arguments or evidence logs.

Ninety minutes remains a planned allowance. Local execution and Linux CI are reported separately
from attended hosted Colab use and learner comprehension; neither latter outcome is inferred.

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
