"""Native Mantle tool functions; installed only by the paired worker launcher.

The module is an adapter source, not an installed skill or runnable launcher.
Business inputs are checked against the frozen contract before dispatch.
"""

from rasa.mantle.tools.decorator import tool
from rasa.mantle.tools.result import ToolResult

from core_binding import CoreBinding

_binding: CoreBinding | None = None


def install_binding(binding: CoreBinding) -> None:
    global _binding
    if _binding is not None or not isinstance(binding, CoreBinding):
        raise RuntimeError("An admitted ERP binding must be installed exactly once")
    _binding = binding


async def _call(name: str, arguments: dict) -> ToolResult:
    if _binding is None:
        raise RuntimeError("The paired worker has not installed an ERP transport")
    result = await _binding.call(name, arguments)
    return ToolResult(llm_response=result)


@tool(description="List available shop products and prices. This does not reserve stock.")
async def list_products() -> ToolResult:
    return await _call("list_products", {})


@tool(description="Check available quantities for requested products without reserving them.")
async def check_stock(lines: list[dict]) -> ToolResult:
    return await _call("check_stock", {"lines": lines})


@tool(description="Prepare a priced draft. This does not confirm the order; a pending projection remains incomplete.")
async def create_draft_order(lines: list[dict]) -> ToolResult:
    return await _call("create_draft_order", {"lines": lines})


@tool(description="Confirm the exact draft after independently verified customer approval. Pending means committed but not fully projected.")
async def confirm_order(order_id: str, draft_version: int) -> ToolResult:
    return await _call("confirm_order", {"order_id": order_id, "draft_version": draft_version})


@tool(description="Read this customer's order and its current revision.")
async def order_status(order_id: str) -> ToolResult:
    return await _call("order_status", {"order_id": order_id})


@tool(description="Cancel this customer's order at the exact observed revision, if permitted.")
async def cancel_order(order_id: str, expected_version: int) -> ToolResult:
    return await _call("cancel_order", {"order_id": order_id, "expected_version": expected_version})


@tool(description="Read this customer's orders, following only their returned cursor.")
async def my_orders() -> ToolResult:
    return await _call("my_orders", {})
