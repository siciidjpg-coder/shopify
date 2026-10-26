import unittest
from datetime import datetime, timezone
from pricing import plan

class PricingTests(unittest.TestCase):
    def row(self, price, previous="100", verified="true"):
        return {
            "variant_id": "gid://shopify/ProductVariant/123",
            "sku": "TEST",
            "current_price": previous,
            "competitor": "Example",
            "competitor_url": "https://example.fi/product",
            "competitor_price": price,
            "verified_same_variant": verified,
            "in_stock": "true",
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "product_name": "Example product",
        }

    def test_cheapest_price(self):
        self.assertEqual(plan([self.row("80"), self.row("70")])[0]["proposed_price_eur"], "70.00")

    def test_price_increase(self):
        self.assertEqual(plan([self.row("110")])[0]["proposed_price_eur"], "110.00")

    def test_alert_threshold(self):
        self.assertFalse(plan([self.row("85")])[0]["email_alert_if_applied"])
        self.assertTrue(plan([self.row("84.99")])[0]["email_alert_if_applied"])

    def test_unverified_rejected(self):
        self.assertEqual(plan([self.row("1", verified="false")]), [])

if __name__ == "__main__":
    unittest.main()
