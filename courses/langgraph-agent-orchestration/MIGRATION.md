# LangGraph Nebius modernization plan

Pinned source: https://github.com/profrodai/langgraph-nebius@78eeb32673b30d2e9fad7671ba28a8fc5d1766d1

Import mode: `legacy-modernize`

Current target: the confidence-routing lab deliberately models a routing decision without
LangGraph or live APIs. Next gate: audit the pinned exercise/test pair and its dependency pins,
write current provider and data-handling guidance, then add a deterministic replacement. Do not
teach the historical setup as current installation advice.
