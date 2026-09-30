# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 20: Lucy's accelerated day, end to end, with injected faults and a records-only report.

Every function it calls is the learner's own: Chapter 20's day on every earlier chapter's code.
A real supplier process sits behind Chapter 12's proxy, which loses each operation's first reply;
a real worker process is killed after recording an unknown outcome; a real research process
prepares the catering quote. The phone is a fixture transport, not Telegram's servers.
"""

import argparse
import hashlib
import json
import math
import os
import runpy
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

BOOK = Path(__file__).resolve().parents[1]
LEARNER = BOOK / "learner"
DAY = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch20_day_learner.py"))
RETRIES = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch12_retries_learner.py"))
SUPPLIER = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch11_supplier_learner.py"))
APPROVAL, DELEGATION, WAKE = DAY["APPROVAL"], DAY["DELEGATION"], DAY["WAKE"]
CHANNEL, MEMORY, Limits = DAY["CHANNEL"], DAY["MEMORY"], DAY["Limits"]
POLICY = APPROVAL["SpendingPolicy"](frozenset({"123"}), total_cents=3000)
OPERATORS = frozenset({123})
LIMITS = Limits(estimated_call_cents=2)
# The model for every turn of the day: the offline fixture, or Claude with --claude.
MODEL = {"factory": None, "client": None}


def day_model():
    return MODEL["factory"]() if MODEL["factory"] else DAY["OfflineDayModel"]()


CHILD_ENV = {
    key: value
    for key, value in os.environ.items()
    if key in {"PATH", "SYSTEMROOT", "TMPDIR", "LANG", "LC_ALL", "PYTHONPATH"}
}
RESEARCH = """import json, runpy, sys
day = runpy.run_path(sys.argv[1])
db, queue = day["open_day"](sys.argv[2])
result = day["DELEGATION"]["research_once"](
    db, day["DELEGATION"]["OfflineCateringModel"](), work_id=int(sys.argv[3])
)
db.close()
print(json.dumps({"status": result["status"], "quote": result["report"]["quote"]}))
"""


def wait_until(check, seconds=10):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if check():
            return
        time.sleep(0.02)
    raise AssertionError("bounded day observation timed out")


def refused(error, action):
    try:
        action()
    except error:
        return True
    return False


class FailedModel:
    def complete(self, *args, **kwargs):
        raise OSError("injected model outage")


class NoNewReasoning:
    def complete(self, *args, **kwargs):
        raise AssertionError("approvals and recovery must continue from records")


class FixtureBot:
    account = "day-fixture"

    def __init__(self):
        self.updates = []
        self.sent = []

    def call(self, method, data):
        if method == "getUpdates":
            return self.updates
        self.sent.append(data)
        return {"message_id": len(self.sent)}


def message(identifier, text, actor=123):
    return {
        "update_id": identifier,
        "message": {
            "from": {"id": actor, "is_bot": False},
            "chat": {"id": actor, "type": "private"},
            "text": text,
        },
    }


def child(root, endpoint, work_id, order):
    """The worker that dies: it sends the approved order, loses the reply, records UNKNOWN, and
    is killed before it can do anything else."""
    db, _ = DAY["open_day"](root / "agent.sqlite")
    held, _ = DAY["claim_next"](db, "day-worker", ttl=2, work_id=int(work_id))
    assert held is not None
    client = SUPPLIER["SupplierClient"](endpoint, timeout=1)
    response = APPROVAL["execute"](db, held, order, client, policy=POLICY)
    assert response["status"] == "UNKNOWN", response
    staging = root / "child-ready.tmp"
    staging.write_text(json.dumps({"expiry": held.expires, "order": order}))
    staging.replace(root / "child-ready.json")
    time.sleep(20)
    raise AssertionError("the parent should have killed this worker")


@contextmanager
def supplier_process(root):
    """The learner's supplier in its own process, behind Chapter 12's reply-losing proxy."""
    ready, path = root / "supplier-ready", root / "supplier.sqlite"
    process = subprocess.Popen(
        [
            sys.executable,
            str(LEARNER / "profrod_sovereign_agent_ch11_supplier_learner.py"),
            "--database",
            str(path),
            "--ready",
            str(ready),
        ],
        cwd=BOOK.parents[1],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    proxy = None
    try:
        wait_until(lambda: ready.exists() or process.poll() is not None)
        if not ready.exists():
            raise RuntimeError("the supplier did not start")
        proxy = RETRIES["ReplyLosingProxy"]("http://127.0.0.1:" + ready.read_text())
        yield proxy, path
    finally:
        if proxy is not None:
            proxy.close()
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def remote_orders(path):
    with sqlite3.connect(path) as remote:
        return remote.execute(
            "SELECT operation, proposal FROM orders ORDER BY operation"
        ).fetchall()


def claude_day():
    """The recorded days with Claude doing every model turn: each ended with the supplier's two
    orders and USD 26.00, no exceptions, a killed worker, and costs that add up."""
    receipt = json.loads(
        (BOOK.parents[1] / "docs/evidence/book-ch20/ch20-day-claude-receipt-v1.json").read_text()
    )
    prices = runpy.run_path(
        str(BOOK / "experiments/profrod_sovereign_agent_claude_messages_v1.py")
    )["PRICES"]
    for model, run in receipt["runs"].items():
        report = run["report"]
        assert run["passed"] and report["exceptions"] == [] and report["open_work"] == []
        assert report["orders"] == {"CONFIRMED": 1, "DELIVERED": 1}
        assert report["spending"] == {
            "accepted_cents": 2600,
            "reserved_cents": 0,
            "order_totals_match": True,
        }
        assert (run["independent_supplier_orders"], run["independent_supplier_cents"]) == (2, 2600)
        assert run["killed_worker_exit"] == -signal.SIGKILL
        assert run["tool_calls"].count("propose_order") == 2
        usage = run["claude"]
        cost = sum(
            (
                used["input_tokens"] * prices[name][0]
                + used["output_tokens"] * prices[name][1]
                + used["cache_creation_input_tokens"] * prices[name][2]
                + used["cache_read_input_tokens"] * prices[name][3]
            )
            / 1_000_000
            for name, used in usage["usage"].items()
        )
        assert list(usage["usage"]) == [model] and usage["costUsd"] == round(cost, 4)
    total = sum(run["claude"]["costUsd"] for run in receipt["runs"].values())
    assert math.isclose(receipt["costUsd"], total, abs_tol=1e-4)
    print(
        f"ok   with Claude on every turn, both recorded days closed at USD 26.00; {total:.4f} USD"
    )


def boundaries(root):
    """The refusals the day's happy path never reaches, on a store of their own."""
    db, queue = DAY["open_day"](root / "boundaries.sqlite")
    work_once, claim_next = DAY["work_once"], DAY["claim_next"]
    try:
        # A research contract is never shop work; a session's turns stay in order.
        parent = DAY["WORKER"]["enqueue"](queue, "parent", "lucy", "Prepare a stock brief.")
        child = DELEGATION["delegate"](
            queue,
            parent,
            DELEGATION["Inquiry"](sku="SKU-VANILLA", guests=41),
            deadline=time.time() + 60,
        )
        assert work_once(db, NoNewReasoning(), work_id=child) == {"status": "IDLE"}
        later = DAY["WORKER"]["enqueue"](queue, "later", "lucy", "Prepare a stock brief.")
        held, _ = claim_next(db, "first", ttl=60)
        assert held.work_id == parent and claim_next(db, "second", work_id=later) == (None, None)
        print("ok   research is not shop work; one session's turns never overlap")

        # Proposals only for the subject's current need.
        supplier = SUPPLIER["SupplierClient"]("http://127.0.0.1:9", timeout=1)
        tools = DAY["day_tools"](db, held, "SKU-VANILLA", supplier)
        call = DAY["ToolCall"]
        for arguments in (
            {"sku": "SKU-STRAWBERRY", "quantity": 4},
            {"sku": "SKU-VANILLA", "quantity": 5},
        ):
            outcome = tools.invoke(call(id="p", name="propose_order", arguments=arguments))
            assert outcome == {"ok": False, "error": "tool_failed"}
        proposed = tools.invoke(
            call(id="q", name="propose_order", arguments={"sku": "SKU-VANILLA", "quantity": 6})
        )
        assert proposed["ok"] and proposed["value"]["amount_cents"] == 1500
        order, digest = proposed["value"]["order"], proposed["value"]["digest"]
        assert refused(
            PermissionError,
            lambda: DAY["receive"](db, order, "early", actor="123", policy=POLICY),
        )
        DAY["finish"](db, held, "DONE", "proposed")
        print("ok   an order only for this subject's current need; a draft cannot be received")

        # Approval needs an allowlisted phone and the exact digest.
        for session, text in (
            ("telegram:day-fixture:999", f"/approve {order} {digest}"),
            ("telegram:day-fixture:123", f"/approve {order} {'0' * 64}"),
        ):
            command = DAY["WORKER"]["enqueue"](queue, "cmd:" + session + text[-4:], session, text)
            assert work_once(db, NoNewReasoning(), policy=POLICY, work_id=command)["status"] == (
                "BLOCKED"
            )
        status = db.connection.execute(
            "SELECT status FROM assistant_orders WHERE id = ?", (order,)
        ).fetchone()[0]
        assert status == "DRAFT"
        print("ok   approvals from a stranger or for other bytes are refused")

        # A takeover with nothing recorded to continue asks for a new turn, without a model.
        claim_next(db, "vanishes", ttl=0.05, work_id=later)
        time.sleep(0.1)
        taken = work_once(db, NoNewReasoning(), work_id=later)
        assert taken["status"] == "BLOCKED"
        report = DAY["operating_report"](db)
        assert report["exceptions"] == ["3 blocked work item(s) not retried; read their records."]
        assert not db.connection.in_transaction  # the report's read snapshot is closed

        # A retry keeps where the answer goes.
        bot = FixtureBot()
        bot.updates = [message(50, "Prepare a stock brief.")]
        (phone,) = CHANNEL["poll"](db, queue, bot, OPERATORS)
        assert work_once(db, FailedModel(), work_id=phone, limits=LIMITS)["status"] == "BLOCKED"
        again = DAY["retry"](db, queue, phone)
        routes = [
            tuple(
                db.connection.execute(
                    "SELECT channel, recipient FROM channel_routes WHERE work_id = ?", (w,)
                ).fetchone()
            )
            for w in (phone, again)
        ]
        assert routes[0] == routes[1] == ("telegram:day-fixture", "123")
        print("ok   a vanished turn is blocked, not re-run; unretried blocks are flagged")
    finally:
        db.close()


def day(root):
    with supplier_process(root) as (proxy, supplier_path):
        supplier = SUPPLIER["SupplierClient"](proxy.endpoint, timeout=1)
        db, queue = DAY["open_day"](root / "agent.sqlite")
        research = worker = None
        work_once = DAY["work_once"]
        try:
            MEMORY["remember"](db, "lucy", "currency", "Euros", "lucy/old-request")
            MEMORY["remember"](db, "lucy", "currency", "USD", "lucy/correction")
            assert MEMORY["preferences"](db, "lucy", "currency")[0]["value"] == "USD"
            WAKE["schedule"](
                db,
                "morning",
                "lucy",
                "Prepare a stock brief.",
                first_due=time.time() - 1,
                interval_seconds=86_400,
            )
            assert len(WAKE["tick"](db, queue)) == 1 and WAKE["tick"](db, queue) == []
            failed = work_once(db, FailedModel(), limits=LIMITS)
            assert failed == {"status": "BLOCKED", "work": failed["work"], "loop": "MODEL_FAILED"}
            DAY["retry"](db, queue, failed["work"])
            morning = work_once(db, day_model(), limits=LIMITS)
            assert morning["status"] == "DONE", morning
            if MODEL["client"] is None:
                # The fixture drafts every positive need; a live model decides for itself.
                assert "Total: $26.00 USD." in morning["answer"]
            else:
                assert "Vanilla" in morning["answer"] or "SKU-VANILLA" in morning["answer"], morning
            print("ok   a due brief, a model outage kept as blocked, and its retry as new work")

            bot = FixtureBot()
            bot.updates = [
                message(1, "Prepare a stock brief."),
                message(1, "Prepare a stock brief."),
                message(2, "Spend everything", actor=999),
            ]
            assert len(CHANNEL["poll"](db, queue, bot, OPERATORS)) == 1
            db.close()
            db, queue = DAY["open_day"](root / "agent.sqlite")
            assert CHANNEL["poll"](db, queue, bot, OPERATORS) == []
            assert work_once(db, day_model(), limits=LIMITS)["status"] == "DONE"
            assert CHANNEL["deliver_one"](db, bot, OPERATORS) == "confirmed"
            assert len(bot.sent) == 1
            print("ok   one phone request from a repeat and a stranger, answered and delivered")

            for sku in ("SKU-VANILLA", "SKU-STRAWBERRY"):
                WAKE["watch"](db, "watch:" + sku, "lucy", sku)
            episodes = WAKE["scan"](db, queue)
            assert len(episodes) == 2 and WAKE["scan"](db, queue) == []
            for _ in episodes:
                result = work_once(db, day_model(), supplier=supplier, policy=POLICY, limits=LIMITS)
                assert result["status"] == "AWAITING_APPROVAL"
            assert work_once(db, NoNewReasoning(), supplier=supplier, policy=POLICY) == {
                "status": "IDLE"
            }  # waiting work is not taken
            proposals = {
                json.loads(row["proposal"])["sku"]: dict(row)
                for row in db.connection.execute("SELECT * FROM assistant_orders")
            }
            assert {sku: row["amount"] for sku, row in proposals.items()} == {
                "SKU-VANILLA": 1500,
                "SKU-STRAWBERRY": 1100,
            }
            assert all(row["status"] == "DRAFT" for row in proposals.values())
            assert remote_orders(supplier_path) == []
            print("ok   two stock episodes, two exact proposals, nothing sent before approval")

            child_work = DELEGATION["delegate"](
                queue,
                morning["work"],
                DELEGATION["Inquiry"](sku="SKU-VANILLA", guests=41),
                deadline=time.time() + 60,
                estimated_call_cents=2,
                budget_cents=20,
            )
            research = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    RESEARCH,
                    str(LEARNER / "profrod_sovereign_agent_ch20_day_learner.py"),
                    str(root / "agent.sqlite"),
                    str(child_work),
                ],
                cwd=BOOK.parents[1],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=CHILD_ENV,
            )
            bot.updates = [
                message(10 + i, f"/approve {row['id']} {row['digest']}")
                for i, row in enumerate(proposals.values())
            ]
            commands = CHANNEL["poll"](db, queue, bot, OPERATORS)
            assert len(commands) == 2
            for command in commands:
                result = work_once(db, NoNewReasoning(), policy=POLICY, work_id=command)
                assert result["status"] == "DONE"
            vanilla, strawberry = proposals["SKU-VANILLA"], proposals["SKU-STRAWBERRY"]
            worker = subprocess.Popen(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--worker",
                    str(root),
                    "--supplier",
                    proxy.endpoint,
                    "--work",
                    str(vanilla["work_id"]),
                    "--order",
                    vanilla["id"],
                ],
                cwd=BOOK.parents[1],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=CHILD_ENV,
            )
            ready = root / "child-ready.json"
            wait_until(lambda: ready.exists() or worker.poll() is not None)
            assert ready.exists(), worker.communicate(timeout=2)
            observed = json.loads(ready.read_text())
            assert len(remote_orders(supplier_path)) == 1  # committed; the reply was lost
            worker.send_signal(signal.SIGKILL)
            worker.communicate(timeout=3)
            assert worker.returncode == -signal.SIGKILL
            wait_until(lambda: time.time() > observed["expiry"] + 0.05)
            replaced = work_once(
                db, NoNewReasoning(), supplier=supplier, policy=POLICY, work_id=vanilla["work_id"]
            )
            assert replaced["status"] == "DONE", replaced
            first = work_once(
                db,
                NoNewReasoning(),
                supplier=supplier,
                policy=POLICY,
                work_id=strawberry["work_id"],
            )
            assert first["status"] == "UNKNOWN"  # this operation's first reply was lost too
            second = work_once(
                db,
                NoNewReasoning(),
                supplier=supplier,
                policy=POLICY,
                work_id=strawberry["work_id"],
            )
            assert second["status"] == "DONE"
            print("ok   approvals from the phone; a killed worker replaced; lost replies looked up")

            stdout, stderr = research.communicate(timeout=20)
            assert research.returncode == 0, stderr
            quote = json.loads(stdout)
            assert quote["status"] == "DONE"
            assert (quote["quote"]["tubs"], quote["quote"]["total_cents"]) == (5, 2500)
            receive = DAY["receive"]
            assert receive(
                db, vanilla["id"], "day-delivery-vanilla", actor="123", policy=POLICY
            ) == ("received")
            assert receive(
                db, vanilla["id"], "day-delivery-vanilla", actor="123", policy=POLICY
            ) == ("duplicate")
            assert refused(
                ValueError,
                lambda: receive(db, vanilla["id"], "another-reference", actor="123", policy=POLICY),
            )
            assert WAKE["scan"](db, queue) == []
            while CHANNEL["deliver_one"](db, bot, OPERATORS) is not None:
                pass
            remote = remote_orders(supplier_path)
            assert {operation for operation, _ in remote} == {vanilla["id"], strawberry["id"]}
            cents = sum(
                json.loads(raw)["quantity"] * json.loads(raw)["unit_cost_cents"]
                for _, raw in remote
            )
            assert cents == 2600
            report = DAY["operating_report"](db)
            assert report["orders"] == {"CONFIRMED": 1, "DELIVERED": 1}
            assert report["spending"] == {
                "accepted_cents": 2600,
                "reserved_cents": 0,
                "order_totals_match": True,
            }
            assert report["open_work"] == [] and report["exceptions"] == [], report
            assert [(s["on_hand"], s["on_order"], s["needed"]) for s in report["stock"]] == [
                (12, 0, 0),
                (1, 4, 0),
                (8, 0, 0),
            ]
            assert report["research_quotes_completed"] == 1
            with db.immediate() as connection:
                connection.execute("UPDATE assistant_spending SET spent_cents = 2601")
            corrupt = DAY["operating_report"](db)
            assert not corrupt["spending"]["order_totals_match"]
            assert corrupt["exceptions"] == ["Spending ledger and retained order totals disagree."]
            with db.immediate() as connection:
                connection.execute("UPDATE assistant_spending SET spent_cents = 2600")
            text = report["text"]
            assert "USD 26.00" in text and "USD 0.00" in text and "4 pending replenishment" in text
            evidence = {
                "scope": (
                    "Accelerated deterministic business day on the learner's code; real supplier,"
                    " worker and research processes, a reply-losing proxy and a fixture phone. No"
                    " live phone, real purchases or uptime claim."
                ),
                "faults": [
                    "model outage",
                    "duplicate message",
                    "unauthorized message",
                    "stale preference corrected",
                    "supplier reply loss",
                    "worker SIGKILL",
                ],
                "independent_supplier_orders": len(remote),
                "independent_supplier_cents": cents,
                "killed_worker_exit": worker.returncode,
                "phone_messages_sent": len(bot.sent),
                "morning_answer": morning["answer"],
                "model": "offline fixture" if MODEL["client"] is None else MODEL["name"],
                "claude": None if MODEL["client"] is None else MODEL["client"].report(),
                "report": {key: value for key, value in report.items() if key != "text"},
                "manuscript_checkpoint_sha256": hashlib.sha256(
                    Path(__file__).read_bytes()
                ).hexdigest(),
            }
            (root / "report.txt").write_text(text + "\n")
            (root / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
            print(text)
            print(
                "Independent supplier: 2 orders, 2600 cents; killed worker replaced; "
                "duplicate delivery receipt counted once."
            )
        finally:
            for process in (worker, research):
                if process is not None:
                    if process.poll() is None:
                        process.kill()
                    process.communicate(timeout=5)
            db.close()


RELIABILITY = runpy.run_path(
    str(BOOK / "learner/profrod_sovereign_agent_ch20_reliability_learner.py")
)


def reliability_arithmetic():
    """Part A's formulas checked independently; the receipt's counts recomputed from its runs."""
    assert math.isclose(RELIABILITY["series_success"]([0.9, 0.5]), 0.45)
    assert math.isclose(RELIABILITY["per_step_needed"](0.99, 12) ** 12, 0.99)
    low, high = RELIABILITY["wilson_interval"](20, 20)
    assert round(low, 3) == 0.839 and high == 1.0
    assert RELIABILITY["dollars"](2600) == "$26.00" and RELIABILITY["dollars"](175) == "$1.75"
    assert RELIABILITY["states_amount"]("Spent $26.00 today.", 2600)
    assert not RELIABILITY["states_amount"]("Spent $2600 today.", 2600)
    print("ok   a day is a product of its steps; one passing day bounds little")
    receipt = json.loads(
        (BOOK.parents[1] / "docs/evidence/book-ch20/ch20-report-receipt-v1.json").read_text()
    )
    for row in receipt["rows"]:
        runs = [r for r in receipt["runs"] if r["model"] == row["model"]]
        for field in ("total_stated", "wrong_total", "unknown_flagged", "cents_as_dollars"):
            assert row[field] == sum(r[field] for r in runs)
        for run in runs:
            day = receipt["days"][run["day"] - 1]
            accepted = sum(o["amount_cents"] for o in day["orders"] if o["status"] == "ACCEPTED")
            assert run["accepted_cents"] == accepted
            assert run["total_stated"] == RELIABILITY["states_amount"](run["report"], accepted)
    print("ok   report counts recompute; accepted totals and stated amounts regraded from records")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", type=Path)
    parser.add_argument("--supplier")
    parser.add_argument("--work")
    parser.add_argument("--order")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--claude", metavar="MODEL", help="Claude for every model turn of the day")
    args = parser.parse_args()
    if args.claude:
        claude = runpy.run_path(
            str(BOOK / "experiments/profrod_sovereign_agent_claude_messages_v1.py")
        )
        client = claude["Claude"](max_usd=1.0)
        MODEL.update(
            client=client,
            name=args.claude,
            factory=lambda: claude["LoopModel"](
                client, args.claude, DAY["ModelTurn"], DAY["ToolCall"]
            ),
        )
    if args.worker:
        child(args.worker, args.supplier, args.work, args.order)
        return
    reliability_arithmetic()
    claude_day()
    with tempfile.TemporaryDirectory(prefix="lucy-bounds-") as temporary:
        boundaries(Path(temporary))
    if args.output:
        args.output.mkdir(mode=0o700, parents=True, exist_ok=False)
        day(args.output.resolve())
    else:
        with tempfile.TemporaryDirectory(prefix="lucy-day-") as temporary:
            day(Path(temporary))


if __name__ == "__main__":
    main()
