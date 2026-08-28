import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from lab import assess_claim, load_claim, verify


FIXTURES = Path(__file__).parent / "fixtures"

class EvidenceGateTest(unittest.TestCase):
    def test_passes_complete_evidence_set(self): self.assertEqual(verify({"a"}, {"a"})["verdict"], "pass")
    def test_names_missing_source(self): self.assertEqual(verify({"a","b"}, {"a"}), {"verdict":"fail","missing":["b"]})
    def test_rejects_an_empty_evidence_requirement(self):
        with self.assertRaisesRegex(ValueError, "required evidence IDs must be a non-empty set"):
            verify(set(), {"receipt-v1"})
    def test_rejects_an_empty_requirement_list_before_it_can_pass(self):
        with self.assertRaisesRegex(ValueError, "required evidence IDs must be a non-empty set"):
            assess_claim({"claim_id": "x", "required": [], "supplied": []})
    def test_rejects_whitespace_only_evidence_ids_before_they_can_pass(self):
        with self.assertRaisesRegex(ValueError, "non-empty"):
            assess_claim({"claim_id": "x", "required": ["  "], "supplied": ["   "]})
    def test_trims_evidence_ids_and_rejects_visual_duplicates(self):
        self.assertEqual(verify({" approval-v1 "}, {"approval-v1"})["verdict"], "pass")
        with self.assertRaisesRegex(ValueError, "unique after trimming"):
            verify({"approval-v1", " approval-v1 "}, {"approval-v1"})
        with self.assertRaisesRegex(ValueError, "unique after trimming"):
            assess_claim({"claim_id": "x", "required": ["approval-v1", " approval-v1 "], "supplied": ["approval-v1"]})
    def test_baseline_fixture_has_a_fixed_failure_trace(self):
        path = FIXTURES / "baseline.json"
        self.assertEqual("74955198e201574c80d4d3262d8c6cf167a9ac6b644552fa072c64d8a5eb79c9", hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(
            {"claim_id": "release-summary", "evidence_supplied": 2, "missing": ["approval-v1"], "verdict": "fail"},
            assess_claim(load_claim(path)),
        )
    def test_acceptance_fixture_requires_the_named_approval(self):
        path = FIXTURES / "acceptance.json"
        self.assertEqual("e18a6dca207f392734f9314d27429c1557fec29d0028af84f851511253a143dd", hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(
            {"claim_id": "release-summary", "evidence_supplied": 3, "missing": [], "verdict": "pass"},
            assess_claim(load_claim(path)),
        )
    def test_rejects_a_malformed_claim(self):
        with self.assertRaisesRegex(ValueError, "lists of non-empty evidence IDs"):
            assess_claim({"claim_id": "x", "required": ["a"], "supplied": [""]})

    def test_rejects_whitespace_only_claim_id_and_trims_a_valid_one(self):
        with self.assertRaisesRegex(ValueError, "claim_id must be a non-empty string"):
            assess_claim({"claim_id": "  ", "required": ["receipt-v1"], "supplied": ["receipt-v1"]})
        self.assertEqual(
            "release-summary",
            assess_claim({"claim_id": " release-summary ", "required": ["receipt-v1"], "supplied": ["receipt-v1"]})["claim_id"],
        )

    def test_cli_rejects_blank_claim_id_and_renders_a_trimmed_one(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            fixture = Path(temporary_directory) / "claim.json"
            fixture.write_text(json.dumps({"claim_id": "   ", "required": ["receipt-v1"], "supplied": ["receipt-v1"]}))
            rejected = subprocess.run(
                [sys.executable, "lab.py", str(fixture)],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("claim_id must be a non-empty string", rejected.stderr)

            fixture.write_text(json.dumps({"claim_id": " release-summary ", "required": ["receipt-v1"], "supplied": ["receipt-v1"]}))
            accepted = subprocess.run(
                [sys.executable, "lab.py", str(fixture)],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            self.assertEqual("release-summary", json.loads(accepted.stdout)["claim_id"])
