"""Offers audit on authentic saved sources (brief section 6), offline: no request.

Sources: every stored result page (purpose listing) of the delivered 1.4.1 edition evidence (extracted under
C:/w7/b), which includes Oxylabs B3's 19 result pages, and the 1,441 saved product pages of the capture index.
For every result tile: the promotion wording and structures the collector reads (badges, promotion objects,
promoDiscount; sites/walmart/page_data.py) and how release 1.5.0 classifies each one (sites/walmart/records.py
offers() -> assembly/offers.py classify(), configured modality PICKUP); plus every key of the tile whose name
looks like a promotion (promo, deal, offer, coupon, rebate, reward, cash, clip, bogo, rollback, clearance,
saving, member, ebt, snap), to find promotion data the readers do not look at.
Then, per exported B3 product (the replay of attempt 2), the disposition of its volume and digital fields:
  absent_on_result_tile     its tile states no promotion wording or structure at all
  promotion_not_volume_or_digital  wording is present and classified otherwise (sale badge, other promo...)
  volume / digital          classified into the field (none expected: both B3 fields are empty)
and whether its saved product page (if any) states a promotion the tile does not (product_page_promotion).
usage: <collector venv python> -I offers_audit.py OUT_DIR
"""

import collections
import csv
import glob
import gzip
import io
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "C:/w7/wt/headless/walmart-azure-headless/src")
from walmart_headless.assembly import offers as aoff  # noqa: E402
from walmart_headless.sites.walmart import page_data as wpd  # noqa: E402
from walmart_headless.sites.walmart import records as wrec  # noqa: E402

PROMO_KEY = re.compile(
    r"promo|deal|offer|coupon|rebate|reward|cash|clip|bogo|rollback|clearance|saving|member|ebt|snap|wplus", re.I
)
SKIP_KEYS = re.compile(r"^(offerId|offerType|sellerOfferId|offerPrice|availableOffers?)$", re.I)
B3 = "01M60V2DCCWR72BGVVG3EM9R74"
RP_EXP = Path("C:/w7/evidence/reprocessing_b3/export_replay_1_5_0")


def raw_tiles(nd):
    """Every raw item dict of the page's item stacks (the shapes parse_item reads)."""
    for st in wpd._stacks(nd):
        if not isinstance(st, dict):
            continue
        for it in st.get("items") or []:
            if isinstance(it, dict):
                yield it


def promo_keys(obj, path=""):
    for p, v in wpd.walk(obj, path):
        last = p.rsplit(".", 1)[-1]
        last = re.sub(r"\[\d+\]$", "", last)
        if PROMO_KEY.search(last) and not SKIP_KEYS.match(last):
            if v not in (None, "", [], {}, False, 0):
                yield re.sub(r"\[\d+\]", "[]", p), v


def main() -> None:
    out = Path(sys.argv[1])
    if out.exists():
        raise SystemExit(f"{out} exists")
    out.mkdir(parents=True)
    pages = []
    for pf in glob.glob("C:/w7/b/*/*/*_new_live_*/runs/*/*/db/page_fetches.csv"):
        run_dir = Path(pf).parent.parent
        for r in csv.DictReader(open(pf, encoding="utf-8", newline="")):
            if r["purpose"] != "listing":
                continue
            p = run_dir / "pages" / "dom" / f"{r['id']}.html.gz"
            if p.is_file():
                pages.append((run_dir.name, r["id"], r["url"], p))
    kinds = collections.Counter()
    texts = collections.Counter()
    keys = collections.Counter()
    key_examples = collections.defaultdict(list)
    tiles_with = collections.Counter()
    by_item = {}  # B3's tiles: item -> what its tile shows
    for run, fid, url, p in pages:
        nd = wpd.next_data(gzip.decompress(p.read_bytes()).decode("utf-8", "replace"))
        if not nd:
            continue
        for raw in raw_tiles(nd):
            for k, v in promo_keys(raw):
                keys[k] += 1
                if len(key_examples[k]) < 3:
                    key_examples[k].append(json.dumps(v)[:160])
        for item in wpd.page_items(nd):
            tiles_with["tiles"] += 1
            obs = wrec.offers(item)
            deals, other = wrec.deal_texts(item)
            classified = [aoff.classify(o, "PICKUP") for o in obs]
            for t in item.badge_texts:
                texts[("badge", t)] += 1
            for t in item.promo_texts:
                texts[("promo_text", t)] += 1
            for c in classified:
                kinds[(str(c.kind), c.offer.text)] += 1
            if item.promo_texts or item.promo_structured or deals:
                tiles_with["tiles_with_promotion_wording_or_structure"] += 1
            if item.promo_structured:
                tiles_with["tiles_with_promoDiscount"] += 1
            if run == B3:
                prior = by_item.get(item.item_id) or {"badges": set(), "promo": set(), "kinds": set(), "struct": 0}
                prior["badges"] |= set(item.badge_texts)
                prior["promo"] |= set(item.promo_texts)
                prior["kinds"] |= {(str(c.kind), c.offer.text) for c in classified}
                prior["struct"] += len(item.promo_structured)
                by_item[item.item_id] = prior
    # Saved product pages: promotion keys on the product object.
    idx = json.loads(Path("C:/w7/b/detail_capture_index_150.json").read_text(encoding="utf-8"))
    pdp_promo = {}
    pdp_keys = collections.Counter()
    seen = set()
    for e in idx:
        if e["item_id"] in seen:
            continue
        seen.add(e["item_id"])
        nd = wpd.next_data(gzip.decompress((Path("C:/w7/b") / e["path"]).read_bytes()).decode("utf-8", "replace"))
        product = wpd.get(nd, "props", "pageProps", "initialData", "data", "product") or {}
        found = []
        for k, v in promo_keys(product, "product"):
            pdp_keys[k] += 1
        # What the page's promotion objects are: payment or financing advertising (promoData 1PAYCC,
        # ONE_PREQUAL), the Walmart+ subscription placeholder (discounts wplus_subscription), a price reduction
        # (rollback, savingsAmount: the sale price's own evidence), or anything else (a product offer).
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
        pdp_promo[e["item_id"]] = found
    # Per B3 product (attempt 2's replay export).
    rows = json.loads((RP_EXP / "products.json").read_text(encoding="utf-8"))
    rows = rows["products"] if isinstance(rows, dict) else rows
    rm = json.loads((RP_EXP / "record_map.json").read_text(encoding="utf-8"))
    kind_of = {r["key"]: r.get("observation_kind") for r in rm["rows"]}
    report, disp = [], collections.Counter()
    for r in rows:
        item = wpd.item_id_from_url(r["url"])
        okind = kind_of.get(f"wm:{item}", "")
        t = by_item.get(item)
        if okind != "replayed":
            continue  # the 200 carried rows were observed by earlier runs, not by B3's pages
        if t is None:
            d = "tile_not_found_in_B3_pages"
        elif not (t["promo"] or t["struct"] or t["kinds"]):
            d = "absent_on_result_tile"
        elif any(k in ("volume", "digital") for k, _ in t["kinds"]):
            d = "classified_volume_or_digital"
        else:
            d = "promotion_not_volume_or_digital"
        pdp = pdp_promo.get(item)
        if pdp is None:
            pd = "product_page_not_read (B3's detail limit was 0; no saved page of the item)"
        elif any(c == "product_offer" for c, _ in pdp):
            pd = "product_offer_on_saved_product_page"
        else:
            pd = "no_product_offer_on_saved_product_page"
        disp[(d, pd)] += 1
        report.append({
            "item_id": item,
            "product_title": r["product_title"],
            "volume_deals_description": r["volume_deals_description"],
            "digital_deals_description": r["digital_deals_description"],
            "sale_price": r["sale_price"],
            "tile_disposition": d,
            "tile_badges": " | ".join(sorted(t["badges"])) if t else "",
            "tile_promotion_texts": " | ".join(sorted(t["promo"])) if t else "",
            "tile_classified": " | ".join(f"{k}: {x}" for k, x in sorted(t["kinds"])) if t else "",
            "product_page": pd,
            "product_page_promotion_objects": " | ".join(f"{c}: {v}" for c, v in (pdp or [])[:6]),
            "volume_disposition": "absent" if d == "absent_on_result_tile" else d,
            "digital_disposition": "absent" if d == "absent_on_result_tile" else d,
        })
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(report[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(report)
    (out / "B3_OFFER_DISPOSITIONS.csv").write_bytes(("\ufeff" + buf.getvalue()).encode("utf-8"))
    summary = {
        "evidence_class": "OFFLINE REPROCESSING (authentic saved pages; no request)",
        "listing_pages_read": len(pages),
        "tiles": dict(tiles_with),
        "classified_offer_kinds": {f"{k} | {t}": n for (k, t), n in kinds.most_common()},
        "badge_and_promo_texts": {f"{k} | {t}": n for (k, t), n in texts.most_common(60)},
        "tile_promotion_like_keys": {k: {"count": n, "examples": key_examples[k]} for k, n in keys.most_common(60)},
        "product_page_promotion_like_keys": dict(pdp_keys.most_common(60)),
        "B3_662_dispositions": {f"{a} | {b}": n for (a, b), n in sorted(disp.items())},
    }
    (out / "OFFERS_AUDIT_SUMMARY.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8",
                                                   newline="\n")
    print(json.dumps(summary, indent=1)[:9000])


if __name__ == "__main__":
    main()
