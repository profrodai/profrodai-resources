import unittest
from lab import verify

class EvidenceGateTest(unittest.TestCase):
    def test_passes_complete_evidence_set(self): self.assertEqual(verify({"a"}, {"a"})["verdict"], "pass")
    def test_names_missing_source(self): self.assertEqual(verify({"a","b"}, {"a"}), {"verdict":"fail","missing":["b"]})
