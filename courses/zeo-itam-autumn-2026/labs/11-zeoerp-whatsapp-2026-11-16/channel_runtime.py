"""Polling and reply policy behind an authenticated messaging transport.

The ports below are internal Python interfaces, not a claim about an installed
HTTP operation. The host supplies the admitted ZEOconnect transport. Tests use
fakes; this module never loads provider credentials or opens a network socket.
"""

from __future__ import annotations

import asyncio
import contextvars
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable, Protocol

from channel_journal import ChannelJournal


class HeldOutcome(RuntimeError):
    """The original operation needs reconciliation; do not dispatch again."""


@dataclass(frozen=True)
class IncomingMessage:
    connection_id: str
    recipient: str
    sender: str
    message_sid: str
    execution_id: str
    text: str
    sent_at: datetime
    num_media: int = 0


@dataclass(frozen=True, order=True)
class PollCursor:
    date_sent: datetime
    sid: str


@dataclass(frozen=True)
class IncomingPage:
    messages: tuple[IncomingMessage, ...]
    next_after: PollCursor | None
    complete: bool


@dataclass(frozen=True)
class InboundObservationRefusal:
    """Normalized metadata from the admitted transport, never an empty page."""

    disposition: str
    code: str
    reason: str


@dataclass(frozen=True)
class SendResult:
    """Effect disposition and digest; a digest is never a provider message ID."""
    state: str
    result_digest: str | None = None


@dataclass(frozen=True)
class OutboundObservation:
    recipient: str
    message_sid: str
    status: str


def confirmed_send_sid(result: SendResult, candidates: list[OutboundObservation], *, recipient: str) -> str:
    """Match a confirmed receipt's immutable SID digest, ignoring status.

    Candidate lists are bounded observations, never proof of absence. An
    uncertain effect has no authoritative original binding and cannot use this
    function to promote a plausible body/time match to confirmed.
    """
    if result.state != "confirmed" or not isinstance(result.result_digest, str):
        raise HeldOutcome("No confirmed original-send binding is available")
    matches = set()
    for item in candidates:
        if item.recipient != recipient:
            continue
        digest = hashlib.sha256(json.dumps(
            {"message_sid": item.message_sid}, sort_keys=True, separators=(",", ":")
        ).encode()).hexdigest()
        if digest == result.result_digest:
            matches.add(item.message_sid)
    if len(matches) != 1:
        raise HeldOutcome("Original send is not proven by these observations")
    return matches.pop()


class BrokerPort(Protocol):
    """Implemented by the admitted host transport, not by model tools."""

    async def inbound_list(
        self, *, after: PollCursor | None, limit: int
    ) -> IncomingPage | InboundObservationRefusal: ...

    async def send_text(
        self, *, recipient: str, text: str, operation_id: str
    ) -> SendResult: ...


@dataclass
class TurnBinding:
    message: IncomingMessage
    deadline: datetime
    active: bool = True
    uncertain: bool = False
    reply_ordinal: int = 0


_current: contextvars.ContextVar[TurnBinding] = contextvars.ContextVar("shop_turn")


def current_binding(now: datetime | None = None) -> TurnBinding:
    """Return only the channel's current, unexpired binding.

    A copied async context cannot keep authority after its parent turn exits:
    the shared binding object is closed in the parent's finally block.
    """
    try:
        binding = _current.get()
    except LookupError:
        raise PermissionError("No authenticated channel turn") from None
    if not binding.active or (now or datetime.now(timezone.utc)) >= binding.deadline:
        raise PermissionError("Channel turn is closed or expired")
    return binding


class PollingRuntime:
    def __init__(
        self,
        broker: BrokerPort,
        journal: ChannelJournal,
        *,
        scope: str,
        connection_id: str,
        sandbox_recipient: str,
        allowed_senders: frozenset[str],
        not_before: datetime,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        timeout: float = 20,
    ) -> None:
        if not scope or not connection_id or not 0 < timeout <= 20:
            raise ValueError("An admitted scope, connection, and bounded timeout are required")
        if not_before.tzinfo is None:
            raise ValueError("The polling cutoff must be timezone-aware")
        self.broker, self.journal = broker, journal
        self.scope, self.connection_id = scope, connection_id
        self.recipient, self.not_before = sandbox_recipient, not_before
        if not allowed_senders:
            raise ValueError("An explicit participant allowlist is required")
        self.allowed_senders = frozenset(allowed_senders)
        self.clock, self.timeout = clock, timeout
        self._stream = hashlib.sha256(f"{connection_id}:{sandbox_recipient}".encode()).hexdigest()
        saved = journal.cursor(scope, self._stream)
        self.after = PollCursor(datetime.fromisoformat(saved[0]), saved[1]) if saved else None
        self._poll_lock = asyncio.Lock()

    def _validate(self, message: IncomingMessage) -> None:
        if not isinstance(message, IncomingMessage):
            raise ValueError("Transport did not return a typed message")
        if not isinstance(message.connection_id, str) or not message.connection_id:
            raise ValueError("Invalid connection ID")
        if not isinstance(message.recipient, str) or not re.fullmatch(r"whatsapp:\+[1-9][0-9]{7,14}", message.recipient):
            raise ValueError("Invalid recipient")
        if not re.fullmatch(r"whatsapp:\+[1-9][0-9]{7,14}", message.sender):
            raise ValueError("Invalid verified sender")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", message.message_sid):
            raise ValueError("Invalid provider message ID")
        if not message.execution_id or len(message.execution_id) > 128:
            raise ValueError("Missing bounded retrieval execution ID")
        if not isinstance(message.text, str) or len(message.text) > 4096:
            raise ValueError("Only bounded text messages are accepted")
        if type(message.num_media) is not int or message.num_media < 0:
            raise ValueError("Invalid media count")
        if message.sent_at.tzinfo is None:
            raise ValueError("Message time must be timezone-aware")

    def _skip_reason(self, message: IncomingMessage) -> str | None:
        if message.connection_id != self.connection_id or message.recipient != self.recipient:
            return "wrong_binding"
        if message.sender not in self.allowed_senders:
            return "unlisted_sender"
        if message.num_media:
            return "media"
        if not message.text:
            return "empty_text"
        if message.sent_at < max(self.not_before, self.clock() - timedelta(minutes=15)) or message.sent_at > self.clock():
            return "outside_window"
        return None

    def _advance(self, message: IncomingMessage) -> None:
        self._save_cursor(PollCursor(message.sent_at, message.message_sid))

    def _save_cursor(self, cursor: PollCursor) -> None:
        self.journal.save_cursor(self.scope, self._stream,
                                 cursor.date_sent.astimezone(timezone.utc).isoformat(timespec="microseconds"),
                                 cursor.sid)
        saved = self.journal.cursor(self.scope, self._stream)
        self.after = PollCursor(datetime.fromisoformat(saved[0]), saved[1])

    async def poll_once(self, deliver: Callable[[IncomingMessage], Awaitable[None]]) -> list[str]:
        async with self._poll_lock:
            return await self._poll_once(deliver)

    async def _poll_once(self, deliver: Callable[[IncomingMessage], Awaitable[None]]) -> list[str]:
        page = await asyncio.wait_for(
            self.broker.inbound_list(after=self.after, limit=50), min(self.timeout, 15)
        )
        if isinstance(page, InboundObservationRefusal):
            if (page.disposition, page.code, page.reason) != (
                "failed_safe", "REQUEST_REFUSED", "inbound_window_truncated"
            ):
                raise ValueError("Unexpected observation refusal metadata")
            # There is no proven oldest prefix. Do not create claims, deliver,
            # or advance. A later read starts from this exact saved frontier.
            raise HeldOutcome("Broker inbound history coverage is unproven")
        if not isinstance(page, IncomingPage) or not isinstance(page.messages, tuple) or len(page.messages) > 50:
            raise ValueError("Transport batch exceeds its limit")
        if type(page.complete) is not bool:
            raise ValueError("Transport page completeness is not established")
        batch = page.messages
        # Validate the whole batch before allowing any turn to start.
        for message in batch:
            self._validate(message)
        cursors = [PollCursor(item.sent_at, item.message_sid) for item in batch]
        if cursors != sorted(cursors):
            raise ValueError("Transport page is not ordered")
        # Broker replays the entire boundary second. A newly observed SID may
        # sort before the saved SID: provider IDs are not chronological.
        if self.after is not None and any(item.date_sent < self.after.date_sent for item in cursors):
            raise ValueError("Transport returned messages before its boundary second")
        if page.next_after != (cursors[-1] if cursors else self.after):
            raise ValueError("Transport returned an inconsistent next cursor")
        pending_boundary = None
        if not page.complete:
            if not batch:
                raise ValueError("An incomplete page cannot be empty")
            # Only earlier complete seconds may be delivered. Resume at the
            # partial second inclusively, so none of its unseen SIDs is lost.
            boundary = batch[-1].sent_at
            safe = tuple(item for item in batch if item.sent_at < boundary)
            if not safe:
                raise HeldOutcome("One boundary second exceeds the page; owner intervention is required")
            batch, pending_boundary = safe, page.next_after
        results = []
        for message in sorted(batch, key=lambda item: (item.sent_at, item.message_sid)):
            binding = {
                "connection": message.connection_id,
                "recipient": message.recipient,
                "sender": message.sender,
                "message_sid": message.message_sid,
                "text": message.text,
                "sent_at": message.sent_at.isoformat(),
                "num_media": str(message.num_media),
            }
            operation = "inbound:" + message.message_sid
            attempt = self.journal.claim(self.scope, operation, binding=binding)
            if attempt.state != "START":
                results.append(attempt.state)
                self._advance(message)
                continue
            reason = self._skip_reason(message)
            if reason:
                self.journal.skip(self.scope, operation, attempt.ticket, reason)
                results.append("SKIPPED")
                self._advance(message)
                continue
            turn = TurnBinding(message, self.clock() + timedelta(seconds=self.timeout))
            token = _current.set(turn)
            try:
                await asyncio.wait_for(deliver(message), self.timeout)
                if turn.uncertain:
                    raise HeldOutcome("Reply outcome needs original-result lookup")
                self.journal.complete(self.scope, operation, attempt.ticket, "turn:" + message.message_sid)
                results.append("DONE")
            except BaseException:
                self.journal.uncertain(self.scope, operation, attempt.ticket)
                raise
            finally:
                turn.active = False
                _current.reset(token)
            self._advance(message)
        if pending_boundary is not None:
            self._save_cursor(pending_boundary)
        return results

    async def reply(self, text: str) -> str:
        turn = current_binding(self.clock())
        if not isinstance(text, str) or not 0 < len(text) <= 1600:
            raise ValueError("Reply must be bounded text")
        turn.reply_ordinal += 1
        operation = "send:" + hashlib.sha256(
            f"{self.scope}:{turn.message.message_sid}:{turn.reply_ordinal}".encode()
        ).hexdigest()[:32]
        claim = self.journal.claim(
            self.scope, operation,
            binding={"recipient": turn.message.sender, "text": text, "message_sid": turn.message.message_sid},
        )
        if claim.state == "DONE":
            return claim.result_ref
        if claim.state != "START":
            turn.uncertain = True
            raise HeldOutcome("Original send is held")
        try:
            result = await asyncio.wait_for(
                self.broker.send_text(recipient=turn.message.sender, text=text, operation_id=operation),
                min(self.timeout, 15),
            )
            if result.state != "confirmed" or not isinstance(result.result_digest, str) or not re.fullmatch(r"[a-f0-9]{64}", result.result_digest):
                raise HeldOutcome("Send is not authoritatively completed")
            self.journal.complete(self.scope, operation, claim.ticket, result.result_digest)
            return result.result_digest
        except BaseException:
            turn.uncertain = True
            self.journal.uncertain(self.scope, operation, claim.ticket)
            raise
