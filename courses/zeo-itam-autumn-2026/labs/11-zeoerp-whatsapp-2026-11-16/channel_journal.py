"""Persist channel attempts before starting a turn or sending a reply.

This journal is downstream of authenticated message retrieval. It does not
authenticate a transport, validate a phone number, or implement ERP orders.
An interrupted attempt stays held until its original result is reconciled.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


class BindingConflict(ValueError):
    """An operation ID was reused with different input or customer binding."""


class StaleAttempt(ValueError):
    """A caller cannot complete an attempt it did not claim."""


@dataclass(frozen=True)
class Claim:
    state: Literal["START", "HELD", "DONE", "SKIPPED"]
    ticket: str | None = None
    result_ref: str | None = None


@dataclass(frozen=True)
class HeldAttempt:
    operation: str
    ticket: str


class ChannelJournal:
    """One persistent journal shared by inbound polling and reply dispatch.

    Scope separates the granted account and sandbox number. Operation IDs are
    channel-controlled: for example, the inbound MessageSid and a reply ordinal.
    Never accept identity, IDs, or scope from model-generated tool arguments.
    Only opaque result references are stored; message bodies and phone numbers
    are hashed as part of the binding, rather than written to the journal.
    """

    def __init__(self, path: str | Path) -> None:
        path = Path(path)
        if str(path) == ":memory:":
            raise ValueError("Use a persistent file for restart-safe replay handling")
        # Exclusive creation gives a new private journal mode 0600. An existing
        # journal is preserved: do not truncate it or reset state on restart.
        try:
            import os

            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            pass
        else:
            os.close(fd)
        self.db = sqlite3.connect(path, timeout=5, isolation_level=None)
        self.db.execute("PRAGMA busy_timeout = 5000")
        self.db.execute("PRAGMA synchronous = FULL")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS attempts ("
            "scope TEXT NOT NULL, operation TEXT NOT NULL, binding TEXT NOT NULL, "
            "phase TEXT NOT NULL CHECK (phase IN ('IN_FLIGHT','UNKNOWN','DONE')), "
            "ticket TEXT NOT NULL, result_ref TEXT, PRIMARY KEY (scope, operation))"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS poll_cursors (scope TEXT NOT NULL, stream TEXT NOT NULL, "
            "date_sent TEXT NOT NULL, sid TEXT NOT NULL, PRIMARY KEY(scope, stream))"
        )

    def close(self) -> None:
        self.db.close()

    def claim(self, scope: str, operation: str, *, binding: dict[str, str]) -> Claim:
        """Atomically admit one attempt; retries never authorize a second call.

        Binding must include all trusted identity and semantic input relevant to
        this operation, including the verified MessageSid. The caller must not
        silently change or omit that binding on a retry.
        """
        if not scope or not operation or not binding:
            raise ValueError("scope, operation, and trusted binding are required")
        if any(not isinstance(k, str) or not isinstance(v, str) for k, v in binding.items()):
            raise ValueError("binding must contain string keys and values")
        digest = hashlib.sha256(
            json.dumps(binding, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                "SELECT binding, phase, result_ref FROM attempts WHERE scope=? AND operation=?",
                (scope, operation),
            ).fetchone()
            if row is not None:
                if row[0] != digest:
                    raise BindingConflict("operation reused with a different binding")
                if row[1] == "DONE":
                    state = "SKIPPED" if row[2].startswith("SKIPPED:") else "DONE"
                    result = Claim(state, result_ref=row[2])
                else:
                    result = Claim("HELD")
            else:
                ticket = secrets.token_hex(24)
                self.db.execute(
                    "INSERT INTO attempts VALUES (?, ?, ?, 'IN_FLIGHT', ?, NULL)",
                    (scope, operation, digest, ticket),
                )
                result = Claim("START", ticket=ticket)
            self.db.execute("COMMIT")
            return result
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def uncertain(self, scope: str, operation: str, ticket: str) -> None:
        """Hold an unknown outcome. This never resets the attempt for retry."""
        self._change(scope, operation, ticket, "UNKNOWN", None, ("IN_FLIGHT",))

    def skip(self, scope: str, operation: str, ticket: str, reason: str) -> None:
        if reason not in {"wrong_binding", "unlisted_sender", "media", "empty_text", "outside_window"}:
            raise ValueError("Unknown skip reason")
        self.complete(scope, operation, ticket, "SKIPPED:" + reason)

    def cursor(self, scope: str, stream: str) -> tuple[str, str] | None:
        return self.db.execute(
            "SELECT date_sent, sid FROM poll_cursors WHERE scope=? AND stream=?", (scope, stream)
        ).fetchone()

    def save_cursor(self, scope: str, stream: str, date_sent: str, sid: str) -> None:
        # The caller normalizes date_sent to fixed-width UTC. Never regress a
        # saved watermark if another poller has already advanced it.
        self.db.execute(
            "INSERT INTO poll_cursors VALUES (?, ?, ?, ?) ON CONFLICT(scope,stream) DO UPDATE "
            "SET date_sent=excluded.date_sent,sid=excluded.sid WHERE "
            "excluded.date_sent>poll_cursors.date_sent OR "
            "(excluded.date_sent=poll_cursors.date_sent AND excluded.sid>poll_cursors.sid)",
            (scope, stream, date_sent, sid),
        )

    def held(self, scope: str, *, limit: int = 100) -> list[HeldAttempt]:
        """Recover original handles for trusted result lookup after a restart.

        These handles are for the transport owner, never the model or classroom
        display. Retrieving a handle does not permit dispatch or resend.
        """
        if not scope or type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("scope and a limit from 1 to 100 are required")
        return [
            HeldAttempt(*row)
            for row in self.db.execute(
                "SELECT operation, ticket FROM attempts "
                "WHERE scope=? AND phase IN ('IN_FLIGHT','UNKNOWN') "
                "ORDER BY rowid LIMIT ?",
                (scope, limit),
            )
        ]

    def complete(self, scope: str, operation: str, ticket: str, result_ref: str) -> None:
        """Record the original result after dispatch or authoritative lookup.

        The transport-owning caller must verify the lookup result refers to this
        exact operation. A model response or local timeout is not such a result.
        """
        if not result_ref or not isinstance(result_ref, str):
            raise ValueError("a nonempty opaque result reference is required")
        self._change(scope, operation, ticket, "DONE", result_ref, ("IN_FLIGHT", "UNKNOWN"))

    def _change(
        self,
        scope: str,
        operation: str,
        ticket: str,
        phase: str,
        result_ref: str | None,
        allowed: tuple[str, ...],
    ) -> None:
        placeholders = ",".join("?" for _ in allowed)
        cursor = self.db.execute(
            "UPDATE attempts SET phase=?, result_ref=? "
            "WHERE scope=? AND operation=? AND ticket=? "
            f"AND phase IN ({placeholders})",
            (phase, result_ref, scope, operation, ticket, *allowed),
        )
        if cursor.rowcount != 1:
            raise StaleAttempt("attempt is not owned or is already terminal")
