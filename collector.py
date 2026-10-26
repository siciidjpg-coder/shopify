"""Bounded, robots-aware collection. Observations are NEVER price approvals."""
import hashlib
import json
import re
import time
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlsplit
from pricing import decimal_price

USER_AGENT = "HKIPriceMonitor/0.1 (+https://hkigroupstore.fi)"
MAX_BYTES = 3_000_000
REVIEWED_HOSTS = {"www.turunturvavaruste.fi", "www.suojaintukku.fi"}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError("Redirect requires source review")


def validate_url(url, host):
    p = urlsplit(url)
    if p.scheme != "https" or p.hostname != host or p.username or p.password or p.port not in (None, 443):
        raise ValueError("Unapproved source URL")
    if p.fragment or not host.endswith(".fi"):
        raise ValueError("Source requires review")


def download(url, host):
    validate_url(url, host)
    # Fixed reviewed hosts, no arbitrary URLs from pages or end users. Resolve
    # through the platform's configured proxy rather than bypassing it.
    if host not in REVIEWED_HOSTS:
        raise ValueError("Host has not been reviewed")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,text/plain"})
    with urllib.request.build_opener(NoRedirect).open(request, timeout=25) as response:
        data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("Source exceeds size limit")
        if response.headers.get_content_type() not in ("text/html", "text/plain"):
            raise ValueError("Unexpected source format")
        return data.decode(response.headers.get_content_charset() or "utf-8")


class ProductHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.variants = []
        self.documents = []
        self.buffer = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "data-product_variations" in a:
            data = json.loads(a["data-product_variations"])
            if isinstance(data, list):
                self.variants.extend(data)
        if tag == "script" and a.get("type") == "application/ld+json":
            self.buffer = ""

    def handle_data(self, data):
        if self.buffer is not None:
            self.buffer += data

    def handle_endtag(self, tag):
        if tag == "script" and self.buffer is not None:
            try:
                self.documents.append(json.loads(self.buffer))
            except ValueError:
                pass
            self.buffer = None


def gross_price(price_html):
    """Only accept an explicitly labelled gross EUR amount for THIS variant.

    Never multiply a bare/net price by a guessed tax rate.
    Reject sales/strikethrough ambiguity and conflicting amounts.
    """
    if re.search(r"<(?:del|ins)\b", price_html, re.I):
        return None
    text = unescape(re.sub(r"<[^>]*>", " ", price_html))
    matches = re.findall(r"([0-9]+[,.][0-9]{2})\s*€\s*alv\s*25[,.]5\s*%", text, re.I)
    amounts = {str(decimal_price(m)) for m in matches}
    return amounts.pop() if len(amounts) == 1 else None


def parse_observations(document, source, checked_at=None):
    parser = ProductHTML()
    parser.feed(document)
    stamp = checked_at or datetime.now(timezone.utc).isoformat()
    digest = hashlib.sha256(document.encode()).hexdigest()
    result = []
    for item in parser.variants:
        if not isinstance(item, dict):
            continue
        attrs = item.get("attributes", {})
        gross = gross_price(item.get("price_html", ""))
        reasons = ["manufacturer_identity_and_pack_not_verified"]
        if not gross:
            reasons.append("explicit_variant_gross_price_missing")
        available = all(item.get(k) is True for k in ("is_in_stock", "is_purchasable", "variation_is_active", "variation_is_visible"))
        if not available:
            reasons.append("variant_not_orderable")
        if item.get("min_qty") != 1:
            reasons.append("minimum_quantity_not_one")
        result.append({
            "competitor": source["name"], "competitor_url": source["url"],
            "sku": item.get("sku", ""), "attributes": attrs,
            "raw_display_price": str(item.get("display_price", "")),
            "gross_price_eur": gross, "verified_vat_included": gross is not None,
            "in_stock": available, "checked_at": stamp, "source_sha256": digest,
            "verified_same_variant": False, "rejection_reasons": reasons,
        })
    if not result:
        raise ValueError("No supported variant data; source parser requires review")
    return result


def collect(source, fetch=download, sleep=time.sleep):
    host = source["host"]
    validate_url(source["url"], host)
    robots = urllib.robotparser.RobotFileParser()
    robots.parse(fetch("https://" + host + "/robots.txt", host).splitlines())
    if not robots.can_fetch(USER_AGENT, source["url"]):
        raise ValueError("Robots rules disallow collection")
    delay = robots.crawl_delay(USER_AGENT) or robots.crawl_delay("*") or 2
    rate = robots.request_rate(USER_AGENT) or robots.request_rate("*")
    if rate:
        delay = max(delay, rate.seconds / rate.requests)
    if delay > 60:
        raise ValueError("Source needs slower dedicated scheduling")
    sleep(max(2, delay))
    return parse_observations(fetch(source["url"], host), source)
