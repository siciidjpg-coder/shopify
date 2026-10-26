import unittest
from identity import valid_gtin, valid_sku, same_variant


class IdentityTests(unittest.TestCase):
    def test_gtin_checksum_and_corruption(self):
        self.assertTrue(valid_gtin("4006381333931"))
        for value in ("4006381333932", "4006381333931.0", "", None, " 4006381333931", "４００６３８１３３３９３１"):
            self.assertFalse(valid_gtin(value))

    def test_invisible_sku_rejected(self):
        self.assertTrue(valid_sku("PW-123/XL"))
        for value in ("PW\u200b123", " PW123", "PW123\n", None, ""):
            self.assertFalse(valid_sku(value))

    def test_exact_variant_required(self):
        own = dict(gtin="4006381333931", brand="Example", size="XL", color="black", pack_quantity="1")
        self.assertTrue(same_variant(own, own.copy()))
        for field in ("brand", "size", "color", "pack_quantity", "gtin"):
            other = dict(own, **{field: "different"})
            self.assertFalse(same_variant(own, other))
            other.pop(field)
            self.assertFalse(same_variant(own, other))
