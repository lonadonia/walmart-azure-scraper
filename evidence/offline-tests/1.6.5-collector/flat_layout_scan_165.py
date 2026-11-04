"""Which price layout each stored live page uses (release 1.6.5's evidence). Reads every stored page copy
(`live/dom/<fetch>.html.gz`) of every live run of store 3891 Pickup on the workstation, and sorts each product
placement on it by where its prices are given:

- `price_lines`: `priceInfo.priceDetails.priceLines` (the layout of almost every page);
- `nested`: `priceInfo.currentPrice` as an object with `priceString`;
- `flat_only`: flat display strings only (`linePriceDisplay`, `linePrice`, `itemPrice`, or `currentPrice` as a string),
  the layout that release 1.6.4's source check could not read;
- `no_price`: none of these (a placement that shows no price).

A placement is a product of a listing page's result grid (`searchResult.itemStacks`) or the product of a product page
(`data.product`). Each run's release is the `parser_version` the run database recorded for it. No request is made.

usage: python -I flat_layout_scan_165.py OUT.json
"""

from __future__ import annotations

import gzip
import json
import os
import re
import sys
from pathlib import Path

os.environ["PSYCOPG_IMPL"] = "python"
os.environ["PATH"] = (
    "C:/w9/live/ed/walmart-oxylabs-1.6.0/.venv/Lib/site-packages/pgserver/pginstall/bin"
    + os.pathsep
    + os.environ.get("PATH", "")
)
sys.path.insert(0, "C:/w9/live")
import live160_run as h  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402

ROOT = Path(r"C:\w9\live\data\runs\walmart-3891-pickup")
LABELS = {v: k for k, v in json.loads(Path(r"C:\w9\evidence\live160\runs.json").read_text(encoding="utf-8")).items()}
NEXT = re.compile(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)
FLAT_KEYS = ("linePriceDisplay", "linePrice", "itemPrice")


def kind_of(info: dict) -> str:
    if (info.get("priceDetails") or {}).get("priceLines"):
        return "price_lines"
    if isinstance(info.get("currentPrice"), dict):
        return "nested"
    flat = any(isinstance(info.get(k), str) and info.get(k) for k in FLAT_KEYS)
    if flat or (isinstance(info.get("currentPrice"), str) and info.get("currentPrice")):
        return "flat_only"
    return "no_price"


def placements(html: str) -> tuple[str, list[dict]]:
    m = NEXT.search(html)
    if not m:
        return "no_page_data", []
    init = ((json.loads(m.group(1)).get("props") or {}).get("pageProps") or {}).get("initialData") or {}
    sr = init.get("searchResult")
    if isinstance(sr, dict):
        its = [it for st in sr.get("itemStacks") or [] for it in (st or {}).get("items") or []
               if isinstance(it, dict) and it.get("usItemId")]
        return "listing", its
    data = init.get("data")
    prod = data.get("product") if isinstance(data, dict) else None
    if isinstance(prod, dict) and prod.get("usItemId"):
        return "product", [prod]
    return "other", []


def main() -> int:
    out = Path(sys.argv[1])
    eng = create_engine(h.db_url())
    with eng.connect() as c:
        meta = {r["id"]: r for r in c.execute(text("SELECT id, parser_version, started_at FROM runs")).mappings()}
    runs = []
    for run_dir in sorted(p for p in ROOT.iterdir() if (p / "live" / "dom").is_dir()):
        m = meta[run_dir.name]
        row = {"label": LABELS.get(run_dir.name, ""), "run_id": run_dir.name, "release": m["parser_version"],
               "started_at": m["started_at"].isoformat(), "pages": {}, "placements": {}, "pages_with_flat_only": []}
        for p in sorted((run_dir / "live" / "dom").glob("*.html.gz")):
            kind, its = placements(gzip.decompress(p.read_bytes()).decode("utf-8", "replace"))
            row["pages"][kind] = row["pages"].get(kind, 0) + 1
            kinds = [kind_of(it.get("priceInfo") or {}) for it in its]
            for k in kinds:
                row["placements"][k] = row["placements"].get(k, 0) + 1
            if "flat_only" in kinds:
                row["pages_with_flat_only"].append({"fetch": p.name.removesuffix(".html.gz"), "page_kind": kind,
                                                    "flat_only": kinds.count("flat_only"), "placements": len(kinds)})
        runs.append(row)

    def total(rows: list[dict]) -> dict:
        t = {"runs": len(rows), "pages": 0, "placements": {}, "pages_with_flat_only": 0}
        for r in rows:
            t["pages"] += sum(r["pages"].values())
            for k, v in r["placements"].items():
                t["placements"][k] = t["placements"].get(k, 0) + v
            t["pages_with_flat_only"] += len(r["pages_with_flat_only"])
        t["placements"]["all"] = sum(v for k, v in t["placements"].items() if k != "all")
        return dict(t, releases=sorted({r["release"] for r in rows}))

    before = [r for r in runs if r["release"] != "1.6.5"]
    result = {
        "tool": "flat_layout_scan_165.py",
        "store": "walmart-3891-pickup",
        "before_1_6_5": total(before),
        "on_1_6_5": total([r for r in runs if r["release"] == "1.6.5"]),
        "runs": runs,
    }
    out.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("before_1_6_5", "on_1_6_5")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
