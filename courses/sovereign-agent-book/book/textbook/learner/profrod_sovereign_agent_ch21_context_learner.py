# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 21 learner file: context engineering, the budget of what the model sees.

Part A: the helpers the chapter's experiment uses to build long contexts, place facts at a depth,
shorten tool results and compact a conversation.

Part B: a context manager for Lucy's agent. It keeps three layers in a fixed order, stable first:
the system layer, the pinned records the application owns, and the conversation. It accounts for
every token against a budget, spills an oversized tool result to a file and leaves a pointer,
compacts the conversation in two steps (clear old tool results, then summarize the oldest turns),
and refuses a context it cannot fit instead of cutting it silently. Pinned records are never
compacted: a rule that must survive belongs in the application's records, not in the transcript.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

Message = dict[str, Any]

# ---------------------------------------------------------------- Part A: measuring and shortening


def estimate_tokens(text: str) -> int:
    """A rough token count: about four characters per token for English prose.

    The chapter measures how wrong this is for JSON, numbers and code. A budget built on an
    estimate needs a margin, or a count from the model's own tokenizer.
    """
    return math.ceil(len(text) / 4)


def message_tokens(message: Message, estimate: Callable[[str], int] = estimate_tokens) -> int:
    """Tokens for one chat message: its content plus a small allowance for the role markers."""
    return estimate(str(message.get("content", ""))) + 4


def place_at_depth(filler: Sequence[str], facts: Sequence[str], depth: float) -> list[str]:
    """Insert `facts`, in order, at a relative position in `filler`: 0 is the start, 1 the end."""
    if not 0 <= depth <= 1:
        raise ValueError("depth is a fraction between 0 and 1")
    at = round(depth * len(filler))
    return [*filler[:at], *facts, *filler[at:]]


def head(text: str, budget: int, estimate: Callable[[str], int] = estimate_tokens) -> str:
    """The longest prefix of whole lines that fits in `budget` tokens."""
    kept: list[str] = []
    used = 0
    for line in text.splitlines():
        cost = estimate(line + "\n")
        if used + cost > budget:
            break
        kept.append(line)
        used += cost
    return "\n".join(kept)


def head_and_tail(text: str, budget: int, estimate: Callable[[str], int] = estimate_tokens) -> str:
    """Whole lines from both ends, half the budget each, with a marker for what was left out."""
    lines = text.splitlines()
    first = head(text, budget // 2, estimate).splitlines()
    last: list[str] = []
    used = 0
    for line in reversed(lines[len(first) :]):
        cost = estimate(line + "\n")
        if used + cost > budget // 2:
            break
        last.insert(0, line)
        used += cost
    omitted = len(lines) - len(first) - len(last)
    if omitted <= 0:
        return text
    return "\n".join([*first, f"[... {omitted} lines omitted ...]", *last])


# ---------------------------------------------------------------- Part B: the context manager


class ContextOverflowError(Exception):
    """The layers that must be sent do not fit in the budget; nothing is cut silently."""


@dataclass
class Spilled:
    """What a tool result becomes when it is too large to send whole."""

    text: str
    path: Path | None
    original_tokens: int


def spill_tool_result(
    text: str,
    limit: int,
    folder: Path,
    name: str,
    estimate: Callable[[str], int] = estimate_tokens,
) -> Spilled:
    """Send a tool result whole if it fits in `limit`; otherwise save it and send a pointer.

    The pointer keeps both ends of the output and says where the whole output is, so the agent can
    read a part of it on purpose instead of losing it without knowing.
    """
    tokens = estimate(text)
    if tokens <= limit:
        return Spilled(text, None, tokens)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name}.txt"
    path.write_text(text)
    note = f"[output of {tokens} tokens saved to {path}; showing both ends]"
    shown = head_and_tail(text, max(limit - estimate(note) - 8, 0), estimate)
    return Spilled(f"{note}\n{shown}", path, tokens)


@dataclass
class Layers:
    """Everything the model will see, in the order it is sent: stable first, volatile last."""

    system: str
    pinned: list[str] = field(default_factory=list)
    conversation: list[Message] = field(default_factory=list)

    def messages(self) -> list[Message]:
        """The request's messages. The system text and pinned records never move."""
        head_text = self.system
        if self.pinned:
            head_text += "\n\nRecords Lucy's shop keeps (current):\n" + "\n".join(
                f"- {record}" for record in self.pinned
            )
        return [{"role": "system", "content": head_text}, *self.conversation]


def budget_report(
    layers: Layers, estimate: Callable[[str], int] = estimate_tokens
) -> dict[str, int]:
    """Tokens per layer, like `/context` in a coding agent."""
    pinned = sum(estimate(record) for record in layers.pinned)
    conversation = sum(message_tokens(m, estimate) for m in layers.conversation)
    system = estimate(layers.system)
    return {
        "system": system,
        "pinned": pinned,
        "conversation": conversation,
        "total": system + pinned + conversation,
    }


def clear_old_tool_results(messages: Sequence[Message], keep_last: int) -> list[Message]:
    """Replace the content of all but the last `keep_last` tool results with a short marker.

    The call that produced each result stays in the conversation, so the agent can see that it
    looked something up, and can look it up again.
    """
    tool_positions = [i for i, m in enumerate(messages) if m.get("role") == "tool"]
    old = set(tool_positions[: max(len(tool_positions) - keep_last, 0)])
    cleared: list[Message] = []
    for i, message in enumerate(messages):
        if i in old:
            size = estimate_tokens(str(message.get("content", "")))
            cleared.append(
                {**message, "content": f"[tool result cleared to save context: {size} tokens]"}
            )
        else:
            cleared.append(dict(message))
    return cleared


def compact(
    layers: Layers,
    budget: int,
    summarize: Callable[[list[Message]], str],
    keep_tool_results: int = 2,
    estimate: Callable[[str], int] = estimate_tokens,
) -> tuple[Layers, dict[str, Any]]:
    """Fit `layers` into `budget` in two steps, and report what each step did.

    1. Clear old tool results, keeping the last `keep_tool_results`.
    2. If still over, replace the oldest turns with one summary message, keeping the latest user
       message and everything after it.

    The system text and pinned records are never touched. If they alone do not fit, or the latest
    turn does not fit beside them, raise `ContextOverflowError`.
    """
    report: dict[str, Any] = {"before": budget_report(layers, estimate)["total"], "steps": []}
    fixed = Layers(layers.system, list(layers.pinned), [])
    if budget_report(fixed, estimate)["total"] > budget:
        raise ContextOverflowError("the system text and pinned records alone exceed the budget")
    current = Layers(layers.system, list(layers.pinned), [dict(m) for m in layers.conversation])
    if budget_report(current, estimate)["total"] <= budget:
        report["after"] = report["before"]
        return current, report
    current.conversation = clear_old_tool_results(current.conversation, keep_tool_results)
    report["steps"].append(
        {"step": "clear-tool-results", "total": budget_report(current, estimate)["total"]}
    )
    if budget_report(current, estimate)["total"] <= budget:
        report["after"] = report["steps"][-1]["total"]
        return current, report
    last_user = max(
        (i for i, m in enumerate(current.conversation) if m.get("role") == "user"),
        default=len(current.conversation),
    )
    recent = current.conversation[last_user:]
    older = current.conversation[:last_user]
    if not older:
        raise ContextOverflowError("the latest turn alone exceeds the budget")
    summary = {
        "role": "user",
        "content": "Summary of the earlier conversation:\n" + summarize(older),
    }
    current.conversation = [summary, *recent]
    total = budget_report(current, estimate)["total"]
    report["steps"].append({"step": "summarize", "turns": len(older), "total": total})
    if total > budget:
        raise ContextOverflowError(
            f"after compaction the context still needs {total} of {budget} tokens"
        )
    report["after"] = total
    return current, report


def tool_message(name: str, payload: Any) -> Message:
    """A tool result as the conversation carries it."""
    return {"role": "tool", "name": name, "content": json.dumps(payload, separators=(",", ":"))}
