"""What product.promoData, product.discounts and the tile promoDiscount hold on the saved pages (offline)."""

import collections
import glob
import csv
import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, "C:/w7/wt/headless/walmart-azure-headless/src")
from walmart_headless.sites.walmart import page_data as wpd  # noqa: E402

idx = json.loads(Path("C:/w7/b/detail_capture_index_150.json").read_text(encoding="utf-8"))
seen, shapes, texts, disc = set(), collections.Counter(), collections.Counter(), collections.Counter()
examples = collections.defaultdict(list)
for e in idx:
    if e["item_id"] in seen:
        continue
    seen.add(e["item_id"])
    nd = wpd.next_data(gzip.decompress((Path("C:/w7/b") / e["path"]).read_bytes()).decode("utf-8", "replace"))
    product = wpd.get(nd, "props", "pageProps", "initialData", "data", "product") or {}
    for pd in product.get("promoData") or []:
        if not isinstance(pd, dict):
            continue
        key = (pd.get("type"), pd.get("templateData", {}).get("priceString") if isinstance(pd.get("templateData"), dict) else None)
        shapes[json.dumps(sorted(pd.keys()))] += 1
        t = pd.get("type") or pd.get("promoType") or ""
        desc = json.dumps({k: pd.get(k) for k in ("type", "description", "terms", "templateData", "message",
                                                  "promoId", "offerName", "promoType", "subType") if pd.get(k)})[:300]
        texts[desc] += 1
        if len(examples[t]) < 3:
            examples[t].append((e["item_id"], json.dumps(pd)[:700]))
    d = product.get("discounts") or {}
    if isinstance(d, dict):
        for m in d.get("discountMetaData") or []:
            if isinstance(m, dict):
                disc[json.dumps({k: m.get(k) for k in m if k != "savings"})[:200]] += 1
print("promoData shapes:", shapes.most_common(5))
print("promoData texts:")
for k, n in texts.most_common(25):
    print(" ", n, k)
print("discountMetaData:")
for k, n in disc.most_common(10):
    print(" ", n, k)
for t, ex in examples.items():
    print("== type", t)
    for i, x in ex:
        print("  ", i, x)
# Tile promoDiscount (result pages)
print("== tile promoDiscount")
for pf in glob.glob("C:/w7/b/*/*/*_new_live_*/runs/*/*/db/page_fetches.csv"):
    run_dir = Path(pf).parent.parent
    for r in csv.DictReader(open(pf, encoding="utf-8", newline="")):
        if r["purpose"] != "listing":
            continue
        p = run_dir / "pages" / "dom" / f"{r['id']}.html.gz"
        if not p.is_file():
            continue
        nd = wpd.next_data(gzip.decompress(p.read_bytes()).decode("utf-8", "replace"))
        for st in wpd._stacks(nd):
            for it in (st or {}).get("items") or [] if isinstance(st, dict) else []:
                if isinstance(it, dict) and isinstance(it.get("promoDiscount"), dict):
                    pdx = it["promoDiscount"]
                    if any(v not in (None, False, "", 0, []) for v in pdx.values()):
                        print("  ", run_dir.name, it.get("usItemId"), (it.get("name") or "")[:60], json.dumps(pdx)[:400])
