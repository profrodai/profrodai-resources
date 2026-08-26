import unittest
from lab import route

class ConfidenceRoutingTest(unittest.TestCase):
    def test_routes_at_threshold(self): self.assertEqual(route(0.8)["route"], "tool")
    def test_routes_below_threshold_to_review(self): self.assertEqual(route(0.79)["route"], "human-review")
    def test_rejects_invalid_confidence(self):
        with self.assertRaises(ValueError): route(1.1)
