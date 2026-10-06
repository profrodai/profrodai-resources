"""Verify the Sovereign Agent book's course: exercises, solutions, educator copies and chapter code.

Ported from sovereign-agent's scripts/verify_book_assets_v2.py at 03b67411 when the course moved
here (see SOURCE.md). The chapters themselves now live only on https://profrod.ai/book, so this
gate checks what this folder holds:

  (default)          the layout and the receipt: every notebook's exact bytes were executed
  --code             every chapter checkpoint runs against the pinned sovereign-agent package
  --execute          run every exercise and solution in fresh kernels, replay each in the same
                     kernel, check every A-to-B handoff, and write the receipt (append-only)
  --check-execution  the same runs, compared against the saved receipt without rewriting it

A green gate is not publication or classroom acceptance; ninety minutes is a teaching plan.
"""

from __future__ import annotations

import argparse
import ast
import concurrent.futures
import hashlib
import json
import platform
import re
import runpy
import subprocess
import sys
import tempfile
from pathlib import Path

if __package__:
    from . import book_distribution_v1 as distribution
    from . import check_colab_v1 as colab
else:
    import book_distribution_v1 as distribution
    import check_colab_v1 as colab


ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "book"
COURSE = ("exercises", "solutions", "educator")
PLANNED: set[int] = set()
AVAILABLE = set(range(1, 22)) - PLANNED
EXPECTED = {f"ch{chapter:02d}-{letter}" for chapter in AVAILABLE for letter in "ab"}
# v5 recorded Python 3.14 kernels. v6 records Colab's Python, which is what readers run.
RECEIPT = ROOT / "docs/evidence/book-four-assets/verification-v9.json"
LEGACY = runpy.run_path(str(ROOT / "scripts/verify_practical_course_v1.py"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_file(book: Path, relative: str) -> Path:
    candidate = book / relative
    assert not Path(relative).is_absolute() and ".." not in Path(relative).parts, relative
    assert candidate.is_file() and not candidate.is_symlink(), relative
    assert candidate.resolve().is_relative_to(book.resolve()), relative
    return candidate


def notebook_paths(book: Path = BOOK) -> list[Path]:
    return sorted(
        path for asset in ("exercises", "solutions") for path in (book / asset).glob("ch*/*.ipynb")
    )


def verify_layout(book: Path = BOOK) -> dict:
    assert {p.name for p in book.iterdir() if p.is_dir()} == {*COURSE, "textbook"}, (
        "book/ holds the three course audiences and the chapter code"
    )
    assert not list((book / "textbook").glob("ch[0-9]*")), "chapter prose lives on profrod.ai/book"
    distribution.verify_unique_names(book)
    manifest = json.loads(local_file(book, "textbook/BOOK.json").read_text())
    assert manifest["schemaVersion"] == 3
    chapters = manifest["chapters"]
    assert [row["number"] for row in chapters] == list(range(1, 22)), "chapter coverage drift"
    assert len({row["lessonId"] for row in chapters}) == 21, "duplicate stable lesson identity"
    assert {row["number"] for row in chapters if row["status"] == "PLANNED"} == PLANNED
    for asset in COURSE:
        local_file(book, f"{asset}/README.md")
        local_file(book, f"{asset}/{distribution.start_name(asset)}")
        actual = {p.name for p in (book / asset).glob("ch[0-9]*") if p.is_dir()}
        assert actual == {f"ch{n:02d}" for n in range(1, 22)}, f"{asset}: chapter coverage drift"
    for row in chapters:
        chapter = row["number"]
        prefix = f"ch{chapter:02d}"
        assert row["status"] in {"DRAFT", "PLANNED"}, "publication acceptance is not established"
        for asset in COURSE:
            readme = local_file(book, f"{asset}/{prefix}/{distribution.chapter_name(chapter, asset)}")
            if chapter in PLANNED:
                assert "PLANNED" in readme.read_text(), f"{readme}: planned status is hidden"
                assert not any(
                    p.suffix in {".ipynb", ".py", ".zip"} for p in readme.parent.rglob("*")
                ), f"{readme}: planned chapter ships fake executable material"
        if chapter in PLANNED:
            assert row["checkpoint"] is None
            continue
        assert row["checkpoint"] == f"checkpoints/{distribution.checkpoint_name(chapter)}"
        local_file(book, f"textbook/{row['checkpoint']}")
        local_file(book, f"educator/{prefix}/{distribution.guide_name(chapter)}")
        for asset in ("exercises", "solutions"):
            expected_names = {distribution.unit_name(chapter, letter, asset) for letter in "ab"}
            assert {p.name for p in (book / asset / prefix).glob("*.ipynb")} == expected_names
            for letter in "ab":
                path = distribution.unit_path(book, chapter, letter, asset)
                local_file(book, str(path.with_suffix(".md").relative_to(book)))
                notebook = json.loads(path.read_text())
                course = notebook["metadata"]["course"]
                assert course["unit"] == f"{prefix}-{letter}", "notebook chapter identity drift"
                assert course["resource_id"] == path.stem, "resource name drift"
                assert course["book_url"] == distribution.BOOK_URL
                assert course["community_url"] == distribution.COMMUNITY_URL
                assert course["source_url"] == distribution.SOURCE_URL
                header = "".join(notebook["cells"][0]["source"])
                footer = "".join(notebook["cells"][-1]["source"])
                distribution.verify_attribution(header)
                assert "Keep building with Prof Rod" in footer, "missing closing invitation"
                assert course["planned_minutes"] == 90
                assert course["instructor"] is (asset == "solutions"), "solution distribution leak"
                tags = {
                    tag for cell in notebook["cells"] for tag in cell.get("metadata", {}).get("tags", [])
                }
                assert {"embedded-runtime", "learner-owned", "transfer-owned", "course-report"} <= tags
                assert ("instructor-check" in tags) is (asset == "solutions")
                educator_kind = "solutions" if asset == "solutions" else "student"
                for suffix in (".ipynb", ".md"):
                    educator_copy = local_file(
                        book,
                        f"educator/{prefix}/{educator_kind}/"
                        + str(
                            Path(distribution.unit_name(chapter, letter, asset, educator=True)).with_suffix(
                                suffix
                            )
                        ),
                    )
                    assert educator_copy.read_bytes() == path.with_suffix(suffix).read_bytes(), (
                        "educator teaching copy diverged from its companion",
                        educator_copy,
                    )
                # Every exercise and every worked solution opens itself on Colab.
                badge_url = (
                    "colab.research.google.com/github/profrodai/profrodai-resources/blob/main/"
                    f"courses/sovereign-agent-book/{path.relative_to(ROOT)}"
                )
                assert badge_url in path.with_suffix(".md").read_text(), (
                    "the notebook's Colab badge must open this very notebook",
                    path,
                )
    for path in book.rglob("*.md"):
        distribution.verify_attribution(path.read_text())
    for pattern in ("*.py", "*.toml"):
        for path in book.rglob(pattern):
            source = path.read_text()
            assert "Join the Prof Rod learner community" in source, path
            for url in (distribution.BOOK_URL, distribution.COMMUNITY_URL, distribution.SOURCE_URL):
                assert url in source, path
    assert len(notebook_paths(book)) == 84
    failures = colab.colab_failures(book)
    assert not failures, "not ready for Colab's Python 3.12:\n" + "\n".join(failures)
    return manifest


# Chapters whose checkpoint builds only on the standard library, locked dependencies and the
# learner's own files. The book promises every chapter joins this set; none may leave it.
SUPPLIED = ("sovereign_agent", "reference_organizations")
# Runs a checkpoint as its own script would run, with the supplied packages refused on import,
# so a file the checkpoint loads indirectly cannot bring them back either.
FROM_SCRATCH_RUNNER = """
import runpy, sys
class Refuse:
    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] in {supplied!r}:
            raise ImportError(name + " is supplied code; this chapter builds from learner files")
sys.meta_path.insert(0, Refuse())
sys.argv = [{path!r}]
sys.path[0] = {folder!r}
runpy.run_path({path!r}, run_name="__main__")
"""


def supplied_imports(chapter: int) -> list[str]:
    """Import lines naming a supplied package, in a chapter's checkpoint and learner files. This
    catches what the import hook cannot: a supplied import on a path the checkpoint never runs,
    such as a live-model branch."""
    textbook = BOOK / "textbook"
    files = [*textbook.glob(f"checkpoints/*_ch{chapter:02d}_*.py")]
    files += textbook.glob(f"learner/*_ch{chapter:02d}_*.py")
    pattern = re.compile(r"^\s*(from|import)\s+(" + "|".join(SUPPLIED) + r")\b")
    return [
        f"{path.name}:{number}"
        for path in files
        for number, line in enumerate(path.read_text().splitlines(), 1)
        if pattern.match(line)
    ]


def verify_code() -> None:
    """Every course Python file parses on Colab's Python; every drafted chapter's checkpoint
    runs from the course root with the supplied packages refused. Every chapter builds from
    scratch, and a new one must too."""
    manifest = verify_layout()
    ran = 0
    for row in manifest["chapters"]:
        if row["status"] == "PLANNED":
            continue
        path = BOOK / "textbook" / row["checkpoint"]
        found = supplied_imports(row["number"])
        assert not found, f"chapter {row['number']} imports supplied code: {found}"
        runner = FROM_SCRATCH_RUNNER.format(
            supplied=set(SUPPLIED), path=str(path), folder=str(path.parent)
        )
        subprocess.run([sys.executable, "-c", runner], cwd=ROOT, check=True, timeout=120)
        ran += 1
    print(
        f"CHAPTER CODE: {ran} checkpoints ran, every one on learner code alone, with the "
        f"supplied packages refused on import. Every course "
        f"Python file and notebook parses as Python {colab.COLAB_PYTHON[0]}."
        f"{colab.COLAB_PYTHON[1]}, Colab's runtime."
    )


def execute_one(path: Path) -> dict:
    import jupytext
    import nbformat

    notebook_hash = digest(path)
    markdown_hash = digest(path.with_suffix(".md"))
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    assert LEGACY["semantics"](notebook) == LEGACY["semantics"](jupytext.read(path.with_suffix(".md")))
    identity = notebook.metadata.course.unit
    instructor = notebook.metadata.course.instructor
    assert identity in EXPECTED
    with tempfile.TemporaryDirectory(prefix=f"course-{identity}-") as folder:
        executed = LEGACY["run_notebook"](notebook, folder)
        if identity.startswith("ch14-"):
            kernel_versions = [
                line.removeprefix("Python ").strip()
                for cell in executed.cells for output in cell.get("outputs", [])
                for line in "".join(output.get("text", "")).splitlines()
                if line.startswith("Python ")
            ]
            assert kernel_versions == [platform.python_version()], (
                "the executed kernel must use the receipt interpreter", kernel_versions
            )
        observed = LEGACY["report"](executed)
        assert observed["unit"] == identity
        assert observed["transfer_passed"] is instructor
        assert observed["starting_evidence"] == (
            "SUPPLIED_REFERENCE" if identity.endswith("b") else "INDEPENDENT_UNIT_A"
        )
        if instructor:
            assert LEGACY["report"](executed, "HOLDOUT_RESULT=") == {"unit": identity, "status": "PASSED"}
        submissions = list((Path(folder) / "practical-work" / identity).rglob(f"{identity}-submission-v1.json"))
        assert len(submissions) == 1, submissions
        saved = json.loads(submissions[0].read_text())
        assert saved["unit"] == identity and len(saved["transfer"]) >= 4
        assert all(item["passed"] for item in saved["transfer"]) is instructor
    with tempfile.TemporaryDirectory(prefix=f"course-replay-{identity}-") as folder:
        LEGACY["run_notebook"](notebook, folder, replay=True)
    assert digest(path) == notebook_hash and digest(path.with_suffix(".md")) == markdown_hash, (
        "notebook sources changed during execution",
        path,
    )
    print("VERIFIED", identity, "solution" if instructor else "exercise", flush=True)
    return {
        "id": identity,
        "asset": "solutions" if instructor else "exercises",
        "notebook": str(path.relative_to(BOOK)),
        "notebookSha256": notebook_hash,
        "markdown": str(path.with_suffix(".md").relative_to(BOOK)),
        "markdownSha256": markdown_hash,
        "freshKernel": "PASS",
        "sameKernelReplay": "PASS",
        "markdownParity": "PASS",
        "embeddedImports": "PASS",
        "transfer": "PASS" if instructor else "EXPECTED_UNFINISHED",
        "coreHoldout": "PASS" if instructor else "NOT_DISTRIBUTED",
    }


def execute_handoff(chapter: int) -> dict:
    import nbformat

    unit_a = nbformat.read(distribution.unit_path(BOOK, chapter, "a", "solutions"), as_version=4)
    unit_b = nbformat.read(distribution.unit_path(BOOK, chapter, "b", "solutions"), as_version=4)
    with tempfile.TemporaryDirectory(prefix=f"course-handoff-{chapter}-") as temporary:
        LEGACY["run_notebook"](unit_a, temporary)
        artifacts = list((Path(temporary) / f"practical-work/ch{chapter:02d}-a").rglob(f"ch{chapter:02d}-unit-a-handoff-v1.json"))
        assert len(artifacts) == 1, artifacts
        artifact = artifacts[0]
        assert artifact.is_file(), artifact
        replacements = 0
        for cell in unit_b.cells:
            if cell.cell_type == "code" and "LEARNER_HANDOFF = None" in cell.source:
                cell.source = cell.source.replace("LEARNER_HANDOFF = None", f"LEARNER_HANDOFF = {str(artifact)!r}")
                replacements += 1
        assert replacements == 1
        executed = LEGACY["run_notebook"](unit_b, temporary)
        observed = LEGACY["report"](executed)
        assert observed["starting_evidence"] == "LEARNER_SELECTED"
        assert observed["transfer_passed"] is True
    print("HANDOFF VERIFIED", chapter, flush=True)
    return {"chapter": chapter, "selectedLearnerHandoff": "PASS"}


def verify_receipt(path: Path = RECEIPT, book: Path = BOOK) -> None:
    verify_layout(book)
    receipt = json.loads(path.read_text())
    assert receipt["schemaVersion"] == 1 and receipt["edition"] == "four-assets-21-chapters"
    if "inheritedFrom" in receipt:
        inherited = receipt["inheritedFrom"]
        prior_path = ROOT / "docs/evidence/book-four-assets/verification-v6.json"
        assert inherited["sha256"] == digest(prior_path), "historical receipt changed"
        prior = json.loads(prior_path.read_text())
        assert inherited["notebookCount"] == 80 and inherited["handoffCount"] == 20
        assert receipt["reexecutedChapters"] == [14]
        assert [r for r in receipt["notebooks"] if not r["id"].startswith("ch14-")] == [
            r for r in prior["notebooks"] if not r["id"].startswith("ch14-")
        ], "unchanged chapter evidence must be inherited verbatim"
        assert [r for r in receipt["handoffs"] if r["chapter"] != 14] == [
            r for r in prior["handoffs"] if r["chapter"] != 14
        ]
    assert receipt["python"].startswith("{}.{}.".format(*colab.COLAB_PYTHON)), (
        "the receipt must record execution on Colab's Python",
        receipt["python"],
    )
    rows = receipt["notebooks"]
    assert len(rows) == 84 and {(row["id"], row["asset"]) for row in rows} == {
        (identity, asset) for identity in EXPECTED for asset in ("exercises", "solutions")
    }, "notebook coverage drift"
    assert {str(p.relative_to(book)) for p in notebook_paths(book)} == {row["notebook"] for row in rows}
    assert len(receipt["handoffs"]) == 21
    assert {row["chapter"] for row in receipt["handoffs"]} == AVAILABLE
    assert all(row["selectedLearnerHandoff"] == "PASS" for row in receipt["handoffs"])
    for row in rows:
        assert row["notebook"] == str(
            distribution.unit_path(book, int(row["id"][2:4]), row["id"][-1], row["asset"]).relative_to(book)
        )
        assert row["markdown"] == str(Path(row["notebook"]).with_suffix(".md"))
        for proof in ("freshKernel", "sameKernelReplay", "markdownParity", "embeddedImports"):
            assert row[proof] == "PASS", f"notebook {proof} missing"
        assert row["transfer"] == ("PASS" if row["asset"] == "solutions" else "EXPECTED_UNFINISHED")
        assert row["coreHoldout"] == ("PASS" if row["asset"] == "solutions" else "NOT_DISTRIBUTED")
        for field in ("notebook", "markdown"):
            assert digest(local_file(book, row[field])) == row[field + "Sha256"], "verified bytes changed"
    print("COURSE: 42 exercise units, 42 solutions, 21 selected handoffs; exact executed bytes intact.")


def execute(workers: int, *, record: bool = True) -> None:
    # Execution is evidence about what readers run, so it happens on Colab's Python or not at all.
    if sys.version_info[:2] != colab.COLAB_PYTHON:
        raise SystemExit(
            "Execute the notebooks on Python {}.{}, Colab's version: make record-execution "
            "or make verify-execution.".format(*colab.COLAB_PYTHON)
        )
    verify_layout()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        notebooks = list(pool.map(execute_one, notebook_paths()))
        handoffs = list(pool.map(execute_handoff, sorted(AVAILABLE)))
    receipt = {
        "schemaVersion": 1,
        "edition": "four-assets-21-chapters",
        "created": "2026-09-29",
        "source": "profrodai/sovereign-agent@03b67411133409f6c897461639c704ec27264fa9, re-homed",
        "python": platform.python_version(),
        "notebooks": notebooks,
        "handoffs": handoffs,
        "limits": [
            "Ninety minutes is a teaching plan, not measured classroom duration.",
            "Offline execution does not certify real phone delivery or host operation.",
            "Executed on Python 3.12, the version Google Colab runs; the Colab interface itself "
            "was not driven.",
        ],
    }
    if not record:
        verify_receipt()
        print("COURSE: all notebooks and handoffs freshly re-executed; receipt unchanged.")
        return
    # A receipt is append-only: remove an unpublished failed draft before rerunning, or write a
    # successor verifier for a later release.
    with RECEIPT.open("x") as output:
        output.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    verify_receipt()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--check-execution", action="store_true")
    parser.add_argument("--code", action="store_true")
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    if args.execute:
        execute(args.workers)
    elif args.check_execution:
        execute(args.workers, record=False)
    elif args.code:
        verify_code()
    else:
        verify_receipt()
