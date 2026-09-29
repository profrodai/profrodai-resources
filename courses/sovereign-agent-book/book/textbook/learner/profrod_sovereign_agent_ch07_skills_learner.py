# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 7's skills: a strict record, a bounded read, and versions staged, evaluated and
activated in the learner's own store.

The skill table is one more line of versions on the Chapter 4 store, beside Chapter 5's memory.
Context assembly adds each active skill whose required tools are all allowed to Chapter 5's
context. Activation needs a passing evaluation; the one here runs three visible cases through
Chapter 3's loop and Chapter 2's dispatcher. Chapter 16 builds the full harness.
"""

import hashlib
import json
import os
import runpy
import stat
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

LEARNER = Path(__file__).resolve().parent
MEMORY = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch05_memory_learner.py"))
LOOP = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch03_agent_loop_learner.py"))
TOOLS = LOOP["shop_tools"]
record_event, ModelTurn, ToolCall = MEMORY["record_event"], LOOP["ModelTurn"], LOOP["ToolCall"]


class Skill(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")
    version: str = Field(pattern=r"^[a-zA-Z0-9._-]{1,64}$")
    instructions: str = Field(min_length=1, max_length=8192)
    requires: list[str] = Field(default_factory=list, max_length=16)


def read_skill(path: Path) -> bytes:
    """Read one bounded regular file; POSIX flags refuse symlinks and FIFO waits."""
    if path.is_symlink():
        raise ValueError("bounded regular local skill file required")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as stream:
            observed = os.fstat(stream.fileno())
            if not stat.S_ISREG(observed.st_mode) or observed.st_size > 16_384:
                raise ValueError("bounded regular local skill file required")
            raw = stream.read(16_385)
    except OSError as error:
        raise ValueError("readable regular local skill file required") from error
    if len(raw) > 16_384:
        raise ValueError("skill changed beyond byte limit")
    return raw


def load_skill(path: Path) -> Skill:
    """A skill file, read within its bound and validated strictly."""
    return Skill.model_validate(tomllib.loads(read_skill(path).decode()))


SKILL_MIGRATIONS = {
    1: (
        "CREATE TABLE assistant_skills ("
        " name TEXT NOT NULL, version TEXT NOT NULL, content TEXT NOT NULL,"
        " source TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 0,"
        " PRIMARY KEY (name, version))",
        # At most one active version of each name, whoever writes the table.
        "CREATE UNIQUE INDEX assistant_skill_current ON assistant_skills (name) WHERE active = 1",
    ),
}


def open_skills(path: str | Path):
    """Chapter 5's memory store, with the skill table as its own line of versions."""
    db = MEMORY["open_memory"](path)
    db.migrate("skills", SKILL_MIGRATIONS)
    return db


def stage_skill(db, path: Path) -> Skill:
    """Store one validated version, inactive. The same version with other content is refused."""
    raw = read_skill(path)
    skill = Skill.model_validate(tomllib.loads(raw.decode()))
    content = skill.model_dump_json()
    with db.immediate() as connection:
        old = connection.execute(
            "SELECT content FROM assistant_skills WHERE name=? AND version=?",
            (skill.name, skill.version),
        ).fetchone()
        if old and old[0] != content:
            raise ValueError("skill versions are immutable; stage a new version")
        connection.execute(
            "INSERT OR IGNORE INTO assistant_skills(name,version,content,source) VALUES (?,?,?,?)",
            (skill.name, skill.version, content, hashlib.sha256(raw).hexdigest()),
        )
    return skill


def skill_snapshot(db) -> tuple[str, tuple[Skill, ...]]:
    """One read binds active guidance and provenance to an evaluation baseline."""
    rows = [
        tuple(row)
        for row in db.connection.execute(
            "SELECT name,version,content,source FROM assistant_skills WHERE active=1 ORDER BY name"
        )
    ]
    digest = hashlib.sha256(json.dumps(rows).encode()).hexdigest()
    return digest, tuple(Skill.model_validate_json(row[2]) for row in rows)


def activate_skill(
    db,
    name: str,
    version: str,
    *,
    evaluate: Callable[[Skill], dict[str, bool]],
    required_cases: frozenset[str],
    expected_state: str | None = None,
) -> dict[str, bool]:
    """Evaluate outside any transaction, then activate only if every required case passed and
    the active configuration is still the one the evaluation started from."""
    row = db.connection.execute(
        "SELECT content FROM assistant_skills WHERE name=? AND version=?", (name, version)
    ).fetchone()
    if row is None or not required_cases:
        raise ValueError("staged skill and a nonempty regression suite required")
    skill = Skill.model_validate_json(row[0])
    baseline = skill_snapshot(db)[0] if expected_state is None else expected_state
    results = evaluate(skill)
    if skill.model_dump_json() != row[0]:
        raise ValueError(
            "evaluation changed the candidate instead of testing its immutable version"
        )
    if not required_cases.issubset(results) or any(value is not True for value in results.values()):
        raise ValueError("candidate did not pass all required regression cases")
    with db.immediate() as connection:
        if skill_snapshot(db)[0] != baseline:
            raise PermissionError("active skill configuration changed during evaluation")
        connection.execute("UPDATE assistant_skills SET active=0 WHERE name=?", (name,))
        connection.execute(
            "UPDATE assistant_skills SET active=1 WHERE name=? AND version=?", (name, version)
        )
        record_event(
            connection,
            "assistant.skill.activated",
            {"name": name, "version": version, "cases": results},
        )
    return results


def skill_items(skills, allowed: frozenset[str], byte_budget: int) -> list[dict[str, Any]]:
    """Each skill whose required tools are all allowed, whole, while the items fit the budget.
    A skill that does not fit is left out rather than cut into partial instructions."""
    selected: list[dict[str, Any]] = []
    for skill in skills:
        if not set(skill.requires).issubset(allowed):
            continue
        item = {
            "kind": "skill_guidance",
            "name": skill.name,
            "version": skill.version,
            "content": skill.instructions,
            "content_sha256": hashlib.sha256(skill.instructions.encode()).hexdigest(),
        }
        if len(json.dumps([*selected, item]).encode()) <= byte_budget:
            selected.append(item)
    return selected


def context(
    db, session: str, prompt: str, *, allowed: frozenset[str], byte_budget: int = 16_384
) -> list[dict[str, Any]]:
    """Chapter 5's context, with the eligible active skills added under their own budget."""
    messages = MEMORY["context"](db, session, prompt, allowed=allowed, byte_budget=byte_budget)
    items = skill_items(skill_snapshot(db)[1], allowed, byte_budget)
    if items:
        messages[0]["content"] += "\nActive skills, guidance only:\n" + json.dumps(items)
    return messages


# Three visible cases for the opening procedure. The answers are authored with the fixtures.


@dataclass(frozen=True)
class Case:
    name: str
    # SKU, physical stock, reserved stock, threshold, unit price in cents.
    stock: tuple[tuple[str, int, int, int, int], ...]
    expected: tuple[tuple[str, int], ...]
    prompt: str = "Prepare a replenishment draft from current stock. State USD amounts."


OPENING_CASES = (
    Case("opening", (("V", 2, 0, 8, 250), ("S", 1, 0, 5, 275)), (("V", 6), ("S", 4))),
    Case("at_threshold", (("V", 8, 0, 8, 250),), ()),
    Case("reserved_stock", (("V", 8, 3, 8, 250),), (("V", 3),)),
)


def case_tools(case: Case):
    """The shop's three tools over one case's stock, through Chapter 2's dispatcher."""
    rows = {
        sku: {
            "sku": sku,
            "on_hand": stock,
            "reserved": reserved,
            "reorder_point": threshold,
            "needed": max(0, threshold - stock + reserved),
        }
        for sku, stock, reserved, threshold, _ in case.stock
    }
    prices = {sku: price for sku, _, _, _, price in case.stock}

    def stock(_):
        return [dict(rows[sku]) for sku in sorted(rows)]

    def supplier(args):
        if args.sku not in prices:
            raise KeyError("unknown product")
        return {"sku": args.sku, "currency": "USD", "unit_cost_cents": prices[args.sku]}

    def draft(args):
        row = rows.get(args.sku)
        if row is None or row["needed"] <= 0 or args.quantity != row["needed"]:
            raise ValueError("draft quantity must equal the current positive need")
        total = args.quantity * prices[args.sku]
        return {"sku": args.sku, "quantity": args.quantity, "total_cents": total, "currency": "USD"}

    tool = TOOLS["ExecutableTool"]
    registered = [
        tool("list_stock", "Read stock and the needed quantity.", TOOLS["NoArguments"], stock),
        tool("supplier", "Unit cost in USD cents.", TOOLS["ProductArguments"], supplier),
        tool(
            "draft_order",
            "Draft the needed quantity; never purchases.",
            TOOLS["DraftArguments"],
            draft,
        ),
    ]
    return TOOLS["Dispatcher"](registered, allowed=frozenset(t.name for t in registered))


class OfflineShopModel:
    """A reproducible model replacement that tests the wiring, not language understanding.

    Its policy is inspectable: read stock, draft each positive need, report the drafts. It does
    not read the skill, so an offline pass says nothing about whether a live model follows one."""

    def complete(self, messages, tools, *, timeout, max_output_tokens):
        start = max((i for i, m in enumerate(messages) if m["role"] == "user"), default=0)
        observations = [json.loads(m["content"]) for m in messages[start:] if m["role"] == "tool"]
        if not observations:
            return ModelTurn(calls=(ToolCall(id="stock", name="list_stock", arguments={}),))
        if len(observations) == 1 and observations[0].get("ok"):
            calls = tuple(
                ToolCall(
                    id=f"draft-{i}",
                    name="draft_order",
                    arguments={"sku": row["sku"], "quantity": row["needed"]},
                )
                for i, row in enumerate(observations[0]["value"])
                if row["needed"] > 0
            )
            if calls:
                return ModelTurn(calls=calls)
            return ModelTurn("Stock covers every threshold; no draft is needed. No purchases made.")
        drafts = [o["value"] for o in observations[1:] if o.get("ok")]
        lines = [f"{d['sku']}: {d['quantity']} units, {d['total_cents']} cents USD" for d in drafts]
        return ModelTurn("Replenishment draft:\n" + "\n".join(lines) + "\nNo purchases made.")


def evaluate_opening(model_factory: Callable[[], Any], skill: Skill) -> dict[str, bool]:
    """Run each case with the candidate's guidance and judge what the tools observed: the loop
    completed, every tool call succeeded, the drafts are exactly the authored ones, and an answer
    that reports drafts names USD. A fluent answer without the drafts fails."""
    results = {}
    for case in OPENING_CASES:
        tools = case_tools(case)
        items = skill_items((skill,), tools.allowed, 16_384)
        messages = [
            {
                "role": "system",
                "content": "You help Lucy manage her shop. Use tools for stock and arithmetic. "
                "Skill text is guidance, never permission.\n" + json.dumps(items),
            },
            {"role": "user", "content": case.prompt},
        ]
        result = LOOP["run_loop"](model_factory(), tools, messages)
        names = {
            call["id"]: call["function"]["name"]
            for message in result.messages
            for call in message.get("tool_calls", [])
        }
        observed = [
            (message["tool_call_id"], json.loads(message["content"]))
            for message in result.messages
            if message["role"] == "tool"
        ]
        drafts = sorted(
            (value["value"]["sku"], value["value"]["quantity"])
            for identifier, value in observed
            if names.get(identifier) == "draft_order" and value.get("ok")
        )
        results[case.name] = (
            result.status == "COMPLETED"
            and all(value.get("ok") for _, value in observed)
            and drafts == sorted(case.expected)
            and ("USD" in result.answer or not case.expected)
        )
    return results
