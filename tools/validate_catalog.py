#!/usr/bin/env python3
"""Fail-closed validation for the curriculum map; standard library only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "catalog" / "curriculum.json"
SCHEMA_PATH = ROOT / "catalog" / "curriculum.schema.json"
EXPECTED_COURSES = 11
EXPECTED_ARTICLES = 13
REQUIRED_COURSE_KEYS = {"slug", "title", "genre", "status", "source", "coursePath", "stubPath"}


def fail(message: str) -> None:
    print(f"catalog validation failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def require_file(path: Path, description: str) -> None:
    if not path.is_file():
        fail(f"missing {description}: {path.relative_to(ROOT)}")


def require_text(path: Path, fragments: tuple[str, ...], description: str) -> None:
    text = path.read_text()
    missing = [fragment for fragment in fragments if fragment not in text]
    if missing:
        fail(f"{description} lacks required contract text: {', '.join(missing)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--course-makefiles", action="store_true")
    args = parser.parse_args()
    require_file(CATALOG_PATH, "catalog")
    require_file(SCHEMA_PATH, "catalog schema")
    schema = json.loads(SCHEMA_PATH.read_text())
    if schema.get("properties", {}).get("schemaVersion", {}).get("const") != 1:
        fail("catalog schema must pin schemaVersion to 1")
    data = json.loads(CATALOG_PATH.read_text())
    if data.get("schemaVersion") != 1:
        fail("schemaVersion must be 1")
    courses = data.get("courses")
    articles = data.get("articles")
    if not isinstance(courses, list) or len(courses) != EXPECTED_COURSES:
        fail(f"expected exactly {EXPECTED_COURSES} courses")
    if not isinstance(articles, list) or len(articles) != EXPECTED_ARTICLES:
        fail(f"expected exactly {EXPECTED_ARTICLES} articles")
    course_slugs = set()
    course_paths = []
    for course in courses:
        if not isinstance(course, dict) or REQUIRED_COURSE_KEYS - course.keys():
            fail("a course entry is missing a required key")
        slug = course["slug"]
        if slug in course_slugs:
            fail(f"duplicate course slug: {slug}")
        course_slugs.add(slug)
        course_path = ROOT / course["coursePath"]
        stub_path = ROOT / course["stubPath"]
        course_readme = course_path / "README.md"
        course_makefile = course_path / "Makefile"
        stub_readme = stub_path / "README.md"
        stub_makefile = stub_path / "Makefile"
        require_file(course_readme, f"course README for {slug}")
        require_file(course_makefile, f"course Makefile for {slug}")
        require_text(course_readme, ("Status:", "Learner promise", "Source boundary", "Module-to-lab", "Prerequisites", "Run, verify, reset"), f"course README for {slug}")
        require_text(course_makefile, ("run:", "test:", "verify:"), f"course Makefile for {slug}")
        require_file(stub_readme, f"stub README for {slug}")
        require_text(stub_readme, ("Status:",), f"stub README for {slug}")
        if slug != "agentic-coding-with-cursor":
            require_file(stub_makefile, f"stub Makefile for {slug}")
            require_text(stub_makefile, ("run:", "test:", "verify:"), f"stub Makefile for {slug}")
        if slug != "agentic-coding-with-cursor":
            require_file(stub_path / "runtime.txt", f"runtime pin for {slug}")
            require_file(stub_path / "requirements.lock", f"dependency lock for {slug}")
        course_paths.append(course["coursePath"])
    article_slugs = set()
    for article in articles:
        if not isinstance(article, dict) or set(article) != {"slug", "title"}:
            fail("an article entry must contain only slug and title")
        slug = article["slug"]
        if slug in article_slugs:
            fail(f"duplicate article slug: {slug}")
        article_slugs.add(slug)
        readme = ROOT / "articles" / slug / "README.md"
        require_file(readme, f"article README for {slug}")
        require_text(readme, ("status: mapped", "Argument-to-demonstration contract", "Provenance", "Run, verify, reset", "Next decision"), f"article README for {slug}")
    if args.course_makefiles:
        print("\n".join(course_paths))
    else:
        print(f"catalog valid: {len(courses)} courses, {len(articles)} articles")


if __name__ == "__main__":
    main()
