"""Validate source prices against live Shopify variants; never writes prices."""
import argparse
import csv
import json
from pricing import plan
from shopify_read import fetch_variant

def build_preview(rows, fetch=fetch_variant):
    proposals = plan(rows)
    accepted = []
    errors = []
    for item in proposals:
        try:
            variant = fetch(item["variant_id"])
            if not variant["taxable"]:
                raise ValueError("Tax treatment requires manual review")
            if variant["sku"] != item["sku"]:
                raise ValueError("SKU mismatch")
            if f'{float(variant["price"]):.2f}' != item["old_price_eur"]:
                raise ValueError("Shopify price changed since competitor snapshot")
            accepted.append(item)
        except Exception as exc:
            errors.append({"variant_id":item["variant_id"],"error":str(exc)})
    return {"proposals":accepted, "rejected":errors, "mode":"READ_ONLY"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file")
    parser.add_argument("--output", default="shopify-preview.json")
    args = parser.parse_args()
    with open(args.csv_file, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    result = build_preview(rows)
    with open(args.output,"w",encoding="utf-8") as f:
        json.dump(result,f,ensure_ascii=False,indent=2)
    print(f'{len(result["proposals"])} verified, {len(result["rejected"])} rejected, NO SHOPIFY WRITES')
