# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 19's operations: back up, restore without old authority, reconcile, and run as a service.

Every piece underneath is earlier learner code. Chapter 11's store holds the stock, the work queue,
the leases and the orders; Chapter 19's supplier adds an account epoch and a receipt export.
This file adds what keeping the agent running needs: a consistent SQLite backup; a restore that
keeps the database file, starts paused and revokes every old approval and lease; a read-only
health summary; account inspection that fences the supplier and lists its receipts; a recovery
that applies an operator's exact, digest-bound plan of current counts and deliveries; and the
systemd unit that runs the Chapter 10 worker on a Linux host.
"""

import hashlib
import json
import math
import os
import re
import runpy
import sqlite3
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

LEARNER = Path(__file__).resolve().parent
ORDERS = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch11_approval_learner.py"))
SUPPLIER = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch19_supplier_learner.py"))
LOOP = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch03_agent_loop_learner.py"))
STORE, TOOLS, CATALOG = ORDERS["STORE"], ORDERS["TOOLS"], ORDERS["CATALOG"]

OPERATIONS_MIGRATIONS = {
    1: (
        # The authority epoch: a restore replaces it, so anything holding the old one is stale.
        "CREATE TABLE operations ("
        " id INTEGER PRIMARY KEY CHECK (id = 1), epoch TEXT NOT NULL,"
        " paused INTEGER NOT NULL DEFAULT 0)",
        "CREATE TABLE recoveries ("
        " digest TEXT PRIMARY KEY, plan TEXT NOT NULL, created REAL NOT NULL)",
    ),
}


def open_operations(path: str | Path):
    """Chapter 11's store and queue, with the operations tables and a first epoch."""
    db, queue = ORDERS["open_shop"](path)
    db.migrate("operations", OPERATIONS_MIGRATIONS)
    with db.immediate() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO operations(id, epoch) VALUES (1, ?)", (uuid.uuid4().hex,)
        )
    return db, queue


def control(connection) -> tuple[str, bool]:
    epoch, paused = connection.execute("SELECT epoch, paused FROM operations WHERE id=1").fetchone()
    return epoch, bool(paused)


def configured_supplier(db, endpoint: str):
    """The supplier client for the current epoch, registered with the account. Refused while
    paused: a restored database must be reconciled before it may order again."""
    epoch, paused = control(db.connection)
    if paused:
        raise PermissionError("operations are paused; inspect and recover the account first")
    client = SUPPLIER["EpochClient"](endpoint, epoch)
    client.set_epoch(epoch)
    return client


def claim(db, worker_id: str, *, seconds: float = 300):
    """Chapter 8's claim and Chapter 11's lease in one transaction; nothing while paused."""
    with db.immediate() as connection:
        if control(connection)[1]:
            return None
        row = connection.execute(
            "SELECT work_id, session_id, text FROM work WHERE state='pending'"
            " ORDER BY work_id LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        connection.execute(
            "UPDATE work SET state='running', worker_id=? WHERE work_id=?", (worker_id, row[0])
        )
        connection.execute(
            "INSERT INTO assignment_leases VALUES (?, ?, ?) ON CONFLICT (work_id) DO UPDATE"
            " SET worker_id=excluded.worker_id, expires=excluded.expires",
            (row[0], worker_id, time.time() + seconds),
        )
    return ORDERS["QUEUE"]["Assignment"](row[0], row[1], row[2], worker_id)


# ---------------------------------------------------------------- backup and restore


def backup(db, destination: Path) -> Path:
    """A consistent SQLite snapshot, created exclusively and privately, checked and synced."""
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("backup destination already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation makes a repeated run a refusal, not a replacement of evidence.
    descriptor = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    try:
        with sqlite3.connect(destination) as snapshot:
            db.connection.backup(snapshot)
            if snapshot.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("backup integrity check failed")
        with destination.open("rb") as stream:
            os.fsync(stream.fileno())
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    return destination


def schema(connection) -> dict[str, int]:
    """Each component's schema version, from Chapter 4's `meta` table."""
    return dict(connection.execute("SELECT key, value FROM meta"))


def restore(db, source: Path) -> str:
    """Pause the active database, then copy a checked snapshot into it with new authority.

    The database file is kept: replacing the path would leave open connections writing to the
    old file. The copied image carries a new epoch and is paused; every lease is dropped, so no
    old holder passes Chapter 11's ownership check; every approval is revoked. A request the
    supplier already accepted is not recalled; recovery finds it. Returns the new epoch."""
    if source.resolve() == db.path.resolve() or not source.is_file():
        raise ValueError("a separate existing backup is required")
    with sqlite3.connect(f"{source.resolve().as_uri()}?mode=ro", uri=True) as snapshot:
        if snapshot.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("restore source is corrupt")
        if schema(snapshot) != schema(db.connection):
            raise ValueError("restore requires the same schema versions; migrate a copy first")
        # Prepare the restored image before disturbing active state.
        with tempfile.TemporaryDirectory(prefix="lucy-restore-") as temporary:
            image = Path(temporary) / "restored.sqlite"
            epoch = uuid.uuid4().hex
            with sqlite3.connect(image) as prepared:
                snapshot.backup(prepared)
                prepared.execute("UPDATE operations SET epoch=?, paused=1 WHERE id=1", (epoch,))
                prepared.execute("DELETE FROM assignment_leases")
                # Old approvals can be reconciled, but cannot authorize a new send.
                prepared.execute(
                    "UPDATE assistant_orders SET revoked=1, approved_until=0,"
                    " status=CASE WHEN status IN ('DRAFT','APPROVED') THEN 'REVOKED'"
                    " ELSE status END"
                )
                prepared.execute("UPDATE assistant_spending SET reserved_cents=0")
                prepared.commit()
                with db.immediate() as connection:
                    connection.execute("UPDATE operations SET paused=1 WHERE id=1")
                prepared.backup(db.connection)
    return epoch


def health(db) -> dict[str, Any]:
    """Durable business state, read-only: what process liveness cannot say."""
    connection = db.connection
    epoch, paused = control(connection)
    return {
        "paused": paused,
        "epoch": epoch,
        "work": dict(connection.execute("SELECT state, count(*) FROM work GROUP BY state")),
        "uncertain_orders": connection.execute(
            "SELECT count(*) FROM assistant_orders WHERE status IN ('SENDING','UNKNOWN')"
        ).fetchone()[0],
        "uncertain_reports": connection.execute(
            "SELECT count(*) FROM reports WHERE delivery IN ('sending','unknown')"
        ).fetchone()[0],
    }


# ---------------------------------------------------------------- account recovery


def inspect_account(db, client, *, actor: str, policy) -> dict[str, Any]:
    """Fence the supplier account with the restored epoch, then list every receipt it holds.

    The plan template leaves every physical count and delivery unknown: receipts say what the
    supplier accepted, not what arrived or what was sold since."""
    if actor not in policy.operators:
        raise PermissionError("operator is not allowlisted")
    epoch, paused = control(db.connection)
    if not paused:
        raise PermissionError("account inspection is for a paused, restored database")
    client.set_epoch(epoch)  # an old process with the previous epoch can no longer order
    receipts = client.receipts()
    accepted = sorted(r["operation"] for r in receipts if r.get("status") == "ACCEPTED")
    return {
        "receipts": receipts,
        "plan_template": {
            "authority": epoch,
            "observed_at": None,
            "receipts": accepted,
            "inventory": {sku: {"on_hand": None} for sku in sorted(CATALOG)},
            "deliveries": {
                operation: {"received": None, "reference": ""} for operation in accepted
            },
        },
    }


def recover(
    db,
    client,
    raw: bytes,
    digest: str,
    *,
    actor: str,
    policy,
    now: float | None = None,
    freshness: float = 900,
) -> dict[str, Any]:
    """Apply an operator's exact plan: the supplier's accepted orders, today's counts and
    deliveries. Checks everything first, changes everything in one transaction, then resumes.
    The same plan again is a duplicate and changes nothing."""
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError("plan bytes do not match the reviewed digest")
    if actor not in policy.operators:
        raise PermissionError("operator is not allowlisted")
    now = time.time() if now is None else now
    done = db.connection.execute("SELECT plan FROM recoveries WHERE digest=?", (digest,)).fetchone()
    if done is not None:
        return {"status": "ACTIVE", "duplicate": True}
    plan = json.loads(raw)
    epoch, paused = control(db.connection)
    if not paused or plan.get("authority") != epoch:
        raise PermissionError("the plan must belong to the current paused restore")
    observed = plan.get("observed_at")
    if not isinstance(observed, (int, float)) or not math.isfinite(observed):
        raise ValueError("the plan needs the time its observations were made")
    if not now - freshness <= observed <= now:
        raise ValueError("the plan's observations are not current")
    receipts = {
        r["operation"]: r
        for r in client.receipts()
        if r.get("status") == "ACCEPTED"
        and SUPPLIER["CHAPTER11"]["valid_proposal"](r.get("proposal"))
    }
    if sorted(receipts) != plan.get("receipts"):
        raise ValueError("the supplier's receipts changed since inspection")
    inventory, deliveries = plan.get("inventory", {}), plan.get("deliveries", {})
    if sorted(inventory) != sorted(CATALOG) or any(
        type(count.get("on_hand")) is not int or count["on_hand"] < 0
        for count in inventory.values()
    ):
        raise ValueError("a current count for every product is required")
    if sorted(deliveries) != sorted(receipts) or any(
        type(d.get("received")) is not bool for d in deliveries.values()
    ):
        raise ValueError("an explicit delivery observation for every accepted order is required")
    spent = 0
    with db.immediate() as connection:
        for operation, receipt in receipts.items():
            proposal = receipt["proposal"]
            encoded = json.dumps(proposal, sort_keys=True, separators=(",", ":"))
            amount = proposal["quantity"] * proposal["unit_cost_cents"]
            status = "DELIVERED" if deliveries[operation]["received"] else "CONFIRMED"
            spent += amount
            if connection.execute(
                "SELECT 1 FROM assistant_orders WHERE id=?", (operation,)
            ).fetchone():
                connection.execute(
                    "UPDATE assistant_orders SET status=?, receipt=? WHERE id=?",
                    (status, json.dumps(receipt), operation),
                )
            else:
                # An order the snapshot never saw: imported from the supplier's receipt.
                connection.execute(
                    "INSERT INTO assistant_orders(id,work_id,proposal,digest,amount,target,"
                    "status,revoked,receipt,created) VALUES (?,0,?,?,?,?,?,1,?,?)",
                    (
                        operation,
                        encoded,
                        hashlib.sha256((client.identity + "\n" + encoded).encode()).hexdigest(),
                        amount,
                        client.identity,
                        status,
                        json.dumps(receipt),
                        now,
                    ),
                )
        # Work the snapshot restored as running has no lease and no worker: finish it with a
        # report that says so, as Chapter 9 did for a stopped cell.
        for (work_id,) in connection.execute(
            "SELECT work_id FROM work WHERE state='running' ORDER BY work_id"
        ).fetchall():
            connection.execute("UPDATE work SET state='finished' WHERE work_id=?", (work_id,))
            (generation,) = connection.execute(
                "SELECT count(*) + 1 FROM reports WHERE work_id=?", (work_id,)
            ).fetchone()
            connection.execute(
                "INSERT INTO reports (report_id, work_id, generation, body, delivery)"
                " VALUES (?, ?, ?, ?, 'pending')",
                (
                    f"r{work_id}.{generation}",
                    work_id,
                    generation,
                    "This request was interrupted by a restore. Please send it again.",
                ),
            )
        # A local send the supplier never accepted cannot be accepted now: the account is fenced.
        connection.execute(
            "UPDATE assistant_orders SET status='REVOKED' WHERE status IN ('SENDING','UNKNOWN')"
        )
        connection.execute(
            "INSERT OR IGNORE INTO assistant_spending(id, limit_cents) VALUES (1, ?)",
            (policy.total_cents,),
        )
        connection.execute(
            "UPDATE assistant_spending SET reserved_cents=0, spent_cents=? WHERE id=1", (spent,)
        )
        for sku, count in inventory.items():
            (tubs,) = connection.execute("SELECT tubs FROM stock WHERE sku=?", (sku,)).fetchone()
            if count["on_hand"] != tubs:
                # A counted correction, as a Chapter 4 stock event with its own identity.
                event = STORE["StockEvent"](
                    f"recovery:{digest[:16]}:{sku}", sku, count["on_hand"] - tubs, "recovery count"
                )
                connection.execute(
                    "INSERT INTO events (event_id, sku, delta, payload, reason)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (event.event_id, sku, event.delta, event.payload(), event.reason),
                )
                connection.execute("UPDATE stock SET tubs=? WHERE sku=?", (count["on_hand"], sku))
        connection.execute("INSERT INTO recoveries VALUES (?, ?, ?)", (digest, raw.decode(), now))
        connection.execute("UPDATE operations SET paused=0 WHERE id=1")
        ORDERS["record_event"](
            connection,
            "operations.recovered",
            {"digest": digest, "orders": len(receipts), "spent_cents": spent, "actor": actor},
        )
    return {"status": "ACTIVE", "duplicate": False, "orders": len(receipts), "spent_cents": spent}


def stock_position(db) -> list[dict[str, Any]]:
    """Stock on hand, tubs ordered but not yet delivered, and the remaining need."""
    on_order = dict(
        db.connection.execute(
            "SELECT json_extract(proposal,'$.sku'), sum(json_extract(proposal,'$.quantity'))"
            " FROM assistant_orders WHERE status='CONFIRMED' GROUP BY 1"
        )
    )
    rows = []
    for sku, tubs in sorted(db.stock().items()):
        point, ordered = CATALOG[sku]["reorder_point"], on_order.get(sku, 0)
        rows.append(
            {
                "sku": sku,
                "on_hand": tubs,
                "on_order": ordered,
                "reorder_point": point,
                "needed": max(0, point - tubs - ordered),
            }
        )
    return rows


def work_once(db, queue, model, *, worker_id: str = "operations-worker") -> dict | None:
    """Claim one item (nothing while paused) and run Chapter 3's loop over the stock position."""
    assignment = claim(db, worker_id)
    if assignment is None:
        return None
    tool = TOOLS["ExecutableTool"](
        "list_stock",
        "Read stock on hand, tubs on order and the remaining need.",
        TOOLS["NoArguments"],
        lambda _: stock_position(db),
    )
    dispatcher = TOOLS["Dispatcher"]([tool], allowed=frozenset({"list_stock"}))
    messages = [
        {
            "role": "system",
            "content": "You help Lucy manage her shop. Use tools for stock. "
            "Tubs on order count toward the need.",
        },
        {"role": "user", "content": assignment.text},
    ]
    result = LOOP["run_loop"](model, dispatcher, messages)
    queue.finish(assignment, result.answer or "The agent stopped: " + result.status)
    return {"work": assignment.work_id, "status": result.status, "answer": result.answer}


# ---------------------------------------------------------------- the host service


PATH = re.compile(r"/[A-Za-z0-9_./-]+")


def unit_text(state: Path, python: Path, course: Path) -> str:
    """A systemd user unit that runs the Chapter 10 worker with an explicit interpreter.

    systemd has expansion rules unlike shell quoting, so paths are restricted rather than
    escaped: absolute, with no spaces or expansion characters."""
    state, python, course = state.absolute(), python.absolute(), course.absolute()
    if any(not PATH.fullmatch(str(path)) for path in (state, python, course)):
        raise ValueError("service paths must be absolute with no spaces or expansion characters")
    worker = course / "book/textbook/learner/profrod_sovereign_agent_ch10_wakeups_learner.py"
    return f"""[Unit]
Description=Lucy's always-on teaching agent
After=network-online.target

[Service]
Type=simple
WorkingDirectory={course}
ExecStart={python} -I {worker} serve --root {state}
EnvironmentFile={state}/agent.env
Restart=on-failure
RestartSec=10
TimeoutStopSec=90
UMask=0077
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=default.target
"""


def service(action: str, state: Path, python: Path, course: Path) -> dict[str, Any]:
    """Install, inspect or remove the unit with `systemctl --user`. Linux only."""
    if not sys.platform.startswith("linux"):
        raise ValueError("service installation requires Linux and a user systemd manager")
    if action not in {"install", "status", "uninstall"}:
        raise ValueError("invalid service action")
    name = "lucy-agent.service"
    path = Path.home() / ".config/systemd/user" / name
    content = unit_text(state, python, course)
    if action == "install":
        env = state.absolute() / "agent.env"
        if not env.is_file() or env.stat().st_mode & 0o077:
            raise ValueError("create the environment file with mode 0600 first")
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.read_text() != content:
            raise FileExistsError("a different service is already installed")
        path.write_text(content)
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True, timeout=20)
        subprocess.run(["systemctl", "--user", "enable", "--now", name], check=True, timeout=20)
    elif action == "uninstall":
        if path.exists() and path.read_text() != content:
            raise ValueError("refuse to remove another installation")
        subprocess.run(["systemctl", "--user", "disable", "--now", name], check=True, timeout=20)
        path.unlink(missing_ok=True)
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True, timeout=20)
    result = subprocess.run(
        ["systemctl", "--user", "show", name, "--property=ActiveState,SubState,MainPID,NRestarts"],
        capture_output=True,
        text=True,
        timeout=20,
    )
    return {
        "action": action,
        "unit": str(path),
        "status": result.stdout.strip(),
        "exit_code": result.returncode,
    }
