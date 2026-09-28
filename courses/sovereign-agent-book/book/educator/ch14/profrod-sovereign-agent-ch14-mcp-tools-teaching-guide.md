# Chapter 14: teach the mechanism, then test transfer

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).


**Created:** 2026-09-28 · **Edition:** v1 · **Review:** classroom outcomes unobserved

## Goals and the evidence to collect

**Unit A, "Build and connect a bounded MCP client".** Learners:

- match replies to requests by id, and see that arrival order proves nothing;
- exchange one line of JSON with a child process, and see diagnostics kept on stderr;
- read a frame that arrives split across two reads;
- build `answer_for`, which accepts a reply only for its own integer id, and `authorize`, which allows a call only when the tool was advertised *and* allowed;
- connect to the scripted teaching server, count the words in "vanilla stock needs review", and prove from the server's own log that the advertised purchase tool was never called, although its description says ALWAYS.

**Unit B, "Break the connection, repair and transfer".** Starting from Unit A's handoff, learners:

- reproduce a careless client that reports a stale reply, 4, as the count of "one two three";
- build `split_frames`, which bounds every line before it is parsed, including a line that never ends;
- watch every failure mode end in an exception rather than a wrong answer;
- see a hung server end at its deadline, and closing the client end the server's whole process group;
- validate a new tool's arguments against its schema before any call;
- remove the allowlist and see the server's log catch the purchase.

Allocate ninety minutes to each unit; together they make the complete three-hour chapter practice. Each notebook runs on its own and includes all the introductions it needs.

A learner who starts with Unit B uses a labeled reference handoff unless they explicitly select their own Unit A work. Record that provenance. A reference start is useful study, not evidence of earlier construction.

## Prepare and rehearse

Use Google Colab or a local Python 3.12+ kernel on Linux or macOS. The notebooks need only the standard library: no model server, network or API key. They write the teaching server to a temporary folder and start it with the same Python, so a locked-down machine that forbids child processes cannot run them.

- Before class, restart and run the worked notebooks on the teaching machine, and check the retained `practical-work/ch14-a` and `ch14-b` folders, including the server call logs.
- Distribute the student notebook and Markdown files. The solutions folder adds answers and holdouts. Public answers are kept apart for teaching reasons; they are not secret examination material.

Chapter 3's agent loop and Chapter 2's typed tools are the prerequisites. Ask learners, before Unit A, who decides which tools Lucy's agent may use: the model, the tool's author, or the operator.

## Ninety-minute sequence for each unit

| Clock | Facilitation | Observable evidence |
|---|---|---|
| 0–5 | Read the concrete goal; commit to a prediction | Prediction and proposed falsifier |
| 5–25 | A: ids, one line to a child, a split frame. B: the careless client against the stale server | Values and corrected explanations |
| 25–50 | A: construct `answer_for` and `authorize`. B: construct `split_frames` | Source and grade table |
| 50–70 | A: connect and read the server's log. B: every failure mode, then deadlines and cleanup | Independent observation |
| 70–85 | Implement the transfer task; in B, run the negative control | Function, positive case, refusal and novel input |
| 85–90 | Retrieve, save and explain | Evidence, exit ticket and remaining limit |

## Misconceptions to surface

**The reply that came back answers my question.** Arrival order is not identity. The stale reply had the right shape and the wrong question.

**The server said the tool exists, so the agent may use it.** Discovery is a description written by an outside party. The operator's allowlist decides, inside the client, before any byte is sent.

**A wrong number is better than an error.** It is worse. Nothing downstream questions a plausible count; an exception is reported as a failure.

**A size limit on messages is enough.** A server that never sends a newline never completes a message. The limit must hold for the bytes still waiting.

**The deadline ends the problem.** It ends the waiting. Cleanup is a separate step: close the input, then signal the whole process group.

**MCP makes the tool safe.** The protocol connects. Starting the server's executable gave it the same access as any program; Chapter 15 adds the operating-system boundary.

## Progressive hints and worked reasoning

Give help in this order:

1. Ask what the message is: a notification, our reply, or someone else's.
2. Ask what the function must refuse, and what it must never change.
3. Only then discuss the order of the checks.

The transfer tasks change one constraint:

- **Unit A, offer only allowed tools.** Filtering the offer and refusing the call are both needed. Every offered tool costs prompt tokens and accuracy, as the chapter measured. None of the experiment's 648 native tool calls named a tool that was not offered, but nothing in the protocol prevents it, and Chapter 15 shows how text from outside can steer a model.
- **Unit B, validate a new tool's arguments.** The schema comes from the server; the check runs in the client. `True` is not a number of tubs, although Python says `isinstance(True, int)`.

An alternative implementation is valid if it meets the same behavioral contract.

## Changed-case prompt and remediation

- **Unit A:** the operator allows `place_purchase` too. What changes, and what should still stop an unapproved purchase? (Chapter 11's exact-spend approval.)
- **Unit B:** the server starts sending replies for two outstanding requests out of order. What would a client that sends two requests at once need that ours does not have? (A table of outstanding ids.)

For an identity error, print each arrived message beside the id you were waiting for. For a framing error, feed `split_frames` one byte at a time and watch the remainder grow. Keep the negative observation as evidence, then restore the learner's implementation.

## Assessment rubric

Score each dimension 0, 1 or 2:

- **0:** absent or incorrect;
- **1:** correct with specific assistance;
- **2:** independently supported by execution and explanation.

The suggested readiness threshold of 8/10 is a teaching choice, not a validated measurement scale.

| Dimension | Evidence for two points |
|---|---|
| Prediction and revision | Prior prediction, actual observation and a causal revision |
| Construction or repair | Learner-owned code satisfies the declared positive and negative cases |
| Connection | Traces the observed ranking or table back through the invoked learner code |
| Transfer | Handles a changed constraint and explains an independent new case |
| Evidence and limits | Retains provenance and distinguishes observations from stronger claims |

Untouched student notebooks intentionally contain unfinished work. A passing Run All means the notebook executes, not that the learner passes. The rubric needs a human assessment of the explanation.

## Record actual classroom evidence

Record anonymous counts for:

- setup success;
- first successful connection;
- the highest hint used;
- independent versus revealed-answer construction;
- novel transfer;
- recurring misconceptions.

Also record the actual minutes spent per stage, and where learners needed prerequisite remediation. Keep unknown values unknown.

**Surviving limitation:** the teaching server is scripted and local, and each failure is one mode at a time. A real server can combine them, and a real deployment adds HTTP, authorization and concurrent requests, which this client does not implement. The chapter measures what offering many tools costs a real model.

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
