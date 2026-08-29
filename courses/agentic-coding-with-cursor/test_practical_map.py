"""Keep each Cursor practical connected to its exact Site lesson."""

from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent
COURSE_URL = "https://profrod.ai/courses/agentic-coding-with-cursor"
PRACTICES = {
    "order-api/practices/01-durable-context.md": "04-cursor-rules-durable-context",
    "order-api/practices/02-scoped-change.md": "05-right-size-the-agent-request",
    "order-api/practices/03-behavioral-review.md": "08-when-the-agent-gets-it-wrong",
    "order-api/practices/04-index-boundary.md": "09-cursorignore-and-team-rules",
}


class PracticalMapTest(unittest.TestCase):
    def test_every_practical_has_its_exact_site_lesson_link(self) -> None:
        readme = (ROOT / "README.md").read_text()
        self.assertIn(COURSE_URL, readme)
        for relative_path, lesson_id in PRACTICES.items():
            expected_url = f"{COURSE_URL}/lesson/{lesson_id}"
            self.assertIn(expected_url, readme)
            self.assertIn(expected_url, (ROOT / relative_path).read_text())


if __name__ == "__main__":
    unittest.main()
