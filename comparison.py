"""Offline comparison review. Never turns an incomplete market scan into a price proposal."""
from datetime import datetime, timezone
from decimal import Decimal
from identity import valid_gtin, valid_sku
from pricing import decimal_price

# Manufacturer's 2201 technical datasheet, 25-Feb-2026. Reference evidence only;
# never used to mutate or silently normalize Shopify product data.
REFERENCE_URL = "https://m.media-amazon.com/images/I/71CU13F2txL.pdf"
REFERENCES = dict(zip(
    ("2201WHRS", "2201WHRM", "2201WHRL", "2201WHRXL", "2201WHRXXL", "2201WHRXXXL"),
    ("5036108106677", "5036108106684", "5036108106691", "5036108106707", "5036108106714", "5036108106721")))


def identifier_review(variant):
    sku = variant.get("sku")
    if not valid_sku(sku):
        return {"status": "INVALID_SKU", "shopify_write": False}
    reference = REFERENCES.get(sku)
    if not reference or variant.get("product", {}).get("vendor", "").casefold() != "portwest":
        return {"status": "NO_MANUFACTURER_REFERENCE", "shopify_write": False}
    barcodes = [n.get("value") for n in variant.get("barcodes", {}).get("nodes", [])]
    if barcodes == [reference] and valid_gtin(reference):
        status = "GTIN_MATCHES_REFERENCE"
    elif barcodes == [reference + ".0"] and valid_gtin(reference):
        status = "BARCODE_CORRECTION_CANDIDATE"
    else:
        status = "BARCODE_CONFLICT_OR_MISSING"
    return {"status": status, "reference_gtin": reference,
            "reference_url": REFERENCE_URL, "shopify_write": False}


def review(candidate, expected_sources, source_errors=(), now=None):
    now = now or datetime.now(timezone.utc)
    reasons, comparable = [], []
    seen = set()
    for row in candidate["observations"]:
        source = row["competitor_url"]
        if source not in expected_sources:
            reasons.append("unapproved_source")
            continue
        seen.add(source)
        try:
            stamp = datetime.fromisoformat(row["checked_at"].replace("Z", "+00:00"))
            age = (now - stamp).total_seconds()
            if not 0 <= age <= 7200:
                raise ValueError("stale")
        except (ValueError, TypeError, KeyError):
            reasons.append("stale_or_invalid_timestamp")
            continue
        if row.get("in_stock") is not True:
            continue
        if row.get("verified_same_variant") is not True:
            reasons.append("identity_or_pack_unverified")
            continue
        if row.get("verified_vat_included") is not True:
            reasons.append("gross_price_unverified")
            continue
        try:
            comparable.append(decimal_price(row["gross_price_eur"]))
        except (ValueError, KeyError):
            reasons.append("invalid_gross_price")
    if seen != set(expected_sources) or source_errors:
        reasons.append("incomplete_source_coverage")
    if not comparable:
        reasons.append("no_verified_orderable_offer")
    result = {"variant_id": candidate["variant_id"], "sku": candidate["sku"],
              "status": "BLOCKED", "reasons": sorted(set(reasons)), "shopify_writes": 0}
    if not reasons:
        try:
            old = decimal_price(candidate["snapshot_price_eur"])
        except (ValueError, KeyError):
            result["reasons"] = ["invalid_snapshot_price"]
            return result
        new = min(comparable)
        result.update(status="OFFLINE_COMPARISON_ONLY", lowest_verified_price_eur=str(new),
                      delta_eur=str(new-old), alert_if_applied=(old-new)/old > Decimal("0.15"),
                      requires_live_shopify_recheck=True)
    return result
