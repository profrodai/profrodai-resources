"""Positive and negative fixtures for the bounded curriculum manifest."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "validate_curriculum_manifest.py"
SPEC = importlib.util.spec_from_file_location("curriculum_validator", MODULE_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
MANIFEST_PATH = ROOT / "catalog" / "curriculum-manifest.json"


class CurriculumManifestTests(unittest.TestCase):
    def manifest(self) -> dict[str, object]:
        return json.loads(MANIFEST_PATH.read_text())

    def assert_invalid(self, fixture: dict[str, object], message: str) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid-manifest.json"
            path.write_text(json.dumps(fixture))
            with self.assertRaisesRegex(ValueError, message):
                VALIDATOR.validate(manifest_path=path)

    def test_positive_fixture_is_valid(self) -> None:
        VALIDATOR.validate()

    def test_rejects_wrong_snapshot(self) -> None:
        fixture = self.manifest()
        fixture["catalog_snapshot"] = "0" * 40
        self.assert_invalid(fixture, "catalog_snapshot")

    def test_rejects_duplicate_catalog_path(self) -> None:
        fixture = self.manifest()
        fixture["records"][1]["catalog_path"] = fixture["records"][0]["catalog_path"]
        self.assert_invalid(fixture, "duplicates catalog_path")

    def test_rejects_title_duplication(self) -> None:
        fixture = self.manifest()
        fixture["records"][0]["title"] = "not allowed"
        self.assert_invalid(fixture, "must not duplicate")

    def test_rejects_maturity_drift(self) -> None:
        fixture = self.manifest()
        fixture["records"][0]["maturity"] = "developed"
        self.assert_invalid(fixture, "maturity must be scaffold")

    def test_rejects_planned_content_fields(self) -> None:
        fixture = self.manifest()
        fixture["records"][1]["readme_contract"] = {}
        self.assert_invalid(fixture, "planned record")

    def test_rejects_unapproved_complete_record(self) -> None:
        fixture = self.manifest()
        record = fixture["records"][1]
        record["contract_status"] = "complete"
        record["readme_contract"] = copy.deepcopy(fixture["records"][0]["readme_contract"])
        record["lab_contracts"] = copy.deepcopy(fixture["records"][0]["lab_contracts"])
        self.assert_invalid(fixture, "only the approved")

    def test_rejects_lab_escape(self) -> None:
        fixture = self.manifest()
        fixture["records"][0]["lab_contracts"][0]["resource_path"] = "../outside"
        self.assert_invalid(fixture, "resource_path")

    def test_rejects_second_lab(self) -> None:
        fixture = self.manifest()
        fixture["records"][0]["lab_contracts"].append(copy.deepcopy(fixture["records"][0]["lab_contracts"][0]))
        self.assert_invalid(fixture, "exactly one nested lab")


if __name__ == "__main__":
    unittest.main()
