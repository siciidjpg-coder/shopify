"""Validate verified competitor observations and generate Shopify price proposals.

Read-only by design. No guessing product matches, no cost or margin floor.
"""
import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

MONEY = Decimal("0.01")
YES = {"true", "1", "yes"}
SHOP_DOMAIN = "hkigroupstore.fi"

def decimal_price(value):
    try:
        number = Decimal(str(value).strip().replace(",", "."))
        if not number.is_finite() or number <= 0 or number.as_tuple().exponent < -2:
            raise ValueError("Price must be positive with at most 2 decimal places")
        return number.quantize(MONEY)
    except (InvalidOperation, ValueError, TypeError, AttributeError) as exc:
        raise ValueError("Invalid price") from exc

def validated_source(url, allowed_domains):
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port not in (None, 443):
        return False
    if not host or host == SHOP_DOMAIN or host.endswith("." + SHOP_DOMAIN):
        return False
    return any(host == domain or host.endswith("." + domain) for domain in allowed_domains)

def plan(rows, max_age_hours=2, allowed_domains=None, now=None):
    """Rows must have been verified by an independent variant + VAT validator.

    No allowlist = no trusted competitor data = no proposals.
    """
    domains = {d.strip().lower() for d in (allowed_domains or set()) if d.strip()}
    now = now or datetime.now(timezone.utc)
    matched = defaultdict(list)
    for row in rows:
        try:
            if str(row["verified_same_variant"]).strip().lower() not in YES:
                continue
            if str(row["in_stock"]).strip().lower() not in YES:
                continue
            if str(row.get("verified_vat_included", "")).strip().lower() not in YES:
                continue
            if str(row.get("currency", "")).strip().upper() != "EUR":
                continue
            if not validated_source(row["competitor_url"], domains):
                continue
            stamp = datetime.fromisoformat(row["checked_at"].replace("Z", "+00:00"))
            age = (now - stamp).total_seconds()
            if stamp.tzinfo is None or age < 0 or age > 3600 * max_age_hours:
                continue
            vid = str(row["variant_id"])
            if not vid.startswith("gid://shopify/ProductVariant/"):
                continue
            old_price = decimal_price(row["current_price"])
            new_price = decimal_price(row["competitor_price"])
            matched[vid].append((new_price, old_price, row))
        except (KeyError, ValueError, TypeError, OverflowError):
            continue
    proposals = []
    for vid, matches in matched.items():
        # Reject conflicting snapshots of our own current price.
        if len({old for _, old, _ in matches}) != 1:
            continue
        new, old, row = min(matches, key=lambda item: item[0])
        decrease = (old - new) / old * 100
        proposals.append({
            "variant_id": vid,
            "sku": row.get("sku", ""),
            "product": row.get("product_name", ""),
            "old_price_eur": str(old),
            "proposed_price_eur": str(new),
            "percent_decrease": str(decrease.quantize(MONEY)),
            "email_alert_if_applied": decrease > Decimal("15"),
            "competitor": row["competitor"],
            "competitor_url": row["competitor_url"],
            "status": "DRY_RUN_ONLY"
        })
    return sorted(proposals, key=lambda p: p["variant_id"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mapping_csv")
    parser.add_argument("--allowed-domain", action="append", required=True)
    parser.add_argument("--output", default="proposals.json")
    args = parser.parse_args()
    with open(args.mapping_csv, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    proposals = plan(rows, allowed_domains=args.allowed_domain)
    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(proposals, fh, ensure_ascii=False, indent=2)
    print(f"{len(proposals)} price proposals. NO SHOPIFY WRITES.")
