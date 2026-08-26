#!/usr/bin/env python3
"""Fail-closed validation for the curriculum map; standard library only."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "catalog" / "curriculum.json"
SCHEMA_PATH = ROOT / "catalog" / "curriculum.schema.json"
SOURCE_INDEX_PATH = ROOT / "catalog" / "profrod-site-source-index.json"
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


def git_output(source_repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(source_repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown git error"
        fail(f"pinned profrod-site source material unavailable: {detail}")
    return result.stdout


def frontmatter_title(contents: str, source_path: str) -> str:
    lines = contents.splitlines()
    if not lines or lines[0] != "---":
        fail(f"pinned source has no frontmatter: {source_path}")
    for line in lines[1:]:
        if line == "---":
            break
        if line.startswith("title: "):
            raw_title = line.removeprefix("title: ")
            if raw_title.startswith('"'):
                try:
                    title = json.loads(raw_title)
                except json.JSONDecodeError as error:
                    fail(f"pinned source title is not a supported JSON string in {source_path}: {error}")
                if not isinstance(title, str):
                    fail(f"pinned source title is not a string: {source_path}")
                return title
            return raw_title
    fail(f"pinned source frontmatter has no title: {source_path}")


def source_titles(source_repo: Path) -> dict[str, str]:
    require_file(SOURCE_INDEX_PATH, "pinned profrod-site source index")
    snapshot = json.loads(SOURCE_INDEX_PATH.read_text())
    if snapshot.get("repository") != "profrodai/profrod-site":
        fail("source index must identify profrodai/profrod-site")
    commit = snapshot.get("commit")
    if not isinstance(commit, str) or len(commit) != 40 or any(char not in "0123456789abcdef" for char in commit):
        fail("source index must carry a 40-character lowercase commit")
    entries = snapshot.get("entries")
    if not isinstance(entries, list) or len(entries) != EXPECTED_COURSES + EXPECTED_ARTICLES:
        fail("source index must contain exactly every catalogued source")
    index: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"path", "title"}:
            fail("source index entry must contain only path and title")
        path, title = entry["path"], entry["title"]
        if not isinstance(path, str) or not isinstance(title, str) or not path or not title or path in index:
            fail("source index has an invalid or duplicate entry")
        index[path] = title
    git_output(source_repo, "cat-file", "-e", f"{commit}^{{commit}}")
    source_titles_from_git: dict[str, str] = {}
    for path, expected_title in index.items():
        contents = git_output(source_repo, "show", f"{commit}:{path}")
        actual_title = frontmatter_title(contents, path)
        if actual_title != expected_title:
            fail(f"source index title differs from pinned git object for {path}: expected {actual_title!r}, found {expected_title!r}")
        source_titles_from_git[path] = actual_title
    return source_titles_from_git


def validate_source(entry: dict[str, object], index: dict[str, str], kind: str) -> None:
    source = entry.get("source")
    if not isinstance(source, dict) or set(source) != {"path"} or not isinstance(source["path"], str):
        fail(f"{kind} {entry.get('slug')} must have a source object with only path")
    source_title = index.get(source["path"])
    if source_title is None:
        fail(f"{kind} {entry.get('slug')} source path is absent from pinned index")
    if entry.get("title") != source_title:
        fail(f"{kind} {entry.get('slug')} title does not exactly match pinned source title")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--course-makefiles", action="store_true")
    parser.add_argument("--source-repo", default=os.environ.get("PROFROD_SITE_REPO"), help="path to a checkout containing the pinned profrod-site git object")
    args = parser.parse_args()
    require_file(CATALOG_PATH, "catalog")
    require_file(SCHEMA_PATH, "catalog schema")
    schema = json.loads(SCHEMA_PATH.read_text())
    if schema.get("properties", {}).get("schemaVersion", {}).get("const") != 1:
        fail("catalog schema must pin schemaVersion to 1")
    data = json.loads(CATALOG_PATH.read_text())
    if data.get("schemaVersion") != 1:
        fail("schemaVersion must be 1")
    if data.get("sourceSnapshot") != "catalog/profrod-site-source-index.json":
        fail("catalog must name the pinned profrod-site source index")
    if not args.source_repo:
        fail("set PROFROD_SITE_REPO or pass --source-repo to a profrod-site checkout containing the pinned commit")
    source_repo = Path(args.source_repo).expanduser().resolve()
    if not (source_repo / ".git").exists():
        fail(f"source repository is unavailable: {source_repo}")
    pinned_titles = source_titles(source_repo)
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
        validate_source(course, pinned_titles, "course")
        course_path = ROOT / course["coursePath"]
        stub_path = ROOT / course["stubPath"]
        course_readme = course_path / "README.md"
        course_makefile = course_path / "Makefile"
        stub_readme = stub_path / "README.md"
        stub_makefile = stub_path / "Makefile"
        require_file(course_readme, f"course README for {slug}")
        require_file(course_makefile, f"course Makefile for {slug}")
        require_text(course_readme, ("Status:", "Learner promise", "Source boundary", "Module-to-lab", "Prerequisites", "Run, verify, reset"), f"course README for {slug}")
        require_text(course_readme, (f"# {course['title']}",), f"course README title for {slug}")
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
        if not isinstance(article, dict) or set(article) != {"slug", "title", "source"}:
            fail("an article entry must contain only slug, title, and source")
        slug = article["slug"]
        if slug in article_slugs:
            fail(f"duplicate article slug: {slug}")
        article_slugs.add(slug)
        validate_source(article, pinned_titles, "article")
        readme = ROOT / "articles" / slug / "README.md"
        require_file(readme, f"article README for {slug}")
        require_text(readme, ("status: mapped", "Argument-to-demonstration contract", "Provenance", "Run, verify, reset", "Next decision"), f"article README for {slug}")
        require_text(readme, (f"# {article['title']}",), f"article README title for {slug}")
    if args.course_makefiles:
        print("\n".join(course_paths))
    else:
        print(f"catalog valid: {len(courses)} courses, {len(articles)} articles")


if __name__ == "__main__":
    main()
