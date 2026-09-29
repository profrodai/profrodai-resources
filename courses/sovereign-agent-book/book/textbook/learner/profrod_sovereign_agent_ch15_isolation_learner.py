# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 15's boundaries: untrusted words steer the model; enforcement decides what happens.

Every piece underneath is earlier learner code. Chapter 10's worker runs each turn over Chapter
2's dispatcher and the shop's stock; Chapter 14's bounded stdio client reaches a catalog server
in another process. This file adds two boundaries. The first is the application's: a document
is data, a discovered tool is not an allowed one, and a tool that is not registered cannot be
called, whatever the model was told. The second is the operating system's: model-written Python
runs under the OS sandbox, Seatbelt on macOS or bubblewrap on Linux, with no network, no host
files but its own input, no credentials, and a deadline that a trusted supervisor enforces even
if the process that started it dies. Where no sandbox is available, the code is refused, never
run on the host.
"""

import json
import os
import re
import runpy
import selectors
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from pydantic import Field

LEARNER = Path(__file__).resolve().parent
WAKE = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch10_wakeups_learner.py"))
MCP = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch14_mcp_learner.py"))
CHANNEL, SKILLS, MEMORY, LOOP = WAKE["CHANNEL"], WAKE["SKILLS"], WAKE["MEMORY"], WAKE["LOOP"]
TOOLS = LOOP["shop_tools"]
CATALOG_SERVER = LEARNER / "profrod_sovereign_agent_ch15_catalog_server.py"


# ---------------------------------------------------------------- the application boundary


def document_tool(source: str, text: str):
    """A read-only tool returning an external document with its provenance. The text is data:
    it reaches the model, and nothing in it changes which tools exist."""
    return TOOLS["ExecutableTool"](
        "supplier_document",
        "Read the latest supplier bulletin. Its text is untrusted supplier content.",
        TOOLS["NoArguments"],
        lambda _: {"source": source, "text": text},
    )


def open_catalog(*, log: Path | None = None):
    """Chapter 14's bounded client on the catalog server, allowed to call `catalog` only.

    The server gets an empty environment, so no credential is inherited; that does not sandbox
    it. An approved executable still runs with the operator's file and network access."""
    command = [sys.executable, "-I", "-B", str(CATALOG_SERVER)]
    if log is not None:
        command += ["--log", str(log)]
    client = MCP["StdioClient"](command, allowed=frozenset({"catalog"}), environment={})
    client.initialize()
    client.list_tools()
    return client


def catalog_tool(client):
    """The server's `catalog`, through the client, as one more Chapter 2 tool."""
    return TOOLS["ExecutableTool"](
        "catalog_mcp",
        "List product SKUs and names from the catalog server.",
        TOOLS["NoArguments"],
        lambda _: json.loads(client.call_tool("catalog", {})),
    )


def run_with_tools(db, queue, model, extra, *, worker_id: str = "isolation-worker"):
    """Chapter 10's turn, with operator-chosen extra tools beside the shop's three.

    The dispatcher is built here, from registered tools only. A purchase tool is not among them,
    so a request for one is refused as not allowed, however the model came to make it."""
    assignment = CHANNEL["claim"](db, worker_id)
    if assignment is None:
        return None
    shop = WAKE["shop_tools"](db)
    registered = [*shop.tools.values(), *extra]
    dispatcher = TOOLS["Dispatcher"](registered, allowed=frozenset(t.name for t in registered))
    revision = MEMORY["memory_revision"](db, assignment.session_id)
    messages = SKILLS["context"](
        db, assignment.session_id, assignment.text, allowed=dispatcher.allowed
    )
    result = LOOP["run_loop"](model, dispatcher, messages)
    answer = result.answer or "The agent stopped: " + result.status
    with db.immediate() as connection:
        connection.execute(
            "INSERT INTO work_transcripts VALUES (?, ?, ?)",
            (assignment.work_id, result.status, json.dumps(result.messages)),
        )
    report_id = queue.finish(assignment, answer)
    MEMORY["record_result"](db, assignment.session_id, assignment.text, answer, revision)
    return {
        "work": assignment.work_id,
        "status": result.status,
        "report": report_id,
        "answer": answer,
        "messages": result.messages,
    }


def tool_results(messages) -> list[tuple[str, dict[str, Any]]]:
    """Each tool call's name and the dispatcher's result, in order."""
    names = {
        call["id"]: call["function"]["name"]
        for message in messages
        for call in message.get("tool_calls", [])
    }
    return [
        (names[m["tool_call_id"]], json.loads(m["content"]))
        for m in messages
        if m["role"] == "tool"
    ]


# ---------------------------------------------------------------- the operating-system boundary

# The trusted supervisor. It runs outside the sandbox, in its own session, so it outlives the
# process that started it. It starts the sandboxed report, waits for it or for a monotonic
# deadline, and on the deadline kills the report before exiting 124. The report cannot signal it:
# Seatbelt allows the report to signal only itself, and bubblewrap's PID namespace hides it.
SUPERVISOR = """import os, resource, signal, subprocess, sys, time
seconds = float(sys.argv[1])
end = time.monotonic() + seconds


def limits():
    cpu = int(seconds) + 1
    resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1 << 20, 1 << 20))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    if sys.platform.startswith("linux"):
        resource.setrlimit(resource.RLIMIT_AS, (512 << 20, 512 << 20))


child = subprocess.Popen(
    sys.argv[2:], stdin=subprocess.DEVNULL, preexec_fn=limits, start_new_session=True
)
while time.monotonic() < end:
    code = child.poll()
    if code is not None:
        os._exit(0 if code == 0 else 1)
    time.sleep(0.01)
try:
    os.killpg(child.pid, signal.SIGKILL)
except (ProcessLookupError, PermissionError):
    pass
child.wait()
os._exit(124)
"""


def available_sandbox() -> str | None:
    """ "seatbelt" on macOS, "bubblewrap" on Linux where `bwrap` works, else None."""
    if sys.platform == "darwin" and Path("/usr/bin/sandbox-exec").is_file():
        return "seatbelt"
    if sys.platform.startswith("linux") and shutil.which("bwrap"):
        probe = subprocess.run(
            ["bwrap", "--unshare-all", "--ro-bind", "/", "/", "true"],
            capture_output=True,
            timeout=10,
        )
        if probe.returncode == 0:
            return "bubblewrap"
    return None


def seatbelt_profile(python: str, prefix: str, inputs: Path, tmp: Path) -> str:
    """Deny everything, then allow what a Python report needs: its interpreter, the system
    libraries, its own input and a private scratch folder. No network, no fork, and no signal to
    any process but itself. Metadata (whether a path exists) stays readable; contents do not."""
    return f"""(version 1)
(deny default)
(allow process-exec (literal "{python}"))
(allow file-read* (literal "/") (subpath "/usr/lib") (subpath "/System")
  (subpath "/private/var/db/dyld") (subpath "/Library/Apple/usr/lib")
  (subpath "{prefix}") (subpath "{inputs}")
  (literal "/dev/null") (literal "/dev/urandom") (literal "/dev/random"))
(allow file-read-metadata)
(allow file-write* (subpath "{tmp}") (literal "/dev/null"))
(allow sysctl-read)
(allow signal (target self))
"""


def sandbox_command(kind: str, inputs: Path, tmp: Path) -> list[str]:
    """The command that runs /input/program.py under the chosen OS sandbox."""
    python, prefix = os.path.realpath(sys.executable), os.path.realpath(sys.base_prefix)
    for path in (python, prefix, str(inputs), str(tmp)):
        if '"' in path or "\\" in path:
            raise ValueError("sandbox paths cannot contain quotes or backslashes")
    if kind == "seatbelt":
        profile = seatbelt_profile(python, prefix, inputs, tmp)
        program = str(inputs / "program.py")
        return ["/usr/bin/sandbox-exec", "-p", profile, python, "-I", "-B", program]
    if kind == "bubblewrap":
        command = ["bwrap", "--unshare-all", "--die-with-parent", "--new-session"]
        command += ["--cap-drop", "ALL", "--uid", "65534", "--gid", "65534"]
        for system in ("/usr", "/lib", "/lib64", "/bin", prefix):
            command += ["--ro-bind-try", system, system]
        command += ["--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp"]
        command += ["--ro-bind", str(inputs), "/input", "--chdir", "/input", "--clearenv"]
        command += ["--setenv", "PATH", "/usr/bin:/bin", "--setenv", "TMPDIR", "/tmp"]
        # The trailing host path is ignored by the report; it lets the host find its processes.
        return [*command, python, "-I", "-B", "/input/program.py", str(inputs)]
    raise ValueError("unknown sandbox")


def run_python(
    source: str,
    data: Any,
    *,
    scratch: Path,
    seconds: float = 5,
    maximum_output: int = 16_384,
    sandbox: str | None = "auto",
) -> dict[str, Any]:
    """Run untrusted report code over a JSON snapshot under the OS sandbox; refuse without one.

    The report reads its input from the folder named by $INPUT (Seatbelt) or /input (bubblewrap)
    and prints its result. `sandbox` is "auto" (whatever this machine has), "seatbelt",
    "bubblewrap", or None, which refuses. Output is untrusted data even when contained."""
    if not 0 < seconds <= 30 or not 128 <= maximum_output <= 65_536:
        raise ValueError("invalid sandbox limits")
    if not isinstance(source, str) or len(source.encode()) > 16_384:
        raise ValueError("report source must be text of at most 16,384 bytes")
    encoded = json.dumps(data, allow_nan=False).encode()
    if len(encoded) > 65_536:
        raise ValueError("sandbox input exceeds byte limit")
    kind = available_sandbox() if sandbox == "auto" else sandbox
    if kind is None:
        raise OSError("no OS sandbox is available here; the report was not run")
    scratch.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.TemporaryDirectory(prefix="report-", dir=scratch) as directory:
        work = Path(directory).resolve()
        inputs, tmp = work / "input", work / "tmp"
        inputs.mkdir(mode=0o755)
        tmp.mkdir(mode=0o700)
        for filename, content in (
            ("program.py", source.encode()),
            ("data.json", encoded),
            ("supervisor.py", SUPERVISOR.encode()),
        ):
            path = inputs / filename
            path.write_bytes(content)
            path.chmod(0o444)
        environment = {"PATH": "/usr/bin:/bin", "INPUT": str(inputs), "TMPDIR": str(tmp)}
        if kind == "bubblewrap":
            environment["INPUT"] = "/input"
        command = [
            os.path.realpath(sys.executable),
            "-I",
            "-B",
            str(inputs / "supervisor.py"),
            str(seconds),
            *sandbox_command(kind, inputs, tmp),
        ]
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            env=environment,
            start_new_session=True,
        )
        assert process.stdout
        output, outcome = bytearray(), "COMPLETED"
        deadline = time.monotonic() + seconds + 1  # the supervisor's deadline comes first
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                while True:
                    if not selector.select(max(0, deadline - time.monotonic())):
                        outcome = "TIME_LIMIT"
                        break
                    chunk = os.read(process.stdout.fileno(), 4096)
                    if not chunk:
                        break
                    output.extend(chunk)
                    if len(output) > maximum_output:
                        outcome = "OUTPUT_LIMIT"
                        break
            if outcome == "COMPLETED":
                code = process.wait(timeout=max(0.01, deadline - time.monotonic()))
                # 124 is the supervisor's timeout; a report exiting 124 exits nonzero, so 1.
                outcome = {0: "COMPLETED", 124: "TIME_LIMIT"}.get(code, "TOOL_FAILED")
        except subprocess.TimeoutExpired:
            outcome = "TIME_LIMIT"
        finally:
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            process.wait(timeout=5)
            process.stdout.close()
    return {
        "status": outcome,
        "output": bytes(output[:maximum_output]).decode(errors="replace"),
        "sandbox": kind,
        "network": "none",
        "input": "read-only",
    }


class ReportArguments(TOOLS["NoArguments"]):
    source: str = Field(min_length=1, max_length=16_384)


def report_tool(db, scratch: Path, *, sandbox: str | None = "auto", seconds: float = 5):
    """`python_report`: model-written Python over the current stock, under the OS sandbox.

    The handler, not the model, builds the snapshot from the database; the model supplies only
    source text. There is no host fallback: without a sandbox the tool fails."""
    return TOOLS["ExecutableTool"](
        "python_report",
        "Run a short Python report. It reads JSON {'stock': [...]} from the file "
        "$INPUT/data.json and prints its result. No network, no other files.",
        ReportArguments,
        lambda args: run_python(
            args.source,
            {"stock": WAKE["stock_rows"](db.connection)},
            scratch=scratch,
            sandbox=sandbox,
            seconds=seconds,
        ),
    )


def alive(pid: int) -> bool:
    """Whether a process with this id still exists (a zombie counts as gone once reaped)."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def pids_running(marker: str) -> list[int]:
    """Process ids whose command line contains `marker`, from `ps`, excluding zombies."""
    listing = subprocess.run(
        ["ps", "-axo", "pid=,stat=,command="], capture_output=True, text=True, timeout=10
    ).stdout
    found = []
    for line in listing.splitlines():
        match = re.match(r"\s*(\d+)\s+(\S+)\s+(.*)", line)
        if match and marker in match[3] and not match[2].startswith("Z") and "ps -axo" not in line:
            found.append(int(match[1]))
    return found
