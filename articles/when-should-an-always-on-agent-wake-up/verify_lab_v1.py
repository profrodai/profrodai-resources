"""Run the Colab entry path, offline replay and failure controls; no model calls.

Default verification mocks public downloads with the pinned local bytes. Pass
--network for an additional real public-download smoke in an empty directory.
Neither execution mode claims an attended hosted-Colab browser observation.
"""
import argparse
import ast
import contextlib
import copy
import hashlib
import io
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import types
import urllib.request
import zipfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
SOURCE_COMMIT = "9c7a224f9ee334085e480911297276651c9cc18d"
BASE_URL = ("https://raw.githubusercontent.com/profrodai/profrodai-resources/"
            + SOURCE_COMMIT + "/articles/when-should-an-always-on-agent-wake-up/")
SOURCES = ("wake_gate_v3.py", "synthetic-events-v1.json", "offline-receipt-v3.json")
CODE_IDS = {"setup", "answers", "tuning", "canonical", "intervention", "probability-audit",
            "costs", "trusted-boundary", "interface", "journal", "export"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def same_receipt(actual, expected, location="receipt"):
    """Keep discrete policy evidence exact; permit only floating rounding noise."""
    assert type(actual) is type(expected), f"{location}: type changed"
    if isinstance(expected, dict):
        assert actual.keys() == expected.keys(), f"{location}: keys changed"
        for key in expected:
            same_receipt(actual[key], expected[key], f"{location}.{key}")
    elif isinstance(expected, list):
        assert len(actual) == len(expected), f"{location}: length changed"
        for index, (value, reference) in enumerate(zip(actual, expected)):
            same_receipt(value, reference, f"{location}[{index}]")
    elif isinstance(expected, float):
        # Python 3.12 changed float sum accuracy. The pinned 3.10 and 3.14
        # Brier scores differ by 3e-17; this does not change any routing result.
        assert math.isfinite(actual) and math.isfinite(expected)
        assert math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12), f"{location}: value changed"
    else:
        assert actual == expected, f"{location}: value changed"


def verify_comparison_controls(reference):
    same_receipt(reference, reference)
    for key, value in [("binary_brier_score", reference["results"]["test"]["binary_brier_score"] + 1e-6),
                       ("missed_important_events", 0),
                       ("synthetic_cascade_cost_cents", 600)]:
        changed = copy.deepcopy(reference)
        changed["results"]["test"][key] = value
        try:
            same_receipt(changed, reference)
        except AssertionError:
            continue
        raise AssertionError(f"Comparison accepted changed {key}")


def verify_export(scope, reference, temporary):
    """The learner can retain a complete, source-bound experiment after disconnect."""
    archive_path = scope["EXPORT_ZIP"]
    expected = {"bootstrap-manifest.json", "interventions.json", "probability-audit.json",
                "boundary-observations.json", "journal-observations.json", "learner-answers.json",
                "runtime.json", "canonical/receipt.json", "canonical/inbox.sqlite3",
                "journal-demo.sqlite3"} | {"source/" + name for name in SOURCES}
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == expected
        for name in SOURCES:
            assert archive.read("source/" + name) == (ROOT / name).read_bytes()
        same_receipt(json.loads(archive.read("canonical/receipt.json")), reference)
        intervention = json.loads(archive.read("interventions.json"))
        assert intervention["used_test_labels"] and not intervention["is_new_held_out_evaluation"]
        assert intervention["result"]["missed_important_events"] == 0
        assert intervention["cost"]["total_cents"] == 552
        assert intervention["cost"]["important_misses"] == 1
        assert intervention["cost"]["break_even_review_cents"] == 44.0
        audit = json.loads(archive.read("probability-audit.json"))
        assert len(audit["judgments"]) == 18 and len(audit["excluded"]) == 6
        assert {item["reason"] for item in audit["excluded"]} == {
            "trusted bypass: judgment not attempted", "missing or malformed probability", "ambiguous label"}
        observations = json.loads(archive.read("journal-observations.json"))
        assert [observations[key] for key in ["before_deciding", "after_deciding_before_recording",
                                            "after_recording_before_action", "after_reopening"]] == [0, 0, 1, 1]
        assert observations["duplicate"] == "duplicate" and observations["conflict_rejected"]
        for key in ["durable_admission_implemented", "downstream_action_executed", "process_crash_tested"]:
            assert observations[key] is False
        assert json.loads(archive.read("learner-answers.json")) == scope["learner_answers"]
        assert json.loads(archive.read("runtime.json"))["model_calls"] == 0
        # Check saved databases, not merely the notebook's printed row-count claim.
        import sqlite3
        for member, rows in [("canonical/inbox.sqlite3", 24), ("journal-demo.sqlite3", 1)]:
            path = temporary / (uuid_name() + ".sqlite3")
            path.write_bytes(archive.read(member))
            with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as db:
                assert db.execute("SELECT COUNT(*) FROM inbox").fetchone()[0] == rows
    return {"members": len(expected), "sha256": sha(archive_path)}


def uuid_name():
    import uuid
    return uuid.uuid4().hex


def run_cells(notebook, work, assets, output, mode, emulate_colab=False, setup_only=False):
    requests, downloads, observations = [], [], []
    scope = {}
    original_urlopen = urllib.request.urlopen

    def acquire(url, *args, **kwargs):
        assert url in {BASE_URL + name for name in SOURCES}, "Unexpected network destination"
        requests.append(url)
        if mode == "offline":
            raise AssertionError("Cached/sibling replay attempted a network download")
        if mode == "failed":
            raise OSError("Injected acquisition failure")
        if mode == "network":
            return original_urlopen(url, *args, **kwargs)
        name = url.rsplit("/", 1)[1]
        content = (ROOT / name).read_bytes()
        if mode == "tampered":
            content += b"\n# changed teaching bytes"
        return io.BytesIO(content)

    def download(path):
        assert Path(path).is_file()
        downloads.append(path)

    work.mkdir(parents=True, exist_ok=True)
    google = types.ModuleType("google")
    google.__path__ = []
    colab = types.ModuleType("google.colab")
    colab.files = types.SimpleNamespace(download=download)
    stubs = {"google": google, "google.colab": colab} if emulate_colab else {}
    previous = Path.cwd()
    try:
        os.chdir(work)
        with patch.dict(os.environ, {"PROFROD_LAB_ASSETS": str(assets), "PROFROD_LAB_OUTPUT": str(output)}), \
             patch.object(urllib.request, "urlopen", acquire), patch.dict(sys.modules, stubs):
            for cell in notebook["cells"]:
                if cell["cell_type"] != "code":
                    continue
                if setup_only and cell["id"] != "setup":
                    continue
                stream = io.StringIO()
                source = "".join(cell["source"])
                ast.parse(source, feature_version=(3, 10))
                with contextlib.redirect_stdout(stream):
                    exec(compile(source, f"notebook:{cell['id']}", "exec"), scope)
                observations.append({"cell": cell["id"], "status": "PASS",
                                     "stdoutSha256": hashlib.sha256(stream.getvalue().encode()).hexdigest()})
            if not setup_only:
                # Colab readers rerun individual cells while exploring. The
                # canonical cell must allocate another output, not require a
                # runtime restart or overwrite the previous receipt/database.
                previous_canonical = scope["CANONICAL_DIR"]
                previous_receipt_sha = sha(previous_canonical / "receipt.json")
                previous_database_sha = sha(previous_canonical / "inbox.sqlite3")
                previous_zip = scope["EXPORT_ZIP"]
                previous_zip_sha = sha(previous_zip)
                for ident in ["canonical", "export"]:
                    cell = next(cell for cell in notebook["cells"] if cell["id"] == ident)
                    with contextlib.redirect_stdout(io.StringIO()):
                        exec(compile("".join(cell["source"]), "rerun:" + ident, "exec"), scope)
                assert scope["CANONICAL_DIR"] != previous_canonical
                assert sha(previous_canonical / "receipt.json") == previous_receipt_sha
                assert sha(previous_canonical / "inbox.sqlite3") == previous_database_sha
                assert sha(previous_zip) == previous_zip_sha
    finally:
        os.chdir(previous)
    return scope, {"cells": observations, "requests": requests, "download_adapter_calls": len(downloads),
                   "canonical_cell_rerun_preserves_previous_evidence": not setup_only}


def verify(network=False):
    notebook = json.loads((ROOT / "jev_wake_gate_v7.ipynb").read_text())
    assert notebook["metadata"]["profrod"]["helperSha256"] == sha(ROOT / SOURCES[0])
    assert notebook["metadata"]["profrod"]["fixtureSha256"] == sha(ROOT / SOURCES[1])
    assert notebook["metadata"]["profrod"]["referenceReceiptSha256"] == sha(ROOT / SOURCES[2])
    assert notebook["metadata"]["profrod"]["sourceCommit"] == SOURCE_COMMIT
    ids = [cell["id"] for cell in notebook["cells"]]
    assert len(ids) == len(set(ids))
    assert {cell["id"] for cell in notebook["cells"] if cell["cell_type"] == "code"} == CODE_IDS
    assert notebook["metadata"]["kernelspec"]["display_name"] == "Python 3"
    reference = json.loads((ROOT / "offline-receipt-v3.json").read_text())
    verify_comparison_controls(reference)
    with tempfile.TemporaryDirectory(prefix="profrod-jev-verify-") as temporary:
        temporary = Path(temporary)
        subprocess.run([sys.executable, str(ROOT / "wake_gate_v3.py"), "--out", str(temporary / "cli")],
                       check=True, cwd=ROOT, stdout=subprocess.PIPE)
        same_receipt(json.loads((temporary / "cli/receipt.json").read_text()), reference)
        assets, output = temporary / "cache", temporary / "runs"
        # This path reproduces Colab's crucial property: there are no sibling files.
        fresh, fresh_checks = run_cells(notebook, temporary / "empty", assets, output, "mock", emulate_colab=True)
        assert fresh_checks["requests"] == [BASE_URL + name for name in SOURCES]
        assert fresh_checks["download_adapter_calls"] == 2  # Run all, then one canonical/export rerun.
        assert len(fresh_checks["cells"]) == len(CODE_IDS)
        same_receipt(fresh["report"], reference)
        assert fresh["lab"].route(fresh["trap"], 0.05)[0] == "review"
        archive = verify_export(fresh, reference, temporary)
        prior_zip_sha = sha(fresh["EXPORT_ZIP"])
        cached, cached_checks = run_cells(notebook, temporary / "empty", assets, output, "offline")
        assert not cached_checks["requests"]
        assert cached["SESSION_DIR"] != fresh["SESSION_DIR"]
        assert sha(fresh["EXPORT_ZIP"]) == prior_zip_sha
        same_receipt(cached["report"], reference)
        verify_export(cached, reference, temporary)
        # A local notebook beside original files also requires no network.
        sibling, sibling_checks = run_cells(notebook, ROOT, temporary / "sibling-cache",
                                           temporary / "sibling-runs", "offline")
        assert not sibling_checks["requests"]
        same_receipt(sibling["report"], reference)
        failure_controls = {}
        for mode in ["failed", "tampered", "corrupt-cache"]:
            damaged = temporary / mode
            damaged.mkdir()
            if mode == "corrupt-cache":
                (damaged / SOURCES[0]).write_bytes(b"raise RuntimeError('do not import me')")
            try:
                run_cells(notebook, temporary / "no-siblings", damaged, temporary / "bad-runs",
                          "offline" if mode == "corrupt-cache" else mode, setup_only=True)
            except RuntimeError as error:
                assert ("Could not fetch" if mode == "failed" else "Changed teaching artifact") in str(error)
                assert not (temporary / "bad-runs").exists(), "Failure reached run creation"
                failure_controls[mode] = "REJECTED before helper import"
            else:
                raise AssertionError("Invalid acquisition accepted: " + mode)
        network_checks = {"status": "NOT RUN"}
        if network:
            online, network_checks = run_cells(notebook, temporary / "public-empty", temporary / "public-cache",
                                              temporary / "public-runs", "network")
            assert network_checks["requests"] == [BASE_URL + name for name in SOURCES]
            same_receipt(online["report"], reference)
            verify_export(online, reference, temporary)
            network_checks["status"] = "PASS: real public acquisition; no hosted Colab session"
        receipt = {"sourceNotebookSha256": sha(ROOT / "jev_wake_gate_v7.ipynb"),
                   "helperSha256": sha(ROOT / SOURCES[0]), "fixtureSha256": sha(ROOT / SOURCES[1]),
                   "referenceReceiptSha256": sha(ROOT / SOURCES[2]), "pythonVersion": platform.python_version(),
                   "fresh_empty_runtime": fresh_checks, "offline_cached_replay": cached_checks,
                   "local_sibling_replay": sibling_checks, "prior_run_preserved": True,
                   "export": archive, "failure_controls": failure_controls, "public_download_smoke": network_checks,
                   "samePolicyResultsAsCli": True, "modelCalls": 0,
                   "colab_download_adapter": "SIMULATED; archive inspected",
                   "hosted_colab_browser": "NOT OBSERVED"}
    destination = os.environ.get("PROFROD_VERIFY_RECEIPT")
    if destination:
        Path(destination).write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--network", action="store_true", help="Also acquire the pinned public files in an empty directory")
    verify(parser.parse_args().network)
