"""One bounded observation run. There is deliberately no price-write path."""
import argparse
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from collector import collect
from identity import valid_sku
from comparison import identifier_review, review


def run(sources, catalog=None, collect_fn=collect):
    observations, errors = [], []
    for source in sources:
        try:
            observations.extend(collect_fn(source))
        except Exception as exc:
            # Do not log response bodies, tokens, or arbitrary exception messages.
            errors.append({"source": source["name"], "error_type": type(exc).__name__})
    candidates = []
    variants = (catalog or {}).get("productVariants", {}).get("nodes", [])
    for own in variants:
        sku = own.get("sku")
        if not valid_sku(sku):
            continue
        matches = [o for o in observations if o["sku"] == sku]
        if matches:
            candidates.append({"variant_id": own["id"], "sku": sku,
                               "snapshot_price_eur": own["price"],
                               "observations": matches,
                               "status": "CANDIDATE_ONLY_NOT_APPROVED"})
    expected = {s["url"] for s in sources}
    return {"mode": "OBSERVATION_ONLY", "shopify_writes": 0,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "catalog_variants_inspected": len(variants), "candidates": candidates,
            "observations": observations, "errors": errors, "approved_proposals": [],
            "comparison_reviews": [review(c, expected, errors) for c in candidates],
            "identifier_reviews": [{"variant_id": v["id"], **identifier_review(v)} for v in variants]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", default="sources.json")
    parser.add_argument("--catalog", help="Read-only Shopify catalog snapshot (optional)")
    parser.add_argument("--output", default="output/observations.json")
    args = parser.parse_args()
    if os.environ.get("MONITOR_PAUSED", "false").lower() == "true":
        print('{"mode":"PAUSED","shopify_writes":0}')
        return 0
    if os.environ.get("ENABLE_PRICE_WRITES", "false").lower() != "false":
        raise SystemExit("This release does not support Shopify writes")
    sources = json.loads(Path(args.sources).read_text())
    catalog = json.loads(Path(args.catalog).read_text()) if args.catalog else None
    result = run(sources, catalog)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=target.parent, delete=False) as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        temp = f.name
    os.replace(temp, target)
    # Cron disks are ephemeral. Preserve bounded factual observations in service
    # logs as well; a durable database is still required before production writes.
    for observation in result["observations"]:
        print(json.dumps({"event": "observation", **observation}, ensure_ascii=False))
    print(json.dumps({"mode": result["mode"], "observations": len(result["observations"]),
                      "candidates": len(result["candidates"]), "errors": result["errors"], "shopify_writes": 0}))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
