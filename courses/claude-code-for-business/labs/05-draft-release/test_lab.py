import unittest
from lab import assess


class DraftReleaseTest(unittest.TestCase):
    def test_approved_draft_only_is_ready(self):
        draft = {"recipient": "supplier@example.test", "body": "draft", "reviewer": "student", "review_approved": True, "delivery": "draft-only"}
        self.assertEqual(assess(draft)["status"], "draft-ready")

    def test_send_action_is_held_even_with_approval(self):
        draft = {"recipient": "supplier@example.test", "body": "draft", "reviewer": "student", "review_approved": True, "delivery": "send"}
        self.assertEqual(assess(draft)["status"], "held")
