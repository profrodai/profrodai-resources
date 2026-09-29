---
jupyter:
  authors:
  - name: Prof Rod
    website: https://profrod.ai
  course:
    book_url: https://profrod.ai/book
    community_url: https://profrod.ai/community
    distribution_version: '2026-09-10'
    edition: twenty-chapter-v1
    instructor: true
    lesson_id: context
    planned_minutes: 90
    resource_id: profrod-sovereign-agent-ch21-a-context-budget-compaction-solution
    self_contained_runtime: true
    source_basis: chapter-21-manuscript
    source_unit: ch21-a
    source_url: https://github.com/profrodai/sovereign-agent
    unit: ch21-a
  jupytext:
    notebook_metadata_filter: all
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.19.5
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
  language_info:
    name: python
    version: '3.12'
---

# Chapter 21, Unit A: Budget and compact Lucy's context

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Instructor worked edition · 90 minutes of dedicated work · 2026-09-29**

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/profrodai/profrodai-resources/blob/main/courses/sovereign-agent-book/book/solutions/ch21/profrod-sovereign-agent-ch21-a-context-budget-compaction-solution.ipynb) Runs on Google Colab or any Python 3.12+ Jupyter kernel.

This edition contains the worked `clear_old_tool_results`, `compact` and transfer solution, instructor explanations and hidden checks. Learners should attempt the student edition first.

| Minutes | Dedicated work | Saved evidence |
| --- | --- | --- |
| 0–10 | Predict which of Lucy's facts survive when the day no longer fits | Written prediction |
| 10–25 | Layers, the budget report, estimates and both cuts of a long tool result | Observed outputs |
| 25–55 | Construct `clear_old_tool_results` and `compact`; pass the visible cases | Learner code and grade table |
| 55–70 | Compact Lucy's day at three budgets and check what survived | Compaction reports |
| 70–85 | Changed-constraint task: keep only the lines that answer a question | Transfer results |
| 85–90 | Explain records versus transcript and save evidence | Retained submission |


## Run the self-contained setup

The unit needs only Python's standard library. The collapsed cell below creates your work folder and defines the supplied parts of the unit:

- **Counting:** `estimate_tokens`, about four characters per token, and `message_tokens` for one chat message.
- **Layers:** `Layers(system, pinned, conversation)` holds what the model will see, stable first. `budget_report` counts the tokens in each layer, as `/context` does in a coding agent.
- **Cutting a tool result:** `head` and `head_and_tail`.
- **Lucy's day:** `lucy_day()` returns a long conversation. Early on, Lucy states rules and decisions and later changes some of them, and bulky tool results sit in between. `QUESTIONS` pairs each fact with where it lives.
- **Summarizers:** `keep_numbers`, which keeps only lines with a digit in them, and `forget_everything`, which keeps nothing. Both are deterministic stand-ins for a model writing a summary.

Run setup on every fresh kernel. Your saved work lives in `practical-work/ch21-a`. Restarting a kernel clears variables, not saved files.

<details><summary>Supplied setup, layers, Lucy's day and summarizers</summary>

```python jupyter={"source_hidden": true} tags=["setup", "embedded-runtime"]
import json
import math
import os
import random
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

minimum_python = (3, 12)
if sys.version_info[:2] < minimum_python:
    raise RuntimeError("This unit needs Python 3.12 or newer; Google Colab runs Python 3.13.")

if "COURSE_START_DIRECTORY" not in globals():
    COURSE_START_DIRECTORY = Path.cwd()
    COURSE_ROOT = Path(tempfile.mkdtemp(prefix="ch21-course-"))


def estimate_tokens(text):
    """About four characters per token for English prose; the chapter measures when it is wrong."""
    return math.ceil(len(text) / 4)


def message_tokens(message):
    return estimate_tokens(str(message.get("content", ""))) + 4


class ContextOverflowError(Exception):
    """What must be sent does not fit in the budget; nothing is cut silently."""


@dataclass
class Layers:
    """Everything the model will see, in the order it is sent: stable first, volatile last."""

    system: str
    pinned: list = field(default_factory=list)
    conversation: list = field(default_factory=list)

    def messages(self):
        head_text = self.system
        if self.pinned:
            head_text += "\n\nRecords Lucy's shop keeps (current):\n" + "\n".join(
                f"- {r}" for r in self.pinned
            )
        return [{"role": "system", "content": head_text}, *self.conversation]


def budget_report(layers):
    system = estimate_tokens(layers.system)
    pinned = sum(estimate_tokens(r) for r in layers.pinned)
    conversation = sum(message_tokens(m) for m in layers.conversation)
    return {
        "system": system,
        "pinned": pinned,
        "conversation": conversation,
        "total": system + pinned + conversation,
    }


def head(text, budget):
    kept, used = [], 0
    for line in text.splitlines():
        cost = estimate_tokens(line + "\n")
        if used + cost > budget:
            break
        kept.append(line)
        used += cost
    return "\n".join(kept)


def head_and_tail(text, budget):
    lines = text.splitlines()
    first = head(text, budget // 2).splitlines()
    last, used = [], 0
    for line in reversed(lines[len(first) :]):
        cost = estimate_tokens(line + "\n")
        if used + cost > budget // 2:
            break
        last.insert(0, line)
        used += cost
    omitted = len(lines) - len(first) - len(last)
    return (
        text if omitted <= 0 else "\n".join([*first, f"[... {omitted} lines omitted ...]", *last])
    )


def tool_message(name, payload):
    return {"role": "tool", "name": name, "content": json.dumps(payload, separators=(",", ":"))}


FLAVORS = "vanilla chocolate pistachio mint coffee caramel lemon raspberry hazelnut coconut".split()
SYSTEM = "You are the assistant for Lucy's ice cream shop. Answer briefly."
PINNED = [
    "The shop is Lucy's Scoops.",
    "Never order mango from Frostline.",
    "Today the shop closes at 7 pm (changed from 6 pm).",
    "Approved: 15 tubs of chocolate from Frostline (changed from 12).",
    "Vanilla is ordered from Polar Dairy.",
    "The health inspector is Dana Ortiz.",
]


def lucy_day():
    """Lucy's day: rules and decisions early, some changed later, bulky tool results between."""
    rng = random.Random(8)

    def freezer():
        return tool_message("stock_level", {"freezer": {f: rng.randint(0, 40) for f in FLAVORS}})

    def sales(n):
        rows = [
            {
                "at": f"{rng.randint(10, 17):02d}:{rng.randint(0, 59):02d}",
                "flavor": rng.choice(FLAVORS),
                "tubs": rng.randint(1, 3),
            }
            for _ in range(n)
        ]
        return tool_message("sales_today", {"rows": rows})

    said = [
        ("Good morning. For the record, the shop is Lucy's Scoops.", None),
        ("Never order mango from Frostline again; they were late twice.", None),
        ("We close at 6 pm today.", None),
        ("Check the whole freezer, please.", freezer),
        ("Approve 12 tubs of chocolate from Frostline.", None),
        ("What sold this morning?", lambda: sales(40)),
        ("From now on, order vanilla from Polar Dairy.", None),
        (
            "Record the delivery that just came in.",
            lambda: tool_message(
                "record_delivery", {"order": "A-4817", "flavor": "pistachio", "tubs": 20}
            ),
        ),
        ("Check the freezer again.", freezer),
        ("Make that 15 tubs of chocolate instead of 12.", None),
        (
            "How much strawberry is left?",
            lambda: tool_message("stock_level", {"flavor": "strawberry", "tubs": 7}),
        ),
        ("Sales so far?", lambda: sales(60)),
        ("The health inspector coming Friday is Dana Ortiz.", None),
        ("Check the freezer.", freezer),
        ("Change of plan: we close at 7 pm today.", None),
        ("Sales update, please.", lambda: sales(70)),
        ("Put the sign-up sheet by the till.", None),
    ]
    messages = []
    for text, tool in said:
        messages.append({"role": "user", "content": text})
        if tool:
            messages.append(tool())
            messages.append({"role": "assistant", "content": "Done; the result is above."})
        else:
            messages.append({"role": "assistant", "content": "Noted."})
    return messages


QUESTIONS = [
    ("the shop's name", "Lucy's Scoops", "rule"),
    ("mango is never ordered from Frostline", "mango from Frostline", "rule"),
    ("closing time is 7 pm", "7 pm", "changed later"),
    ("chocolate approved is 15 tubs", "15 tubs of chocolate", "changed later"),
    ("vanilla comes from Polar Dairy", "Polar Dairy", "rule"),
    ("delivery A-4817 was 20 tubs", "A-4817", "old tool result"),
    ("strawberry stock was 7 tubs", "strawberry", "old tool result"),
    ("the inspector is Dana Ortiz", "Dana Ortiz", "rule"),
    ("the sign-up sheet goes by the till", "till", "recent"),
]


def survives(layers, needle):
    """Is `needle` anywhere in what the model will see?"""
    return any(needle.lower() in str(m["content"]).lower() for m in layers.messages())


def keep_numbers(older):
    """A summarizer that keeps only the lines with a digit in them, oldest first."""
    return "\n".join(
        f"{m['role']}: {m['content']}"[:160]
        for m in older
        if m["role"] != "tool" and any(c.isdigit() for c in str(m["content"]))
    )


def forget_everything(older):
    return "(the earlier conversation was about the shop)"


COURSE_WORK = COURSE_START_DIRECTORY / "practical-work" / "ch21-a"
COURSE_WORK.mkdir(parents=True, exist_ok=True)
os.chdir(COURSE_WORK)
print("Python", sys.version.split()[0])
print("Save your work here:", COURSE_WORK)
```

</details>


## Commit to a prediction before the examples

Lucy's day is a long conversation: rules and decisions at the start, some changed later, and bulky freezer and sales tables in between. It no longer fits the budget, so the oldest part must go. Before you run anything below, write down which of these facts you expect the model can still see after the day is cut to fit:

- the shop's name, and the rule about mango and Frostline;
- the closing time, which Lucy changed from 6 pm to 7 pm;
- delivery A-4817's 20 tubs, which appeared only in a tool result;
- where the sign-up sheet goes, from the last minute of the day.

```python tags=["prediction", "learner-notes"]
prediction_notes = {
    "prediction": "Write which of the four facts survive a cut to the budget.",
    "reason": "Name the rule behind that prediction.",
    "falsifier": "Name an observation that would prove the explanation wrong.",
    "revision": "After execution, explain what changed in your understanding.",
}
```

### Layers, and a budget for each

A model sees one request: a sequence of messages. It is useful to split that request into **layers** by how often they change. The system text changes almost never. The **pinned records**, facts the application itself keeps (Lucy's rules, approvals and suppliers), change rarely. The **conversation** grows every turn. Sending the stable layers first matters for cost (Chapter 9's prefix cache), and splitting them lets you see where the budget goes.

```python tags=["foundation", "worked-example"]
day = lucy_day()
print(len(day), "messages")
print(json.dumps(budget_report(Layers(SYSTEM, [], day)), indent=1))
print(json.dumps(budget_report(Layers(SYSTEM, PINNED, day)), indent=1))
biggest = max(day, key=message_tokens)
print("largest message:", biggest["role"], message_tokens(biggest), "tokens")
```

Most of the day's tokens are tool results that nobody will read again: freezer tables and sales logs. The rules Lucy stated cost almost nothing. That imbalance is why compaction starts with tool results.

### An estimate, and when it is wrong

`estimate_tokens` assumes four characters per token. A tokenizer splits digits, punctuation and JSON keys into more pieces than English words, so the right ratio depends on the kind of text. The chapter counted real tokens with the qwen2.5 tokenizer; the cell below compares the estimate with those counts.

```python tags=["foundation", "worked-example"]
MEASURED = [
    {"kind": "prose", "chars": 1775, "estimate": 444, "actual": 349},
    {"kind": "json", "chars": 2573, "estimate": 644, "actual": 1048},
    {"kind": "numbers", "chars": 2016, "estimate": 504, "actual": 1187},
    {"kind": "python", "chars": 2400, "estimate": 600, "actual": 540},
]
for row in MEASURED:
    error = row["estimate"] / row["actual"] - 1
    counts = f"estimate {row['estimate']:5}, tokenizer {row['actual']:5} ({error:+.0%})"
    print(f"{row['kind']:8} {row['chars']:5} characters: {counts}")
```

### Two cuts of a long tool result

When one tool result is too long, keep part of it. `head` keeps the start, which loses the most recent rows of a log. `head_and_tail` keeps both ends and says how many lines it left out, so the model at least knows something is missing.

```python tags=["foundation", "worked-example"]
log = "\n".join(
    f"{10 + i // 12}:{(i * 5) % 60:02d} | {FLAVORS[i % 10]} | {1 + i % 3} tubs" for i in range(80)
)
print(head(log, 60))
print("---")
print(head_and_tail(log, 60))
```

## 1. Construct `clear_old_tool_results`

`clear_old_tool_results(messages, keep_last)` returns a new list in which every tool result except the last `keep_last` has its content replaced by a short marker:

```text
[tool result cleared to save context: N tokens]
```

`N` is `estimate_tokens` of the old content. Keep every other message unchanged, keep the order, and do not change the input list or its dictionaries. The call that produced each result stays in the conversation, so the agent can see that it looked something up, and can look it up again.

The starter clears nothing.

```python tags=["exercise", "learner-owned", "ch21-clear"]
def clear_old_tool_results(messages, keep_last):
    """All but the last `keep_last` tool results replaced by a marker; the input is unchanged."""
    positions = [i for i, m in enumerate(messages) if m.get("role") == "tool"]
    old = set(positions[: max(len(positions) - keep_last, 0)])
    cleared = []
    for i, message in enumerate(messages):
        if i in old:
            size = estimate_tokens(str(message.get("content", "")))
            cleared.append(
                {**message, "content": f"[tool result cleared to save context: {size} tokens]"}
            )
        else:
            cleared.append(dict(message))
    return cleared
```

## 2. Construct `compact`

`compact(layers, budget, summarize)` returns new `Layers` that fit in `budget` tokens, according to `budget_report(...)["total"]`, in at most two steps:

1. If the layers already fit, return a copy unchanged.
2. Clear old tool results, keeping the last two. If that fits, stop.
3. Otherwise replace every message **before the latest user message** with one user message whose content is `"Summary of the earlier conversation:\n" + summarize(older)`. Keep the latest user message and everything after it.

Never change `system` or `pinned`. If `system` and `pinned` alone exceed the budget, if there is nothing older to summarize, or if the result still does not fit, raise `ContextOverflowError`. Never return a context over the budget.

The starter drops the oldest messages until the rest fits, which is what many agents do.

```python tags=["exercise", "learner-owned", "ch21-compact"]
def compact(layers, budget, summarize):
    """Fit `layers` into `budget`: clear old tool results, then summarize the oldest turns."""
    if budget_report(Layers(layers.system, layers.pinned, []))["total"] > budget:
        raise ContextOverflowError("the system text and pinned records alone exceed the budget")
    current = Layers(layers.system, list(layers.pinned), [dict(m) for m in layers.conversation])
    if budget_report(current)["total"] <= budget:
        return current
    current.conversation = clear_old_tool_results(current.conversation, 2)
    if budget_report(current)["total"] <= budget:
        return current
    users = [i for i, m in enumerate(current.conversation) if m.get("role") == "user"]
    latest = users[-1] if users else len(current.conversation)
    older, recent = current.conversation[:latest], current.conversation[latest:]
    if not older:
        raise ContextOverflowError("the latest turn alone exceeds the budget")
    summary = {
        "role": "user",
        "content": "Summary of the earlier conversation:\n" + summarize(older),
    }
    current.conversation = [summary, *recent]
    if budget_report(current)["total"] > budget:
        raise ContextOverflowError("the compacted context still exceeds the budget")
    return current
```

<details><summary>Hint 1 — why the tool results go first</summary>

The worked example showed where the tokens are: freezer tables and sales logs. Clearing them loses facts that appeared only in a tool result, but the agent can call the tool again. A rule Lucy said once cannot be fetched again.

</details>

<details><summary>Hint 2 — what "the latest user message" protects</summary>

The latest user message is the question being answered now. Summarizing it away would answer a question nobody asked. Find its index with the last position whose role is `user`.

</details>

<details><summary>Hint 3 — why raise instead of cutting</summary>

A context over the budget is either rejected by the model API or cut somewhere you did not choose. An exception is a failure someone can see and fix; a silent cut is a wrong answer later.

</details>

```python tags=["assessment", "visible"]
import copy

TOOL = tool_message("stock_level", {"rows": ["vanilla 12"] * 40})
SMALL = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
LONG = [
    m
    for i in range(8)
    for m in ({"role": "user", "content": f"q{i}"}, TOOL, {"role": "assistant", "content": f"a{i}"})
]


def cleared_count(messages):
    return sum("cleared to save context" in str(m["content"]) for m in messages)


def run_compact(candidate, layers, budget, summarize):
    try:
        out = candidate(layers, budget, summarize)
        return out, None
    except ContextOverflowError:
        return None, "ContextOverflowError"
    except Exception as error:
        return None, type(error).__name__


def grade_unit(clear, compactor):
    rows = []

    def row(case, passed, observed):
        rows.append({"case": case, "observed": observed, "status": "PASS" if passed else "FAIL"})

    original = copy.deepcopy(LONG)
    out = clear(LONG, 2)
    row(
        "clears all but the last two",
        cleared_count(out) == 6 and LONG == original,
        cleared_count(out),
    )
    row(
        "keeps every message and the order",
        [m["role"] for m in out] == [m["role"] for m in LONG],
        len(out),
    )
    row(
        "keep_last beyond the count clears nothing",
        cleared_count(clear(LONG, 99)) == 0,
        cleared_count(clear(LONG, 99)),
    )

    fits, error = run_compact(compactor, Layers("s", ["rule"], SMALL), 10_000, forget_everything)
    row(
        "a context that fits is unchanged",
        error is None and fits.conversation == SMALL,
        error or "unchanged",
    )

    layers = Layers("s", ["Never order mango from Frostline."], LONG)
    after_clear = budget_report(Layers("s", layers.pinned, clear_old_tool_results_reference(LONG)))[
        "total"
    ]
    out, error = run_compact(compactor, layers, after_clear, forget_everything)
    step_one = error is None and out is not None and len(out.conversation) == len(LONG)
    row(
        "step one alone when it is enough",
        step_one and cleared_count(out.conversation) == 6,
        error or len(LONG),
    )

    out, error = run_compact(compactor, layers, 250, forget_everything)
    ok = (
        error is None
        and out is not None
        and len(out.conversation) >= 3
        and out.conversation[-3]["content"] == "q7"
        and budget_report(out)["total"] <= 250
    )
    row(
        "summarizes up to the latest question",
        ok,
        error or (out and out.conversation[0]["content"][:30]),
    )
    row(
        "pinned records are untouched",
        error is None and out is not None and out.pinned == layers.pinned,
        error or "pinned kept",
    )

    _, error = run_compact(compactor, Layers("s", ["x" * 4000], SMALL), 100, forget_everything)
    row("pinned records over the budget raise", error == "ContextOverflowError", error)
    _, error = run_compact(
        compactor,
        Layers("s", [], [{"role": "user", "content": "y" * 4000}]),
        100,
        forget_everything,
    )
    row("a latest turn over the budget raises", error == "ContextOverflowError", error)
    return rows


def clear_old_tool_results_reference(messages):
    positions = [i for i, m in enumerate(messages) if m.get("role") == "tool"]
    old = set(positions[:-2])
    marker = "[tool result cleared to save context: {} tokens]"
    return [
        {**m, "content": marker.format(estimate_tokens(m["content"]))} if i in old else dict(m)
        for i, m in enumerate(messages)
    ]


visible_results = grade_unit(clear_old_tool_results, compact)
VISIBLE_PASSED = all(r["status"] == "PASS" for r in visible_results)
for visible_row in visible_results:
    print(visible_row["status"], visible_row["case"], "->", visible_row["observed"])
print("VISIBLE_CONTRACT", "PASSED" if VISIBLE_PASSED else "NEEDS_WORK")
```

## 3. Compact Lucy's day at three budgets

Once the visible cases pass, the cell below compacts Lucy's day three times, with the `keep_numbers` summarizer:

1. at the whole day's size, where nothing needs to change;
2. at the size the day has after clearing its old tool results, where step one is enough;
3. at 400 tokens, where the summary must do the rest.

Each time it checks which of the facts are still anywhere the model can see. Then it repeats 400 tokens with the rules moved into pinned records.

Before running it, predict which facts survive each budget, and which survive 400 tokens with pinned records.

```python tags=["integration", "learner-path"]
survival = None
if VISIBLE_PASSED:
    survival = {}
    whole = budget_report(Layers(SYSTEM, [], lucy_day()))["total"]
    after_clearing = budget_report(Layers(SYSTEM, [], clear_old_tool_results(lucy_day(), 2)))[
        "total"
    ]
    print(
        f"the whole day: {whole} tokens; after clearing old tool results: {after_clearing} tokens"
    )
    plans = (
        ("whole day", [], whole),
        ("clear only", [], after_clearing),
        ("400", [], 400),
        ("400+pinned", PINNED, 400),
    )
    for label, pinned, budget in plans:
        layers = compact(Layers(SYSTEM, pinned, lucy_day()), budget, keep_numbers)
        survival[label] = {
            "budget": budget,
            "tokens": budget_report(layers)["total"],
            "kept": [fact for fact, needle, _ in QUESTIONS if survives(layers, needle)],
        }
        kept, tokens = len(survival[label]["kept"]), survival[label]["tokens"]
        print(f"{label:11} {tokens:5} tokens, {kept} of {len(QUESTIONS)} facts visible")
        for fact, _, where in QUESTIONS:
            status = "kept" if fact in survival[label]["kept"] else "LOST"
            print("    ", status, f"{fact}  ({where})")
    assert len(survival["whole day"]["kept"]) == len(QUESTIONS)
    assert "delivery A-4817 was 20 tubs" not in survival["clear only"]["kept"]
    assert "mango is never ordered from Frostline" in survival["clear only"]["kept"]
    assert "mango is never ordered from Frostline" not in survival["400"]["kept"]
    assert "mango is never ordered from Frostline" in survival["400+pinned"]["kept"]
else:
    print("COMPACTION_NOT_READY — repair clear_old_tool_results and compact, then run again.")
```

Read the lists before moving on.

- **The whole day** fits its own size, so nothing changed.
- **At the size after clearing,** step one was enough: every rule stayed. The facts that lived only in a tool result went: delivery A-4817 and the strawberry count. The agent could fetch those again.
- **At 400 tokens** the summary kept only the lines with digits in them. That included both closing times and both chocolate approvals, old and new, and none of Lucy's rules, which contain no digits.
- **With the rules pinned,** the same 400 tokens kept every rule, because pinned records are never compacted.

A summary is a guess about what will matter later. A record is the application's decision.

## 4. Save the handoff

Unit B breaks compaction on purpose. The handoff records your budgets and what survived at each.

```python tags=["handoff"]
ARTIFACT_PATH = Path("ch21-unit-a-handoff-v1.json")
artifact_status = "NOT_WRITTEN"
if survival is not None:
    handoff = {
        "unit": "ch21-a",
        "status": "COMPLETED",
        "budgets": [survival[label]["budget"] for label in ("whole day", "clear only", "400")],
        "summarizer": "keep_numbers",
        "pinned": PINNED,
        "survival": survival,
    }
    ARTIFACT_PATH.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    artifact_status = "WRITTEN"
    print(ARTIFACT_PATH)
else:
    print("HANDOFF_NOT_WRITTEN")
```

## Exit ticket

Answer three questions:

- Why does compaction clear tool results before it summarizes anything?
- Which of Lucy's facts could the agent recover after compaction without asking her, and how?
- Why does `compact` raise an error instead of returning a context a little over the budget?

```python tags=["exercise-report"]
exercise_report = {
    "unit": "ch21-a",
    "attempted": 1,
    "completed": int(VISIBLE_PASSED),
    "failed": int(not VISIBLE_PASSED),
    "skipped": 0,
    "compaction": "PASSED" if survival else "NOT_READY",
    "handoff": artifact_status,
}
print("EXERCISE_REPORT=" + json.dumps(exercise_report, sort_keys=True))
```

## Changed-constraint construction: keep only the lines that answer a question

**Allow fifteen minutes:** three to predict, eight to implement and trace, and four for a case of your own.

Cutting a long tool result by position keeps lines that may not matter. When the agent knows what it is looking for, it can keep the lines that match. `transfer_filter(text, needle, budget)` returns the lines of `text` that contain `needle`, compared case-insensitively. It keeps the **most recent** matching lines, meaning those nearest the end, within `budget` tokens by `estimate_tokens(line + "\n")`, in their original order. After them comes one final line:

```text
[kept K of M matching lines; T lines in total]
```

With no matching line, return just the final line with `K` and `M` both 0. Do not change the input.

Write your expected values before you run the table.

```python tags=["exercise", "transfer-owned"]
def transfer_filter(text, needle, budget):
    lines = text.splitlines()
    matching = [line for line in lines if needle.lower() in line.lower()]
    kept, used = [], 0
    for line in reversed(matching):
        cost = estimate_tokens(line + "\n")
        if used + cost > budget:
            break
        kept.insert(0, line)
        used += cost
    return "\n".join(
        [
            *kept,
            f"[kept {len(kept)} of {len(matching)} matching lines; {len(lines)} lines in total]",
        ]
    )
```

```python tags=["assessment", "transfer-invocation"]
SALES = "\n".join(
    [
        "10:02 | vanilla | 2 tubs",
        "10:05 | Pistachio | 1 tubs",
        "10:09 | mint | 3 tubs",
        "10:15 | pistachio | 2 tubs",
        "10:20 | pistachio | 3 tubs",
    ]
)
TRANSFER_CASES = [
    (
        "every match fits",
        [SALES, "pistachio", 100],
        "\n".join(
            [
                "10:05 | Pistachio | 1 tubs",
                "10:15 | pistachio | 2 tubs",
                "10:20 | pistachio | 3 tubs",
                "[kept 3 of 3 matching lines; 5 lines in total]",
            ]
        ),
    ),
    (
        "only the most recent fit",
        [SALES, "pistachio", 14],
        "\n".join(
            [
                "10:15 | pistachio | 2 tubs",
                "10:20 | pistachio | 3 tubs",
                "[kept 2 of 3 matching lines; 5 lines in total]",
            ]
        ),
    ),
    ("no match", [SALES, "mango", 100], "[kept 0 of 0 matching lines; 5 lines in total]"),
    (
        "a zero budget keeps none",
        [SALES, "mint", 0],
        "[kept 0 of 1 matching lines; 5 lines in total]",
    ),
]


def run_transfer(candidate, cases):
    observations = []
    for label, arguments, expected in cases:
        supplied = copy.deepcopy(arguments)
        try:
            actual = candidate(*supplied)
        except NotImplementedError:
            actual = {"unfinished": True}
        except Exception as error:
            actual = {"raises": type(error).__name__}
        passed = actual == expected and supplied == arguments
        observations.append(
            {"case": label, "expected": expected, "observed": actual, "passed": passed}
        )
        print("PASS" if passed else "NEEDS_WORK", label)
    return observations


transfer_observations = run_transfer(transfer_filter, TRANSFER_CASES)
TRANSFER_PASSED = all(r["passed"] for r in transfer_observations)
print("TRANSFER_STATUS", "PASS" if TRANSFER_PASSED else "NEEDS_WORK")
```

### Design a counterexample and retrieve the mechanism

Add one case with an expected outcome you worked out independently, and rerun the driver. Then ask which question about the sales log this filter cannot answer however large its budget, and what the agent would need instead.


## Instructor explanation and additional transfer cases

Three misconceptions come up.

**"A bigger context window means compaction is optional."** A larger window moves the budget; it does not remove it. Every token is read on every turn, and the chapter measured accuracy falling with length well before the window was full.

**"A good summary keeps what matters."** The summarizer decides what matters before anyone knows the next question. The chapter's real model kept the old closing time and dropped the new one. A rule the application must keep belongs in its records, which compaction never touches.

**"Clearing a tool result loses the fact."** It loses it from the context, not from the world. The call stays in the conversation, and the agent can make it again. That is why tool results go first, and why facts Lucy only said once must not live only in the transcript.

The filter answers "which lines mention X". It cannot answer "how many tubs of pistachio in total" when the matching lines do not fit: an aggregate needs a program that reads every line, which is the digest the chapter measured.

```python tags=["instructor-check"]
INSTRUCTOR_TRANSFER_CASES = [
    ("an empty text", ["", "vanilla", 100], "[kept 0 of 0 matching lines; 0 lines in total]"),
    (
        "case is ignored both ways",
        ["A | VANILLA\nb | vanilla", "Vanilla", 100],
        "A | VANILLA\nb | vanilla\n[kept 2 of 2 matching lines; 2 lines in total]",
    ),
]
instructor_observations = run_transfer(transfer_filter, INSTRUCTOR_TRANSFER_CASES)
assert TRANSFER_PASSED and all(r["passed"] for r in instructor_observations)
```

```python tags=["instructor-check", "core-holdout"]
empty = compact(Layers("s", [], []), 100, forget_everything)
assert empty.conversation == []
only_tools = [
    {"role": "user", "content": "q"},
    tool_message("t", {"rows": ["x"] * 200}),
    tool_message("t", {"rows": ["y"] * 200}),
    tool_message("t", {"rows": ["z"] * 200}),
]
assert cleared_count(clear_old_tool_results(only_tools, 0)) == 3
try:
    compact(Layers("s", [], only_tools), 50, forget_everything)
    holdout_ok = False
except ContextOverflowError:
    holdout_ok = True
assert holdout_ok, "a latest turn that cannot fit must raise"
print("HOLDOUT_RESULT=" + json.dumps({"status": "PASSED", "unit": "ch21-a"}, sort_keys=True))
```

## Save your evidence and explain the result

Fill in the prediction notes and your explanation before saving. Include:

- the exact observed value, and the input that caused it;
- your code's invocation point;
- one failed hypothesis;
- the strongest claim the evidence still cannot support.

This unit measures what is visible to the model, not what the model does with it. A fact in the context can still be misread; the chapter's experiment measures that on real models.

```python tags=["course-report", "retained-evidence"]
explanation_notes = {
    "causal_trace": "Explain the input, learner invocation and observed result.",
    "failed_hypothesis": "Describe a prediction the evidence changed.",
    "remaining_limit": "Name the guarantee not established by this experiment.",
}
course_submission = {
    "unit": "ch21-a",
    "planned_minutes": 90,
    "starting_evidence": globals().get("HANDOFF_ORIGIN", "INDEPENDENT_UNIT_A"),
    "prediction": prediction_notes,
    "explanation": explanation_notes,
    "core_report": exercise_report,
    "transfer": transfer_observations,
    "explanation_review": "HUMAN_REVIEW_REQUIRED",
}
submission_path = COURSE_WORK / "ch21-a-submission-v1.json"
submission_path.write_text(
    json.dumps(course_submission, indent=2, sort_keys=True), encoding="utf-8"
)
print("Saved evidence:", submission_path)
print(
    "COURSE_REPORT="
    + json.dumps(
        {
            "unit": "ch21-a",
            "transfer_passed": TRANSFER_PASSED,
            "starting_evidence": course_submission["starting_evidence"],
            "edition": "instructor",
        },
        sort_keys=True,
    )
)
```

<!-- #region tags=["profrod-community"] -->
## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
<!-- #endregion -->
