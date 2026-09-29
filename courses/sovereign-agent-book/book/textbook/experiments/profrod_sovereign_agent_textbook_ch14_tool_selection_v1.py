# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 14 experiment: what happens to tool choice as an agent is offered more tools?

  uv run python \
    book/textbook/experiments/profrod_sovereign_agent_textbook_ch14_tool_selection_v1.py \
      --out ch14-tool-selection-receipt.json

Every tool an MCP server advertises becomes text in the model's prompt. Twenty-four of Lucy's
requests each need exactly one of eight shop tools. Real models (served by Ollama on localhost,
temperature zero) choose among catalogs of 8, 16, 32 and 64 tools, padded either with unrelated
tools, of the kind common MCP servers ship, or with confusable ones (a warehouse count beside
the freezer count, a stock-market quote beside stock level). Two protocols:

  native   the catalog as function-calling tools; the model may call one, or answer in prose
  choice   the catalog listed in the prompt; the model must return one name (a JSON enum)

With --provider anthropic the same decisions go to Claude through the Messages API: native as
its tools parameter, choice as a JSON schema in output_config. Tool search still ranks with
BM25 and the local all-minilm. The receipt records every token and the list-price cost, and the
run stops at --max-usd.

Then tool search: BM25 (Chapter 5) or all-minilm (Chapter 6) picks the five most relevant of
the sixty-four tools first, and only those are offered. The receipt keeps every call: the tool
chosen, prompt tokens and prefill time. Finally, the stdio round trip of the learner's own MCP
client against the teaching server, for scale.
"""

from __future__ import annotations

import argparse
import json
import platform
import random
import runpy
import statistics
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[3]
LEARNER = ROOT / "book/textbook/learner"
MCP = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch14_mcp_learner.py"))
LEXICAL = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch05_retrieval_learner.py"))
VEC = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch06_embeddings_learner.py"))
STATS = runpy.run_path(
    str(LEARNER / "profrod_sovereign_agent_ch16_evaluation_statistics_learner.py")
)
SERVER = str(LEARNER / "profrod_sovereign_agent_ch14_teaching_server.py")
CLAUDE = runpy.run_path(
    str(Path(__file__).with_name("profrod_sovereign_agent_claude_messages_v1.py"))
)
OLLAMA = "http://localhost:11434"
MODELS = ("qwen2.5:0.5b", "qwen2.5:1.5b", "qwen3:0.6b")
CLAUDE_MODELS = ("claude-haiku-4-5-20251001", "claude-sonnet-5-5")
# Set by main(): the provider, and the Claude connection that counts tokens and cost.
RUN: dict = {"provider": "ollama", "claude": None}
SIZES = (8, 16, 32, 64)
SEED = 7


def tool(name: str, description: str, **fields: str) -> dict:
    return {
        "name": name,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": {key: {"type": kind} for key, kind in fields.items()},
            "required": list(fields),
        },
    }


SHOP = [
    tool("stock_level", "Tubs of one flavor currently in Lucy's freezer.", flavor="string"),
    tool(
        "draft_restock",
        "Prepare, but do not send, a replenishment order for Lucy to approve.",
        flavor="string",
        tubs="integer",
    ),
    tool(
        "supplier_delivery_status",
        "Where a placed supplier order is: accepted, shipped or delivered.",
        order_id="string",
    ),
    tool("word_count", "Count the words in a short text.", text="string"),
    tool("send_message_to_lucy", "Send Lucy a message on her phone.", text="string"),
    tool("sales_today", "Tubs of one flavor sold since the shop opened today.", flavor="string"),
    tool(
        "schedule_reminder",
        "Remind Lucy about something at a given time.",
        when="string",
        text="string",
    ),
    tool(
        "record_delivery",
        "Record that a supplier delivery arrived, and how many tubs.",
        order_id="string",
        tubs="integer",
    ),
]

# Three per shop tool, in the same order: a second system's tool that a model could mistake for it.
CONFUSABLE = [
    tool(
        "warehouse_inventory_count",
        "Units of a product held in the central warehouse.",
        sku="string",
    ),
    tool("get_stock_quote", "Latest market price for a stock ticker.", ticker="string"),
    tool(
        "inventory_audit_report",
        "Full inventory audit across all locations for a date.",
        date="string",
    ),
    tool(
        "purchase_order_create",
        "Create and send a purchase order to a vendor.",
        vendor="string",
        items="string",
    ),
    tool("draft_email", "Draft an email without sending it.", to="string", subject="string"),
    tool(
        "restock_forecast", "Forecast next month's restock needs for a product line.", line="string"
    ),
    tool(
        "shipment_tracking",
        "Track a parcel by its carrier tracking number.",
        tracking_number="string",
    ),
    tool("order_history", "List a customer's past orders.", customer_id="string"),
    tool(
        "vendor_lead_time",
        "Typical days between ordering from a vendor and delivery.",
        vendor="string",
    ),
    tool("character_count", "Count the characters in a text.", text="string"),
    tool("text_summarize", "Summarize a long text in a few sentences.", text="string"),
    tool("readability_score", "Score how easy a text is to read.", text="string"),
    tool("send_sms", "Send an SMS to a phone number.", phone="string", text="string"),
    tool(
        "post_team_announcement", "Post an announcement to the whole team channel.", text="string"
    ),
    tool("send_push_notification", "Send a push notification to all app users.", text="string"),
    tool("revenue_report", "Revenue totals for a period.", period="string"),
    tool("customer_count_today", "How many customers visited today.", store="string"),
    tool("sales_forecast", "Forecast sales for next week.", product="string"),
    tool(
        "create_calendar_event",
        "Create a calendar event with a title and start time.",
        title="string",
        start="string",
    ),
    tool("set_timer", "Start a countdown timer on this device.", seconds="integer"),
    tool("snooze_alarm", "Snooze the current alarm.", minutes="integer"),
    tool(
        "receive_goods",
        "Mark a purchase order's goods as received in the ERP system.",
        po_number="string",
    ),
    tool("log_return", "Record goods returned by a customer.", order_id="string", items="string"),
    tool(
        "update_shipment_address",
        "Change the delivery address of an outgoing shipment.",
        shipment_id="string",
        address="string",
    ),
]

UNRELATED = [
    tool(name, description, **{"input": "string"})
    for name, description in [
        ("github_create_issue", "Open an issue in a GitHub repository."),
        ("github_list_pull_requests", "List open pull requests in a GitHub repository."),
        ("github_merge_pull_request", "Merge a GitHub pull request."),
        ("git_commit", "Commit staged changes in a git repository."),
        ("read_file", "Read a file from the local filesystem."),
        ("write_file", "Write text to a file on the local filesystem."),
        ("list_directory", "List the files in a directory."),
        ("search_files", "Search files by name pattern."),
        ("web_search", "Search the web and return result links."),
        ("fetch_url", "Fetch the contents of a web page."),
        ("weather_forecast", "Weather forecast for a city."),
        ("translate_text", "Translate text into another language."),
        ("convert_units", "Convert a quantity between measurement units."),
        ("currency_exchange_rate", "Exchange rate between two currencies."),
        ("send_email", "Send an email."),
        ("slack_post_message", "Post a message to a Slack channel."),
        ("jira_create_ticket", "Create a Jira ticket."),
        ("jira_search", "Search Jira tickets."),
        ("notion_create_page", "Create a page in Notion."),
        ("google_drive_search", "Search documents in Google Drive."),
        ("spreadsheet_read_range", "Read a range of cells from a spreadsheet."),
        ("spreadsheet_write_range", "Write values into spreadsheet cells."),
        ("run_sql_query", "Run a SQL query against a database."),
        ("describe_table", "Describe the columns of a database table."),
        ("create_invoice", "Create an invoice for a client."),
        ("list_invoices", "List issued invoices."),
        ("stripe_refund", "Refund a card payment."),
        ("docker_list_containers", "List running Docker containers."),
        ("kubernetes_get_pods", "List pods in a Kubernetes namespace."),
        ("aws_s3_list_buckets", "List Amazon S3 buckets."),
        ("render_chart", "Render a chart from data."),
        ("summarize_pdf", "Summarize a PDF document."),
        ("extract_text_from_image", "Extract text from an image."),
        ("generate_image", "Generate an image from a description."),
        ("spotify_play", "Play a song on Spotify."),
        ("maps_directions", "Driving directions between two places."),
        ("maps_nearby_search", "Find nearby places of a kind."),
        ("flight_search", "Search for flights."),
        ("hotel_search", "Search for hotels."),
        ("news_headlines", "Latest news headlines."),
        ("wikipedia_lookup", "Look up a Wikipedia article."),
        ("dictionary_define", "Define an English word."),
        ("calculator", "Evaluate an arithmetic expression."),
        ("random_number", "Generate a random number."),
        ("uuid_generate", "Generate a UUID."),
        ("hash_text", "Compute a cryptographic hash of text."),
        ("encode_base64", "Encode text as base64."),
        ("json_validate", "Validate a JSON document."),
        ("regex_test", "Test a regular expression against text."),
        ("cron_explain", "Explain a cron schedule expression."),
        ("timezone_convert", "Convert a time between time zones."),
        ("password_generate", "Generate a strong password."),
        ("qr_code_create", "Create a QR code image."),
        ("pdf_merge", "Merge several PDF files."),
        ("zip_archive", "Create a zip archive of files."),
        ("ping_host", "Check whether a network host responds."),
    ]
]

# Three requests per shop tool, in SHOP order. The third of each is worded to share few words
# with the tool it needs.
TASKS = [
    ("How many tubs of vanilla are in the freezer?", "stock_level"),
    ("Check the strawberry stock for me.", "stock_level"),
    ("Is there much mango left?", "stock_level"),
    ("Prepare a restock of 12 tubs of chocolate for Lucy to approve.", "draft_restock"),
    ("Draft a reorder for pistachio, but don't send it.", "draft_restock"),
    ("We're nearly out of mint; get something ready for Lucy to sign off.", "draft_restock"),
    ("Has supplier order A-1043 shipped yet?", "supplier_delivery_status"),
    ("What's the delivery status of order A-1051?", "supplier_delivery_status"),
    ("Is the van with A-1060 on its way?", "supplier_delivery_status"),
    ("How many words are in 'vanilla stock needs review'?", "word_count"),
    ("Count the words in this note: 'Close early on Sunday for the inspection'.", "word_count"),
    ("Is 'Fresh mango sorbet all week' short enough for the six-word sign?", "word_count"),
    ("Send Lucy a message that the freezer door was left open.", "send_message_to_lucy"),
    ("Tell Lucy on her phone that the supplier called.", "send_message_to_lucy"),
    ("Let the owner know the card reader is down.", "send_message_to_lucy"),
    ("How many tubs of chocolate have we sold today?", "sales_today"),
    ("What are today's vanilla sales so far?", "sales_today"),
    ("How has strawberry been moving since we opened this morning?", "sales_today"),
    ("Remind Lucy at 4pm to call the supplier.", "schedule_reminder"),
    ("Set a reminder for tomorrow morning to defrost the freezer.", "schedule_reminder"),
    ("Make sure Lucy remembers the health inspection on Friday at 9.", "schedule_reminder"),
    ("Record that order A-1043 arrived with 20 tubs.", "record_delivery"),
    ("Log the delivery for A-1051: 15 tubs came in.", "record_delivery"),
    ("The A-1060 van just dropped off 30 tubs.", "record_delivery"),
]


def catalog(size: int, kind: str, task: int) -> list[dict]:
    """The eight shop tools plus size-8 distractors, in a per-task seeded order."""
    extra = size - len(SHOP)
    if kind == "confusable":
        # One confusable per shop tool first, then all of them, then unrelated tools.
        firsts = [CONFUSABLE[3 * i] for i in range(len(SHOP))]
        rest = [t for t in CONFUSABLE if t not in firsts]
        pool = firsts + rest + UNRELATED
    else:
        pool = list(UNRELATED)
    tools = SHOP + pool[:extra]
    random.Random(SEED * 1000 + size * 10 + task).shuffle(tools)
    return tools


def post(path: str, payload: dict) -> dict:
    request = Request(
        f"{OLLAMA}{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=600) as response:
        return json.loads(response.read())


SYSTEM = "You are the assistant for Lucy's ice cream shop. Use the one tool that fits the request."


def claude_ask(model: str, protocol: str, request: str, tools: list[dict]) -> dict:
    """One decision on Claude: native as the tools parameter, choice as a JSON schema."""
    extra: dict = {}
    if protocol == "native":
        system = SYSTEM
        extra["tools"] = [
            {"name": t["name"], "description": t["description"], "input_schema": t["inputSchema"]}
            for t in tools
        ]
    else:
        listing = "\n".join(f"- {t['name']}: {t['description']}" for t in tools)
        system = (
            f"{SYSTEM}\n\nTools:\n{listing}\n\n"
            'Answer with JSON: {"tool": "<name of the one tool that fits>"}'
        )
        schema = {
            "type": "object",
            "required": ["tool"],
            "properties": {"tool": {"type": "string", "enum": [t["name"] for t in tools]}},
            "additionalProperties": False,
        }
        extra["output_config"] = {"format": {"type": "json_schema", "schema": schema}}
    started = time.perf_counter()
    reply = RUN["claude"].messages(
        model,
        max_tokens=256,
        system=system,
        messages=[{"role": "user", "content": request}],
        **extra,
    )
    wall = (time.perf_counter() - started) * 1000
    if protocol == "native":
        calls = CLAUDE["tool_calls"](reply)
        chosen = calls[0]["name"] if calls else None
    else:
        try:
            chosen = json.loads(CLAUDE["text_of"](reply)).get("tool")
        except ValueError:
            chosen = None
    return {
        "chosen": chosen,
        "promptTokens": reply.get("usage", {}).get("input_tokens"),
        "prefillMs": None,
        "wallMs": round(wall, 1),
        "stopReason": reply.get("stop_reason"),
    }


def ask(model: str, protocol: str, request: str, tools: list[dict]) -> dict:
    """One decision. Returns the chosen tool (or None), prompt tokens and prefill milliseconds."""
    if RUN["provider"] == "anthropic":
        return claude_ask(model, protocol, request, tools)
    payload: dict = {
        "model": model,
        "stream": False,
        "think": False,
        "options": {"temperature": 0, "seed": SEED},
    }
    if protocol == "native":
        payload["messages"] = [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": request},
        ]
        payload["tools"] = [MCP["as_model_tool"](t) for t in tools]
    else:
        listing = "\n".join(f"- {t['name']}: {t['description']}" for t in tools)
        payload["messages"] = [
            {
                "role": "system",
                "content": f"{SYSTEM}\n\nTools:\n{listing}\n\n"
                'Answer with JSON: {"tool": "<name of the one tool that fits>"}',
            },
            {"role": "user", "content": request},
        ]
        payload["format"] = {
            "type": "object",
            "required": ["tool"],
            "properties": {"tool": {"type": "string", "enum": [t["name"] for t in tools]}},
        }
    started = time.perf_counter()
    reply = post("/api/chat", payload)
    wall = (time.perf_counter() - started) * 1000
    message = reply.get("message", {})
    if protocol == "native":
        tool_calls = message.get("tool_calls") or []
        chosen = tool_calls[0]["function"]["name"] if tool_calls else None
    else:
        try:
            chosen = json.loads(message.get("content", "")).get("tool")
        except ValueError:
            chosen = None
    return {
        "chosen": chosen,
        "promptTokens": reply.get("prompt_eval_count"),
        "prefillMs": round(reply.get("prompt_eval_duration", 0) / 1e6, 1),
        "wallMs": round(wall, 1),
    }


def embed(texts: list[str]) -> list[list[float]]:
    return [
        VEC["normalize"](v)
        for v in post("/api/embed", {"model": "all-minilm", "input": texts})["embeddings"]
    ]


def summarize(rows: list[dict]) -> dict:
    right = sum(r["chosen"] == r["expected"] for r in rows)
    low, high = STATS["wilson_interval"](right, len(rows))
    return {
        "n": len(rows),
        "correct": right,
        "accuracy": round(right / len(rows), 3),
        "wilson95": [round(low, 3), round(high, 3)],
        "calledAnyTool": round(sum(r["chosen"] is not None for r in rows) / len(rows), 3),
        "medianPromptTokens": statistics.median(r["promptTokens"] or 0 for r in rows),
        "medianPrefillMs": (
            statistics.median(r["prefillMs"] for r in rows)
            if all(r["prefillMs"] is not None for r in rows)
            else None
        ),
        "medianWallMs": statistics.median(r["wallMs"] for r in rows),
    }


def protocol_round_trip(calls: int = 200) -> dict:
    """The learner's own client against the teaching server: handshake, then repeated calls."""
    with tempfile.TemporaryDirectory() as folder:
        command = [sys.executable, SERVER, "--mode", "normal", "--log", str(Path(folder) / "log")]
        started = time.perf_counter()
        with MCP["StdioClient"](command, allowed=frozenset({"word_count"})) as client:
            client.initialize()
            client.list_tools()
            ready = (time.perf_counter() - started) * 1000
            times = []
            for _ in range(calls):
                start = time.perf_counter()
                assert client.call_tool("word_count", {"text": "vanilla stock needs review"}) == "4"
                times.append((time.perf_counter() - start) * 1000)
    return {
        "startAndHandshakeMs": round(ready, 1),
        "calls": calls,
        "medianCallMs": round(statistics.median(times), 3),
        "p95CallMs": round(sorted(times)[int(0.95 * calls) - 1], 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--models", nargs="*")
    parser.add_argument("--provider", choices=("ollama", "anthropic"), default="ollama")
    parser.add_argument("--max-usd", type=float, default=5.0, help="Claude spending ceiling")
    args = parser.parse_args()
    claude = args.provider == "anthropic"
    RUN["provider"] = args.provider
    if claude:
        RUN["claude"] = CLAUDE["Claude"](max_usd=args.max_usd)
    args.models = args.models or list(CLAUDE_MODELS if claude else MODELS)
    catalog64 = catalog(64, "confusable", 0)
    by_name = {t["name"]: t for t in SHOP + CONFUSABLE + UNRELATED}
    assert len(by_name) == len(SHOP) + len(CONFUSABLE) + len(UNRELATED) == 88, "duplicate tool name"
    assert {expected for _, expected in TASKS} == {t["name"] for t in SHOP}

    # Tool search: rank the same sixty-four tools for every request with BM25 and all-minilm.
    names64 = [t["name"] for t in catalog64]
    texts64 = [MCP["tool_text"](t) for t in catalog64]
    tool_vectors = embed(texts64)
    request_vectors = embed([request for request, _ in TASKS])
    searches = {}
    for index, (request, _) in enumerate(TASKS):
        bm25 = LEXICAL["bm25_scores"](request, texts64)
        dense = [VEC["dot"](request_vectors[index], v) for v in tool_vectors]
        for retriever, scores in (("bm25", bm25), ("all-minilm", dense)):
            order = sorted(range(64), key=lambda i: (-scores[i], i))
            searches[(retriever, index)] = [names64[i] for i in order[:5]]
    retrieval = {
        retriever: round(
            sum(expected in searches[(retriever, i)] for i, (_, expected) in enumerate(TASKS))
            / len(TASKS),
            3,
        )
        for retriever in ("bm25", "all-minilm")
    }

    rows: list[dict] = []
    for model in args.models:
        # Start every model cold: a model still loaded from an earlier run keeps those prompts'
        # key-value cache, and a cached prompt reports a prefill of a few milliseconds.
        if not claude:
            post("/api/generate", {"model": model, "keep_alive": 0})
            post(
                "/api/chat",
                {
                    "model": model,
                    "stream": False,
                    "think": False,
                    "messages": [{"role": "user", "content": "hi"}],
                },
            )  # load it once
        for protocol in ("native", "choice"):
            conditions = [
                (size, kind)
                for size in SIZES
                for kind in ("unrelated", "confusable")
                if not (size == 8 and kind == "confusable")
            ]
            for size, kind in conditions:
                for index, (request, expected) in enumerate(TASKS):
                    result = ask(model, protocol, request, catalog(size, kind, index))
                    rows.append(
                        {
                            "model": model,
                            "protocol": protocol,
                            "offer": f"{kind}-{size}",
                            "task": index,
                            "expected": expected,
                            **result,
                        }
                    )
            for retriever in ("bm25", "all-minilm"):
                for index, (request, expected) in enumerate(TASKS):
                    offered = [by_name[name] for name in searches[(retriever, index)]]
                    result = ask(model, protocol, request, offered)
                    rows.append(
                        {
                            "model": model,
                            "protocol": protocol,
                            "offer": f"search-{retriever}-5",
                            "task": index,
                            "expected": expected,
                            **result,
                        }
                    )
            spent = f" ({RUN['claude'].cost():.2f} USD so far)" if claude else ""
            print(model, protocol, "done" + spent, flush=True)

    table = []
    for model in args.models:
        for protocol in ("native", "choice"):
            for offer in dict.fromkeys(r["offer"] for r in rows if r["model"] == model):
                picked = [
                    r
                    for r in rows
                    if (r["model"], r["protocol"], r["offer"]) == (model, protocol, offer)
                ]
                table.append(
                    {"model": model, "protocol": protocol, "offer": offer, **summarize(picked)}
                )

    receipt = {
        "schemaVersion": 1,
        "chapter": 14,
        "created": time.strftime("%Y-%m-%d"),
        "python": platform.python_version(),
        "ollama": OLLAMA,
        "models": args.models,
        "seed": SEED,
        "temperature": 0,
        "coldStart": (
            "each model is unloaded before it is measured: no prompt cached from a prior run"
        ),
        "tasks": [{"request": r, "expected": e} for r, e in TASKS],
        "catalogs": {
            "shop": [t["name"] for t in SHOP],
            "confusable": [t["name"] for t in CONFUSABLE],
            "unrelated": [t["name"] for t in UNRELATED],
        },
        "search": {
            "k": 5,
            "catalog": "confusable-64",
            "recallAt5": retrieval,
            "offered": {f"{r}:{i}": names for (r, i), names in searches.items()},
        },
        "table": table,
        "protocolRoundTrip": protocol_round_trip(),
        "rows": rows,
        "limits": [
            "Small local models at temperature zero; larger models choose better, but the growth"
            " of prompt tokens with the catalog is the same for any model.",
            "Twenty-four requests per condition: differences under about 0.2 are within noise.",
        ],
    }
    if claude:
        receipt |= {
            "provider": "anthropic",
            "api": f"Messages API, anthropic-version {CLAUDE['VERSION']}",
            "settings": {m: CLAUDE["SETTINGS"][m] for m in args.models},
            "coldStart": "no local cache; no request is marked for prompt caching",
            "temperature": "0 on Haiku 4.5; Sonnet 5.5 accepts no temperature setting",
            "usage": RUN["claude"].report(),
            "limits": [
                "Two Claude models through the API; Sonnet 5.5 runs without a temperature "
                "setting, so a rerun can differ by a request or two per condition.",
                "Twenty-four requests per condition: differences under about 0.2 are within "
                "noise. Wall times include the network and the API's queue.",
            ],
        }
        del receipt["ollama"]
    Path(args.out).write_text(json.dumps(receipt, indent=2) + "\n")
    for row in table:
        print(
            f"{row['model']:14} {row['protocol']:6} {row['offer']:22} acc {row['accuracy']:.3f} "
            f"called {row['calledAnyTool']:.2f} tokens {row['medianPromptTokens']:>6} "
            f"prefill {str(row['medianPrefillMs']):>7}ms wall {row['medianWallMs']:>7}ms"
        )


if __name__ == "__main__":
    main()
