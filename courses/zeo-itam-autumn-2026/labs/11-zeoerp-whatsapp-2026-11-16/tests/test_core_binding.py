"""Current commerce policy with fake bridge and already-validated port.

These tests execute no ERP, MCP, Rasa, full JSON Schema engine or provider.
"""
import ast
import asyncio
from contextlib import asynccontextmanager
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
import sqlite3
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from channel_journal import BindingConflict, ChannelJournal
from channel_runtime import HeldOutcome
from commerce_schema import CONTRACT_SHA256
from core_binding import (ApprovalEvidence, BoundRequest, CompletedAfterDeadline, CoreBinding, CoreRequest,
                          business_result, core_turn)
from mcp_port import CORE_TOOLS

ORDER = "ord_" + "1" * 24
OPERATION = "op_" + "2" * 24


def envelope(*, state="draft", version=1, projection="confirmed", order_id=ORDER):
    return {"success": True, "data": {"ok": True,
        "state": "pending" if projection == "pending" else "completed",
        "projection": projection, "operation_id": OPERATION,
        "data": {"order_id": order_id, "version": version, "state": state,
                 "operation_id": OPERATION, "expires_at_epoch": 1900000000.0}}}


class Bridge:
    def __init__(self):
        self.approval = None
        self.calls = []
        self.wrong_user = False

    async def approval_for(self, request, **kwargs):
        self.calls.append(("approval", request, kwargs))
        return self.approval

    async def bind(self, request, *, tool, approval):
        self.calls.append(("bind", request, tool, approval))
        return BoundRequest(request.company_id, request.channel,
            "other" if self.wrong_user else request.user_id,
            request.request_id, "fixture-selector:" + request.request_id)


class Port:
    def __init__(self):
        self.calls = []
        self.response = envelope()
        self.after = None

    def validate_schema(self, tool, direction, value):
        # Already-validated transport fake. Full frozen-schema runtime is
        # deliberately not claimed by this standard-library test composition.
        if direction == "input" and tool in {"list_products", "my_orders"} and value:
            raise ValueError("Empty input required")

    async def call(self, tool, arguments, **kwargs):
        self.calls.append((tool, arguments, kwargs))
        if isinstance(self.response, BaseException):
            raise self.response
        if self.after:
            self.after()
        return json.loads(json.dumps(self.response))


class CoreBindingTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "private.sqlite3"
        self.journal = ChannelJournal(self.path)
        self.now = datetime(2026, 11, 14, 17, tzinfo=timezone.utc)
        self.request = CoreRequest("demo", "telegram", "operator-fixture", "update-1", "two teas",
            self.now - timedelta(seconds=1), self.now + timedelta(seconds=30))
        self.bridge, self.port = Bridge(), Port()
        self.binding = CoreBinding(self.port, self.journal, self.bridge, clock=lambda: self.now)

    def tearDown(self):
        self.journal.close()
        self.tmp.cleanup()

    async def call(self, tool="create_draft_order", args=None, **changes):
        request = replace(self.request, **changes)
        with core_turn(request):
            return await self.binding.call(tool, {"lines": [{"product_id": "tea", "quantity": 2}]} if args is None else args)

    def approve(self, **changes):
        self.bridge.approval = ApprovalEvidence("demo", "telegram", "operator-fixture", "yes-2",
            ORDER, 1, "verified-original-prompt-receipt", self.now + timedelta(minutes=2))
        self.bridge.approval = replace(self.bridge.approval, **changes)

    async def test_current_order_without_legacy_prompt_or_quote_is_accepted(self):
        result = await self.call()
        self.assertEqual(result["data"]["expires_at_epoch"], 1900000000.0)
        self.assertEqual(self.port.calls[0][2], {"context_header": "fixture-selector:update-1"})
        self.assertEqual(self.journal.db.execute("SELECT count(*) FROM commerce_holds").fetchone()[0], 0)

    async def test_pending_is_not_rollback_and_later_write_is_held(self):
        self.port.response = envelope(projection="pending")
        result = await self.call()
        self.assertTrue(result["ok"])
        self.assertEqual(result["state"], "pending")
        with self.assertRaises(HeldOutcome):
            await self.call(request_id="another-update")
        original = self.binding.owner_original(company_id="demo", channel="telegram", user_id="operator-fixture")
        self.assertEqual(original["operation_id"], OPERATION)
        self.assertEqual(original["original"]["request_id"], "update-1")
        self.assertEqual(len(self.port.calls), 1)

    async def test_only_exact_current_record_status_resolves_known_pending(self):
        self.port.response = envelope(projection="pending")
        await self.call()
        self.port.response = envelope(version=2)
        await self.call("order_status", {"order_id": ORDER}, request_id="read-newer")
        self.assertEqual(self.journal.db.execute("SELECT count(*) FROM commerce_holds").fetchone()[0], 1)
        self.port.response = envelope()
        await self.call("order_status", {"order_id": ORDER}, request_id="read-exact")
        self.assertEqual(self.journal.db.execute("SELECT count(*) FROM commerce_holds").fetchone()[0], 0)
        self.assertEqual(self.journal.db.execute("SELECT phase FROM attempts").fetchone()[0], "DONE")

    async def test_current_status_without_operation_id_uses_known_original_binding(self):
        self.port.response = envelope(projection="pending")
        await self.call()
        self.port.response = envelope()
        self.port.response["data"]["operation_id"] = None
        self.port.response["data"]["data"]["operation_id"] = None
        await self.call("order_status", {"order_id": ORDER}, request_id="read-exact")
        self.assertEqual(self.journal.db.execute("SELECT count(*) FROM commerce_holds").fetchone()[0], 0)
        self.assertEqual(self.journal.db.execute("SELECT result_ref FROM attempts").fetchone()[0], OPERATION)

    async def test_status_with_different_operation_cannot_resolve_original(self):
        self.port.response = envelope(projection="pending")
        await self.call()
        self.port.response = envelope()
        self.port.response["data"]["data"]["operation_id"] = "op_" + "3" * 24
        await self.call("order_status", {"order_id": ORDER}, request_id="read-foreign-operation")
        self.assertEqual(self.journal.db.execute("SELECT count(*) FROM commerce_holds").fetchone()[0], 1)

    async def test_unknown_without_id_survives_restart_without_invented_lookup(self):
        self.port.response = TimeoutError("Synthetic lost original response")
        with self.assertRaises(TimeoutError):
            await self.call()
        self.journal.close()
        self.journal = ChannelJournal(self.path)
        self.binding = CoreBinding(self.port, self.journal, self.bridge, clock=lambda: self.now)
        with self.assertRaises(HeldOutcome):
            await self.call(request_id="fresh-update")
        original = self.binding.owner_original(company_id="demo", channel="telegram", user_id="operator-fixture")
        self.assertIsNone(original["operation_id"])
        self.assertEqual(len(self.port.calls), 1)

    async def test_exact_yes_requires_independent_matching_approval(self):
        self.port.response = envelope(state="confirmed", version=2)
        args = {"order_id": ORDER, "draft_version": 1}
        with self.assertRaises(PermissionError):
            await self.call("confirm_order", args, request_id="yes-2", text="yes")
        self.approve(draft_version=2)
        with self.assertRaises(PermissionError):
            await self.call("confirm_order", args, request_id="yes-2", text="yes")
        self.approve()
        with self.assertRaises(PermissionError):
            await self.call("confirm_order", args, request_id="yes-2", text="yes, change it")
        self.assertEqual(self.port.calls, [])
        result = await self.call("confirm_order", args, request_id="yes-2", text=" YES ")
        self.assertEqual(result["data"]["state"], "confirmed")
        self.assertNotIn("approval", self.port.calls[-1][1])
        self.assertEqual(self.bridge.calls[-1][3], self.bridge.approval)

    async def test_wrong_customer_or_expired_approval_never_dispatches(self):
        args = {"order_id": ORDER, "draft_version": 1}
        for changes in ({"user_id": "other"}, {"expires_at": self.now}):
            self.approve(**changes)
            with self.assertRaises(PermissionError):
                await self.call("confirm_order", args, request_id="yes-2", text="yes")
        self.assertEqual(self.port.calls, [])

    async def test_native_request_identity_includes_channel_and_rejects_user_rebinding(self):
        await self.call()
        await self.call(channel="whatsapp")
        self.assertEqual(len(self.port.calls), 2)
        with self.assertRaises(BindingConflict):
            await self.call(user_id="other")
        self.assertEqual(len(self.port.calls), 2)

    async def test_closed_or_expired_turn_cannot_use_inherited_context(self):
        ready = asyncio.Event()
        async def late():
            await ready.wait()
            return await self.binding.call("my_orders", {})
        with core_turn(self.request):
            task = asyncio.create_task(late())
        ready.set()
        with self.assertRaises(PermissionError):
            await task
        with self.assertRaises(PermissionError):
            await self.call(deadline=self.now)
        self.assertEqual(self.port.calls, [])

    async def test_wrong_bridge_identity_refuses_before_claim_or_call(self):
        self.bridge.wrong_user = True
        with self.assertRaises(PermissionError):
            await self.call()
        self.assertEqual(self.port.calls, [])
        self.assertEqual(self.journal.db.execute("SELECT count(*) FROM attempts").fetchone()[0], 0)

    async def test_legacy_read_fields_refuse_before_context_binding(self):
        with self.assertRaises(ValueError):
            await self.call("list_products", {"limit": 20})
        self.assertEqual(self.bridge.calls, [])
        self.assertEqual(self.port.calls, [])

    async def test_known_completion_is_recorded_before_late_turn_refusal(self):
        self.port.after = lambda: setattr(self, "now", self.now + timedelta(minutes=1))
        with self.assertRaises(CompletedAfterDeadline) as raised:
            await self.call()
        self.assertEqual(raised.exception.result["state"], "completed")
        self.assertEqual(raised.exception.result["operation_id"], OPERATION)
        self.assertEqual(raised.exception.result["data"]["order_id"], ORDER)
        self.assertEqual(self.journal.db.execute("SELECT phase FROM attempts").fetchone()[0], "DONE")

    async def test_concurrent_preclaim_hold_race_fails_closed_before_second_dispatch(self):
        both_bound, release_bind = asyncio.Event(), asyncio.Event()
        in_port, release_port = asyncio.Event(), asyncio.Event()
        count = 0
        original_bind = self.bridge.bind

        async def bind(request, **kwargs):
            nonlocal count
            count += 1
            if count == 2:
                both_bound.set()
            await release_bind.wait()
            return await original_bind(request, **kwargs)

        async def slow_call(tool, arguments, **kwargs):
            self.port.calls.append((tool, arguments, kwargs))
            in_port.set()
            await release_port.wait()
            return envelope()

        self.bridge.bind, self.port.call = bind, slow_call
        first = asyncio.create_task(self.call(request_id="concurrent-1"))
        second = asyncio.create_task(self.call(request_id="concurrent-2"))
        try:
            await asyncio.wait_for(both_bound.wait(), 1)
            release_bind.set()
            await asyncio.wait_for(in_port.wait(), 1)
            done, _pending = await asyncio.wait((first, second), timeout=1,
                                               return_when=asyncio.FIRST_COMPLETED)
            self.assertEqual(len(done), 1)
            self.assertIsInstance(next(iter(done)).exception(), sqlite3.IntegrityError)
            self.assertEqual(len(self.port.calls), 1)
            self.assertEqual(self.journal.db.execute("SELECT count(*) FROM commerce_holds").fetchone()[0], 1)
        finally:
            release_bind.set()
            release_port.set()
            outcomes = await asyncio.gather(first, second, return_exceptions=True)
        self.assertEqual(sum(isinstance(value, sqlite3.IntegrityError) for value in outcomes), 1)

    async def test_mutation_wrong_order_or_version_is_held_not_completed(self):
        self.approve()
        self.port.response = envelope(state="confirmed", version=3)
        with self.assertRaises(HeldOutcome):
            await self.call("confirm_order", {"order_id": ORDER, "draft_version": 1}, request_id="yes-2", text="yes")
        self.assertEqual(self.journal.db.execute("SELECT phase FROM attempts").fetchone()[0], "UNKNOWN")

    def test_pending_phase_semantics_and_frozen_contract_integrity(self):
        payload = envelope(projection="pending")
        self.assertEqual(business_result("create_draft_order", payload)["state"], "pending")
        payload["data"]["state"] = "completed"
        with self.assertRaises(HeldOutcome):
            business_result("create_draft_order", payload)
        path = Path(__file__).resolve().parents[1] / "contracts/commerce-mcp-v1.json"
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), CONTRACT_SHA256)
        tools = json.loads(path.read_text())["tools"]
        self.assertEqual(set(tools), CORE_TOOLS)

    async def test_actual_native_wrapper_bodies_emit_only_seven_current_inputs(self):
        # Selected source bodies with fake decorator/result; not a native import.
        source = Path(__file__).resolve().parents[1] / "mantle_tools.py"
        module = ast.parse(source.read_text())
        decorated = [node.name for node in module.body if isinstance(node, ast.AsyncFunctionDef) and node.decorator_list]
        self.assertEqual(set(decorated), CORE_TOOLS)
        calls = []
        async def call(name, args):
            calls.append((name, args))
            return SimpleNamespace(llm_response={})
        selected = [node for node in module.body if isinstance(node, ast.AsyncFunctionDef) and node.name in CORE_TOOLS]
        namespace = {"tool": lambda **_kw: lambda fn: fn, "ToolResult": object, "_call": call}
        exec(compile(ast.Module(body=selected, type_ignores=[]), str(source), "exec"), namespace)
        await namespace["list_products"]()
        await namespace["my_orders"]()
        self.assertEqual(calls, [("list_products", {}), ("my_orders", {})])
