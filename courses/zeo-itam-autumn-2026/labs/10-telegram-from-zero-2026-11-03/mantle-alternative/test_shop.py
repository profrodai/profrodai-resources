import os
import unittest

import shop


class ShelfTests(unittest.TestCase):
    def setUp(self):
        self.saved = dict(shop.INVENTORY)
        # Fixed unit-test shelf, so the instructor can edit the live shelf without breaking the tests.
        shop.INVENTORY["vanilla"] = 2
        os.environ["LUCY_PIN"] = "1234"

    def tearDown(self):
        shop.INVENTORY.clear()
        shop.INVENTORY.update(self.saved)
        os.environ.pop("LUCY_PIN", None)

    def test_minute_one(self):
        self.assertEqual(shop.stock_reply("vanilla"), "vanilla: 2 tubs")

    def test_change_one_number(self):
        shop.INVENTORY["vanilla"] = 7
        self.assertEqual(shop.stock_reply("vanilla"), "vanilla: 7 tubs")
        self.assertEqual(shop.stock_reply("chocolate"), "chocolate: 12 tubs")

    def test_empty_shelf_is_not_unknown(self):
        self.assertEqual(shop.stock_reply("strawberry"), "strawberry: 0 tubs")
        self.assertEqual(shop.stock_reply("mango"), "Unknown flavor")

    def test_owner_gets_a_proposal_and_stock_is_unchanged(self):
        self.assertEqual(shop.restock_reply("1234", "vanilla"), "Propose 6 tubs")
        self.assertEqual(shop.INVENTORY["vanilla"], 2)

    def test_customer_is_refused_and_stock_is_unchanged(self):
        self.assertEqual(shop.restock_reply("", "vanilla"), "Owner only")
        self.assertEqual(shop.INVENTORY["vanilla"], 2)

    def test_wrong_pin_is_refused(self):
        self.assertEqual(shop.restock_reply("0000", "vanilla"), "Owner only")

    def test_default_pin_comes_from_the_shop_file(self):
        del os.environ["LUCY_PIN"]
        self.assertEqual(shop.restock_reply(shop.OWNER_PIN, "vanilla"), "Propose 6 tubs")
        self.assertEqual(shop.restock_reply("1234", "vanilla"), "Owner only")

    def test_spoken_pin_from_voice_works(self):
        self.assertEqual(shop.restock_reply("one two three four", "vanilla"), "Propose 6 tubs")
        self.assertEqual(shop.restock_reply("one, two, three, four", "vanilla"), "Propose 6 tubs")

    def test_spoken_wrong_or_partial_pin_is_refused(self):
        self.assertEqual(shop.restock_reply("one two three five", "vanilla"), "Owner only")
        self.assertEqual(shop.restock_reply("one two three", "vanilla"), "Owner only")
        self.assertEqual(shop.restock_reply("my pin is one two three four", "vanilla"), "Owner only")

    def test_proposal_never_below_zero(self):
        shop.INVENTORY["vanilla"] = 11
        self.assertEqual(shop.restock_reply("1234", "vanilla"), "Propose 0 tubs")

    def test_other_flavor_has_no_target(self):
        self.assertEqual(shop.restock_reply("1234", "chocolate"), "No target for that flavor")


if __name__ == "__main__":
    unittest.main()
