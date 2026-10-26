import io
import json
import os
import unittest
from unittest.mock import patch
from shopify_auth import ShopifyTokenProvider

class FakeResponse:
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def read(self,*args): return json.dumps({"access_token":"fake-token","expires_in":86400}).encode()

class AuthTests(unittest.TestCase):
    def test_expiry_renews_token(self):
        from datetime import datetime, timezone
        calls = []
        def opener(request, timeout):
            calls.append(request.full_url)
            return FakeResponse()
        with patch.dict(os.environ, {"SHOPIFY_SHOP_DOMAIN":"example.myshopify.com","SHOPIFY_CLIENT_ID":"demo","SHOPIFY_CLIENT_SECRET":"not-real"}, clear=True):
            provider = ShopifyTokenProvider(opener)
            provider.get()
            provider._expires_at = datetime.now(timezone.utc)
            provider.get()
        self.assertEqual(len(calls), 2)

    def test_token_requested_and_cached(self):
        calls=[]
        def opener(request,timeout):
            calls.append(request.full_url)
            return FakeResponse()
        with patch.dict(os.environ, {"SHOPIFY_SHOP_DOMAIN":"example.myshopify.com","SHOPIFY_CLIENT_ID":"demo","SHOPIFY_CLIENT_SECRET":"not-real"},clear=True):
            p=ShopifyTokenProvider(opener)
            self.assertEqual(p.get(),"fake-token")
            self.assertEqual(p.get(),"fake-token")
        self.assertEqual(calls,["https://example.myshopify.com/admin/oauth/access_token"])
    def test_custom_domain_rejected(self):
        with patch.dict(os.environ, {"SHOPIFY_SHOP_DOMAIN":"hkigroupstore.fi","SHOPIFY_CLIENT_ID":"demo","SHOPIFY_CLIENT_SECRET":"not-real"},clear=True):
            with self.assertRaises(ValueError):
                ShopifyTokenProvider(lambda *a,**k: None).get()

if __name__ == "__main__":
    unittest.main()
