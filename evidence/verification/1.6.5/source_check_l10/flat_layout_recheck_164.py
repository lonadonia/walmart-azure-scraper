"""Independent recheck of the records that `validate-export --run` of L10 (release 1.6.4) reports as source-check
mismatches (offline; no request). The collector's checker (checks/source_check.py) reads two of the three price
layouts that its page reader (sites/walmart/page_data.py) reads: price lines and nested price objects, but not the
flat display strings (priceInfo.linePriceDisplay / linePrice / itemPrice, priceInfo.wasPrice and priceInfo.unitPrice
as strings). This script reads each mismatched record's item on every stored page that holds it, with a few lines of
its own (not the collector's reader), and reports, for each page, which of the record's checked fields equal what
that page shows, including the flat layout.

usage: python -I -X utf8 flat_layout_recheck_164.py MISMATCHES.json PRODUCTS.json PAGES_DIR OUT_DIR
       MISMATCHES.json: the output of source_mismatch_164.py; PAGES_DIR: the run's stored listing pages (*.html.gz)
writes OUT_DIR/L10_SOURCE_CHECK_RECHECK.csv (one row per record and page) and OUT_DIR/L10_SOURCE_CHECK_RECHECK.json
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

NEXT = re.compile(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)
ITEM = re.compile(r"/ip/(?:[^/?#]+/)?(\d+)")
AMOUNT = re.compile(r"\d+(?:\.\d+)?")


def amount(s: str) -> Decimal | None:
    m = AMOUNT.search((s or "").replace(",", ""))
    return Decimal(m.group(0)) if m else None


def shown(item: dict) -> dict[str, str]:
    """What the tile shows, in whichever layout the page uses."""
    info = item.get("priceInfo") or {}
    lines: dict[str, dict[str, str]] = {}
    for ln in (info.get("priceDetails") or {}).get("priceLines") or []:
        for v in ln.get("values") or []:
            if v.get("value") not in (None, ""):
                lines.setdefault(str(ln.get("lineType") or "").upper(), {})[str(v.get("key") or "").upper()] = str(v["value"])
    layout, cur, was, unit = "", "", "", ""
    if lines:
        layout = "price lines"
        cur = (lines.get("DISCOUNTED_PRICE") or {}).get("PRICE") or (lines.get("CURRENT_PRICE") or {}).get("PRICE") or ""
        was = (lines.get("COMPARISON") or {}).get("WAS_PRICE") or ""
        unit = (lines.get("UNIT_PRICE") or {}).get("UNIT_PRICE") or ""
    elif isinstance(info.get("currentPrice"), dict):
        layout = "nested objects"
        cur = info["currentPrice"].get("priceString") or ""
        was = (info.get("wasPrice") or {}).get("priceString") or "" if isinstance(info.get("wasPrice"), dict) else ""
        unit = (info.get("unitPrice") or {}).get("priceString") or "" if isinstance(info.get("unitPrice"), dict) else ""
    else:
        layout = "flat strings"
        cur = str(info.get("linePriceDisplay") or info.get("linePrice") or info.get("itemPrice") or "")
        was = info.get("wasPrice") if isinstance(info.get("wasPrice"), str) else ""
        unit = info.get("unitPrice") if isinstance(info.get("unitPrice"), str) else ""
    c, w = amount(cur), amount(was or "")
    regular, sale = (str(w), str(c)) if (c is not None and w is not None and w > c) else (str(c) if c is not None else "", "")
    pickup = [str(f.get("storeId") or "") for f in item.get("fulfillmentSummary") or []
              if str(f.get("fulfillment") or "").upper() == "PICKUP"]
    return {
        "layout": layout,
        "regular_price": regular,
        "sale_price": sale,
        "ppm": unit,
        "url": "https://www.walmart.com" + str(item.get("canonicalUrl") or ""),
        "image_url": str((item.get("imageInfo") or {}).get("thumbnailUrl") or ""),
        "product_title": " ".join(str(item.get("name") or "").split()),
        "pickup_at_3891": "yes" if "3891" in pickup else "no",
        "seller": str(item.get("sellerName") or ""),
    }


def same_amount(a: str, b: str) -> bool:
    return (amount(a) == amount(b)) if (a or b) else True


def main() -> int:
    mism, products, pages_dir, out = (Path(a) for a in sys.argv[1:5])
    bad = json.loads(mism.read_text("utf-8"))["mismatches"]
    records = {r["url"]: r for r in json.loads(products.read_text("utf-8"))}
    pages = {}
    for p in sorted(pages_dir.glob("*.html.gz")):
        raw = gzip.decompress(p.read_bytes())
        m = NEXT.search(raw.decode("utf-8", "replace"))
        if m:
            pages[p.name] = (json.loads(m.group(1)), hashlib.sha256(p.read_bytes()).hexdigest())
    rows, summary = [], []
    for b in bad:
        rec = records[b["url"]]
        iid = ITEM.search(rec["url"]).group(1)
        any_full = False
        for name, (nd, digest) in pages.items():
            sr = (((nd.get("props") or {}).get("pageProps") or {}).get("initialData") or {}).get("searchResult") or {}
            for si, st in enumerate(sr.get("itemStacks") or []):
                for ii, it in enumerate((st or {}).get("items") or []):
                    if str((it or {}).get("usItemId")) != iid:
                        continue
                    s = shown(it)
                    eq = {
                        "regular_price": same_amount(rec["regular_price"], s["regular_price"]),
                        "sale_price": same_amount(rec["sale_price"], s["sale_price"]),
                        "ppm": rec["ppm"] == s["ppm"],
                        "url": rec["url"] == s["url"],
                        "image_url": rec["image_url"] == s["image_url"],
                        "product_title": " ".join(rec["product_title"].split()) == s["product_title"],
                    }
                    full = all(eq.values()) and s["pickup_at_3891"] == "yes"
                    any_full |= full
                    rows.append({
                        "item_id": iid, "product_title": rec["product_title"],
                        "checker_reported": "; ".join(b["mismatched_fields"]),
                        "page": name, "page_sha256": digest, "item_path": f"itemStacks[{si}].items[{ii}]",
                        "price_layout": s["layout"],
                        "record_regular_price": rec["regular_price"], "page_regular_price": s["regular_price"],
                        "record_sale_price": rec["sale_price"], "page_sale_price": s["sale_price"],
                        "record_ppm": rec["ppm"], "page_ppm": s["ppm"],
                        "url_equal": eq["url"], "image_url_equal": eq["image_url"], "title_equal": eq["product_title"],
                        "pickup_at_3891": s["pickup_at_3891"], "seller": s["seller"],
                        "all_fields_equal": all(eq.values()),
                    })
        summary.append({"item_id": iid, "checker_reported": b["mismatched_fields"], "a_page_shows_every_field": any_full})
    out.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    (out / "L10_SOURCE_CHECK_RECHECK.csv").write_bytes(buf.getvalue().encode("utf-8"))
    res = {
        "about": ("validate-export --run 01M6KA3CKYJSD6WDY4TDAAV73Y (L10, release 1.6.4) exits 6: its source check reports "
                  "21 of 10,301 records as mismatches. This recheck reads each one's item on every stored L10 page that "
                  "holds it, in the three price layouts the collector's page reader documents. a_page_shows_every_field: "
                  "one page shows the record's prices, unit price, url, image and title exactly, with a Pickup line for "
                  "store 3891."),
        "records": len(summary),
        "records_shown_exactly_by_a_page": sum(1 for s in summary if s["a_page_shows_every_field"]),
        "layouts_of_those_pages": sorted({r["price_layout"] for r in rows if r["all_fields_equal"]}),
        "per_record": summary,
    }
    (out / "L10_SOURCE_CHECK_RECHECK.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", "utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "per_record"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
