import unittest
from lab import assess


class ReusableInstructionsTest(unittest.TestCase):
    def test_complete_instruction_is_usable(self):
        self.assertEqual(assess({"trigger": "month-end", "steps": ["read"], "output": "draft.md", "verification": "three sections"})["status"], "usable")

    def test_instruction_without_verification_is_incomplete(self):
        self.assertEqual(assess({"trigger": "month-end", "steps": ["read"], "output": "draft.md", "verification": ""}), {"status": "incomplete", "missing": ["verification"]})
