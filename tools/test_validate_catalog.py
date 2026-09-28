#!/usr/bin/env python3
"""Regression fixtures for consolidation-source provenance rules."""

from __future__ import annotations

import contextlib
import copy
import io
import json
import unittest

import validate_catalog


REGISTRY = validate_catalog.CONSOLIDATION_SOURCES_PATH


def zeotool_source() -> dict[str, object]:
    sources = json.loads(REGISTRY.read_text())["sources"]
    return next(source for source in sources if source["id"] == "zeotool")


class ZeoToolProvenanceFixtures(unittest.TestCase):
    def assert_rejected(self, fixture: dict[str, object], message: str) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            validate_catalog.validate_historical_quacktool_source(fixture)
        self.assertIn(message, stderr.getvalue())

    def test_canonical_zeotool_fixture_is_accepted(self) -> None:
        contract = validate_catalog.validate_historical_quacktool_source(zeotool_source())
        self.assertIn(f"Canonical upstream: {validate_catalog.ZEOTOOL_URL}", contract)

    def test_unlabelled_legacy_canonical_url_is_rejected(self) -> None:
        fixture = copy.deepcopy(zeotool_source())
        fixture.pop("historicalSource")
        fixture["upstreamUrl"] = validate_catalog.LEGACY_QUACKTOOL_URL
        fixture["pinnedCommit"] = "2a69d2ee6f79b24416e1a6a14104a927addb4deb"
        fixture["originalLicense"] = "GPL-3.0"
        fixture["licenseStatus"] = "verified-mit"
        fixture["importMode"] = "canonical-import"
        fixture["migrationStatus"] = "mapped"
        self.assert_rejected(fixture, "ZeoTool source entry has an incomplete or unexpected contract")

    def test_unlabelled_historical_source_is_rejected(self) -> None:
        fixture = copy.deepcopy(zeotool_source())
        fixture["upstreamUrl"] = validate_catalog.LEGACY_QUACKTOOL_URL
        self.assert_rejected(fixture, "ZeoTool must name its canonical URL")



def catalog() -> dict[str, object]:
    return json.loads(validate_catalog.CATALOG_PATH.read_text())


def sources() -> dict[str, dict[str, object]]:
    return {source["id"]: source for source in json.loads(REGISTRY.read_text())["sources"]}


class ImportedCourseFixtures(unittest.TestCase):
    def assert_rejected(self, courses: list[object], registry: dict[str, dict[str, object]], message: str) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            validate_catalog.validate_imported_courses(courses, registry)
        self.assertIn(message, stderr.getvalue())

    def test_the_book_course_is_accepted(self) -> None:
        paths = validate_catalog.validate_imported_courses(catalog()["importedCourses"], sources())
        self.assertEqual(paths, ["courses/sovereign-agent-book"])

    def test_a_mapped_status_is_not_an_import(self) -> None:
        courses = copy.deepcopy(catalog()["importedCourses"])
        courses[0]["status"] = "mapped"
        self.assert_rejected(courses, sources(), "must be uniquely tied to a registered consolidation source")

    def test_the_source_must_be_registered_as_imported(self) -> None:
        registry = copy.deepcopy(sources())
        registry["sovereign-agent-book"]["migrationStatus"] = "mapped"
        self.assert_rejected(catalog()["importedCourses"], registry, "canonical import registered as imported")

    def test_an_unlicensed_import_is_rejected(self) -> None:
        registry = copy.deepcopy(sources())
        registry["sovereign-agent-book"]["licenseStatus"] = "awaiting-merged-mit-pin"
        self.assert_rejected(catalog()["importedCourses"], registry, "verified or operator-authorised MIT licence")

    def test_the_course_must_live_at_its_registered_target(self) -> None:
        courses = copy.deepcopy(catalog()["importedCourses"])
        courses[0]["coursePath"] = "courses/elsewhere"
        self.assert_rejected(courses, sources(), "must live at its source's registered target")


if __name__ == "__main__":
    unittest.main()
