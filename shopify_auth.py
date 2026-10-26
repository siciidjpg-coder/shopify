"""Shopify client credentials token helper for one merchant-owned custom app.

No secrets are stored in GitHub source. Token is requested at runtime.
Shopify Dev Dashboard app must be installed in the same organization as the shop.
"""
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

def shop_domain():
    domain = os.environ["SHOPIFY_SHOP_DOMAIN"].strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*\.myshopify\.com", domain):
        raise ValueError("A valid myshopify.com shop domain is required")
    return domain

class ShopifyTokenProvider:
    def __init__(self, opener=None):
        self.opener = opener or urllib.request.urlopen
        self._token = None
        self._identity = None
        self._expires_at = datetime.min.replace(tzinfo=timezone.utc)

    def get(self):
        domain = shop_domain()
        client_id = os.environ["SHOPIFY_CLIENT_ID"]
        client_secret = os.environ["SHOPIFY_CLIENT_SECRET"]
        identity = (domain, client_id, client_secret)
        if self._identity == identity and self._token and datetime.now(timezone.utc) + timedelta(minutes=5) < self._expires_at:
            return self._token
        body = urllib.parse.urlencode({
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        }).encode("utf-8")
        req = urllib.request.Request(
            f"https://{domain}/admin/oauth/access_token",
            data=body, method="POST",
            headers={"Content-Type":"application/x-www-form-urlencoded"},
        )
        with self.opener(req, timeout=20) as response:
            payload = json.load(response)
        token = payload.get("access_token")
        expires_in = int(payload.get("expires_in", 0))
        if not token or expires_in <= 0:
            raise RuntimeError("Shopify did not issue a valid access token")
        self._token = token
        self._identity = identity
        self._expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        return token
