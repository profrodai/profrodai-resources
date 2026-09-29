# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 13's worker recovery: leases with generations, fenced writes, and a recovery turn.

It upgrades the queue the earlier chapters built. Chapter 8's queue admits work, Chapter 11's
lease records who holds it, and this file adds a generation to each acquisition. The worker
identity written on the work row is the owner and its generation together, so every check
Chapter 11 already makes against that identity becomes a generation fence, even when a restarted
process reuses its owner label.
"""

import json
import math
import runpy
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

APPROVAL = runpy.run_path(
    str(Path(__file__).with_name("profrod_sovereign_agent_ch11_approval_learner.py"))
)
execute = APPROVAL["execute"]

LEASE_MIGRATIONS = {
    1: (
        "ALTER TABLE assignment_leases ADD COLUMN generation INTEGER NOT NULL DEFAULT 1",
        "CREATE TABLE transcript ("
        " seq INTEGER PRIMARY KEY AUTOINCREMENT, work_id INTEGER NOT NULL,"
        " generation INTEGER NOT NULL, message TEXT NOT NULL)",
        "CREATE TABLE outcomes ("
        " work_id INTEGER PRIMARY KEY, generation INTEGER NOT NULL,"
        " status TEXT NOT NULL CHECK (status IN ('DONE', 'BLOCKED', 'CANCELED')),"
        " result TEXT NOT NULL)",
    ),
}


def open_worker_shop(path):
    """Chapter 11's shop and queue, with leases that carry a generation."""
    db, queue = APPROVAL["open_shop"](path)
    db.migrate("leases", LEASE_MIGRATIONS)
    return db, queue


@dataclass(frozen=True)
class Claim:
    """What a worker must present to write: which work, which acquisition, and until when."""

    work_id: int
    session_id: str
    text: str
    owner: str
    generation: int
    expires: float

    @property
    def worker_id(self) -> str:
        # The identity Chapters 8 and 11 check: an owner label plus the acquisition it made.
        return f"{self.owner}#{self.generation}"


def enqueue(queue, source_id: str, session_id: str, text: str) -> int:
    """Admit work through Chapter 8's queue and return its id."""
    if queue.admit(source_id, session_id, text) not in {"accepted", "duplicate"}:
        raise ValueError("work was not admitted")
    return queue.store.connection.execute(
        "SELECT work_id FROM work WHERE source_id=?", (source_id,)
    ).fetchone()[0]


def claim(db, owner: str, *, ttl: float = 90, now: float | None = None) -> Claim | None:
    """Acquire the oldest work that is pending, or running under an expired lease, in one
    transaction. A session with another live holder is skipped, so its turns stay in order."""
    now = time.time() if now is None else now
    if not owner or "#" in owner or not math.isfinite(ttl) or not 0 < ttl <= 3600:
        raise ValueError("an owner label and a bounded lease are required")
    with db.immediate() as connection:
        row = connection.execute(
            "SELECT w.work_id, w.session_id, w.text, w.state, coalesce(l.generation, 0)"
            " FROM work w LEFT JOIN assignment_leases l ON l.work_id = w.work_id"
            " WHERE (w.state = 'pending' OR (w.state = 'running' AND l.expires <= ?))"
            " AND NOT EXISTS (SELECT 1 FROM work other"
            "   JOIN assignment_leases ol ON ol.work_id = other.work_id"
            "   WHERE other.session_id = w.session_id AND other.state = 'running'"
            "   AND ol.expires > ?)"
            " ORDER BY w.work_id LIMIT 1",
            (now, now),
        ).fetchone()
        if row is None:
            return None
        work_id, session_id, text, state, previous = row
        held = Claim(work_id, session_id, text, owner, previous + 1, now + ttl)
        if state == "pending":
            connection.execute(
                "UPDATE work SET state = 'running', worker_id = ? WHERE work_id = ?",
                (held.worker_id, work_id),
            )
        else:
            connection.execute(
                "UPDATE work SET worker_id = ? WHERE work_id = ?", (held.worker_id, work_id)
            )
        connection.execute(
            "INSERT INTO assignment_leases (work_id, worker_id, expires, generation)"
            " VALUES (?, ?, ?, ?) ON CONFLICT (work_id) DO UPDATE SET"
            " worker_id = excluded.worker_id, expires = excluded.expires,"
            " generation = excluded.generation",
            (work_id, held.worker_id, held.expires, held.generation),
        )
    return held


def assert_current(connection, held: Claim, now: float | None = None) -> float:
    """Refuse unless this acquisition is still the current, unexpired holder; return expiry."""
    now = time.time() if now is None else now
    row = connection.execute(
        "SELECT w.state, w.worker_id, l.generation, l.expires FROM work w"
        " JOIN assignment_leases l ON l.work_id = w.work_id WHERE w.work_id = ?",
        (held.work_id,),
    ).fetchone()
    if (
        row is None
        or row[0] != "running"
        or row[1] != held.worker_id
        or row[2] != held.generation
        or row[3] <= now
    ):
        raise PermissionError("worker claim expired or superseded")
    return row[3]


def observe(db, held: Claim, message: dict[str, Any]) -> None:
    """Append one transcript message, attributed to the generation that produced it."""
    with db.immediate() as connection:
        assert_current(connection, held)
        connection.execute(
            "INSERT INTO transcript (work_id, generation, message) VALUES (?, ?, ?)",
            (held.work_id, held.generation, json.dumps(message, allow_nan=False)),
        )


def finish(db, held: Claim, status: str, result: str) -> None:
    """Only the current holder may end the work and record its outcome."""
    if status not in {"DONE", "BLOCKED", "CANCELED"}:
        raise ValueError("invalid terminal work state")
    with db.immediate() as connection:
        assert_current(connection, held)
        connection.execute("UPDATE work SET state = 'finished' WHERE work_id = ?", (held.work_id,))
        connection.execute(
            "INSERT INTO outcomes (work_id, generation, status, result) VALUES (?, ?, ?, ?)",
            (held.work_id, held.generation, status, result),
        )


def recover_once(db, *, owner: str, supplier, policy, ttl: float = 30) -> dict[str, Any]:
    """Take over expired or waiting work and continue only what is already recorded.

    This turn has no model. If the work holds an approved or uncertain order, it continues that
    exact order through Chapter 11's send check. Anything else needs a new turn with a model,
    and is left blocked rather than guessed at.
    """
    held = claim(db, owner, ttl=ttl)
    if held is None:
        return {"status": "IDLE"}
    orders = [
        row[0]
        for row in db.connection.execute(
            "SELECT id FROM assistant_orders WHERE work_id = ?"
            " AND status IN ('APPROVED', 'SENDING', 'UNKNOWN') ORDER BY created, id",
            (held.work_id,),
        )
    ]
    if not orders:
        finish(db, held, "BLOCKED", "No recorded approval to continue; a new turn is needed.")
        return {"status": "BLOCKED", "work": held.work_id, "generation": held.generation}
    receipts = [execute(db, held, order, supplier, policy=policy) for order in orders]
    if all(receipt.get("status") in {"ACCEPTED", "REJECTED"} for receipt in receipts):
        pairs = zip(orders, receipts, strict=True)
        summary = ", ".join(f"{order}: {receipt['status']}" for order, receipt in pairs)
        finish(db, held, "DONE", "Continued the approved orders. " + summary)
        return {"status": "DONE", "work": held.work_id, "generation": held.generation}
    finish(db, held, "BLOCKED", "An order's outcome is uncertain; discover it before retrying.")
    return {"status": "BLOCKED", "work": held.work_id, "generation": held.generation}
