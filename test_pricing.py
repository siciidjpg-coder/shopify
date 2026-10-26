import unittest
from datetime import datetime, timezone
from pricing import plan, decimal_price, validated_source

NOW = datetime(2026, 10, 26, tzinfo=timezone.utc)

class PricingTests(unittest.TestCase):
    def row(self, price, previous="100", verified="true", **overrides):
        item = {
            "variant_id": "gid://shopify/ProductVariant/123",
            "sku": "TEST",
            "current_price": previous,
            "competitor": "Example",
            "competitor_url": "https://example.fi/product",
            "competitor_price": price,
            "verified_same_variant": verified,
            "verified_vat_included": "true",
            "currency": "EUR",
            "in_stock": "true",
            "checked_at": NOW.isoformat(),
            "product_name": "Example product",
        }
        item.update(overrides)
        return item

    def call(self, rows, domains=("example.fi",)):
        return plan(rows, now=NOW, allowed_domains=domains)

    def test_cheapest_price(self):
        self.assertEqual(self.call([self.row("80"), self.row("70")])[0]["proposed_price_eur"], "70.00")

    def test_price_increase(self):
        self.assertEqual(self.call([self.row("110")])[0]["proposed_price_eur"], "110.00")

    def test_alert_threshold(self):
        self.assertFalse(self.call([self.row("85")])[0]["email_alert_if_applied"])
        self.assertTrue(self.call([self.row("84.99")])[0]["email_alert_if_applied"])

    def test_unverified_rejected(self):
        self.assertEqual(self.call([self.row("1", verified="false")]), [])

    def test_missing_allowlist_rejected(self):
        self.assertEqual(self.call([self.row("50")], domains=()), [])

    def test_unverified_vat_rejected(self):
        self.assertEqual(self.call([self.row("50", verified_vat_included="false")]), [])

    def test_wrong_currency_rejected(self):
        self.assertEqual(self.call([self.row("50", currency="USD")]), [])

    def test_subdomain_spoof_rejected(self):
        self.assertEqual(self.call([self.row("50", competitor_url="https://example.fi.evil.com/x")]), [])

    def test_own_shop_rejected(self):
        self.assertEqual(self.call([self.row("50", competitor_url="https://hkigroupstore.fi/x")], domains=("hkigroupstore.fi",)), [])

    def test_conflicting_old_prices_rejected(self):
        self.assertEqual(self.call([self.row("50"), self.row("40", previous="120")]), [])

    def test_stale_rejected(self):
        self.assertEqual(self.call([self.row("50", checked_at="2026-10-20T10:00:00Z")]), [])

    def test_negative_or_zero_rejected(self):
        self.assertEqual(self.call([self.row("0")]), [])
        self.assertEqual(self.call([self.row("-1")]), [])

    def test_strict_cent_precision(self):
        with self.assertRaises(ValueError):
            decimal_price("0.001")

if __name__ == "__main__":
    unittest.main()
