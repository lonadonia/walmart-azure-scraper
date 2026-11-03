"""Release 1.5.2: checks of the S6 replay on the PC, by reading its exports. Nothing is changed.

usage: python -I -X utf8 s6_checks_152.py EXPORTS
"""

from __future__ import annotations

import collections
import csv
import json
import sys
from pathlib import Path

x = Path(sys.argv[1])
man = json.loads((x / "manifest.json").read_text("utf-8"))
val = json.loads((x / "validation_report.json").read_text("utf-8"))
prod = json.loads((x / "products.json").read_text("utf-8"))
rows = prod["products"] if isinstance(prod, dict) else prod
fresh = json.loads((x / "products_fresh.json").read_text("utf-8"))
fresh = fresh["products"] if isinstance(fresh, dict) else fresh
prov = json.loads((x / "provenance.json").read_text("utf-8"))
rm = json.loads((x / "record_map.json").read_text("utf-8"))
disp = json.loads((x / "field_dispositions.json").read_text("utf-8"))
print("manifest keys", sorted(man)[:40])
print("counts", {k: man[k] for k in man if "count" in k.lower() or "products" in k.lower()})
print("validation", {k: v for k, v in val.items() if not isinstance(v, (list, dict))})
print("rows", len(rows), "fresh", len(fresh), "provenance", len(prov["records"]), "dispositions", len(disp))
print("record_map type", type(rm).__name__, (list(rm)[:6] if isinstance(rm, dict) else rm[0]))
print("observation_kind", collections.Counter(d.get("observation_kind") for d in disp))
for f in ("upc", "weight"):
    print(f, "disposition", collections.Counter((d.get(f) or {}).get("disposition") for d in disp).most_common())
    print(f, "reason", collections.Counter((d.get(f) or {}).get("reason") for d in disp).most_common(8))
print("store_brand", collections.Counter(r["store_brand"] for r in rows))
print("blank upc", sum(1 for r in rows if not r["upc"]), "blank weight", sum(1 for r in rows if not r["weight"]))
print("gupc distinct", len({r["gupc"] for r in rows if r["gupc"]}))
mk = collections.Counter()
for key, rec in prov["records"].items():
    for f, kind in (rec.get("missing_kind") or {}).items():
        mk[(f, kind)] += 1
print("missing_kind", mk.most_common(30))
wanted = {
    "18472720019": "30 lb",
    "18468708077": "24 lbs",
    "18511760810": "15 lbs",
    "20636621408": "30 lbs",
    "18529653937": "15 lbs",
}
for r in rows:
    item = r["url"].rsplit("/", 1)[-1].split("?")[0]
    if item in wanted:
        print(item, repr(r["weight"]), "|", r["product_title"][:90])
