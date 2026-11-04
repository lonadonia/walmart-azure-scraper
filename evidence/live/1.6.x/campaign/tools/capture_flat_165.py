"""Copies two authentic listing pages of live run L10 (release 1.6.4) into the collector's test captures for
release 1.6.5, byte for byte, with their manifest, and the run's exported records of the items they hold (offline;
no request). Run with an edition's Python (the harness's database).

usage: python -I -X utf8 capture_flat_165.py OUT_DIR
"""

from __future__ import annotations

import gzip
import hashlib
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

RUN = "01M6KA3CKYJSD6WDY4TDAAV73Y"
DATA = Path(r"C:\w9\live\data")
RUN_DIR = DATA / "runs" / "walmart-3891-pickup" / RUN
PAGES = {
    "flat_layout_page.html.gz": "01M6KB69AJA2N65MDQP4V1QWTE",
    "price_lines_page.html.gz": "01M6KB1YNCARK7HQ80N2KNCE23",
}
NEXT = re.compile(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)
ITEM = re.compile(r"/ip/(?:[^/?#]+/)?(\d+)")


def item_ids(html: str) -> list[str]:
    nd = json.loads(NEXT.search(html).group(1))
    sr = nd["props"]["pageProps"]["initialData"]["searchResult"]
    return [str(it["usItemId"]) for st in sr["itemStacks"] for it in (st.get("items") or []) if it.get("usItemId")]


def main() -> int:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    eng = create_engine(h.db_url())
    manifest = []
    with eng.connect() as c:
        for name, fetch in PAGES.items():
            row = c.execute(
                text("SELECT url, started_at FROM page_fetches WHERE id=:f AND run_id=:r"),
                {"f": fetch, "r": RUN},
            ).mappings().one()
            stored = (RUN_DIR / "live" / "dom" / f"{fetch}.html.gz").read_bytes()
            raw = gzip.decompress((RUN_DIR / "live" / "raw" / f"{fetch}.listing.body.gz").read_bytes())
            (out / name).write_bytes(stored)
            manifest.append({
                "file": name,
                "fetch_id": fetch,
                "url": row["url"],
                "fetched_at": str(row["started_at"]),
                "run": RUN,
                "release": "1.6.4",
                "source": f"campaign evidence store: runs/walmart-3891-pickup/{RUN}/live/dom/{fetch}.html.gz",
                "source_sha256": hashlib.sha256(stored).hexdigest(),
                "content_sha256": hashlib.sha256(gzip.decompress(stored)).hexdigest(),
                "raw_original_body_sha256": hashlib.sha256(raw).hexdigest(),
                "copied": "byte for byte: the collector's stored copy (sanitized at capture by release 1.6.4), not recompressed",
            })
    flat_ids = item_ids(gzip.decompress((out / "flat_layout_page.html.gz").read_bytes()).decode("utf-8"))
    products = json.loads((RUN_DIR / "exports" / "products.json").read_text("utf-8"))
    rmap = json.loads((RUN_DIR / "exports" / "record_map.json").read_text("utf-8"))["rows"]
    flat_fetch = PAGES["flat_layout_page.html.gz"]
    # The run's exported records that it read from the flat page (record_map.json names each record's page).
    read_here = {r["url"] for r in rmap if (r.get("page") or {}).get("page_fetch_id") == flat_fetch}
    records = [r for r in products if r["url"] in read_here]
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8", newline="\n")
    (out / "l10_records.json").write_text(json.dumps(records, indent=1, ensure_ascii=False) + "\n",
                                          encoding="utf-8", newline="\n")
    print(json.dumps({"pages": [m["file"] for m in manifest], "flat_page_items": len(flat_ids),
                      "distinct": len(set(flat_ids)), "records_read_from_the_flat_page": len(records)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
