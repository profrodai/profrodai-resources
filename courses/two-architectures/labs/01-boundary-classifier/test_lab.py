import unittest
from lab import classify

class BoundaryClassifierTest(unittest.TestCase):
    def test_low_uncertainty_is_deterministic(self): self.assertEqual(classify("low", "low"), {"boundary":"deterministic","human_review":False})
    def test_high_side_effect_requires_review(self): self.assertEqual(classify("high", "high")["human_review"], True)
