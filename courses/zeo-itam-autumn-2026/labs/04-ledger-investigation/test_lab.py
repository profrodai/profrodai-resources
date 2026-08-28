import json
from pathlib import Path
import unittest

from lab import investigate


FIXTURE = Path(__file__).parent / "fixtures" / "baseline.json"


class LedgerInvestigationTest(unittest.TestCase):
    def test_pinned_baseline_names_receipt_gap(self):
        self.assertEqual({"review_required": True, "duplicate_ids": [], "missing_receipts": ["xolo-103"]}, investigate(json.loads(FIXTURE.read_text())))

    def test_duplicate_is_named(self):
        records = json.loads(FIXTURE.read_text()) + [{"id": "xolo-101", "amount": 24, "receipt": True}]
        self.assertEqual(["xolo-101"], investigate(records)["duplicate_ids"])

    def test_bad_shape_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "only id, amount, and receipt"):
            investigate([{"id": "x", "amount": 1, "receipt": True, "owner": "extra"}])
