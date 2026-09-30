# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 19's supplier: Chapter 11's, plus an account epoch and a complete receipt export.

    python profrod_sovereign_agent_ch19_supplier_learner.py --database s.sqlite --ready port.txt

Recovering a restored agent needs two things from the supplier that Chapter 11 did not. The first
is a write fence: an account epoch that every order must carry, which the recovering operator
rotates, so an agent process still running with the old epoch can no longer buy. The second is
discovery: every receipt the account holds, so accepted orders the restored snapshot forgot can be
found. A real supplier authenticates who may rotate the epoch; this loopback teaching supplier
does not, and cannot purchase real stock.
"""

import argparse
import json
import re
import runpy
import sqlite3
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

CHAPTER11 = runpy.run_path(
    str(Path(__file__).with_name("profrod_sovereign_agent_ch11_supplier_learner.py"))
)
TRANSPORT = CHAPTER11["TRANSPORT"]
EPOCH = re.compile(r"[a-f0-9]{32}")


def serve(path: Path, port: int, ready: Path | None = None) -> None:
    ledger = sqlite3.connect(path)
    ledger.execute("PRAGMA journal_mode=WAL")
    ledger.execute(
        "CREATE TABLE IF NOT EXISTS orders("
        "operation TEXT PRIMARY KEY, proposal TEXT NOT NULL, receipt TEXT NOT NULL)"
    )
    # One account. The epoch starts unset; the agent registers it once, and only a rotation to
    # a new epoch changes it afterwards.
    ledger.execute(
        "CREATE TABLE IF NOT EXISTS account(id INTEGER PRIMARY KEY CHECK (id = 1), epoch TEXT)"
    )
    ledger.execute("INSERT OR IGNORE INTO account VALUES (1, NULL)")
    ledger.commit()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def reply(self, code, data):
            raw = json.dumps(data).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def body(self):
            length = int(self.headers.get("Content-Length", "0"))
            try:
                return json.loads(self.rfile.read(length)) if 0 < length <= 4096 else None
            except ValueError:
                return None

        def do_GET(self):  # noqa: N802
            if self.path == "/orders":
                receipts = [
                    json.loads(row[0])
                    for row in ledger.execute("SELECT receipt FROM orders ORDER BY operation")
                ]
                self.reply(200, {"receipts": receipts})
                return
            match = CHAPTER11["OPERATION"].fullmatch(self.path)
            row = (
                match
                and ledger.execute(
                    "SELECT receipt FROM orders WHERE operation=?", (match[1],)
                ).fetchone()
            )
            self.reply(200, json.loads(row[0])) if row else self.reply(404, {"error": "none"})

        def do_POST(self):  # noqa: N802
            if self.path == "/account/epoch":
                request = self.body()
                epoch = request.get("epoch") if isinstance(request, dict) else None
                if not isinstance(epoch, str) or not EPOCH.fullmatch(epoch):
                    self.reply(400, {"error": "invalid epoch"})
                    return
                with ledger:
                    ledger.execute("UPDATE account SET epoch=? WHERE id=1", (epoch,))
                self.reply(200, {"epoch": epoch})
                return
            match = CHAPTER11["OPERATION"].fullmatch(self.path)
            proposal = self.body()
            if match is None or not CHAPTER11["valid_proposal"](proposal):
                self.reply(400, {"error": "invalid order"})
                return
            (current,) = ledger.execute("SELECT epoch FROM account WHERE id=1").fetchone()
            if current is None or self.headers.get("X-Account-Epoch") != current:
                self.reply(409, {"error": "account epoch is not current"})
                return
            operation, encoded = match[1], json.dumps(proposal, sort_keys=True)
            row = ledger.execute(
                "SELECT proposal, receipt FROM orders WHERE operation=?", (operation,)
            ).fetchone()
            if row:
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


class EpochClient(CHAPTER11["SupplierClient"]):
    """Chapter 11's client, sending the account epoch with every order."""

    def __init__(self, endpoint: str, epoch: str, *, timeout: float = 3):
        super().__init__(endpoint, timeout=timeout)
        if not EPOCH.fullmatch(epoch):
            raise ValueError("invalid account epoch")
        self.epoch = epoch

    def _call(self, operation: str, proposal: dict | None = None) -> dict | None:
        if not re.fullmatch("[a-f0-9]{32}", operation):
            raise ValueError("invalid operation identity")
        response = TRANSPORT["request"](
            f"{self.endpoint}/orders/{operation}",
            data=None if proposal is None else json.dumps(proposal).encode(),
            headers={"Content-Type": "application/json", "X-Account-Epoch": self.epoch},
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

    def set_epoch(self, epoch: str) -> None:
        """Register or rotate the account's epoch; this client then uses it."""
        response = TRANSPORT["request"](
            f"{self.endpoint}/account/epoch",
            data=json.dumps({"epoch": epoch}).encode(),
            headers={"Content-Type": "application/json"},
            timeout=self.timeout,
            maximum_bytes=4096,
        )
        if response.status != 200 or json.loads(response.body).get("epoch") != epoch:
            raise OSError("supplier did not confirm the account epoch")
        self.epoch = epoch

    def receipts(self) -> list[dict]:
        """Every receipt the account holds: discovery that does not depend on local records."""
        response = TRANSPORT["request"](
            f"{self.endpoint}/orders", timeout=self.timeout, maximum_bytes=1_048_576
        )
        if response.status != 200:
            raise OSError(f"supplier answered {response.status}")
        receipts = json.loads(response.body).get("receipts")
        if not isinstance(receipts, list) or not all(isinstance(r, dict) for r in receipts):
            raise ValueError("invalid receipt export")
        return receipts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--ready", type=Path)
    args = parser.parse_args()
    serve(args.database, args.port, args.ready)


if __name__ == "__main__":
    sys.exit(main())
