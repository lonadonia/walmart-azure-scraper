"""Full promoDiscount structure of every distinct result tile that carries one, and every string of that raw tile
that reads like promotion wording (save, buy, off, deal, offer, promo, coupon, clip, rebate, cash, reward), to see
whether terms are displayed anywhere the readers do not look. Offline: stored result pages only.
usage: <collector venv python> -I -X utf8 tile_promo_full.py
"""

import csv
import glob
import gzip
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "C:/w7/wt/headless/walmart-azure-headless/src")
from walmart_headless.sites.walmart import page_data as wpd  # noqa: E402

WORDING = re.compile(r"\b(save|saving|buy|off|deal|offer|promo|coupon|clip|rebate|cash|reward|bogo|free)\b", re.I)
seen = {}
for pf in sorted(glob.glob("C:/w7/b/*/*/*_new_live_*/runs/*/*/db/page_fetches.csv")):
    run_dir = Path(pf).parent.parent
    zip_root = Path(pf).parts[3:5]
    for r in csv.DictReader(open(pf, encoding="utf-8", newline="")):
        if r["purpose"] != "listing":
            continue
        p = run_dir / "pages" / "dom" / f"{r['id']}.html.gz"
        if not p.is_file():
            continue
        nd = wpd.next_data(gzip.decompress(p.read_bytes()).decode("utf-8", "replace"))
        for st in wpd._stacks(nd):
            if not isinstance(st, dict):
                continue
            for it in st.get("items") or []:
                if not isinstance(it, dict) or not isinstance(it.get("promoDiscount"), dict):
                    continue
                pdx = it["promoDiscount"]
                if not any(v not in (None, False, "", 0, []) for v in pdx.values()):
                    continue
                key = (it.get("usItemId"), json.dumps(pdx, sort_keys=True))
                wording = sorted({f"{k}={v[:120]}" for k, v in wpd.walk(it, "") if isinstance(v, str)
                                  and WORDING.search(v) and not k.endswith(("canonicalUrl", "image", "imageInfo"))})
                ent = seen.setdefault(key, {"item": it.get("usItemId"), "name": (it.get("name") or "")[:70],
                                            "promoDiscount": pdx, "wording": wording, "where": []})
                ent["where"].append(f"{'/'.join(zip_root)} run {run_dir.name} page_fetch {r['id']} "
                                    f"observed {r.get('fetched_at') or r.get('observed_at') or ''} {r['url'][:90]}")
for (item, _), e in seen.items():
    print("=" * 100)
    print(e["item"], e["name"])
    print(" promoDiscount:", json.dumps(e["promoDiscount"]))
    print(" wording in the raw tile:")
    for w in e["wording"][:15]:
        print("   ", w)
    for w in e["where"]:
        print("  at", w)
