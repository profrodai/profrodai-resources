"""Behavioral coverage for every supplementary article exercise."""

from __future__ import annotations

import importlib.util
import json
import hashlib
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "run_article_practice.py"
SPEC = importlib.util.spec_from_file_location("article_practice", MODULE_PATH)
assert SPEC and SPEC.loader
PRACTICE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PRACTICE)


class ArticlePracticeTests(unittest.TestCase):
    def specs(self) -> list[Path]:
        return sorted((ROOT / "articles").glob("*/practice.json"))

    def test_all_thirteen_article_specs_have_positive_and_failure_proof(self) -> None:
        specs = self.specs()
        self.assertEqual(13, len(specs))
        for path in specs:
            with self.subTest(path=path):
                result = PRACTICE.verify_spec(path)
                self.assertEqual({"positive", "failure"}, set(result))

    def test_unknown_exercise_type_fails_closed(self) -> None:
        path = ROOT / "articles" / "build-a-working-agent-with-sovereign-agent" / "practice.json"
        spec = PRACTICE.load_spec(path)
        spec["exercise_type"] = "not-authorized"
        with tempfile.TemporaryDirectory() as directory:
            invalid = Path(directory) / "practice.json"
            invalid.write_text(json.dumps(spec))
            with self.assertRaisesRegex(ValueError, "unsupported"):
                PRACTICE.load_spec(invalid)

    def test_malformed_case_input_fails_closed(self) -> None:
        path = ROOT / "articles" / "build-a-working-agent-with-sovereign-agent" / "practice.json"
        spec = PRACTICE.load_spec(path)
        spec["cases"]["positive"]["input"] = []
        with self.assertRaisesRegex(ValueError, "input and expected must be objects"):
            PRACTICE.run_case(spec, "positive")

    def test_event_replay_reports_every_missing_sequence(self) -> None:
        result = PRACTICE.event_replay(
            {
                "events": [
                    {"sequence": 1, "field": "status", "value": "open"},
                    {"sequence": 4, "field": "owner", "value": "student"},
                ]
            }
        )
        self.assertEqual([2, 3], result["sequence_gaps"])
        self.assertFalse(result["replayable"])

    def test_event_replay_rejects_non_monotonic_sequences(self) -> None:
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            PRACTICE.event_replay(
                {
                    "events": [
                        {"sequence": 2, "field": "status", "value": "open"},
                        {"sequence": 1, "field": "owner", "value": "student"},
                    ]
                }
            )

    def test_autonomy_proposals_require_hard_controls_even_with_a_high_score(self) -> None:
        path = ROOT / "articles" / "when-to-let-an-agent-run-unsupervised" / "proposals.json"
        self.assertEqual("b0d264545dd89359f5ee7f8750a4dc52ad1e3b8829d944121920a94950ecb925", hashlib.sha256(path.read_bytes()).hexdigest())
        proposals = json.loads(path.read_text())
        self.assertEqual(
            [
                {"id": "ready-batch", "hard_gates_pass": True, "missing_hard_controls": [], "readiness_score": 72, "decision": "ready"},
                {"id": "missing-rollback", "hard_gates_pass": False, "missing_hard_controls": ["rollback"], "readiness_score": 96, "decision": "must-review"},
                {"id": "missing-multiple-controls", "hard_gates_pass": False, "missing_hard_controls": ["verification", "no_live_pii", "escalation"], "readiness_score": 91, "decision": "must-review"},
            ],
            PRACTICE.assess_autonomy_proposals(proposals),
        )

    def test_autonomy_proposals_reject_wrong_shape(self) -> None:
        with self.assertRaisesRegex(ValueError, "exactly three"):
            PRACTICE.assess_autonomy_proposals({"proposals": []})

    def test_autonomy_proposals_reject_truthy_control_strings(self) -> None:
        proposals = json.loads(
            (ROOT / "articles" / "when-to-let-an-agent-run-unsupervised" / "proposals.json").read_text()
        )
        proposals["proposals"][0]["controls"]["rollback"] = "true"
        with self.assertRaisesRegex(ValueError, "values must be Boolean"):
            PRACTICE.assess_autonomy_proposals(proposals)

    def test_autonomy_proposals_reject_missing_or_extra_controls(self) -> None:
        source = ROOT / "articles" / "when-to-let-an-agent-run-unsupervised" / "proposals.json"
        for mutation in ("missing", "extra"):
            with self.subTest(mutation=mutation):
                proposals = json.loads(source.read_text())
                controls = proposals["proposals"][0]["controls"]
                if mutation == "missing":
                    del controls["escalation"]
                else:
                    controls["optimism"] = True
                with self.assertRaisesRegex(ValueError, "exactly the five hard controls"):
                    PRACTICE.assess_autonomy_proposals(proposals)

    def test_autonomy_proposals_reject_non_mapping_controls(self) -> None:
        proposals = json.loads(
            (ROOT / "articles" / "when-to-let-an-agent-run-unsupervised" / "proposals.json").read_text()
        )
        proposals["proposals"][0]["controls"] = ["bounded_scope"]
        with self.assertRaisesRegex(ValueError, "controls must be a JSON object"):
            PRACTICE.assess_autonomy_proposals(proposals)


if __name__ == "__main__":
    unittest.main()
