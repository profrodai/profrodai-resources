#!/usr/bin/env python3
"""Validate repository-local Markdown links without network access."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


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
        for line_number, line in enumerate(markdown.read_text().splitlines(), start=1):
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
