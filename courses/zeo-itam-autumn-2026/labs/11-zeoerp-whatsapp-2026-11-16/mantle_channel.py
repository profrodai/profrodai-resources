"""The native Mantle channel shell around the tested polling runtime.

Only the paired worker launcher may install its admitted runtime before Rasa
loads this channel. Running the generic CLI without that setup fails closed.
No provider credential or arbitrary webhook is accepted by this channel.
"""

from __future__ import annotations

import asyncio
import hashlib

from rasa.core.channels.channel import InputChannel, OutputChannel, UserMessage
from sanic import Blueprint, response

from channel_runtime import IncomingMessage, PollingRuntime, current_binding

_installed: PollingRuntime | None = None


def install_runtime(runtime: PollingRuntime) -> None:
    """Called once by the trusted launcher after host and grant admission."""
    global _installed
    if _installed is not None or not isinstance(runtime, PollingRuntime):
        raise RuntimeError("Channel runtime is missing or already installed")
    _installed = runtime


def conversation_id(runtime: PollingRuntime, message: IncomingMessage) -> str:
    # A stable opaque tracker ID keeps raw phone numbers out of tracker IDs.
    # It is not an authentication token or a claim of anonymization.
    return "shop-" + hashlib.sha256(
        f"{runtime.scope}:{message.sender}".encode()
    ).hexdigest()


class BrokerOutput(OutputChannel):
    def __init__(self, runtime: PollingRuntime) -> None:
        self.runtime = runtime

    @classmethod
    def name(cls) -> str:
        return "custody_poll"

    @property
    def supports_streaming(self) -> bool:
        return False

    async def send_text_message(self, recipient_id: str, text: str, **kwargs) -> None:
        message = current_binding(self.runtime.clock()).message
        if recipient_id != conversation_id(self.runtime, message):
            raise PermissionError("Reply recipient does not match this channel turn")
        await self.runtime.reply(text)


class CustodyPollingChannel(InputChannel):
    def __init__(self, runtime: PollingRuntime) -> None:
        self.runtime = runtime
        self.stop = asyncio.Event()
        self.task: asyncio.Task | None = None
        self.failed = False

    @classmethod
    def name(cls) -> str:
        return "custody_poll"

    @classmethod
    def from_credentials(cls, credentials):
        if credentials or _installed is None:
            raise RuntimeError("A paired worker must install the admitted channel runtime")
        return cls(_installed)

    def blueprint(self, on_new_message) -> Blueprint:
        blueprint = Blueprint("custody_poll", __name__)

        async def deliver(message: IncomingMessage) -> None:
            await on_new_message(
                UserMessage(
                    message.text,
                    BrokerOutput(self.runtime),
                    conversation_id(self.runtime, message),
                    input_channel=self.name(),
                    message_id=message.message_sid,
                    metadata={"retrieval_execution": message.execution_id},
                )
            )

        async def poll() -> None:
            try:
                while not self.stop.is_set():
                    await self.runtime.poll_once(deliver)
                    try:
                        await asyncio.wait_for(self.stop.wait(), 5)
                    except asyncio.TimeoutError:
                        pass
            except asyncio.CancelledError:
                raise
            except Exception:
                # No raw provider, phone, message, or credential-bearing errors
                # are logged. The host observes this failed health state.
                self.failed = True

        @blueprint.listener("after_server_start")
        async def start(_app, _loop):
            self.task = asyncio.create_task(poll())

        @blueprint.listener("before_server_stop")
        async def stop(_app, _loop):
            self.stop.set()
            if self.task is not None:
                self.task.cancel()
                await asyncio.gather(self.task, return_exceptions=True)

        @blueprint.route("/", methods=["GET"])
        async def health(_request):
            ready = self.task is not None and not self.task.done() and not self.failed
            return response.json({"ready": ready}, status=200 if ready else 503)

        return blueprint
