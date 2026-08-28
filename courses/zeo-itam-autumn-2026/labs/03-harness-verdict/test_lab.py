import json
from pathlib import Path
import unittest

from lab import verdict


FIXTURE = Path(__file__).parent / "fixtures" / "baseline.json"


class HarnessVerdictTest(unittest.TestCase):
    def test_pinned_baseline_is_accepted(self):
        self.assertEqual({"decision": "accept", "reason": "check-agrees", "missing": []}, verdict(json.loads(FIXTURE.read_text())))

    def test_disagreement_holds_claim(self):
        claim = json.loads(FIXTURE.read_text())
        claim["observed"] = "two invoices unmatched"
        self.assertEqual({"decision": "hold", "reason": "check-disagrees", "missing": []}, verdict(claim))

    def test_missing_check_holds_claim(self):
        claim = json.loads(FIXTURE.read_text())
        claim["check"] = ""
        self.assertEqual({"decision": "hold", "reason": "missing-evidence", "missing": ["check"]}, verdict(claim))
