import json
from pathlib import Path
import unittest

from lab import verdict


FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str) -> object:
    return json.loads((FIXTURES / name).read_text())


class HarnessVerdictTest(unittest.TestCase):
    def test_pinned_baseline_is_accepted(self):
        self.assertEqual({"decision": "accept", "reason": "check-agrees", "missing": []}, verdict(fixture("claim.json"), fixture("evidence.json")))

    def test_fabricated_claim_cannot_override_independently_computed_evidence(self):
        claim = fixture("claim.json")
        claim["claimed_unmatched_ids"] = ["invented"]
        self.assertEqual({"decision": "hold", "reason": "check-disagrees", "missing": []}, verdict(claim, fixture("evidence.json")))

    def test_missing_check_holds_claim(self):
        claim = fixture("claim.json")
        claim["check"] = ""
        self.assertEqual({"decision": "hold", "reason": "missing-evidence", "missing": ["check"]}, verdict(claim, fixture("evidence.json")))

    def test_non_executed_check_name_is_held(self):
        claim = fixture("claim.json")
        claim["check"] = "never-executed"
        self.assertEqual({"decision": "hold", "reason": "unrecognized-check", "missing": []}, verdict(claim, fixture("evidence.json")))
