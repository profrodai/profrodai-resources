"""Offline replay checks; these do not validate a live messaging service."""

import concurrent.futures
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from channel_journal import BindingConflict, ChannelJournal, StaleAttempt


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "journal.sqlite3"
        self.binding = {"sender": "synthetic-customer-a", "message_sid": "synthetic-1", "text": "yes"}
        self.journal = ChannelJournal(self.path)

    def tearDown(self):
        self.journal.close()
        self.tmp.cleanup()

    def test_completed_poll_replay_returns_reference_without_dispatch(self):
        sent = []
        for _ in range(3):
            attempt = self.journal.claim("sandbox-a", "inbound-1", binding=self.binding)
            if attempt.state == "START":
                sent.append("turn")
                self.journal.complete("sandbox-a", "inbound-1", attempt.ticket, "turn-result-1")
        self.assertEqual(sent, ["turn"])
        self.assertEqual(attempt.state, "DONE")
        self.assertEqual(attempt.result_ref, "turn-result-1")

    def test_restart_holds_inflight_instead_of_repeating_side_effect(self):
        self.journal.claim("sandbox-a", "reply-1", binding=self.binding)
        self.journal.close()
        self.journal = ChannelJournal(self.path)
        self.assertEqual(self.journal.claim("sandbox-a", "reply-1", binding=self.binding).state, "HELD")
        pending = self.journal.held("sandbox-a")
        self.assertEqual(len(pending), 1)
        self.journal.complete("sandbox-a", pending[0].operation, pending[0].ticket, "looked-up-original")
        self.assertEqual(self.journal.held("sandbox-a"), [])

    def test_pending_lookup_is_scoped_and_bounded(self):
        for number in range(3):
            self.journal.claim("sandbox-a", f"reply-{number}", binding=self.binding)
        self.assertEqual(len(self.journal.held("sandbox-a", limit=2)), 2)
        self.assertEqual(self.journal.held("sandbox-b"), [])
        with self.assertRaises(ValueError):
            self.journal.held("sandbox-a", limit=101)

    def test_unknown_send_is_not_retried_and_lookup_can_finish_original(self):
        attempt = self.journal.claim("sandbox-a", "reply-1", binding=self.binding)
        self.journal.uncertain("sandbox-a", "reply-1", attempt.ticket)
        self.assertEqual(self.journal.claim("sandbox-a", "reply-1", binding=self.binding).state, "HELD")
        self.journal.complete("sandbox-a", "reply-1", attempt.ticket, "original-provider-message")
        result = self.journal.claim("sandbox-a", "reply-1", binding=self.binding)
        self.assertEqual((result.state, result.result_ref), ("DONE", "original-provider-message"))

    def test_changed_sender_or_payload_cannot_reuse_operation(self):
        self.journal.claim("sandbox-a", "inbound-1", binding=self.binding)
        for key, value in (("sender", "synthetic-customer-b"), ("text", "different order")):
            with self.assertRaises(BindingConflict):
                self.journal.claim("sandbox-a", "inbound-1", binding={**self.binding, key: value})
        # A rejected replay must leave the transaction usable.
        self.assertEqual(self.journal.claim("sandbox-a", "inbound-1", binding=self.binding).state, "HELD")

    def test_scope_separates_two_granted_sandbox_accounts(self):
        self.journal.claim("sandbox-a", "inbound-1", binding=self.binding)
        self.assertEqual(self.journal.claim("sandbox-b", "inbound-1", binding=self.binding).state, "START")

    def test_wrong_ticket_and_terminal_rewrite_are_refused(self):
        attempt = self.journal.claim("sandbox-a", "inbound-1", binding=self.binding)
        with self.assertRaises(StaleAttempt):
            self.journal.complete("sandbox-a", "inbound-1", "wrong", "forged")
        self.journal.complete("sandbox-a", "inbound-1", attempt.ticket, "original")
        with self.assertRaises(StaleAttempt):
            self.journal.complete("sandbox-a", "inbound-1", attempt.ticket, "replacement")

    def test_simultaneous_pollers_only_admit_one_attempt(self):
        def claim(_):
            journal = ChannelJournal(self.path)
            try:
                return journal.claim("sandbox-a", "inbound-1", binding=self.binding).state
            finally:
                journal.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            states = list(pool.map(claim, range(12)))
        self.assertEqual(states.count("START"), 1)
        self.assertEqual(states.count("HELD"), 11)

    def test_stored_binding_does_not_contain_message_text_or_sender(self):
        self.journal.claim("sandbox-a", "inbound-1", binding=self.binding)
        stored = self.journal.db.execute("SELECT binding FROM attempts").fetchone()[0]
        self.assertNotIn(self.binding["sender"], stored)
        self.assertNotIn(self.binding["text"], stored)
        self.assertEqual(len(stored), 64)
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
