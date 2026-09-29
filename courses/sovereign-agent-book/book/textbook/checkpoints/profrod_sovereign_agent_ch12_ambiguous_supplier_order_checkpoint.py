# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 12: a supplier commits an order, its reply is lost, and the agent reconciles it.

Every function it calls is the learner's own: Chapter 11's approvals, send check and supplier
process, and Chapter 12's reply-losing proxy between them.
"""

import json
import math
import runpy
import sqlite3
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

BOOK = Path(__file__).resolve().parents[1]
RETRY = runpy.run_path(str(BOOK / "learner/profrod_sovereign_agent_ch12_retries_learner.py"))
APPROVAL = runpy.run_path(str(BOOK / "learner/profrod_sovereign_agent_ch11_approval_learner.py"))
SUPPLIER_FILE = BOOK / "learner/profrod_sovereign_agent_ch11_supplier_learner.py"
SUPPLIER = runpy.run_path(str(SUPPLIER_FILE))
open_shop, hold, SpendingPolicy = (
    APPROVAL["open_shop"],
    APPROVAL["hold"],
    APPROVAL["SpendingPolicy"],
)
propose, approve, revoke = APPROVAL["propose"], APPROVAL["approve"], APPROVAL["revoke"]
execute, record_receipt = APPROVAL["execute"], APPROVAL["record_receipt"]
POLICY = SpendingPolicy(frozenset({"lucy"}), total_cents=2000)


def retry_arithmetic():
    """Part A's formulas by independent checks, and the receipt recomputed from its runs."""
    attempts, duplicates = RETRY["expected_attempts"], RETRY["expected_duplicates"]
    assert attempts(0, 0) == 1 and duplicates(0.3, 0) == 0
    a, b = 0.1, 0.2
    s = 1 - a - b
    series = sum(s * (1 - s) ** (k - 1) * (k - 1) * b / (a + b) for k in range(1, 400))
    assert math.isclose(series, duplicates(a, b)) and math.isclose(attempts(a, b), 1 / s)
    capped = RETRY["capped_attempts"]
    assert capped(0.5, 3) == 1.75 and capped(1, 3) == 3 and capped(0, 5) == 1
    key = RETRY["operation_key"]
    proposal = {"sku": "SKU-VANILLA", "quantity": 6}
    assert key("w", "t", proposal) == key("w", "t", dict(reversed(list(proposal.items()))))
    assert key("w", "t", proposal) != key("w", "other", proposal)
    print("ok   duplicates are b / (1 - a - b), and one key names one intended order")
    receipt = json.loads(
        (BOOK.parents[1] / "docs/evidence/book-ch12/ch12-retries-receipt-v1.json").read_text()
    )
    latencies = receipt["timeouts"]["pilot_latencies"]
    rules = {
        "pilot median": RETRY["percentile"](latencies, 50),
        "pilot 90th percentile": RETRY["percentile"](latencies, 90),
        "twice the pilot maximum": round(2 * max(latencies), 3),
    }
    for row in receipt["timeouts"]["rows"]:
        assert row["timeout_seconds"] == rules[row["rule"]]
        share = RETRY["timed_out_share"](latencies, row["timeout_seconds"])
        assert round(share, 3) == row["pilot_timed_out_share"]
        mine = [
            order
            for order in receipt["timeouts"]["orders"]
            if (order["rule"], order["operation_key"]) == (row["rule"], row["operation_key"])
        ]
        attempts = sum(len(order["attempts"]) for order in mine) / len(mine)
        placed = sum(order["supplier_orders"] for order in mine) / len(mine)
        assert round(attempts, 3) == row["mean_attempts"]
        assert round(placed, 3) == row["supplier_orders_per_intended"]
    for row in receipt["behavior"]["rows"]:
        runs = [
            [c["name"] for c in run["turns"][-1]["calls"]]
            for run in receipt["runs"]
            if (run["model"], run["error"]) == (row["model"], row["error_text"])
        ]
        assert row["resent"] == sum("place_order" in names for names in runs)
        assert row["looked_up"] == sum("lookup_order" in names for names in runs)
        resends = sum(names.count("place_order") for names in runs)
        assert row["supplier_orders_without_key"] == len(runs) + resends
        assert row["supplier_orders_with_key"] == len(runs)
    print("ok   timeouts, re-sends and supplier orders recompute from the retained runs")


@contextmanager
def supplier_process(root):
    """The learner's Chapter 11 supplier in its own process, with its own database."""
    ready, path = root / "ready", root / "supplier.sqlite"
    command = [sys.executable, str(SUPPLIER_FILE), "--database", str(path), "--ready", str(ready)]
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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


def spending(db):
    return tuple(
        db.connection.execute(
            "SELECT reserved_cents, spent_cents FROM assistant_spending WHERE id=1"
        ).fetchone()
    )


def status(db, identifier):
    row = db.connection.execute("SELECT status FROM assistant_orders WHERE id=?", (identifier,))
    return row.fetchone()[0]


def approved_order(db, queue, name, target, policy=POLICY):
    """One claimed, held assignment with one approved six-tub vanilla order."""
    queue.admit("chapter12:" + name, "lucy", "Replenish vanilla")
    work = queue.claim("chapter12-" + name)
    hold(db, work)
    identifier = propose(db, work, "SKU-VANILLA", 6, target=target)
    assert propose(db, work, "SKU-VANILLA", 6, target=target) == identifier
    digest = db.connection.execute(
        "SELECT digest FROM assistant_orders WHERE id=?", (identifier,)
    ).fetchone()[0]
    approve(db, identifier, digest, actor="lucy", policy=policy, expires=time.time() + 600)
    return work, identifier


class CountingSupplier:
    """In-process supplier fixtures that count every send and lookup.

    fault: "after" commits the order and then loses the reply; "before" loses the request before
    anything is kept; "lookup" also fails every lookup; "blind" keeps nothing, can look up
    nothing and promises no idempotency."""

    timeout = 3

    def __init__(self, fault):
        self.fault, self.identity = fault, "lucy-local:" + fault
        self.idempotent = fault != "blind"
        self.kept, self.sends, self.lookups, self.failed = {}, 0, 0, False

    def lookup(self, operation):
        self.lookups += 1
        if self.fault == "lookup":
            raise OSError("lookup unavailable")
        return self.kept.get(operation)

    def order(self, operation, proposal):
        self.sends += 1
        if self.fault == "blind" or (self.fault == "before" and not self.failed):
            self.failed = True
            raise TimeoutError("no reply; nothing is known")
        receipt = self.kept.setdefault(
            operation, {"operation": operation, "proposal": proposal, "status": "ACCEPTED"}
        )
        if self.fault in {"after", "lookup"} and not self.failed:
            self.failed = True
            raise TimeoutError("committed, but the reply was lost")
        return receipt


def over_http(root):
    """The lost reply over real HTTP: supplier process, proxy, and a reopened agent database."""
    with supplier_process(root) as (upstream, supplier_path):
        proxy = RETRY["ReplyLosingProxy"](upstream)
        supplier = SUPPLIER["SupplierClient"](proxy.endpoint)
        db, queue = open_shop(root / "agent.sqlite")
        try:
            work, identifier = approved_order(db, queue, "http", supplier.identity)
            initial = execute(db, work, identifier, supplier, policy=POLICY)
            assert initial == {"status": "UNKNOWN", "operation": identifier}
            assert status(db, identifier) == "UNKNOWN" and spending(db) == (1500, 0)
            assert proxy.lost == [f"/orders/{identifier}"]
            print("initial", initial["status"])
            print("reserved and spent", *spending(db))
            with sqlite3.connect(supplier_path) as remote:
                assert remote.execute("SELECT count(*) FROM orders").fetchone()[0] == 1
            # Reopen the durable ledger while the same ownership claim remains valid.
            # Worker death and replacement are a separate Chapter 13 experiment.
            db.close()
            db, queue = open_shop(root / "agent.sqlite")
            receipt = execute(db, work, identifier, supplier, policy=POLICY)
            assert receipt["status"] == "ACCEPTED" and receipt["operation"] == identifier
            assert execute(db, work, identifier, supplier, policy=POLICY) == receipt
            # The same key sent again, straight to the supplier: the stored receipt, no new order.
            proposal = db.connection.execute(
                "SELECT proposal FROM assistant_orders WHERE id=?", (identifier,)
            ).fetchone()[0]
            assert supplier.order(identifier, json.loads(proposal)) == receipt
            print("after reconciliation", receipt["status"], status(db, identifier))
            print("reserved and spent", *spending(db))
            with sqlite3.connect(supplier_path) as remote:
                count = remote.execute("SELECT count(*) FROM orders").fetchone()[0]
            assert count == 1 and spending(db) == (0, 1500)
            print("supplier orders", count)
        finally:
            db.close()
            proxy.close()


def in_process(root):
    """Each kind of silence, counted: what the send check does after it."""
    db, queue = open_shop(root / "fixtures.sqlite")
    wide = SpendingPolicy(frozenset({"lucy"}), total_cents=20_000)
    results = {}
    for fault in ("after", "before", "lookup", "blind"):
        supplier = CountingSupplier(fault)
        work, identifier = approved_order(db, queue, fault, supplier.identity, wide)
        first = execute(db, work, identifier, supplier, policy=wide)
        assert first == {"status": "UNKNOWN", "operation": identifier}
        if fault == "blind":
            revoke(db, identifier, actor="lucy", policy=wide)
        second = execute(db, work, identifier, supplier, policy=wide)
        results[fault] = (
            second.get("status"),
            supplier.sends,
            supplier.lookups,
            status(db, identifier),
        )
        if fault == "after":
            accepted, accepted_work = second, work
        if fault == "blind":
            assert second.get("needs_operator") is True
    assert results["after"] == ("ACCEPTED", 1, 1, "CONFIRMED"), results
    assert results["before"] == ("ACCEPTED", 2, 1, "CONFIRMED"), results
    assert results["lookup"] == ("UNKNOWN", 1, 1, "UNKNOWN"), results
    assert results["blind"] == ("UNKNOWN", 1, 1, "UNKNOWN"), results
    print("lost reply: one send, one lookup, confirmed")
    print("lost request: resent under the same key after an empty lookup, confirmed")
    print("failed lookup, and a blind supplier after revocation: UNKNOWN, no second send")
    reserved, spent = spending(db)
    assert (reserved, spent) == (3000, 3000), (reserved, spent)
    wrong = json.loads(json.dumps(accepted))
    wrong["proposal"]["quantity"] = 7
    try:
        record_receipt(db, accepted_work, accepted["operation"], wrong)
    except ValueError:
        pass
    else:
        raise AssertionError("mismatched receipt settled an order")
    assert spending(db) == (3000, 3000)
    assert record_receipt(db, accepted_work, accepted["operation"], accepted) == accepted
    assert spending(db) == (3000, 3000)
    stock = dict(db.connection.execute("SELECT sku, tubs FROM stock").fetchall())
    assert stock["SKU-VANILLA"] == APPROVAL["CATALOG"]["SKU-VANILLA"]["on_hand"]
    print("mismatched receipt refused; uncertain reservations held; stock unchanged until delivery")
    db.close()


def main():
    retry_arithmetic()
    with tempfile.TemporaryDirectory(prefix="lucy-chapter12-") as directory:
        over_http(Path(directory))
        in_process(Path(directory))


if __name__ == "__main__":
    main()
