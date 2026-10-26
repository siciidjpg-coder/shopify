# HKI Price Monitor – private Shopify app deployment checklist

**Scope: HKI Group Store only.** This is not a Shopify App Store application.

## What exists
- Verified pricing proposal engine and read-only Shopify GraphQL client.
- Automated GitHub Actions tests on push and periodically.
- No competitor collection production integration or live Shopify price changes.

## Step A – Create one-store app in Shopify Dev Dashboard
1. Sign in to https://dev.shopify.com/dashboard with the HKI Group Store owner account.
2. Create an app named **HKI Price Monitor** and configure **custom distribution** for HKI Group Store only, following the current Shopify UI.
3. Request minimum Admin API scopes: **read_products**; add **write_products** only when production price updates are approved.
4. Install the app on HKI Group Store. Owner/admin authorization may be required.
5. Keep client secrets, tokens and refresh credentials exclusively in encrypted deployment secrets. Never put them in repository files, issues, workflows, or chat messages.

## Step B – Read-only integration test
1. Determine the store's original `*.myshopify.com` domain from Shopify Admin.
2. Set secrets `SHOPIFY_SHOP_DOMAIN` and `SHOPIFY_ADMIN_TOKEN` in the secure hosting environment.
3. Use a verified real Shopify variant ID and a verified competitor input CSV.
4. Run `python shopify_preview.py input.csv --allowed-domain example-verified.fi` (replace with a legitimate approved competitor domain).
5. Confirm that mismatched SKU, changed current price, unverified variant, stale data, wrong currency or VAT are rejected.

## Step C – Before first live update
- Verify competitor collection permission and exact EAN/GTIN/size/color/pack match.
- Add Shopify Admin API write mutation, per-change audit log, idempotency, rollback and kill switch.
- Test email delivery to info@hkigroup.fi and confirm alert threshold >15% from immediately previous successfully published price.
- Verify storefront/cart/checkout VAT and Merchant Center synchronization.
- Explicitly approve production pricing and any paid infrastructure.

**NO LIVE PRICE WRITES SHOULD BE ENABLED BY THIS DOCUMENT.**
