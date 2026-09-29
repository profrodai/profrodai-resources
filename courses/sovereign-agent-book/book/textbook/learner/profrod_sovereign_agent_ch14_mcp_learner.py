# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 14 learner file: an external tool over MCP, and the cost of offering many tools.

Part A: a tool offered to a model is text in its prompt. The helpers here turn a tool into that
text, measure how many tools a request should see, and pick them by retrieval (Chapters 5 and 6).

Part B: a bounded client for the Model Context Protocol's stdio transport, pinned to protocol
version 2025-06-18, built from the standard library. Each message is one line of JSON on the
child's stdin or stdout; stderr carries diagnostics and is never read as protocol. The client
matches every response to its request by id, refuses an unsupported version, validates what the
server advertises, calls only tools the application allowed, bounds bytes and time, and ends the
child it started. It is not the finished `sovereign_agent.mcp_client`: you build this one.
"""

from __future__ import annotations

import json
import os
import selectors
import signal
import subprocess
import time
from collections.abc import Callable, Sequence
from types import TracebackType
from typing import Any

PROTOCOL_VERSION = "2025-06-18"


# ---------------------------------------------------------------- Part A: tools are prompt text


def tool_text(tool: dict[str, Any]) -> str:
    """The words a retriever sees for one tool: its name, split on underscores, and description."""
    return f"{tool['name'].replace('_', ' ')}. {tool.get('description', '')}"


def top_tools(
    request: str,
    tools: Sequence[dict[str, Any]],
    score: Callable[[str, Sequence[str]], Sequence[float]],
    m: int,
) -> list[dict[str, Any]]:
    """The m tools whose text scores highest for `request`, best first; ties keep catalog order."""
    scores = score(request, [tool_text(tool) for tool in tools])
    order = sorted(range(len(tools)), key=lambda i: (-scores[i], i))
    return [tools[i] for i in order[:m]]


def as_model_tool(tool: dict[str, Any]) -> dict[str, Any]:
    """An MCP tool description in the function-calling shape a model API expects."""
    return {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool.get("description", ""),
            "parameters": tool.get("inputSchema", {"type": "object", "properties": {}}),
        },
    }


# ---------------------------------------------------------------- Part B: messages and framing


def request_message(request_id: int, method: str, params: dict[str, Any]) -> dict[str, Any]:
    """A JSON-RPC 2.0 request: it carries an id, so exactly one response may answer it."""
    return {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}


def notification_message(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """A notification has no id: the peer must not answer it."""
    message: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        message["params"] = params
    return message


def encode_frame(message: dict[str, Any], limit: int) -> bytes:
    """One message, one line: compact JSON with no raw newline inside, then a newline."""
    raw = json.dumps(message, allow_nan=False, separators=(",", ":")).encode()
    if len(raw) + 1 > limit:
        raise ValueError(f"message of {len(raw) + 1} bytes exceeds the {limit}-byte frame limit")
    return raw + b"\n"


class FrameReader:
    """Collects bytes from a stream and yields whole lines, refusing any line beyond `limit`.

    A newline ends a frame; bytes after it wait for the next call. The limit applies before
    parsing, so an endless line is refused without ever being held whole in memory.
    """

    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.buffer = b""

    def feed(self, chunk: bytes) -> list[bytes]:
        self.buffer += chunk
        lines = []
        while b"\n" in self.buffer:
            line, self.buffer = self.buffer.split(b"\n", 1)
            if len(line) + 1 > self.limit:
                raise ValueError(f"frame exceeds the {self.limit}-byte limit")
            lines.append(line)
        if len(self.buffer) >= self.limit:
            raise ValueError(f"frame exceeds the {self.limit}-byte limit")
        return lines


def parse_frame(line: bytes) -> dict[str, Any]:
    """A frame must be one JSON-RPC 2.0 object; anything else is a protocol error, not a log."""
    try:
        message = json.loads(line)
    except (ValueError, UnicodeDecodeError) as error:
        raise ValueError(f"malformed frame: {line[:60]!r}") from error
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
        raise ValueError("not a JSON-RPC 2.0 message")
    return message


def answer_for(request_id: int, message: dict[str, Any]) -> dict[str, Any] | None:
    """The result `message` gives request `request_id`, or None if it answers nothing we wait for.

    A notification (a method, no id) is skipped. A response for another id is refused: in a
    one-at-a-time client it means the stream is confused, and accepting it would attach one
    request's evidence to another. An error response is raised, never treated as a result.
    """
    if "method" in message and "id" not in message:
        return None
    if type(message.get("id")) is not int or message["id"] != request_id:
        raise ValueError(f"response id {message.get('id')!r} does not answer request {request_id}")
    if "error" in message:
        error = message["error"]
        raise RuntimeError(f"server error {error.get('code')}: {error.get('message')}")
    result = message.get("result")
    if not isinstance(result, dict):
        raise ValueError("response carries no result object")
    return result


# ---------------------------------------------------------------- Part B: handshake and discovery


def check_initialize(result: dict[str, Any], version: str = PROTOCOL_VERSION) -> dict[str, Any]:
    """The server must agree on our pinned version and offer tools, or we stop before discovery."""
    if result.get("protocolVersion") != version:
        raise ValueError(f"server speaks {result.get('protocolVersion')!r}, not {version}")
    capabilities = result.get("capabilities")
    if not isinstance(capabilities, dict) or "tools" not in capabilities:
        raise ValueError("server does not offer tools")
    return capabilities


def check_tools(result: dict[str, Any], limit: int = 32) -> dict[str, dict[str, Any]]:
    """Discovery, validated: a bounded, unpaginated list of uniquely named tools with object
    schemas. Advertising a tool describes it; it grants nothing."""
    if result.get("nextCursor"):
        raise ValueError("paginated tool lists are outside this client's bounds")
    tools = result.get("tools")
    if not isinstance(tools, list) or len(tools) > limit:
        raise ValueError(f"tool list missing or longer than {limit}")
    catalog: dict[str, dict[str, Any]] = {}
    for tool in tools:
        name = tool.get("name") if isinstance(tool, dict) else None
        if not isinstance(name, str) or not name or name in catalog:
            raise ValueError(f"invalid or duplicate tool name {name!r}")
        schema = tool.get("inputSchema")
        if not isinstance(schema, dict) or schema.get("type") != "object":
            raise ValueError(f"tool {name!r} lacks an object input schema")
        catalog[name] = tool
    return catalog


def result_text(result: dict[str, Any]) -> str:
    """A tool result's text blocks, joined. A result flagged isError is a failed call."""
    blocks = result.get("content")
    if not isinstance(blocks, list):
        raise ValueError("tool result has no content list")
    text = "\n".join(
        block["text"] for block in blocks if isinstance(block, dict) and block.get("type") == "text"
    )
    if result.get("isError"):
        raise RuntimeError(f"tool reported an error: {text}")
    return text


# ---------------------------------------------------------------- Part B: the bounded client


class StdioClient:
    """One operator-configured server process, spoken to one request at a time.

    Every operation shares a single deadline across its writes and reads, so a server that
    trickles one byte before each timeout cannot stretch it. The allowlist is the application's
    decision and is checked before any call is sent.
    """

    def __init__(
        self,
        command: Sequence[str],
        *,
        allowed: frozenset[str],
        timeout: float = 5.0,
        frame_limit: int = 65_536,
        environment: dict[str, str] | None = None,
    ) -> None:
        if not command or not 0 < timeout <= 60:
            raise ValueError("an explicit server command and a bounded timeout are required")
        self.allowed, self.timeout, self.frame_limit = allowed, timeout, frame_limit
        self.reader = FrameReader(frame_limit)
        self.pending: list[bytes] = []  # whole frames read but not yet consumed
        self.next_id = 0
        self.catalog: dict[str, dict[str, Any]] = {}
        self.process = subprocess.Popen(
            list(command),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,  # diagnostics are the server's, never protocol
            env=environment if environment is not None else {"PATH": os.environ.get("PATH", "")},
            start_new_session=True,  # its own process group, so close() can end its children
        )
        assert self.process.stdin and self.process.stdout
        # Non-blocking both ways: every wait goes through a selector with the deadline.
        os.set_blocking(self.process.stdin.fileno(), False)
        os.set_blocking(self.process.stdout.fileno(), False)

    def _write(self, frame: bytes, deadline: float) -> None:
        assert self.process.stdin
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdin, selectors.EVENT_WRITE)
            while frame:
                if not selector.select(max(0.0, deadline - time.monotonic())):
                    raise TimeoutError("write deadline passed")
                written = os.write(self.process.stdin.fileno(), frame)
                frame = frame[written:]

    def _read(self, deadline: float) -> dict[str, Any]:
        assert self.process.stdout
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdout, selectors.EVENT_READ)
            while True:
                if self.pending:
                    return parse_frame(self.pending.pop(0))
                if not selector.select(max(0.0, deadline - time.monotonic())):
                    raise TimeoutError("response deadline passed")
                chunk = os.read(self.process.stdout.fileno(), 4096)
                if not chunk:
                    raise EOFError("server closed its output")
                self.pending.extend(self.reader.feed(chunk))

    def request(
        self, method: str, params: dict[str, Any], notifications: int = 16
    ) -> dict[str, Any]:
        """Send one request and return its result; at most `notifications` may arrive first."""
        self.next_id += 1
        deadline = time.monotonic() + self.timeout
        self._write(
            encode_frame(request_message(self.next_id, method, params), self.frame_limit), deadline
        )
        for _ in range(notifications + 1):
            result = answer_for(self.next_id, self._read(deadline))
            if result is not None:
                return result
        raise ValueError("too many notifications before the response")

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        deadline = time.monotonic() + self.timeout
        self._write(encode_frame(notification_message(method, params), self.frame_limit), deadline)

    def initialize(self) -> dict[str, Any]:
        """Agree on the version and capabilities; nothing else may happen before this succeeds."""
        result = self.request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "lucy-learner", "version": "1"},
            },
        )
        check_initialize(result)
        self.notify("notifications/initialized")
        return result

    def list_tools(self) -> dict[str, dict[str, Any]]:
        self.catalog = check_tools(self.request("tools/list", {}))
        return self.catalog

    def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Call a tool the server advertised AND the application allowed; return its text."""
        if name not in self.allowed:
            raise PermissionError(f"{name!r} is not allowed by this application")
        if name not in self.catalog:
            raise PermissionError(f"{name!r} was not advertised by this server")
        return result_text(self.request("tools/call", {"name": name, "arguments": arguments}))

    def close(self, grace: float = 1.0) -> int | None:
        """The stdio shutdown MCP describes: close the server's input and give it `grace` seconds
        to exit; then end its whole process group, first with SIGTERM and then with SIGKILL, so
        neither a hung server nor a grandchild it started outlives the client. Returns the
        server's exit status: 0 for a clean exit, a negative signal number otherwise."""
        if self.process.stdin:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=grace)
        except subprocess.TimeoutExpired:
            pass
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(self.process.pid, sig)
            except (ProcessLookupError, PermissionError):
                break  # the group is gone (macOS says EPERM for an exited, unreaped leader)
            time.sleep(0.05 if sig == signal.SIGTERM else 0)
        status = self.process.wait(timeout=5)
        if self.process.stdout:
            self.process.stdout.close()
        return status

    def __enter__(self) -> StdioClient:
        return self

    def __exit__(
        self,
        kind: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
