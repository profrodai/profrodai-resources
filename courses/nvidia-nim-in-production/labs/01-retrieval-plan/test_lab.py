import unittest
from lab import plan

class RetrievalPlanTest(unittest.TestCase):
    def test_rounds_up_batches(self): self.assertEqual(plan(25, 8), {"batches":4, "concurrency":4})
    def test_empty_input_has_no_workers(self): self.assertEqual(plan(0, 8), {"batches":0, "concurrency":0})
