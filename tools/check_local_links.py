#!/usr/bin/env python3
"""Validate repository-local Markdown links without network access."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
FENCE_PATTERN = re.compile(r"^\s*(`{3,}|~{3,})")


def markdown_paths(root: Path) -> list[Path]:
    if root.resolve() == ROOT.resolve():
        result = subprocess.run(
            [
                "git",
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "--",
                "*.md",
            ],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        return [root / path for path in result.stdout.splitlines()]
    return sorted(root.rglob("*.md"))


def broken_links(root: Path = ROOT) -> list[str]:
    broken: list[str] = []
    for markdown in markdown_paths(root):
        fence = None
        for line_number, line in enumerate(markdown.read_text().splitlines(), start=1):
            # Code in a fenced block is code: `table["SHOP"](...)` is a call, not a link.
            marker = FENCE_PATTERN.match(line)
            if marker and (fence is None or marker.group(1)[0] == fence):
                fence = marker.group(1)[0] if fence is None else None
                continue
            if fence is not None:
                continue
            for raw_target in LINK_PATTERN.findall(line):
                target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                path_text = target.split("#", 1)[0]
                if not path_text:
                    continue
                candidate = (markdown.parent / path_text).resolve()
                try:
                    candidate.relative_to(root.resolve())
                except ValueError:
                    broken.append(f"{markdown.relative_to(root)}:{line_number}: link escapes repository: {target}")
                    continue
                if not candidate.exists():
                    broken.append(f"{markdown.relative_to(root)}:{line_number}: missing local link: {target}")
    return broken


def main() -> None:
    broken = broken_links()
    if broken:
        print("local Markdown link validation failed:", file=sys.stderr)
        for item in broken:
            print(item, file=sys.stderr)
        raise SystemExit(1)
    print("local Markdown links valid")


if __name__ == "__main__":
    main()
