import json
from pathlib import Path
import unittest

from lab import assess_brief


FIXTURE = Path(__file__).parent / "fixtures" / "baseline.json"


class BriefContractTest(unittest.TestCase):
    def test_pinned_baseline_is_ready(self):
        self.assertEqual({"ready": True, "missing": []}, assess_brief(json.loads(FIXTURE.read_text())))

    def test_empty_scope_is_held(self):
        result = assess_brief({"objective": "reconcile", "owner": "Sam", "scope": " ", "evidence": "report", "escalation": "lead"})
        self.assertEqual({"ready": False, "missing": ["scope"]}, result)

    def test_non_object_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "JSON object"):
            assess_brief([])
