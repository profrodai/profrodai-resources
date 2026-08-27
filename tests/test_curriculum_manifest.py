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
INDEX_PATH = ROOT / "catalog" / "profrod-site-source-index.json"


class CurriculumManifestTests(unittest.TestCase):
    def manifest(self) -> dict[str, object]:
        return json.loads(MANIFEST_PATH.read_text())

    def assert_invalid(self, fixture: dict[str, object], message: str) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid-manifest.json"
            path.write_text(json.dumps(fixture))
            with self.assertRaisesRegex(ValueError, message):
                VALIDATOR.validate(manifest_path=path)

    def assert_invalid_index(self, fixture: dict[str, object], message: str) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid-index.json"
            path.write_text(json.dumps(fixture))
            with self.assertRaisesRegex(ValueError, message):
                VALIDATOR.validate(index_path=path)

    def index(self) -> dict[str, object]:
        return json.loads(INDEX_PATH.read_text())

    def cursor_record(self, fixture: dict[str, object]) -> dict[str, object]:
        return next(record for record in fixture["records"] if record["catalog_path"] == VALIDATOR.CURSOR_PATH)

    def test_positive_fixture_is_valid(self) -> None:
        VALIDATOR.validate()

    def test_rejects_wrong_snapshot(self) -> None:
        fixture = self.manifest()
        fixture["catalog_snapshot"] = "0" * 40
        self.assert_invalid(fixture, "catalog_snapshot")

    def test_rejects_unknown_manifest_field(self) -> None:
        fixture = self.manifest()
        fixture["unapproved"] = True
        self.assert_invalid(fixture, "only schema_version")

    def test_rejects_wrong_schema_version(self) -> None:
        fixture = self.manifest()
        fixture["schema_version"] = 2
        self.assert_invalid(fixture, "schema_version")

    def test_rejects_missing_manifest_record(self) -> None:
        fixture = self.manifest()
        fixture["records"].pop()
        self.assert_invalid(fixture, "exactly 24")

    def test_rejects_duplicate_catalog_path(self) -> None:
        fixture = self.manifest()
        fixture["records"][1]["catalog_path"] = fixture["records"][0]["catalog_path"]
        self.assert_invalid(fixture, "duplicates catalog_path")

    def test_rejects_foreign_manifest_record(self) -> None:
        fixture = self.manifest()
        fixture["records"][-1]["catalog_path"] = "content/articles/not-in-the-source-index.md"
        self.assert_invalid(fixture, "absent from source index")

    def test_rejects_kind_drift(self) -> None:
        fixture = self.manifest()
        fixture["records"][0]["kind"] = "article"
        self.assert_invalid(fixture, "kind must match")

    def test_rejects_source_index_root_shape_drift(self) -> None:
        fixture = self.index()
        fixture["unapproved"] = True
        self.assert_invalid_index(fixture, "unexpected shape")

    def test_rejects_source_index_entry_shape_drift(self) -> None:
        fixture = self.index()
        fixture["entries"][0]["unexpected"] = "field"
        self.assert_invalid_index(fixture, "entry has an unexpected shape")

    def test_rejects_source_index_path_set_drift(self) -> None:
        fixture = self.index()
        fixture["entries"][0]["path"] = "content/courses/different/_course.md"
        self.assert_invalid_index(fixture, "absent from source index")

    def test_rejects_title_duplication(self) -> None:
        fixture = self.manifest()
        fixture["records"][0]["title"] = "not allowed"
        self.assert_invalid(fixture, "must not duplicate")

    def test_rejects_maturity_drift(self) -> None:
        fixture = self.manifest()
        fixture["records"][0]["maturity"] = "developed"
        self.assert_invalid(fixture, "maturity must be scaffold")

    def test_rejects_invalid_contract_status(self) -> None:
        fixture = self.manifest()
        fixture["records"][1]["contract_status"] = "developed"
        self.assert_invalid(fixture, "contract_status")

    def test_rejects_planned_content_fields(self) -> None:
        fixture = self.manifest()
        fixture["records"][1]["readme_contract"] = {}
        self.assert_invalid(fixture, "planned record")

    def test_rejects_completed_set_losing_cursor(self) -> None:
        fixture = self.manifest()
        record = self.cursor_record(fixture)
        record.clear()
        record.update({
            "catalog_path": VALIDATOR.CURSOR_PATH,
            "kind": "course",
            "maturity": "scaffold",
            "contract_status": "planned",
        })
        self.assert_invalid(fixture, "completed record set")

    def test_rejects_unknown_completed_cursor_field(self) -> None:
        fixture = self.manifest()
        self.cursor_record(fixture)["unapproved"] = True
        self.assert_invalid(fixture, "completed Cursor record")

    def test_rejects_unapproved_complete_record(self) -> None:
        fixture = self.manifest()
        record = fixture["records"][1]
        record["contract_status"] = "complete"
        record["readme_contract"] = copy.deepcopy(fixture["records"][0]["readme_contract"])
        record["lab_contracts"] = copy.deepcopy(fixture["records"][0]["lab_contracts"])
        self.assert_invalid(fixture, "only the approved")

    def test_rejects_lab_escape(self) -> None:
        fixture = self.manifest()
        lab = copy.deepcopy(self.cursor_record(fixture)["lab_contracts"][0])
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            temporary_root = Path(directory)
            lab_path = temporary_root / VALIDATOR.ORDER_API_PATH
            lab_path.parent.mkdir(parents=True)
            lab_path.symlink_to(Path(outside), target_is_directory=True)
            original_root = VALIDATOR.ROOT
            try:
                VALIDATOR.ROOT = temporary_root
                with self.assertRaisesRegex(ValueError, "escapes the repository"):
                    VALIDATOR.validate_lab_contract(lab)
            finally:
                VALIDATOR.ROOT = original_root

    def test_rejects_lab_parent_mismatch(self) -> None:
        fixture = self.manifest()
        self.cursor_record(fixture)["lab_contracts"][0]["parent_catalog_path"] = "content/courses/other/_course.md"
        self.assert_invalid(fixture, "parent_catalog_path")

    def test_rejects_missing_exact_lab_directory(self) -> None:
        fixture = self.manifest()
        lab = copy.deepcopy(self.cursor_record(fixture)["lab_contracts"][0])
        with tempfile.TemporaryDirectory() as directory:
            original_root = VALIDATOR.ROOT
            try:
                VALIDATOR.ROOT = Path(directory)
                with self.assertRaisesRegex(ValueError, "existing directory"):
                    VALIDATOR.validate_lab_contract(lab)
            finally:
                VALIDATOR.ROOT = original_root

    def test_rejects_second_lab(self) -> None:
        fixture = self.manifest()
        fixture["records"][0]["lab_contracts"].append(copy.deepcopy(fixture["records"][0]["lab_contracts"][0]))
        self.assert_invalid(fixture, "exactly one nested lab")

    def test_rejects_missing_or_forged_readme_heading(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "README.md"
            path.write_text(
                "Verification appears in prose.\n"
                "## Verification details\n"
                "```markdown\n## Verification\n```\n"
            )
            with self.assertRaisesRegex(ValueError, "lacks required headings: Verification"):
                VALIDATOR.require_readme_headings(path, ("Verification",))


if __name__ == "__main__":
    unittest.main()
