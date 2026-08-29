"""Keep every business practice tied to its exact Site lesson."""
from __future__ import annotations
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
COURSE_URL = "https://profrod.ai/courses/claude-code-for-business"
PRACTICES = {
    "labs/01-brief-readiness/PRACTICE.md": "05-practice-01-brief-before-you-delegate",
    "labs/02-scope-boundary/PRACTICE.md": "06-practice-02-right-size-the-task",
    "labs/03-evidence-reconciliation/PRACTICE.md": "07-practice-03-demand-evidence-not-assurances",
    "labs/04-reusable-instructions/PRACTICE.md": "08-practice-04-durable-instructions-reusable-workflows",
    "labs/05-draft-release/PRACTICE.md": "09-practice-05-drafted-not-sent",
}


class PracticalMapTest(unittest.TestCase):
    def test_course_and_practices_link_to_exact_site_lessons(self):
        readme = (ROOT / "README.md").read_text()
        self.assertIn(COURSE_URL, readme)
        for path, lesson in PRACTICES.items():
            url = f"{COURSE_URL}/lesson/{lesson}"
            self.assertIn(url, readme)
            self.assertIn(url, (ROOT / path).read_text())


if __name__ == "__main__":
    unittest.main()
