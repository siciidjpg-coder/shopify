"""Fail-closed product identifier checks. Never repair identifiers by guessing."""
import re
import unicodedata


def valid_gtin(value):
    if not isinstance(value, str) or not re.fullmatch(r"(?:[0-9]{8}|[0-9]{12}|[0-9]{13}|[0-9]{14})", value):
        return False
    digits = [int(c) for c in value]
    total = sum(d * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(digits[:-1])))
    return (10 - total % 10) % 10 == digits[-1]


def valid_sku(value):
    return (isinstance(value, str) and bool(value) and value == value.strip()
            and not any(unicodedata.category(c).startswith("C") for c in value))


def same_variant(own, other):
    """Require a valid GTIN and explicit brand, size, color and pack quantity.

    Missing attributes must be reviewed, not inferred from the product title.
    Manufacturer-code matching is intentionally not enabled yet.
    """
    if not valid_gtin(own.get("gtin")) or not valid_gtin(other.get("gtin")):
        return False
    if own["gtin"].zfill(14) != other["gtin"].zfill(14):
        return False
    for field in ("brand", "size", "color", "pack_quantity"):
        a, b = own.get(field), other.get(field)
        if not isinstance(a, str) or not isinstance(b, str) or not a.strip() or a != b:
            return False
    return True
