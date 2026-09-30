# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 20's day: every earlier chapter's learner code in one store, one worker and one report.

Each chapter built its piece on its own store. This file opens them as one: Chapter 18's store
(Chapter 11's orders, Chapter 13's leases with generations, delegation and the daily model
account), with Chapter 5's memory, Chapter 7's skills, Chapter 9's channel and Chapter 10's wake-ups
migrated beside it. One worker runs every kind of shop work: an approval command from the phone,
with no model; a continuation of approved or uncertain orders through Chapter 11's send check,
with no model; or a model turn over the subject's tools, which may propose orders and then waits
for approval. The report reads one snapshot and states only what the records say.
"""

import json
import re
import runpy
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import Field

LEARNER = Path(__file__).resolve().parent
DELEGATION = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch18_delegation_learner.py"))
WAKE = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch10_wakeups_learner.py"))
APPROVAL, WORKER = DELEGATION["APPROVAL"], DELEGATION["WORKER"]
CHANNEL, SKILLS, MEMORY, LOOP = WAKE["CHANNEL"], WAKE["SKILLS"], WAKE["MEMORY"], WAKE["LOOP"]
STORE, TOOLS = WAKE["STORE"], WAKE["TOOLS"]
Limits, ModelTurn, ToolCall = LOOP["Limits"], LOOP["ModelTurn"], LOOP["ToolCall"]
APPROVE = re.compile(r"/approve ([a-f0-9]{32}) ([a-f0-9]{64})")


def open_day(path: str | Path):
    """Chapter 18's store with every other chapter's tables beside it, each on its own line of
    migrations, and rows readable by column name."""
    db, queue = DELEGATION["open_delegation_shop"](path)
    db.migrate("memory", MEMORY["MEMORY_MIGRATIONS"])
    db.migrate("skills", SKILLS["SKILL_MIGRATIONS"])
    db.migrate("channel", CHANNEL["CHANNEL_MIGRATIONS"])
    db.migrate("wakeups", WAKE["WAKE_MIGRATIONS"])
    with db.immediate() as connection:
        # Chapter 11 counted the stock in; Chapter 10's tools also need each product's terms.
        for sku, row in APPROVAL["CATALOG"].items():
            connection.execute(
                "INSERT OR IGNORE INTO products VALUES (?, ?, ?, ?)",
                (sku, row["name"], row["reorder_point"], APPROVAL["PRICES"][sku]),
            )
    db.connection.row_factory = CHANNEL["named_rows"]
    return db, queue


def retry(db, queue, work_id: int) -> int:
    """A retry is new work that names what it retries: Chapter 8's states never run backward.
    It keeps the original's session, text, route and subject."""
    with db.immediate() as connection:
        row = connection.execute(
            "SELECT w.session_id, w.text, r.channel, r.recipient, s.subject FROM work w"
            " JOIN channel_routes r ON r.work_id = w.work_id"
            " LEFT JOIN work_subjects s ON s.work_id = w.work_id WHERE w.work_id = ?",
            (work_id,),
        ).fetchone()
        if row is None:
            raise ValueError("unknown work")
        (tries,) = connection.execute(
            "SELECT count(*) FROM work WHERE source_id LIKE ?", (f"retry:{work_id}:%",)
        ).fetchone()
        new = WAKE["admit"](
            connection,
            queue,
            f"retry:{work_id}:{tries + 1}",
            row["session_id"],
            row["text"],
            (row["channel"], row["recipient"]),
            subject=row["subject"],
        )
    if new is None:
        raise ValueError("the queue is full; the retry was not admitted")
    return new


def claim_next(db, owner: str, *, ttl: float = 90, work_id: int | None = None):
    """Chapter 18's shop claim, and one more rule: work whose only orders are drafts is waiting
    for Lucy, so it is not taken until one of them is approved."""
    now = time.time()
    with db.immediate() as connection:
        row = connection.execute(
            "SELECT w.work_id, w.session_id, w.text, w.state, coalesce(l.generation, 0)"
            " FROM work w LEFT JOIN assignment_leases l ON l.work_id = w.work_id"
            " WHERE (w.state = 'pending' OR (w.state = 'running' AND l.expires <= :now))"
            " AND w.work_id NOT IN (SELECT work_id FROM delegations)"
            " AND (:work IS NULL OR w.work_id = :work)"
            " AND NOT (w.state = 'running' AND EXISTS (SELECT 1 FROM assistant_orders o"
            "   WHERE o.work_id = w.work_id) AND NOT EXISTS (SELECT 1 FROM assistant_orders o"
            "   WHERE o.work_id = w.work_id AND o.status IN ('APPROVED','SENDING','UNKNOWN')))"
            " AND NOT EXISTS (SELECT 1 FROM work other"
            "   JOIN assignment_leases ol ON ol.work_id = other.work_id"
            "   WHERE other.session_id = w.session_id AND other.state = 'running'"
            "   AND ol.expires > :now)"
            " ORDER BY w.work_id LIMIT 1",
            {"now": now, "work": work_id},
        ).fetchone()
        if row is None:
            return None, None
        work, session_id, text, state, previous = row
        held = DELEGATION["Claim"](work, session_id, text, owner, previous + 1, now + ttl)
        DELEGATION["_take"](connection, work, state, held.generation, held.worker_id, held.expires)
    return held, state


def finish(db, held, status: str, answer: str) -> None:
    """Chapter 18's fenced completion, with Chapter 8's report in the same transaction, so the
    phone can deliver what the work concluded."""
    if status not in {"DONE", "BLOCKED", "CANCELED"}:
        raise ValueError("invalid terminal work state")
    with db.immediate() as connection:
        DELEGATION["assert_current"](connection, held)
        connection.execute("UPDATE work SET state = 'finished' WHERE work_id = ?", (held.work_id,))
        connection.execute(
            "INSERT INTO outcomes (work_id, generation, status, result) VALUES (?, ?, ?, ?)",
            (held.work_id, held.generation, status, answer),
        )
        (generation,) = connection.execute(
            "SELECT count(*) + 1 FROM reports WHERE work_id = ?", (held.work_id,)
        ).fetchone()
        connection.execute(
            "INSERT INTO reports (report_id, work_id, generation, body, delivery)"
            " VALUES (?, ?, ?, ?, 'pending')",
            (f"r{held.work_id}.{generation}", held.work_id, generation, answer),
        )


class OrderArguments(TOOLS["NoArguments"]):
    sku: str = Field(min_length=1, max_length=100)
    quantity: int = Field(gt=0, le=1000)


def day_tools(db, held, subject: str | None, supplier):
    """Chapter 10's tools for the subject. For a scoped episode with a supplier configured, the
    draft is a real one: `propose_order` replaces `draft_order` and records Chapter 11's exact
    proposal of the current need. It never sends anything; sending needs Lucy's approval of that
    exact proposal. A live model asked for a draft uses whichever draft tool it is given."""
    shop = WAKE["shop_tools"](db, subject)
    registered = list(shop.tools.values())
    if subject is not None and supplier is not None:
        registered = [tool for tool in registered if tool.name != "draft_order"]

        def propose(args):
            if args.sku != subject:
                raise PermissionError("this work is scoped to another product")
            rows = WAKE["stock_rows"](db.connection, args.sku)
            if not rows or args.quantity != rows[0]["needed"] or args.quantity <= 0:
                raise ValueError("an order must be for the current positive need")
            order = APPROVAL["propose"](db, held, args.sku, args.quantity, target=supplier.identity)
            row = db.connection.execute(
                "SELECT amount, digest FROM assistant_orders WHERE id = ?", (order,)
            ).fetchone()
            return {
                "order": order,
                "digest": row["digest"],
                "amount_cents": row["amount"],
                "status": "DRAFT",
            }

        registered.append(
            TOOLS["ExecutableTool"](
                "propose_order",
                "Draft an order for the current need, as a proposal that waits for Lucy's"
                " approval. Never purchases.",
                OrderArguments,
                propose,
            )
        )
    return TOOLS["Dispatcher"](registered, allowed=frozenset(t.name for t in registered))


def orders_of(db, work_id: int, statuses: tuple[str, ...]) -> list[str]:
    marks = ",".join("?" * len(statuses))
    return [
        row[0]
        for row in db.connection.execute(
            f"SELECT id FROM assistant_orders WHERE work_id = ? AND status IN ({marks})"
            " ORDER BY created, id",
            (work_id, *statuses),
        )
    ]


def approve_command(db, held, policy) -> dict[str, Any]:
    """`/approve ORDER DIGEST` from an allowlisted phone: Chapter 11's approval, no model."""
    match = APPROVE.fullmatch(held.text.strip())
    actor = held.session_id.rsplit(":", 1)[-1]
    try:
        if match is None:
            raise ValueError("expected /approve ORDER DIGEST")
        APPROVAL["approve"](
            db, match[1], match[2], actor=actor, policy=policy, expires=time.time() + 3600
        )
    except (ValueError, PermissionError) as refused:
        finish(db, held, "BLOCKED", f"Approval refused: {refused}")
        return {"status": "BLOCKED", "work": held.work_id}
    finish(db, held, "DONE", f"Approved order {match[1]}. It will be sent once.")
    return {"status": "DONE", "work": held.work_id, "approved": match[1]}


def continue_orders(db, held, supplier, policy) -> dict[str, Any]:
    """Send or reconcile this work's approved orders through Chapter 11's check, no model.
    An uncertain outcome hands the work back, to be looked up again; it is never resent blind."""
    receipts = {
        order: APPROVAL["execute"](db, held, order, supplier, policy=policy)
        for order in orders_of(db, held.work_id, ("APPROVED", "SENDING", "UNKNOWN"))
    }
    if all(r.get("status") in {"ACCEPTED", "REJECTED"} for r in receipts.values()):
        summary = ", ".join(f"{order}: {r['status']}" for order, r in receipts.items())
        finish(db, held, "DONE", "Continued the approved orders. " + summary)
        return {"status": "DONE", "work": held.work_id, "receipts": receipts}
    DELEGATION["release"](db, held)
    return {"status": "UNKNOWN", "work": held.work_id, "receipts": receipts}


def work_once(
    db,
    model,
    *,
    supplier=None,
    policy=None,
    owner: str | None = None,
    ttl: float = 90,
    work_id: int | None = None,
    limits=None,
) -> dict[str, Any]:
    """Claim the next shop work and do the one kind of step it needs."""
    limits = limits or Limits()
    held, state = claim_next(db, owner or uuid.uuid4().hex, ttl=ttl, work_id=work_id)
    if held is None:
        return {"status": "IDLE"}
    if APPROVE.match(held.text.strip()):
        return approve_command(db, held, policy)
    if orders_of(db, held.work_id, ("APPROVED", "SENDING", "UNKNOWN")):
        return continue_orders(db, held, supplier, policy)
    if state == "running":
        # Taken over after its holder vanished, with nothing recorded to continue.
        finish(db, held, "BLOCKED", "The agent stopped before answering. Please ask again.")
        return {"status": "BLOCKED", "work": held.work_id}
    row = db.connection.execute(
        "SELECT subject FROM work_subjects WHERE work_id = ?", (held.work_id,)
    ).fetchone()
    subject = row[0] if row else None
    tools = day_tools(db, held, subject, supplier)
    messages = SKILLS["context"](db, held.session_id, held.text, allowed=tools.allowed)
    try:
        result = DELEGATION["run_held"](db, held, model, tools, messages, limits=limits)
    except PermissionError:
        return {"status": "STALE", "work": held.work_id}
    if result.status != "COMPLETED":
        finish(db, held, "BLOCKED", "The agent stopped: " + result.status)
        return {"status": "BLOCKED", "work": held.work_id, "loop": result.status}
    if orders_of(db, held.work_id, ("DRAFT",)):
        # The proposals wait for Lucy; the work stays open, and no one takes it meanwhile.
        DELEGATION["release"](db, held)
        return {"status": "AWAITING_APPROVAL", "work": held.work_id}
    answer = WAKE["draft_report"](result.messages) or result.answer
    finish(db, held, "DONE", answer)
    return {"status": "DONE", "work": held.work_id, "answer": answer}


class OfflineDayModel(SKILLS["OfflineShopModel"]):
    """Chapter 7's fixture, and where `propose_order` is offered, it proposes each positive
    need instead of drafting it. It tests the wiring, not language understanding."""

    def complete(self, messages, tools, *, timeout, max_output_tokens):
        if "propose_order" not in {tool["function"]["name"] for tool in tools}:
            return super().complete(
                messages, tools, timeout=timeout, max_output_tokens=max_output_tokens
            )
        start = max(i for i, m in enumerate(messages) if m["role"] == "user")
        if sum(m["role"] == "tool" for m in messages[start:]) >= 2:
            return ModelTurn("Proposed the replenishment; it waits for Lucy's approval.")
        turn = super().complete(
            messages, tools, timeout=timeout, max_output_tokens=max_output_tokens
        )
        calls = tuple(
            ToolCall(
                id=call.id.replace("draft", "order"), name="propose_order", arguments=call.arguments
            )
            if call.name == "draft_order"
            else call
            for call in turn.calls
        )
        return ModelTurn(turn.content, calls, turn.output_tokens)


def receive(db, order: str, reference: str, *, actor: str, policy) -> str:
    """Record a delivery: the order becomes DELIVERED and its tubs arrive, once. The same
    reference again changes nothing; a different one for a delivered order is refused."""
    if actor not in policy.operators:
        raise PermissionError("operator is not allowlisted")
    if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,100}", reference):
        raise ValueError("invalid delivery reference")
    with db.immediate() as connection:
        row = connection.execute("SELECT * FROM assistant_orders WHERE id = ?", (order,)).fetchone()
        if row is None:
            raise ValueError("unknown order")
        proposal = json.loads(row["proposal"])
        event = STORE["StockEvent"](
            f"delivery:{reference}", proposal["sku"], proposal["quantity"], "delivery received"
        )
        existing = connection.execute(
            "SELECT payload FROM events WHERE event_id = ?", (event.event_id,)
        ).fetchone()
        if row["status"] == "DELIVERED":
            if existing is None or existing[0] != event.payload():
                raise ValueError("this order was already received under another reference")
            return "duplicate"
        if row["status"] != "CONFIRMED":
            raise PermissionError("only an accepted order can be received")
        connection.execute(
            "INSERT INTO events (event_id, sku, delta, payload, reason) VALUES (?, ?, ?, ?, ?)",
            (event.event_id, event.sku, event.delta, event.payload(), event.reason),
        )
        connection.execute(
            "UPDATE stock SET tubs = tubs + ? WHERE sku = ?", (event.delta, event.sku)
        )
        connection.execute("UPDATE assistant_orders SET status='DELIVERED' WHERE id = ?", (order,))
        APPROVAL["record_event"](
            connection, "order.received", {"order": order, "reference": reference, "actor": actor}
        )
    return "received"


def usd(cents: int) -> str:
    return f"USD {cents // 100}.{cents % 100:02d}"


def operating_report(db) -> dict[str, Any]:
    """Read one SQLite snapshot and render what the records say; no model is consulted.

    Work, orders and spending cover all retained history; model usage covers the current UTC
    day. It is not revenue, cash profit or an audit of the supplier's account."""
    connection = db.connection
    if connection.in_transaction:
        raise ValueError("the report needs its own read snapshot")
    observed = time.time()
    connection.execute("BEGIN")
    try:
        states = dict(connection.execute("SELECT state, count(*) FROM work GROUP BY state"))
        outcomes = dict(connection.execute("SELECT status, count(*) FROM outcomes GROUP BY status"))
        orders = dict(
            connection.execute("SELECT status, count(*) FROM assistant_orders GROUP BY status")
        )
        accepted, held = connection.execute(
            "SELECT coalesce(sum(CASE WHEN status IN ('CONFIRMED','DELIVERED') THEN amount END),0),"
            " coalesce(sum(CASE WHEN status IN ('APPROVED','SENDING','UNKNOWN') THEN amount END),0)"
            " FROM assistant_orders"
        ).fetchone()
        budget = connection.execute(
            "SELECT reserved_cents, spent_cents FROM assistant_spending WHERE id = 1"
        ).fetchone()
        reserved, spent = (0, 0) if budget is None else tuple(budget)
        pending = dict(
            connection.execute(
                "SELECT json_extract(proposal,'$.sku'), sum(json_extract(proposal,'$.quantity'))"
                " FROM assistant_orders WHERE status IN ('APPROVED','SENDING','UNKNOWN','CONFIRMED')"
                " GROUP BY 1"
            )
        )
        stock = [
            {
                **row,
                "on_order": pending.get(row["sku"], 0),
                "needed": max(
                    0, row["reorder_point"] - row["on_hand"] - pending.get(row["sku"], 0)
                ),
            }
            for row in WAKE["stock_rows"](connection)
        ]
        waiting = [
            row[0]
            for row in connection.execute(
                "SELECT work_id FROM work WHERE state != 'finished' ORDER BY work_id LIMIT 20"
            )
        ]
        # A blocked item someone retried is history; one nobody retried needs attention.
        unretried = connection.execute(
            "SELECT count(*) FROM outcomes o WHERE o.status = 'BLOCKED' AND NOT EXISTS"
            " (SELECT 1 FROM work r WHERE r.source_id LIKE 'retry:' || o.work_id || ':%')"
        ).fetchone()[0]
        research = connection.execute(
            "SELECT count(*) FROM outcomes o JOIN delegations d ON d.work_id = o.work_id"
            " WHERE o.status = 'DONE'"
        ).fetchone()[0]
        calls, estimate = connection.execute(
            "SELECT coalesce(sum(model_calls),0), coalesce(sum(estimated_cost_cents),0)"
            " FROM model_usage WHERE day = ?",
            (int(observed // 86400),),
        ).fetchone()
        uncertain_reports = connection.execute(
            "SELECT count(*) FROM reports r JOIN channel_routes c ON c.work_id = r.work_id"
            " WHERE c.channel LIKE 'telegram:%' AND r.delivery IN ('sending','unknown')"
        ).fetchone()[0]
    finally:
        # The store's connection is in autocommit mode, where rollback() does nothing: end the
        # read transaction explicitly, or the next write finds it still open.
        connection.execute("ROLLBACK")
    exceptions = []
    if unretried:
        exceptions.append(f"{unretried} blocked work item(s) not retried; read their records.")
    uncertain = orders.get("SENDING", 0) + orders.get("UNKNOWN", 0)
    if uncertain:
        exceptions.append(f"{uncertain} supplier outcome(s) remain uncertain.")
    if uncertain_reports:
        exceptions.append(f"{uncertain_reports} phone report(s) may or may not have arrived.")
    matching = (spent, reserved) == (accepted, held)
    if not matching:
        exceptions.append("Spending ledger and retained order totals disagree.")
    report = {
        "observed_at": datetime.fromtimestamp(observed, UTC).isoformat(),
        "work": states,
        "outcomes": outcomes,
        "orders": orders,
        "spending": {
            "accepted_cents": spent,
            "reserved_cents": reserved,
            "order_totals_match": matching,
        },
        "stock": stock,
        "open_work": waiting,
        "research_quotes_completed": research,
        "model_usage": {"calls": calls, "estimated_cents": estimate},
        "exceptions": exceptions,
    }
    lines = [
        "Lucy's operating report",
        f"Observed: {report['observed_at']}",
        "Current local snapshot. Work, orders and spending cover all retained history; model"
        " usage covers today (UTC). No external account audit was performed.",
        "",
        f"Supplier purchases accepted: {usd(spent)}",
        f"Allowance reserved for pending orders: {usd(reserved)}",
        f"Orders delivered: {orders.get('DELIVERED', 0)}; accepted and awaiting delivery: "
        f"{orders.get('CONFIRMED', 0)}; drafts awaiting approval: {orders.get('DRAFT', 0)}",
        f"Work completed: {outcomes.get('DONE', 0)}; ended blocked: {outcomes.get('BLOCKED', 0)}"
        f" ({outcomes.get('BLOCKED', 0) - unretried} retried); still open: {len(waiting)}",
        f"Read-only research quotes completed: {research}",
        "",
        "Current stock:",
    ]
    for row in stock:
        name = json.dumps(row["sku"], ensure_ascii=True)
        lines.append(
            f"- {name}: {row['on_hand']} on hand, {row['on_order']} pending replenishment,"
            f" {row['needed']} still needed"
        )
    lines += [
        "",
        f"Model calls reserved today: {calls}; configured estimate: {estimate} cents."
        " This is not a provider invoice.",
        "",
        "Exceptions requiring inspection:",
    ]
    lines += [f"- {item}" for item in exceptions] or [
        "- None in this local snapshot; external outcomes still need their own evidence."
    ]
    report["text"] = "\n".join(lines)
    return report
