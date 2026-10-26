"""Read-only competitor pricing plan. Requires verified matching variants."""
import csv
import json
import argparse
from decimal import Decimal, InvalidOperation
from collections import defaultdict
from datetime import datetime, timezone

def decimal_price(value):
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number <= 0:
            raise ValueError("Price must be positive")
        return number.quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Invalid price") from exc

def plan(rows, max_age_hours=2):
    now = datetime.now(timezone.utc)
    matched = defaultdict(list)
    for row in rows:
        try:
            if row["verified_same_variant"].strip().lower() != "true":
                continue
            if row["in_stock"].strip().lower() != "true":
                continue
            timestamp = datetime.fromisoformat(row["checked_at"].replace("Z", "+00:00"))
            age = (now - timestamp).total_seconds()
            if timestamp.tzinfo is None or age < 0 or age > max_age_hours * 3600:
                continue
            if not row["competitor_url"].startswith("https://"):
                continue
            if not row["variant_id"].startswith("gid://shopify/ProductVariant/"):
                continue
            own_price = decimal_price(row["current_price"])
            competition = decimal_price(row["competitor_price"])
            matched[row["variant_id"]].append((competition, own_price, row))
        except (KeyError, ValueError):
            continue
    proposals = []
    for variant_id, options in matched.items():
        new, old, row = min(options, key=lambda item: item[0])
        decrease = (old - new) / old * 100
        proposals.append({
            "variant_id": variant_id,
            "sku": row.get("sku", ""),
            "product": row.get("product_name", ""),
            "old_price_eur": str(old),
            "proposed_price_eur": str(new),
            "percent_decrease": str(decrease.quantize(Decimal("0.01"))),
            "email_alert_if_applied": decrease > 15,
            "competitor": row["competitor"],
            "competitor_url": row["competitor_url"],
            "status": "DRY_RUN_ONLY"
        })
    return proposals

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mapping_csv")
    parser.add_argument("--output", default="proposals.json")
    args = parser.parse_args()
    with open(args.mapping_csv, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    proposals = plan(rows)
    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(proposals, fh, ensure_ascii=False, indent=2)
    print(f"{len(proposals)} price proposals. NO SHOPIFY WRITES.")
