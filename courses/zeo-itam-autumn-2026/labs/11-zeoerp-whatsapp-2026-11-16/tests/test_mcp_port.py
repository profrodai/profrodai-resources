import json
import unittest
from contextlib import asynccontextmanager
from types import SimpleNamespace

from channel_runtime import HeldOutcome
from mcp_port import SessionERPPort


class Session:
    def __init__(self):
        self.calls = []
        self.failure = None
        self.envelope = {"success": True, "data": {"ok": True, "state": "completed", "data": {"items": []}}}
        self.text = None
        self.is_error = False

    async def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        if self.failure:
            raise self.failure
        return SimpleNamespace(isError=self.is_error, structuredContent=self.envelope,
                               content=[SimpleNamespace(type="text", text=self.text or json.dumps(self.envelope))])


class MCPPortTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = Session()
        self.contexts = []
        self.closed = 0
        self.validated = []
        self.reject_input = False
        self.reject_output = False

        @asynccontextmanager
        async def factory(*, context_header):
            self.contexts.append(context_header)
            try:
                yield self.session
            finally:
                self.closed += 1

        def validator(tool, direction, value):
            # A boundary fake, not a substitute for full ERP schema validation.
            self.validated.append((tool, direction))
            if (direction == "input" and self.reject_input) or (direction == "output" and self.reject_output):
                raise ValueError("Synthetic schema refusal")

        self.port = SessionERPPort(factory, validator)

    async def test_passes_original_context_once_and_detaches_result(self):
        result = await self.port.call("list_products", {}, context_header="synthetic-original-turn")
        self.assertEqual(self.contexts, ["synthetic-original-turn"])
        self.assertEqual(self.session.calls, [("list_products", {})])
        self.assertEqual(self.validated, [("list_products", "input"), ("list_products", "output")])
        result["data"]["data"]["items"].append("local-change")
        self.assertEqual(self.session.envelope["data"]["data"]["items"], [])
        self.assertEqual(self.closed, 1)

    async def test_typeerror_after_dispatch_never_retries_or_drops_context(self):
        self.session.failure = TypeError("Synthetic failure after a possible effect")
        with self.assertRaises(TypeError):
            await self.port.call("create_draft_order", {"lines": [{"product_id": "p1", "quantity": 1}]},
                                 context_header="original-mutation")
        self.assertEqual(len(self.session.calls), 1)
        self.assertEqual(self.contexts, ["original-mutation"])
        self.assertEqual(self.closed, 1)

    async def test_output_mismatch_never_becomes_a_business_result(self):
        self.session.text = '{"success":false}'
        with self.assertRaises(HeldOutcome):
            await self.port.call("list_products", {}, context_header="turn")
        self.assertEqual(len(self.session.calls), 1)
        self.assertEqual(self.closed, 1)

    async def test_duplicate_text_keys_and_nonfinite_values_refuse(self):
        for text in ['{"success":false,"success":true}', '{"success":NaN}']:
            self.session.text = text
            with self.assertRaises(HeldOutcome):
                await self.port.call("list_products", {}, context_header="turn")

    async def test_schema_refusal_before_call_and_after_response(self):
        self.reject_input = True
        with self.assertRaises(ValueError):
            await self.port.call("list_products", {}, context_header="turn")
        self.assertEqual(self.session.calls, [])
        self.assertEqual(self.contexts, [])
        self.reject_input = False
        self.reject_output = True
        with self.assertRaises(HeldOutcome):
            await self.port.call("list_products", {}, context_header="turn")
        self.assertEqual(len(self.session.calls), 1)
        self.assertEqual(self.closed, 1)

    async def test_transport_error_flag_is_not_business_success(self):
        self.session.is_error = True
        with self.assertRaises(HeldOutcome):
            await self.port.call("list_products", {}, context_header="turn")

    async def test_missing_context_refuses_before_session(self):
        with self.assertRaises(ValueError):
            await self.port.call("list_products", {}, context_header="")
        self.assertEqual(self.contexts, [])
