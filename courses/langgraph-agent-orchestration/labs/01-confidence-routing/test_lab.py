import hashlib
from pathlib import Path
import subprocess
import sys
import unittest

from lab import assess_cases, load_cases, route


FIXTURE = Path(__file__).parent / "fixtures" / "routing-cases.json"
VISUAL_DUPLICATE_FIXTURE = Path(__file__).parent / "fixtures" / "routing-cases-visual-duplicate.json"

class ConfidenceRoutingTest(unittest.TestCase):
    def test_routes_at_threshold(self): self.assertEqual(route(0.8)["route"], "tool")
    def test_routes_below_threshold_to_review(self): self.assertEqual(route(0.79)["review_reason"], "below-threshold")
    def test_invalid_confidence_must_be_reviewed(self): self.assertEqual(route(1.1)["review_reason"], "invalid-confidence")
    def test_boolean_is_not_a_numeric_confidence(self): self.assertEqual(route(True)["route"], "human-review")
    def test_fixed_fixture_covers_tool_review_and_invalid_routes(self):
        self.assertEqual("fcd8c2fe6c87bbc4568652c7ebff3017ddde5ffa1d63edf44738d87837b41472", hashlib.sha256(FIXTURE.read_bytes()).hexdigest())
        self.assertEqual(
            [
                {"id": "high-confidence", "route": "tool", "review_reason": None, "threshold": 0.8},
                {"id": "threshold", "route": "tool", "review_reason": None, "threshold": 0.8},
                {"id": "below-threshold", "route": "human-review", "review_reason": "below-threshold", "threshold": 0.8},
                {"id": "out-of-range", "route": "human-review", "review_reason": "invalid-confidence", "threshold": 0.8},
            ],
            assess_cases(load_cases(FIXTURE)),
        )
    def test_bad_fixture_shape_is_denied(self):
        with self.assertRaisesRegex(ValueError, "only id and confidence"):
            assess_cases({"cases": [{"id": "bad", "confidence": 0.9, "route": "tool"}]})
    def test_blank_and_visually_duplicate_case_ids_are_denied(self):
        with self.assertRaisesRegex(ValueError, "non-empty"):
            assess_cases({"cases": [{"id": " ", "confidence": 0.9}]})
        with self.assertRaisesRegex(ValueError, "unique after trimming"):
            assess_cases({"cases": [{"id": "case", "confidence": 0.9}, {"id": " case ", "confidence": 0.8}]})

    def test_cli_reports_visual_duplicate_without_output_or_traceback(self):
        result = subprocess.run(
            [sys.executable, "lab.py", str(VISUAL_DUPLICATE_FIXTURE)],
            capture_output=True,
            cwd=Path(__file__).parent,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual("", result.stdout)
        self.assertEqual("error: routing case ids must be unique after trimming whitespace\n", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
