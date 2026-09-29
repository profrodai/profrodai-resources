# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 11's supplier: a separate process with its own SQLite ledger, and a client for it.

Run as a script, this file is the supplier. It listens on loopback only and keeps every order it
accepts, keyed by the operation identity the agent sends:

    python profrod_sovereign_agent_ch11_supplier_learner.py --database s.sqlite --ready port.txt

Imported, it gives the agent a client whose requests go through Chapter 3's killable transport.
The same operation sent twice gets the same receipt back, so a retry cannot buy twice. It cannot
purchase real stock.
"""

import argparse
import json
import re
import runpy
import sqlite3
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit

FIELDS = {"sku": str, "quantity": int, "unit_cost_cents": int, "supplier": str, "currency": str}
OPERATION = re.compile(r"/orders/([a-f0-9]{32})")


def valid_proposal(proposal) -> bool:
    """Exactly the fields of an order, with the right types and bounds; nothing else."""
    return (
        isinstance(proposal, dict)
        and set(proposal) == set(FIELDS)
        and all(type(proposal[name]) is kind for name, kind in FIELDS.items())
        and 0 < proposal["quantity"] <= 1000
        and 0 < proposal["unit_cost_cents"] <= 100_000
        and proposal["supplier"] == "lucy-local"
        and proposal["currency"] == "USD"
    )


def serve(path: Path, port: int, ready: Path | None = None) -> None:
    ledger = sqlite3.connect(path)
    ledger.execute("PRAGMA journal_mode=WAL")
    ledger.execute(
        "CREATE TABLE IF NOT EXISTS orders("
        "operation TEXT PRIMARY KEY, proposal TEXT NOT NULL, receipt TEXT NOT NULL)"
    )
    ledger.commit()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass  # a teaching supplier logs nothing about its callers

        def reply(self, code, data):
            raw = json.dumps(data).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def operation(self):
            match = OPERATION.fullmatch(self.path)
            return match[1] if match else None

        def do_GET(self):  # noqa: N802
            row = ledger.execute(
                "SELECT receipt FROM orders WHERE operation=?", (self.operation(),)
            ).fetchone()
            self.reply(200, json.loads(row[0])) if row else self.reply(404, {"error": "none"})

        def do_POST(self):  # noqa: N802
            operation = self.operation()
            length = int(self.headers.get("Content-Length", "0"))
            try:
                proposal = json.loads(self.rfile.read(length)) if 0 < length <= 4096 else None
            except ValueError:
                proposal = None
            if operation is None or not valid_proposal(proposal):
                self.reply(400, {"error": "invalid order"})
                return
            encoded = json.dumps(proposal, sort_keys=True)
            row = ledger.execute(
                "SELECT proposal, receipt FROM orders WHERE operation=?", (operation,)
            ).fetchone()
            if row:
                # The same operation again: the same receipt. Different content: refused.
                if row[0] == encoded:
                    self.reply(200, json.loads(row[1]))
                else:
                    self.reply(409, {"error": "operation reused for another order"})
                return
            receipt = {"operation": operation, "proposal": proposal, "status": "ACCEPTED"}
            with ledger:
                ledger.execute(
                    "INSERT INTO orders VALUES (?,?,?)", (operation, encoded, json.dumps(receipt))
                )
            self.reply(200, receipt)

    server = HTTPServer(("127.0.0.1", port), Handler)
    if ready:
        ready.write_text(str(server.server_port))
    try:
        server.serve_forever()
    finally:
        server.server_close()
        ledger.close()


TRANSPORT = runpy.run_path(
    str(Path(__file__).with_name("profrod_sovereign_agent_ch03_http_transport_learner.py"))
)


class SupplierClient:
    """The agent's side: look up an operation, or place it. Idempotent by operation identity."""

    idempotent = True

    def __init__(self, endpoint: str, *, timeout: float = 3):
        parsed = urlsplit(endpoint)
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"}:
            raise ValueError("the teaching supplier is loopback HTTP only")
        self.endpoint, self.timeout = endpoint.rstrip("/"), timeout

    @property
    def identity(self) -> str:
        """The destination an approval binds: moving the endpoint changes the approved effect."""
        return "lucy-local@" + self.endpoint

    def _call(self, operation: str, proposal: dict | None = None) -> dict | None:
        if not re.fullmatch("[a-f0-9]{32}", operation):
            raise ValueError("invalid operation identity")
        response = TRANSPORT["request"](
            f"{self.endpoint}/orders/{operation}",
            data=None if proposal is None else json.dumps(proposal).encode(),
            headers={"Content-Type": "application/json"},
            timeout=self.timeout,
            maximum_bytes=16_384,
        )
        if proposal is None and response.status == 404:
            return None
        if response.status != 200:
            raise OSError(f"supplier answered {response.status}")
        receipt = json.loads(response.body)
        if not isinstance(receipt, dict):
            raise ValueError("invalid supplier receipt")
        return receipt

    def lookup(self, operation: str) -> dict | None:
        return self._call(operation)

    def order(self, operation: str, proposal: dict) -> dict:
        return self._call(operation, proposal)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--ready", type=Path)
    args = parser.parse_args()
    serve(args.database, args.port, args.ready)


if __name__ == "__main__":
    sys.exit(main())
