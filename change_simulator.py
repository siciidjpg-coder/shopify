"""Offline rehearsal of price updates, rollback and alert batching.

No Shopify or email transport is imported. This is NOT a production writer.
"""
from decimal import Decimal
from email.message import EmailMessage
from pricing import decimal_price


class Simulator:
    def __init__(self, prices):
        self.prices = {k: decimal_price(v) for k, v in prices.items()}
        self.audit = {}
        self.locked = set()
        self.stopped = False

    def apply(self, change_id, variant_id, expected, new_price, verified=False, fail=False):
        if self.stopped or variant_id in self.locked:
            raise ValueError("Emergency stop or manual price lock")
        if not verified:
            raise ValueError("Unverified proposal")
        old, new = decimal_price(expected), decimal_price(new_price)
        if change_id in self.audit:
            previous = self.audit[change_id]
            if (previous["variant_id"], previous["old"], previous["new"]) != (variant_id, old, new):
                raise ValueError("Idempotency key reused with a different change")
            return previous
        if self.prices[variant_id] != old:
            raise ValueError("Price changed since preview")
        if fail:
            raise RuntimeError("Simulated API failure")
        event = {"variant_id": variant_id, "old": old, "new": new,
                 "alert": (old-new)/old > Decimal("0.15"), "status": "SIMULATED_APPLIED"}
        self.prices[variant_id] = new
        self.audit[change_id] = event
        return event

    def rollback(self, change_id):
        event = self.audit[change_id]
        if event["status"] == "SIMULATED_ROLLED_BACK":
            return
        if self.prices[event["variant_id"]] != event["new"]:
            raise ValueError("Later change prevents rollback")
        self.prices[event["variant_id"]] = event["old"]
        event["status"] = "SIMULATED_ROLLED_BACK"

    def preview_alert(self):
        events = [e for e in self.audit.values() if e["alert"] and e["status"] == "SIMULATED_APPLIED"]
        if not events:
            return None
        mail = EmailMessage()
        mail["To"] = "info@hkigroup.fi"
        mail["Subject"] = "TESTILUONNOS – HKI Price Monitor, ei oikeita hintamuutoksia"
        lines = ["Tämä on paikallinen simulaatio. Viestiä ei ole lähetetty."]
        for e in events:
            lines.append(f'{e["variant_id"]}: {e["old"]} EUR -> {e["new"]} EUR')
        mail.set_content("\n".join(lines))
        return mail
