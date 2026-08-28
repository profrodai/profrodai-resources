"""Adversarial coverage for the full companion-practice manifest."""

from __future__ import annotations

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
    def manifest(self) -> dict:
        return json.loads(MANIFEST_PATH.read_text())

    def index(self) -> dict:
        return json.loads(INDEX_PATH.read_text())

    def assert_invalid(self, fixture: dict, message: str, *, index: dict | None = None) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = Path(directory) / "manifest.json"
            index_path = Path(directory) / "index.json"
            manifest_path.write_text(json.dumps(fixture))
            index_path.write_text(json.dumps(index if index is not None else self.index()))
            with self.assertRaisesRegex(ValueError, message):
                VALIDATOR.validate(index_path=index_path, manifest_path=manifest_path)

    def test_full_24_resource_companion_contract_is_valid(self) -> None:
        self.assertEqual(
            {"course": 11, "article": 13, "complete": 24, "developed": 1, "reviewed": 0},
            VALIDATOR.validate(),
        )

    def test_rejects_wrong_schema_and_snapshot(self) -> None:
        fixture = self.manifest()
        fixture["schema_version"] = 1
        self.assert_invalid(fixture, "schema_version")
        fixture = self.manifest()
        fixture["catalog_snapshot"] = "0" * 40
        self.assert_invalid(fixture, "catalog_snapshot")

    def test_rejects_missing_duplicate_and_foreign_records(self) -> None:
        fixture = self.manifest()
        fixture["records"].pop()
        self.assert_invalid(fixture, "exactly 24")
        fixture = self.manifest()
        fixture["records"][1]["catalog_path"] = fixture["records"][0]["catalog_path"]
        self.assert_invalid(fixture, "duplicates")
        fixture = self.manifest()
        fixture["records"][-1]["catalog_path"] = "content/articles/foreign.md"
        self.assert_invalid(fixture, "absent from source index")

    def test_rejects_record_shape_identity_and_maturity_drift(self) -> None:
        fixture = self.manifest()
        fixture["records"][0]["title"] = "forbidden duplicate identity"
        self.assert_invalid(fixture, "exactly the companion-contract fields")
        fixture = self.manifest()
        fixture["records"][0]["kind"] = "article"
        self.assert_invalid(fixture, "kind does not match")
        fixture = self.manifest()
        fixture["records"][0]["maturity"] = "developed"
        self.assert_invalid(fixture, "maturity must remain scaffold")
        fixture = self.manifest()
        fixture["records"][10]["maturity"] = "scaffold"
        self.assert_invalid(fixture, "maturity must remain developed")

    def test_rejects_incomplete_or_invalid_review_state(self) -> None:
        fixture = self.manifest()
        fixture["records"][0]["contract_status"] = "planned"
        self.assert_invalid(fixture, "must be complete")
        fixture = self.manifest()
        fixture["records"][0]["review_status"] = "self-reviewed"
        self.assert_invalid(fixture, "invalid review_status")

    def test_operator_review_state_is_allowed_but_not_inferred(self) -> None:
        fixture = self.manifest()
        fixture["records"][0]["review_status"] = "operator-reviewed"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(fixture))
            counts = VALIDATOR.validate(manifest_path=path)
        self.assertEqual(1, counts["reviewed"])

    def test_rejects_invalid_date_and_verification_command(self) -> None:
        fixture = self.manifest()
        fixture["records"][0]["last_verified"] = "tomorrow"
        self.assert_invalid(fixture, "ISO date")
        fixture = self.manifest()
        fixture["records"][0]["verification"] = "echo pass"
        self.assert_invalid(fixture, "course verification")
        fixture = self.manifest()
        fixture["records"][0]["verification"] += " && echo pass"
        self.assert_invalid(fixture, "course verification")
        fixture = self.manifest()
        fixture["records"][-1]["verification"] = "echo pass"
        self.assert_invalid(fixture, "article verification")
        fixture = self.manifest()
        fixture["records"][0]["last_verified"] = "2999-01-01"
        self.assert_invalid(fixture, "must not be in the future")

    def test_rejects_missing_or_forged_guide_heading(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "PRACTICE.md"
            path.write_text("Rubric in prose\n## Rubric detail\n```markdown\n## Rubric\n```\n")
            with self.assertRaisesRegex(ValueError, "lacks required headings"):
                VALIDATOR.require_headings(path, {"Rubric"})

    def test_rejects_contained_path_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            temporary_root = Path(directory)
            link = temporary_root / "courses" / "demo"
            link.parent.mkdir(parents=True)
            link.symlink_to(Path(outside), target_is_directory=True)
            original_root = VALIDATOR.ROOT
            try:
                VALIDATOR.ROOT = temporary_root
                with self.assertRaisesRegex(ValueError, "escapes"):
                    VALIDATOR.repo_path("courses/demo", "exercise_path", directory=True)
            finally:
                VALIDATOR.ROOT = original_root

    def test_rejects_source_lesson_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            (temporary_root / "courses" / "demo" / "lessons").mkdir(parents=True)
            (temporary_root / "articles").mkdir()
            original_root = VALIDATOR.ROOT
            try:
                VALIDATOR.ROOT = temporary_root
                with self.assertRaisesRegex(ValueError, "source lesson directory is forbidden"):
                    VALIDATOR.reject_source_bodies()
            finally:
                VALIDATOR.ROOT = original_root

    def test_rejects_source_index_shape_and_set_drift(self) -> None:
        fixture = self.manifest()
        index = self.index()
        index["unapproved"] = True
        self.assert_invalid(fixture, "source index has an unexpected shape", index=index)
        index = self.index()
        index["entries"][0]["path"] = "content/courses/replaced/_course.md"
        self.assert_invalid(fixture, "absent from source index", index=index)


if __name__ == "__main__":
    unittest.main()
