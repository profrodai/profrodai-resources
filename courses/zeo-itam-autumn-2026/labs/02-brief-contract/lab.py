"""Assess whether a fictional work request is briefed well enough to begin."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


REQUIRED_FIELDS = ("objective", "owner", "scope", "evidence", "escalation")


def assess_brief(brief: Any) -> dict[str, object]:
    if not isinstance(brief, dict):
        raise ValueError("brief must be a JSON object")
    missing = [field for field in REQUIRED_FIELDS if not isinstance(brief.get(field), str) or not brief[field].strip()]
    return {"ready": not missing, "missing": missing}


def main(path: Path) -> None:
    print(json.dumps(assess_brief(json.loads(path.read_text())), sort_keys=True))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
