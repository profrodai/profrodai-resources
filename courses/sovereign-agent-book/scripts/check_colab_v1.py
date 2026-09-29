# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Everything a reader opens on Google Colab must run on Colab's Python.

Checks, with the standard library only, that every course Python file and every notebook in the
book parses as Python 3.12, declares no other Python, demands no newer one, and carries an embedded
runtime whose Python files parse too. The course gate imports these checks; the repository's
verify-pr target runs this file directly, so a future notebook cannot land without them.

    python3 courses/sovereign-agent-book/scripts/check_colab_v1.py
"""

from __future__ import annotations

import ast
import base64
import json
import re
import sys
import zlib
from pathlib import Path

BOOK = Path(__file__).resolve().parents[1] / "book"

# Google Colab is where most readers run this code, and its runtime is Python 3.12 (Colab's
# 2026.07 runtime ships 3.12.13). The course itself runs on 3.14, whose parser accepts syntax
# 3.12 refuses, so a file that passes here can still fail on Colab before its first line.
COLAB_PYTHON = (3, 12)


NEWER_THAN_COLAB = re.compile(
    r"(?:minimum_python\s*=|version_info(?:\[:2\])?\s*>=?)\s*\(3,\s*(1[3-9]|[2-9]\d)\)"
)


MAGIC = re.compile(r"\s*(?:%|!(?!=))")


def colab_parse_failures(book: Path = BOOK) -> list[str]:
    """Every course Python file a reader may run, parsed as Colab's Python would parse it."""
    failures = []
    for path in sorted((book / "textbook").rglob("*.py")):
        try:
            ast.parse(path.read_text(), str(path), feature_version=COLAB_PYTHON)
        except SyntaxError as error:
            failures.append(f"{path.relative_to(book)}:{error.lineno}: {error.msg}")
    return failures


def colab_notebook_failures(path: Path, book: Path = BOOK) -> list[str]:
    """One notebook as Colab would run it: its declared Python, any demand for a newer one, its
    code cells and the Python files inside its embedded runtime, parsed as Python 3.12."""
    name = str(path.relative_to(book))
    notebook = json.loads(path.read_text())
    failures = []
    declared = notebook["metadata"].get("language_info", {}).get("version")
    shown = notebook["metadata"].get("kernelspec", {}).get("display_name", "Python 3")
    if declared not in (None, "{}.{}".format(*COLAB_PYTHON)) or shown != "Python 3":
        failures.append(f"{name}: declares Python {declared!r} / kernel {shown!r}, not Colab's")
    for index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] != "code":
            continue
        source = "".join(cell["source"])
        if NEWER_THAN_COLAB.search(source):
            failures.append(f"{name} cell {index}: requires a Python newer than Colab's")
        # IPython magics and shell escapes (%pip, !git) are not Python; "!=" is.
        code = "\n".join("pass" if MAGIC.match(line) else line for line in source.splitlines())
        try:
            ast.parse(code, feature_version=COLAB_PYTHON)
        except SyntaxError as error:
            failures.append(f"{name} cell {index}:{error.lineno}: {error.msg}")
        reference = re.search(r"reference_encoded = \(\n(.*?)\n\s*\)", source, re.S)
        if reference:
            # Unit B notebooks exec their Unit A reference from compressed source.
            literal = "".join(re.findall(r'"([^"]*)"', reference.group(1)))
            code = zlib.decompress(base64.b85decode(literal)).decode()
            if NEWER_THAN_COLAB.search(code):
                failures.append(f"{name} cell {index}: its reference requires a newer Python")
            try:
                ast.parse(code, feature_version=COLAB_PYTHON)
            except SyntaxError as error:
                failures.append(f"{name} cell {index} reference:{error.lineno}: {error.msg}")
        archive = re.search(r"COURSE_ARCHIVE = \(\n(.*?)\n\)", source, re.S)
        if archive and "lucy-course-runtime.pth" not in source:
            # Colab installs no course package: without this, a child process cannot import it.
            failures.append(
                f"{name} cell {index}: embedded runtime not registered for child processes"
            )
        if archive:
            literal = "".join(re.findall(r'"([^"]*)"', archive.group(1)))
            files = json.loads(zlib.decompress(base64.b85decode(literal)))
            for relative, content in files.items():
                if relative.endswith(".py"):
                    try:
                        ast.parse(content, relative, feature_version=COLAB_PYTHON)
                    except SyntaxError as error:
                        failures.append(f"{name} runtime {relative}:{error.lineno}: {error.msg}")
    return failures


def colab_failures(book: Path = BOOK) -> list[str]:
    """Everything a reader opens on Colab: course Python files and every notebook in the book."""
    failures = colab_parse_failures(book)
    for path in sorted(book.rglob("*.ipynb")):
        failures += colab_notebook_failures(path, book)
    return failures


if __name__ == "__main__":
    problems = colab_failures()
    for problem in problems:
        print(problem)
    notebooks = len(list(BOOK.rglob("*.ipynb")))
    print(
        f"COLAB: {notebooks} notebooks and every course Python file checked against Python "
        f"{COLAB_PYTHON[0]}.{COLAB_PYTHON[1]}; {len(problems)} problems."
    )
    sys.exit(1 if problems else 0)
