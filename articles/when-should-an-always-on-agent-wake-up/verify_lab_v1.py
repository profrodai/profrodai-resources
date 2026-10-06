"""Execute the original CLI and every plain notebook cell; no network or model call."""
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent


def verify():
    notebook = json.loads((ROOT / "jev_wake_gate_v7.ipynb").read_text())
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    assert notebook["metadata"]["profrod"]["helperSha256"] == sha(ROOT / "wake_gate_v3.py")
    assert notebook["metadata"]["profrod"]["fixtureSha256"] == sha(ROOT / "synthetic-events-v1.json")
    reference = json.loads((ROOT / "offline-receipt-v3.json").read_text())
    previous_dir = Path.cwd()
    previous_output = os.environ.get("PROFROD_LAB_OUTPUT")
    with tempfile.TemporaryDirectory(prefix="profrod-jev-verify-") as temporary:
        temporary = Path(temporary)
        subprocess.run([sys.executable, str(ROOT / "wake_gate_v3.py"), "--out", str(temporary / "cli")], check=True, cwd=ROOT, stdout=subprocess.PIPE)
        assert json.loads((temporary / "cli/receipt.json").read_text()) == reference
        scope = {}
        executed = copy.deepcopy(notebook)
        observations = []
        try:
            os.chdir(ROOT)
            os.environ["PROFROD_LAB_OUTPUT"] = str(temporary / "notebook")
            for cell in executed["cells"]:
                if cell["cell_type"] != "code":
                    continue
                stream = io.StringIO()
                with contextlib.redirect_stdout(stream):
                    exec(compile("".join(cell["source"]), f"notebook:{cell['id']}", "exec"), scope)
                cell["execution_count"] = len(observations) + 1
                text = stream.getvalue()
                cell["outputs"] = [{"output_type": "stream", "name": "stdout", "text": text.splitlines(keepends=True)}] if text else []
                observations.append({"cell": cell["id"], "status": "PASS", "stdoutSha256": hashlib.sha256(text.encode()).hexdigest()})
            reports = [v for v in scope.values() if isinstance(v, dict) and "threshold_frozen_from_tune" in v and "results" in v]
            assert reports and all(report == reference for report in reports)
            assert len(observations) == 5
        finally:
            os.chdir(previous_dir)
            if previous_output is None:
                os.environ.pop("PROFROD_LAB_OUTPUT", None)
            else:
                os.environ["PROFROD_LAB_OUTPUT"] = previous_output
        receipt = {"sourceNotebookSha256": sha(ROOT / "jev_wake_gate_v7.ipynb"), "helperSha256": sha(ROOT / "wake_gate_v3.py"), "fixtureSha256": sha(ROOT / "synthetic-events-v1.json"), "referenceReceiptSha256": sha(ROOT / "offline-receipt-v3.json"), "pythonVersion": platform.python_version(), "cells": observations, "samePolicyResultsAsCli": True, "modelCalls": 0, "jupyterBrowser": "NOT OBSERVED"}
        destination = os.environ.get("PROFROD_VERIFY_RECEIPT")
        if destination:
            Path(destination).write_text(json.dumps(receipt, indent=2) + "\n")
        print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    verify()
