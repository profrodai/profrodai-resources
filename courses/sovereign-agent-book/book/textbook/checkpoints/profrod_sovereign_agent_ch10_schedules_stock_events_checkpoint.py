# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 10: durable clock jobs and stock episodes create draft work while unattended.

Every function it calls is the learner's own: Chapter 10's wake-ups on Chapter 9's channel,
Chapter 8's queue, Chapter 7's skills and context, Chapter 5's memory, Chapter 4's store, and
Chapter 3's loop. The unattended worker is the learner file itself, run as a separate process.
"""

import argparse
import json
import math
import os
import runpy
import subprocess
import sys
import tempfile
import time
from pathlib import Path

BOOK = Path(__file__).resolve().parents[1]
QUEUE = runpy.run_path(str(BOOK / "learner/profrod_sovereign_agent_ch10_queueing_learner.py"))
WAKEUPS = BOOK / "learner/profrod_sovereign_agent_ch10_wakeups_learner.py"
WAKE = runpy.run_path(str(WAKEUPS))
MEMORY, CHANNEL = WAKE["MEMORY"], WAKE["CHANNEL"]
PROMPT = "Prepare replenishment drafts from current stock. State USD amounts."
READ_AND_DRAFT = {"list_stock", "supplier", "draft_order"}


def queueing_arithmetic():
    """Part A's formulas by independent checks, and the receipt recomputed from its records."""
    pk, exponential = QUEUE["pk_wait"], QUEUE["exponential_wait"]
    assert math.isclose(exponential(0.5, 1.0), pk(0.5, 1.0, 2.0)) and exponential(0.5, 1.0) == 1.0
    assert pk(0.5, 1.0, 1.0) == 0.5  # constant service waits half as long as exponential
    rate = QUEUE["highest_rate"](2.0, 0.5, 0.4)
    assert math.isclose(pk(rate, 0.5, 0.4), 2.0)
    gaps = QUEUE["arrivals"](4.0, 20_000, seed=1)
    assert abs(gaps[-1] / len(gaps) - 0.25) < 0.01  # the mean gap is 1 / rate
    print("ok   Pollaczek-Khinchine, its exponential case and the rate for a target wait")
    receipt = json.loads(
        (BOOK.parents[1] / "docs/evidence/book-ch10/ch10-queueing-receipt-v1.json").read_text()
    )
    for pilot in receipt["pilots"].values():
        mean, second = QUEUE["moments"](pilot["service_seconds"])
        assert (round(mean, 4), round(second, 4)) == (pilot["mean_service"], pilot["second_moment"])
    for row, run in zip(receipt["rows"], receipt["runs"], strict=True):
        records = run["records"]
        waits = [r["started"] - r["arrived"] for r in records]
        assert round(sum(waits) / len(waits), 3) == row["measured_mean_wait"]
        assert all(
            later["started"] >= earlier["finished"]
            for earlier, later in zip(records, records[1:], strict=False)
        )
    print("ok   pilot moments and mean waits recompute; one job served at a time, in order")


def claude_receipt():
    """The recorded Claude runs: every check passed in both processes, the reports agree with the
    drafts, and the costs add up."""
    receipt = json.loads(
        (
            BOOK.parents[1] / "docs/evidence/book-ch10/ch10-unattended-claude-receipt-v1.json"
        ).read_text()
    )
    for run in receipt["models"].values():
        assert run["passed"] and run["checks"][-1] == "Worker stopped cleanly: True"
        for turn in run["turns"].values():
            total = turn["report"].rsplit("Total: ", 1)[1].split(" ")[0]
            assert turn["narration_states_report_total"] == (total in turn["model_narration"])
        assert run["turns"]["unattended_episode"]["report"] == (
            'Draft estimates:\n- "SKU-VANILLA": 7 tubs, $17.50 USD.\nTotal: $17.50 USD.'
        )
        assert math.isclose(run["costUsd"], sum(side["costUsd"] for side in run["claude"].values()))
    total = sum(run["costUsd"] for run in receipt["models"].values())
    assert math.isclose(receipt["costUsd"], total, abs_tol=1e-4)
    print(
        f"ok   the Claude runs passed in parent and child; they cost {total:.4f} USD at list price"
    )


def observed_drafts(messages):
    names = {
        call["id"]: call["function"]["name"]
        for message in messages
        for call in message.get("tool_calls", [])
    }
    drafts = []
    for message in messages:
        if message["role"] == "tool" and names.get(message["tool_call_id"]) == "draft_order":
            value = json.loads(message["content"])
            if value.get("ok") is True:
                draft = value["value"]
                drafts.append((draft["sku"], draft["quantity"], draft["total_cents"]))
    return sorted(drafts)


def called_tools(messages):
    return [
        call["function"]["name"] for message in messages for call in message.get("tool_calls", [])
    ]


def refused(error, action):
    try:
        action()
    except error:
        return True
    return False


def one(db, sql, *values):
    return db.connection.execute(sql, values).fetchone()[0]


def prepare(path, *, capacity=10):
    db, queue = WAKE["open_shop"](path, capacity=capacity)
    WAKE["seed_shop"](db)
    CHANNEL["activate_opening_skill"](db)
    return db, queue


def events(db, kind):
    return [
        json.loads(row[0])
        for row in db.connection.execute(
            "SELECT payload FROM memory_events WHERE kind=? ORDER BY seq", (kind,)
        )
    ]


def boundaries(root):
    """Configuration, capacity, scope and reporting boundaries, with no model and no clock."""
    db, queue = prepare(root / "boundaries.sqlite", capacity=1)
    WAKE["seed_shop"](db)
    counted = {row["sku"]: row["on_hand"] for row in WAKE["stock_rows"](db.connection)}
    assert counted == {"SKU-CHOCOLATE": 12, "SKU-STRAWBERRY": 1, "SKU-VANILLA": 2}  # seeded once
    route = WAKE["validate_route"]
    route("local", "")
    route("telegram:teaching", "123")
    assert refused(ValueError, lambda: route("telegram:teaching", "Lucy"))
    assert refused(ValueError, lambda: route("local", "123"))
    assert refused(ValueError, lambda: route("email", "lucy@example.com"))
    schedule = WAKE["schedule"]
    schedule(db, "morning", "lucy", PROMPT, first_due=100.0, interval_seconds=10)
    assert refused(
        ValueError,
        lambda: schedule(db, "morning", "lucy", "Other", first_due=100.0, interval_seconds=10),
    )
    for bad in ({"interval_seconds": 0}, {"interval_seconds": 1.5}, {"first_due": math.inf}):
        values = {"first_due": 100.0, "interval_seconds": 10, **bad}
        assert refused(
            ValueError, lambda values=values: schedule(db, "x", "lucy", PROMPT, **values)
        )
    assert refused(
        ValueError,
        lambda: schedule(db, "x" * 101, "lucy", PROMPT, first_due=100.0, interval_seconds=10),
    )
    print("ok   routes, job identities, intervals and due times are validated at registration")

    watch = WAKE["watch"]
    watch(db, "vanilla-low", "lucy", "SKU-VANILLA")
    watch(db, "vanilla-low", "lucy", "SKU-VANILLA")
    assert one(db, "SELECT count(*) FROM stock_conditions") == 1
    assert refused(ValueError, lambda: watch(db, "vanilla-low", "lucy", "SKU-STRAWBERRY"))
    assert refused(ValueError, lambda: watch(db, "vanilla-2", "lucy", "SKU-VANILLA"))
    assert refused(ValueError, lambda: watch(db, "pistachio", "lucy", "SKU-PISTACHIO"))
    print("ok   one immutable condition per product; unknown products refused")

    # Capacity 1, and one item already waiting: neither producer may create work or reports.
    with db.immediate() as connection:
        held = WAKE["admit"](connection, queue, "manual:1", "lucy", PROMPT, ("local", ""))
    for now in (139.0, 150.0):
        assert WAKE["tick"](db, queue, now=now) == [] and WAKE["scan"](db, queue, now=now) == []
    assert one(db, "SELECT next_due FROM wake_jobs") == 100.0
    assert len(events(db, "wake.job.deferred")) == 1
    assert one(db, "SELECT armed FROM stock_conditions") == 1
    assert one(db, "SELECT count(*) FROM work") == 1
    assert one(db, "SELECT count(*) FROM reports") == 0
    print("ok   a full queue defers the job once and leaves the condition armed; nothing stored")
    CHANNEL["claim"](db, "boundary-worker")
    queue.finish(CHANNEL["Assignment"](held, "lucy", PROMPT, "boundary-worker"), "done")
    job = WAKE["tick"](db, queue, now=155.0)
    assert len(job) == 1 and one(db, "SELECT next_due FROM wake_jobs") == 160.0
    assert events(db, "wake.job.enqueued")[-1]["coalesced"] == 5
    assert one(db, "SELECT deferred FROM wake_jobs") == 0
    print("ok   with capacity back, one current occurrence is admitted and five coalesced")

    # Scope is enforced by the tools, not by the prompt.
    call = CHANNEL["LOOP"]["ToolCall"]
    scoped = WAKE["shop_tools"](db, "SKU-VANILLA")
    listed = scoped.invoke(call(id="a", name="list_stock", arguments={}))
    assert [row["sku"] for row in listed["value"]] == ["SKU-VANILLA"]
    for name, arguments in (
        ("draft_order", {"sku": "SKU-STRAWBERRY", "quantity": 4}),
        ("supplier", {"sku": "SKU-STRAWBERRY"}),
        ("draft_order", {"sku": "SKU-VANILLA", "quantity": 5}),
    ):
        assert scoped.invoke(call(id="b", name=name, arguments=arguments))["ok"] is False
    drafted = scoped.invoke(
        call(id="c", name="draft_order", arguments={"sku": "SKU-VANILLA", "quantity": 6})
    )
    assert drafted["value"]["total_cents"] == 1500 and drafted["value"]["status"] == "DRAFT"
    assert set(scoped.tools) == READ_AND_DRAFT
    print("ok   a vanilla subject sees and drafts vanilla only; no tool can purchase")

    # The report comes from draft observations only.
    report = WAKE["draft_report"]
    assert report([{"role": "assistant", "content": "I drafted seven tubs for $15.00."}]) is None

    def transcript(*values):
        messages = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {"id": f"d{i}", "function": {"name": "draft_order", "arguments": "{}"}}
                    for i in range(len(values))
                ],
            }
        ]
        for i, value in enumerate(values):
            content = {"ok": True, "value": value} if value else {"ok": False, "error": "x"}
            messages.append(
                {"role": "tool", "tool_call_id": f"d{i}", "content": json.dumps(content)}
            )
        return messages

    vanilla = {"sku": "SKU-VANILLA", "quantity": 7, "total_cents": 1750, "currency": "USD"}
    assert report(transcript({**vanilla, "quantity": 6, "total_cents": 1500}, vanilla, None)) == (
        'Draft estimates:\n- "SKU-VANILLA": 7 tubs, $17.50 USD.\nTotal: $17.50 USD.'
    )
    for broken in ({"currency": "EUR"}, {"total_cents": -1}, {"quantity": 0}, {"sku": ""}):
        assert refused(ValueError, lambda b=broken: report(transcript({**vanilla, **b})))
    assert report(transcript({**vanilla, "sku": "X\n- fake"})).count("\n") == 2  # one line each
    print("ok   reports use the latest valid draft per product; narration and bad amounts refused")
    db.close()


def main():
    queueing_arithmetic()
    claude_receipt()
    parser = argparse.ArgumentParser(description=__doc__)
    model = parser.add_mutually_exclusive_group()
    model.add_argument("--live", action="store_true", help="use the local HTTP model")
    model.add_argument("--claude", metavar="MODEL", help="use Claude, e.g. on Colab")
    parser.add_argument("--model", default="qwen3")
    parser.add_argument("--transcript", action="store_true")
    args = parser.parse_args()
    live = args.live or args.claude
    if args.claude:
        claude = runpy.run_path(
            str(BOOK / "experiments/profrod_sovereign_agent_claude_messages_v1.py")
        )
        client = claude["Claude"](max_usd=1.0)
        LOOP = CHANNEL["LOOP"]

        def model_factory():
            return claude["LoopModel"](client, args.claude, LOOP["ModelTurn"], LOOP["ToolCall"])

    elif args.live:

        def model_factory():
            return CHANNEL["LOOP"]["HTTPModel"](model=args.model, reasoning_effort="none")

    else:
        model_factory = CHANNEL["SKILLS"]["OfflineShopModel"]
    with tempfile.TemporaryDirectory(prefix="lucy-wake-") as temporary:
        root = Path(temporary)
        boundaries(root)
        db, queue = prepare(root / "agent.sqlite")
        first_due = time.time() - 39
        observed = first_due + 39
        WAKE["schedule"](db, "morning", "lucy", PROMPT, first_due=first_due, interval_seconds=10)
        WAKE["set_paused"](db, True)
        assert WAKE["tick"](db, queue, now=observed) == []
        assert one(db, "SELECT next_due FROM wake_jobs") == first_due
        print("Pause preserved due job:", True)
        WAKE["set_paused"](db, False)
        created = WAKE["tick"](db, queue, now=observed)
        assert len(created) == 1 and WAKE["tick"](db, queue, now=observed) == []
        assert one(db, "SELECT next_due FROM wake_jobs") == first_due + 40
        print("Coalesced missed runs:", events(db, "wake.job.enqueued")[0]["coalesced"])
        assert events(db, "wake.job.enqueued")[0]["coalesced"] == 3
        whole_shop = WAKE["run_next"](db, queue, model_factory())
        assert whole_shop["status"] == "COMPLETED" and whole_shop["subject"] is None
        assert observed_drafts(whole_shop["messages"]) == [
            ("SKU-STRAWBERRY", 4, 1100),
            ("SKU-VANILLA", 6, 1500),
        ]
        assert whole_shop["answer"] == (
            'Draft estimates:\n- "SKU-STRAWBERRY": 4 tubs, $11.00 USD.\n'
            '- "SKU-VANILLA": 6 tubs, $15.00 USD.\nTotal: $26.00 USD.'
        )
        print("Morning draft evidence:", "PASS")
        WAKE["unschedule"](db, "morning")
        assert WAKE["tick"](db, queue, now=observed + 100) == []
        WAKE["watch"](db, "vanilla-low", "lucy", "SKU-VANILLA")
        WAKE["set_paused"](db, True)
        assert WAKE["scan"](db, queue) == [] and one(db, "SELECT armed FROM stock_conditions") == 1
        WAKE["set_paused"](db, False)
        first = WAKE["scan"](db, queue)
        assert len(first) == 1 and WAKE["scan"](db, queue) == []
        scoped = WAKE["run_next"](db, queue, model_factory())
        assert scoped["status"] == "COMPLETED" and scoped["subject"] == "SKU-VANILLA"
        assert observed_drafts(scoped["messages"]) == [("SKU-VANILLA", 6, 1500)]
        print("First stock episode:", "PASS")
        WAKE["adjust_stock"](db, "delivery-1", "SKU-VANILLA", 6, "received")
        assert WAKE["scan"](db, queue) == []
        WAKE["adjust_stock"](db, "sales-1", "SKU-VANILLA", -7, "sold")
        assert one(db, "SELECT armed FROM stock_conditions") == 1
        # Two more things for the unattended worker to find: a job due now, and a turn that a
        # killed worker left running, which holds Lucy's session until it is released.
        WAKE["schedule"](
            db, "evening", "lucy", PROMPT, first_due=time.time(), interval_seconds=86_400
        )
        with db.immediate() as connection:
            WAKE["admit"](connection, queue, "manual:crashed", "lucy", PROMPT, ("local", ""))
        assert CHANNEL["claim"](db, "wake-worker") is not None
        db.close()
        environment = {
            key: value
            for key, value in os.environ.items()
            if key in {"PATH", "SYSTEMROOT", "TMPDIR", "LANG", "LC_ALL", "PYTHONPATH"}
        }
        command = [sys.executable, str(WAKEUPS), "serve", "--root", str(root), "--interval", "0.05"]
        if args.claude:
            command += ["--claude", args.claude]
            environment.update(
                {
                    k: v
                    for k, v in os.environ.items()
                    if k in {"ANTHROPIC_API_KEY", "ANTHROPIC_ENV_FILE"}
                }
            )
        elif args.live:
            command += ["--live", "--model", args.model]
        # No prompt argument, no bot credential and no supplier: the child must discover the
        # stored condition itself, and its tools can only read and draft.
        process = subprocess.Popen(
            command,
            cwd=BOOK.parents[1],
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        db, queue = WAKE["open_shop"](root / "agent.sqlite")
        try:
            deadline = time.monotonic() + (120 if live else 15)
            row = None
            while time.monotonic() < deadline and process.poll() is None:
                row = db.connection.execute(
                    "SELECT w.work_id, w.state, r.body FROM work w"
                    " LEFT JOIN reports r ON r.work_id = w.work_id"
                    " WHERE w.source_id = 'stock-condition:vanilla-low:2'"
                ).fetchone()
                if row and row["state"] == "finished":
                    break
                time.sleep(0.02)
            if row is None or row["state"] != "finished":
                process.terminate()
                raise AssertionError(
                    (dict(row) if row else "no condition work", process.communicate()[1][-2000:])
                )
            messages = json.loads(
                one(db, "SELECT messages FROM work_transcripts WHERE work_id=?", row["work_id"])
            )
            assert observed_drafts(messages) == [("SKU-VANILLA", 7, 1750)]
            assert row["body"] == (
                'Draft estimates:\n- "SKU-VANILLA": 7 tubs, $17.50 USD.\nTotal: $17.50 USD.'
            )
            print("Unattended second episode:", "PASS")
            assert one(
                db,
                "SELECT r.body FROM reports r JOIN work w ON w.work_id = r.work_id"
                " WHERE w.source_id = 'manual:crashed'",
            ) == ("The agent stopped before answering this request. Please send it again.")
            print("Interrupted turn reported:", True)
            evening = db.connection.execute(
                "SELECT r.body FROM reports r JOIN work w ON w.work_id = r.work_id"
                " WHERE w.source_id LIKE 'job:evening:%'"
            ).fetchall()
            assert [row[0] for row in evening] == [
                'Draft estimates:\n- "SKU-STRAWBERRY": 4 tubs, $11.00 USD.\n'
                '- "SKU-VANILLA": 7 tubs, $17.50 USD.\nTotal: $28.50 USD.'
            ]
            print("Unattended scheduled brief:", "PASS")
            print("Persisted draft amount:", "$17.50 USD")
            assert one(db, "SELECT generation FROM stock_conditions") == 2
            assert WAKE["scan"](db, queue) == []
            print("Duplicate episode work:", 0)
            transcripts = [
                json.loads(value)
                for (value,) in db.connection.execute("SELECT messages FROM work_transcripts")
            ]
            assert len(transcripts) == 4
            purchases = sum(
                name not in READ_AND_DRAFT for item in transcripts for name in called_tools(item)
            )
            print("Purchases:", purchases)
            assert purchases == 0
            if args.transcript:
                print(
                    json.dumps(
                        {
                            "morning": whole_shop["messages"],
                            "first_episode": scoped["messages"],
                            "unattended_episode": messages,
                            "displayed_reports": {
                                "morning": whole_shop["answer"],
                                "first_episode": scoped["answer"],
                                "unattended_episode": row["body"],
                            },
                        },
                        indent=2,
                    )
                )
        finally:
            if process.poll() is None:
                process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate(timeout=5)
            db.close()
        assert process.returncode == 0, (process.returncode, stderr)
        assert "STOPPED" in stdout
        print("Worker stopped cleanly:", True)
        if args.claude:
            (child,) = [line[7:] for line in stdout.splitlines() if line.startswith("CLAUDE ")]
            print(json.dumps({"parent": client.report(), "child": json.loads(child)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
