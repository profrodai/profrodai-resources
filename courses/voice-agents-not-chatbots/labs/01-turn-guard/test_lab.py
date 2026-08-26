import unittest
from lab import next_action

class TurnGuardTest(unittest.TestCase):
    def test_open_call_can_speak(self): self.assertEqual(next_action("open")["action"], "speak")
    def test_completed_call_is_held(self): self.assertEqual(next_action("completed"), {"action":"hold","reason":"call-completed"})
