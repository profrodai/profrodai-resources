# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 12 learner file: what retries do to an effect whose reply can be lost.

A request to another system can be lost before the system acts, or after it acts but before its
reply arrives. The caller cannot tell the two apart. This file computes, with the standard library
only, how many attempts and how many duplicate effects a "retry until a reply arrives" policy
makes, how a timeout turns slow successes into lost replies, and the stable operation key that
lets the receiving system recognize a retry. Chapter 12 derives each and measures them.

It also holds Part B's fault: a proxy between Lucy's agent and the Chapter 11 supplier that loses
the reply to each operation's first order after the supplier has committed it. The fault sits in
the network, where a lost reply happens, so the supplier and the agent stay the learner's own.
"""

from __future__ import annotations

import hashlib
import json
import math
import threading
import uuid
from collections.abc import Sequence
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def expected_attempts(lost_before: float, lost_after: float) -> float:
    """Mean attempts until a reply arrives, when each attempt independently loses its request
    with probability a or its reply with probability b: a geometric count, 1 / (1 - a - b)."""
    if lost_before < 0 or lost_after < 0 or lost_before + lost_after >= 1:
        raise ValueError("need a, b >= 0 and a + b < 1")
    return 1 / (1 - lost_before - lost_after)


def expected_duplicates(lost_before: float, lost_after: float) -> float:
    """Mean extra effects per intended effect when every retry is a new request: b / (1 - a - b).

    Each failed attempt is a lost reply with probability b / (a + b), and there are (a + b) / s
    failed attempts on average, where s = 1 - a - b; every lost reply was an effect."""
    return lost_after * expected_attempts(lost_before, lost_after)


def capped_attempts(timeout_share: float, attempts: int) -> float:
    """Mean attempts when each one times out with probability p, independently, and the caller
    stops after `attempts`: 1 + p + p^2 + ... + p^(attempts - 1)."""
    if not 0 <= timeout_share <= 1 or attempts < 1:
        raise ValueError("need 0 <= p <= 1 and at least one attempt")
    return sum(timeout_share**j for j in range(attempts))


def percentile(values: Sequence[float], q: float) -> float:
    """Nearest-rank percentile: the smallest value with at least q percent of values at or below."""
    ordered = sorted(values)
    return ordered[max(1, math.ceil(q / 100 * len(ordered))) - 1]


def timed_out_share(latencies: Sequence[float], timeout: float) -> float:
    """Share of calls a caller waiting `timeout` seconds would abandon: P(latency > timeout)."""
    return sum(latency > timeout for latency in latencies) / len(latencies)


def operation_key(work_id: str, target: str, proposal: dict[str, object]) -> str:
    """A stable identity for one intended effect: the same work, destination and exact proposal
    always give the same key, however many times the request is sent."""
    encoded = json.dumps(proposal, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256((target + "\n" + encoded).encode()).hexdigest()
    return uuid.uuid5(uuid.NAMESPACE_URL, work_id + ":" + digest).hex


class ReplyLosingProxy:
    """Forward every request to the supplier, and lose the reply to each operation's first
    order once the supplier has answered it: the order is committed, and the agent hears nothing.
    Lookups and repeated orders pass through untouched."""

    def __init__(self, upstream: str) -> None:
        self.upstream = upstream.rstrip("/")
        self.lost: list[str] = []
        proxy = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass

            def forward(self, data):
                request = Request(
                    proxy.upstream + self.path,
                    data=data,
                    headers={"Content-Type": "application/json"},
                    method=self.command,
                )
                try:
                    with urlopen(request, timeout=10) as response:
                        return response.status, response.read()
                except HTTPError as error:
                    return error.code, error.read()

            def answer(self, status, body):
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):  # noqa: N802
                self.answer(*self.forward(None))

            def do_POST(self):  # noqa: N802
                data = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                status, body = self.forward(data)
                if status == 200 and self.path not in proxy.lost:
                    proxy.lost.append(self.path)
                    self.close_connection = True  # committed upstream; the reply never arrives
                    return
                self.answer(status, body)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    @property
    def endpoint(self) -> str:
        return f"http://127.0.0.1:{self.server.server_port}"

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
