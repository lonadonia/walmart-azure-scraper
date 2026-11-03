"""For the items whose result tile carries a promoDiscount structure: does a saved product page of the item display
the offer's terms? Prints every string of the product page's __NEXT_DATA__ that reads like offer wording, with its
path, and the product page's promotion objects. Offline: the capture index's saved pages only.
usage: <collector venv python> -I -X utf8 pdp_offer_wording.py ITEM [ITEM...]
"""

import gzip
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "C:/w7/wt/headless/walmart-azure-headless/src")
from walmart_headless.sites.walmart import page_data as wpd  # noqa: E402

WORDING = re.compile(
    r"(buy \d|buy more|save \$|\bsave\b|\boff\b|\bbogo\b|coupon|clip|rebate|walmart cash|reward|"
    r"promo|deal|offer|when you buy|each when|for \$|\d+ for )",
    re.I,
)
SKIP = re.compile(r"(seo|canonical|image|url|description|shortDescription|longDescription|specification)$", re.I)
idx = json.loads(Path("C:/w7/b/detail_capture_index_150.json").read_text(encoding="utf-8"))
want = set(sys.argv[1:])
for e in idx:
    if e["item_id"] not in want:
        continue
    raw = gzip.decompress((Path("C:/w7/b") / e["path"]).read_bytes()).decode("utf-8", "replace")
    nd = wpd.next_data(raw)
    print("=" * 100)
    print(e["item_id"], e["run_id"], e.get("page_fetch_id"), e["observed_at"], e["path"])
    product = wpd.get(nd, "props", "pageProps", "initialData", "data", "product") or {}
    print(" name:", product.get("name"))
    for key in ("promoData", "promoDiscount", "discounts", "offerType", "flag", "badges"):
        if product.get(key):
            print(f" product.{key}:", json.dumps(product.get(key))[:700])
    hits = set()
    for p, v in wpd.walk(nd, ""):
        if isinstance(v, str) and WORDING.search(v) and not SKIP.search(p.rsplit(".", 1)[-1]):
            if len(v) < 300:
                hits.add((re.sub(r"\[\d+\]", "[]", p)[-110:], v[:200]))
    for p, v in sorted(hits)[:60]:
        print("   ", p, "=", v)
    print(" (offer-like strings:", len(hits), ")")
