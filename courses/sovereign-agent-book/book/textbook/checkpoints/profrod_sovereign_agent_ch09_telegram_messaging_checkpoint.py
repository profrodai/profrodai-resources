# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 9: durable private messages, session routing and explicit delivery uncertainty.

Every function it calls is the learner's own: Chapter 9's channel on Chapter 8's queue, Chapter 7's
skills and context, Chapter 5's memory, Chapter 4's store, and Chapter 3's loop and transport.
"""

import argparse
import json
import math
import os
import runpy
import tempfile
from pathlib import Path

BOOK = Path(__file__).resolve().parents[1]
CHANNEL = runpy.run_path(str(BOOK / "learner/profrod_sovereign_agent_ch09_messaging_learner.py"))
open_channel, poll, claim = CHANNEL["open_channel"], CHANNEL["poll"], CHANNEL["claim"]
run_claim, deliver_one = CHANNEL["run_claim"], CHANNEL["deliver_one"]
MEMORY, SKILLS, LOOP = CHANNEL["MEMORY"], CHANNEL["SKILLS"], CHANNEL["LOOP"]
PROMPT = "Prepare replenishment drafts from current stock. State USD amounts."
LATENCY = runpy.run_path(str(BOOK / "learner/profrod_sovereign_agent_ch09_latency_learner.py"))


def latency_arithmetic():
    """Part A's formulas by independent checks, and the receipt's fits recomputed from its rows."""
    assert LATENCY["fit_line"]([1, 2, 3], [3, 5, 7]) == (1.0, 2.0)
    assert LATENCY["conversation_prefill"](8, 100, cached=False) == 3600
    assert LATENCY["conversation_prefill"](8, 100, cached=True) == 800
    first = LATENCY["first_token_seconds"](1000, 1e-4, 1e-8, 5e-3)
    assert math.isclose(first, 0.1 + 0.01 + 0.005)
    whole = LATENCY["reply_seconds"](1000, 101, 1e-4, 1e-8, 5e-3)
    assert math.isclose(whole - first, 100 * 5e-3)
    print("ok   prefill b n + c n^2, reply time, and quadratic against linear conversation cost")
    receipt = json.loads(
        (BOOK.parents[1] / "docs/evidence/book-ch09/ch09-latency-receipt-v1.json").read_text()
    )
    for model in receipt["models"].values():
        rows = model["prefill"]["rows"]
        b, c = LATENCY["fit_line"](
            [r["prompt_tokens"] for r in rows],
            [r["prefill_seconds"] / r["prompt_tokens"] for r in rows],
        )
        assert round(b, 9) == model["prefill"]["seconds_per_token"]
        assert round(c, 12) == model["prefill"]["seconds_per_token_squared"]
        assert c > 0  # the per-token prefill cost rises with the prompt's length
    cached, uncached = receipt["conversation"]["cached"], receipt["conversation"]["uncached"]
    assert all(
        a["prefill_seconds"] < b["prefill_seconds"] for a, b in zip(cached, uncached, strict=True)
    )
    print("ok   prefill fits recompute; cached turns always prefilled faster than uncached ones")


def update(identifier, actor=123, text=PROMPT):
    return {
        "update_id": identifier,
        "message": {
            "from": {"id": actor, "is_bot": False},
            "chat": {"id": actor, "type": "private"},
            "text": text,
        },
    }


class OfflineBot:
    account = "teaching"

    def __init__(self, updates):
        self.updates = updates
        self.offsets = []
        self.sent = []
        self.lose_next_reply = False

    def call(self, method, data):
        if method == "getUpdates":
            self.offsets.append(data["offset"])
            # Replaying even acknowledged data deliberately challenges local deduplication.
            return self.updates
        self.sent.append(data)
        if self.lose_next_reply:
            self.lose_next_reply = False
            raise TimeoutError("accepted remotely but reply lost")
        return {"message_id": 900 + len(self.sent)}


def refused(error, action):
    try:
        action()
    except error:
        return True
    return False


def one(db, sql, *values):
    return db.connection.execute(sql, values).fetchone()[0]


def boundaries(root):
    """The intake refuses what it cannot vouch for, and rolls back the whole batch when it must."""
    db, queue = open_channel(root / "boundaries.sqlite", capacity=2)
    operators = frozenset({123})
    assert refused(ValueError, lambda: CHANNEL["Telegram"]("not-a-bot-credential"))
    bot = CHANNEL["Telegram"]("123:fake-teaching-credential")
    assert bot.account == "123"
    assert refused(ValueError, lambda: bot.call("deleteWebhook", {}))
    assert refused(ValueError, lambda: poll(db, queue, OfflineBot([]), frozenset()))
    assert refused(ValueError, lambda: poll(db, queue, OfflineBot([]), frozenset({0})))
    ignored = [
        {
            "update_id": 1,
            "message": {"from": {"id": 123}, "chat": {"id": 7, "type": "private"}, "text": PROMPT},
        },
        {
            "update_id": 2,
            "message": {"from": {"id": 123}, "chat": {"id": 123, "type": "group"}, "text": PROMPT},
        },
        {
            "update_id": 3,
            "message": {
                "from": {"id": 123, "is_bot": True},
                "chat": {"id": 123, "type": "private"},
                "text": PROMPT,
            },
        },
        {"update_id": 4, "message": {"from": {"id": 123}, "chat": {"id": 123, "type": "private"}}},
        update(5, actor=999),
        update(6, text="   "),
    ]
    assert poll(db, queue, OfflineBot(ignored), operators) == []
    assert one(db, "SELECT offset FROM channel_cursor") == 7
    bad = OfflineBot([update(8), {"update_id": 9, "message": None}])
    assert refused(ValueError, lambda: poll(db, queue, bad, operators))
    for batch in ([update(8), "not an update"], [update(8), {"update_id": -1}], {"a": 1}):
        assert refused(ValueError, lambda b=batch: poll(db, queue, OfflineBot(b), operators))
    assert (
        one(db, "SELECT count(*) FROM work") == 0
        and one(db, "SELECT offset FROM channel_cursor") == 7
    )
    assert one(db, "SELECT count(*) FROM channel_leases") == 0
    first = poll(db, queue, OfflineBot([update(8)]), operators)
    changed = OfflineBot([update(8, text="Buy everything now.")])
    assert refused(ValueError, lambda: poll(db, queue, changed, operators))
    assert one(db, "SELECT text FROM work WHERE work_id = ?", first[0]) == PROMPT
    with db.immediate() as connection:
        connection.execute("INSERT INTO channel_leases VALUES ('telegram:teaching', 'other', 9e18)")
    assert refused(PermissionError, lambda: poll(db, queue, OfflineBot([]), operators))
    with db.immediate() as connection:
        connection.execute("DELETE FROM channel_leases")
    full = poll(db, queue, OfflineBot([update(10), update(11)]), operators)
    assert one(db, "SELECT state FROM work WHERE work_id = ?", full[-1]) == "finished"
    assert "queue is full" in one(db, "SELECT body FROM reports WHERE work_id = ?", full[-1])
    print("Refused: forged chats, groups, bots, empty text, unknown senders and malformed batches")
    print("Changed replay refused; a full queue answers the sender instead of dropping the request")
    db.close()


def offline():
    with tempfile.TemporaryDirectory(prefix="lucy-channel-") as temporary:
        root = Path(temporary)
        boundaries(root)
        db, queue = open_channel(root / "agent.sqlite")
        CHANNEL["activate_opening_skill"](db)
        bot = OfflineBot([update(103, actor=999), update(101), update(102)])
        operators = frozenset({123})
        ids = poll(db, queue, bot, operators)
        assert len(ids) == 2
        print("Accepted private requests:", len(ids))
        session = "telegram:teaching:123"
        MEMORY["remember"](db, session, "format", "three bullets", "lucy/explicit-message")
        db.close()
        db, queue = open_channel(root / "agent.sqlite")
        replayed = poll(db, queue, bot, operators)
        assert replayed == []
        print("Duplicate intake after restart:", len(replayed))
        assert bot.offsets == [0, 104]
        first = claim(db, "phone-worker", work_id=ids[0])
        assert first is not None and first.session_id == session
        second_db, _ = open_channel(root / "agent.sqlite")
        competing = claim(second_db, "second-worker", work_id=ids[1])
        assert competing is None
        print("Conflicting session claim:", competing)
        second_db.close()
        passed, result = run_claim(db, queue, first, SKILLS["OfflineShopModel"]())
        assert passed and "three bullets" in result.messages[0]["content"]
        assert '"opening_check"' in result.messages[0]["content"]
        second = claim(db, "phone-worker", work_id=ids[1])
        assert second is not None
        passed, result = run_claim(db, queue, second, SKILLS["OfflineShopModel"]())
        assert passed and PROMPT in result.messages[0]["content"]
        print("Completed drafts:", 2)
        bot.lose_next_reply = True
        print("First delivery:", deliver_one(db, bot, operators))
        print("Second delivery:", deliver_one(db, bot, operators))
        db.close()
        db, queue = open_channel(root / "agent.sqlite")
        print("Automatic resend:", deliver_one(db, bot, operators))
        assert len(bot.sent) == 2
        assert [message["chat_id"] for message in bot.sent] == [123, 123]
        states = [
            row[0] for row in db.connection.execute("SELECT delivery FROM reports ORDER BY work_id")
        ]
        assert states == ["unknown", "confirmed"]
        receipts = one(db, "SELECT count(*) FROM reports WHERE receipt IS NOT NULL")
        print("Recorded send receipts:", receipts)
        assert json.loads(one(db, "SELECT receipt FROM reports WHERE delivery='confirmed'")) == {
            "message_id": 902
        }
        late = poll(db, queue, OfflineBot([update(104)]), operators)
        assert claim(db, "phone-worker", work_id=late[0]) is not None
        queue.finish(CHANNEL["Assignment"](late[0], session, PROMPT, "phone-worker"), "Done.")
        print("Delivery after the allowlist changed:", deliver_one(db, bot, frozenset({456})))
        assert len(bot.sent) == 2 and deliver_one(db, bot, operators) is None
        tools = LOOP["shop_tools"]
        purchase = tools["build_tools"](tools["SHOP"]).invoke(
            tools["ToolCall"](id="p", name="purchase", arguments={})
        )
        assert purchase == {"ok": False, "error": "tool_not_allowed"}
        print("Purchase tool: refused by the dispatcher")
        # Claiming a named item takes that item, not the oldest one waiting.
        assert poll(db, queue, OfflineBot([update(105)]), operators)
        waiting = poll(db, queue, OfflineBot([update(1, actor=7)]), frozenset({7}))
        named = claim(db, "phone-worker", work_id=waiting[0])
        assert named is not None and named.work_id == waiting[0]
        queue.finish(named, "Done.")
        # Its report is pending now, but not for another bot account to send.
        other = OfflineBot([])
        other.account = "other"
        assert deliver_one(db, other, frozenset({7})) is None

        class BadReceipt(OfflineBot):
            def call(self, method, data):
                super().call(method, data)
                return {"message_id": "902"}

        assert deliver_one(db, BadReceipt([]), frozenset({7})) == "unknown"
        db.close()
    return 0


def main():
    latency_arithmetic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--telegram",
        action="store_true",
        help="use your dedicated test bot and allowlisted private account",
    )
    parser.add_argument(
        "--root", type=Path, help="persistent dedicated test state; required for Telegram"
    )
    parser.add_argument(
        "--live", action="store_true", help="use the local HTTP model for Telegram work"
    )
    parser.add_argument("--model", default="qwen3")
    parser.add_argument("--transcript", action="store_true")
    args = parser.parse_args()
    if not args.telegram:
        if args.live:
            parser.error(
                "--live requires --telegram here; Chapter 7 supplies the model-only experiment"
            )
        return offline()
    if args.root is None:
        parser.error("--telegram requires a dedicated persistent --root")
    token = os.environ.get("SOVEREIGN_AGENT_TELEGRAM_TOKEN", "")
    actors = os.environ.get("SOVEREIGN_AGENT_OPERATORS", "").split(",")
    if not token or not all(actor.isdigit() and int(actor) > 0 for actor in actors):
        parser.error(
            "set the bot credential and positive numeric operator allowlist in your environment"
        )
    bot = CHANNEL["Telegram"](token)
    operators = frozenset(int(actor) for actor in actors)
    args.root.mkdir(parents=True, exist_ok=True)
    db, queue = open_channel(args.root / "agent.sqlite")
    CHANNEL["activate_opening_skill"](db)
    ids = poll(db, queue, bot, operators)
    print("New allowed requests:", len(ids))
    if not ids:
        print("No new allowed private text arrived during the bounded poll.")
    # Read durable work, including requests admitted by a prior process that
    # stopped before execution. The in-memory poll result is not the queue.
    queued = db.connection.execute(
        "SELECT w.work_id FROM work w JOIN channel_routes c ON c.work_id = w.work_id"
        " WHERE c.channel = ? AND w.state = 'pending' ORDER BY w.work_id LIMIT 20",
        ("telegram:" + bot.account,),
    ).fetchall()
    results = []
    for row in queued:
        identifier = row[0]
        current = claim(db, "phone-checkpoint", work_id=identifier)
        if current is None:
            continue
        model = (
            LOOP["HTTPModel"](model=args.model, reasoning_effort="none")
            if args.live
            else SKILLS["OfflineShopModel"]()
        )
        passed, result = run_claim(db, queue, current, model)
        results.append({"work": identifier, "draft_evidence": passed})
        if args.transcript:
            print(json.dumps(result.messages, indent=2))
    deliveries = []
    for _ in range(20):
        delivery = deliver_one(db, bot, operators)
        if delivery is None:
            break
        deliveries.append(delivery)
    for row in results:
        row["delivery"] = db.connection.execute(
            "SELECT delivery FROM reports WHERE work_id=? ORDER BY generation DESC", (row["work"],)
        ).fetchone()[0]
    print(
        json.dumps(
            {
                "results": results,
                "outbox_observations": deliveries,
                "scope": "bounded construction run; inspect the actual reply on your phone",
            },
            indent=2,
        )
    )
    db.close()
    return (
        0
        if (results or deliveries)
        and all(row["draft_evidence"] and row["delivery"] == "confirmed" for row in results)
        and all(value == "confirmed" for value in deliveries)
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
