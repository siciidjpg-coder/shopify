"""Read-only Shopify Admin GraphQL access. No product mutations."""
import json
import os
import urllib.request

API_VERSION = "2026-10"
QUERY = """query($id: ID!) { productVariant(id: $id) { id sku price taxable product { title } } }"""

def fetch_variant(variant_id, request_fn=None):
    shop = os.environ["SHOPIFY_SHOP_DOMAIN"].strip()
    token = os.environ["SHOPIFY_ADMIN_TOKEN"].strip()
    if not shop.endswith(".myshopify.com"):
        raise ValueError("Use the official .myshopify.com domain, not the storefront domain")
    if not variant_id.startswith("gid://shopify/ProductVariant/"):
        raise ValueError("Invalid Shopify variant ID")
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
