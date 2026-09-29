# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 18: concurrent research and stock work, cancellation and bounded replacement.

Every function it calls is the learner's own: Chapter 18's delegation file on Chapter 13's
worker, Chapter 11's shop, Chapter 8's queue, Chapter 4's store, Chapter 3's loop and Chapter
2's tools.
"""

import json
import math
import os
import runpy
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

BOOK = Path(__file__).resolve().parents[1]
DELEGATION = runpy.run_path(
    str(BOOK / "learner/profrod_sovereign_agent_ch18_delegation_learner.py")
)
LOOP, WORKER = DELEGATION["LOOP"], DELEGATION["WORKER"]
open_delegation_shop, Inquiry, quote = (
    DELEGATION["open_delegation_shop"],
    DELEGATION["Inquiry"],
    DELEGATION["quote"],
)
delegate, claim, cancel, expire = (
    DELEGATION["delegate"],
    DELEGATION["claim"],
    DELEGATION["cancel"],
    DELEGATION["expire"],
)
reserve_model_call, research_once, shop_once = (
    DELEGATION["reserve_model_call"],
    DELEGATION["research_once"],
    DELEGATION["shop_once"],
)
OfflineCateringModel, enqueue = DELEGATION["OfflineCateringModel"], WORKER["enqueue"]
ModelTurn, ToolCall = DELEGATION["ModelTurn"], DELEGATION["ToolCall"]
StockEvent = DELEGATION["APPROVAL"]["StockEvent"]


def shop_model():
    return LOOP["ReplayModel"](LOOP["opening_turns"]())


def one(db, sql, *values):
    return db.connection.execute(sql, values).fetchone()


def outcome(db, work):
    row = one(db, "SELECT status FROM outcomes WHERE work_id = ?", work)
    return None if row is None else row[0]


def refused(error, action):
    try:
        action()
    except error:
        return True
    return False


def child():
    root = Path(sys.argv[2])
    identifier = int(sys.argv[3])
    gate = Path(sys.argv[4])
    output = Path(sys.argv[5])
    db, _ = open_delegation_shop(root / "agent.sqlite")

    class WaitingModel(OfflineCateringModel):
        announced = False

        def complete(self, *args, **kwargs):
            if not self.announced:
                self.announced = True
                gate.with_suffix(".ready").write_text("model entered")
                end = time.monotonic() + 10
                while not gate.exists():
                    if time.monotonic() > end:
                        raise TimeoutError("test release not received")
                    time.sleep(0.01)
            return super().complete(*args, **kwargs)

    result = research_once(db, WaitingModel(), work_id=identifier)
    output.write_text(json.dumps(result))
    db.close()


def delegation_arithmetic():
    """Part A's formulas by independent checks, and the receipt recomputed from its runs."""
    amdahl, vote = DELEGATION["amdahl_speedup"], DELEGATION["majority_accuracy"]
    assert amdahl(1.0, 4) == 4 and amdahl(0.0, 8) == 1
    assert math.isclose(amdahl(0.9, 10**9), 10, rel_tol=1e-6)
    assert math.isclose(vote(0.5, 5), 0.5)
    assert all(vote(p, 3) > p for p in (0.6, 0.8, 0.95)) and all(vote(p, 3) < p for p in (0.1, 0.4))
    assert math.isclose(vote(0.7, 3), 0.7**3 + 3 * 0.7**2 * 0.3)
    print("ok   Amdahl's limits, and Condorcet: voting helps above one half, hurts below")
    receipt = json.loads(
        (BOOK.parents[1] / "docs/evidence/book-ch18/ch18-delegation-receipt-v1.json").read_text()
    )
    correct = [[False] * 10 for _ in range(12)]
    for run in receipt["runs"]:
        correct[run["question"]][run["sample"]] = run["correct"]
    accuracy = [round(sum(row) / 10, 2) for row in correct]
    assert accuracy == receipt["sampling"]["accuracy"]
    for task in receipt["sampling"]["composed"]:
        joint = sum(all(correct[q][s] for q in task["questions"]) for s in range(10)) / 10
        assert joint == task["measured"]
    print("ok   accuracies and composed successes recompute from the retained answers")


def boundaries():
    """Quote arithmetic against authored answers, and the inquiry's strict refusals."""
    for guests, tubs, cents in (
        (1, 1, 500),
        (10, 1, 500),
        (11, 2, 1000),
        (41, 5, 2500),
        (200, 20, 10000),
    ):
        result = quote(Inquiry(sku="SKU-VANILLA", guests=guests))
        assert (result["tubs"], result["total_cents"]) == (tubs, cents)
        assert result["currency"] == "USD" and result["stock_reserved"] is False
    # Strawberry costs Lucy 275 cents a tub from the supplier and sells for 500.
    assert quote(Inquiry(sku="SKU-STRAWBERRY", guests=9))["total_cents"] == 500
    bad = (
        {"sku": "SKU-VANILLA", "guests": True},
        {"sku": "SKU-VANILLA", "guests": 0},
        {"sku": "SKU-VANILLA", "guests": 201},
        {"sku": "SKU-VANILLA", "guests": "41"},
        {"sku": "SKU-VANILLA", "guests": 4, "stock": "reserve"},
    )
    for arguments in bad:
        assert refused(ValueError, lambda a=arguments: Inquiry.model_validate(a, strict=True))
    assert refused(ValueError, lambda: quote(Inquiry(sku="SKU-MINT", guests=4)))
    print("Authored quote boundary cases:", 5, "; refused inquiries:", len(bad) + 1)


def handoff(root):
    """One immutable child per parent, committed together with its contract or not at all."""
    db, queue = open_delegation_shop(root / "handoff.sqlite")
    parent = enqueue(queue, "parent:handoff", "lucy", "Prepare the stock brief.")
    inquiry = Inquiry(sku="SKU-VANILLA", guests=41)
    deadline = time.time() + 30
    terms = {"deadline": deadline, "estimated_call_cents": 7}
    identifier = delegate(queue, parent, inquiry, **terms)
    assert delegate(queue, parent, inquiry, **terms) == identifier
    contract = one(
        db,
        "SELECT d.billing_session, w.session_id, w.state FROM delegations d"
        " JOIN work w ON w.work_id = d.work_id WHERE d.work_id = ?",
        identifier,
    )
    assert tuple(contract) == ("lucy", f"research:{parent}", "pending")
    changed = (
        lambda: delegate(queue, parent, Inquiry(sku="SKU-VANILLA", guests=42), **terms),
        lambda: delegate(queue, parent, inquiry, deadline=deadline + 1, estimated_call_cents=7),
        lambda: delegate(queue, parent, inquiry, deadline=deadline, estimated_call_cents=6),
        lambda: delegate(queue, parent, inquiry, model_calls=3, **terms),
        lambda: delegate(queue, parent, inquiry, budget_cents=99, **terms),
    )
    assert all(refused(ValueError, attempt) for attempt in changed)
    unbounded = (
        {"deadline": time.time() - 1},
        {"deadline": time.time() + 3601},
        {"deadline": math.inf},
        {"deadline": deadline, "model_calls": 0},
        {"deadline": deadline, "model_calls": 9},
        {"deadline": deadline, "model_calls": True},
        {"deadline": deadline, "estimated_call_cents": -1},
        {"deadline": deadline, "budget_cents": 0},
        {"deadline": deadline, "budget_cents": 1001},
    )
    other = enqueue(queue, "parent:other", "lucy", "brief")
    assert all(
        refused(ValueError, lambda t=t: delegate(queue, other, inquiry, **t)) for t in unbounded
    )
    unknown = Inquiry(sku="SKU-MINT", guests=4)
    assert refused(ValueError, lambda: delegate(queue, other, unknown, **terms))
    assert refused(PermissionError, lambda: delegate(queue, identifier, inquiry, **terms))
    assert refused(PermissionError, lambda: delegate(queue, 999, inquiry, **terms))
    withdrawn = enqueue(queue, "parent:withdrawn", "lucy", "brief")
    cancel(db, withdrawn)
    assert outcome(db, withdrawn) == "CANCELED"
    assert refused(PermissionError, lambda: delegate(queue, withdrawn, inquiry, **terms))
    db.connection.execute(
        "CREATE TEMP TRIGGER fail_event BEFORE INSERT ON order_events"
        " BEGIN SELECT RAISE(ABORT, 'injected event failure'); END"
    )
    assert refused(sqlite3.IntegrityError, lambda: delegate(queue, other, inquiry, **terms))
    db.connection.execute("DROP TRIGGER fail_event")
    assert one(db, "SELECT count(*) FROM work WHERE source_id = ?", f"delegation:{other}")[0] == 0
    assert one(db, "SELECT count(*) FROM delegations WHERE parent_id = ?", other)[0] == 0
    (open_now,) = one(db, "SELECT count(*) FROM work WHERE state IN ('pending', 'running')")
    full = DELEGATION["APPROVAL"]["WorkQueue"](db, capacity=open_now)
    assert refused(ValueError, lambda: delegate(full, other, inquiry, **terms))
    assert one(db, "SELECT count(*) FROM delegations WHERE parent_id = ?", other)[0] == 0
    assert delegate(queue, other, inquiry, **terms) != identifier
    print("Same handoff, same child:", True, "; changed terms refused:", len(changed))
    print("Recursive, unknown and canceled parents: refused; a failed handoff leaves no child")
    db.close()


def roles(root):
    """A shop worker never takes a contract; a research worker never takes shop work."""
    db, queue = open_delegation_shop(root / "roles.sqlite")
    parent = enqueue(queue, "parent:roles", "lucy", "brief")
    child_id = delegate(
        queue, parent, Inquiry(sku="SKU-VANILLA", guests=4), deadline=time.time() + 30
    )
    assert claim(db, "researcher", role="research", work_id=parent) is None
    held = claim(db, "shop", role="shop")
    assert held is not None and held.work_id == parent
    assert claim(db, "shop", role="shop") is None
    assert shop_once(db, shop_model()) == {"status": "IDLE"}
    research = claim(db, "researcher", role="research")
    assert research is not None and research.work_id == child_id
    assert refused(ValueError, lambda: claim(db, "buyer", role="buyer"))
    assert refused(ValueError, lambda: claim(db, "a#1", role="shop"))
    later = enqueue(queue, "parent:later", "lucy", "brief")
    assert claim(db, "shop", role="shop", work_id=later) is None
    elsewhere = enqueue(queue, "shop:elsewhere", "maria", "brief")
    assert claim(db, "shop", role="shop").work_id == elsewhere
    db.apply(StockEvent("delivery:roles", "SKU-VANILLA", 6, "delivery"))
    listed = DELEGATION["stock_tools"](db).invoke(ToolCall(id="s", name="list_stock", arguments={}))
    vanilla = next(row for row in listed["value"] if row["sku"] == "SKU-VANILLA")
    assert (vanilla["on_hand"], vanilla["needed"]) == (8, 0)
    print("Roles: the shop worker took the parent only, the research worker the child only")
    print("A session's second turn waits while its first is held; other sessions proceed")
    db.close()


def graded(root):
    """Research is graded on the tool's checked result, and fenced calls stop at lost authority."""
    db, queue = open_delegation_shop(root / "graded.sqlite")

    def contract(name, **terms):
        parent = enqueue(queue, "parent:" + name, "lucy", "brief")
        terms = {"deadline": time.time() + 30, **terms}
        return delegate(queue, parent, Inquiry(sku="SKU-VANILLA", guests=41), **terms)

    class Unchecked:
        def complete(self, messages, tools, *, timeout, max_output_tokens):
            return ModelTurn("Five tubs, USD 25.00.")

    class Broadening(OfflineCateringModel):
        def complete(self, messages, tools, *, timeout, max_output_tokens):
            if messages[-1]["role"] != "tool":
                wider = {"sku": "SKU-VANILLA", "guests": 42}
                return ModelTurn(calls=(ToolCall(id="q", name="catering_quote", arguments=wider),))
            return ModelTurn("Done.")

    for model in (Unchecked(), Broadening()):
        work = contract(type(model).__name__)
        result = research_once(db, model, work_id=work)
        assert result["status"] == "BLOCKED" and result["report"]["quote"] is None
        assert outcome(db, work) == "BLOCKED"
    # In one run, Chapter 3's loop stops at the contract's limits before asking for more.
    tight = contract("tight", estimated_call_cents=7, budget_cents=10)
    assert research_once(db, OfflineCateringModel(), work_id=tight)["status"] == "BLOCKED"
    assert one(db, "SELECT model_calls FROM delegations WHERE work_id = ?", tight)[0] == 1
    # After a replacement, only the durable count knows what the old generation spent.
    for name, terms, spent in (
        ("calls", {"model_calls": 2}, 0),
        ("cents", {"estimated_call_cents": 7, "budget_cents": 14}, 7),
    ):
        work = contract(name, **terms)
        old = claim(db, "old", role="research", work_id=work, ttl=0.1)
        reserve_model_call(db, old, spent)
        time.sleep(0.15)
        result = research_once(db, OfflineCateringModel(), work_id=work)
        assert result == {"status": "AUTHORITY_STOP", "work": work}
        assert outcome(db, work) == "BLOCKED"
        assert one(db, "SELECT model_calls FROM delegations WHERE work_id = ?", work)[0] == 2
    lapsing = contract("lapsing", deadline=time.time() + 0.2)
    held = claim(db, "research", role="research", work_id=lapsing)
    time.sleep(0.25)
    assert refused(PermissionError, lambda: reserve_model_call(db, held, 0))
    print("Unchecked and broadened answers: BLOCKED; an exhausted allowance: AUTHORITY_STOP")
    db.close()
    db, queue = open_delegation_shop(root / "stale.sqlite")
    work = enqueue(queue, "shop:stale", "lucy", "brief")

    class CancelsItsTurn:
        def complete(self, messages, tools, *, timeout, max_output_tokens):
            cancel(db, work)
            return ModelTurn("Done.")

    assert shop_once(db, CancelsItsTurn()) == {"status": "STALE", "work": work}
    assert outcome(db, work) == "CANCELED"
    ran = []
    probe = DELEGATION["ExecutableTool"](
        "probe", "Record a call.", DELEGATION["NoArguments"], lambda _: ran.append(1) or "ran"
    )
    other = enqueue(queue, "shop:probe", "lucy", "brief")
    held = claim(db, "shop", role="shop", work_id=other)
    tools = DELEGATION["HeldTools"](
        db, held, DELEGATION["Dispatcher"]([probe], allowed=frozenset({"probe"}))
    )
    cancel(db, other)
    call = ToolCall(id="p", name="probe", arguments={})
    assert refused(DELEGATION["AuthorityLostError"], lambda: tools.invoke(call))
    assert ran == []
    print("A turn canceled mid-call: STALE; a canceled holder's tool never runs")
    db.close()


def processes(root):
    """Research waits inside its model call in another process while stock work completes."""
    db, queue = open_delegation_shop(root / "agent.sqlite")
    for cancel_child in (False, True):
        label = "cancel" if cancel_child else "complete"
        parent = enqueue(queue, "parent:" + label, "lucy", "Prepare the stock brief.")
        inquiry = Inquiry(sku="SKU-VANILLA", guests=41)
        identifier = delegate(
            queue, parent, inquiry, deadline=time.time() + 30, estimated_call_cents=7
        )
        gate = root / (label + ".release")
        output = root / (label + ".json")
        env = {
            k: v
            for k, v in os.environ.items()
            if k in {"PATH", "SYSTEMROOT", "TMPDIR", "LANG", "LC_ALL"}
        }
        process = subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "child",
                str(root),
                str(identifier),
                str(gate),
                str(output),
            ],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            end = time.monotonic() + 10
            while not gate.with_suffix(".ready").exists():
                if process.poll() is not None:
                    raise AssertionError(process.communicate())
                assert time.monotonic() < end, "research child did not claim"
                time.sleep(0.01)
            assert one(db, "SELECT state FROM work WHERE work_id = ?", identifier)[0] == "running"
            assert shop_once(db, shop_model())["status"] == "DONE"
            assert outcome(db, parent) == "DONE"
            assert process.poll() is None
            print(label + ": stock done while research process waits", True)
            if cancel_child:
                cancel(db, parent)
                assert outcome(db, parent) == "DONE"
            gate.write_text("continue")
            process.communicate(timeout=10)
            assert process.returncode == 0
            result = json.loads(output.read_text())
            if cancel_child:
                assert result["status"] == "AUTHORITY_STOP"
                assert outcome(db, identifier) == "CANCELED"
                assert (
                    one(db, "SELECT count(*) FROM transcript WHERE work_id = ?", identifier)[0] == 0
                )
                assert outcome(db, parent) == "DONE"
                print("Cancellation preserves completed stock result:", True)
            else:
                assert result["status"] == "DONE"
                report = result["report"]
                assert report["quote"]["tubs"] == 5 and report["quote"]["total_cents"] == 2500
                assert report["assignment_usage"] == {
                    "model_calls": 2,
                    "estimated_cost_cents": 14,
                }
                assert report["baseline"]["model_calls"] == 0
                assert outcome(db, identifier) == "DONE"
                written = db.connection.execute(
                    "SELECT generation FROM transcript WHERE work_id = ?", (identifier,)
                ).fetchall()
                assert [row[0] for row in written] == [1, 1, 1]
                repeat = research_once(db, OfflineCateringModel(), work_id=identifier)
                assert repeat == {"status": "IDLE"}
                print("Child quote:", 5, "tubs", 2500, "cents; repeat research work", "IDLE")
        finally:
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=5)
    return db, queue


def lapses(db, queue):
    """An unclaimed contract expires by elapsed time; a replacement cannot reset its allowance."""
    parent = enqueue(queue, "parent:expired", "lucy", "brief")
    identifier = delegate(
        queue, parent, Inquiry(sku="SKU-VANILLA", guests=1), deadline=time.time() + 0.1
    )
    time.sleep(0.15)
    assert research_once(db, OfflineCateringModel(), work_id=identifier) == {"status": "IDLE"}
    assert outcome(db, identifier) == "CANCELED"
    assert expire(db) == 0
    print("Expired unclaimed work:", "CANCELED")
    parent = enqueue(queue, "parent:budget", "lucy", "brief")
    identifier = delegate(
        queue,
        parent,
        Inquiry(sku="SKU-VANILLA", guests=1),
        deadline=time.time() + 30,
        model_calls=1,
        estimated_call_cents=5,
    )
    old = claim(db, "old-research", role="research", work_id=identifier, ttl=0.1)
    assert old is not None
    assert refused(PermissionError, lambda: reserve_model_call(db, old, 4))
    reserve_model_call(db, old, 5)
    time.sleep(0.15)
    replacement = claim(db, "replacement", role="research", work_id=identifier)
    assert replacement is not None and replacement.generation == old.generation + 1
    assert refused(PermissionError, lambda: reserve_model_call(db, old, 5))
    assert refused(PermissionError, lambda: reserve_model_call(db, replacement, 5))
    calls = one(db, "SELECT model_calls FROM delegations WHERE work_id = ?", identifier)[0]
    assert calls == 1
    print("Replacement cannot reset assignment allowance:", True)


def stop_and_allowance(root):
    """A stop hands the work straight back; the daily account refuses past its allowance."""
    db, queue = open_delegation_shop(root / "stop.sqlite")
    parent = enqueue(queue, "parent:stop", "lucy", "brief")
    identifier = delegate(
        queue, parent, Inquiry(sku="SKU-VANILLA", guests=4), deadline=time.time() + 30
    )
    stop = []

    class StopAfterReply(OfflineCateringModel):
        def complete(self, *args, **kwargs):
            stop.append(True)
            return super().complete(*args, **kwargs)

    result = research_once(db, StopAfterReply(), work_id=identifier, should_stop=lambda: bool(stop))
    assert result == {"status": "STOPPED", "work": identifier}
    again = claim(db, "next", role="research", work_id=identifier)
    assert again is not None and again.generation == 2
    assert research_once(db, OfflineCateringModel(), should_stop=lambda: True) == {
        "status": "STOPPED"
    }
    shop = enqueue(queue, "shop:allowance", "lucy", "brief")
    held = claim(db, "shop", role="shop", work_id=shop)
    assert held is not None and held.work_id == shop
    assert refused(ValueError, lambda: reserve_model_call(db, held, -1))
    assert refused(ValueError, lambda: reserve_model_call(db, held, True))
    before = one(db, "SELECT model_calls, estimated_cost_cents FROM model_usage")
    assert refused(PermissionError, lambda: reserve_model_call(db, held, 501))
    assert one(db, "SELECT model_calls, estimated_cost_cents FROM model_usage") == before
    reserve_model_call(db, held, 500 - before[1])
    assert refused(PermissionError, lambda: reserve_model_call(db, held, 1))
    while one(db, "SELECT model_calls FROM model_usage")[0] < 200:
        reserve_model_call(db, held, 0)
    assert refused(PermissionError, lambda: reserve_model_call(db, held, 0))
    assert tuple(one(db, "SELECT model_calls, estimated_cost_cents FROM model_usage")) == (200, 500)
    print("Stop hands the work back at once; the daily account refuses call 201 and cent 501")
    db.close()


def main():
    delegation_arithmetic()
    boundaries()
    with tempfile.TemporaryDirectory(prefix="lucy-delegation-") as temporary:
        root = Path(temporary)
        handoff(root)
        roles(root)
        graded(root)
        stop_and_allowance(root)
        db, queue = processes(root)
        stock = db.connection.execute("SELECT sku, tubs FROM stock ORDER BY sku").fetchall()
        lapses(db, queue)
        opening = {sku: row["on_hand"] for sku, row in DELEGATION["APPROVAL"]["CATALOG"].items()}
        assert dict(stock) == opening
        assert db.connection.execute("SELECT sku, tubs FROM stock ORDER BY sku").fetchall() == stock
        assert one(db, "SELECT count(*) FROM assistant_orders")[0] == 0
        usage = db.connection.execute(
            "SELECT billing_session, sum(model_calls), sum(estimated_cost_cents)"
            " FROM model_usage GROUP BY billing_session"
        ).fetchall()
        assert [tuple(row) for row in usage] == [("lucy", 10, 26)], usage
        print("One shared billing account:", 10, "calls and", 26, "estimated cents")
        print("Purchases and stock changes:", 0)
        print("Architecture decision: retain the function for this fixed calculation")
        db.close()


if __name__ == "__main__":
    child() if len(sys.argv) > 1 and sys.argv[1] == "child" else main()
