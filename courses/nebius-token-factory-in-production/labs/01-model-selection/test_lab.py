import unittest
from lab import choose

class ModelSelectionTest(unittest.TestCase):
    def test_selects_lowest_cost_eligible_fixture(self):
        result = choose([{"name":"a","latency_ms":100,"cost":2}, {"name":"b","latency_ms":200,"cost":1}], 200)
        self.assertEqual(result["name"], "b")
    def test_reports_no_eligible_fixture(self): self.assertIsNone(choose([{"name":"a","latency_ms":201,"cost":1}], 200))
