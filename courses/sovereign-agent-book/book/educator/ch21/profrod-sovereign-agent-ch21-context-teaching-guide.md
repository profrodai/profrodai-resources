# Chapter 21: teach the mechanism, then test transfer

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).


**Created:** 2026-09-29 · **Edition:** v1 · **Review:** classroom outcomes unobserved

## Goals and the evidence to collect

**Unit A, "Budget and compact Lucy's context".** Learners:

- split a request into layers, stable first, and account for every token to one of them;
- compare the four-characters-per-token estimate with the tokenizer counts the chapter recorded;
- build `clear_old_tool_results`, which replaces all but the latest tool results with a marker, and `compact`, which clears tool results first, then summarizes the oldest turns, never touches pinned records and raises rather than cut silently;
- compact Lucy's day at three budgets and see a rule kept only in the transcript disappear, while the same rule kept as a pinned record survives.

**Unit B, "Break the context, then repair and transfer it".** Starting from Unit A's handoff, learners:

- check a summary that a real model wrote of Lucy's day against the facts it had to keep, including values Lucy later changed;
- build `cached_prefix_tokens`, which measures how much of a request a prefix cache can reuse, and `stable_first`, which puts the volatile snapshot last;
- replay ten turns in both layouts and compare the reuse with the prefill the chapter measured;
- count tokens pessimistically, with the smallest measured ratio of characters to tokens.

Allocate ninety minutes to each unit; together they make the complete three-hour chapter practice. Each notebook runs on its own and includes all the introductions it needs.

A learner who starts with Unit B uses a labeled reference handoff unless they explicitly select their own Unit A work. Record that provenance. A reference start is useful study, not evidence of earlier construction.

## Prepare and rehearse

Use Google Colab or a local Python 3.12+ kernel. The notebooks need only the standard library: no model server, network or API key. The model outputs Unit B studies were recorded in the chapter's experiment and ship inside the notebook, so every learner sees the same summary.

- Before class, restart and run the worked notebooks on the teaching machine, and check the retained `practical-work/ch21-a` and `ch21-b` folders.
- Distribute the student notebook and Markdown files. The solutions folder adds answers and holdouts. Public answers are kept apart for teaching reasons; they are not secret examination material.

Chapter 5's memory and Chapter 9's prefix cache are the prerequisites. Before Unit A, ask learners where Lucy's rule "never order mango from Frostline" should live so that it is still true tomorrow: in the conversation, in a summary, or somewhere else.

## Ninety-minute sequence for each unit

| Clock | Facilitation | Observable evidence |
|---|---|---|
| 0–5 | Read the concrete goal; commit to a prediction | Prediction and proposed falsifier |
| 5–25 | A: layers, the budget report, estimates and both cuts. B: check the real summary, then repair with pinned records | Values and corrected explanations |
| 25–50 | A: construct `clear_old_tool_results` and `compact`. B: construct `cached_prefix_tokens` and `stable_first` | Source and grade table |
| 50–70 | A: compact Lucy's day at three budgets. B: replay both layouts | Independent observation |
| 70–85 | Implement the transfer task | Function, positive case, refusal and novel input |
| 85–90 | Retrieve, save and explain | Evidence, exit ticket and remaining limit |

## Misconceptions to surface

**A bigger window makes this unnecessary.** The chapter measured accuracy falling with length well inside the window, and most of all for facts in the middle. Every token is also read on every turn.

**A good summary keeps what matters.** The summarizer decides what matters before the next question exists. The recorded summary is the evidence: learners check it fact by fact.

**Clearing a tool result loses the fact.** It loses it from the context. The call stays visible, and the agent can make it again. A rule Lucy said once cannot be fetched again, which is why it belongs in a record.

**The cache reuses what two requests share.** It reuses a prefix. One changed character at the top makes the rest new.

**Four characters per token is close enough.** For numbers and JSON it undercounts by more than half in the chapter's measurement, and a model server that receives a prompt longer than its window can cut it without an error.

## Progressive hints and worked reasoning

Give help in this order:

1. Ask which layer the text belongs to, and how often it changes.
2. Ask what the function must never change or drop.
3. Only then discuss the order of the steps.

The transfer tasks change one constraint:

- **Unit A, keep only the lines that answer a question.** Filtering by content beats cutting by position when the agent knows what it needs, and it still cannot answer an aggregate question whose matching lines do not fit.
- **Unit B, a worst-case count.** The smallest measured ratio makes a budget safe for any kind of text, at the price of leaving room unused for prose.

An alternative implementation is valid if it meets the same behavioral contract.

## Changed-case prompt and remediation

- **Unit A:** Lucy changes a pinned rule. What must happen to the old value, and who is allowed to change a pinned record? (Chapter 11's approval, and Chapter 4's events.)
- **Unit B:** the model server evicts its cache after five minutes idle. What does that do to the stable-first replay, and what would you measure?

For a compaction error, print the budget report after each step. For a cache error, print each request's first message on two consecutive turns and compare them character by character. Keep the negative observation as evidence, then restore the learner's implementation.

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

**Surviving limitation:** the notebooks measure what is visible to the model and what a cache could reuse, not what a model does with the context. The chapter's experiment measures that on small local models, and the recorded summary is one sample from one model.

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
