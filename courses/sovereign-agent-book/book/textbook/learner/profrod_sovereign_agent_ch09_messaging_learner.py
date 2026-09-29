# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 9's phone channel: Telegram intake and delivery on the learner's own queue.

Every piece underneath is earlier learner code. Chapter 3's killable transport carries the Bot API
calls. Chapter 8's queue holds the work and its reports, and its report states carry delivery.
Chapter 7's context, with Chapter 5's memory, gives each turn its session's preferences and active
skills, and Chapter 3's loop runs it. This file adds what a phone needs: an allowlisted private
intake whose batch and cursor commit together, a claim that serializes a session's turns, and a
delivery that knows its recipient and never resends a report whose outcome is unknown.
"""

import json
import re
import runpy
import time
import uuid
from pathlib import Path
from typing import Any, Protocol

LEARNER = Path(__file__).resolve().parent
SKILLS = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch07_skills_learner.py"))
QUEUE = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch08_work_queue_learner.py"))
TRANSPORT = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch03_http_transport_learner.py"))
MEMORY, LOOP = SKILLS["MEMORY"], SKILLS["LOOP"]
TOOLS, Assignment = LOOP["shop_tools"], QUEUE["Assignment"]

CHANNEL_MIGRATIONS = {
    1: (
        # One inbound cursor and one live poller per bot account.
        "CREATE TABLE channel_cursor (channel TEXT PRIMARY KEY, offset INTEGER NOT NULL)",
        "CREATE TABLE channel_leases ("
        " channel TEXT PRIMARY KEY, owner TEXT NOT NULL, expires REAL NOT NULL)",
        # Where each piece of work came from, so its reports go back there and nowhere else.
        "CREATE TABLE channel_routes ("
        " work_id INTEGER PRIMARY KEY, channel TEXT NOT NULL, recipient TEXT NOT NULL)",
        # A report whose recipient left the allowlist before it was sent. It is never sent.
        "CREATE TABLE report_denials ("
        " report_id TEXT PRIMARY KEY, recipient TEXT NOT NULL, created REAL NOT NULL)",
    ),
}


class Record(tuple):
    """A row that compares as a tuple, as Chapter 8's queue expects, and reads by column name,
    as Chapter 5's memory expects, including dict(row)."""

    names: tuple[str, ...] = ()

    def __getitem__(self, key):
        return super().__getitem__(self.names.index(key) if isinstance(key, str) else key)

    def keys(self):
        return self.names


def named_rows(cursor, values):
    record = Record(values)
    record.names = tuple(column[0] for column in cursor.description)
    return record


def open_channel(path: str | Path, *, capacity: int = 10):
    """Chapter 7's store of memory and skills, Chapter 8's queue, and the channel's own tables."""
    db = SKILLS["open_skills"](path)
    queue = QUEUE["WorkQueue"](db, capacity=capacity)
    db.migrate("channel", CHANNEL_MIGRATIONS)
    db.connection.row_factory = named_rows
    return db, queue


class Bot(Protocol):
    account: str

    def call(self, method: str, data: dict[str, Any]) -> Any: ...


class Telegram:
    """The two Bot API operations this agent uses, over Chapter 3's killable transport."""

    def __init__(self, token: str) -> None:
        if not re.fullmatch(r"[0-9]+:[a-zA-Z0-9_-]+", token):
            raise ValueError("invalid Telegram credential format")
        self._token = token
        self.account = token.split(":", 1)[0]

    def call(self, method: str, data: dict[str, Any]) -> Any:
        if method not in {"getUpdates", "sendMessage"}:
            raise ValueError("unsupported Telegram operation")
        try:
            response = TRANSPORT["request"](
                "https://api.telegram.org/bot" + self._token + "/" + method,
                data=json.dumps(data).encode(),
                headers={"Content-Type": "application/json"},
                timeout=35,
            )
            if response.status != 200:
                raise OSError("Telegram declined operation")
            result = json.loads(response.body)
            if not isinstance(result, dict) or result.get("ok") is not True:
                raise ValueError("Telegram declined operation")
            return result["result"]
        except OSError, ValueError, KeyError, TypeError:
            # API URLs contain the token. Never expose exception URLs or bodies.
            raise OSError("Telegram request failed; inspect connectivity and credentials") from None


def check_operators(operators: frozenset[int]) -> None:
    if not operators or any(type(actor) is not int or actor <= 0 for actor in operators):
        raise ValueError("explicit numeric operator allowlist required")


def allowed_text(message: Any, operators: frozenset[int]) -> tuple[int, str] | None:
    """The sender and text of a private message from an allowlisted person, or None to ignore.
    A malformed message raises instead: the whole batch is then refused, cursor and all."""
    if not isinstance(message, dict):
        raise ValueError("invalid Telegram message object")
    sender, chat = message.get("from", {}), message.get("chat", {})
    if not isinstance(sender, dict) or not isinstance(chat, dict):
        raise ValueError("invalid Telegram sender or chat object")
    actor, text = sender.get("id"), message.get("text")
    if (
        type(actor) is int
        and actor in operators
        and chat.get("type") == "private"
        and type(chat.get("id")) is int
        and chat.get("id") == actor
        and not sender.get("is_bot")
        and isinstance(text, str)
        and text.strip()
        and len(text.encode()) <= 16_384
    ):
        return actor, text
    return None


def admit_message(connection, queue, source_id: str, session_id: str, text: str, route):
    """Chapter 8's admission, inside the caller's transaction, with the message's route.

    Returns (work_id, new). A known source with the same content is a duplicate; with other
    content it is refused. Over capacity, the request is recorded as finished work whose report
    tells the sender, rather than silently dropped."""
    row = connection.execute(
        "SELECT work_id, session_id, text FROM work WHERE source_id = ?", (source_id,)
    ).fetchone()
    if row is not None:
        if (row[1], row[2]) != (session_id, text):
            raise ValueError("intake identity reused for different content")
        return row[0], False
    (open_work,) = connection.execute(
        "SELECT COUNT(*) FROM work WHERE state IN ('pending', 'running')"
    ).fetchone()
    full = open_work >= queue.capacity
    work_id = connection.execute(
        "INSERT INTO work (source_id, session_id, text, state) VALUES (?, ?, ?, ?)",
        (source_id, session_id, text, "finished" if full else "pending"),
    ).lastrowid
    connection.execute("INSERT INTO channel_routes VALUES (?, ?, ?)", (work_id, *route))
    if full:
        connection.execute(
            "INSERT INTO reports (report_id, work_id, generation, body, delivery)"
            " VALUES (?, ?, 1, ?, 'pending')",
            (f"r{work_id}.1", work_id, "The queue is full; nothing was started. Try again later."),
        )
    return work_id, True


def poll(db, queue, bot: Bot, operators: frozenset[int]) -> list[int]:
    """One bounded poll. Returns the newly admitted work ids; the queue, not this list, is
    the durable record."""
    check_operators(operators)
    channel = "telegram:" + bot.account
    owner = uuid.uuid4().hex
    with db.immediate() as connection:
        lease = connection.execute(
            "SELECT expires FROM channel_leases WHERE channel=?", (channel,)
        ).fetchone()
        if lease and lease[0] > time.time():
            raise PermissionError("another poller owns this bot account")
        connection.execute(
            "INSERT INTO channel_leases(channel,owner,expires) VALUES (?,?,?) "
            "ON CONFLICT(channel) DO UPDATE SET owner=excluded.owner,expires=excluded.expires",
            (channel, owner, time.time() + 40),
        )
    try:
        return _poll_owned(db, queue, bot, operators, channel, owner)
    finally:
        with db.immediate() as connection:
            connection.execute(
                "DELETE FROM channel_leases WHERE channel=? AND owner=?", (channel, owner)
            )


def _poll_owned(db, queue, bot, operators, channel: str, owner: str) -> list[int]:
    cursor = db.connection.execute(
        "SELECT offset FROM channel_cursor WHERE channel=?", (channel,)
    ).fetchone()
    offset = cursor[0] if cursor else 0
    updates = bot.call(
        "getUpdates",
        {"offset": offset, "limit": 100, "timeout": 20, "allowed_updates": ["message"]},
    )
    if not isinstance(updates, list) or len(updates) > 100:
        raise ValueError("invalid Telegram update batch")
    admitted = []
    with db.immediate() as connection:
        current = connection.execute(
            "SELECT 1 FROM channel_leases WHERE channel=? AND owner=? AND expires>?",
            (channel, owner, time.time()),
        ).fetchone()
        if not current:
            raise PermissionError("poller claim expired")
        highest = offset - 1
        for update in updates:
            if not isinstance(update, dict):
                raise ValueError("invalid Telegram update object")
            update_id = update.get("update_id")
            if type(update_id) is not int or update_id < 0:
                raise ValueError("invalid update identity")
            # Do not skip an earlier member of an unordered batch. The cursor is published only
            # after every member has been considered, in the same transaction as the work.
            highest = max(highest, update_id)
            allowed = allowed_text(update.get("message", {}), operators)
            if allowed is None:
                continue
            actor, text = allowed
            session = f"{channel}:{actor}"
            work_id, new = admit_message(
                connection, queue, f"{channel}:{update_id}", session, text, (channel, str(actor))
            )
            if new:
                admitted.append(work_id)
        connection.execute(
            "INSERT INTO channel_cursor(channel,offset) VALUES (?,?) "
            "ON CONFLICT(channel) DO UPDATE SET offset=excluded.offset",
            (channel, max(offset, highest + 1)),
        )
    return admitted


def claim(db, worker_id: str, *, work_id: int | None = None) -> Any:
    """Chapter 8's claim, with one more rule: a session with a running turn waits.

    Two turns of one conversation must not assemble context from the same unfinished history.
    Chapter 13 adds leases, so a crashed holder does not block its session forever."""
    with db.immediate() as connection:
        row = connection.execute(
            "SELECT w.work_id, w.session_id, w.text FROM work w"
            " WHERE w.state = 'pending' AND (? IS NULL OR w.work_id = ?)"
            " AND NOT EXISTS (SELECT 1 FROM work other"
            "   WHERE other.session_id = w.session_id AND other.state = 'running')"
            " ORDER BY w.work_id LIMIT 1",
            (work_id, work_id),
        ).fetchone()
        if row is None:
            return None
        connection.execute(
            "UPDATE work SET state = 'running', worker_id = ? WHERE work_id = ?",
            (worker_id, row[0]),
        )
    return Assignment(row[0], row[1], row[2], worker_id)


def run_claim(db, queue, assignment, model) -> tuple[bool, Any]:
    """One turn: the session's context, Chapter 3's loop over the shop tools, and a report.

    The finished result also enters Chapter 5's history, under the memory revision the turn
    started with, so a later turn in the same session can see it and a forget can exclude it."""
    revision = MEMORY["memory_revision"](db, assignment.session_id)
    dispatcher = TOOLS["build_tools"](TOOLS["SHOP"])
    messages = SKILLS["context"](
        db, assignment.session_id, assignment.text, allowed=dispatcher.allowed
    )
    result = LOOP["run_loop"](model, dispatcher, messages)
    passed = result.status == "COMPLETED" and LOOP["draft_evidence"](result)
    answer = result.answer or "The agent stopped: " + result.status
    queue.finish(assignment, answer)
    MEMORY["record_result"](db, assignment.session_id, assignment.text, answer, revision)
    return passed, result


def deliver_one(db, bot: Bot, operators: frozenset[int]) -> str | None:
    """Chapter 8's send_one, with a destination and an allowlist.

    Sends this bot's oldest pending report to the recipient its work came from, once. The
    recipient must still be allowed; if not, the report is denied and never sent. "sending" is
    committed before the call. A valid message id confirms it; anything else leaves it "unknown",
    which this function never picks up again. Returns "confirmed", "unknown", "denied" or None."""
    check_operators(operators)
    channel = "telegram:" + bot.account
    with db.immediate() as connection:
        row = connection.execute(
            "SELECT r.report_id, r.body, c.recipient FROM reports r"
            " JOIN channel_routes c ON c.work_id = r.work_id"
            " WHERE c.channel = ? AND r.delivery = 'pending'"
            " AND r.report_id NOT IN (SELECT report_id FROM report_denials)"
            " ORDER BY r.work_id, r.generation LIMIT 1",
            (channel,),
        ).fetchone()
        if row is None:
            return None
        report_id, body, recipient = row
        if not recipient.isdigit() or int(recipient) not in operators:
            connection.execute(
                "INSERT INTO report_denials VALUES (?, ?, ?)", (report_id, recipient, time.time())
            )
            return "denied"
        # A crash after this commit is ambiguous, even if no HTTP call happened.
        connection.execute(
            "UPDATE reports SET delivery = 'sending' WHERE report_id = ?", (report_id,)
        )
    try:
        text = body if len(body) <= 3900 else body[:3800] + "\n[Report truncated.]"
        result = bot.call("sendMessage", {"chat_id": int(recipient), "text": text})
        if (
            not isinstance(result, dict)
            or type(result.get("message_id")) is not int
            or result["message_id"] <= 0
        ):
            raise ValueError("missing delivery receipt")
        outcome, receipt = "confirmed", json.dumps({"message_id": result["message_id"]})
    except OSError, ValueError:
        outcome, receipt = "unknown", None
    with db.immediate() as connection:
        updated = connection.execute(
            "UPDATE reports SET delivery = ?, receipt = ? WHERE report_id = ?"
            " AND delivery = 'sending'",
            (outcome, receipt, report_id),
        )
        if not updated.rowcount:
            return "unknown"
    return outcome


def activate_opening_skill(db) -> None:
    """Stage the repository's opening procedure and activate it through Chapter 7's evaluation."""
    if SKILLS["skill_snapshot"](db)[1]:
        return
    source = LEARNER.parent / "skills" / "profrod_sovereign_agent_textbook_opening_check_v1.toml"
    candidate = SKILLS["stage_skill"](db, source)
    SKILLS["activate_skill"](
        db,
        candidate.name,
        candidate.version,
        evaluate=lambda skill: SKILLS["evaluate_opening"](SKILLS["OfflineShopModel"], skill),
        required_cases=frozenset(case.name for case in SKILLS["OPENING_CASES"]),
    )
