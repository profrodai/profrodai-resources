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
    instructor: false
    lesson_id: context
    planned_minutes: 90
    resource_id: profrod-sovereign-agent-ch21-b-context-repair-transfer-exercise
    self_contained_runtime: true
    source_basis: chapter-21-manuscript
    source_unit: ch21-b
    source_url: https://github.com/profrodai/sovereign-agent
    unit: ch21-b
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

# Chapter 21, Unit B: Break the context, then repair and transfer it

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Student edition · 90 minutes of dedicated work · 2026-09-29**

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/profrodai/profrodai-resources/blob/main/courses/sovereign-agent-book/book/exercises/ch21/profrod-sovereign-agent-ch21-b-context-repair-transfer-exercise.ipynb) Runs on Google Colab or any Python 3.12+ Jupyter kernel. It needs no packages beyond the standard library, no model and no network. The model outputs it studies were recorded in the chapter's experiment.

This is the second of Chapter 21's two practical units, each a complete ninety-minute session. Unit A built compaction and pinned records. This unit breaks the context three ways and repairs each:

- **a summary a real model wrote**, which kept some of Lucy's facts, dropped others and changed one;
- **a layout that defeats the prefix cache**, so every turn pays to read the whole prompt again;
- **an estimate that undercounts**, so a context that "fits" does not.

You can start from your own Unit A handoff or from a supplied reference. By the end you should be able to:

1. Check a model-written summary against the facts it had to keep, and name what it lost and what it changed.
2. Implement `cached_prefix_tokens`, which measures how much of a request a prefix cache can reuse.
3. Implement `stable_first`, which orders a request so the volatile part comes last.
4. Budget with a tokenizer's measured ratios instead of a flat estimate.

| Minutes | Dedicated work | Saved evidence |
| --- | --- | --- |
| 0–10 | Predict what a model keeps when it summarizes Lucy's day | Written prediction |
| 10–30 | Check the real summary; repair with pinned records | Fact table |
| 30–55 | Construct `cached_prefix_tokens` and `stable_first`; pass the visible cases | Learner code and grade table |
| 55–70 | Replay ten turns in both layouts and compare with the measured prefill | Cache table |
| 70–85 | Changed-constraint task: a worst-case token count | Transfer results |
| 85–90 | Explain records, layout and margins; save evidence | Retained submission |

These times are planning estimates, not measured completion times. Run All only checks that the notebook executes; the unfinished student functions deliberately report NEEDS_WORK. Keep your first attempt before opening the worked edition.


## Run the self-contained setup

The unit needs only Python's standard library. The collapsed cell below creates your work folder and defines the supplied parts of the unit:

- **Unit A's parts:** `estimate_tokens`, `message_tokens`, `Layers`, `budget_report`, `clear_old_tool_results` and `compact`, as the worked Unit A builds them.
- **Lucy's day:** `lucy_day()`, the pinned records `PINNED`, and `survives(layers, needle)`.
- **Recorded measurements** from the chapter's experiment with qwen2.5:1.5b: `REAL_SUMMARY`, the summary the model wrote of the older part of Lucy's day; `MEASURED`, token counts by kind of text; and `MEASURED_PREFILL`, the median prefill per turn in each layout.

Run setup on every fresh kernel. Your saved work lives in `practical-work/ch21-b`.

<details><summary>Supplied setup, Unit A's parts and the recorded measurements</summary>

```python jupyter={"source_hidden": true} tags=["setup", "embedded-runtime"]
import base64
import json
import math
import os
import random
import sys
import tempfile
import zlib
from dataclasses import dataclass, field
from pathlib import Path

minimum_python = (3, 12)
if sys.version_info[:2] < minimum_python:
    raise RuntimeError("This unit needs Python 3.12 or newer; Google Colab runs Python 3.13.")

if "COURSE_START_DIRECTORY" not in globals():
    COURSE_START_DIRECTORY = Path.cwd()
    COURSE_ROOT = Path(tempfile.mkdtemp(prefix="ch21-course-"))


def estimate_tokens(text):
    return math.ceil(len(text) / 4)


def message_tokens(message):
    return estimate_tokens(str(message.get("content", ""))) + 4


class ContextOverflowError(Exception):
    """What must be sent does not fit in the budget; nothing is cut silently."""


@dataclass
class Layers:
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


def tool_message(name, payload):
    return {"role": "tool", "name": name, "content": json.dumps(payload, separators=(",", ":"))}


def clear_old_tool_results(messages, keep_last):
    positions = [i for i, m in enumerate(messages) if m.get("role") == "tool"]
    old = set(positions[: max(len(positions) - keep_last, 0)])
    marker = "[tool result cleared to save context: {} tokens]"
    return [
        {**m, "content": marker.format(estimate_tokens(str(m["content"])))} if i in old else dict(m)
        for i, m in enumerate(messages)
    ]


def compact(layers, budget, summarize):
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
    current.conversation = [
        {"role": "user", "content": "Summary of the earlier conversation:\n" + summarize(older)},
        *recent,
    ]
    if budget_report(current)["total"] > budget:
        raise ContextOverflowError("the compacted context still exceeds the budget")
    return current


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


def survives(layers, needle):
    return any(needle.lower() in str(m["content"]).lower() for m in layers.messages())


REAL_SUMMARY = (
    "Lucy's Scoops has been operating since morning, with a focus on selling "
    "chocolate tubs and checking the freezer regularly. The conversation incl"
    "udes updates on orders from Frostline (mango), changes in closing time t"
    "o 6 pm, and adjustments for vanilla sales at Polar Dairy. Sales figures "
    "are provided daily, including updates after changing plans to close earl"
    "ier at 7 pm. The assistant also checks the freezer multiple times throug"
    "hout the day and records deliveries as they come in."
)
MEASURED = [
    {"kind": "prose", "chars": 1775, "estimate": 444, "actual": 349},
    {"kind": "json", "chars": 2573, "estimate": 644, "actual": 1048},
    {"kind": "numbers", "chars": 2016, "estimate": 504, "actual": 1187},
    {"kind": "python", "chars": 2400, "estimate": 600, "actual": 540},
]
MEASURED_PREFILL = {"volatile-first": 963, "stable-first": 92.1}

COURSE_WORK = COURSE_START_DIRECTORY / "practical-work" / "ch21-b"
COURSE_WORK.mkdir(parents=True, exist_ok=True)
os.chdir(COURSE_WORK)
print("Python", sys.version.split()[0])
print("Save your work here:", COURSE_WORK)
```

</details>


## Commit to a prediction before the failures

In the chapter's experiment, qwen2.5:1.5b was asked to summarize the older part of Lucy's day: "keep every rule, decision, name and number Lucy stated; where she changed something, keep only the latest value." Before you read its summary, write down:

- which of Lucy's rules you expect it to keep;
- whether it keeps the closing time and the chocolate approval at their changed values;
- whether it can introduce something that was never said.

```python tags=["prediction", "learner-notes"]
prediction_notes = {
    "prediction": "Write which facts the summary keeps, and whether it keeps the latest values.",
    "reason": "Name the rule behind that prediction.",
    "falsifier": "Name an observation that would prove the explanation wrong.",
    "revision": "After execution, explain what changed in your understanding.",
}
```

### Start from Unit A's handoff

This unit uses the budgets and pinned records you tested in Unit A. To use your own, replace `None` with the path to your `practical-work/ch21-a/ch21-unit-a-handoff-v1.json`. Leave it as `None` to start from the supplied reference, which is the handoff the worked Unit A produces. Your submission records which you chose.

```python tags=["setup", "handoff-selection"]
LEARNER_HANDOFF = None
```

```python tags=["setup", "independent-reference-start"]
import shutil

COURSE_INPUT = COURSE_WORK / "ch21-unit-a-handoff-v1.json"
if LEARNER_HANDOFF is not None:
    learner_input = Path(LEARNER_HANDOFF).expanduser().resolve()
    if not learner_input.is_file():
        raise FileNotFoundError("The selected learner handoff does not exist")
    if learner_input != COURSE_INPUT.resolve():
        shutil.copy2(learner_input, COURSE_INPUT)
    HANDOFF_ORIGIN = "LEARNER_SELECTED"
else:
    reference_encoded = (
        "c-q}m%Wm5+5WM><7QD1Y?ZC1V$IUIM(^J|6h|x<C1hllV2vej$QZkev|K6n@l<l~O0x3}BVvGCY?952d0|2%vk~K"
        "QZF5nj(0VdP=Y*;@<llioHIvtPc|K1;1E|kI~l(S`uU{jrguy9?()dvfAvDUdgVNEmpfh8KyCZXSqtF?wlqciwsv"
        "~^M_424Ub@CsZvFqYb)1@7P+@(e!4DK%r#bk8XCDRf@uxzQyi7Z9C+D^?ctBgCnWwd4*D?mL(iP5L=Mxe`)xze|m"
        "`tGT5)1{PeHsz*yWQ{>X6Ae7B9cG~#H1y>wyj1x~MEU;!BcZDaJeZBd9dwsRMTCgTjWEnT&35`!~5c3CBWGghb%b"
        "QY^TvGPAxtGKUhoB!tC_e0h8_ZphsE&9tg<69X8G4kSQa0Sl2eNp}rLSt)+%2r-5o<Lna*_$r!CI3_t426S^s%=1"
        "KEQE$gUWCJWm<<`hGCV@!B2m?QRfpfoZ=boVr*PS_*HMcPRd||z3tzMow7AhtTQ6z&^w1b{=qkIMt5{J+v7WyNKm"
        "wr)lt6t7ydmGZk^#<da+Ce*6DZyTkh{Y=I?*53lY61%r?~$fxdo6b?HCJ?@^Zor66z>T#ioX(RnS)Wc+I2e<YvRq"
        "mggWO2`T&yeh=cBpPuxcp3Z#_qq#4"
    )
    COURSE_INPUT.write_bytes(zlib.decompress(base64.b85decode(reference_encoded)))
    HANDOFF_ORIGIN = "SUPPLIED_REFERENCE"
print("Starting evidence:", HANDOFF_ORIGIN)
```

```python tags=["setup", "handoff-consumer"]
handoff = json.loads(COURSE_INPUT.read_text(encoding="utf-8"))
completed = handoff.get("status") == "COMPLETED" and handoff.get("unit") == "ch21-a"
handoff_status = "VERIFIED" if completed else "INVALID"
TIGHT_BUDGET = min(handoff["budgets"])
HANDOFF_PINNED = handoff["pinned"]
print(
    "UNIT_A_HANDOFF",
    handoff_status,
    "| tightest budget",
    TIGHT_BUDGET,
    "| pinned records",
    len(HANDOFF_PINNED),
)
```

## 1. Check a summary a model wrote

The facts below are the ones the summary had to keep. For each, the check looks for the current value and for the value Lucy later replaced. A summary can keep a fact, lose it, or keep the old value as if it were current.

```python tags=["foundation", "worked-example"]
print(REAL_SUMMARY)
print("-" * 60)
FACTS = [
    ("the shop's name", "Lucy's Scoops", None),
    ("mango is never ordered from Frostline", "mango", None),
    ("closing time", "7 pm", "6 pm"),
    ("chocolate approved", "15", "12"),
    ("vanilla supplier", "Polar Dairy", None),
    ("health inspector", "Dana Ortiz", None),
]
summary_check = {}
for fact, current, old in FACTS:
    text = REAL_SUMMARY.lower()
    has_current = current.lower() in text
    has_old = old is not None and old.lower() in text
    status = (
        "kept"
        if has_current and not has_old
        else "kept, with the old value too"
        if has_current
        else "OLD VALUE"
        if has_old
        else "LOST"
    )
    summary_check[fact] = status
    print(f"{fact:40} {status}")
```

Read what the model wrote, not only the table. The table says the mango rule was kept, because the word "mango" is there. The summary says "updates on orders from Frostline (mango)": it kept the words and turned the rule into its opposite. A keyword check cannot see that, and neither can compaction. A summary is text the model produced, and it can state things that were never said. It is also the only memory the compacted conversation keeps of the older turns. Now repair it the way Unit A did: move the rules into pinned records, which compaction never touches, and compact the same day with the same real summary.

```python tags=["foundation", "worked-example"]
real_summarizer = lambda older: REAL_SUMMARY  # noqa: E731
SUMMARY_BUDGET = TIGHT_BUDGET + estimate_tokens(REAL_SUMMARY)
without = compact(Layers(SYSTEM, [], lucy_day()), SUMMARY_BUDGET, real_summarizer)
with_pinned = compact(
    Layers(SYSTEM, HANDOFF_PINNED, lucy_day()), SUMMARY_BUDGET + 120, real_summarizer
)
for fact, current, _ in FACTS:
    plain = "visible" if survives(without, current) else "missing"
    pinned = "visible" if survives(with_pinned, current) else "missing"
    print(f"{fact:40} without pinned: {plain:8} with pinned: {pinned}")
```

With pinned records, every rule is visible whatever the summary says. That does not make the summary right: where it disagrees with a record, the model now sees both. The record should win, and the system text can say so, but the cleaner fix is to keep facts that have a record out of the summary's job altogether.

## 2. Construct `cached_prefix_tokens`

A prefix cache reuses the work done on the start of the previous request, up to the first difference. Everything after the first difference is read again. At the level of messages, `cached_prefix_tokens(previous, current)` returns the sum of `message_tokens` over the leading messages of `current` that are identical, in role and content, to the messages at the same positions in `previous`. It stops at the first difference. Do not change the inputs.

The starter assumes the cache reuses every message the two requests have in common, anywhere.

```python tags=["exercise", "learner-owned", "ch21-cached"]
def cached_prefix_tokens(previous, current):
    """Tokens at the start of `current` identical to `previous`, up to the first difference."""
    return sum(message_tokens(m) for m in current if m in previous)
```

## 3. Construct `stable_first`

`stable_first(stable, snapshot, history, question)` builds one request so that the prefix cache can do its job. It returns a new list:

1. a system message whose content is exactly `stable`;
2. every message of `history`, unchanged and in order;
3. one user message whose content is `snapshot + "\n" + question`.

The snapshot, meaning the time and the freezer readings, changes every turn, so it goes last. Do not change `history`.

The starter puts the snapshot at the top of the system message, where it changes the first message of every request.

```python tags=["exercise", "learner-owned", "ch21-stable"]
def stable_first(stable, snapshot, history, question):
    """One request: stable system text, then history, then the volatile snapshot and question."""
    return [
        {"role": "system", "content": snapshot + "\n\n" + stable},
        *history,
        {"role": "user", "content": question},
    ]
```

<details><summary>Hint 1 — "up to the first difference"</summary>

Walk both lists in step with `zip`. The first position where role or content differ ends the reuse, even if later messages match again. The cache matches a prefix, not a set.

</details>

<details><summary>Hint 2 — what changes every turn</summary>

The rules and the tool list change almost never. The conversation only grows at its end. The time and the freezer snapshot change every turn. Put them last, and every earlier message stays the same from one turn to the next.

</details>

```python tags=["assessment", "visible"]
import copy

A = {"role": "system", "content": "rules " * 50}
B = {"role": "user", "content": "q1"}
C = {"role": "assistant", "content": "a1"}
D = {"role": "user", "content": "q2"}


def grade_unit(cached, ordered):
    rows = []

    def row(case, passed, observed):
        rows.append({"case": case, "observed": observed, "status": "PASS" if passed else "FAIL"})

    previous, current = [A, B, C], [A, B, C, D]
    saved = copy.deepcopy((previous, current))
    got = cached(previous, current)
    row(
        "an identical start is reused",
        got == sum(map(message_tokens, [A, B, C])) and (previous, current) == saved,
        got,
    )
    changed = {"role": "system", "content": "10:05 " + A["content"]}
    got = cached([A, B, C], [changed, B, C, D])
    row("a changed first message reuses nothing", got == 0, got)
    got = cached([A, B, C], [A, {"role": "user", "content": "other"}, C, D])
    row("reuse stops at the first difference", got == message_tokens(A), got)
    got = cached([], [A])
    row("nothing before, nothing reused", got == 0, got)

    history = [B, C]
    saved = copy.deepcopy(history)
    request = ordered("RULES", "10:05 vanilla 12", history, "Anything low?")
    row(
        "stable text is the whole system message",
        request[0] == {"role": "system", "content": "RULES"},
        request[0]["content"][:20],
    )
    row("history follows unchanged", request[1:3] == [B, C] and history == saved, len(request))
    row(
        "snapshot and question come last",
        request[-1] == {"role": "user", "content": "10:05 vanilla 12\nAnything low?"},
        request[-1]["content"][:30],
    )
    return rows


visible_results = grade_unit(cached_prefix_tokens, stable_first)
VISIBLE_PASSED = all(r["status"] == "PASS" for r in visible_results)
for visible_row in visible_results:
    print(visible_row["status"], visible_row["case"], "->", visible_row["observed"])
print("VISIBLE_CONTRACT", "PASSED" if VISIBLE_PASSED else "NEEDS_WORK")
```

## 4. Replay ten turns in both layouts

Once the visible cases pass, the cell below replays ten turns of Lucy's day twice. The first time, the snapshot sits at the top of the system message. The second time it sits in the last message, via `stable_first`. For each turn it counts the tokens a prefix cache could reuse from the previous request. Then it prints the prefill the chapter measured on qwen2.5:1.5b for the same two layouts.

Predict the reuse in each layout before running it.

```python tags=["integration", "learner-path"]
replay = None
if VISIBLE_PASSED:
    stable = "You are the assistant for Lucy's ice cream shop.\n" + "\n".join(
        f"Rule {i}: confirm every order with Lucy before it is placed." for i in range(40)
    )
    rng = random.Random(3)
    snapshots = [
        f"Current time 10:{t:02d}. Freezer: "
        + ", ".join(f"{f} {rng.randint(0, 40)}" for f in FLAVORS)
        for t in range(10)
    ]
    replay = {}
    for layout in ("volatile-first", "stable-first"):
        history, previous, reused = [], [], []
        for turn in range(10):
            question = f"Question {turn}: is any flavor below 5 tubs?"
            if layout == "volatile-first":
                request = [
                    {"role": "system", "content": snapshots[turn] + "\n\n" + stable},
                    *history,
                    {"role": "user", "content": question},
                ]
            else:
                request = stable_first(stable, snapshots[turn], history, question)
            total = sum(map(message_tokens, request))
            reused.append(round(cached_prefix_tokens(previous, request) / total, 2))
            history += [request[-1], {"role": "assistant", "content": "Checked."}]
            previous = request
        replay[layout] = reused
        print(f"{layout:15} share of each request reusable: {reused}")
    print("measured median prefill per turn after the first (ms):", MEASURED_PREFILL)
    assert all(share == 0 for share in replay["volatile-first"])
    assert all(share > 0.8 for share in replay["stable-first"][1:])
else:
    print("REPLAY_NOT_READY — repair cached_prefix_tokens and stable_first, then run again.")
```

With the snapshot first, nothing is reusable on any turn, because the first message changes every time. With the snapshot last, almost every token of each request was already read on the previous turn. The measured prefill shows what that costs on a real model.

### An estimate that undercounts

Unit A's budgets counted four characters per token. The recorded measurements show how far that is from a real tokenizer, by kind of text. A budget of 4,096 estimated tokens, filled with the numbers-heavy text a sales log contains, needs this many real tokens:

```python tags=["foundation", "worked-example"]
for row in MEASURED:
    ratio = row["chars"] / row["actual"]
    real = math.ceil(4096 * 4 / ratio)
    print(f"{row['kind']:8} {ratio:.2f} chars per token: 4,096 estimated = about {real:,} real")
```

A context that fits by the estimate can overflow the model's window. The chapter measured what one model server does then: it cut the prompt silently and answered from what was left. Budget with the ratio of the text you actually send, or with the worst one, and keep a margin.

```python tags=["exercise-report"]
exercise_report = {
    "unit": "ch21-b",
    "attempted": 1,
    "completed": int(VISIBLE_PASSED),
    "failed": int(not VISIBLE_PASSED),
    "skipped": 0,
    "replay": "PASSED" if replay else "NOT_READY",
    "handoff": handoff_status,
    "summary_check": summary_check,
}
print("EXERCISE_REPORT=" + json.dumps(exercise_report, sort_keys=True))
```

## Changed-constraint construction: a worst-case token count

**Allow fifteen minutes:** three to predict, eight to implement and trace, and four for a case of your own.

`worst_case_tokens(text, measured)` counts `text` pessimistically. `measured` is a list of rows like `MEASURED`, each with `chars` and `actual`. Divide the length of `text` by the **smallest** ratio of `chars / actual` among the rows, and round up with `math.ceil`. With no rows, fall back to one character per token, which is `len(text)`. Do not change the inputs.

Write your expected values before you run the table.

```python tags=["exercise", "transfer-owned"]
def worst_case_tokens(text, measured):
    raise NotImplementedError(
        "Divide by the smallest measured characters-per-token ratio, rounding up"
    )
```

```python tags=["assessment", "transfer-invocation"]
ROWS = [
    {"kind": "prose", "chars": 500, "actual": 100},
    {"kind": "numbers", "chars": 300, "actual": 200},
]
TRANSFER_CASES = [
    ("the smallest ratio decides", ["x" * 30, ROWS], 20),
    ("rounds up", ["x" * 31, ROWS], 21),
    ("one row", ["x" * 10, ROWS[:1]], 2),
    ("no rows: one character per token", ["x" * 7, []], 7),
    ("empty text", ["", ROWS], 0),
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


transfer_observations = run_transfer(worst_case_tokens, TRANSFER_CASES)
TRANSFER_PASSED = all(r["passed"] for r in transfer_observations)
print("TRANSFER_STATUS", "PASS" if TRANSFER_PASSED else "NEEDS_WORK")
```

### Design a counterexample and retrieve the mechanism

Add one case with an expected outcome you worked out independently, and rerun the driver. Then say what a worst-case count costs: for Lucy's prose, how much of the budget would it leave unused?


## Save your evidence and explain the result

Fill in the prediction notes and your explanation before saving. Include:

- the exact observed value, and the input that caused it;
- your code's invocation point;
- one failed hypothesis;
- the strongest claim the evidence still cannot support.

The cache replay counts reusable messages; it does not time a model. The measured prefill comes from one model on one machine. Real servers cache at the token level and evict caches over time, so the share reused is an upper bound.

```python tags=["course-report", "retained-evidence"]
explanation_notes = {
    "causal_trace": "Explain the input, learner invocation and observed result.",
    "failed_hypothesis": "Describe a prediction the evidence changed.",
    "remaining_limit": "Name the guarantee not established by this experiment.",
}
course_submission = {
    "unit": "ch21-b",
    "planned_minutes": 90,
    "starting_evidence": HANDOFF_ORIGIN,
    "prediction": prediction_notes,
    "explanation": explanation_notes,
    "core_report": exercise_report,
    "transfer": transfer_observations,
    "explanation_review": "HUMAN_REVIEW_REQUIRED",
}
submission_path = COURSE_WORK / "ch21-b-submission-v1.json"
submission_path.write_text(
    json.dumps(course_submission, indent=2, sort_keys=True), encoding="utf-8"
)
print("Saved evidence:", submission_path)
print(
    "COURSE_REPORT="
    + json.dumps(
        {
            "unit": "ch21-b",
            "transfer_passed": TRANSFER_PASSED,
            "starting_evidence": course_submission["starting_evidence"],
            "edition": "student",
        },
        sort_keys=True,
    )
)
```

<!-- #region tags=["profrod-community"] -->
## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
<!-- #endregion -->
