"""Brief section 6 on the live campaign's own pages, offline (no request): the stored result pages (purpose
listing) and product pages (purpose product_detail and product_page) of every campaign run in walmart_live150,
read after the last live stage with the readers of edition 1.5.1 (C:/w7/live/ed/walmart-oxylabs-1.5.1, commit 488a033;
1.5.1 changed no offer reader: assembly/offers.py and the offer code of sites/walmart/records.py are the same as in 1.5.0):
  - per result tile: badges, promotion texts, promoDiscount structures, the offers the collector derives
    (sites/walmart/records.py offers()) and how they classify (assembly/offers.py classify(), modality PICKUP),
    plus every promotion-like key of the raw tile;
  - per product page: its promotion objects, classified as payment_or_financing_advertising (promoData 1PAYCC,
    ONE_PREQUAL), membership_subscription_placeholder (discounts wplus_subscription), price_reduction (rollback,
    savingsAmount) or product_offer (anything else);
  - per fresh product each run exported: the disposition of its volume and digital fields (absent on its tile,
    present but not volume or digital, classified), and whether a page of this campaign shows a product offer.
Every stored page is located through the artifacts table (key, sha256) and its SHA-256 is checked before reading.
usage: <edition venv python> -I -X utf8 offers_live_151.py OUT_DIR
"""

import collections
import csv
import gzip
import hashlib
import io
import json
import re
import sys
from pathlib import Path

import pgserver
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from walmart_headless.assembly import offers as aoff
from walmart_headless.sites.walmart import page_data as wpd
from walmart_headless.sites.walmart import records as wrec

DATA = Path(r"C:\w7\live\data")
LIVE = Path(r"C:\w7\evidence\live150")
PROMO_KEY = re.compile(
    r"promo|deal|offer|coupon|rebate|reward|cash|clip|bogo|rollback|clearance|saving|member|ebt|snap|wplus", re.I
)
SKIP_KEYS = re.compile(r"^(offerId|offerType|sellerOfferId|offerPrice|availableOffers?)$", re.I)


def promo_keys(obj, path=""):
    for p, v in wpd.walk(obj, path):
        last = re.sub(r"\[\d+\]$", "", p.rsplit(".", 1)[-1])
        if PROMO_KEY.search(last) and not SKIP_KEYS.match(last) and v not in (None, "", [], {}, False, 0):
            yield re.sub(r"\[\d+\]", "[]", p), v


def raw_tiles(nd):
    for st in wpd._stacks(nd):
        if isinstance(st, dict):
            for it in st.get("items") or []:
                if isinstance(it, dict):
                    yield it


def page_objects(product: dict) -> list[tuple[str, str]]:
    found = []
    for pd in product.get("promoData") or []:
        if isinstance(pd, dict):
            t = str(pd.get("type") or "")
            cls = "payment_or_financing_advertising" if t in ("1PAYCC", "ONE_PREQUAL") else "product_offer"
            found.append((cls, f"promoData {t}: {wpd.text(pd.get('description'))[:90]}"))
    for m in (product.get("discounts") or {}).get("discountMetaData") or []:
        if isinstance(m, dict):
            t = str(m.get("type") or "")
            cls = "membership_subscription_placeholder" if t == "wplus_subscription" else "product_offer"
            found.append((cls, f"discounts {t}"))
    codes = wpd.get(product, "priceInfo", "priceDisplayCodes") or {}
    if (isinstance(codes, dict) and codes.get("rollback")) or wpd.get(product, "priceInfo", "savingsAmount"):
        found.append(("price_reduction", "priceInfo rollback/savingsAmount"))
    return found


def main() -> None:
    out = Path(sys.argv[1])
    if out.exists():
        raise SystemExit(f"{out} exists")
    out.mkdir(parents=True)
    stages = {v: k for k, v in json.loads((LIVE / "runs.json").read_text(encoding="utf-8")).items()}
    srv = pgserver.get_server(str(Path(r"C:\w7\live\pgdata")), cleanup_mode=None)
    url = make_url(srv.get_uri()).set(database="walmart_live150").render_as_string(hide_password=False)
    eng = create_engine(url.replace("postgresql://", "postgresql+psycopg://", 1))
    with eng.connect() as c:
        c.execute(text("set default_transaction_read_only = on"))
        c.execute(text("begin read only"))
        fetches = [dict(r._mapping) for r in c.execute(text(
            "select pf.id, pf.run_id, pf.purpose, pf.url, a.key, a.sha256 from page_fetches pf join artifacts a on"
            " a.id = pf.dom_artifact_id where pf.run_id = any(:runs) and pf.purpose in"
            " ('listing', 'product_detail', 'product_page') order by pf.started_at"), {"runs": list(stages)})]
    kinds, texts, keys = collections.Counter(), collections.Counter(), collections.Counter()
    key_examples = collections.defaultdict(list)
    tiles = collections.Counter()
    by_item: dict[str, dict] = {}
    pdp: dict[str, list] = {}
    pages_checked = collections.Counter()
    for f in fetches:
        p = DATA / f["key"]
        b = p.read_bytes()
        assert hashlib.sha256(b).hexdigest() == f["sha256"], f["id"]
        nd = wpd.next_data(gzip.decompress(b).decode("utf-8", "replace"))
        pages_checked[f["purpose"]] += 1
        if not nd:
            pages_checked[f"{f['purpose']}_without_next_data"] += 1
            continue
        if f["purpose"] == "listing":
            for raw in raw_tiles(nd):
                for k, v in promo_keys(raw):
                    keys[k] += 1
                    if len(key_examples[k]) < 3:
                        key_examples[k].append(json.dumps(v)[:160])
            for item in wpd.page_items(nd):
                tiles["tiles"] += 1
                classified = [aoff.classify(o, "PICKUP") for o in wrec.offers(item)]
                deals, _other = wrec.deal_texts(item)
                for t in item.badge_texts:
                    texts[("badge", t)] += 1
                for t in item.promo_texts:
                    texts[("promo_text", t)] += 1
                for cl in classified:
                    kinds[(str(cl.kind), cl.offer.text)] += 1
                if item.promo_texts or item.promo_structured or deals:
                    tiles["tiles_with_promotion_wording_or_structure"] += 1
                if item.promo_structured:
                    tiles["tiles_with_promoDiscount"] += 1
                e = by_item.setdefault(item.item_id, {"badges": set(), "promo": set(), "kinds": set(), "struct": 0,
                                                      "pages": set()})
                e["badges"] |= set(item.badge_texts)
                e["promo"] |= set(item.promo_texts)
                e["kinds"] |= {(str(cl.kind), cl.offer.text) for cl in classified}
                e["struct"] += len(item.promo_structured)
                e["pages"].add(f"{stages[f['run_id']]} {f['id']}")
        else:
            product = wpd.get(nd, "props", "pageProps", "initialData", "data", "product") or {}
            item = wpd.item_id_from_url(f["url"])
            pdp.setdefault(item, [])
            pdp[item] += [(c, v, f"{stages[f['run_id']]} {f['id']}") for c, v in page_objects(product)]
            pdp[item].append(("read", "", f"{stages[f['run_id']]} {f['id']}"))
    report, disp = [], collections.Counter()
    for run_id, stage in stages.items():
        recs = json.loads((DATA / "runs" / "walmart-3891-pickup" / run_id / "exports" / "products_fresh.json")
                          .read_text(encoding="utf-8"))
        for r in recs:
            item = wpd.item_id_from_url(r["url"])
            t = by_item.get(item)
            if t is None:
                d = "tile_not_found_in_campaign_pages"
            elif not (t["promo"] or t["struct"] or t["kinds"]):
                d = "absent_on_result_tile"
            elif any(k in ("volume", "digital") for k, _ in t["kinds"]):
                d = "classified_volume_or_digital"
            else:
                d = "promotion_not_volume_or_digital"
            objs = pdp.get(item)
            if objs is None:
                pd = "product_page_not_read_in_campaign"
            elif any(cl == "product_offer" for cl, _v, _p in objs):
                pd = "product_offer_on_campaign_product_page"
            else:
                pd = "no_product_offer_on_campaign_product_page"
            disp[(stage, d, pd)] += 1
            report.append({
                "stage": stage, "run": run_id, "item_id": item, "product_title": r["product_title"],
                "volume_deals_description": r["volume_deals_description"],
                "digital_deals_description": r["digital_deals_description"], "sale_price": r["sale_price"],
                "tile_disposition": d,
                "tile_badges": " | ".join(sorted(t["badges"])) if t else "",
                "tile_promotion_texts": " | ".join(sorted(t["promo"])) if t else "",
                "tile_promoDiscount_structures": str(t["struct"]) if t else "",
                "tile_classified": " | ".join(f"{k}: {x}" for k, x in sorted(t["kinds"])) if t else "",
                "product_page": pd,
                "product_page_objects": " | ".join(f"{cl}: {v} ({p})" for cl, v, p in (objs or []) if cl != "read")[:400],
                "product_page_reads": " | ".join(p for cl, _v, p in (objs or []) if cl == "read"),
            })
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(report[0]), lineterminator="\r\n")
    w.writeheader()
    w.writerows(report)
    (out / "LIVE_OFFER_DISPOSITIONS_1_5_1.csv").write_bytes(("\ufeff" + buf.getvalue()).encode("utf-8"))
    summary = {
        "evidence_class": "OFFLINE REPROCESSING of LIVE pages (the campaign's own stored pages; no request)",
        "pages_checked": dict(pages_checked),
        "tiles": dict(tiles),
        "classified_offer_kinds": {f"{k} | {t}": n for (k, t), n in kinds.most_common()},
        "badge_and_promo_texts": {f"{k} | {t}": n for (k, t), n in texts.most_common(60)},
        "tile_promotion_like_keys": {k: {"count": n, "examples": key_examples[k]} for k, n in keys.most_common(40)},
        "items_with_promoDiscount": sorted(i for i, e in by_item.items() if e["struct"]),
        "product_pages_with_product_offer": sorted(i for i, o in pdp.items() if any(c == "product_offer"
                                                                                  for c, _v, _p in o)),
        "fresh_product_dispositions": {f"{a} | {b} | {c}": n for (a, b, c), n in sorted(disp.items())},
    }
    (out / "LIVE_OFFERS_SUMMARY.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1)[:7000])


if __name__ == "__main__":
    main()
