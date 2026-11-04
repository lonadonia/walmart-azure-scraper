"""Check Walmart records against the pages they came from, independently of the collector's parser
(offline: no network request). Used by the automated canary (the first recorded page of a run) and by
``walmart-collector verify-sources`` (a whole run's export against its stored pages).

``records`` is a run's export (``products.json``: a list of 22-field records). The pages are the run's
stored listing pages as Walmart returned them (``*.body.gz`` or ``.html``), and the product pages it read
for products it followed (sponsored-only products, variant siblings). Every record is matched to its item
by the item id in its URL (``/ip/…/<id>``); the item's own JSON in the page (``__NEXT_DATA__`` ›
``searchResult`` › ``itemStacks`` › ``items``, or a product page's ``data`` › ``product``) is read here with
a few lines of code of its own, and compared with the record:

* ``product_title`` = the item's ``name`` (runs of spaces read as one, as a browser shows them); ``url`` =
  its ``canonicalUrl`` on walmart.com; ``image_url`` = its ``imageInfo.thumbnailUrl``;
* prices, in whichever of the three price layouts the item uses (the three that the collector's page reader
  reads): the price lines ``priceInfo.priceDetails.priceLines`` (a sale is a ``DISCOUNTED_PRICE`` with a
  ``COMPARISON``/``WAS_PRICE`` above it: ``sale_price`` and ``regular_price``; otherwise ``CURRENT_PRICE`` is
  ``regular_price``), the nested objects ``currentPrice``/``wasPrice``/``unitPrice`` › ``priceString``, or the
  flat display strings ``priceInfo.linePriceDisplay``/``linePrice``/``itemPrice``, ``priceInfo.wasPrice`` and
  ``priceInfo.unitPrice``; a was-price above the current price makes a sale in each layout; amounts compared
  as decimals;
* ``ppm`` = the ``UNIT_PRICE`` line (or the unit price of the other two layouts) exactly as displayed;
* the item's Pickup line for the store (``fulfillmentSummary``), seller and availability are reported.

Release 1.6.5 reads the flat display strings. Release 1.6.4 and earlier read only the first two layouts, so
a record read correctly from a page in the flat layout was reported as a mismatch (live census L10 of
2026-11-04: 21 of 10,301 records, all from one page; ``tests/captures/listing_pages_20261104_flat``). The
canary judges the first recorded page with the same comparison, so such a first page would have stopped a run.

When an item appears on several pages (a repeat, a later page), the page that matches the record best is
reported, each page judged with its own Pickup line (below; release 1.3.1 chose the page before setting
aside the prices of a page without the store's line, so an earlier page with the line could be chosen and
reported as a mismatch). A record whose item is in none of the pages is reported ``unverified`` (never
assumed correct).

A record exported without a local price (its prices and ``ppm`` empty: a verified store product the page
shows with no Pickup line for the store) is verified on its other fields when the page indeed shows no
Pickup line for the store (``verified_without_local_price``): the price the page displays is not the
store's Pickup price, so it is not compared. Empty prices while the page has the store's Pickup line are a
mismatch.
"""

from __future__ import annotations

import gzip
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

NEXT_DATA = re.compile(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)
ITEM_ID = re.compile(r"/ip/(?:[^/?#]+/)?(\d+)")


def page_json_text(html: str) -> dict[str, Any] | None:
    m = NEXT_DATA.search(html)
    if not m:
        return None
    data: dict[str, Any] = json.loads(m.group(1))
    return data


def page_json(path: Path) -> dict[str, Any] | None:
    raw = path.read_bytes()
    if path.suffix == ".gz":
        raw = gzip.decompress(raw)
    return page_json_text(raw.decode("utf-8", "replace"))


def item_id_of(url: str) -> str | None:
    m = ITEM_ID.search(url or "")
    return m.group(1) if m else None


def items_of(nd: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """A result page's items (``searchResult.itemStacks[].items[]``), or a product page's own item
    (``initialData.data.product``: a product the run followed to its own page)."""
    initial = ((nd.get("props") or {}).get("pageProps") or {}).get("initialData") or {}
    sr = initial.get("searchResult") or {}
    out = []
    for si, stack in enumerate(sr.get("itemStacks") or []):
        for ii, item in enumerate((stack or {}).get("items") or []):
            if isinstance(item, dict) and item.get("usItemId"):
                out.append((f"itemStacks[{si}].items[{ii}]", item))
    product = (initial.get("data") or {}).get("product") if isinstance(initial.get("data"), dict) else None
    if isinstance(product, dict) and product.get("usItemId"):
        out.append(("data.product", product))
    return out


def lines(item: dict[str, Any]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for line in ((item.get("priceInfo") or {}).get("priceDetails") or {}).get("priceLines") or []:
        kind = str(line.get("lineType") or "").upper()
        for v in line.get("values") or []:
            if v.get("value") not in (None, ""):
                out.setdefault(kind, {})[str(v.get("key") or "").upper()] = str(v.get("value"))
    return out


def dec(text: str) -> Decimal | None:
    m = re.search(r"\d+(?:\.\d+)?", (text or "").replace(",", ""))
    if not m:
        return None
    try:
        return Decimal(m.group(0))
    except InvalidOperation:
        return None


def flat_text(info: dict[str, Any], *keys: str) -> str:
    """The first non-empty flat display string of ``priceInfo`` among ``keys``, as given ("" when none)."""
    for key in keys:
        value = info.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def expected_prices(item: dict[str, Any]) -> tuple[str, str, str]:
    """(regular, sale, ppm) as the page shows them ("" when not shown): the price lines, else the nested
    objects, else the flat display strings (release 1.6.5)."""
    info = item.get("priceInfo") or {}
    pl = lines(item)
    current = (pl.get("DISCOUNTED_PRICE") or {}).get("PRICE") or (pl.get("CURRENT_PRICE") or {}).get("PRICE")
    was = (pl.get("COMPARISON") or {}).get("WAS_PRICE")
    if not current and isinstance(info.get("currentPrice"), dict):
        current = info["currentPrice"].get("priceString")
    if not was and isinstance(info.get("wasPrice"), dict):
        was = info["wasPrice"].get("priceString")
    if not current:
        current = flat_text(info, "currentPrice", "linePriceDisplay", "linePrice", "itemPrice")
    if not was:
        was = flat_text(info, "wasPrice")
    ppm = (pl.get("UNIT_PRICE") or {}).get("UNIT_PRICE") or ""
    if not ppm and isinstance(info.get("unitPrice"), dict):
        ppm = info["unitPrice"].get("priceString") or ""
    if not ppm:
        ppm = flat_text(info, "unitPrice")
    c, w = dec(current or ""), dec(was or "")
    if c is not None and w is not None and w > c:
        return str(was), str(current), ppm
    return (str(current) if current else ""), "", ppm


def same_amount(a: str, b: str) -> bool:
    if not a and not b:
        return True
    da, db = dec(a), dec(b)
    return da is not None and da == db


def squash(text: Any) -> str:
    return " ".join(str(text or "").split())


def compare(rec: dict[str, Any], item: dict[str, Any]) -> tuple[dict[str, bool], tuple[str, str, str]]:
    regular, sale, ppm = expected_prices(item)
    canonical = str(item.get("canonicalUrl") or "")
    image = (item.get("imageInfo") or {}).get("thumbnailUrl") or item.get("image")
    checks = {
        "product_title": squash(rec.get("product_title")) == squash(item.get("name")),
        "url": rec.get("url")
        == (canonical if canonical.startswith("http") else "https://www.walmart.com" + canonical),
        "image_url": rec.get("image_url") == image,
        "regular_price": same_amount(rec.get("regular_price", ""), regular)
        or (rec.get("regular_price", "") == "" and rec.get("_status") not in (None, "valid")),
        "sale_price": same_amount(rec.get("sale_price", ""), sale),
        "ppm": rec.get("ppm", "") == ppm,
    }
    return checks, (regular, sale, ppm)


def load_records(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("items") if isinstance(data, dict) else data
    out = []
    for r in rows or []:
        if "record" in r:
            out.append(
                {**r["record"], "_key": r.get("upc"), "_status": r.get("status"), "_flags": r.get("flags")}
            )
        else:
            out.append(dict(r))
    return out


def _judge(
    rec: dict[str, Any], src: dict[str, Any], store_id: str
) -> tuple[dict[str, Any], dict[str, bool], tuple[str, str, str], list[str], bool]:
    """A record against one page holding its item: the field checks, the page's prices, its Pickup store
    ids and whether the record is exported without a local price that this page explains (no Pickup line
    for the store: the price it displays is not the store's, so it is not compared)."""
    checks, prices = compare(rec, src["item"])
    pickup = [
        str(f.get("storeId") or "")
        for f in src["item"].get("fulfillmentSummary") or []
        if str(f.get("fulfillment") or "").upper() == "PICKUP"
    ]
    no_local_price = store_id not in pickup and not any(
        rec.get(k) for k in ("regular_price", "sale_price", "ppm")
    )
    if no_local_price:
        checks.update(regular_price=True, sale_price=True, ppm=True)
    return src, checks, prices, pickup, no_local_price


def check(records: list[dict[str, Any]], pages_dir: Path, store_id: str) -> dict[str, Any]:
    """Every record against the stored pages: verified, mismatch (with the fields) or unverified."""
    found: dict[str, list[dict[str, Any]]] = {}
    pages = sorted(p for p in pages_dir.rglob("*") if p.is_file() and p.name.endswith((".gz", ".html")))
    for p in pages:
        nd = page_json(p)
        if nd is None:
            continue
        for path, item in items_of(nd):
            found.setdefault(str(item["usItemId"]), []).append({"page": p.name, "path": path, "item": item})
    results = []
    summary = {"records": 0, "verified": 0, "mismatch": 0, "unverified": 0}
    field_mismatch: dict[str, int] = {}
    for rec in records:
        summary["records"] += 1
        m = ITEM_ID.search(rec.get("url", ""))
        sources = found.get(m.group(1), []) if m else []
        if not sources:
            summary["unverified"] += 1
            results.append({"url": rec.get("url"), "result": "unverified", "reason": "item not in the pages"})
            continue
        src, checks, (regular, sale, ppm), pickup, no_local_price = min(
            (_judge(rec, s, store_id) for s in sources), key=lambda x: sum(not ok for ok in x[1].values())
        )
        item = src["item"]
        bad = [k for k, ok in checks.items() if not ok]
        for k in bad:
            field_mismatch[k] = field_mismatch.get(k, 0) + 1
        summary["mismatch" if bad else "verified"] += 1
        if no_local_price and not bad:
            summary["verified_without_local_price"] = summary.get("verified_without_local_price", 0) + 1
        results.append(
            {
                "url": rec.get("url"),
                "status": rec.get("_status"),
                "result": "mismatch"
                if bad
                else ("verified_without_local_price" if no_local_price else "verified"),
                "mismatched_fields": bad,
                "source": {"page": src["page"], "json_path": src["path"], "pages_with_item": len(sources)},
                "record": {
                    k: rec.get(k, "") for k in ("product_title", "regular_price", "sale_price", "ppm")
                },
                "page": {
                    "name": item.get("name"),
                    "regular_price": regular,
                    "sale_price": sale,
                    "ppm": ppm,
                    "pickup_store_ids": pickup,
                    "pickup_at_store": store_id in pickup,
                    "seller": item.get("sellerName") or "",
                    "availability": ((item.get("availabilityStatusV2") or {}).get("value") or ""),
                },
            }
        )
    return {
        "pages_read": len(pages),
        "items_in_pages": sum(len(v) for v in found.values()),
        "summary": summary,
        "mismatched_fields": field_mismatch,
        "results": results,
    }
