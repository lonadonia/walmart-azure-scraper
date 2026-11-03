"""What Walmart's own product pages say about who makes each brand: every saved product page's brand, manufacturer and
any private-brand mark, per brand. Offline; reads the capture index. usage: python brand_evidence_152.py OUT.json"""
import collections
import gzip
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "C:/w7/wt/headless/walmart-azure-headless/src")
from walmart_headless.sites.walmart import page_data as wpd  # noqa: E402

idx = json.loads(Path("C:/w7/b/detail_capture_index_150.json").read_text(encoding="utf-8"))
seen = set()
by_brand: dict[str, dict] = {}
marks = collections.Counter()
PRIVATE = re.compile(r"private.?(?:brand|label)|walmart.?(?:brand|own|exclusive)|ownBrand|isWalmart", re.I)
for e in idx:
    if e["item_id"] in seen:
        continue
    seen.add(e["item_id"])
    html = gzip.decompress((Path("C:/w7/b") / e["path"]).read_bytes()).decode("utf-8", "replace")
    nd = wpd.next_data(html)
    if not nd:
        continue
    for m in PRIVATE.finditer(html):
        marks[html[max(0, m.start() - 30) : m.end() + 40]] += 1
    data = wpd.get(nd, "props", "pageProps", "initialData", "data") or {}
    product = data.get("product") or {}
    idml = data.get("idml") or {}
    brand = str(product.get("brand") or "")
    mfr = str(product.get("manufacturerName") or "")
    specs = {str(s.get("name")): str(s.get("value")) for s in (idml.get("specifications") or []) if isinstance(s, dict)}
    entry = by_brand.setdefault(brand, {"pages": 0, "manufacturer_name": collections.Counter(), "spec_manufacturer": collections.Counter(), "seller": collections.Counter(), "items": []})
    entry["pages"] += 1
    entry["manufacturer_name"][mfr] += 1
    entry["spec_manufacturer"][specs.get("Manufacturer", "")] += 1
    entry["seller"][str(product.get("sellerDisplayName") or product.get("sellerName") or "")] += 1
    if len(entry["items"]) < 3:
        entry["items"].append(e["item_id"])
out = {
    "pages_read": len(seen),
    "private_marks": marks.most_common(25),
    "brands": {
        b: {**v, "manufacturer_name": v["manufacturer_name"].most_common(4), "spec_manufacturer": v["spec_manufacturer"].most_common(4), "seller": v["seller"].most_common(3)}
        for b, v in sorted(by_brand.items(), key=lambda kv: -kv[1]["pages"])
    },
}
Path(sys.argv[1]).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(out["pages_read"], len(out["brands"]))
print(out["private_marks"][:12])
wal = {b: v for b, v in out["brands"].items() if any("wal" in str(n).lower() for n, _ in v["manufacturer_name"] + v["spec_manufacturer"])}
for b, v in wal.items():
    print(b, v["pages"], v["manufacturer_name"][:2], v["spec_manufacturer"][:2], v["seller"][:1])
print("--- the candidates")
for b in ("Prima Della", "Clear American", "ReliOn", "Special Kitty", "Vibrant Life", "Pure Balance", "Pure Balance Pro+", "Great Value", "Equate", "Ol' Roy"):
    if b in out["brands"]:
        v = out["brands"][b]
        print(b, v["pages"], v["manufacturer_name"][:3], v["spec_manufacturer"][:3], v["seller"][:2], v["items"])
    else:
        print(b, "no saved page")
