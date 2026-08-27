"""Regression tests for maintenance cadence and local-link gates."""

from __future__ import annotations

from datetime import date
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MAINTENANCE = load("maintenance", ROOT / "tools" / "validate_curriculum_maintenance.py")
LINKS = load("links", ROOT / "tools" / "check_local_links.py")


class CurriculumMaintenanceTests(unittest.TestCase):
    def policy(self) -> dict:
        return json.loads((ROOT / "catalog" / "curriculum-maintenance.json").read_text())

    def write_policy(self, directory: str, policy: dict) -> Path:
        path = Path(directory) / "policy.json"
        path.write_text(json.dumps(policy))
        return path

    def test_current_policy_passes_with_injected_date(self) -> None:
        areas = MAINTENANCE.validate(today=date(2026, 8, 27))
        self.assertEqual(5, len(areas))

    def test_overdue_area_fails_with_owner_and_due_date(self) -> None:
        with self.assertRaisesRegex(ValueError, "locked-dependencies owner=maintainer due=2026-09-03"):
            MAINTENANCE.validate(today=date(2026, 9, 4))

    def test_inconsistent_due_date_fails(self) -> None:
        policy = self.policy()
        policy["areas"][0]["next_due"] = "2026-09-28"
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "does not match cadence"):
                MAINTENANCE.validate(self.write_policy(directory, policy), date(2026, 8, 27))

    def test_broken_local_link_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("[missing](docs/missing.md)\n")
            self.assertEqual(["README.md:1: missing local link: docs/missing.md"], LINKS.broken_links(root))


if __name__ == "__main__":
    unittest.main()
