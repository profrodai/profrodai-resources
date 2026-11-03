from rasa.mantle.tools.decorator import ToolContext, tool
from rasa.mantle.tools.result import ToolResult

import shop


@tool(description="Propose how many tubs to restock for one flavor. Only the owner may ask, and the owner proves it with the shop PIN. Changes nothing on the shelf.")
async def propose_restock(context: ToolContext, flavor: str, pin: str = "") -> ToolResult:
    return ToolResult(llm_response={"reply": shop.restock_reply(pin, flavor)})
