"""Read-only Shopify Admin GraphQL access. No product mutations."""
import json
import os
import re
import urllib.request
from shopify_auth import ShopifyTokenProvider, shop_domain

API_VERSION = "2026-10"
QUERY = """query($id: ID!) { productVariant(id: $id) { id sku price taxable product { title } } }"""
TOKEN_PROVIDER = ShopifyTokenProvider()

def fetch_variant(variant_id, request_fn=None, token_provider=None):
    shop = shop_domain()
    if not re.fullmatch(r"gid://shopify/ProductVariant/[1-9][0-9]*", variant_id):
        raise ValueError("Invalid Shopify variant ID")
    if os.environ.get("SHOPIFY_CLIENT_ID") or os.environ.get("SHOPIFY_CLIENT_SECRET"):
        token = (token_provider or TOKEN_PROVIDER).get()
    else:
        token = os.environ["SHOPIFY_ADMIN_TOKEN"].strip()
        if not token:
            raise ValueError("Shopify credentials are missing")
    payload = json.dumps({"query": QUERY, "variables": {"id": variant_id}}).encode()
    req = urllib.request.Request(
        f"https://{shop}/admin/api/{API_VERSION}/graphql.json",
        data=payload,
        headers={"Content-Type": "application/json", "X-Shopify-Access-Token": token},
        method="POST",
    )
    opener = request_fn or urllib.request.urlopen
    with opener(req, timeout=20) as response:
        result = json.load(response)
    if result.get("errors"):
        raise RuntimeError("Shopify GraphQL returned errors")
    variant = result.get("data", {}).get("productVariant")
    if not variant or variant["id"] != variant_id:
        raise ValueError("Product variant missing or mismatched")
    return variant
