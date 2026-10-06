"""Chapter14's executable notebook contract; stdlib checks in every PR, real kernels on request.

The student notebooks are deliberately unfinished. The gate executes both untouched and repaired
student cells, separately executes the worked editions, and tests evidence transfer/refusal/export.
Local Python and Linux CI are not an attended Colab browser observation.
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import copy
import hashlib
import io
import json
import linecache
import os
import sys
import tempfile
import types
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "book"
SERVER = BOOK / "textbook/learner/profrod_sovereign_agent_ch14_teaching_server.py"


def paths(asset):
    return sorted((BOOK / asset / "ch14").glob("*.ipynb"))


def source(cell):
    return "".join(cell["source"])


def tagged(notebook, tag):
    return [c for c in notebook["cells"] if tag in c.get("metadata", {}).get("tags", [])]


def structure(notebook):
    for tag in ("runtime-check", "server-source", "embedded-runtime", "learner-owned", "transfer-owned", "course-report", "evidence-export"):
        cells = tagged(notebook, tag)
        assert cells and all(c["cell_type"] == "code" for c in cells), f"{tag} is not executable"
    for tag in ("learner-owned", "transfer-owned"):
        for cell in tagged(notebook, tag):
            tree = ast.parse(source(cell))
            assert any(isinstance(n, ast.FunctionDef) for n in tree.body), "learner definition commented out"
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            ast.parse(source(cell), feature_version=(3, 10))
            assert cell.get("execution_count") is None and not cell.get("outputs"), "publish source, not private execution output"
    assignment = ast.parse(source(tagged(notebook, "server-source")[0])).body[0]
    assert ast.literal_eval(assignment.value) == SERVER.read_text(), "embedded server drift"


def load(path):
    notebook = json.loads(path.read_text())
    structure(notebook)
    kind = "solutions" if notebook["metadata"]["course"]["instructor"] else "student"
    name = path.name.replace("-exercise", "-educator-exercise").replace("-solution", "-educator-solution")
    educator = BOOK / "educator/ch14" / kind / name
    for suffix in (".ipynb", ".md"):
        assert path.with_suffix(suffix).read_bytes() == educator.with_suffix(suffix).read_bytes()
    return notebook


def cells(notebook, namespace, *, stop_tag=None):
    for i, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] != "code":
            continue
        text = source(cell)
        name = f"<ch14-{id(namespace)}-{i}>"
        linecache.cache[name] = (len(text), None, text.splitlines(True), name)
        try:
            exec(compile(text, name, "exec"), namespace)
        except Exception as error:
            raise RuntimeError(f"{notebook['metadata']['course']['unit']} code cell {i}: {error}") from error
        if stop_tag and stop_tag in cell.get("metadata", {}).get("tags", []):
            return


def check_result(namespace, worked):
    assert namespace["VISIBLE_PASSED"] is worked
    assert namespace["TRANSFER_PASSED"] is worked
    assert bool(namespace["connected"]) is worked
    assert namespace["runtime"]["learnerSourceCaptured"] is True
    bundle = namespace["EVIDENCE_ZIP"]
    with zipfile.ZipFile(bundle) as archive:
        saved = json.loads(archive.read(f"{namespace['course_submission']['unit']}-submission-v1.json"))
        assert saved == namespace["course_submission"]
        assert archive.read("teaching_server.py") == SERVER.read_bytes()
        exported = archive.read("learner_code.py").decode()
        for name in namespace["learner_names"]:
            assert f"def {name}(" in exported
        assert json.loads(archive.read("runtime.json"))["modelCalls"] == 0
    if namespace["course_submission"]["unit"] == "ch14-b":
        assert namespace["NEGATIVE_CONTROL"] == "FAILED_AS_EXPECTED"
        assert namespace["grandchild_state"] == "gone", "cleanup left its child alive"
    return bundle.read_bytes()


def repaired(student, solution):
    changed = copy.deepcopy(student)
    answers = {tuple(c.get("metadata", {}).get("tags", [])): source(c) for c in solution["cells"] if "exercise" in c.get("metadata", {}).get("tags", [])}
    count = 0
    for cell in changed["cells"]:
        if "exercise" in cell.get("metadata", {}).get("tags", []):
            cell["source"] = answers[tuple(cell["metadata"]["tags"])]
            count += 1
    assert count == (3 if student["metadata"]["course"]["unit"] == "ch14-a" else 2)
    return changed


def select(notebook, path=None, upload=False):
    changed = copy.deepcopy(notebook)
    cell = tagged(changed, "handoff-selection")[0]
    cell["source"] = f"LEARNER_HANDOFF = {str(path)!r}" if path is not None else "LEARNER_HANDOFF = None"
    cell["source"] += f"\nUPLOAD_HANDOFF = {upload!r}"
    return changed


def expect_failure(call, message):
    try:
        call()
    except (AssertionError, RuntimeError, ValueError):
        return
    raise AssertionError(message)


def colab_adapter(uploaded=None):
    module = types.ModuleType("google.colab")
    downloads = []
    module.files = types.SimpleNamespace(upload=lambda: uploaded, download=lambda p: downloads.append(Path(p).read_bytes()))
    return module, downloads


def verify():
    initial_cwd = Path.cwd()
    students = [load(p) for p in paths("exercises")]
    solutions = [load(p) for p in paths("solutions")]
    try:
        # Fresh environment and same-kernel replay for each untouched and worked notebook.
        for notebook in students + solutions:
            worked = notebook["metadata"]["course"]["instructor"]
            with tempfile.TemporaryDirectory(prefix="ch14-gate-") as folder:
                os.chdir(folder)
                namespace = {"__name__": "__main__"}
                with contextlib.redirect_stdout(io.StringIO()):
                    cells(notebook, namespace)
                    preserved = check_result(namespace, worked)
                    original_zip = namespace["EVIDENCE_ZIP"]
                    cells(notebook, namespace)
                    check_result(namespace, worked)
                assert original_zip != namespace["EVIDENCE_ZIP"] and original_zip.read_bytes() == preserved
            print("PASS fresh/replay/export", notebook["metadata"]["course"]["resource_id"])
        # A learner's repaired cells must work in the actual student notebook, not just solutions.
        with tempfile.TemporaryDirectory(prefix="ch14-handoff-") as folder:
            os.chdir(folder)
            namespace_a = {"__name__": "__main__"}
            with contextlib.redirect_stdout(io.StringIO()):
                cells(repaired(students[0], solutions[0]), namespace_a)
                check_result(namespace_a, True)
                previous_log = namespace_a["log"]
                previous_wire = Path(str(previous_log) + ".wire").read_bytes()
                # The recommended edit -> assessment -> integration -> trace path may run twice.
                repeat = {"metadata": students[0]["metadata"], "cells": tagged(students[0], "integration")}
                cells(repeat, namespace_a)
                assert namespace_a["log"] != previous_log
                assert Path(str(previous_log) + ".wire").read_bytes() == previous_wire
            artifact = namespace_a["ARTIFACT_PATH"].resolve()
            os.chdir(folder)
            relative = artifact.relative_to(Path(folder).resolve())
            namespace_b = {"__name__": "__main__"}
            with contextlib.redirect_stdout(io.StringIO()):
                cells(select(repaired(students[1], solutions[1]), relative), namespace_b)
                check_result(namespace_b, True)
            assert namespace_b["HANDOFF_ORIGIN"] == "LEARNER_SELECTED"
            for invalid_args in ({3: "x"}, {"extra": object()}, {"extra": [float("inf")]}, {"extra": {1, 2}}):
                expect_failure(lambda: namespace_b["require_teaching_schema"]({"type": "object", "properties": {}}, invalid_args), "non-JSON argument accepted")
            for invalid_catalog in ({"tools": [{"name": "x", "inputSchema": {"type": "array"}}]},
                                    {"tools": [{"name": "x", "inputSchema": {"type": "object"}}] * 2},
                                    {"tools": "bad"}, {"tools": [], "nextCursor": "more"}):
                expect_failure(lambda: namespace_b["check_tools"](invalid_catalog), "malformed discovery accepted")
            # The validator must not relabel or accept adversarial/invalid selected evidence.
            valid = json.loads(artifact.read_text())
            for invalid in ([], {}, {**valid, "allowed": ["word_count", "place_purchase"]},
                            {**valid, "status": "INVALID"}, {**valid, "observations": {}}):
                expect_failure(lambda: namespace_b["validate_handoff"](invalid), "invalid handoff accepted")
            bad_path = Path(folder) / "invalid.json"
            bad_path.write_text(json.dumps({**valid, "allowed": ["place_purchase"]}))
            for path in (bad_path, Path(folder) / "missing.json"):
                os.chdir(folder)
                with contextlib.redirect_stdout(io.StringIO()):
                    expect_failure(lambda: cells(select(students[1], path), {"__name__": "__main__"}, stop_tag="handoff-consumer"), "invalid selected path fell back")
            # Real Colab adapter branches, simulated locally: exact upload selection and downloaded bytes.
            adapter, downloads = colab_adapter({"handoff.json": artifact.read_bytes()})
            old_module = sys.modules.get("google.colab")
            sys.modules["google.colab"] = adapter
            try:
                os.chdir(folder)
                uploaded_namespace = {"__name__": "__main__"}
                with contextlib.redirect_stdout(io.StringIO()):
                    cells(select(repaired(students[1], solutions[1]), upload=True), uploaded_namespace)
                    check_result(uploaded_namespace, True)
                assert uploaded_namespace["HANDOFF_ORIGIN"] == "LEARNER_SELECTED"
                assert downloads == [uploaded_namespace["EVIDENCE_ZIP"].read_bytes()]
                adapter.files.upload = lambda: {}
                os.chdir(folder)
                with contextlib.redirect_stdout(io.StringIO()):
                    expect_failure(lambda: cells(select(students[1], upload=True), {}, stop_tag="handoff-consumer"), "empty upload accepted")
            finally:
                if old_module is None:
                    del sys.modules["google.colab"]
                else:
                    sys.modules["google.colab"] = old_module
            # Negative controls: a commented-out learner cell and the unsafe reference answer fail.
            broken = copy.deepcopy(students[0])
            tagged(broken, "learner-owned")[0]["source"] = "# def answer_for(request_id, message): pass"
            expect_failure(lambda: structure(broken), "commented learner definition escaped gate")
            rows = namespace_a["grade_unit"](lambda request_id, message: message.get("result"), lambda name, catalog, allowed: name in catalog)
            assert any(r["status"] == "FAIL" for r in rows)
            # Lifecycle and unsupported schema boundaries are behavioral checks.
            for invalid_schema in ({"type": "array"}, {"type": "object", "oneOf": []}, {"type": "object", "properties": {"x": {"type": "string", "minLength": 2}}}):
                expect_failure(lambda: namespace_b["require_teaching_schema"](invalid_schema, {}), "unsupported schema accepted")
            with namespace_a["Client"](namespace_a["server_command"]("normal", Path(folder) / "early.log"), allowed={"word_count"}) as client:
                expect_failure(client.list_tools, "discovery before initialize accepted")
                assert not (Path(folder) / "early.log.wire").exists()
                client.initialize()
                expect_failure(client.initialize, "duplicate initialize accepted")
            with namespace_b["Client"](namespace_b["server_command"]("wrong-id", Path(folder) / "broken.log"), allowed={"word_count"}) as client:
                client.initialize(); client.list_tools()
                expect_failure(lambda: client.call_tool("word_count", {"text": "one"}), "wrong-id accepted")
                assert client.state == "BROKEN"
                expect_failure(lambda: client.request("tools/list", {}), "failed stream reused")
        print("PASS repaired students, relative/invalid/missing/uploaded handoffs, exact download, negative controls, lifecycle/schema bounds")
    finally:
        os.chdir(initial_cwd)


def record_kernels():
    import verify_course_v1 as course
    assert sys.version_info[:2] == (3, 12), "receipt is recorded on pinned Python3.12"
    rows = [course.execute_one(p) for p in paths("exercises") + paths("solutions")]
    handoff = course.execute_handoff(14)
    prior_path = ROOT / "docs/evidence/book-four-assets/verification-v6.json"
    prior = json.loads(prior_path.read_text())
    for row in prior["notebooks"]:
        if not row["id"].startswith("ch14-"):
            for field in ("notebook", "markdown"):
                assert course.digest(BOOK / row[field]) == row[field + "Sha256"], "cannot inherit changed bytes"
    current = copy.deepcopy(prior)
    current["created"] = "2026-10-06"
    current["python"] = sys.version.split()[0]
    current["inheritedFrom"] = {"path": prior_path.name, "sha256": course.digest(prior_path), "notebookCount": 80, "handoffCount": 20}
    current["reexecutedChapters"] = [14]
    replacement = {(r["id"], r["asset"]): r for r in rows}
    current["notebooks"] = [replacement.get((r["id"], r["asset"]), r) for r in prior["notebooks"]]
    current["handoffs"] = [handoff if r["chapter"] == 14 else r for r in prior["handoffs"]]
    current["limits"] = ["Only Chapter14's four notebooks and handoff re-executed on Python3.12; other80 notebooks/20 handoffs inherit exact historical v6 evidence.", "Local Jupyter kernels and Linux CI do not establish attended hosted Colab or classroom comprehension.", "Ninety minutes is planned, not measured."]
    with course.RECEIPT.open("x") as stream:
        stream.write(json.dumps(current, indent=2, sort_keys=True) + "\n")
    course.verify_receipt()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record-kernels", action="store_true")
    args = parser.parse_args()
    verify()
    if args.record_kernels:
        record_kernels()
