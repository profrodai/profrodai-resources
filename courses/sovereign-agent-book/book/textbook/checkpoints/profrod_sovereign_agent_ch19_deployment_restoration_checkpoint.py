# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 19: backup, restore without old authority, account recovery, and the host service.

Every function it calls is the learner's own: Chapter 19's operations on Chapter 11's orders and
Chapter 19's supplier, and the chapters beneath them. The systemd service itself runs only on a
Linux host; see the chapter's service experiment and its receipt.
"""

import bisect
import hashlib
import json
import math
import random
import runpy
import sqlite3
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

BOOK = Path(__file__).resolve().parents[1]
OPS = runpy.run_path(str(BOOK / "learner/profrod_sovereign_agent_ch19_operations_learner.py"))
ORDERS, SUPPLIER = OPS["ORDERS"], OPS["SUPPLIER"]
SUPPLIER_FILE = BOOK / "learner/profrod_sovereign_agent_ch19_supplier_learner.py"


def refused(error, action):
    try:
        action()
    except error:
        return True
    return False


@contextmanager
def supplier_process(root):
    """The chapter's supplier in its own process, with its own ledger."""
    ready, path = root / "ready", root / "supplier.sqlite"
    process = subprocess.Popen(
        [sys.executable, str(SUPPLIER_FILE), "--database", str(path), "--ready", str(ready)],
        cwd=BOOK.parents[1],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 10
        while not ready.exists() and time.monotonic() < deadline and process.poll() is None:
            time.sleep(0.02)
        if not ready.exists():
            raise RuntimeError("chapter supplier failed to start")
        yield "http://127.0.0.1:" + ready.read_text(), path
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def experiment(root):
    policy = ORDERS["SpendingPolicy"](frozenset({"lucy"}))
    with supplier_process(root) as (endpoint, supplier_path):
        db, queue = OPS["open_operations"](root / "agent.sqlite")
        observer = None
        try:
            client = OPS["configured_supplier"](db, endpoint)

            def prepare(source, sku, quantity):
                assert queue.admit(source, "lucy", "Prepare replenishment.") == "accepted"
                holder = OPS["claim"](db, "worker-" + source)
                operation = ORDERS["propose"](db, holder, sku, quantity, target=client.identity)
                digest = db.connection.execute(
                    "SELECT digest FROM assistant_orders WHERE id=?", (operation,)
                ).fetchone()[0]
                ORDERS["approve"](
                    db, operation, digest, actor="lucy", policy=policy, expires=time.time() + 120
                )
                return holder, operation

            original, vanilla = prepare("morning", "SKU-VANILLA", 6)
            snapshot = OPS["backup"](db, root / "morning.sqlite")
            snapshot_hash = hashlib.sha256(snapshot.read_bytes()).hexdigest()
            assert refused(FileExistsError, lambda: OPS["backup"](db, snapshot))
            assert snapshot.stat().st_mode & 0o077 == 0
            with sqlite3.connect(snapshot) as saved:
                assert saved.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            print("ok   a private, checked snapshot; a second backup to it is refused")
            receipt = ORDERS["execute"](db, original, vanilla, client, policy=policy)
            assert receipt["status"] == "ACCEPTED"
            db.apply(OPS["STORE"]["StockEvent"]("delivery-A", "SKU-VANILLA", 6, "received"))
            queue.finish(original, "received")
            later, strawberry = prepare("afternoon", "SKU-STRAWBERRY", 4)
            receipt = ORDERS["execute"](db, later, strawberry, client, policy=policy)
            assert receipt["status"] == "ACCEPTED"
            assert refused(ValueError, lambda: OPS["restore"](db, db.path))
            other = ORDERS["StateStore"](root / "other.sqlite")
            other.migrate("extra", {1: ("CREATE TABLE extra (x)",)})
            OPS["backup"](other, root / "other-snapshot.sqlite")
            other.close()
            assert refused(ValueError, lambda: OPS["restore"](db, root / "other-snapshot.sqlite"))
            observer = ORDERS["StateStore"](db.path)
            ORDERS["assert_current"](observer.connection, later)  # still owned before restore
            inode = db.path.stat().st_ino
            OPS["restore"](db, snapshot)
            assert db.path.stat().st_ino == inode
            assert OPS["health"](db)["paused"] is True
            # Intake still works while paused; nothing may claim what it admits.
            assert queue.admit("during-pause", "lucy", "Prepare a stock brief.") == "accepted"
            assert OPS["claim"](db, "replacement") is None
            for holder in (original, later):
                assert refused(
                    PermissionError,
                    lambda h=holder: ORDERS["assert_current"](observer.connection, h),
                )
            assert refused(PermissionError, lambda: OPS["configured_supplier"](db, endpoint))
            orders = dict(db.connection.execute("SELECT id, status FROM assistant_orders"))
            assert orders == {vanilla: "REVOKED"} and db.stock()["SKU-VANILLA"] == 2
            print("ok   restored in place and paused; old holders and connections refused")
            inspector = SUPPLIER["EpochClient"](endpoint, OPS["control"](db.connection)[0])
            inspection = OPS["inspect_account"](db, inspector, actor="lucy", policy=policy)
            assert len(inspection["receipts"]) == 2
            plan = inspection["plan_template"]
            assert plan["inventory"]["SKU-VANILLA"]["on_hand"] is None
            # The pre-restore client still holds the old epoch: the account now refuses it.
            assert refused(OSError, lambda: client.order("f" * 32, receipt["proposal"]))
            plan["observed_at"] = time.time()
            # Authored physical observations, independent of the restored stock.
            plan["inventory"] = {
                "SKU-CHOCOLATE": {"on_hand": 12},
                "SKU-STRAWBERRY": {"on_hand": 1},
                "SKU-VANILLA": {"on_hand": 8},
            }
            plan["deliveries"] = {
                vanilla: {"received": True, "reference": "delivery-A"},
                strawberry: {"received": False, "reference": ""},
            }
            raw = json.dumps(plan).encode()
            digest = hashlib.sha256(raw).hexdigest()
            recover = OPS["recover"]
            for broken in (
                {**plan, "receipts": plan["receipts"][:1]},
                {**plan, "deliveries": {vanilla: plan["deliveries"][vanilla]}},
                {**plan, "inventory": {"SKU-VANILLA": {"on_hand": 8}}},
            ):
                wrong = json.dumps(broken).encode()
                assert refused(
                    ValueError,
                    lambda w=wrong: recover(
                        db,
                        inspector,
                        w,
                        hashlib.sha256(w).hexdigest(),
                        actor="lucy",
                        policy=policy,
                    ),
                )
            assert refused(
                ValueError,
                lambda: recover(db, inspector, raw, "0" * 64, actor="lucy", policy=policy),
            )
            stale = json.dumps({**plan, "observed_at": time.time() - 3600}).encode()
            assert refused(
                ValueError,
                lambda: recover(
                    db,
                    inspector,
                    stale,
                    hashlib.sha256(stale).hexdigest(),
                    actor="lucy",
                    policy=policy,
                ),
            )
            assert OPS["health"](db)["paused"] is True
            result = recover(db, inspector, raw, digest, actor="lucy", policy=policy)
            assert result == {
                "status": "ACTIVE",
                "duplicate": False,
                "orders": 2,
                "spent_cents": 2600,
            }
            again = recover(db, inspector, raw, digest, actor="lucy", policy=policy)
            assert refused(
                PermissionError,
                lambda: OPS["inspect_account"](db, inspector, actor="lucy", policy=policy),
            )
            assert again["duplicate"] is True
            assert dict(db.connection.execute("SELECT id, status FROM assistant_orders")) == {
                vanilla: "DELIVERED",
                strawberry: "CONFIRMED",
            }
            spending = db.connection.execute(
                "SELECT reserved_cents, spent_cents FROM assistant_spending"
            ).fetchone()
            assert tuple(spending) == (0, 2600)
            position = [
                (r["on_hand"], r["on_order"], r["needed"]) for r in OPS["stock_position"](db)
            ]
            assert position == [(12, 0, 0), (1, 4, 0), (8, 0, 0)]
            interrupted = db.connection.execute(
                "SELECT body FROM reports r JOIN work w ON w.work_id = r.work_id"
                " WHERE w.source_id='morning'"
            ).fetchall()
            assert [row[0] for row in interrupted] == [
                "This request was interrupted by a restore. Please send it again."
            ]
            assert queue.admit("after-recovery", "lucy", "Prepare a stock brief.") == "accepted"
            skills = runpy.run_path(
                str(BOOK / "learner/profrod_sovereign_agent_ch07_skills_learner.py")
            )
            fresh = OPS["work_once"](db, queue, skills["OfflineShopModel"]())
            assert fresh["status"] == "COMPLETED"
            assert (
                OPS["configured_supplier"](db, endpoint).epoch == OPS["control"](db.connection)[0]
            )
            assert hashlib.sha256(snapshot.read_bytes()).hexdigest() == snapshot_hash
            with sqlite3.connect(supplier_path) as remote:
                assert remote.execute("SELECT count(*) FROM orders").fetchone()[0] == 2
            return {
                "same_inode": True,
                "old_connection_refused": True,
                "restored_local_orders": 1,
                "reconciled_orders": 2,
                "spent_cents": 2600,
                "vanilla_on_hand": 8,
                "strawberry_on_order": 4,
                "fresh_work": fresh["status"],
                "backup_unchanged": True,
            }
        finally:
            if observer is not None:
                observer.close()
            db.close()


ECONOMICS = runpy.run_path(
    str(
        Path(__file__).resolve().parents[1]
        / "learner/profrod_sovereign_agent_ch19_inference_economics_learner.py"
    )
)


def economics():
    """Part A's formulas, each checked against an independent computation."""
    kv = ECONOMICS["kv_cache_bytes"]
    # qwen2.5:1.5b: 28 layers, 2 KV heads of dimension 128, 16-bit values, one token.
    assert kv(28, 2, 128, 1) == 2 * 28 * 2 * 128 * 2 == 28_672
    assert kv(28, 12, 128, 1) == 6 * kv(28, 2, 128, 1)
    print("ok   KV cache per token from the architecture; GQA divides it by 12 / 2")

    assert (
        ECONOMICS["arithmetic_intensity"](1, 2) == 1
        and ECONOMICS["arithmetic_intensity"](8, 0.5) == 32
    )
    assert math.isclose(ECONOMICS["decode_ceiling"](273e9, 986e6), 273e9 / 986e6)
    print("ok   arithmetic intensity grows with the batch; the ceiling is bandwidth over bytes")

    rng = random.Random(18)
    values = [rng.random() for _ in range(37)]
    for q in (1, 50, 90, 99, 100):
        chosen = ECONOMICS["percentile"](values, q)
        at_or_below = sum(v <= chosen for v in values)
        assert at_or_below >= q / 100 * len(values)
        assert all(
            sum(w <= v for w in values) < q / 100 * len(values) for v in values if v < chosen
        )
    print("ok   nearest-rank percentile is the smallest value covering q percent")

    for calls, first, added in ((1, 300, 60), (8, 300, 60), (20, 120, 45)):
        explicit = sum(first + k * added for k in range(calls))
        assert ECONOMICS["loop_input_tokens"](calls, first, added) == explicit
    assert math.isclose(ECONOMICS["cost_cents"](1_000_000, 0, 0.15, 0.60), 15)
    print("ok   loop input equals the explicit sum of every call's transcript")

    # Little's law, checked on a simulated single-server queue with random arrivals.
    rng = random.Random(7)
    clock = free_at = 0.0
    spans = []
    for _ in range(20_000):
        clock += rng.expovariate(2.0)
        start = max(clock, free_at)
        free_at = start + 0.3
        spans.append((clock, free_at))
    horizon = spans[-1][1]
    rate = len(spans) / horizon
    mean_time = sum(end - begin for begin, end in spans) / len(spans)
    # Count requests in progress at random instants, independently of the formula.
    instants = sorted(rng.uniform(0, horizon) for _ in range(20_000))
    starts = sorted(begin for begin, _ in spans)
    ends = sorted(end for _, end in spans)
    in_system = sum(bisect.bisect(starts, t) - bisect.bisect(ends, t) for t in instants) / len(
        instants
    )
    predicted = ECONOMICS["concurrency"](rate, mean_time)
    assert abs(in_system - predicted) < 0.03 * predicted
    print(f"ok   Little's law: sampled {in_system:.2f} in progress, predicted {predicted:.2f}")


def service_unit():
    """The unit text, checked here; the service itself is proven on Linux by the experiment."""
    unit = OPS["unit_text"](
        Path("/srv/lucy/state"), Path("/srv/lucy/course/.venv/bin/python"), Path("/srv/lucy/course")
    )
    assert "Restart=on-failure" in unit and "TimeoutStopSec=90" in unit
    assert "ExecStart=/srv/lucy/course/.venv/bin/python -I /srv/lucy/course/book/" in unit
    assert unit.rstrip().endswith("WantedBy=default.target")
    assert refused(
        ValueError,
        lambda: OPS["unit_text"](Path("/srv/lucy state"), Path("/usr/bin/python3"), Path("/srv")),
    )
    receipt = json.loads(
        (BOOK.parents[1] / "docs/evidence/book-ch19/ch19-service-receipt-v1.json").read_text()
    )
    assert receipt["unit"] == OPS["unit_text"](
        Path(receipt["paths"]["state"]),
        Path(receipt["paths"]["python"]),
        Path(receipt["paths"]["course"]),
    )
    checks = receipt["checks"]
    assert all(checks.values()), checks
    print(
        "ok   unit text; the recorded Linux run served work, restarted after SIGKILL and came"
        " back after a reboot"
    )


def main():
    economics()
    service_unit()
    with tempfile.TemporaryDirectory(prefix="lucy-maintenance-") as directory:
        result = experiment(Path(directory))
    print("Snapshot retained; original database inode preserved:", result["same_inode"])
    print("Old open connection and supplier epoch refused:", result["old_connection_refused"])
    print(
        "Local orders after restore / reconciled:",
        result["restored_local_orders"],
        result["reconciled_orders"],
    )
    print("Recovered expenditure:", result["spent_cents"], "cents")
    print(
        "Vanilla on hand / strawberry pending:",
        result["vanilla_on_hand"],
        result["strawberry_on_order"],
    )
    print("Fresh work:", result["fresh_work"])
    print("Systemd host operations: recorded on Linux; not run by this portable checkpoint")


if __name__ == "__main__":
    main()
