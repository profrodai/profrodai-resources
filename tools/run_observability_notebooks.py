#!/usr/bin/env python3
"""Execute the ITAM Agentic Observability notebooks top to bottom on the labelled test double.

No API key and no model call: the notebooks' scripted stand-in answers (USE_TEST_DOUBLE = True).
Code cells run in order in one namespace per notebook; any exception fails the gate. The
notebooks' own pinned `pip install` cell runs as written. IPython.display is replaced by a
minimal stand-in so no kernel is needed. This is not a Colab browser observation.
"""
from __future__ import annotations

import contextlib
import io
import json
import re
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "courses/zeo-itam-autumn-2026/labs/12-agentic-observability-edition5"
NOTEBOOKS = sorted(LAB.glob("ITAM-Agentic-Observability-0[12]-2026.ipynb"))
FLAG = re.compile(r"^USE_TEST_DOUBLE\s*=\s*False\b", re.M)


def install_display_stub() -> None:
    display = types.ModuleType("IPython.display")
    display.HTML = lambda data="": ("HTML", data)
    display.Markdown = lambda data="": ("Markdown", data)
    display.display = lambda *items, **kw: None
    package = types.ModuleType("IPython")
    package.display = display
    sys.modules["IPython"] = package
    sys.modules["IPython.display"] = display


def run(path: Path) -> int:
    notebook = json.loads(path.read_text())
    cells = [("".join(c["source"]), i) for i, c in enumerate(notebook["cells"]) if c["cell_type"] == "code"]
    flips = 0
    # A real module, so pydantic can resolve annotations through sys.modules as it does in a kernel.
    module = types.ModuleType("__main__")
    sys.modules["__main__"] = module
    namespace = module.__dict__
    for source, index in cells:
        source, n = FLAG.subn("USE_TEST_DOUBLE = True", source)
        flips += n
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                exec(compile(source, f"{path.name}[cell {index}]", "exec"), namespace)
        except BaseException as error:  # any failure, including SystemExit, fails the gate
            raise SystemExit(f"FAIL {path.name} cell {index}: {type(error).__name__}: {error}") from error
    if flips != 1:
        raise SystemExit(f"FAIL {path.name}: expected exactly one USE_TEST_DOUBLE = False to switch, found {flips}")
    if namespace.get("USE_TEST_DOUBLE") is not True:
        raise SystemExit(f"FAIL {path.name}: test double not active")
    return len(cells)


def main() -> None:
    if len(NOTEBOOKS) != 2:
        raise SystemExit(f"FAIL: expected 2 observability notebooks, found {len(NOTEBOOKS)}")
    install_display_stub()
    runner_main = sys.modules["__main__"]
    for path in NOTEBOOKS:
        try:
            count = run(path)
        finally:
            sys.modules["__main__"] = runner_main
        print(f"observability notebook ran clean on the test double: {path.name} ({count} code cells)")


if __name__ == "__main__":
    main()
