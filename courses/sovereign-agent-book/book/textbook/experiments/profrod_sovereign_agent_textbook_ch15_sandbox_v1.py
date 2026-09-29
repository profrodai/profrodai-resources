# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 15's containment experiment: attack the report's sandbox, then kill its host.

  uv run python book/textbook/experiments/profrod_sovereign_agent_textbook_ch15_sandbox_v1.py \
      --out docs/evidence/book-ch15/ch15-sandbox-receipt-v1.json

A report written as an attacker tries, one operation at a time, to write its input, write its
scratch folder, read a file beside its input, read the credential the host holds, reach the
network, start a process and signal the supervisor. Each outcome is recorded as the exception it
raised, so one refusal cannot hide another permission. Then the host process running a report
that waits forever, using no CPU, is killed with SIGKILL, twice: once with the deadline kept only by the host, the
first design, and once with the trusted supervisor. The receipt records whether the report
outlived its host. It runs only where an OS sandbox is available.
"""

import argparse
import json
import os
import platform
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

BOOK = Path(__file__).resolve().parents[1]
LEARNER = BOOK / "learner/profrod_sovereign_agent_ch15_isolation_learner.py"

ATTACK = r"""import json, os, signal, socket, time
root = os.environ.get("INPUT", "/input")
out = {}


def attempt(name, action):
    try:
        action()
        out[name] = "allowed"
    except Exception as error:
        out[name] = type(error).__name__


def fork():
    if os.fork() == 0:
        time.sleep(600)  # a descendant that outlives the report unless something ends it
        os._exit(0)


def data():
    return json.load(open(os.path.join(root, "data.json")))


attempt("read_input", data)
attempt("write_input", lambda: open(os.path.join(root, "data.json"), "a").write("x"))
attempt("write_scratch", lambda: open(os.path.join(os.environ.get("TMPDIR", "/tmp"), "x"), "w").write("x"))
attempt("read_beside_input", lambda: open(os.path.join(root, "..", "..", "secret.txt")).read())
attempt("network", lambda: socket.create_connection(("1.1.1.1", 80), timeout=3))
attempt("start_process", fork)
attempt("signal_outside", lambda: os.kill(data()["outside_pid"], signal.SIGKILL))
out["credential_visible"] = "SOVEREIGN_AGENT_TELEGRAM_TOKEN" in os.environ
out["uid"] = os.getuid()
print(json.dumps(out, sort_keys=True))
"""

# What each probe must show for the sandbox to count as holding. Reading the input is allowed.
# Starting a process is recorded but not judged: Seatbelt refuses it, while bubblewrap allows it
# inside a PID namespace that ends with the report. What must hold on both is judged by the host:
# no descendant outlives the report, and a process outside survives the report's SIGKILL.
EXPECTED = {
    "read_input": "allowed",
    "write_input": "refused",
    "write_scratch": "allowed",
    "read_beside_input": "refused",
    "network": "refused",
    "signal_outside": "refused",
    "credential_visible": False,
    "outside_process_survived": True,
    "descendant_outlived_report": False,
}
HOST_OBSERVED = ("outside_process_survived", "descendant_outlived_report")

HOST = r"""import runpy, sys
from pathlib import Path
WAITING = "import time\ntime.sleep(600)"
iso = runpy.run_path(sys.argv[1])
scratch, supervised = Path(sys.argv[2]), sys.argv[3] == "supervised"
if supervised:
    iso["run_python"](WAITING, {}, scratch=scratch, seconds=float(sys.argv[4]))
else:
    # The first design: the host alone keeps the deadline, then kills the report.
    import os, signal, subprocess, tempfile, time
    work = Path(tempfile.mkdtemp(dir=scratch))
    inputs, tmp = work / "input", work / "tmp"
    inputs.mkdir(); tmp.mkdir()
    (inputs / "program.py").write_text(WAITING)
    command = iso["sandbox_command"](iso["available_sandbox"](), inputs, tmp)
    child = subprocess.Popen(command, start_new_session=True, env={"PATH": "/usr/bin:/bin"})
    time.sleep(float(sys.argv[4]))
    os.killpg(child.pid, signal.SIGKILL)
"""


def outcome(value):
    if isinstance(value, bool) or value == "allowed":
        return value
    return "refused"


def probe(scratch: Path, sandbox: str) -> dict:
    """Run the attack report through run_python with a secret file beside its scratch folder
    and a credential in the host's environment; return each probe's raw and judged outcome."""
    iso = runpy_learner()
    scratch.mkdir(parents=True, exist_ok=True)
    (scratch / "secret.txt").write_text("not for the report")
    outside = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    os.environ["SOVEREIGN_AGENT_TELEGRAM_TOKEN"] = "123:host-credential-sentinel"
    try:
        data = {"stock": [], "outside_pid": outside.pid}
        result = iso["run_python"](ATTACK, data, scratch=scratch, sandbox=sandbox)
    finally:
        del os.environ["SOVEREIGN_AGENT_TELEGRAM_TOKEN"]
        time.sleep(0.2)
        raw_survived = outside.poll() is None
        outside.kill()
        outside.wait()
    raw = json.loads(result["output"])
    raw["outside_process_survived"] = raw_survived
    raw["descendant_outlived_report"] = bool(iso["pids_running"](str(scratch)))
    judged = {name: outcome(raw[name]) for name in EXPECTED}
    return {"status": result["status"], "raw": raw, "judged": judged, "holds": judged == EXPECTED}


def runpy_learner():
    import runpy

    return runpy.run_path(str(LEARNER))


def host_death(scratch: Path, *, supervised: bool, seconds: float = 2.0) -> dict:
    """Start a host running a never-ending report, kill the host with SIGKILL once the report is
    running, and check whether the report is still running after the deadline has passed."""
    iso = runpy_learner()
    scratch = Path(tempfile.mkdtemp(prefix="death-", dir=scratch)).resolve()
    host = subprocess.Popen(
        [
            sys.executable,
            "-c",
            HOST,
            str(LEARNER),
            str(scratch),
            "supervised" if supervised else "host-only",
            str(seconds if supervised else 60),
        ],
        cwd=BOOK.parents[1],
    )
    marker = str(scratch)
    started = time.monotonic()
    while not [p for p in iso["pids_running"](marker) if p != host.pid]:
        if time.monotonic() - started > 15:
            host.kill()
            raise RuntimeError("the report never started")
        time.sleep(0.05)
    time.sleep(0.3)
    os.kill(host.pid, signal.SIGKILL)
    host.wait()
    time.sleep(seconds + 1.5)
    survivors = iso["pids_running"](marker)
    for pid in survivors:  # clean up our own test processes only
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    return {
        "design": "supervisor" if supervised else "host deadline only",
        "deadline_seconds": seconds,
        "report_survived_host": bool(survivors),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not args.out.parent.is_dir():
        raise SystemExit(f"output folder {args.out.parent} does not exist")
    iso = runpy_learner()
    sandbox = iso["available_sandbox"]()
    if sandbox is None:
        raise SystemExit("no OS sandbox here: nothing to measure")
    with tempfile.TemporaryDirectory(prefix="lucy-sandbox-") as temporary:
        root = Path(temporary).resolve()
        attack = probe(root / "attack", sandbox)
        endless = iso["run_python"](
            "import time\ntime.sleep(600)", {}, scratch=root / "t", seconds=1
        )
        busy = iso["run_python"]("while True: pass", {}, scratch=root / "u", seconds=1)
        flood = iso["run_python"]("print('x' * 100_000)", {}, scratch=root / "f", seconds=5)
        deaths = [host_death(root, supervised=False), host_death(root, supervised=True)]
    receipt = {
        "schema": "profrod.sovereign-agent.ch15-sandbox.v1",
        "recorded": time.strftime("%Y-%m-%d"),
        "platform": f"{platform.system()} {platform.release()} {platform.machine()}",
        "python": platform.python_version(),
        "sandbox": sandbox,
        "attack": attack,
        "endless_report": endless["status"],
        "busy_report": busy["status"],
        "excessive_output": flood["status"],
        "host_death": deaths,
    }
    args.out.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
