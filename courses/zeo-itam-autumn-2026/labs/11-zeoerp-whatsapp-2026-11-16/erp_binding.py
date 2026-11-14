"""Historical nine-tool WhatsApp prototype, retained for its original tests.

The active seven-tool Mantle wrapper uses core_binding.py instead. This module
must not be wired to the current commerce server: its old prompt/quote fields,
context shape and maintenance tools are a different contract.

This is a mockable policy component. The admitted transport must additionally
validate the complete producer schemas and MCP structured/text agreement. The
ERP independently verifies the provider record and canonical prompt history;
the context header below is correlation input, never authentication.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Callable, Protocol
from dataclasses import dataclass

from channel_journal import ChannelJournal
from channel_runtime import HeldOutcome, current_binding

MUTATIONS = frozenset({
    "create_draft_order", "confirm_order", "cancel_order", "request_human_handoff",
})
READS = frozenset({"list_products", "check_stock", "order_status", "my_orders", "operation_status"})


class ERPPort(Protocol):
    """A paired transport that validates full MCP input/output schemas."""

    async def call(self, tool: str, arguments: dict, *, context_header: str) -> dict: ...


@dataclass(frozen=True)
class OriginalOperation:
    message_sid: str
    tool: str
    arguments: dict
    operation_id: str


class OriginalLookupPort(Protocol):
    """Transport-owner lookup in the already admitted company namespace.

    This is a private maintenance port, not a tenth model tool or an installed
    endpoint. It must authoritatively identify a persisted original operation;
    candidate matching or a caller's assertion is insufficient. No dispatch.
    Its adapter must recompute domain_payload(tool, arguments) and reject a
    supplied canonical_payload that differs, before the producer lookup.
    """

    async def lookup_original(self, *, message_sid: str, tool: str, arguments: dict,
                              canonical_payload: object) -> OriginalOperation | None: ...


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def arguments_for(tool: str, arguments: dict) -> dict:
    """Validate the nine closed input shapes without accepting model context."""
    fields = {
        "list_products": (set(), {"query", "limit", "cursor"}),
        "check_stock": ({"lines"}, {"lines"}),
        "create_draft_order": ({"lines"}, {"lines"}),
        "confirm_order": ({"order_id", "draft_version"}, {"order_id", "draft_version"}),
        "order_status": ({"order_id"}, {"order_id"}),
        "cancel_order": ({"order_id", "expected_version"}, {"order_id", "expected_version"}),
        "my_orders": (set(), {"limit", "cursor", "state"}),
        "request_human_handoff": (set(), {"order_id", "reason"}),
        "operation_status": ({"operation_id"}, {"operation_id"}),
    }
    if tool not in fields or type(arguments) is not dict:
        raise ValueError("Unknown tool or invalid arguments")
    required, allowed = fields[tool]
    if not required <= arguments.keys() or not arguments.keys() <= allowed:
        raise ValueError("Missing or unexpected tool arguments")
    # Copy before awaiting: the caller cannot change an admitted payload.
    value = json.loads(canonical(arguments))
    for key, item in value.items():
        if key in {"draft_version", "expected_version", "limit"}:
            maximum = 50 if key == "limit" else 2147483647
            if type(item) is not int or not 1 <= item <= maximum:
                raise ValueError("Invalid bounded integer")
        elif key in {"order_id", "operation_id"}:
            prefix = "ord" if key == "order_id" else "op"
            if not isinstance(item, str) or not re.fullmatch(prefix + r"_[0-9a-f]{24}", item):
                raise ValueError("Invalid object ID")
        elif key in {"query", "cursor"}:
            if not isinstance(item, str) or len(item) > (100 if key == "query" else 256):
                raise ValueError("Invalid bounded string")
        elif key == "state" and item not in {"draft", "confirmed", "fulfilled", "cancelled"}:
            raise ValueError("Invalid order state")
        elif key == "reason" and item not in {"customer_request", "order_exception", "delivery_question"}:
            raise ValueError("Invalid handoff reason")
        elif key == "lines":
            if not isinstance(item, list) or not 1 <= len(item) <= 25:
                raise ValueError("Invalid order lines")
            for line in item:
                if type(line) is not dict or set(line) != {"product_id", "quantity"}:
                    raise ValueError("Invalid order line")
                if not isinstance(line["product_id"], str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", line["product_id"]):
                    raise ValueError("Invalid product ID")
                if type(line["quantity"]) is not int or not 1 <= line["quantity"] <= 1000:
                    raise ValueError("Invalid quantity")
            if tool == "create_draft_order" and len({line["product_id"] for line in item}) != len(item):
                raise ValueError("Duplicate product")
    return value


def normalized_arguments(tool: str, arguments: dict) -> dict:
    """Compare original business arguments by the agreed semantic form."""
    value = arguments_for(tool, arguments)
    if tool == "create_draft_order":
        value["lines"].sort(key=lambda line: line["product_id"])
    if tool == "request_human_handoff":
        value.setdefault("reason", "customer_request")
    return value


def domain_payload(tool: str, arguments: dict) -> object:
    """Translate closed wire arguments to the producer's mutation fingerprint.

    Preserve the original wire tuple separately. Sorting JSON object keys does
    not normalize a list or translate version fields. The private owner bridge
    must use this same mapping before its read-only domain lookup.
    """
    value = normalized_arguments(tool, arguments)
    if tool == "create_draft_order":
        return value["lines"]
    if tool == "confirm_order":
        return {"order_id": value["order_id"], "version": value["draft_version"]}
    if tool == "cancel_order":
        return {"order_id": value["order_id"], "version": value["expected_version"]}
    if tool == "request_human_handoff":
        return {"order_id": value.get("order_id"), "reason": value.get("reason", "customer_request")}
    raise ValueError("Original lookup requires a mutation tool")


def business_envelope(tool: str, response: dict) -> dict:
    """Apply consumer invariants after the port's full schema validation."""
    if type(response) is not dict or set(response) != {"success", "data"} or response["success"] is not True:
        raise HeldOutcome("ERP adapter did not return a business envelope")
    envelope = response["data"]
    if type(envelope) is not dict or type(envelope.get("ok")) is not bool:
        raise HeldOutcome("Invalid business envelope")
    phase = envelope.get("state")
    if phase not in {"completed", "pending", "unknown", "refused"} or envelope["ok"] != (phase == "completed"):
        raise HeldOutcome("Inconsistent business completion")
    if phase in {"pending", "unknown"} or (phase == "completed" and tool in MUTATIONS):
        if not re.fullmatch(r"op_[0-9a-f]{24}", str(envelope.get("operation_id", ""))):
            raise HeldOutcome("Missing original operation ID")
    if phase == "refused":
        error = envelope.get("error", {})
        if type(error) is not dict:
            raise HeldOutcome("Invalid refusal")
        if error.get("code") in {"NOT_FOUND", "FORBIDDEN", "UNAUTHENTICATED"} and set(error) != {"code", "message"}:
            raise HeldOutcome("Refusal disclosed another customer's identifiers")
    if phase == "completed" and tool in {"create_draft_order", "confirm_order", "cancel_order"}:
        order = envelope.get("data", {})
        wanted = {"create_draft_order": "draft", "confirm_order": "confirmed", "cancel_order": "cancelled"}[tool]
        if order.get("state") != wanted or order.get("projection", {}).get("state") != "confirmed":
            raise HeldOutcome("Business mutation or projection is incomplete")
    if tool == "operation_status" and phase == "completed":
        original = envelope.get("data", {})
        if original.get("phase") not in {"completed", "pending", "unknown", "refused"}:
            raise HeldOutcome("Original operation phase is missing")
    return envelope


class ERPBinding:
    def __init__(self, port: ERPPort, journal: ChannelJournal, *, scope: str,
                 clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
                 original_lookup: OriginalLookupPort | None = None):
        if not scope:
            raise ValueError("An admitted company/grant scope is required")
        self.port, self.journal, self.scope, self.clock = port, journal, scope, clock
        self.original_lookup = original_lookup
        self.journal.db.execute(
            "CREATE TABLE IF NOT EXISTS reviews (customer TEXT PRIMARY KEY, snapshot TEXT NOT NULL, source_sid TEXT NOT NULL)"
        )
        self.journal.db.execute(
            "CREATE TABLE IF NOT EXISTS mutation_holds (customer TEXT PRIMARY KEY, operation TEXT NOT NULL, operation_id TEXT)"
        )
        if "original" not in {row[1] for row in self.journal.db.execute("PRAGMA table_info(mutation_holds)")}:
            self.journal.db.execute("ALTER TABLE mutation_holds ADD COLUMN original TEXT")
        if "scope" not in {row[1] for row in self.journal.db.execute("PRAGMA table_info(mutation_holds)")}:
            self.journal.db.execute("ALTER TABLE mutation_holds ADD COLUMN scope TEXT")

    async def owner_reconcile(self, message_sid: str) -> dict:
        """Resolve a hold through authoritative owner lookup and a status read.

        Never call a mutation here, replace its SID, or infer that an absent
        lookup result means no effect. The launcher must admit the lookup port;
        this function is deliberately absent from all model tool adapters.
        """
        operation = "erp-mutation:" + message_sid
        row = self.journal.db.execute(
            "SELECT customer,original FROM mutation_holds WHERE operation=? AND scope=?", (operation, self.scope)
        ).fetchone()
        if row is None or row[1] is None or self.original_lookup is None:
            raise HeldOutcome("Original metadata or admitted owner lookup is unavailable")
        customer, encoded = row
        original = json.loads(encoded)
        expected_arguments = canonical(normalized_arguments(original["tool"], original["arguments"]))
        found = await asyncio.wait_for(self.original_lookup.lookup_original(
            message_sid=message_sid, tool=original["tool"], arguments=json.loads(expected_arguments),
            canonical_payload=domain_payload(original["tool"], original["arguments"]),
        ), 20)
        if not isinstance(found, OriginalOperation):
            raise HeldOutcome("Lookup did not establish the exact original operation")
        try:
            found_arguments = canonical(normalized_arguments(found.tool, found.arguments))
        except (ValueError, TypeError):
            raise HeldOutcome("Lookup returned invalid original arguments") from None
        if (found.message_sid != message_sid or found.tool != original["tool"]
                or found_arguments != expected_arguments
                or not re.fullmatch(r"op_[0-9a-f]{24}", found.operation_id)):
            raise HeldOutcome("Lookup did not establish the exact original operation")
        self.journal.db.execute(
            "UPDATE mutation_holds SET operation_id=? WHERE customer=? AND operation=?",
            (found.operation_id, customer, operation),
        )
        context = {**original["context"], "tool": "operation_status", "operation_discriminator": "read",
                   "issued_at": self.clock().isoformat(),
                   "deadline": (self.clock() + timedelta(seconds=20)).isoformat()}
        context.pop("confirmation", None)
        header = base64.urlsafe_b64encode(canonical(context).encode()).decode().rstrip("=")
        result = business_envelope("operation_status", await asyncio.wait_for(self.port.call(
            "operation_status", {"operation_id": found.operation_id}, context_header=header
        ), 20))
        if result["state"] != "completed":
            return result
        observed = result["data"]
        if observed["target_operation_id"] != found.operation_id or observed["tool_name"] != found.tool:
            raise HeldOutcome("Status read did not match the original operation")
        if observed["phase"] in {"completed", "refused"}:
            if observed["phase"] == "completed":
                business_envelope(found.tool, {"success": True, "data": {
                    "ok": True, "state": "completed", "operation_id": found.operation_id,
                    "data": observed["result"],
                }})
                if found.tool == "create_draft_order":
                    self._remember_draft(customer, observed["result"], message_sid)
            self._finish_original(customer, operation, found.operation_id, observed["phase"])
        return result

    def _remember_draft(self, customer: str, order: dict, source_sid: str) -> None:
        if order["state"] == "draft":
            self.journal.db.execute(
                "INSERT OR REPLACE INTO reviews VALUES (?, ?, ?)",
                (customer, canonical(order), source_sid),
            )

    def _finish_original(self, customer: str, operation: str, operation_id: str, phase: str) -> None:
        claim = self.journal.db.execute(
            "SELECT ticket,phase FROM attempts WHERE scope=? AND operation=?", (self.scope, operation)
        ).fetchone()
        if claim is None:
            raise HeldOutcome("Original journal claim is unavailable")
        if claim[1] != "DONE":
            reference = operation_id if phase == "completed" else "refused:" + operation_id
            self.journal.complete(self.scope, operation, claim[0], reference)
        self.journal.db.execute(
            "DELETE FROM mutation_holds WHERE customer=? AND operation=?", (customer, operation)
        )

    def _customer(self, turn) -> str:
        return hashlib.sha256(f"{self.scope}:{turn.message.sender}".encode()).hexdigest()

    def _confirmation(self, turn, arguments: dict) -> dict:
        if turn.message.text.strip().casefold() not in {"yes", "confirm"}:
            raise PermissionError("A separate exact affirmative reply is required")
        row = self.journal.db.execute(
            "SELECT snapshot, source_sid FROM reviews WHERE customer=?", (self._customer(turn),)
        ).fetchone()
        if row is None or row[1] == turn.message.message_sid:
            raise PermissionError("No prior draft review is available for this customer")
        order = json.loads(row[0])
        if order["order_id"] != arguments["order_id"] or order["version"] != arguments["draft_version"]:
            raise PermissionError("The exact reviewed draft version is required")
        prompt = order["prompt"]
        expiry = datetime.fromisoformat(order["quote"]["expires_at"].replace("Z", "+00:00"))
        if expiry.tzinfo is None or expiry <= self.clock() or prompt["delivery_state"] != "confirmed" or not prompt["send_receipt"]:
            raise PermissionError("The review prompt is unsent, uncertain, or expired")
        return {"draft_id": order["order_id"], "draft_version": order["version"],
                "prompt_event_id": prompt["event_id"], "prompt_send_receipt": prompt["send_receipt"]}

    async def call(self, tool: str, arguments: dict) -> dict:
        turn = current_binding(self.clock())
        arguments = arguments_for(tool, arguments)
        context = {
            "schema": "zeoerp.trusted-channel-context/v1", "mode": "broker_poll",
            "message_sid": turn.message.message_sid,
            "broker_execution_id": turn.message.execution_id, "tool": tool,
            "operation_discriminator": "turn-mutation" if tool in MUTATIONS else "read",
            "issued_at": self.clock().isoformat(), "deadline": turn.deadline.isoformat(),
        }
        if tool == "confirm_order":
            context["confirmation"] = self._confirmation(turn, arguments)
        operation = "erp-mutation:" + turn.message.message_sid
        attempt = None
        if tool in MUTATIONS:
            if self.journal.db.execute(
                "SELECT 1 FROM mutation_holds WHERE customer=?", (self._customer(turn),)
            ).fetchone():
                raise HeldOutcome("An earlier mutation requires original-result lookup")
            if self.clock() - turn.message.sent_at > timedelta(seconds=300):
                raise PermissionError("Message is too old for a new mutation")
            # Reserve the customer first. A crash before the message claim
            # leaves a conservative hold; no later message can bypass it.
            self.journal.db.execute(
                "INSERT INTO mutation_holds(customer,operation,operation_id,original,scope) VALUES (?, ?, NULL, ?, ?)",
                (self._customer(turn), operation, canonical({"tool": tool, "arguments": arguments, "context": context}), self.scope),
            )
            try:
                attempt = self.journal.claim(self.scope, operation, binding={
                    "customer": self._customer(turn), "tool": tool, "arguments": canonical(arguments),
                })
                if attempt.state != "START":
                    raise HeldOutcome("This message already has a mutation; look up the original outcome")
            except BaseException:
                # Nothing was dispatched by this caller. Preserve the original
                # message claim while removing only this new pre-dispatch hold.
                self.journal.db.execute(
                    "DELETE FROM mutation_holds WHERE customer=? AND operation=?",
                    (self._customer(turn), operation),
                )
                raise
        header = base64.urlsafe_b64encode(canonical(context).encode()).decode().rstrip("=")
        try:
            timeout = min(20, (turn.deadline - self.clock()).total_seconds())
            if timeout <= 0:
                raise PermissionError("Channel turn expired")
            response = await asyncio.wait_for(
                self.port.call(tool, arguments, context_header=header), timeout
            )
            envelope = business_envelope(tool, response)
            if tool == "operation_status" and envelope["state"] == "completed":
                if envelope["data"]["target_operation_id"] != arguments["operation_id"]:
                    raise HeldOutcome("Lookup returned a different operation")
                if envelope["data"]["phase"] in {"completed", "refused"}:
                    held = self.journal.db.execute(
                        "SELECT operation,original FROM mutation_holds WHERE customer=? AND operation_id=?",
                        (self._customer(turn), arguments["operation_id"]),
                    ).fetchone()
                    if held:
                        original = json.loads(held[1]) if held[1] else None
                        observed = envelope["data"]
                        if original is None or observed["tool_name"] != original["tool"]:
                            raise HeldOutcome("Status read did not match the held original tool")
                        if observed["phase"] == "completed":
                            business_envelope(original["tool"], {"success": True, "data": {
                                "ok": True, "state": "completed", "operation_id": arguments["operation_id"],
                                "data": observed["result"],
                            }})
                            if original["tool"] == "create_draft_order":
                                self._remember_draft(self._customer(turn), observed["result"],
                                                     original["context"]["message_sid"])
                        self._finish_original(self._customer(turn), held[0], arguments["operation_id"], envelope["data"]["phase"])
            if attempt is not None:
                if envelope["state"] in {"completed", "refused"}:
                    reference = envelope.get("operation_id") if envelope["state"] == "completed" else "refused:" + tool
                    self.journal.complete(self.scope, operation, attempt.ticket, reference)
                else:
                    self.journal.uncertain(self.scope, operation, attempt.ticket)
                if envelope["state"] in {"completed", "refused"}:
                    self.journal.db.execute(
                        "DELETE FROM mutation_holds WHERE customer=? AND operation=?",
                        (self._customer(turn), operation),
                    )
                else:
                    self.journal.db.execute(
                        "UPDATE mutation_holds SET operation_id=? WHERE customer=? AND operation=?",
                        (envelope["operation_id"], self._customer(turn), operation),
                    )
            # ERP alone establishes authoritative prompt time, first-reply
            # ordering and provider binding. This snapshot cannot replace it.
            if tool in {"create_draft_order", "order_status"} and envelope["state"] == "completed":
                order = envelope["data"]
                self._remember_draft(self._customer(turn), order, turn.message.message_sid)
            # Record a received authoritative outcome before fencing a turn
            # that expired while awaiting ERP. Never turn known completion
            # into UNKNOWN merely because its customer response is now late.
            current_binding(self.clock())
            return envelope
        except BaseException:
            if attempt is not None:
                # Preserve a completed claim if subsequent local processing
                # failed; never overwrite it or mask the original exception.
                try:
                    self.journal.uncertain(self.scope, operation, attempt.ticket)
                except ValueError:
                    pass
            raise
