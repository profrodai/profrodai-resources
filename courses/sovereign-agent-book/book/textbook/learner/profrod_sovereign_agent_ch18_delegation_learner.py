# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 18 learner file: when a second agent pays, and one bounded delegation.

Part A computes the conditions with the standard library only: Amdahl's law for the speedup of
partly parallel work, the success of a task that needs every subagent to be right, the accuracy
of a majority vote over independent answers, and how many tokens a delegation sends compared
with one agent doing the work. Chapter 18 derives each and measures them.

Part B builds the one delegation this shop has, on earlier chapters' code: Chapter 13's leased,
generation-fenced work, Chapter 3's loop, wrapped rather than changed, and Chapter 2's strict
tools. A child gets one immutable inquiry, a deadline and a model allowance billed to its
parent's account, and no tool that reserves stock, buys or delegates again.
"""

from __future__ import annotations

import json
import math
import runpy
import time
import uuid
from collections.abc import Callable, Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any

from pydantic import Field


def amdahl_speedup(parallel_fraction: float, workers: int) -> float:
    """Speedup when a fraction f of the work splits across n workers: 1 / ((1 - f) + f / n)."""
    if not 0 <= parallel_fraction <= 1 or workers < 1:
        raise ValueError("need 0 <= f <= 1 and at least one worker")
    return 1 / ((1 - parallel_fraction) + parallel_fraction / workers)


def all_correct(accuracies: Sequence[float]) -> float:
    """Chance that every one of several independent subtasks is right: the product."""
    return math.prod(accuracies)


def majority_accuracy(p: float, voters: int) -> float:
    """Chance that more than half of `voters` independent answers, each right with p, are right."""
    if voters < 1 or voters % 2 == 0:
        raise ValueError("use an odd number of voters, so there are no ties")
    return sum(
        math.comb(voters, k) * p**k * (1 - p) ** (voters - k)
        for k in range(voters // 2 + 1, voters + 1)
    )


def delegation_tokens(shared: int, own: Sequence[int], coordinator: int) -> dict[str, int]:
    """Input tokens when each of several subagents is sent the shared context plus its own part,
    and a coordinator reads their results, against one agent reading everything once."""
    delegated = sum(shared + part for part in own) + coordinator
    single = shared + sum(own)
    return {"delegated": delegated, "single": single}


# Part B: one bounded delegation, on the learner's own queue, worker, loop and tools.

LEARNER = Path(__file__).resolve().parent
WORKER = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch13_worker_learner.py"))
LOOP = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch03_agent_loop_learner.py"))
APPROVAL, TOOLS = WORKER["APPROVAL"], LOOP["shop_tools"]
Claim, record_event = WORKER["Claim"], APPROVAL["record_event"]
Limits, ModelTurn, run_loop = LOOP["Limits"], LOOP["ModelTurn"], LOOP["run_loop"]
Dispatcher, ExecutableTool = TOOLS["Dispatcher"], TOOLS["ExecutableTool"]
NoArguments, ToolCall = TOOLS["NoArguments"], TOOLS["ToolCall"]

# Lucy's catering fixture: what a tub sells for. Chapter 2's PRICES are what the supplier charges.
SELLING_PRICE_CENTS = {"SKU-VANILLA": 500, "SKU-CHOCOLATE": 500, "SKU-STRAWBERRY": 500}
PORTIONS_PER_TUB = 10
# One billing account's model allowance per UTC day, across every worker that bills to it.
DAILY_CALLS, DAILY_CENTS = 200, 500

DELEGATION_MIGRATIONS = {
    1: (
        # Research work is work with a contract. Everything else in the queue is shop work.
        "CREATE TABLE delegations ("
        " work_id INTEGER PRIMARY KEY, parent_id INTEGER NOT NULL UNIQUE,"
        " billing_session TEXT NOT NULL, deadline REAL NOT NULL,"
        " model_calls_limit INTEGER NOT NULL, estimated_call_cents INTEGER NOT NULL,"
        " budget_cents INTEGER NOT NULL, model_calls INTEGER NOT NULL DEFAULT 0,"
        " estimated_cost_cents INTEGER NOT NULL DEFAULT 0)",
        "CREATE TABLE cancellations (work_id INTEGER PRIMARY KEY, created REAL NOT NULL)",
        "CREATE TABLE model_usage ("
        " billing_session TEXT NOT NULL, day INTEGER NOT NULL,"
        " model_calls INTEGER NOT NULL DEFAULT 0,"
        " estimated_cost_cents INTEGER NOT NULL DEFAULT 0,"
        " PRIMARY KEY (billing_session, day))",
    ),
}


def open_delegation_shop(path):
    """Chapter 13's worker shop, with contracts, cancellations and a shared model account."""
    db, queue = WORKER["open_worker_shop"](path)
    db.migrate("delegation", DELEGATION_MIGRATIONS)
    return db, queue


class Inquiry(NoArguments):
    sku: str = Field(min_length=1, max_length=100)
    guests: int = Field(ge=1, le=200)


def quote(inquiry: Inquiry) -> dict[str, Any]:
    """Ten portions per tub is Lucy's authored catering fixture, not a model estimate."""
    price = SELLING_PRICE_CENTS.get(inquiry.sku)
    if price is None:
        raise ValueError("unknown catering product")
    tubs = (inquiry.guests + PORTIONS_PER_TUB - 1) // PORTIONS_PER_TUB
    return {
        "sku": inquiry.sku,
        "guests": inquiry.guests,
        "portions_per_tub": PORTIONS_PER_TUB,
        "tubs": tubs,
        "total_cents": tubs * price,
        "currency": "USD",
        "status": "DRAFT_QUOTE",
        "stock_reserved": False,
    }


def delegate(
    queue,
    parent: int,
    inquiry: Inquiry,
    *,
    deadline: float,
    model_calls: int = 4,
    estimated_call_cents: int = 0,
    budget_cents: int = 100,
) -> int:
    """Bind one child to a shop parent: an exact inquiry, a deadline and a model allowance billed
    to the parent's account. The same handoff again returns the same child; different terms
    under the same parent are refused."""
    now = time.time()
    if (
        not math.isfinite(deadline)
        or not now < deadline <= now + 3600
        or type(model_calls) is not int
        or not 1 <= model_calls <= 8
        or type(estimated_call_cents) is not int
        or estimated_call_cents < 0
        or type(budget_cents) is not int
        or not 1 <= budget_cents <= 1000
    ):
        raise ValueError("bounded delegation contract required")
    quote(inquiry)
    encoded = inquiry.model_dump_json()
    terms = (encoded, deadline, model_calls, estimated_call_cents, budget_cents)
    with queue.store.immediate() as connection:
        source = connection.execute(
            "SELECT session_id FROM work WHERE work_id = ?"
            " AND work_id NOT IN (SELECT work_id FROM delegations)"
            " AND work_id NOT IN (SELECT work_id FROM cancellations)",
            (parent,),
        ).fetchone()
        if source is None:
            raise PermissionError("eligible shop parent required; delegation cannot recurse")
        existing = connection.execute(
            "SELECT d.work_id, w.text, d.deadline, d.model_calls_limit,"
            " d.estimated_call_cents, d.budget_cents"
            " FROM delegations d JOIN work w ON w.work_id = d.work_id WHERE d.parent_id = ?",
            (parent,),
        ).fetchone()
        if existing is not None:
            if tuple(existing[1:]) != terms:
                raise ValueError("parent already has a different immutable assignment")
            return existing[0]
        # Chapter 8's admission rule, inside this transaction, so child and contract commit
        # together or not at all.
        (open_work,) = connection.execute(
            "SELECT COUNT(*) FROM work WHERE state IN ('pending', 'running')"
        ).fetchone()
        if open_work >= queue.capacity:
            raise ValueError("the queue is full; the handoff was not admitted")
        child = connection.execute(
            "INSERT INTO work (source_id, session_id, text, state) VALUES (?, ?, ?, 'pending')",
            (f"delegation:{parent}", f"research:{parent}", encoded),
        ).lastrowid
        connection.execute(
            "INSERT INTO delegations (work_id, parent_id, billing_session, deadline,"
            " model_calls_limit, estimated_call_cents, budget_cents) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (child, parent, source[0], deadline, model_calls, estimated_call_cents, budget_cents),
        )
        record_event(connection, "delegation.created", {"parent": parent, "child": child})
    return child


def _take(connection, work_id: int, state: str, generation: int, worker_id: str, expires: float):
    """Chapter 13's acquisition: the next generation holds the work, fencing every earlier one."""
    if state == "pending":
        connection.execute(
            "UPDATE work SET state = 'running', worker_id = ? WHERE work_id = ?",
            (worker_id, work_id),
        )
    else:
        connection.execute("UPDATE work SET worker_id = ? WHERE work_id = ?", (worker_id, work_id))
    connection.execute(
        "INSERT INTO assignment_leases (work_id, worker_id, expires, generation)"
        " VALUES (?, ?, ?, ?) ON CONFLICT (work_id) DO UPDATE SET"
        " worker_id = excluded.worker_id, expires = excluded.expires,"
        " generation = excluded.generation",
        (work_id, worker_id, expires, generation),
    )


def claim(
    db,
    owner: str,
    *,
    role: str = "shop",
    work_id: int | None = None,
    ttl: float = 90,
    now: float | None = None,
) -> Claim | None:
    """Chapter 13's claim with two more conditions: the kind of work this worker does, and
    optionally which item. A shop worker never picks up a contract, nor a research worker a sale."""
    now = time.time() if now is None else now
    if role not in {"shop", "research"}:
        raise ValueError("a worker is a shop worker or a research worker")
    if not owner or "#" in owner or not math.isfinite(ttl) or not 0 < ttl <= 3600:
        raise ValueError("an owner label and a bounded lease are required")
    with db.immediate() as connection:
        row = connection.execute(
            "SELECT w.work_id, w.session_id, w.text, w.state, coalesce(l.generation, 0)"
            " FROM work w LEFT JOIN assignment_leases l ON l.work_id = w.work_id"
            " WHERE (w.state = 'pending' OR (w.state = 'running' AND l.expires <= :now))"
            " AND EXISTS (SELECT 1 FROM delegations d WHERE d.work_id = w.work_id) = :research"
            " AND (:work IS NULL OR w.work_id = :work)"
            " AND NOT EXISTS (SELECT 1 FROM work other"
            "   JOIN assignment_leases ol ON ol.work_id = other.work_id"
            "   WHERE other.session_id = w.session_id AND other.state = 'running'"
            "   AND ol.expires > :now)"
            " ORDER BY w.work_id LIMIT 1",
            {"now": now, "research": role == "research", "work": work_id},
        ).fetchone()
        if row is None:
            return None
        work, session_id, text, state, previous = row
        held = Claim(work, session_id, text, owner, previous + 1, now + ttl)
        _take(connection, work, state, held.generation, held.worker_id, held.expires)
    return held


def assert_current(connection, held: Claim, now: float | None = None) -> float:
    """Chapter 13's fence, and for research work its deadline too. A canceled parent needs no
    check here: cancel ends its unfinished children in the same transaction. Returns the
    lease's expiry."""
    now = time.time() if now is None else now
    expires = WORKER["assert_current"](connection, held, now)
    contract = connection.execute(
        "SELECT deadline FROM delegations WHERE work_id = ?", (held.work_id,)
    ).fetchone()
    if contract is not None and contract[0] <= now:
        raise PermissionError("delegation expired")
    return expires


def observe(db, held: Claim, message: dict[str, Any]) -> None:
    """Chapter 13's transcript write, fenced by this file's check."""
    with db.immediate() as connection:
        assert_current(connection, held)
        connection.execute(
            "INSERT INTO transcript (work_id, generation, message) VALUES (?, ?, ?)",
            (held.work_id, held.generation, json.dumps(message, allow_nan=False)),
        )


def finish(db, held: Claim, status: str, result: str) -> None:
    """Chapter 13's completion, fenced by this file's check."""
    if status not in {"DONE", "BLOCKED", "CANCELED"}:
        raise ValueError("invalid terminal work state")
    with db.immediate() as connection:
        assert_current(connection, held)
        connection.execute("UPDATE work SET state = 'finished' WHERE work_id = ?", (held.work_id,))
        connection.execute(
            "INSERT INTO outcomes (work_id, generation, status, result) VALUES (?, ?, ?, ?)",
            (held.work_id, held.generation, status, result),
        )


def _close(connection, work_id: int, result: str, now: float) -> None:
    """End unfinished work CANCELED. Chapter 8 allows only pending, running, finished in that
    order, so the cancellation first holds the work as a new generation, which fences whoever
    held it before. Finished work keeps its outcome."""
    row = connection.execute(
        "SELECT w.state, coalesce(l.generation, 0) FROM work w"
        " LEFT JOIN assignment_leases l ON l.work_id = w.work_id WHERE w.work_id = ?",
        (work_id,),
    ).fetchone()
    if row is None or row[0] == "finished":
        return
    generation = row[1] + 1
    _take(connection, work_id, row[0], generation, f"canceler#{generation}", now)
    connection.execute("UPDATE work SET state = 'finished' WHERE work_id = ?", (work_id,))
    connection.execute(
        "INSERT INTO outcomes (work_id, generation, status, result) VALUES (?, ?, 'CANCELED', ?)",
        (work_id, generation, result),
    )
    record_event(connection, "work.canceled", {"work": work_id, "generation": generation})


def cancel(db, work_id: int, *, now: float | None = None) -> None:
    """Lucy withdraws a request. Unfinished work and any unfinished child end CANCELED; finished
    work keeps its result, and the cancellation is recorded beside it. Nothing here recalls a
    model call or a supplier order already sent. An approved order on canceled work can no
    longer be sent, since sending needs the current holder; Chapter 11's revoke releases it."""
    now = time.time() if now is None else now
    with db.immediate() as connection:
        if (
            connection.execute("SELECT 1 FROM work WHERE work_id = ?", (work_id,)).fetchone()
            is None
        ):
            raise ValueError("unknown work")
        connection.execute(
            "INSERT OR IGNORE INTO cancellations (work_id, created) VALUES (?, ?)", (work_id, now)
        )
        _close(connection, work_id, "Canceled; transmitted orders still need reconciliation.", now)
        children = connection.execute(
            "SELECT work_id FROM delegations WHERE parent_id = ?", (work_id,)
        ).fetchall()
        for (child,) in children:
            _close(connection, child, "Parent canceled.", now)


def expire(db, *, now: float | None = None) -> int:
    """End contracts whose deadline has passed, whether or not a worker ever claimed them."""
    now = time.time() if now is None else now
    with db.immediate() as connection:
        rows = connection.execute(
            "SELECT d.work_id FROM delegations d JOIN work w ON w.work_id = d.work_id"
            " WHERE w.state != 'finished' AND d.deadline <= ?",
            (now,),
        ).fetchall()
        for (child,) in rows:
            _close(connection, child, "Delegation expired.", now)
    return len(rows)


def reserve_model_call(db, held: Claim, estimate_cents: int, *, now: float | None = None) -> None:
    """Record a model call before making it, against the contract for research work and against
    the billing account's day, in one transaction. Estimated exposure, kept even if the reply
    is lost; not an invoice cap."""
    if type(estimate_cents) is not int or estimate_cents < 0:
        raise ValueError("nonnegative integral model estimate required")
    now = time.time() if now is None else now
    if not math.isfinite(now):
        raise ValueError("finite clock required")
    with db.immediate() as connection:
        assert_current(connection, held, now)
        contract = connection.execute(
            "SELECT * FROM delegations WHERE work_id = ?", (held.work_id,)
        ).fetchone()
        billing = held.session_id
        if contract is not None:
            billing = contract["billing_session"]
            if (
                contract["model_calls"] >= contract["model_calls_limit"]
                or estimate_cents != contract["estimated_call_cents"]
                or contract["estimated_cost_cents"] + estimate_cents > contract["budget_cents"]
            ):
                raise PermissionError("delegation model allowance exhausted")
            connection.execute(
                "UPDATE delegations SET model_calls = model_calls + 1,"
                " estimated_cost_cents = estimated_cost_cents + ? WHERE work_id = ?",
                (estimate_cents, held.work_id),
            )
        day = int(now // 86400)
        connection.execute(
            "INSERT OR IGNORE INTO model_usage (billing_session, day) VALUES (?, ?)", (billing, day)
        )
        calls, cents = connection.execute(
            "SELECT model_calls, estimated_cost_cents FROM model_usage"
            " WHERE billing_session = ? AND day = ?",
            (billing, day),
        ).fetchone()
        if calls >= DAILY_CALLS or cents + estimate_cents > DAILY_CENTS:
            raise PermissionError("daily model allowance exhausted")
        connection.execute(
            "UPDATE model_usage SET model_calls = model_calls + 1,"
            " estimated_cost_cents = estimated_cost_cents + ?"
            " WHERE billing_session = ? AND day = ?",
            (estimate_cents, billing, day),
        )


class AuthorityLostError(Exception):
    """A held claim stopped being current. Deliberately not an OSError: Chapter 3's loop reads
    OSError as a failed model call, and PermissionError is an OSError."""


class HeldModel:
    """Chapter 3's model interface, fenced: each call is reserved against the holder's allowance
    first, and its reply is recorded only while the holder is still current."""

    def __init__(self, db, held: Claim, model, estimate_cents: int) -> None:
        self.db, self.held, self.model, self.estimate_cents = db, held, model, estimate_cents

    def complete(self, messages, tools, *, timeout, max_output_tokens):
        try:
            reserve_model_call(self.db, self.held, self.estimate_cents)
        except PermissionError as refused:
            raise AuthorityLostError(str(refused)) from refused
        turn = self.model.complete(
            messages, tools, timeout=timeout, max_output_tokens=max_output_tokens
        )
        try:
            observe(self.db, self.held, turn.message())
        except PermissionError as refused:
            raise AuthorityLostError(str(refused)) from refused
        return turn


class HeldTools:
    """Chapter 2's dispatcher, fenced the same way: no tool runs, and no result is recorded,
    unless the holder is current."""

    def __init__(self, db, held: Claim, dispatcher) -> None:
        self.db, self.held, self.dispatcher = db, held, dispatcher

    def schemas(self):
        return self.dispatcher.schemas()

    def invoke(self, call):
        try:
            with self.db.immediate() as connection:
                assert_current(connection, self.held)
            result = self.dispatcher.invoke(call)
            content = json.dumps(result, allow_nan=False)
            observe(
                self.db, self.held, {"role": "tool", "tool_call_id": call.id, "content": content}
            )
        except PermissionError as refused:
            raise AuthorityLostError(str(refused)) from refused
        return result


def run_held(db, held: Claim, model, dispatcher, messages, *, limits, should_stop=lambda: False):
    """Chapter 3's loop, unchanged, over a fenced model and fenced tools. Lost authority leaves
    the loop as the PermissionError it is, rather than as a model failure."""
    try:
        return run_loop(
            HeldModel(db, held, model, limits.estimated_call_cents),
            HeldTools(db, held, dispatcher),
            messages,
            limits=limits,
            should_stop=should_stop,
        )
    except AuthorityLostError as lost:
        raise PermissionError(str(lost)) from lost


def release(db, held: Claim) -> None:
    """Hand the work back early: end this lease now, so a replacement need not wait out its term."""
    with db.immediate() as connection:
        assert_current(connection, held)
        connection.execute(
            "UPDATE assignment_leases SET expires = ? WHERE work_id = ?",
            (time.time(), held.work_id),
        )


def stock_tools(db):
    """Chapter 2's tools over the stock Chapter 4 records, rather than the fixture's counts."""
    counts = dict(db.connection.execute("SELECT sku, tubs FROM stock").fetchall())
    products = [{**row, "on_hand": counts[sku]} for sku, row in APPROVAL["CATALOG"].items()]
    return TOOLS["build_tools"]({"products": products})


def shop_once(db, model, *, limits: Limits | None = None) -> dict[str, Any]:
    """One shop turn: Chapter 3's loop and Chapter 2's tools, run as held, billed work."""
    limits = limits or Limits()
    held = claim(db, uuid.uuid4().hex, role="shop", ttl=limits.seconds + 10)
    if held is None:
        return {"status": "IDLE"}
    messages = [LOOP["messages"][0], {"role": "user", "content": held.text}]
    try:
        result = run_held(db, held, model, stock_tools(db), messages, limits=limits)
        status = "DONE" if result.status == "COMPLETED" else "BLOCKED"
        answer = result.answer or "The agent stopped: " + result.status
        finish(db, held, status, answer)
    except PermissionError:
        return {"status": "STALE", "work": held.work_id}
    return {"status": status, "work": held.work_id, "answer": answer}


class OfflineCateringModel:
    """A fixture: request the quote for the inquiry in the user message, then finish."""

    def complete(self, messages, tools, *, timeout, max_output_tokens):
        if messages[-1]["role"] != "tool":
            arguments = json.loads(messages[1]["content"])
            return ModelTurn(
                calls=(ToolCall(id="quote-1", name="catering_quote", arguments=arguments),)
            )
        return ModelTurn("The draft quote is ready; no stock or purchase was committed.")


RESEARCH_PROMPT = (
    "Prepare a catering draft using catering_quote. "
    "You cannot reserve stock, buy supplies, or delegate."
)


def research_once(
    db, model, *, work_id: int | None = None, should_stop: Callable[[], bool] = lambda: False
) -> dict[str, Any]:
    """One research turn: claim a contract, let the model use one read-only tool on exactly the
    recorded inquiry, and grade the result against the function it could have been."""
    expire(db)
    if should_stop():
        return {"status": "STOPPED"}
    held = claim(db, uuid.uuid4().hex, role="research", work_id=work_id)
    if held is None:
        return {"status": "IDLE"}
    contract = db.connection.execute(
        "SELECT * FROM delegations WHERE work_id = ?", (held.work_id,)
    ).fetchone()
    inquiry = Inquiry.model_validate_json(held.text)
    started = time.monotonic()
    baseline = quote(inquiry)
    baseline_seconds = time.monotonic() - started
    observations: list[dict[str, Any]] = []

    def calculate(arguments: Inquiry) -> dict[str, Any]:
        if arguments != inquiry:
            raise PermissionError("quote differs from the immutable inquiry")
        observations.append(quote(inquiry))
        return observations[-1]

    tool = ExecutableTool(
        "catering_quote", "Calculate this assignment's read-only draft quote.", Inquiry, calculate
    )
    tools = Dispatcher([tool], allowed=frozenset({"catering_quote"}))
    messages = [
        {"role": "system", "content": RESEARCH_PROMPT},
        {"role": "user", "content": held.text},
    ]
    try:
        remaining = contract["deadline"] - time.time()
        if remaining <= 0:
            raise PermissionError("delegation expired")
        limits = Limits(
            model_calls=contract["model_calls_limit"],
            tool_calls=4,
            seconds=min(60, remaining),
            estimated_call_cents=contract["estimated_call_cents"],
            model_budget_cents=contract["budget_cents"],
        )
        started = time.monotonic()
        result = run_held(db, held, model, tools, messages, limits=limits, should_stop=should_stop)
        if result.status == "STOP_REQUESTED":
            release(db, held)
            return {"status": "STOPPED", "work": held.work_id}
        passed = (
            result.status == "COMPLETED" and bool(observations) and observations[-1] == baseline
        )
        usage = db.connection.execute(
            "SELECT model_calls, estimated_cost_cents FROM delegations WHERE work_id = ?",
            (held.work_id,),
        ).fetchone()
        report = {
            "passed": passed,
            "quote": observations[-1] if observations else None,
            "model_answer": result.answer,
            "loop": asdict(result),
            "baseline": {"quote": baseline, "model_calls": 0, "seconds": baseline_seconds},
            "seconds": time.monotonic() - started,
            "decision": "Retain the function for this fixed calculation; model prose is ungraded.",
            "assignment_usage": {"model_calls": usage[0], "estimated_cost_cents": usage[1]},
        }
        # What Lucy reads is stated from the checked quote, not from the model's prose.
        answer = (
            f"Catering draft: {baseline['tubs']} tubs for {inquiry.guests} guests, "
            f"USD {baseline['total_cents'] / 100:.2f}. No stock reserved."
            if passed
            else "Catering research did not produce verified quote evidence."
        )
        with db.immediate() as connection:
            assert_current(connection, held)
            record_event(
                connection, "delegation.evaluated", {"work": held.work_id, "report": report}
            )
        finish(db, held, "DONE" if passed else "BLOCKED", answer)
        return {"status": "DONE" if passed else "BLOCKED", "work": held.work_id, "report": report}
    except PermissionError:
        expire(db)
        # A stale worker must never finish or cancel a replacement's claim.
        try:
            finish(db, held, "BLOCKED", "Delegation authority or allowance exhausted.")
        except PermissionError:
            pass
        return {"status": "AUTHORITY_STOP", "work": held.work_id}
