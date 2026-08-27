#!/usr/bin/env python3
"""Run the fixed, synthetic unattended-automation assessment."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "tools" / "run_article_practice.py"
SPEC = importlib.util.spec_from_file_location("article_practice", RUNNER_PATH)
assert SPEC and SPEC.loader
PRACTICE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PRACTICE)


def load_proposals(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read autonomy proposals: {error}") from error
    if not isinstance(data, dict):
        raise ValueError("autonomy proposals must be a JSON object")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Assess synthetic unattended automation proposals.")
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()
    try:
        result = PRACTICE.assess_autonomy_proposals(load_proposals(args.fixture))
    except ValueError as error:
        print(f"autonomy assessment failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
