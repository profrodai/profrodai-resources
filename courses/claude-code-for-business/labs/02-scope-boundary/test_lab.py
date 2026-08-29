import unittest
from lab import assess


class ScopeBoundaryTest(unittest.TestCase):
    def test_complete_scope_is_ready(self):
        request = {"objective": "summarize", "allowed_paths": ["fixtures/contracts"], "forbidden_actions": ["send"], "acceptance_checks": ["three rows"]}
        self.assertEqual(assess(request)["status"], "ready")

    def test_missing_boundary_is_named(self):
        self.assertEqual(assess({"objective": "summarize", "allowed_paths": ["x"], "forbidden_actions": [], "acceptance_checks": ["y"]}), {"status": "blocked", "missing": ["forbidden_actions"]})
