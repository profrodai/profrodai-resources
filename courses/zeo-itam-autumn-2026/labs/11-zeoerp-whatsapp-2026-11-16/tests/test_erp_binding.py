"""Policy tests with a fake already-schema-validated ERP transport.

These do not qualify the producer JSON Schemas, MCP wire, or provider identity.
"""

import base64
import copy
import json
import sys
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from channel_journal import BindingConflict, ChannelJournal
from channel_runtime import HeldOutcome, IncomingMessage, IncomingPage, PollCursor, PollingRuntime
from erp_binding import ERPBinding, OriginalOperation, arguments_for, business_envelope, domain_payload

ORDER_ID = "ord_" + "1" * 24
OP_ID = "op_" + "2" * 24


class FakeERP:
    def __init__(self, order):
        self.order = order
        self.calls = []
        self.response = None

    async def call(self, tool, arguments, *, context_header):
        context = json.loads(base64.urlsafe_b64decode(context_header + "=" * (-len(context_header) % 4)))
        self.calls.append((tool, arguments, context))
        if isinstance(self.response, BaseException):
            raise self.response
        if self.response is not None:
            return copy.deepcopy(self.response)
        order = copy.deepcopy(self.order)
        if tool == "confirm_order":
            order["state"] = "confirmed"
        return {"success": True, "data": {
            "ok": True, "state": "completed", "operation_id": OP_ID, "data": order,
        }}


class FakeInbound:
    async def inbound_list(self, **_kwargs):
        return self.page


class FakeOriginalLookup:
    def __init__(self, result):
        self.result = result
        self.calls = []

    async def lookup_original(self, **kwargs):
        self.calls.append(kwargs)
        return self.result


class BindingTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.journal = ChannelJournal(Path(self.tmp.name) / "channel.sqlite3")
        self.now = datetime(2026, 11, 14, 12, tzinfo=timezone.utc)
        self.message = IncomingMessage("demo", "whatsapp:+15550000001", "whatsapp:+15550000002",
                                       "SM_synthetic_1", "execution-1", "two teas", self.now - timedelta(seconds=1))
        self.inbound = FakeInbound()
        self.runtime = PollingRuntime(
            self.inbound, self.journal, scope="demo", connection_id="demo",
            sandbox_recipient=self.message.recipient,
            allowed_senders=frozenset([self.message.sender, "whatsapp:+15550000003"]),
            not_before=self.now - timedelta(minutes=10), clock=lambda: self.now,
        )
        self.order = {
            "order_id": ORDER_ID, "version": 1, "state": "draft",
            "quote": {"expires_at": (self.now + timedelta(minutes=5)).isoformat()},
            "prompt": {"event_id": "prompt-1", "send_receipt": "opaque-original-receipt", "delivery_state": "confirmed"},
            "projection": {"state": "confirmed"},
        }
        self.erp = FakeERP(self.order)
        self.binding = ERPBinding(self.erp, self.journal, scope="demo", clock=lambda: self.now)

    def tearDown(self):
        self.journal.close()
        self.tmp.cleanup()

    async def turn(self, callback, **changes):
        self.now += timedelta(seconds=1)
        self.message = replace(self.message, message_sid="SM_" + str(self.now.timestamp()).replace(".", "_"),
                               sent_at=self.now - timedelta(microseconds=1), **changes)
        self.inbound.page = IncomingPage((self.message,), PollCursor(self.message.sent_at, self.message.message_sid), True)
        async def deliver(_message):
            await callback()
        return await self.runtime.poll_once(deliver)

    async def draft(self):
        await self.binding.call("create_draft_order", {"lines": [{"product_id": "tea", "quantity": 2}]})

    async def confirm(self):
        return await self.binding.call("confirm_order", {"order_id": ORDER_ID, "draft_version": 1})

    async def test_separate_yes_uses_bound_sid_and_no_claimed_sender_or_reply(self):
        await self.turn(self.draft)
        await self.turn(self.confirm, text=" YES ")
        tool, args, context = self.erp.calls[-1]
        self.assertEqual(tool, "confirm_order")
        self.assertEqual(context["message_sid"], self.message.message_sid)
        self.assertEqual(context["confirmation"]["prompt_send_receipt"], "opaque-original-receipt")
        self.assertNotIn("sender", context)
        self.assertNotIn("explicit_reply", context["confirmation"])
        self.assertEqual(args, {"order_id": ORDER_ID, "draft_version": 1})

    async def test_draft_and_confirm_in_one_message_cannot_dispatch_two_mutations(self):
        async def two_calls():
            await self.draft()
            await self.confirm()
        with self.assertRaises(PermissionError):
            await self.turn(two_calls, text="yes")
        self.assertEqual(len(self.erp.calls), 1)

    async def test_second_different_mutation_conflicts_even_with_different_tool(self):
        async def two_calls():
            await self.draft()
            await self.binding.call("request_human_handoff", {})
        with self.assertRaises(BindingConflict):
            await self.turn(two_calls)
        self.assertEqual(len(self.erp.calls), 1)

    async def test_model_cannot_inject_identity_or_confirmation(self):
        for extra in ["sender", "message_sid", "company", "context", "confirmation"]:
            async def call():
                await self.binding.call("create_draft_order", {"lines": [{"product_id": "tea", "quantity": 1}], extra: "forged"})
            with self.assertRaises(ValueError):
                await self.turn(call)
        self.assertEqual(self.erp.calls, [])

    async def test_nonaffirmative_foreign_customer_and_stale_version_do_not_confirm(self):
        await self.turn(self.draft)
        with self.assertRaises(PermissionError):
            await self.turn(self.confirm, text="yes, but make it three")
        with self.assertRaises(PermissionError):
            await self.turn(self.confirm, text="yes", sender="whatsapp:+15550000003")
        async def stale():
            await self.binding.call("confirm_order", {"order_id": ORDER_ID, "draft_version": 2})
        with self.assertRaises(PermissionError):
            await self.turn(stale, sender="whatsapp:+15550000002", text="yes")
        self.assertEqual(len(self.erp.calls), 1)

    async def test_expired_and_uncertain_prompt_are_not_armed(self):
        for field, value in [("delivery_state", "unknown"), ("send_receipt", None)]:
            self.erp.order["prompt"][field] = value
            await self.turn(self.draft, text="two teas")
            with self.assertRaises(PermissionError):
                await self.turn(self.confirm, text="yes")
            self.erp.order = copy.deepcopy(self.order)
        self.erp.order["quote"]["expires_at"] = (self.now - timedelta(seconds=1)).isoformat()
        await self.turn(self.draft, text="two teas")
        with self.assertRaises(PermissionError):
            await self.turn(self.confirm, text="yes")

    async def test_lost_response_holds_original_and_never_reissues_mutation(self):
        self.erp.response = TimeoutError("synthetic timeout")
        with self.assertRaises(TimeoutError):
            await self.turn(self.draft)
        self.assertEqual(len(self.erp.calls), 1)
        held = self.journal.held("demo")
        self.assertTrue(any(item.operation.startswith("erp-mutation:") for item in held))
        # Reopening the poller sees the original held SID, not a fresh attempt.
        self.runtime.after = None
        await self.runtime.poll_once(lambda _message: self.draft())
        self.assertEqual(len(self.erp.calls), 1)
        with self.assertRaises(HeldOutcome):
            await self.turn(self.draft, text="try a new order")
        self.assertEqual(len(self.erp.calls), 1)

    async def test_pending_is_not_completion_and_only_original_lookup_is_read(self):
        self.erp.response = {"success": True, "data": {
            "ok": False, "state": "pending", "operation_id": OP_ID,
            "error": {"code": "PENDING_SYNC", "message": "Pending"}, "next_action": "poll_operation_status",
        }}
        results = []
        async def draft():
            results.append(await self.binding.call("create_draft_order", {"lines": [{"product_id": "tea", "quantity": 1}]}))
        await self.turn(draft)
        self.assertFalse(results[-1]["ok"])
        self.erp.response = {"success": True, "data": {"ok": True, "state": "completed", "data": {
            "target_operation_id": OP_ID, "tool_name": "create_draft_order", "phase": "unknown",
            "result": None, "next_action": "owner_reconciliation",
        }}}
        async def lookup():
            results.append(await self.binding.call("operation_status", {"operation_id": OP_ID}))
        await self.turn(lookup)
        self.assertEqual(results[-1]["data"]["phase"], "unknown")
        self.assertEqual([call[0] for call in self.erp.calls], ["create_draft_order", "operation_status"])
        with self.assertRaises(HeldOutcome):
            await self.turn(self.draft)
        self.erp.response["data"]["data"]["phase"] = "completed"
        self.erp.response["data"]["data"]["result"] = copy.deepcopy(self.order)
        self.erp.response["data"]["data"]["next_action"] = "none"
        await self.turn(lookup)
        self.erp.response = None
        await self.turn(self.draft)
        self.assertEqual(self.erp.calls[-1][0], "create_draft_order")

    async def test_owner_lookup_recovers_lost_id_then_status_and_separate_confirmation(self):
        self.erp.response = TimeoutError("Synthetic response lost after ERP accepted it")
        with self.assertRaises(TimeoutError):
            await self.turn(self.draft)
        sid = self.message.message_sid
        original_tool, original_args, _context = self.erp.calls[0]
        lookup = FakeOriginalLookup(OriginalOperation(sid, original_tool, original_args, OP_ID))
        # Recreate the binding to exercise persisted metadata after restart.
        self.binding = ERPBinding(self.erp, self.journal, scope="demo", clock=lambda: self.now,
                                  original_lookup=lookup)
        self.erp.response = {"success": True, "data": {"ok": True, "state": "completed", "data": {
            "target_operation_id": OP_ID, "tool_name": "create_draft_order", "phase": "pending",
            "result": None, "next_action": "poll_operation_status",
        }}}
        result = await self.binding.owner_reconcile(sid)
        self.assertEqual(result["data"]["phase"], "pending")
        with self.assertRaises(HeldOutcome):
            await self.turn(self.draft)
        self.erp.response["data"]["data"].update(phase="completed", result=copy.deepcopy(self.order), next_action="none")
        await self.binding.owner_reconcile(sid)
        self.assertEqual(self.journal.db.execute("SELECT COUNT(*) FROM mutation_holds").fetchone()[0], 0)
        state = self.journal.db.execute("SELECT phase,result_ref FROM attempts WHERE operation=?",
                                        ("erp-mutation:" + sid,)).fetchone()
        self.assertEqual(state, ("DONE", OP_ID))
        self.assertEqual([call[0] for call in self.erp.calls],
                         ["create_draft_order", "operation_status", "operation_status"])
        self.assertTrue(all(call[2]["message_sid"] == sid for call in self.erp.calls))
        self.erp.response = None
        await self.turn(self.confirm, text="yes")
        self.assertEqual(self.erp.calls[-1][0], "confirm_order")

    async def test_owner_lookup_must_establish_exact_original_and_never_dispatches(self):
        self.erp.response = TimeoutError("Synthetic lost response")
        with self.assertRaises(TimeoutError):
            await self.turn(self.draft)
        sid = self.message.message_sid
        tool, args, _context = self.erp.calls[0]
        for result in [None, OriginalOperation(sid, tool, {"lines": []}, OP_ID),
                       OriginalOperation(sid, tool, {"lines": [{"product_id": "tea", "quantity": 3}]}, OP_ID),
                       OriginalOperation("another-sid", tool, args, OP_ID)]:
            self.binding.original_lookup = FakeOriginalLookup(result)
            with self.assertRaises(HeldOutcome):
                await self.binding.owner_reconcile(sid)
        self.assertEqual(len(self.erp.calls), 1)
        self.assertEqual(self.journal.db.execute("SELECT COUNT(*) FROM mutation_holds").fetchone()[0], 1)

    async def test_normal_status_after_pending_owner_lookup_restores_original_draft_review(self):
        self.erp.response = TimeoutError("Synthetic lost draft response")
        with self.assertRaises(TimeoutError):
            await self.turn(self.draft)
        sid = self.message.message_sid
        tool, args, _context = self.erp.calls[0]
        self.binding.original_lookup = FakeOriginalLookup(OriginalOperation(sid, tool, args, OP_ID))
        observed = {"target_operation_id": OP_ID, "tool_name": tool, "phase": "pending",
                    "result": None, "next_action": "poll_operation_status"}
        self.erp.response = {"success": True, "data": {"ok": True, "state": "completed", "data": observed}}
        await self.binding.owner_reconcile(sid)
        observed.update(phase="completed", result=copy.deepcopy(self.order), next_action="none")
        async def status():
            await self.binding.call("operation_status", {"operation_id": OP_ID})
        await self.turn(status, text="check the original order")
        status_sid = self.message.message_sid
        snapshot, source_sid = self.journal.db.execute("SELECT snapshot,source_sid FROM reviews").fetchone()
        self.assertEqual(source_sid, sid)
        self.assertNotEqual(source_sid, status_sid)
        self.assertEqual(json.loads(snapshot)["prompt"], self.order["prompt"])
        self.assertEqual(json.loads(snapshot)["version"], 1)
        self.erp.response = None
        await self.turn(self.confirm, text="yes")
        self.assertEqual(self.erp.calls[-1][0], "confirm_order")
        self.assertEqual([call[0] for call in self.erp.calls],
                         ["create_draft_order", "operation_status", "operation_status", "confirm_order"])

    async def test_unsorted_original_lines_match_normalized_owner_arguments(self):
        wire = {"lines": [{"product_id": "tea", "quantity": 2}, {"product_id": "mug", "quantity": 1}]}
        normalized = {"lines": [{"product_id": "mug", "quantity": 1}, {"product_id": "tea", "quantity": 2}]}
        self.erp.response = TimeoutError("Synthetic lost response")
        async def draft():
            await self.binding.call("create_draft_order", wire)
        with self.assertRaises(TimeoutError):
            await self.turn(draft)
        sid = self.message.message_sid
        saved = json.loads(self.journal.db.execute("SELECT original FROM mutation_holds").fetchone()[0])
        self.assertEqual(saved["arguments"], wire)
        lookup = FakeOriginalLookup(OriginalOperation(sid, "create_draft_order", normalized, OP_ID))
        self.binding.original_lookup = lookup
        self.erp.response = {"success": True, "data": {"ok": True, "state": "completed", "data": {
            "target_operation_id": OP_ID, "tool_name": "create_draft_order", "phase": "completed",
            "result": copy.deepcopy(self.order), "next_action": "none",
        }}}
        await self.binding.owner_reconcile(sid)
        self.assertNotEqual(wire, normalized)
        self.assertEqual(lookup.calls[0]["arguments"], normalized)
        self.assertEqual(lookup.calls[0]["canonical_payload"],
                         normalized["lines"])
        self.assertEqual([call[0] for call in self.erp.calls], ["create_draft_order", "operation_status"])

    async def test_duplicate_products_are_refused_before_claim_or_transport(self):
        async def duplicate():
            await self.binding.call("create_draft_order", {"lines": [
                {"product_id": "tea", "quantity": 1}, {"product_id": "tea", "quantity": 2}]})
        with self.assertRaises(ValueError):
            await self.turn(duplicate)
        self.assertEqual(self.erp.calls, [])
        self.assertEqual(self.journal.db.execute("SELECT COUNT(*) FROM mutation_holds").fetchone()[0], 0)

    def test_domain_fingerprints_match_version_aliases_defaults_and_duplicate_refusal(self):
        self.assertEqual(domain_payload("confirm_order", {"order_id": ORDER_ID, "draft_version": 7}),
                         {"order_id": ORDER_ID, "version": 7})
        self.assertEqual(domain_payload("cancel_order", {"order_id": ORDER_ID, "expected_version": 8}),
                         {"order_id": ORDER_ID, "version": 8})
        self.assertEqual(domain_payload("request_human_handoff", {}),
                         {"order_id": None, "reason": "customer_request"})
        with self.assertRaises(ValueError):
            domain_payload("create_draft_order", {"lines": [
                {"product_id": "tea", "quantity": 1}, {"product_id": "tea", "quantity": 2}]})

    async def test_late_completed_response_is_recorded_before_turn_expiry_refusal(self):
        original_call = self.erp.call
        async def late_call(*args, **kwargs):
            result = await original_call(*args, **kwargs)
            self.now += timedelta(seconds=30)
            return result
        self.erp.call = late_call
        with self.assertRaises(PermissionError):
            await self.turn(self.draft)
        state = self.journal.db.execute("SELECT phase,result_ref FROM attempts WHERE operation=?",
                                        ("erp-mutation:" + self.message.message_sid,)).fetchone()
        self.assertEqual(state, ("DONE", OP_ID))
        self.assertEqual(self.journal.db.execute("SELECT COUNT(*) FROM mutation_holds").fetchone()[0], 0)

    async def test_definitive_refusal_finishes_claim_instead_of_becoming_unknown(self):
        self.erp.response = {"success": True, "data": {"ok": False, "state": "refused",
                             "error": {"code": "INSUFFICIENT_STOCK", "message": "Unavailable"}}}
        await self.turn(self.draft)
        self.assertEqual(self.journal.held("demo"), [])
        state = self.journal.db.execute("SELECT phase,result_ref FROM attempts WHERE operation=?",
                                        ("erp-mutation:" + self.message.message_sid,)).fetchone()
        self.assertEqual(state, ("DONE", "refused:create_draft_order"))

    def test_bad_adapter_success_projection_and_foreign_identity_fail_closed(self):
        cases = [
            ("confirm_order", {"success": True}),
            ("confirm_order", {"success": True, "data": {"ok": True, "state": "pending"}}),
            ("confirm_order", {"success": True, "data": {"ok": True, "state": "completed", "operation_id": OP_ID, "data": self.order}}),
            ("order_status", {"success": True, "data": {"ok": False, "state": "refused", "error": {"code": "NOT_FOUND", "message": "Missing", "current_version": 7}}}),
        ]
        for tool, response in cases:
            with self.assertRaises(HeldOutcome):
                business_envelope(tool, response)

    def test_closed_arguments_refuse_boolean_quantity_and_bad_ids(self):
        for quantity in [True, 0, 1001]:
            with self.assertRaises(ValueError):
                arguments_for("check_stock", {"lines": [{"product_id": "tea", "quantity": quantity}]})
        with self.assertRaises(ValueError):
            arguments_for("confirm_order", {"order_id": "another-order", "draft_version": 1})


if __name__ == "__main__":
    unittest.main()
