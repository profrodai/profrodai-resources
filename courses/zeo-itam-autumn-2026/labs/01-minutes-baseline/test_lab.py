import unittest
from lab import measure

class MinutesBaselineTest(unittest.TestCase):
    def test_reports_saving(self): self.assertEqual(measure(45, 30)["percent_change"], 33.3)
    def test_preserves_regression(self): self.assertEqual(measure(20, 25)["percent_change"], -25.0)
