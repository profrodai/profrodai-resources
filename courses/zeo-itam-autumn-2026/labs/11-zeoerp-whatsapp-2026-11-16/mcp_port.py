"""One MCP call through an injected, context-bound ERP session.

The launcher must supply the reviewed session factory and full producer-schema
validator. This module opens no socket and supplies no authentication. It does
not use the SDK's TypeError compatibility fallback or infer business completion
from MCP transport success. This adapter owns no attempt journal or deadline.
Callers must claim mutations durably, retain uncertain outcomes, and bound the
whole session lifecycle, including callers outside a channel turn. ERP must
independently enforce replay protection for the channel and native request ID.
"""

from __future__ import annotations

import json
from typing import AsyncContextManager, Callable, Protocol

from channel_runtime import HeldOutcome

CORE_TOOLS = frozenset({
    "list_products", "check_stock", "create_draft_order", "confirm_order",
    "order_status", "cancel_order", "my_orders",
})


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


class MCPSession(Protocol):
    async def call_tool(self, name: str, arguments: dict): ...


class BoundSessionFactory(Protocol):
    def __call__(self, *, context_header: str) -> AsyncContextManager[MCPSession]: ...


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate result field")
        result[key] = value
    return result


def _nonfinite(_value):
    raise ValueError("Nonfinite result value")


class SessionERPPort:
    """Require one structured envelope and an identical JSON text envelope.

    validate_schema(tool, direction, value) must raise on failure, using the
    pinned complete ERP input/output schemas, including inner union branches.
    The factory must initialize MCP and bind the original context in transport
    headers, not model arguments. Both are mandatory and remain independently
    qualified boundaries; injecting a fake does not qualify a real transport.
    """

    def __init__(self, sessions: BoundSessionFactory,
                 validate_schema: Callable[[str, str, dict], None]):
        if not callable(sessions) or not callable(validate_schema):
            raise TypeError("A bound session factory and schema validator are required")
        self.sessions = sessions
        self.validate_schema = validate_schema

    async def call(self, tool: str, arguments: dict, *, context_header: str) -> dict:
        if tool not in CORE_TOOLS or not isinstance(context_header, str) or not context_header:
            raise ValueError("A known ERP tool and trusted turn context are required")
        if type(arguments) is not dict:
            raise ValueError("Tool arguments must be an object")
        arguments = json.loads(canonical(arguments))
        self.validate_schema(tool, "input", arguments)
        async with self.sessions(context_header=context_header) as session:
            # Never catch TypeError and try another signature: a failure can
            # follow dispatch. Reconciliation must read the original operation.
            result = await session.call_tool(tool, arguments)
            if getattr(result, "isError", None) is not False:
                raise HeldOutcome("MCP did not return a successful tool envelope")
            structured = getattr(result, "structuredContent", None)
            content = getattr(result, "content", None)
            if type(structured) is not dict or type(content) is not list or len(content) != 1:
                raise HeldOutcome("MCP structured and text envelopes are required")
            item = content[0]
            if getattr(item, "type", None) != "text" or not isinstance(getattr(item, "text", None), str):
                raise HeldOutcome("MCP returned an unexpected content block")
            try:
                text = json.loads(item.text, object_pairs_hook=_object, parse_constant=_nonfinite)
                if canonical(text) != canonical(structured):
                    raise ValueError("Mismatched envelopes")
                self.validate_schema(tool, "output", structured)
                # Detach mutable SDK-owned objects before returning to policy.
                return json.loads(canonical(structured))
            except (ValueError, TypeError, RecursionError):
                raise HeldOutcome("ERP response schema or envelope agreement failed") from None
