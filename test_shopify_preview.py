import unittest
from datetime import datetime, timezone
from shopify_preview import build_preview

class PreviewTests(unittest.TestCase):
    def row(self):
        return dict(variant_id="gid://shopify/ProductVariant/123",sku="SKU1",
            current_price="100.00",competitor="example",competitor_url="https://example.fi/item",
            competitor_price="80.00",verified_same_variant="true",verified_vat_included="true",
            currency="EUR",in_stock="true",
            checked_at=datetime.now(timezone.utc).isoformat(),product_name="Example")
    def test_valid_read_only(self):
        output=build_preview([self.row()],lambda variant_id:dict(id=variant_id,sku="SKU1",price="100.00",taxable=True),allowed_domains=("example.fi",))
        self.assertEqual(len(output["proposals"]),1)
        self.assertEqual(output["mode"],"READ_ONLY")
    def test_changed_shopify_price_rejected(self):
        output=build_preview([self.row()],lambda variant_id:dict(id=variant_id,sku="SKU1",price="120.00",taxable=True),allowed_domains=("example.fi",))
        self.assertEqual(len(output["proposals"]),0)
        self.assertEqual(len(output["rejected"]),1)
if __name__=="__main__":
    unittest.main()
