"""Tests for single-shop, read-only Shopify connector.

All requests are mocked. Never sends credentials to a real endpoint.
"""
import io
import json
import os
import unittest
from unittest.mock import patch
from shopify_read import fetch_variant

VID = "gid://shopify/ProductVariant/123"

class ShopifyConnectorTests(unittest.TestCase):
    def test_valid_read(self):
        seen = {}
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, *args): return self.data
        def opener(req, timeout):
            seen["url"] = req.full_url
            seen["token"] = req.get_header("X-shopify-access-token")
            response = Response()
            response.data = json.dumps({"data":{"productVariant":{"id":VID,"sku":"TEST","price":"20.00","taxable":True}}}).encode()
            return response
        with patch.dict(os.environ, {"SHOPIFY_SHOP_DOMAIN":"hki-test.myshopify.com","SHOPIFY_ADMIN_TOKEN":"dummy"}, clear=True):
            # json.load uses Response.read
            result = fetch_variant(VID, request_fn=opener)
        self.assertEqual(result["sku"],"TEST")
        self.assertEqual(seen["url"],"https://hki-test.myshopify.com/admin/api/2026-10/graphql.json")
        self.assertEqual(seen["token"],"dummy")

    def test_custom_domain_rejected(self):
        with patch.dict(os.environ, {"SHOPIFY_SHOP_DOMAIN":"hkigroupstore.fi","SHOPIFY_ADMIN_TOKEN":"dummy"}, clear=True):
            with self.assertRaises(ValueError):
                fetch_variant(VID)

    def test_bad_variant_rejected(self):
        with patch.dict(os.environ, {"SHOPIFY_SHOP_DOMAIN":"hki-test.myshopify.com","SHOPIFY_ADMIN_TOKEN":"dummy"}, clear=True):
            with self.assertRaises(ValueError):
                fetch_variant("123")

if __name__=="__main__":
    unittest.main()
