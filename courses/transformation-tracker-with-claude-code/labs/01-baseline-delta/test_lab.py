import unittest
from lab import compare

class BaselineDeltaTest(unittest.TestCase):
    def test_keeps_baseline_and_calculates_saving(self): self.assertEqual(compare(60, 42)["minutes_saved"], 18)
    def test_reports_regression_honestly(self): self.assertEqual(compare(10, 12)["percent_change"], -20.0)
