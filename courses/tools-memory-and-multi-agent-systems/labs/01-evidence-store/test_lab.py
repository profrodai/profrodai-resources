import unittest
from lab import add

class EvidenceStoreTest(unittest.TestCase):
    def test_stores_new_record(self): self.assertEqual(add({}, "a", "fixture")["stored"], True)
    def test_rejects_duplicate_without_mutation(self):
        store = {"a":"fixture"}
        self.assertEqual(add(store, "a", "other"), {"stored":False,"reason":"duplicate","count":1})
        self.assertEqual(store, {"a":"fixture"})
