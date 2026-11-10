from rasa.mantle.tools.decorator import ToolContext, tool
from rasa.mantle.tools.result import ToolResult

import shop


@tool(description="Look up how many tubs of one flavor are on the shelf. Changes nothing.")
async def check_stock(context: ToolContext, flavor: str) -> ToolResult:
    return ToolResult(llm_response={"reply": shop.stock_reply(flavor)})
