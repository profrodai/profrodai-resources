# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""A standard-library client for the Claude Messages API, used by the chapters' experiments.

The key comes from ANTHROPIC_API_KEY in the environment, else from the `.env` file named by
ANTHROPIC_ENV_FILE, else from the course folder's `.env`, which git ignores. It is never
printed, logged or written to a receipt. Every request is counted against a spending ceiling,
and every experiment records the tokens and the list-price cost it used, so a Claude run is as
inspectable as a local one.

Prices, model ids and request settings are from platform.claude.com, read on 2026-09-29: the
pricing page, the models overview and the thinking page.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
VERSION = "2023-06-01"
COURSE = Path(__file__).resolve().parents[3]

# model id: (input, output, cache write 5 min, cache read), USD per million tokens
PRICES = {
    "claude-haiku-4-5-20251001": (1.00, 5.00, 1.25, 0.10),
    "claude-sonnet-5-5": (2.00, 10.00, 2.50, 0.20),
    "claude-opus-5-5": (4.00, 20.00, 5.00, 0.20),
}
# What each model accepts for a short, direct answer. Haiku 4.5 thinks only when asked and takes
# temperature 0. Sonnet 5.5 rejects any temperature and thinks by default; "between_tools" turns
# up-front thinking off. Opus 5.5 always thinks, so its thinking tokens are billed as output.
SETTINGS = {
    "claude-haiku-4-5-20251001": {"temperature": 0},
    "claude-sonnet-5-5": {"thinking": {"type": "between_tools"}},
    "claude-opus-5-5": {},
}
WINDOW = {
    "claude-haiku-4-5-20251001": 200_000,
    "claude-sonnet-5-5": 1_000_000,
    "claude-opus-5-5": 1_000_000,
}


class BudgetExceededError(Exception):
    """The run reached its spending ceiling; no further request is sent."""


def api_key() -> str:
    """ANTHROPIC_API_KEY from the environment, else from ANTHROPIC_ENV_FILE's file, else from the
    course folder's .env file. The value is returned, never printed."""
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        env = Path(os.environ.get("ANTHROPIC_ENV_FILE") or COURSE / ".env").expanduser()
        if env.is_file():
            for line in env.read_text().splitlines():
                name, _, value = line.strip().partition("=")
                if name == "ANTHROPIC_API_KEY":
                    key = value.strip().strip('"').strip("'")
    if not key:
        raise RuntimeError(
            "No Claude key: set ANTHROPIC_API_KEY or add it to the course folder's .env file"
        )
    return key


class Claude:
    """One experiment's connection: requests, retries, token accounting and a spending ceiling."""

    def __init__(self, max_usd: float, timeout: float = 300.0):
        self.max_usd, self.timeout = max_usd, timeout
        self.usage: dict[str, dict[str, int]] = {}
        self.requests = 0
        self._key = api_key()

    def cost(self) -> float:
        total = 0.0
        for model, used in self.usage.items():
            price_in, price_out, price_write, price_read = PRICES[model]
            total += (
                used["input_tokens"] * price_in
                + used["output_tokens"] * price_out
                + used["cache_creation_input_tokens"] * price_write
                + used["cache_read_input_tokens"] * price_read
            ) / 1_000_000
        return total

    def report(self) -> dict:
        """What a receipt records: the models, tokens, requests and cost. Never the key."""
        return {
            "provider": "anthropic",
            "requests": self.requests,
            "usage": self.usage,
            "costUsd": round(self.cost(), 4),
            "prices": "USD per million tokens, platform.claude.com pricing page, 2026-09-29",
            "settings": {model: SETTINGS[model] for model in self.usage},
            "ceilingUsd": self.max_usd,
        }

    def _post(self, path: str, payload: dict) -> dict:
        body = json.dumps(payload).encode()
        headers = {
            "content-type": "application/json",
            "anthropic-version": VERSION,
            "x-api-key": self._key,
        }
        for attempt in range(8):
            try:
                with urlopen(
                    Request(f"{API}{path}", data=body, headers=headers),
                    timeout=self.timeout,
                ) as response:
                    return json.loads(response.read())
            except HTTPError as error:
                if error.code not in (408, 429, 500, 502, 503, 504, 529) or attempt == 7:
                    detail = error.read().decode(errors="replace")[:300]
                    raise RuntimeError(f"Claude API {error.code}: {detail}") from None
                wait = float(error.headers.get("retry-after") or 2**attempt)
            except (URLError, TimeoutError):
                if attempt == 7:
                    raise
                wait = 2**attempt
            time.sleep(min(wait, 60))
        raise RuntimeError("unreachable")

    def messages(self, model: str, **request) -> dict:
        """POST /v1/messages; counts the usage and refuses to start past the ceiling."""
        if model not in PRICES:
            raise ValueError(f"no price recorded for {model}")
        if self.cost() >= self.max_usd:
            raise BudgetExceededError(f"spent {self.cost():.2f} of {self.max_usd:.2f} USD")
        reply = self._post("/v1/messages", {"model": model, **SETTINGS[model], **request})
        self.requests += 1
        used = self.usage.setdefault(
            model,
            {
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0,
            },
        )
        for field, value in reply.get("usage", {}).items():
            if field in used and isinstance(value, int):
                used[field] += value
        return reply

    def count_tokens(self, model: str, **request) -> int:
        """The model's own token count for a request (the counting endpoint is free)."""
        return self._post("/v1/messages/count_tokens", {"model": model, **request})["input_tokens"]


def to_claude(messages: list[dict]) -> tuple[str, list[dict]]:
    """A chat transcript as the Messages API takes it: system text apart, tool results as user
    text, and turns of the same role joined, since the API alternates user and assistant."""
    system, turns = [], []
    for message in messages:
        role, content = message["role"], message["content"]
        if role == "system":
            system.append(content)
            continue
        if role == "tool":
            role, content = "user", f"[{message.get('name', 'tool')} result] {content}"
        if turns and turns[-1]["role"] == role:
            turns[-1]["content"] += "\n\n" + content
        else:
            turns.append({"role": role, "content": content})
    return "\n\n".join(system), turns


def text_of(reply: dict) -> str:
    return "".join(block.get("text", "") for block in reply.get("content", []))


def tool_calls(reply: dict) -> list[dict]:
    return [block for block in reply.get("content", []) if block.get("type") == "tool_use"]


def as_claude_tool(schema: dict) -> dict:
    """A function-calling tool schema, as Chapter 2 builds them, in the Messages API's shape."""
    function = schema["function"]
    return {
        "name": function["name"],
        "description": function.get("description", ""),
        "input_schema": function.get("parameters", {"type": "object", "properties": {}}),
    }


def loop_transcript(messages: list[dict]) -> tuple[str, list[dict]]:
    """Chapter 3's transcript in the Messages API's shape: tool calls become tool_use blocks, and
    tool observations become tool_result blocks in the next user turn."""
    system, turns = [], []

    def add(role: str, blocks: list[dict]) -> None:
        if turns and turns[-1]["role"] == role:
            turns[-1]["content"].extend(blocks)
        else:
            turns.append({"role": role, "content": blocks})

    for message in messages:
        role, content = message["role"], message.get("content") or ""
        if role == "system":
            system.append(content)
        elif role == "tool":
            result = {"type": "tool_result", "tool_use_id": message["tool_call_id"]}
            add("user", [{**result, "content": content}])
        elif role == "assistant":
            blocks = [{"type": "text", "text": content}] if content.strip() else []
            for call in message.get("tool_calls", []):
                function = call["function"]
                blocks.append(
                    {
                        "type": "tool_use",
                        "id": call["id"],
                        "name": function["name"],
                        "input": json.loads(function["arguments"]),
                    }
                )
            add("assistant", blocks)
        else:
            add("user", [{"type": "text", "text": content}])
    return "\n\n".join(system), turns


class LoopModel:
    """Claude behind Chapter 3's model interface: complete() returns the learner's ModelTurn."""

    def __init__(self, client: Claude, model: str, turn, call, **request):
        self.client, self.model, self.turn, self.call = client, model, turn, call
        self.request = request

    def complete(self, messages, tools, *, timeout, max_output_tokens):
        system, turns = loop_transcript(messages)
        extra = dict(self.request)
        if system:
            extra["system"] = system
        reply = self.client.messages(
            self.model,
            max_tokens=max_output_tokens,
            messages=turns,
            tools=[as_claude_tool(tool) for tool in tools],
            **extra,
        )
        calls = tuple(
            self.call(id=block["id"], name=block["name"], arguments=block["input"])
            for block in tool_calls(reply)
        )
        return self.turn(text_of(reply), calls, reply.get("usage", {}).get("output_tokens", 0))
