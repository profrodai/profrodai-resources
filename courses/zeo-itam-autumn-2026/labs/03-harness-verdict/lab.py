"""Hold a synthetic claimed result until its named check agrees with it."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


REQUIRED_FIELDS = ("claim_id", "owner", "check", "expected", "observed")


def verdict(claim: Any) -> dict[str, object]:
    if not isinstance(claim, dict):
        raise ValueError("claim must be a JSON object")
    missing = [field for field in REQUIRED_FIELDS if not isinstance(claim.get(field), str) or not claim[field].strip()]
    if missing:
        return {"decision": "hold", "reason": "missing-evidence", "missing": missing}
    if claim["expected"] != claim["observed"]:
        return {"decision": "hold", "reason": "check-disagrees", "missing": []}
    return {"decision": "accept", "reason": "check-agrees", "missing": []}


def main(path: Path) -> None:
    print(json.dumps(verdict(json.loads(path.read_text())), sort_keys=True))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
