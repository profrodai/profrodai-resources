# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 19's host experiment: the Chapter 10 worker as a systemd user service, on Linux.

  python profrod_sovereign_agent_textbook_ch19_service_v1.py install --state DIR --python PY \
      --out receipt.json
  (reboot the host)
  python profrod_sovereign_agent_textbook_ch19_service_v1.py after-reboot --state DIR --python PY \
      --out receipt.json
  python profrod_sovereign_agent_textbook_ch19_service_v1.py uninstall --state DIR --python PY

Run it from the course folder on a Linux host whose user manager lingers (`loginctl enable-linger`),
with PY a Python 3.12 that has Pydantic, such as a uv virtual environment. `install` prepares a new
state folder with a due brief and a vanilla shortage, installs the unit, and waits for the service
to finish both; then it kills the service's process with SIGKILL and waits for systemd to restart
it and for the restarted process to finish new work. `after-reboot` checks that the service came
back after a real reboot and still does new work. Every observation goes in the receipt.
"""

import argparse
import json
import os
import platform
import runpy
import signal
import sqlite3
import subprocess
import time
from pathlib import Path

BOOK = Path(__file__).resolve().parents[1]
COURSE = BOOK.parents[1]
OPS = runpy.run_path(str(BOOK / "learner/profrod_sovereign_agent_ch19_operations_learner.py"))
WAKE = BOOK / "learner/profrod_sovereign_agent_ch10_wakeups_learner.py"


def show(state: Path, python: Path) -> dict[str, str]:
    result = OPS["service"]("status", state, python, COURSE)
    return dict(line.split("=", 1) for line in result["status"].splitlines() if "=" in line)


def boot_id() -> str:
    return Path("/proc/sys/kernel/random/boot_id").read_text().strip()


def finished(state: Path, source_prefix: str) -> list[str]:
    with sqlite3.connect(f"file:{state / 'agent.sqlite'}?mode=ro", uri=True) as db:
        return [
            row[0]
            for row in db.execute(
                "SELECT r.body FROM work w JOIN reports r ON r.work_id = w.work_id"
                " WHERE w.state='finished' AND w.source_id LIKE ?",
                (source_prefix + "%",),
            )
        ]


def wait_for(condition, seconds: float = 60) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(0.5)
    return False


def schedule_now(state: Path, identifier: str) -> None:
    """A job due now, written by a separate process while the service runs."""
    subprocess.run(
        [
            str(Path(os.environ.get("LUCY_PYTHON", ""))),
            "-c",
            "import runpy, sys, time\n"
            f"wake = runpy.run_path({str(WAKE)!r})\n"
            "db, queue = wake['open_shop'](sys.argv[1])\n"
            "wake['schedule'](db, sys.argv[2], 'lucy', 'Prepare a stock brief.',"
            " first_due=time.time(), interval_seconds=86_400)\n"
            "db.close()\n",
            str(state / "agent.sqlite"),
            identifier,
        ],
        check=True,
        cwd=COURSE,
    )


def install(state: Path, python: Path) -> dict:
    wake = runpy.run_path(str(WAKE))
    state.mkdir(mode=0o700)
    env = state / "agent.env"
    env.touch(mode=0o600)
    db, _ = wake["open_shop"](state / "agent.sqlite")
    wake["seed_shop"](db)
    wake["CHANNEL"]["activate_opening_skill"](db)
    wake["schedule"](
        db,
        "morning",
        "lucy",
        "Prepare the opening brief.",
        first_due=time.time(),
        interval_seconds=86_400,
    )
    wake["watch"](db, "vanilla-low", "lucy", "SKU-VANILLA")
    db.close()
    OPS["service"]("install", state, python, COURSE)
    served = wait_for(
        lambda: finished(state, "job:morning") and finished(state, "stock-condition:vanilla-low:1")
    )
    before = show(state, python)
    os.kill(int(before["MainPID"]), signal.SIGKILL)
    restarted = wait_for(
        lambda: (
            show(state, python).get("NRestarts") == "1"
            and show(state, python).get("ActiveState") == "active"
            and show(state, python).get("MainPID") not in {"0", before["MainPID"]}
        ),
        seconds=40,
    )
    after = show(state, python)
    schedule_now(state, "after-restart")
    worked = wait_for(lambda: finished(state, "job:after-restart"))
    return {
        "linger": subprocess.run(
            ["loginctl", "show-user", os.environ["USER"], "-p", "Linger"],
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip(),
        "boot_before": boot_id(),
        "status_before_kill": before,
        "status_after_restart": after,
        "reports": {
            "morning": finished(state, "job:morning"),
            "vanilla episode": finished(state, "stock-condition:vanilla-low:1"),
            "after restart": finished(state, "job:after-restart"),
        },
        "checks": {
            "served_work": served,
            "restarted_after_sigkill": restarted,
            "work_after_restart": worked,
        },
    }


def after_reboot(state: Path, python: Path, receipt: dict) -> dict:
    active = wait_for(lambda: show(state, python).get("ActiveState") == "active", seconds=60)
    schedule_now(state, "after-reboot")
    worked = wait_for(lambda: finished(state, "job:after-reboot"))
    receipt["boot_after"] = boot_id()
    receipt["status_after_reboot"] = show(state, python)
    receipt["reports"]["after reboot"] = finished(state, "job:after-reboot")
    receipt["checks"]["rebooted"] = receipt["boot_after"] != receipt["boot_before"]
    receipt["checks"]["active_after_reboot"] = active
    receipt["checks"]["work_after_reboot"] = worked
    receipt["checks"]["linger_enabled"] = receipt["linger"] == "Linger=yes"
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("phase", choices=("install", "after-reboot", "uninstall"))
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    os.environ["LUCY_PYTHON"] = str(args.python)
    if args.phase == "uninstall":
        print(OPS["service"]("uninstall", args.state, args.python, COURSE))
        return
    if args.out is None or not args.out.parent.is_dir():
        raise SystemExit("an --out path in an existing folder is required")
    if args.phase == "install":
        receipt = {
            "schema": "profrod.sovereign-agent.ch19-service.v1",
            "recorded": time.strftime("%Y-%m-%d"),
            "platform": f"{platform.system()} {platform.release()} {platform.machine()}",
            "systemd": subprocess.run(
                ["systemctl", "--version"], capture_output=True, text=True, timeout=10
            ).stdout.splitlines()[0],
            "python": subprocess.run(
                [str(args.python), "-c", "import platform; print(platform.python_version())"],
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout.strip(),
            "paths": {"state": str(args.state), "python": str(args.python), "course": str(COURSE)},
            "unit": OPS["unit_text"](args.state, args.python, COURSE),
            **install(args.state, args.python),
        }
    else:
        receipt = after_reboot(args.state, args.python, json.loads(args.out.read_text()))
    args.out.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt["checks"], indent=2))


if __name__ == "__main__":
    main()
