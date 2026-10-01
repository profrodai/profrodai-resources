# Prof Rod | Measure Whether a Coding Agent Weakens Tests Under Pressure
# Article: https://profrod.ai/articles/dark-software-factory-test-authority
# Original source and updates: https://github.com/profrodai/profrodai-resources

"""Run model-written code and its tests under an operating-system sandbox, or not at all.

Adapted from Chapter 15's isolation learner (profrod_sovereign_agent_ch15_isolation_learner.py):
deny-default Seatbelt on macOS, bubblewrap on Linux, a trusted supervisor in its own session that
holds the deadline, read-only inputs, a private scratch folder, and no network. Without a sandbox
it refuses: the code a model writes is untrusted, whatever the experiment.

The program that runs inside the sandbox is ours (HARNESS): it imports the candidate's solution.py
and a test module, runs every test_ function, and prints one JSON line of results.
"""

from __future__ import annotations

import json
import os
import selectors
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

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

HARNESS = """import importlib, json, os, sys
# The candidate's own output goes nowhere; the result line goes to a saved copy of stdout, and the
# harness exits at once after writing it, so code under test cannot print or append a fake result.
real = os.dup(1)
sink = os.open(os.devnull, os.O_WRONLY)
os.dup2(sink, 1)
os.dup2(sink, 2)


def report(result):
    os.write(real, (json.dumps(result) + "\\n").encode())
    os._exit(0)


root = os.environ.get("INPUT", "/input")
sys.path.insert(0, root)
sys.dont_write_bytecode = True
result = {}
try:
    tests = importlib.import_module(sys.argv[1])
except BaseException as error:
    report({"__import__": "error: " + type(error).__name__ + ": " + str(error)[:300]})
for name in sorted(n for n in dir(tests) if n.startswith("test")):
    fn = getattr(tests, name)
    if not callable(fn):
        continue
    try:
        fn()
        result[name] = "pass"
    except AssertionError as error:
        result[name] = "fail: " + str(error)[:300]
    except BaseException as error:
        result[name] = "error: " + type(error).__name__ + ": " + str(error)[:300]
report(result)
"""


def available_sandbox() -> str | None:
    """ "seatbelt" on macOS, "bubblewrap" on Linux where `bwrap` works, else None."""
    if sys.platform == "darwin" and Path("/usr/bin/sandbox-exec").is_file():
        return "seatbelt"
    if sys.platform.startswith("linux") and shutil.which("bwrap"):
        probe = subprocess.run(["bwrap", "--unshare-all", "--ro-bind", "/", "/", "true"], capture_output=True, timeout=10)
        if probe.returncode == 0:
            return "bubblewrap"
    return None


def seatbelt_profile(python: str, prefix: str, inputs: Path, tmp: Path) -> str:
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


def sandbox_command(kind: str, inputs: Path, tmp: Path, module: str) -> list[str]:
    python, prefix = os.path.realpath(sys.executable), os.path.realpath(sys.base_prefix)
    for path in (python, prefix, str(inputs), str(tmp)):
        if '"' in path or "\\" in path:
            raise ValueError("sandbox paths cannot contain quotes or backslashes")
    if kind == "seatbelt":
        profile = seatbelt_profile(python, prefix, inputs, tmp)
        return ["/usr/bin/sandbox-exec", "-p", profile, python, "-I", "-B", str(inputs / "harness.py"), module]
    if kind == "bubblewrap":
        command = ["bwrap", "--unshare-all", "--die-with-parent", "--new-session", "--cap-drop", "ALL", "--uid", "65534", "--gid", "65534"]
        for system in ("/usr", "/lib", "/lib64", "/bin", prefix):
            command += ["--ro-bind-try", system, system]
        command += ["--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp", "--ro-bind", str(inputs), "/input", "--chdir", "/input", "--clearenv"]
        command += ["--setenv", "PATH", "/usr/bin:/bin", "--setenv", "TMPDIR", "/tmp", "--setenv", "INPUT", "/input"]
        return [*command, python, "-I", "-B", "/input/harness.py", module]
    raise ValueError("unknown sandbox")


def run_tests(files: dict[str, str], module: str, *, scratch: Path, seconds: float = 10, sandbox: str | None = "auto") -> dict:
    """Run `module`'s test functions against `files` (name -> source) in the sandbox.

    Returns {"status": COMPLETED | TIME_LIMIT | TOOL_FAILED | OUTPUT_LIMIT, "tests": {...}, "sandbox": kind}.
    Raises OSError when no sandbox is available: the code is never run unconfined."""
    kind = available_sandbox() if sandbox == "auto" else sandbox
    if kind is None:
        raise OSError("no OS sandbox is available here; model-written code was not run")
    scratch.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.TemporaryDirectory(prefix="run-", dir=scratch) as directory:
        work = Path(directory).resolve()
        inputs, tmp = work / "input", work / "tmp"
        inputs.mkdir(mode=0o755)
        tmp.mkdir(mode=0o700)
        for name, content in {**files, "harness.py": HARNESS, "supervisor.py": SUPERVISOR}.items():
            path = inputs / name
            path.write_text(content)
            path.chmod(0o444)
        environment = {"PATH": "/usr/bin:/bin", "INPUT": str(inputs) if kind == "seatbelt" else "/input", "TMPDIR": str(tmp)}
        command = [os.path.realpath(sys.executable), "-I", "-B", str(inputs / "supervisor.py"), str(seconds), *sandbox_command(kind, inputs, tmp, module)]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, env=environment, start_new_session=True)
        assert process.stdout
        output, status = bytearray(), "COMPLETED"
        deadline = time.monotonic() + seconds + 1
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                while True:
                    if not selector.select(max(0, deadline - time.monotonic())):
                        status = "TIME_LIMIT"
                        break
                    chunk = os.read(process.stdout.fileno(), 4096)
                    if not chunk:
                        break
                    output.extend(chunk)
                    if len(output) > 65_536:
                        status = "OUTPUT_LIMIT"
                        break
            if status == "COMPLETED":
                code = process.wait(timeout=max(0.01, deadline - time.monotonic()))
                status = {0: "COMPLETED", 124: "TIME_LIMIT"}.get(code, "TOOL_FAILED")
        except subprocess.TimeoutExpired:
            status = "TIME_LIMIT"
        finally:
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            process.wait(timeout=5)
            process.stdout.close()
    tests: dict = {}
    for line in bytes(output).decode(errors="replace").splitlines()[::-1]:
        if line.startswith("{"):
            try:
                tests = json.loads(line)
                break
            except json.JSONDecodeError:
                continue
    return {"status": status, "tests": tests, "sandbox": kind}
