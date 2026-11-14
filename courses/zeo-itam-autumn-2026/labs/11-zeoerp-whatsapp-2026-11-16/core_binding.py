"""Channel-neutral caller policy for the seven-tool commerce contract.

The bridge is an independently admitted authentication/approval adapter, not
implemented by this module. The producer's preissued Python fixture bindings
can implement it in a synthetic test; request headers alone cannot implement
production authentication. No channel token or provider call belongs here.
"""
from __future__ import annotations

import asyncio
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from typing import Protocol

from channel_journal import ChannelJournal
from channel_runtime import HeldOutcome
from mcp_port import CORE_TOOLS, canonical

MUTATIONS = frozenset({"create_draft_order", "confirm_order", "cancel_order"})


@dataclass(frozen=True)
class CoreRequest:
    company_id: str
    channel: str
    user_id: str
    request_id: str
    text: str
    sent_at: datetime
    deadline: datetime


@dataclass(frozen=True)
class ApprovalEvidence:
    company_id: str
    channel: str
    user_id: str
    request_id: str
    order_id: str
    draft_version: int
    prompt_reference: str
    expires_at: datetime


@dataclass(frozen=True)
class BoundRequest:
    company_id: str
    channel: str
    user_id: str
    request_id: str
    selector: str


class RequestBridge(Protocol):
    async def approval_for(self, request: CoreRequest, *, order_id: str,
                           draft_version: int) -> ApprovalEvidence | None: ...

    async def bind(self, request: CoreRequest, *, tool: str,
                   approval: ApprovalEvidence | None) -> BoundRequest: ...


@dataclass
class _Turn:
    request: CoreRequest
    active: bool = True


_current: ContextVar[_Turn | None] = ContextVar("commerce_turn", default=None)


@contextmanager
def core_turn(request: CoreRequest):
    """Trusted launcher scope; never populate it from model arguments."""
    if not isinstance(request, CoreRequest) or _current.get() is not None:
        raise ValueError("A distinct trusted commerce turn is required")
    turn = _Turn(request)
    token = _current.set(turn)
    try:
        yield
    finally:
        turn.active = False
        _current.reset(token)


def current_request(now: datetime) -> CoreRequest:
    turn = _current.get()
    if turn is None or not turn.active:
        raise PermissionError("No active commerce turn")
    request = turn.request
    values = (request.company_id, request.channel, request.user_id, request.request_id)
    if any(not isinstance(value, str) or not 0 < len(value) <= 256 for value in values):
        raise PermissionError("Invalid trusted request identity")
    if (not isinstance(request.text, str) or request.sent_at.tzinfo is None
            or request.deadline.tzinfo is None or not request.sent_at <= now < request.deadline):
        raise PermissionError("Commerce turn is invalid or expired")
    return request


def business_result(tool: str, payload: dict) -> dict:
    """Interpret an already full-schema-validated current commerce envelope."""
    if type(payload) is not dict or payload.get("success") is not True:
        raise HeldOutcome("Missing Core envelope")
    result = payload.get("data")
    if type(result) is not dict or type(result.get("ok")) is not bool:
        raise HeldOutcome("Missing commerce business result")
    if result["ok"] is False:
        if result.get("state") != "refused" or type(result.get("error")) is not dict:
            raise HeldOutcome("Invalid commerce refusal")
        return result
    state, projection = result.get("state"), result.get("projection")
    if state not in {"completed", "pending"} or projection not in {"confirmed", "pending", "not_requested"}:
        raise HeldOutcome("Invalid commerce phase")
    if (state == "pending") != (projection == "pending"):
        raise HeldOutcome("Inconsistent commerce phase")
    if tool in MUTATIONS:
        record = result.get("data")
        wanted = {"create_draft_order": "draft", "confirm_order": "confirmed", "cancel_order": "cancelled"}[tool]
        if (type(record) is not dict or record.get("state") != wanted
                or projection == "not_requested" or not isinstance(result.get("operation_id"), str)
                or not result["operation_id"] or record.get("operation_id") != result["operation_id"]):
            raise HeldOutcome("Mutation record or projection is incomplete")
    if tool in MUTATIONS | {"order_status"}:
        record = result.get("data")
        expiry = record.get("expires_at_epoch") if type(record) is dict else None
        if type(expiry) not in (int, float) or not math.isfinite(expiry):
            raise HeldOutcome("Missing finite order expiry")
    elif tool in {"list_products", "check_stock", "my_orders"} and projection != "not_requested":
        raise HeldOutcome("Unexpected read projection")
    return result


class CoreBinding:
    def __init__(self, port, journal: ChannelJournal, bridge: RequestBridge, *,
                 clock=lambda: datetime.now(timezone.utc)):
        if not callable(getattr(port, "validate_schema", None)):
            raise TypeError("The current complete schema validator is required")
        self.port, self.journal, self.bridge, self.clock = port, journal, bridge, clock
        self.journal.db.execute("CREATE TABLE IF NOT EXISTS commerce_holds ("
            "customer TEXT PRIMARY KEY, scope TEXT NOT NULL, operation TEXT NOT NULL, "
            "ticket TEXT NOT NULL, original TEXT NOT NULL, operation_id TEXT, order_id TEXT, version INTEGER)")

    async def _bounded(self, function, *args, **kwargs):
        request = current_request(self.clock())
        async with asyncio.timeout((request.deadline - self.clock()).total_seconds()):
            return await function(*args, **kwargs)

    async def call(self, tool: str, arguments: dict) -> dict:
        request = current_request(self.clock())
        if tool not in CORE_TOOLS or type(arguments) is not dict:
            raise ValueError("Unknown commerce tool or arguments")
        arguments = json.loads(canonical(arguments))
        self.port.validate_schema(tool, "input", arguments)
        identity = (request.company_id, request.channel, request.user_id, request.request_id)
        customer = hashlib.sha256(canonical(identity[:3]).encode()).hexdigest()
        scope = "commerce:" + request.company_id
        operation = "request:" + hashlib.sha256(canonical(identity[1::2]).encode()).hexdigest()
        if tool in MUTATIONS and self.journal.db.execute(
                "SELECT 1 FROM commerce_holds WHERE customer=?", (customer,)).fetchone():
            raise HeldOutcome("An original mutation requires read-only reconciliation")
        approval = None
        if tool == "confirm_order":
            if request.text.strip().casefold() not in {"yes", "confirm"}:
                raise PermissionError("A separate explicit affirmative reply is required")
            approval = await self._bounded(self.bridge.approval_for, request,
                order_id=arguments["order_id"], draft_version=arguments["draft_version"])
            if (not isinstance(approval, ApprovalEvidence)
                    or (approval.company_id, approval.channel, approval.user_id, approval.request_id) != identity
                    or approval.order_id != arguments["order_id"]
                    or type(approval.draft_version) is not int or approval.draft_version != arguments["draft_version"]
                    or not isinstance(approval.prompt_reference, str) or not approval.prompt_reference
                    or approval.expires_at.tzinfo is None
                    or approval.expires_at <= self.clock()):
                raise PermissionError("Exact independently verified draft approval is unavailable")
        bound = await self._bounded(self.bridge.bind, request, tool=tool, approval=approval)
        if (not isinstance(bound, BoundRequest)
                or (bound.company_id, bound.channel, bound.user_id, bound.request_id) != identity
                or not isinstance(bound.selector, str) or not 0 < len(bound.selector) <= 256
                or "\r" in bound.selector or "\n" in bound.selector):
            raise PermissionError("The authenticated bridge did not bind this exact request")
        attempt = None
        if tool in MUTATIONS:
            if (self.clock() - request.sent_at).total_seconds() > 300:
                raise PermissionError("Request is too old for a new mutation")
            # A pre-claim row conservatively holds a crash before dispatch too.
            self.journal.db.execute("INSERT INTO commerce_holds VALUES (?, ?, ?, '', ?, NULL, NULL, NULL)",
                (customer, scope, operation, canonical({"request_id": request.request_id,
                    "channel": request.channel, "tool": tool, "arguments": arguments})))
            try:
                attempt = self.journal.claim(scope, operation, binding={"customer": customer,
                    "tool": tool, "arguments": canonical(arguments)})
                if attempt.state != "START":
                    raise HeldOutcome("This request already has an original mutation")
                self.journal.db.execute("UPDATE commerce_holds SET ticket=? WHERE customer=?", (attempt.ticket, customer))
            except BaseException:
                self.journal.db.execute("DELETE FROM commerce_holds WHERE customer=? AND ticket=''", (customer,))
                raise
        try:
            payload = await self._bounded(self.port.call, tool, arguments, context_header=bound.selector)
            result = business_result(tool, payload)
            if result["ok"] and tool in {"confirm_order", "cancel_order", "order_status"}:
                record = result["data"]
                if record["order_id"] != arguments["order_id"]:
                    raise HeldOutcome("A different order was returned")
                version_key = {"confirm_order": "draft_version", "cancel_order": "expected_version"}.get(tool)
                if version_key and record["version"] != arguments[version_key] + 1:
                    raise HeldOutcome("A different mutation version was returned")
            if attempt is not None:
                if result["state"] == "pending":
                    record = result["data"]
                    self.journal.db.execute("UPDATE commerce_holds SET operation_id=?,order_id=?,version=? WHERE customer=?",
                        (result["operation_id"], record["order_id"], record["version"], customer))
                    self.journal.uncertain(scope, operation, attempt.ticket)
                else:
                    reference = result.get("operation_id") or "refused:" + operation
                    self.journal.complete(scope, operation, attempt.ticket, reference)
                    self.journal.db.execute("DELETE FROM commerce_holds WHERE customer=?", (customer,))
            if tool == "order_status" and result["state"] == "completed" and result["projection"] == "confirmed":
                record = result["data"]
                held = self.journal.db.execute("SELECT scope,operation,ticket,operation_id FROM commerce_holds "
                    "WHERE customer=? AND order_id=? AND version=?", (customer, record["order_id"], record["version"])).fetchone()
                if held and held[3] == record.get("operation_id") and held[2]:
                    self.journal.complete(held[0], held[1], held[2], held[3])
                    self.journal.db.execute("DELETE FROM commerce_holds WHERE customer=?", (customer,))
            current_request(self.clock())
            return result
        except BaseException:
            if attempt is not None:
                try:
                    self.journal.uncertain(scope, operation, attempt.ticket)
                except ValueError:
                    pass
            raise

    def owner_original(self, *, company_id: str, channel: str, user_id: str) -> dict:
        """Private maintenance metadata only: no tool, lookup endpoint or replay.

        If the operation ID was lost, the ERP owner must establish the original
        company/channel/request outcome. No model-callable recovery method or
        automatic clear is invented while that owner path remains unqualified.
        """
        customer = hashlib.sha256(canonical((company_id, channel, user_id)).encode()).hexdigest()
        row = self.journal.db.execute("SELECT original,operation_id,order_id,version FROM commerce_holds WHERE customer=?",
                                      (customer,)).fetchone()
        if row is None:
            raise HeldOutcome("No original held request is available")
        return {"original": json.loads(row[0]), "operation_id": row[1], "order_id": row[2], "version": row[3]}
