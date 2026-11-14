"""Exercise the poller with synthetic transport messages, without a network."""

import asyncio
import hashlib
import json
import sys
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from channel_journal import BindingConflict, ChannelJournal
from channel_runtime import (
    HeldOutcome, IncomingMessage, IncomingPage, PollCursor, PollingRuntime,
    SendResult, current_binding, OutboundObservation, confirmed_send_sid, InboundObservationRefusal,
)


class FakeBroker:
    def __init__(self):
        self.pages = []
        self.polls = []
        self.sends = []
        self.send_result = SendResult("confirmed", "a" * 64)

    async def inbound_list(self, *, after, limit):
        self.polls.append((after, limit))
        return self.pages.pop(0)

    async def send_text(self, **kwargs):
        self.sends.append(kwargs)
        if isinstance(self.send_result, BaseException):
            raise self.send_result
        return self.send_result


class RuntimeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.journal = ChannelJournal(Path(self.tmp.name) / "channel.sqlite3")
        self.broker = FakeBroker()
        self.now = datetime(2026, 11, 14, 12, tzinfo=timezone.utc)
        self.message = IncomingMessage(
            "synthetic-connection", "whatsapp:+15550000001", "whatsapp:+15550000002",
            "SM_synthetic_1", "execution-1", "show the shelf", self.now - timedelta(seconds=10),
        )
        self.runtime = self.new_runtime()

    def new_runtime(self):
        return PollingRuntime(
            self.broker, self.journal, scope="synthetic-demo",
            connection_id=self.message.connection_id,
            sandbox_recipient=self.message.recipient,
            allowed_senders=frozenset([self.message.sender]),
            not_before=self.now - timedelta(minutes=10), clock=lambda: self.now,
        )

    def page(self, *messages):
        self.broker.pages.append(IncomingPage(
            tuple(messages),
            PollCursor(messages[-1].sent_at, messages[-1].message_sid) if messages else self.runtime.after,
            True,
        ))

    def tearDown(self):
        self.journal.close()
        self.tmp.cleanup()

    async def test_restart_deduplicates_even_when_retrieval_execution_changes(self):
        delivered = []
        async def deliver(message):
            delivered.append(message.message_sid)
            await self.runtime.reply("Synthetic shelf")
        self.page(self.message)
        save_cursor = self.journal.save_cursor
        def unavailable_cursor(*_args):
            raise OSError("Synthetic stop after journal completion")
        self.journal.save_cursor = unavailable_cursor
        with self.assertRaises(OSError):
            await self.runtime.poll_once(deliver)
        self.journal.save_cursor = save_cursor
        self.runtime = self.new_runtime()
        self.page(replace(self.message, execution_id="execution-2"))
        self.assertEqual(await self.runtime.poll_once(deliver), ["DONE"])
        self.assertEqual(delivered, [self.message.message_sid])
        self.assertEqual(len(self.broker.sends), 1)
        self.assertEqual(self.broker.sends[0]["recipient"], self.message.sender)

    async def test_cursor_is_passed_back_and_empty_page_preserves_it(self):
        async def deliver(_message):
            pass
        self.page(self.message)
        await self.runtime.poll_once(deliver)
        cursor = self.runtime.after
        self.page()
        self.assertEqual(await self.runtime.poll_once(deliver), [])
        self.assertEqual(self.runtime.after, cursor)
        self.assertEqual(self.broker.polls, [(None, 50), (cursor, 50)])

    async def test_restart_tolerates_inclusive_boundary_without_repeated_delivery(self):
        delivered = []
        async def deliver(message):
            delivered.append(message.message_sid)
        self.page(self.message)
        await self.runtime.poll_once(deliver)
        self.runtime = self.new_runtime()
        boundary = replace(self.message, execution_id="new-retrieval")
        self.page(boundary)
        self.assertEqual(await self.runtime.poll_once(deliver), ["DONE"])
        fresh = replace(self.message, message_sid="SM_fresh", sent_at=self.now - timedelta(seconds=1))
        self.page(boundary, fresh)
        self.assertEqual(await self.runtime.poll_once(deliver), ["DONE", "DONE"])
        self.assertEqual(delivered, [self.message.message_sid, fresh.message_sid])
        self.assertEqual(self.runtime.after.sid, fresh.message_sid)

    async def test_foreign_message_is_skipped_before_valid_turn_and_cursor_advances(self):
        delivered = []
        async def deliver(message):
            delivered.append(message)
        foreign = replace(self.message, sender="whatsapp:+15550000003", message_sid="SM_foreign",
                          sent_at=self.message.sent_at - timedelta(seconds=1))
        self.page(foreign, self.message)
        self.assertEqual(await self.runtime.poll_once(deliver), ["SKIPPED", "DONE"])
        self.assertEqual(delivered, [self.message])
        self.assertEqual(self.runtime.after.sid, self.message.message_sid)
        stored = self.journal.db.execute("SELECT result_ref FROM attempts WHERE operation=?",
                                         ("inbound:SM_foreign",)).fetchone()[0]
        self.assertEqual(stored, "SKIPPED:unlisted_sender")

    async def test_wrong_grant_old_messages_and_media_skip_but_bad_cursor_refuses(self):
        delivered = []
        async def deliver(_message):
            delivered.append(_message)
        cases = [
            replace(self.message, message_sid="SM_old", sent_at=self.now - timedelta(hours=1)),
            replace(self.message, message_sid="SM_grant", connection_id="another-grant", sent_at=self.now - timedelta(seconds=9)),
            replace(self.message, message_sid="SM_recipient", recipient="whatsapp:+15550000003", sent_at=self.now - timedelta(seconds=8)),
            replace(self.message, message_sid="SM_media", num_media=1, sent_at=self.now - timedelta(seconds=7)),
            replace(self.message, sent_at=self.now - timedelta(seconds=1)),
        ]
        self.page(*cases)
        self.assertEqual(await self.runtime.poll_once(deliver), ["SKIPPED"] * 4 + ["DONE"])
        self.assertEqual(delivered, [cases[-1]])
        self.broker.pages.append(IncomingPage((replace(self.message, sent_at=self.now),), None, True))
        with self.assertRaises(ValueError):
            await self.runtime.poll_once(deliver)

    async def test_broken_transport_shape_refuses_entire_page_before_delivery(self):
        async def deliver(_message):
            self.fail("A malformed transport page reached the agent")
        self.page(self.message, replace(self.message, text=123))
        with self.assertRaises(ValueError):
            await self.runtime.poll_once(deliver)
        self.assertIsNone(self.runtime.after)

    async def test_same_second_late_smaller_sid_is_delivered_once_after_restart(self):
        delivered = []
        async def deliver(message):
            delivered.append(message.message_sid)
        seen = replace(self.message, message_sid="SM_9")
        self.page(seen)
        await self.runtime.poll_once(deliver)
        self.runtime = self.new_runtime()
        late = replace(seen, message_sid="SM_2", execution_id="later-retrieval")
        fresh = replace(seen, message_sid="SM_3", sent_at=seen.sent_at + timedelta(seconds=1))
        self.page(late, seen, fresh)
        self.assertEqual(await self.runtime.poll_once(deliver), ["DONE", "DONE", "DONE"])
        self.assertEqual(delivered, ["SM_9", "SM_2", "SM_3"])
        self.assertEqual(self.runtime.after.sid, "SM_3")
        self.runtime = self.new_runtime()
        self.page(fresh)
        await self.runtime.poll_once(deliver)
        self.assertEqual(delivered, ["SM_9", "SM_2", "SM_3"])
        self.page(seen)
        with self.assertRaises(ValueError):
            await self.runtime.poll_once(deliver)

    async def test_partial_last_second_is_deferred_and_replayed_whole_after_restart(self):
        delivered = []
        async def deliver(message):
            delivered.append(message.message_sid)
        self.page(self.message)
        await self.runtime.poll_once(deliver)
        partial = replace(self.message, message_sid="SM_partial_2", sent_at=self.message.sent_at + timedelta(seconds=1))
        self.broker.pages.append(IncomingPage((self.message, partial),
                                              PollCursor(partial.sent_at, partial.message_sid), False))
        self.assertEqual(await self.runtime.poll_once(deliver), ["DONE"])
        self.assertEqual(delivered, [self.message.message_sid])
        self.assertEqual(self.runtime.after.date_sent, partial.sent_at)
        self.runtime = self.new_runtime()
        earlier_sid = replace(partial, message_sid="SM_partial_1")
        self.page(earlier_sid, partial)
        self.assertEqual(await self.runtime.poll_once(deliver), ["DONE", "DONE"])
        self.assertEqual(delivered, [self.message.message_sid, "SM_partial_1", "SM_partial_2"])

    async def test_single_second_overflow_stops_without_partial_delivery_or_cursor_change(self):
        async def deliver(_message):
            self.fail("An incomplete second reached the agent")
        messages = tuple(replace(self.message, message_sid=f"SM_{number:02}") for number in range(50))
        self.broker.pages.append(IncomingPage(messages, PollCursor(messages[-1].sent_at, messages[-1].message_sid), False))
        with self.assertRaises(HeldOutcome):
            await self.runtime.poll_once(deliver)
        self.assertIsNone(self.runtime.after)
        self.assertEqual(self.journal.db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0], 0)

    async def test_truncated_provider_window_refuses_then_restarts_at_same_cursor(self):
        delivered = []
        async def deliver(message):
            delivered.append(message.message_sid)
        seen = replace(self.message, message_sid="SM_9")
        self.page(seen)
        await self.runtime.poll_once(deliver)
        saved = self.runtime.after
        count = self.journal.db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
        self.broker.pages.append(InboundObservationRefusal(
            "failed_safe", "REQUEST_REFUSED", "inbound_window_truncated"))
        with self.assertRaises(HeldOutcome):
            await self.runtime.poll_once(deliver)
        self.assertEqual(self.runtime.after, saved)
        self.assertEqual(self.broker.polls[-1][0], saved)
        self.assertEqual(delivered, ["SM_9"])
        self.assertEqual(self.broker.sends, [])
        self.assertEqual(self.journal.db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0], count)
        self.runtime = self.new_runtime()
        late = replace(seen, message_sid="SM_2")
        self.page(late, seen)
        await self.runtime.poll_once(deliver)
        self.assertEqual(self.broker.polls[-1][0], saved)
        self.assertEqual(delivered, ["SM_9", "SM_2"])
        self.assertEqual(self.runtime.after, saved)

    async def test_persisted_cursor_and_old_history_survive_restart_and_long_gap(self):
        delivered = []
        async def deliver(message):
            delivered.append(message.message_sid)
        self.page(self.message)
        await self.runtime.poll_once(deliver)
        saved = self.runtime.after
        self.now += timedelta(days=2)
        self.runtime = self.new_runtime()
        self.assertEqual(self.runtime.after, saved)
        old = replace(self.message, message_sid="SM_weekend", sent_at=self.message.sent_at + timedelta(seconds=1))
        fresh = replace(self.message, message_sid="SM_monday", sent_at=self.now - timedelta(seconds=1))
        self.page(old, fresh)
        self.assertEqual(await self.runtime.poll_once(deliver), ["SKIPPED", "DONE"])
        self.assertEqual(self.broker.polls[-1][0], saved)
        self.assertEqual(delivered, [self.message.message_sid, fresh.message_sid])
        self.runtime = self.new_runtime()
        self.assertEqual(self.runtime.after.sid, fresh.message_sid)

    async def test_unknown_send_holds_turn_and_does_not_resend_after_restart(self):
        self.broker.send_result = SendResult("ambiguous", "b" * 64)
        async def deliver(_message):
            await self.runtime.reply("Synthetic review")
        self.page(self.message)
        with self.assertRaises(HeldOutcome):
            await self.runtime.poll_once(deliver)
        self.assertIsNone(self.runtime.after)
        self.runtime = self.new_runtime()
        self.page(self.message)
        self.assertEqual(await self.runtime.poll_once(deliver), ["HELD"])
        self.assertEqual(len(self.broker.sends), 1)
        self.assertEqual(len(self.journal.held("synthetic-demo")), 2)

    async def test_provider_sid_cannot_be_accepted_as_confirmation_digest(self):
        self.broker.send_result = SendResult("confirmed", "SM_not_a_digest")
        async def deliver(_message):
            await self.runtime.reply("Synthetic review")
        self.page(self.message)
        with self.assertRaises(HeldOutcome):
            await self.runtime.poll_once(deliver)

    async def test_reply_outside_turn_and_inherited_context_after_close_are_refused(self):
        with self.assertRaises(PermissionError):
            await self.runtime.reply("No turn")
        release = asyncio.Event()
        tasks = []
        async def late_reply():
            await release.wait()
            with self.assertRaises(PermissionError):
                await self.runtime.reply("Too late")
        async def deliver(_message):
            tasks.append(asyncio.create_task(late_reply()))
        self.page(self.message)
        await self.runtime.poll_once(deliver)
        release.set()
        await asyncio.gather(*tasks)
        self.assertEqual(self.broker.sends, [])

    async def test_cancellation_preserves_claim_and_closes_context(self):
        entered = asyncio.Event()
        bindings = []
        async def deliver(_message):
            bindings.append(current_binding(self.now))
            entered.set()
            await asyncio.Event().wait()
        self.page(self.message)
        task = asyncio.create_task(self.runtime.poll_once(deliver))
        await entered.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertFalse(bindings[0].active)
        self.assertEqual(len(self.journal.held("synthetic-demo")), 1)

    async def test_changed_payload_under_same_sid_is_refused_after_restart(self):
        async def deliver(_message):
            pass
        self.page(self.message)
        await self.runtime.poll_once(deliver)
        self.runtime = self.new_runtime()
        self.page(replace(self.message, text="different order", sent_at=self.message.sent_at + timedelta(seconds=1)))
        with self.assertRaises(BindingConflict):
            await self.runtime.poll_once(deliver)

    def test_confirmed_sid_digest_survives_status_change_and_equal_body_candidates(self):
        sid = "SM_original"
        digest = hashlib.sha256(json.dumps({"message_sid": sid}, separators=(",", ":")).encode()).hexdigest()
        candidates = [OutboundObservation(self.message.sender, "SM_other", "sent"),
                      OutboundObservation(self.message.sender, sid, "delivered")]
        self.assertEqual(confirmed_send_sid(SendResult("confirmed", digest), candidates,
                                            recipient=self.message.sender), sid)

    def test_unknown_or_missing_candidate_cannot_authorize_original_send(self):
        candidates = [OutboundObservation(self.message.sender, "SM_only_candidate", "sent")]
        for result in [SendResult("ambiguous"), SendResult("confirmed", "a" * 64)]:
            with self.assertRaises(HeldOutcome):
                confirmed_send_sid(result, candidates, recipient=self.message.sender)


if __name__ == "__main__":
    unittest.main()
