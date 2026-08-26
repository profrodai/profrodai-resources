import unittest
from lab import assess

class BriefReadinessTest(unittest.TestCase):
    def test_accepts_complete_brief(self):
        self.assertEqual(assess({"objective":"x", "owner":"y", "evidence":["z"]})["status"], "ready")
    def test_names_missing_evidence(self):
        self.assertEqual(assess({"objective":"x", "owner":"y", "evidence":[]}), {"status":"blocked", "missing":["evidence"]})
