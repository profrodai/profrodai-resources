"""Keep the ITAM practical track linked to the live Site lessons it reinforces."""

from pathlib import Path
import unittest


ROOT = Path(__file__).parent
COURSE_URL = "https://profrod.ai/courses/zeo-itam-autumn-2026"
PRACTICALS = {
    "labs/01-minutes-baseline/PRACTICE.md": f"{COURSE_URL}/lesson/03-lab-minutes-baseline",
    "labs/02-brief-contract/PRACTICE.md": f"{COURSE_URL}/lesson/02-prompting-is-briefing",
    "labs/03-harness-verdict/PRACTICE.md": f"{COURSE_URL}/lesson/04-the-harness-at-work",
    "labs/04-ledger-investigation/PRACTICE.md": f"{COURSE_URL}/lesson/03-lab-the-needle-in-xolos-ledger",
}


class PracticalMapTest(unittest.TestCase):
    def test_course_map_and_every_practice_use_exact_lesson_urls(self):
        course_readme = (ROOT / "README.md").read_text()
        for relative_path, lesson_url in PRACTICALS.items():
            self.assertIn(lesson_url, course_readme)
            practice = (ROOT / relative_path).read_text()
            self.assertIn(lesson_url, practice)
            self.assertIn("## Transfer challenge", practice)
            for heading in ("## Objective", "## Guided exercise", "## Project", "## Evidence", "## Debrief", "## Rubric", "## Accessibility", "## Safety and cost"):
                self.assertIn(heading, practice)


if __name__ == "__main__":
    unittest.main()
