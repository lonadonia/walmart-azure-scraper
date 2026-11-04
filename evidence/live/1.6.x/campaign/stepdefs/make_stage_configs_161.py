"""Stage configurations on release 1.6.1 (L3, L2b, census and repeat): the frozen 1.6.1 edition's
config/collector.yaml, byte for byte, except (1) its four relative file names made absolute (the copy lives outside
the edition's folder) and (2) for a stage with listings below, the store's follow_up.seeds: the products of the
1.5.2 exact live-read queue on the stage's listings. A stage with no listings keeps the edition's own "seeds: []"
line. Nothing else changes.

A seed's URL is the queue's identity column when it is a product link; otherwise the link the store's follow-up
queue recorded when a run named it. A seed with no recorded link would be reported, not invented.

usage: python -I make_stage_configs_161.py   (writes C:/w9/evidence/live160/configs/collector.<stage>.yaml,
seeds_<stage>.csv and stage_configs_161.json)
"""

import csv
import hashlib
import json
import os
import sys
import zlib
from collections import Counter
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

ED = Path("C:/w9/live/ed/walmart-oxylabs-1.6.1/config")
OUT = Path("C:/w9/evidence/live160/configs")
QUEUE = Path(
    "C:/w8/repo/evidence/reconciliation/1.5.2/sponsored_and_variant_reconciliation/EXACT_LIVE_READ_QUEUE_1_5_2.csv"
)
STAGES: dict[str, list[str]] = {
    "l3_161": [],
    "l2b_161": ["1005862_1071969", "5427_486190"],
    "l4r_161": [],
    "census_161": [],
    "l5_161": [],
}
SEEDS_LINE = "      seeds: []                    # items an earlier report named, read first: {kind, item_id, url, listing_id}\n"

rows = list(csv.DictReader(QUEUE.open(encoding="utf-8-sig")))
assert len(rows) == 275 and len({r["item_id"] for r in rows}) == 275
eng = create_engine(h.db_url())
with eng.connect() as c:
    c.execute(text("SET TRANSACTION READ ONLY"))
    queued = {
        str(i): (u, run)
        for i, u, run in c.execute(
            text("SELECT item_id, url, first_seen_run FROM follow_up_queue WHERE kind='variant' AND url IS NOT NULL")
        )
    }

base = (ED / "collector.yaml").read_bytes().decode("utf-8")
for name in ("settings.yaml", "stores.yaml", "Walmart_Category_URLs.csv", "walmart_private_label_brands.yaml"):
    assert base.count(f": {name}") == 1, name
assert base.count(SEEDS_LINE) == 1
OUT.mkdir(parents=True, exist_ok=True)
summary = {}
for stage, listings in STAGES.items():
    seeds = []
    for n, r in enumerate(rows, start=2):  # CSV line numbers (the header is line 1)
        lid = r["listing"].split(" ", 1)[0]
        if lid not in listings:
            continue
        if r["identity"].startswith("https://www.walmart.com/ip/"):
            url, how = r["identity"], "the queue's identity link"
        elif r["item_id"] in queued:
            url, how = queued[r["item_id"]][0], f"the store's follow-up queue (named by run {queued[r['item_id']][1]})"
        else:
            raise SystemExit(f"no recorded link for {r['item_id']}: report it, never invent one")
        seeds.append(
            {
                "kind": "variant",
                "item_id": r["item_id"],
                "url": url,
                "listing_id": lid,
                "named_by": "",
                "source": f"EXACT_LIVE_READ_QUEUE_1_5_2.csv line {n} ({r['kind']}); link from {how}",
            }
        )
    text_cfg = base
    for name in ("settings.yaml", "stores.yaml", "Walmart_Category_URLs.csv", "walmart_private_label_brands.yaml"):
        text_cfg = text_cfg.replace(f": {name}", f": {(ED / name).as_posix()}")
    if seeds:
        block = "      seeds:\n" + "".join("        - " + json.dumps(s, ensure_ascii=False) + "\n" for s in seeds)
        text_cfg = text_cfg.replace(SEEDS_LINE, block)
        with (OUT / f"seeds_{stage}.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(seeds[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(seeds)
    p = OUT / f"collector.{stage}.yaml"
    p.write_bytes(text_cfg.encode("utf-8"))
    summary[stage] = {
        "config": str(p),
        "sha256": hashlib.sha256(text_cfg.encode("utf-8")).hexdigest(),
        "edition_config_sha256": hashlib.sha256(base.encode("utf-8")).hexdigest(),
        "seeds": len(seeds),
        "by_listing": dict(Counter(s["listing_id"] for s in seeds)),
        "links_from_queue": sum(1 for s in seeds if "follow-up queue" in s["source"]),
        "seeds_per_shard_of_2": dict(Counter(zlib.crc32(s["item_id"].encode()) % 2 for s in seeds)),
    }
(OUT / "stage_configs_161.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=1))
