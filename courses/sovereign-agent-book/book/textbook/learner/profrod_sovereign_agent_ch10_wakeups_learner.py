# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 10's wake-ups: a clock and a stock scanner that put work on the learner's own queue.

Every piece underneath is earlier learner code. Chapter 4's store keeps the stock and its event
log. Chapter 9's channel supplies the store, Chapter 8's queue, a route for every piece of work, a
claim that serializes a session's turns, and delivery. Chapter 7's context and Chapter 3's loop run
each turn. This file adds the producers: fixed-interval jobs that coalesce missed runs, stock
conditions that turn a shortage into one episode of work, a work subject that scopes the shop
tools, a report taken from the tools' observations rather than the model's narration, and a
serving loop that runs them with nobody prompting.

Run `python profrod_sovereign_agent_ch10_wakeups_learner.py serve --root DIR` from the course
folder to serve a prepared database until the process is stopped.
"""

import argparse
import json
import math
import re
import runpy
import signal
import sqlite3
import sys
import threading
import time
from pathlib import Path
from typing import Any

LEARNER = Path(__file__).resolve().parent
CHANNEL = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch09_messaging_learner.py"))
SKILLS, MEMORY, LOOP = CHANNEL["SKILLS"], CHANNEL["MEMORY"], CHANNEL["LOOP"]
STORE, TOOLS = MEMORY["STORE"], LOOP["shop_tools"]

WAKE_MIGRATIONS = {
    1: (
        # Chapter 4's `stock` table holds each product's tubs; this is what a tub is worth.
        "CREATE TABLE products ("
        " sku TEXT PRIMARY KEY, name TEXT NOT NULL,"
        " reorder_point INTEGER NOT NULL CHECK (reorder_point >= 0),"
        " unit_cost_cents INTEGER NOT NULL CHECK (unit_cost_cents >= 0))",
        "CREATE TABLE wake_control (id INTEGER PRIMARY KEY CHECK (id = 1), paused INTEGER NOT NULL)",
        "INSERT INTO wake_control (id, paused) VALUES (1, 0)",
        "CREATE TABLE wake_jobs ("
        " id TEXT PRIMARY KEY, session TEXT NOT NULL, prompt TEXT NOT NULL,"
        " interval_seconds INTEGER NOT NULL, next_due REAL NOT NULL,"
        " channel TEXT NOT NULL, recipient TEXT NOT NULL,"
        " enabled INTEGER NOT NULL DEFAULT 1, deferred INTEGER NOT NULL DEFAULT 0)",
        "CREATE TABLE stock_conditions ("
        " id TEXT PRIMARY KEY, session TEXT NOT NULL, subject TEXT NOT NULL,"
        " channel TEXT NOT NULL, recipient TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1,"
        " armed INTEGER NOT NULL DEFAULT 1, generation INTEGER NOT NULL DEFAULT 0)",
        # One enabled condition per product, whoever writes the table.
        "CREATE UNIQUE INDEX stock_condition_subject ON stock_conditions (subject) WHERE enabled = 1",
        # The product a piece of work is scoped to. Work without a row here is whole-shop work.
        "CREATE TABLE work_subjects (work_id INTEGER PRIMARY KEY, subject TEXT NOT NULL)",
        # Each turn's raw transcript, kept for evaluation beside the report it produced.
        "CREATE TABLE work_transcripts ("
        " work_id INTEGER PRIMARY KEY, status TEXT NOT NULL, messages TEXT NOT NULL)",
    ),
}


def open_shop(path: str | Path, *, capacity: int = 10):
    """Chapter 9's store and queue, with Chapter 4's stock tables and this chapter's own."""
    db, queue = CHANNEL["open_channel"](path, capacity=capacity)
    db.initialize()
    db.migrate("wakeups", WAKE_MIGRATIONS)
    return db, queue


def seed_shop(db) -> None:
    """Lucy's three products from Chapter 1, at Chapter 2's prices, counted in by stock events.
    Seeding twice changes nothing: each opening count is an event with a fixed identity."""
    with db.immediate() as connection:
        for row in TOOLS["SHOP"]["products"]:
            connection.execute(
                "INSERT OR IGNORE INTO products VALUES (?, ?, ?, ?)",
                (row["sku"], row["name"], row["reorder_point"], TOOLS["PRICES"][row["sku"]]),
            )
    for row in TOOLS["SHOP"]["products"]:
        db.apply(STORE["StockEvent"](f"opening:{row['sku']}", row["sku"], row["on_hand"], "count"))


def adjust_stock(db, event_id: str, sku: str, delta: int, reason: str) -> str:
    """A delivery or a sale, as a Chapter 4 stock event: "applied" or "duplicate"."""
    return db.apply(STORE["StockEvent"](event_id, sku, delta, reason))


def stock_rows(connection, subject: str | None = None) -> list[dict[str, Any]]:
    """Current stock with its replenishment need, read from the database at call time."""
    rows = connection.execute(
        "SELECT p.sku, p.name, s.tubs, p.reorder_point FROM products p"
        " JOIN stock s ON s.sku = p.sku WHERE (? IS NULL OR p.sku = ?) ORDER BY p.sku",
        (subject, subject),
    ).fetchall()
    return [
        {
            "sku": sku,
            "name": name,
            "on_hand": tubs,
            "reorder_point": point,
            "needed": max(0, point - tubs),
        }
        for sku, name, tubs, point in rows
    ]


def shop_tools(db, subject: str | None = None):
    """Chapter 2's three tools over the database's current stock, through Chapter 2's dispatcher.

    With a subject, the tools see and draft only that product: a request for another product is
    refused by the tool, whatever the model was told or remembers."""

    def in_scope(sku: str) -> None:
        if subject is not None and sku != subject:
            raise PermissionError("this work is scoped to another product")

    def stock(_):
        return stock_rows(db.connection, subject)

    def quote(args):
        in_scope(args.sku)
        row = db.connection.execute(
            "SELECT unit_cost_cents FROM products WHERE sku = ?", (args.sku,)
        ).fetchone()
        if row is None:
            raise KeyError("unknown product")
        return {
            "sku": args.sku,
            "supplier": "lucy-local",
            "currency": "USD",
            "unit_cost_cents": row[0],
        }

    def draft(args):
        in_scope(args.sku)
        rows = stock_rows(db.connection, args.sku)
        if not rows or rows[0]["needed"] <= 0 or args.quantity != rows[0]["needed"]:
            raise ValueError("draft quantity must equal the current positive need")
        price = quote(args)
        return {
            **price,
            "quantity": args.quantity,
            "total_cents": args.quantity * price["unit_cost_cents"],
            "status": "DRAFT",
        }

    tool = TOOLS["ExecutableTool"]
    registered = [
        tool("list_stock", "Read stock and calculated need.", TOOLS["NoArguments"], stock),
        tool("supplier", "Read supplier price in USD cents.", TOOLS["ProductArguments"], quote),
        tool("draft_order", "Calculate a draft; never purchases.", TOOLS["DraftArguments"], draft),
    ]
    return TOOLS["Dispatcher"](registered, allowed=frozenset(t.name for t in registered))


def validate_route(channel: str, recipient: str) -> None:
    """Local output, or a Telegram bot account and a positive numeric recipient."""
    if (
        not isinstance(channel, str)
        or not isinstance(recipient, str)
        or len(channel) > 200
        or len(recipient) > 200
        or not (
            (channel == "local" and not recipient)
            or (
                re.fullmatch(r"telegram:[A-Za-z0-9_-]+", channel)
                and recipient.isascii()
                and recipient.isdigit()
                and int(recipient) > 0
            )
        )
    ):
        raise ValueError("local output or an explicit positive Telegram recipient required")


def admit(connection, queue, source_id, session_id, text, route, subject=None) -> int | None:
    """Chapter 8's admission, strict, inside the caller's transaction.

    Returns the work id, or None when the queue is full: nothing is stored, so a producer can
    leave its own state as it was and try again on a later pass. The route and the subject are
    stored with the work."""
    row = connection.execute(
        "SELECT work_id, session_id, text FROM work WHERE source_id = ?", (source_id,)
    ).fetchone()
    if row is not None:
        if (row[1], row[2]) != (session_id, text):
            raise ValueError("intake identity reused for different content")
        return row[0]
    (open_work,) = connection.execute(
        "SELECT COUNT(*) FROM work WHERE state IN ('pending', 'running')"
    ).fetchone()
    if open_work >= queue.capacity:
        return None
    work_id = connection.execute(
        "INSERT INTO work (source_id, session_id, text, state) VALUES (?, ?, ?, 'pending')",
        (source_id, session_id, text),
    ).lastrowid
    connection.execute("INSERT INTO channel_routes VALUES (?, ?, ?)", (work_id, *route))
    if subject is not None:
        connection.execute("INSERT INTO work_subjects VALUES (?, ?)", (work_id, subject))
    return work_id


def schedule(
    db,
    identifier: str,
    session: str,
    prompt: str,
    *,
    first_due: float,
    interval_seconds: int,
    channel: str = "local",
    recipient: str = "",
) -> None:
    """Epoch UTC intervals; missed runs coalesce to one, rather than a backlog storm."""
    if type(interval_seconds) is not int or interval_seconds < 1 or not math.isfinite(first_due):
        raise ValueError("finite due time and positive integral interval required")
    if (
        any(
            not isinstance(value, str) or not value.strip() or len(value) > 100
            for value in (identifier, session)
        )
        or not isinstance(prompt, str)
        or not prompt.strip()
        or len(prompt.encode()) > 16_384
    ):
        raise ValueError("bounded job identity, session and prompt required")
    validate_route(channel, recipient)
    with db.immediate() as connection:
        if connection.execute("SELECT 1 FROM wake_jobs WHERE id=?", (identifier,)).fetchone():
            raise ValueError(
                "schedule identity already exists; use a new identity for a replacement"
            )
        connection.execute(
            "INSERT INTO wake_jobs(id,session,prompt,interval_seconds,next_due,channel,recipient) "
            "VALUES (?,?,?,?,?,?,?)",
            (identifier, session, prompt, interval_seconds, first_due, channel, recipient),
        )


def unschedule(db, identifier: str) -> None:
    """Stop future ticks without deleting work that a prior tick already admitted."""
    with db.immediate() as connection:
        if (
            connection.execute("UPDATE wake_jobs SET enabled=0 WHERE id=?", (identifier,)).rowcount
            != 1
        ):
            raise ValueError("unknown schedule")


def paused(connection) -> bool:
    return bool(connection.execute("SELECT paused FROM wake_control WHERE id=1").fetchone()[0])


def set_paused(db, value: bool) -> None:
    with db.immediate() as connection:
        connection.execute("UPDATE wake_control SET paused=? WHERE id=1", (int(value),))


def tick(db, queue, *, now: float | None = None, maximum: int = 100) -> list[int]:
    """One scheduler pass: admit each due job's current occurrence and advance it, together."""
    now = time.time() if now is None else now
    if not math.isfinite(now) or type(maximum) is not int or not 1 <= maximum <= 1000:
        raise ValueError("invalid scheduler pass")
    created = []
    with db.immediate() as connection:
        if paused(connection):
            return []
        rows = connection.execute(
            "SELECT * FROM wake_jobs WHERE enabled=1 AND next_due<=? ORDER BY next_due,id LIMIT ?",
            (now, maximum),
        ).fetchall()
        for row in rows:
            work = admit(
                connection,
                queue,
                f"job:{row['id']}:{row['next_due']!r}",
                row["session"],
                row["prompt"],
                (row["channel"], row["recipient"]),
            )
            if work is None:
                # The queue is full: keep the due time, and record the deferral once.
                if not row["deferred"]:
                    MEMORY["record_event"](connection, "wake.job.deferred", {"job": row["id"]})
                    connection.execute("UPDATE wake_jobs SET deferred=1 WHERE id=?", (row["id"],))
                continue
            created.append(work)
            skipped = math.floor((now - row["next_due"]) / row["interval_seconds"])
            next_due = row["next_due"] + (skipped + 1) * row["interval_seconds"]
            connection.execute(
                "UPDATE wake_jobs SET next_due=?,deferred=0 WHERE id=?", (next_due, row["id"])
            )
            MEMORY["record_event"](
                connection,
                "wake.job.enqueued",
                {"job": row["id"], "work": work, "coalesced": skipped},
            )
    return created


def watch(
    db,
    identifier: str,
    session: str,
    sku: str,
    *,
    channel: str = "local",
    recipient: str = "",
) -> None:
    """Register a stock condition on one product. Its scope and route never change."""
    if any(
        not isinstance(value, str) or not value.strip() or len(value) > 100
        for value in (identifier, session, sku)
    ):
        raise ValueError("bounded condition identity, session and product required")
    validate_route(channel, recipient)
    with db.immediate() as connection:
        if not connection.execute(
            "SELECT 1 FROM products p JOIN stock s ON s.sku = p.sku WHERE p.sku=?", (sku,)
        ).fetchone():
            raise ValueError("condition requires a known product with stock")
        if connection.execute(
            "SELECT 1 FROM stock_conditions WHERE subject=? AND enabled=1 AND id!=?",
            (sku, identifier),
        ).fetchone():
            raise ValueError("one active stock condition per product is allowed")
        previous = connection.execute(
            "SELECT * FROM stock_conditions WHERE id=?", (identifier,)
        ).fetchone()
        if previous:
            if (
                previous["session"],
                previous["subject"],
                previous["channel"],
                previous["recipient"],
            ) != (session, sku, channel, recipient):
                raise ValueError("condition identity already binds another scope or route")
            if not previous["enabled"]:
                connection.execute(
                    "UPDATE stock_conditions SET enabled=1,armed=1 WHERE id=?", (identifier,)
                )
        else:
            if connection.execute("SELECT count(*) FROM stock_conditions").fetchone()[0] >= 100:
                raise ValueError("teaching implementation supports at most 100 stock conditions")
            connection.execute(
                "INSERT INTO stock_conditions(id,session,subject,channel,recipient) "
                "VALUES (?,?,?,?,?)",
                (identifier, session, sku, channel, recipient),
            )


def unwatch(db, identifier: str) -> None:
    """Stop a condition; the work its episodes already admitted remains."""
    with db.immediate() as connection:
        if (
            connection.execute(
                "UPDATE stock_conditions SET enabled=0 WHERE id=?", (identifier,)
            ).rowcount
            != 1
        ):
            raise ValueError("unknown stock condition")


def scan(db, queue, *, now: float | None = None, maximum: int = 100) -> list[int]:
    """One condition pass: admit one piece of work per observed shortage episode."""
    now = time.time() if now is None else now
    if not math.isfinite(now) or type(maximum) is not int or not 1 <= maximum <= 100:
        raise ValueError("finite observation time and bounded scan required")
    emitted = []
    with db.immediate() as connection:
        if paused(connection):
            return []
        for condition in connection.execute(
            "SELECT * FROM stock_conditions WHERE enabled=1 ORDER BY id"
        ).fetchall():
            rows = stock_rows(connection, condition["subject"])
            if not rows:
                raise ValueError("condition inventory observation is unavailable")
            if rows[0]["needed"] == 0:
                connection.execute(
                    "UPDATE stock_conditions SET armed=1 WHERE id=?", (condition["id"],)
                )
                continue
            if not condition["armed"]:
                continue
            generation = condition["generation"] + 1
            work = admit(
                connection,
                queue,
                f"stock-condition:{condition['id']}:{generation}",
                condition["session"],
                f"Prepare a replenishment draft for {condition['subject']} from current stock. "
                "State USD amounts.",
                (condition["channel"], condition["recipient"]),
                subject=condition["subject"],
            )
            if work is None:
                continue  # The queue is full; leave this episode armed for a later pass.
            connection.execute(
                "UPDATE stock_conditions SET armed=0,generation=? WHERE id=?",
                (generation, condition["id"]),
            )
            MEMORY["record_event"](
                connection,
                "stock.condition.triggered",
                {
                    "condition": condition["id"],
                    "subject": condition["subject"],
                    "generation": generation,
                    "work": work,
                },
            )
            emitted.append(work)
            if len(emitted) >= maximum:
                break
    return emitted


def draft_report(messages: list[dict[str, Any]]) -> str | None:
    """Render latest successful draft estimates; model narration is not arithmetic."""
    names = {
        call["id"]: call["function"]["name"]
        for message in messages
        for call in message.get("tool_calls", [])
    }
    latest: dict[str, tuple[int, int]] = {}
    for message in messages:
        if message["role"] != "tool" or names.get(message["tool_call_id"]) != "draft_order":
            continue
        observation = json.loads(message["content"])
        if observation.get("ok") is not True:
            continue
        value = observation["value"]
        sku, quantity, amount = value.get("sku"), value.get("quantity"), value.get("total_cents")
        if (
            not isinstance(sku, str)
            or not 1 <= len(sku) <= 100
            or type(quantity) is not int
            or quantity <= 0
            or type(amount) is not int
            or amount < 0
            or value.get("currency") != "USD"
        ):
            raise ValueError("draft observation lacks validated quantity or USD amount")
        # Recalculating a draft is not creating another purchase. Display only
        # the latest estimate for each SKU.
        latest[sku] = (quantity, amount)
    if not latest:
        return None
    lines = ["Draft estimates:"]
    for sku, (quantity, amount) in sorted(latest.items()):
        label = json.dumps(sku, ensure_ascii=False)
        lines.append(f"- {label}: {quantity} tubs, ${amount // 100}.{amount % 100:02d} USD.")
    total = sum(amount for _, amount in latest.values())
    lines.append(f"Total: ${total // 100}.{total % 100:02d} USD.")
    return "\n".join(lines)


def run_next(db, queue, model, *, worker_id: str = "wake-worker") -> dict[str, Any] | None:
    """Claim the next eligible work and run one turn: the session's context, Chapter 3's loop over
    the tools its subject allows, and a report built from the draft observations.

    The raw transcript is kept beside the report; the model's own final sentence is kept in the
    transcript and Chapter 5's history, never used as the amounts Lucy reads."""
    assignment = CHANNEL["claim"](db, worker_id)
    if assignment is None:
        return None
    row = db.connection.execute(
        "SELECT subject FROM work_subjects WHERE work_id = ?", (assignment.work_id,)
    ).fetchone()
    subject = row[0] if row else None
    dispatcher = shop_tools(db, subject)
    revision = MEMORY["memory_revision"](db, assignment.session_id)
    messages = SKILLS["context"](
        db, assignment.session_id, assignment.text, allowed=dispatcher.allowed
    )
    result = LOOP["run_loop"](model, dispatcher, messages)
    report = draft_report(result.messages) if result.status == "COMPLETED" else None
    answer = report or result.answer or "The agent stopped: " + result.status
    with db.immediate() as connection:
        connection.execute(
            "INSERT INTO work_transcripts VALUES (?, ?, ?)",
            (assignment.work_id, result.status, json.dumps(result.messages)),
        )
    report_id = queue.finish(assignment, answer)
    MEMORY["record_result"](db, assignment.session_id, assignment.text, answer, revision)
    return {
        "work": assignment.work_id,
        "subject": subject,
        "status": result.status,
        "report": report_id,
        "answer": answer,
        "messages": result.messages,
    }


def serve(
    db,
    queue,
    model_factory,
    *,
    stop: threading.Event,
    interval: float = 1.0,
    worker_id: str = "wake-worker",
    bot=None,
    operators: frozenset[int] = frozenset(),
    log=print,
) -> None:
    """Tick, scan, run at most one item and deliver, until `stop` is set. Nobody prompts it.

    An idle pass calls no model. An expected failure waits with bounded exponential backoff and
    does not end the loop; work already admitted stays in the database either way. Work this
    worker label left running when a previous process stopped is finished with a report first."""
    for work_id in CHANNEL["release_interrupted"](db, queue, worker_id):
        log(f"work {work_id} interrupted by an earlier stop; reported")
    failures = 0
    while not stop.is_set():
        try:
            tick(db, queue)
            scan(db, queue)
            ran = run_next(db, queue, model_factory(), worker_id=worker_id)
            if ran is not None:
                log(f"work {ran['work']} finished: {ran['status']}")
            if bot is not None:
                while (outcome := CHANNEL["deliver_one"](db, bot, operators)) is not None:
                    log(f"delivery: {outcome}")
            failures = 0
        except (OSError, ValueError, sqlite3.Error, STORE["StoreError"]) as error:
            failures += 1
            ran = None
            log(f"pass failed ({type(error).__name__}); waiting before the next pass")
        stop.wait(min(60.0, interval * 2**failures) if failures else (0 if ran else interval))


def model_from(args):
    """A factory for the model each turn uses, and the Claude connection whose spend is reported,
    if any: the offline fixture, the local HTTP model, or Claude. The Claude key is read from the
    environment or a `.env` file, never from an argument."""
    if args.claude:
        claude = runpy.run_path(
            str(LEARNER.parent / "experiments/profrod_sovereign_agent_claude_messages_v1.py")
        )
        client = claude["Claude"](max_usd=args.max_usd)
        return (
            lambda: claude["LoopModel"](client, args.claude, LOOP["ModelTurn"], LOOP["ToolCall"]),
            client,
        )
    if args.live:
        return lambda: LOOP["HTTPModel"](model=args.model, reasoning_effort="none"), None
    return SKILLS["OfflineShopModel"], None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    serving = commands.add_parser("serve", help="serve a prepared database until stopped")
    serving.add_argument("--root", type=Path, required=True, help="folder holding agent.sqlite")
    serving.add_argument("--interval", type=float, default=1.0, help="seconds between idle passes")
    choice = serving.add_mutually_exclusive_group()
    choice.add_argument("--live", action="store_true", help="use the local HTTP model")
    choice.add_argument(
        "--claude", metavar="MODEL", help="use Claude, e.g. claude-haiku-4-5-20251001"
    )
    serving.add_argument("--model", default="qwen3", help="the local model's name")
    serving.add_argument("--max-usd", type=float, default=1.0, help="Claude spending ceiling")
    args = parser.parse_args(argv)
    path = args.root / "agent.sqlite"
    if not path.is_file():
        raise SystemExit("no prepared database at " + str(path))
    db, queue = open_shop(path)
    token = CHANNEL["secret"]("SOVEREIGN_AGENT_TELEGRAM_TOKEN")
    operators = frozenset(
        int(value) for value in CHANNEL["secret"]("SOVEREIGN_AGENT_OPERATORS").split(",") if value
    )
    bot = CHANNEL["Telegram"](token) if token and operators else None
    factory, client = model_from(args)
    stop = threading.Event()
    for name in ("SIGTERM", "SIGINT"):
        signal.signal(getattr(signal, name), lambda *_: stop.set())
    print("SERVING", flush=True)
    try:
        serve(
            db,
            queue,
            factory,
            stop=stop,
            interval=args.interval,
            bot=bot,
            operators=operators,
            log=lambda line: print(line, flush=True),
        )
    finally:
        db.close()
        if client is not None:
            # Model id, tokens and list-price cost only.
            print("CLAUDE " + json.dumps(client.report()), flush=True)
    print("STOPPED", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
