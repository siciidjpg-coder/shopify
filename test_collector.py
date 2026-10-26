import html
import json
import unittest
from collector import collect, gross_price, parse_observations, validate_url
from monitor import run

SOURCE = {"name": "Test", "host": "example.fi", "url": "https://example.fi/product"}


def document(**changes):
    v = dict(sku="TEST-M", attributes={"size": "M"}, min_qty=1, display_price=10,
             price_html="<p>12,55 € alv 25,5%</p><p>10,00 € alv 0%</p>",
             is_in_stock=True, is_purchasable=True, variation_is_active=True, variation_is_visible=True)
    v.update(changes)
    return '<form data-product_variations="' + html.escape(json.dumps([v]), quote=True) + '"></form>'


class CollectorTests(unittest.TestCase):
    def test_gross_not_net(self):
        row = parse_observations(document(), SOURCE)[0]
        self.assertEqual(row["gross_price_eur"], "12.55")
        self.assertFalse(row["verified_same_variant"])

    def test_missing_vat_and_ambiguous_sales_rejected(self):
        for markup in ("10,00 €", "10,00 € alv 0%", "<del>12,55 € alv 25,5%</del>", "12,55 € alv 25,5% 13,55 € alv 25,5%"):
            self.assertIsNone(gross_price(markup))

    def test_stock_and_orderability(self):
        for field in ("is_in_stock", "is_purchasable", "variation_is_active", "variation_is_visible"):
            self.assertFalse(parse_observations(document(**{field: False}), SOURCE)[0]["in_stock"])

    def test_robots_denial_stops_fetch(self):
        calls = []
        def fetch(url, host):
            calls.append(url)
            return "User-agent: *\nDisallow: /"
        with self.assertRaises(ValueError):
            collect(SOURCE, fetch, lambda _: None)
        self.assertEqual(len(calls), 1)

    def test_robots_checked_and_delay_respected(self):
        waits = []
        def fetch(url, host):
            return "User-agent: *\nCrawl-delay: 5\nAllow: /" if url.endswith('robots.txt') else document()
        self.assertEqual(len(collect(SOURCE, fetch, waits.append)), 1)
        self.assertEqual(waits, [5])

    def test_host_and_scheme_rejected(self):
        for url in ("http://example.fi/a", "https://example.fi.evil.com/a", "https://user@example.fi/a"):
            with self.assertRaises(ValueError):
                validate_url(url, "example.fi")

    def test_changed_page_fails_closed(self):
        with self.assertRaises(ValueError):
            parse_observations("<html>Captcha</html>", SOURCE)

    def test_matching_sku_is_only_candidate(self):
        catalog = {"productVariants": {"nodes": [{"id": "123", "sku": "TEST-M", "price": "20.00"}]}}
        result = run([SOURCE], catalog, lambda s: parse_observations(document(), s))
        self.assertEqual(len(result["candidates"]), 1)
        self.assertEqual(result["approved_proposals"], [])
        self.assertEqual(result["shopify_writes"], 0)

    def test_source_failure_is_visible(self):
        def fail(_): raise TimeoutError("secret")
        result = run([SOURCE], collect_fn=fail)
        self.assertEqual(result["errors"], [{"source": "Test", "error_type": "TimeoutError"}])
