#!/usr/bin/env python3
"""The local-link gate reads prose links, never code that happens to look like one."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

TOOL = Path(__file__).resolve().parents[1] / "tools" / "check_local_links.py"
SPEC = importlib.util.spec_from_file_location("check_local_links", TOOL)
assert SPEC and SPEC.loader
check_local_links = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_local_links)


class FencedCodeIsNotALink(unittest.TestCase):
    def broken(self, text: str) -> list[str]:
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "page.md").write_text(text)
            return check_local_links.broken_links(Path(folder))

    def test_a_call_inside_a_fence_is_code(self) -> None:
        self.assertEqual(self.broken('```python\ntools = build[\"SHOP\"](shop)\n```\n'), [])

    def test_a_missing_link_in_prose_still_fails(self) -> None:
        self.assertEqual(len(self.broken("See [the guide](missing.md).\n")), 1)

    def test_prose_after_a_closed_fence_is_checked_again(self) -> None:
        self.assertEqual(len(self.broken("~~~\nx[1](y)\n~~~\nSee [the guide](missing.md).\n")), 1)


if __name__ == "__main__":
    unittest.main()
