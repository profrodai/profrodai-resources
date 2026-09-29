# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 3's killable HTTP request: one deadline covers DNS, headers and the whole body.

The parent runs this same file as a short-lived child and kills it when the deadline expires.
The request, including any credential header, crosses the child's standard input, never its
command line. Killing the child cannot cancel work or a bill the remote service already accepted.
"""

import base64
import json
import math
import os
import signal
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """A redirect could forward an authorization header to another host; refuse every one."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise OSError("redirect refused")


@dataclass(frozen=True)
class HTTPResult:
    status: int
    body: bytes


def request(url, *, data=None, headers=None, timeout=10, maximum_bytes=262_144):
    if not math.isfinite(timeout) or not 0 < timeout <= 120 or not 1 <= maximum_bytes <= 1_048_576:
        raise ValueError("bounded HTTP deadline and response required")
    payload = json.dumps(
        {
            "url": url,
            "data": None if data is None else base64.b64encode(data).decode(),
            "headers": headers or {},
            "timeout": timeout,
            "maximum": maximum_bytes,
        }
    )
    # The child inherits only what it needs: no proxies, no PYTHONPATH, no other secrets.
    keep = {"PATH", "SYSTEMROOT", "SSL_CERT_FILE", "SSL_CERT_DIR"}
    environment = {name: value for name, value in os.environ.items() if name in keep}
    try:
        child = subprocess.run(
            [sys.executable, os.path.abspath(__file__)],
            input=payload.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            env=environment,
            check=False,
        )
        if child.returncode:
            raise OSError("HTTP transport failed")
        result = json.loads(child.stdout)
        return HTTPResult(result["status"], base64.b64decode(result["body"], validate=True))
    except subprocess.TimeoutExpired:
        raise TimeoutError("HTTP deadline expired; remote outcome may be unknown") from None
    except (ValueError, KeyError):
        raise OSError("invalid HTTP transport result") from None


def child():
    try:
        spec = json.loads(sys.stdin.buffer.read(1_048_577))
        if hasattr(signal, "setitimer"):
            # If the parent is killed, the child still stops itself at the deadline.
            signal.signal(signal.SIGALRM, signal.SIG_DFL)
            signal.setitimer(signal.ITIMER_REAL, spec["timeout"])
        data = spec["data"]
        outgoing = urllib.request.Request(
            spec["url"],
            data=None if data is None else base64.b64decode(data),
            headers=spec["headers"],
        )
        try:
            opener = urllib.request.build_opener(NoRedirect())
            with opener.open(outgoing, timeout=spec["timeout"]) as response:
                body = response.read(spec["maximum"] + 1)
                if len(body) > spec["maximum"]:
                    return 2
                status = response.status
        except urllib.error.HTTPError as error:
            status, body = error.code, b""
        print(json.dumps({"status": status, "body": base64.b64encode(body).decode()}))
        return 0
    except (OSError, ValueError, KeyError, TypeError):
        return 2


if __name__ == "__main__":
    raise SystemExit(child())
