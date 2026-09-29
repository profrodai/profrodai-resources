# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 11's spending permission: exact proposals, approvals, reservations and the send check.

Everything sits on earlier chapters' code: the Chapter 4 store holds the stock and every table
here, the Chapter 8 queue supplies the assignment a proposal belongs to, and Chapter 1's catalog
and Chapter 2's prices say what a tub costs. Orders get their own line of versions, "orders".
"""

import hashlib
import json
import math
import runpy
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LEARNER = Path(__file__).resolve().parent
STORE = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch04_state_store_learner.py"))
QUEUE = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch08_work_queue_learner.py"))
TOOLS = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch02_pydantic_shop_tools_learner.py"))
StateStore, StockEvent, WorkQueue = STORE["StateStore"], STORE["StockEvent"], QUEUE["WorkQueue"]
CATALOG = {row["sku"]: row for row in TOOLS["SHOP"]["products"]}
PRICES = TOOLS["PRICES"]

ORDER_MIGRATIONS = {
    1: (
        "CREATE TABLE assistant_orders ("
        " id TEXT PRIMARY KEY, work_id INTEGER NOT NULL, proposal TEXT NOT NULL,"
        " digest TEXT NOT NULL, amount INTEGER NOT NULL CHECK (amount > 0),"
        " target TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'DRAFT',"
        " approved_by TEXT, approved_until REAL,"
        " approval_basis TEXT NOT NULL DEFAULT 'UNKNOWN'"
        " CHECK (approval_basis IN ('UNKNOWN', 'OPERATOR', 'AUTOMATIC')),"
        " revoked INTEGER NOT NULL DEFAULT 0, receipt TEXT, created REAL NOT NULL)",
        # An approved proposal can never be edited into a different purchase.
        "CREATE TRIGGER assistant_order_identity_fixed"
        " BEFORE UPDATE OF id, work_id, proposal, digest, amount, target ON assistant_orders"
        " BEGIN SELECT RAISE(ABORT, 'order identity is immutable'); END",
        "CREATE TABLE assistant_spending ("
        " id INTEGER PRIMARY KEY CHECK (id = 1), limit_cents INTEGER NOT NULL,"
        " reserved_cents INTEGER NOT NULL DEFAULT 0, spent_cents INTEGER NOT NULL DEFAULT 0)",
        # Who owns an assignment, and until when. Chapter 13 replaces workers; here a lease is
        # what lets the send check ask whether this worker still owns the order's assignment.
        "CREATE TABLE assignment_leases ("
        " work_id INTEGER PRIMARY KEY, worker_id TEXT NOT NULL, expires REAL NOT NULL)",
        "CREATE TABLE order_events ("
        " seq INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, payload TEXT NOT NULL,"
        " created REAL NOT NULL)",
    ),
}


class Record(tuple):
    """A row that still compares as a tuple, so Chapter 4 and 8 code keeps working, and that
    also reads by column name, which the order checks below need."""

    names: tuple[str, ...] = ()

    def __getitem__(self, key):
        return super().__getitem__(self.names.index(key) if isinstance(key, str) else key)


def named_rows(cursor, values):
    record = Record(values)
    record.names = tuple(column[0] for column in cursor.description)
    return record


def open_shop(path: str | Path):
    """Lucy's store: Chapter 4's stock seeded once, the work queue, and the order tables."""
    db = StateStore(path)
    db.initialize()
    for sku, product in CATALOG.items():
        # An event id per product: reopening the shop is a duplicate, never a second delivery.
        db.apply(StockEvent(f"opening:{sku}", sku, product["on_hand"], "opening count"))
    queue = WorkQueue(db)
    db.migrate("orders", ORDER_MIGRATIONS)
    db.connection.row_factory = named_rows
    return db, queue


def record_event(connection, kind: str, payload: dict[str, Any]) -> None:
    connection.execute(
        "INSERT INTO order_events(kind, payload, created) VALUES (?, ?, ?)",
        (kind, json.dumps(payload, sort_keys=True), time.time()),
    )


def hold(db, assignment, *, seconds: float = 300) -> None:
    """Record how long this worker owns the assignment it just claimed."""
    with db.immediate() as connection:
        connection.execute(
            "INSERT INTO assignment_leases VALUES (?, ?, ?)"
            " ON CONFLICT (work_id) DO UPDATE SET worker_id=excluded.worker_id,"
            " expires=excluded.expires",
            (assignment.work_id, assignment.worker_id, time.time() + seconds),
        )


def assert_current(connection, assignment) -> float:
    """Refuse unless this worker still runs the assignment and its lease holds; return expiry."""
    row = connection.execute(
        "SELECT w.state, w.worker_id, l.expires FROM work w"
        " JOIN assignment_leases l ON l.work_id = w.work_id WHERE w.work_id = ?",
        (assignment.work_id,),
    ).fetchone()
    if (
        row is None
        or row[0] != "running"
        or row[1] != assignment.worker_id
        or row[2] <= time.time()
    ):
        raise PermissionError("this worker no longer owns the assignment")
    return row[2]


@dataclass(frozen=True)
class SpendingPolicy:
    operators: frozenset[str]
    total_cents: int = 20_000
    automatic_order_cents: int = 0

    def __post_init__(self) -> None:
        if not self.operators or type(self.total_cents) is not int or self.total_cents <= 0:
            raise ValueError("operators and positive spending ceiling required")
        if (
            type(self.automatic_order_cents) is not int
            or not 0 <= self.automatic_order_cents <= self.total_cents
        ):
            raise ValueError("automatic allowance must fit the total ceiling")


def propose(db, assignment, sku: str, quantity: int, *, target: str = "lucy-local") -> str:
    if type(quantity) is not int or not 1 <= quantity <= 1000:
        raise ValueError("positive integral bounded quantity required")
    with db.immediate() as connection:
        assert_current(connection, assignment)
        cost = PRICES.get(sku)
        if type(cost) is not int or cost <= 0:
            raise ValueError("unknown product or invalid authoritative price")
        proposal = {
            "sku": sku,
            "quantity": quantity,
            "unit_cost_cents": cost,
            "supplier": "lucy-local",
            "currency": "USD",
        }
        encoded = json.dumps(proposal, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256((target + "\n" + encoded).encode()).hexdigest()
        # One stable intent for this exact proposal in this assignment.
        identifier = uuid.uuid5(uuid.NAMESPACE_URL, f"{assignment.work_id}:{digest}").hex
        if connection.execute(
            "SELECT 1 FROM assistant_orders WHERE id=?", (identifier,)
        ).fetchone():
            return identifier  # Repeating an old revision never resurrects its authority.
        previous = connection.execute(
            "SELECT id,status,amount FROM assistant_orders "
            "WHERE work_id=? AND json_extract(proposal,'$.sku')=?",
            (assignment.work_id, sku),
        ).fetchall()
        if any(row["status"] in {"SENDING", "UNKNOWN", "CONFIRMED"} for row in previous):
            raise PermissionError(
                "existing product effect must be resolved; new purchase needs new work"
            )
        for row in previous:
            if row["status"] not in {"DRAFT", "APPROVED"}:
                continue
            if row["status"] == "APPROVED":
                connection.execute(
                    "UPDATE assistant_spending SET reserved_cents=reserved_cents-? WHERE id=1",
                    (row["amount"],),
                )
            connection.execute(
                "UPDATE assistant_orders SET status='REVOKED',revoked=1 WHERE id=?", (row["id"],)
            )
            record_event(
                connection,
                "assistant.order.superseded",
                {"order": row["id"], "replacement": identifier},
            )
        connection.execute(
            "INSERT INTO assistant_orders(id,work_id,proposal,digest,amount,target,created) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                identifier,
                assignment.work_id,
                encoded,
                digest,
                quantity * cost,
                target,
                time.time(),
            ),
        )
        return identifier


def approve(
    db,
    identifier: str,
    digest: str,
    *,
    actor: str,
    policy: SpendingPolicy,
    expires: float,
    automatic: bool = False,
    now: float | None = None,
) -> None:
    now = time.time() if now is None else now
    if type(automatic) is not bool:
        raise ValueError("approval basis must be explicit")
    if not math.isfinite(expires) or not now < expires <= now + 86400:
        raise ValueError("approval must expire within one day")
    if actor not in policy.operators:
        raise PermissionError("operator is not allowlisted")
    with db.immediate() as connection:
        order = connection.execute(
            "SELECT * FROM assistant_orders WHERE id=?", (identifier,)
        ).fetchone()
        if (
            order is None
            or order["digest"] != digest
            or order["status"] not in {"DRAFT", "APPROVED"}
            or order["revoked"]
        ):
            raise PermissionError("approval does not match an eligible exact proposal")
        if automatic and order["amount"] > policy.automatic_order_cents:
            raise PermissionError("exact proposal needs operator approval")
        connection.execute(
            "INSERT OR IGNORE INTO assistant_spending(id,limit_cents) VALUES (1,?)",
            (policy.total_cents,),
        )
        budget = connection.execute("SELECT * FROM assistant_spending WHERE id=1").fetchone()
        addition = order["amount"] if order["status"] == "DRAFT" else 0
        # A supplied policy cannot silently raise the installed account ceiling.
        if budget["spent_cents"] + budget["reserved_cents"] + addition > min(
            budget["limit_cents"], policy.total_cents
        ):
            raise PermissionError("cumulative spending ceiling reached")
        connection.execute(
            "UPDATE assistant_spending SET reserved_cents=reserved_cents+? WHERE id=1", (addition,)
        )
        connection.execute(
            "UPDATE assistant_orders SET status='APPROVED',approved_by=?,approved_until=?,"
            "approval_basis=? WHERE id=?",
            (actor, expires, "AUTOMATIC" if automatic else "OPERATOR", identifier),
        )
        record_event(
            connection,
            "assistant.order.approved",
            {"order": identifier, "digest": digest, "actor": actor, "automatic": automatic},
        )


def revoke(db, identifier: str, *, actor: str, policy: SpendingPolicy) -> None:
    if actor not in policy.operators:
        raise PermissionError("operator is not allowlisted")
    with db.immediate() as connection:
        row = connection.execute(
            "SELECT * FROM assistant_orders WHERE id=?", (identifier,)
        ).fetchone()
        if row is None or row["revoked"]:
            return
        # In-flight/unknown reservations remain held until the supplier resolves them.
        if row["status"] == "APPROVED":
            connection.execute(
                "UPDATE assistant_spending SET reserved_cents=reserved_cents-? WHERE id=1",
                (row["amount"],),
            )
            connection.execute(
                "UPDATE assistant_orders SET status='REVOKED' WHERE id=?", (identifier,)
            )
        connection.execute(
            "UPDATE assistant_orders SET revoked=1,status=CASE WHEN status='DRAFT' "
            "THEN 'REVOKED' ELSE status END WHERE id=?",
            (identifier,),
        )
        record_event(connection, "assistant.order.revoked", {"order": identifier, "actor": actor})


def record_receipt(db, assignment, identifier: str, receipt: dict[str, Any]) -> dict[str, Any]:
    """Settle a conclusive supplier answer: spent on acceptance, released on rejection.

    Chapter 12 handles the answers that are not conclusive; here a receipt must name this exact
    operation and proposal, or it is refused.
    """
    with db.immediate() as connection:
        assert_current(connection, assignment)
        row = connection.execute(
            "SELECT * FROM assistant_orders WHERE id=? AND work_id=?",
            (identifier, assignment.work_id),
        ).fetchone()
        stated = json.dumps(receipt.get("proposal"), sort_keys=True, separators=(",", ":"))
        if row is None or receipt.get("operation") != identifier or stated != row["proposal"]:
            raise ValueError("supplier receipt does not match the exact intent")
        if receipt.get("status") not in {"ACCEPTED", "REJECTED"}:
            raise ValueError("supplier outcome is not conclusive")
        if row["status"] in {"CONFIRMED", "REJECTED"}:
            return dict(json.loads(row["receipt"]))
        if row["status"] not in {"SENDING", "UNKNOWN"}:
            raise PermissionError("order was not admitted for transmission")
        accepted = receipt["status"] == "ACCEPTED"
        connection.execute(
            "UPDATE assistant_orders SET status=?,receipt=? WHERE id=?",
            ("CONFIRMED" if accepted else "REJECTED", json.dumps(receipt), identifier),
        )
        connection.execute(
            "UPDATE assistant_spending SET reserved_cents=reserved_cents-?,"
            "spent_cents=spent_cents+? WHERE id=1",
            (row["amount"], row["amount"] if accepted else 0),
        )
        settled = {"order": identifier, "status": receipt["status"]}
        record_event(connection, "assistant.order.settled", settled)
    return receipt


def execute(db, assignment, identifier: str, supplier, *, policy: SpendingPolicy) -> dict:
    """Admit a supplier request only after checking current authority, then send it once."""
    row = db.connection.execute(
        "SELECT * FROM assistant_orders WHERE id=? AND work_id=?", (identifier, assignment.work_id)
    ).fetchone()
    if row is None:
        raise PermissionError("order belongs to another work item")
    assert_current(db.connection, assignment)
    if row["target"] != supplier.identity:
        raise PermissionError("supplier destination differs from the approved proposal")
    if row["status"] in {"CONFIRMED", "REJECTED"}:
        return dict(json.loads(row["receipt"]))
    if row["status"] in {"SENDING", "UNKNOWN"}:
        try:
            receipt = supplier.lookup(identifier)
            if receipt is not None:
                return record_receipt(db, assignment, identifier, receipt)
        except (OSError, ValueError):
            return {"status": "UNKNOWN", "operation": identifier}
        if not supplier.idempotent:
            return {"status": "UNKNOWN", "operation": identifier, "needs_operator": True}
    with db.immediate() as connection:
        expires = assert_current(connection, assignment)
        current = connection.execute(
            "SELECT * FROM assistant_orders WHERE id=?", (identifier,)
        ).fetchone()
        budget = connection.execute("SELECT * FROM assistant_spending WHERE id=1").fetchone()
        held = connection.execute(
            "SELECT coalesce(sum(amount),0) FROM assistant_orders "
            "WHERE status IN ('APPROVED','SENDING','UNKNOWN')"
        ).fetchone()[0]
        if (
            budget is None
            or budget["reserved_cents"] < held
            or budget["spent_cents"] + budget["reserved_cents"]
            > min(budget["limit_cents"], policy.total_cents)
            or current["approved_by"] not in policy.operators
            or current["approval_basis"] == "UNKNOWN"
            or (
                current["approval_basis"] == "AUTOMATIC"
                and current["amount"] > policy.automatic_order_cents
            )
        ):
            raise PermissionError("current spending authority or reservation is insufficient")
        if (
            not math.isfinite(supplier.timeout)
            or supplier.timeout <= 0
            or expires - time.time() <= supplier.timeout
        ):
            raise PermissionError("supplier wait would exceed current ownership")
        if (
            current["status"] not in {"APPROVED", "SENDING", "UNKNOWN"}
            or current["revoked"]
            or (current["approved_until"] or 0) <= time.time()
        ):
            raise PermissionError("current exact-order approval required")
        connection.execute("UPDATE assistant_orders SET status='SENDING' WHERE id=?", (identifier,))
        record_event(connection, "assistant.order.intent", {"order": identifier})
    try:
        receipt = supplier.order(identifier, json.loads(row["proposal"]))
        return record_receipt(db, assignment, identifier, receipt)
    except (OSError, ValueError):
        with db.immediate() as connection:
            connection.execute(
                "UPDATE assistant_orders SET status='UNKNOWN' WHERE id=? AND status='SENDING'",
                (identifier,),
            )
        return {"status": "UNKNOWN", "operation": identifier}
