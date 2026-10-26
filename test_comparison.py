import unittest
from datetime import datetime, timezone
from comparison import identifier_review, review

NOW = datetime(2026, 10, 26, 20, tzinfo=timezone.utc)


class ComparisonTests(unittest.TestCase):
    def candidate(self, **changes):
        row = dict(competitor_url="https://example.fi/a", checked_at=NOW.isoformat(),
                   in_stock=True, verified_same_variant=True, verified_vat_included=True,
                   gross_price_eur="85.00")
        row.update(changes)
        return dict(variant_id="v", sku="TEST", snapshot_price_eur="100.00", observations=[row])

    def test_missing_source_blocks_false_cheapest_claim(self):
        r = review(self.candidate(), {"https://example.fi/a", "https://other.fi/b"}, now=NOW)
        self.assertEqual(r["status"], "BLOCKED")
        self.assertIn("incomplete_source_coverage", r["reasons"])

    def test_source_failure_blocks(self):
        r = review(self.candidate(), {"https://example.fi/a"}, ["timeout"], now=NOW)
        self.assertEqual(r["status"], "BLOCKED")

    def test_stale_future_and_unknown_timezone_block(self):
        for stamp in ("2026-10-26T17:00:00Z", "2026-10-26T21:00:00Z", "2026-10-26T20:00:00"):
            r = review(self.candidate(checked_at=stamp), {"https://example.fi/a"}, now=NOW)
            self.assertEqual(r["status"], "BLOCKED")

    def test_variant_vat_stock_and_invalid_price_block(self):
        for change in ({"verified_same_variant":False}, {"verified_vat_included":False},
                       {"in_stock":False}, {"gross_price_eur":"NaN"}):
            r = review(self.candidate(**change), {"https://example.fi/a"}, now=NOW)
            self.assertEqual(r["status"], "BLOCKED")

    def test_comparison_is_never_live_approval(self):
        for price, alert in (("85.00",False),("84.99",True),("110.00",False)):
            r = review(self.candidate(gross_price_eur=price), {"https://example.fi/a"}, now=NOW)
            self.assertEqual(r["status"], "OFFLINE_COMPARISON_ONLY")
            self.assertEqual(r["alert_if_applied"], alert)
            self.assertTrue(r["requires_live_shopify_recheck"])
            self.assertEqual(r["shopify_writes"], 0)

    def test_reference_is_not_an_automatic_barcode_repair(self):
        v = dict(sku="2201WHRS", product={"vendor":"Portwest"},
                 barcodes={"nodes":[{"value":"5036108106677.0"}]})
        r = identifier_review(v)
        self.assertEqual(r["status"], "BARCODE_CORRECTION_CANDIDATE")
        self.assertFalse(r["shopify_write"])
        self.assertEqual(v["barcodes"]["nodes"][0]["value"], "5036108106677.0")
        v["product"]["vendor"] = "Other"
        self.assertEqual(identifier_review(v)["status"], "NO_MANUFACTURER_REFERENCE")
