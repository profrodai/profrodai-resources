import unittest
from lab import verify


class EvidenceReconciliationTest(unittest.TestCase):
    def setUp(self):
        self.evidence = [{"amount": 40.0}, {"amount": 12.5}]

    def test_accepts_independently_matching_claim(self):
        self.assertEqual(verify({"invoice_count": 2, "invoice_total": 52.5}, self.evidence)["status"], "accepted")

    def test_holds_fabricated_matching_words_when_evidence_disagrees(self):
        result = verify({"invoice_count": 2, "invoice_total": 999.0}, self.evidence)
        self.assertEqual(result, {"status": "held", "computed_count": 2, "computed_total": 52.5})
