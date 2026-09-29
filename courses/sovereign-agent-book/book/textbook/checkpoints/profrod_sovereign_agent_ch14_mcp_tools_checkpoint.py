# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 14: the bounded stdio MCP client against every failure its brief names.

Each check starts the scripted teaching server in one mode and reads the server's own call log,
so a tool invocation is observed independently of what the client reports about itself.
"""

import json
import os
import runpy
import statistics
import sys
import tempfile
import time
from pathlib import Path

BOOK = Path(__file__).resolve().parents[1]
MCP = runpy.run_path(str(BOOK / "learner/profrod_sovereign_agent_ch14_mcp_learner.py"))
SERVER = str(BOOK / "learner/profrod_sovereign_agent_ch14_teaching_server.py")
StdioClient = MCP["StdioClient"]
LEXICAL = runpy.run_path(str(BOOK / "learner/profrod_sovereign_agent_ch05_retrieval_learner.py"))
STATS = runpy.run_path(
    str(BOOK / "learner/profrod_sovereign_agent_ch16_evaluation_statistics_learner.py")
)
EXPERIMENT = runpy.run_path(
    str(BOOK / "experiments/profrod_sovereign_agent_textbook_ch14_tool_selection_v1.py")
)
ALLOWED = frozenset({"word_count"})


def calls(log: Path) -> list[dict]:
    return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []


def server(mode: str, folder: str) -> tuple[list[str], Path]:
    log = Path(folder) / f"{mode}-calls.jsonl"
    return [sys.executable, SERVER, "--mode", mode, "--log", str(log)], log


def fails(mode: str, error: type[BaseException], *, step: str = "call", **options) -> list[dict]:
    """Run one mode, expect `error` at `step`, and return what the server really received."""
    with tempfile.TemporaryDirectory() as folder:
        command, log = server(mode, folder)
        with StdioClient(command, allowed=ALLOWED, **options) as client:
            try:
                client.initialize()
                if step == "initialize":
                    raise AssertionError(f"{mode}: initialization should have been refused")
                client.list_tools()
                client.call_tool("word_count", {"text": "vanilla stock needs review"})
            except error:
                return calls(log)
        raise AssertionError(f"{mode}: expected {error.__name__}")


def framing_and_identity():
    """The pieces, by hand: frames, the frame limit, and response identity."""
    frame = MCP["encode_frame"](MCP["request_message"](41, "tools/list", {}), 1024)
    assert frame.endswith(b"\n") and frame.count(b"\n") == 1
    reader = MCP["FrameReader"](64)
    assert reader.feed(b'{"a":1}\n{"b"') == [b'{"a":1}'] and reader.feed(b":2}\n") == [b'{"b":2}']
    try:
        MCP["FrameReader"](16).feed(b"x" * 16)
    except ValueError:
        pass
    else:
        raise AssertionError("an unterminated frame at the limit must be refused")
    reply = {"jsonrpc": "2.0", "id": 42, "result": {"tools": []}}
    try:
        MCP["answer_for"](41, reply)
    except ValueError:
        pass
    else:
        raise AssertionError("request 41 must not accept the answer labeled 42")
    assert MCP["answer_for"](41, {"jsonrpc": "2.0", "method": "notifications/message"}) is None
    print("ok   frames are single lines, the limit holds, and a reply answers only its own id")


def the_protocol_done_right():
    with tempfile.TemporaryDirectory() as folder:
        command, log = server("normal", folder)
        with StdioClient(command, allowed=ALLOWED) as client:
            assert client.initialize()["protocolVersion"] == "2025-06-18"
            assert set(client.list_tools()) == {"word_count", "place_purchase"}
            assert client.call_tool("word_count", {"text": "vanilla stock needs review"}) == "4"
            try:
                client.call_tool("place_purchase", {"flavor": "vanilla", "tubs": 100})
            except PermissionError:
                pass
            else:
                raise AssertionError("discovery must not grant permission")
        received = calls(log)
    assert [call["name"] for call in received] == ["word_count"], received
    print(
        "ok   handshake, discovery and one allowed call;"
        " the advertised purchase never reached the server"
    )


def every_failure_the_brief_names():
    assert fails("old-version", ValueError, step="initialize") == []
    assert len(fails("wrong-id", ValueError)) == 1  # the server did run it; we refused the answer
    assert len(fails("oversized", ValueError)) == 1
    assert len(fails("stdout-log", ValueError)) == 1
    started = time.monotonic()
    assert len(fails("hang", TimeoutError, timeout=1.0)) == 1
    assert time.monotonic() - started < 5, "the deadline, not the server, ends a hung call"
    with tempfile.TemporaryDirectory() as folder:
        command, _ = server("stale", folder)
        with StdioClient(command, allowed=ALLOWED) as client:
            client.initialize()
            client.list_tools()
            assert client.call_tool("word_count", {"text": "vanilla stock needs review"}) == "4"
            try:
                client.call_tool("word_count", {"text": "one two three"})
            except ValueError:
                pass
            else:
                raise AssertionError("a late reply to the previous call answered this one")
    for mode in ("stderr-log", "notify"):
        with tempfile.TemporaryDirectory() as folder:
            command, _ = server(mode, folder)
            with StdioClient(command, allowed=ALLOWED) as client:
                client.initialize()
                client.list_tools()
                assert client.call_tool("word_count", {"text": "one two three"}) == "3", mode
    print(
        "ok   old version, wrong id, stale reply, oversized frame, stdout log and hang"
        " all end without a result;"
        " stderr and notifications do not disturb a call"
    )


def cleanup_ends_the_group():
    with tempfile.TemporaryDirectory() as folder:
        command, log = server("lingering", folder)
        client = StdioClient(command, allowed=ALLOWED)
        client.initialize()
        grandchild = int(Path(str(log) + ".grandchild").read_text())
        client.close()
        time.sleep(0.2)
        try:
            os.kill(grandchild, 0)
        except ProcessLookupError:
            pass
        else:
            raise AssertionError("closing the client left the server's grandchild running")
    print("ok   closing the client ends the server's whole process group")


def negative_control():
    """Remove the allowlist and the server's own log exposes the forbidden call."""

    class NoAllowlist(StdioClient):
        def call_tool(self, name, arguments):
            return MCP["result_text"](
                self.request("tools/call", {"name": name, "arguments": arguments})
            )

    with tempfile.TemporaryDirectory() as folder:
        command, log = server("normal", folder)
        with NoAllowlist(command, allowed=ALLOWED) as client:
            client.initialize()
            client.list_tools()
            client.call_tool("place_purchase", {"flavor": "vanilla", "tubs": 100})
        assert "place_purchase" in [call["name"] for call in calls(log)]
    print("ok   negative control: without the allowlist the server records the purchase")


def claude_cost(usage):
    """List-price cost from token counts, with the Claude client's own price table."""
    prices = EXPERIMENT["CLAUDE"]["PRICES"]
    total = 0.0
    for model, used in usage["usage"].items():
        price_in, price_out, price_write, price_read = prices[model]
        total += (
            used["input_tokens"] * price_in
            + used["output_tokens"] * price_out
            + used["cache_creation_input_tokens"] * price_write
            + used["cache_read_input_tokens"] * price_read
        ) / 1_000_000
    return round(total, 4)


def measured_selection():
    """Both receipts' tables recomputed from their rows, and the BM25 tool search rerun here."""
    evidence = BOOK.parents[1] / "docs/evidence/book-ch14"
    for run in ("", "-claude"):
        name = f"ch14-tool-selection{run}-receipt-v1.json"
        raw = (evidence / name).read_text()
        assert "sk-ant" not in raw and "x-api-key" not in raw, "a receipt must never hold a key"
        receipt = json.loads(raw)
        recompute_selection(receipt)
        if "usage" in receipt:
            usage = receipt["usage"]
            assert usage["costUsd"] == claude_cost(usage) <= usage["ceilingUsd"]
            assert usage["requests"] == len(receipt["rows"])
            spent = usage["costUsd"]
    print(
        "ok   both receipts' tables recomputed from their rows; BM25 tool search reran identically;"
        f" the Claude run cost {spent:.2f} USD at list price"
    )


def recompute_selection(receipt):
    rows = receipt["rows"]
    for entry in receipt["table"]:
        key = (entry["model"], entry["protocol"], entry["offer"])
        picked = [r for r in rows if (r["model"], r["protocol"], r["offer"]) == key]
        right = sum(r["chosen"] == r["expected"] for r in picked)
        low, high = STATS["wilson_interval"](right, len(picked))
        assert (entry["n"], entry["correct"]) == (len(picked), right), key
        assert entry["accuracy"] == round(right / len(picked), 3), key
        assert entry["wilson95"] == [round(low, 3), round(high, 3)], key
        tokens = statistics.median(r["promptTokens"] or 0 for r in picked)
        assert entry["medianPromptTokens"] == tokens, key
    assert len(rows) == sum(entry["n"] for entry in receipt["table"])
    tasks = [(task["request"], task["expected"]) for task in receipt["tasks"]]
    assert tasks == EXPERIMENT["TASKS"]
    catalog64 = EXPERIMENT["catalog"](64, "confusable", 0)
    texts = [MCP["tool_text"](tool) for tool in catalog64]
    found = 0
    for index, (request, expected) in enumerate(tasks):
        scores = LEXICAL["bm25_scores"](request, texts)
        order = sorted(range(64), key=lambda i: (-scores[i], i))
        top = [catalog64[i]["name"] for i in order[:5]]
        assert top == receipt["search"]["offered"][f"bm25:{index}"], index
        found += expected in top
    assert receipt["search"]["recallAt5"]["bm25"] == round(found / len(tasks), 3)


def main():
    framing_and_identity()
    the_protocol_done_right()
    every_failure_the_brief_names()
    cleanup_ends_the_group()
    negative_control()
    measured_selection()


if __name__ == "__main__":
    main()
