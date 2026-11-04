"""Offline sizing of stage L2 (no request): for each listing page the store's runs read, the products seen there,
their latest record status, whether an earlier read of their own page is reusable (the collector's own rule,
``WalmartCollector.saved_details``, 30 days), and the 1.5.2 exact live-read queue joined by item id.

usage: python -I plan_l2.py OUT_JSON
"""

import csv
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta

os.environ["PSYCOPG_IMPL"] = "python"
os.environ["PATH"] = (
    "C:/w9/live/ed/walmart-oxylabs-1.6.0/.venv/Lib/site-packages/pgserver/pginstall/bin"
    + os.pathsep
    + os.environ.get("PATH", "")
)
sys.path.insert(0, "C:/w9/live")
import live160_run as h  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402

QUEUE = (
    "C:/w8/repo/evidence/reconciliation/1.5.2/sponsored_and_variant_reconciliation/EXACT_LIVE_READ_QUEUE_1_5_2.csv"
)
FD = "C:/w9/evidence/live160/runs/L1/exports/field_dispositions.csv"
STORE = "walmart-3891-pickup"
NOW = datetime.now(UTC)
SINCE = NOW - timedelta(days=30)

eng = create_engine(h.db_url())
with eng.connect() as c:
    c.execute(text("SET TRANSACTION READ ONLY"))
    store_id = c.execute(text("SELECT id FROM stores WHERE key=:k"), {"k": STORE}).scalar_one()
    # The reusable reads, as saved_details builds them.
    saved: dict[str, str] = {}
    for key, prov in c.execute(
        text(
            "SELECT r.upc, r.provenance FROM records r JOIN runs u ON u.id=r.run_id WHERE u.store_id=:s AND "
            "u.mode='LIVE' AND r.provenance ? 'upc_detail'"
        ),
        {"s": store_id},
    ):
        d = (prov or {}).get("upc_detail") or {}
        at = str(d.get("requested_at") or "")
        if d.get("status") != "extracted" or not d.get("fresh") or not d.get("value") or not at:
            continue
        if datetime.fromisoformat(at.replace("Z", "+00:00")) < SINCE:
            continue
        saved[str(d.get("item_id") or key.removeprefix("wm:"))] = "extracted (fetched by a run)"
    for item, status, sizes in c.execute(
        text(
            "SELECT item_id, status, size_statements FROM detail_observations WHERE store_id=:s AND observed_at>=:t "
            "ORDER BY observed_at, id"
        ),
        {"s": store_id, "t": SINCE},
    ):
        if status != "extracted" and saved.get(item, "").startswith("extracted"):
            continue
        saved[item] = f"{status}{' (sizes)' if sizes is not None else ' (no sizes)'}"
    # Every listing page read, newest run first, with its products and their record in that run.
    pages: dict[tuple[str, int], dict] = {}
    for run_id, listing, page, keys in c.execute(
        text(
            "SELECT m.run_id, m.taxonomy_id, m.page_offset, array_agg(m.upc ORDER BY m.position) FROM memberships m "
            "JOIN runs u ON u.id=m.run_id WHERE u.store_id=:s AND u.mode='LIVE' GROUP BY 1,2,3 "
            "ORDER BY max(u.created_at) DESC"
        ),
        {"s": store_id},
    ):
        pages.setdefault((listing, int(page)), {"run": run_id, "keys": list(dict.fromkeys(keys))})
    status: dict[tuple[str, str], tuple[str, str, str]] = {}
    for run_id, key, st, upc, weight in c.execute(
        text(
            "SELECT run_id, upc, status, record->>'upc', record->>'weight' FROM records WHERE run_id IN "
            "(SELECT id FROM runs WHERE store_id=:s)"
        ),
        {"s": store_id},
    ):
        status[(run_id, key)] = (st, upc or "", weight or "")

fd = {r["key"]: r for r in csv.DictReader(open(FD, encoding="utf-8-sig"))}
queue = list(csv.DictReader(open(QUEUE, encoding="utf-8-sig")))
seed_items = {q["item_id"]: q for q in queue}

out: dict = {"generated_at": NOW.isoformat(), "reuse_since": SINCE.isoformat(), "saved_items": len(saved), "pages": []}
by_listing: dict[str, Counter] = defaultdict(Counter)
for (listing, page), p in sorted(pages.items()):
    cnt: Counter = Counter()
    for key in p["keys"]:
        st, upc, weight = status.get((p["run"], key), ("no record", "", ""))
        item = key.removeprefix("wm:")
        cnt["tiles"] += 1
        cnt[f"status:{st}"] += 1
        if st in ("valid", "exported_not_valid"):
            need = (not upc) or (not weight)
            hit = saved.get(item)
            reusable = hit is not None and (bool(weight) or "(sizes)" in hit)
            if not need:
                cnt["no_read_needed"] += 1
            elif reusable:
                cnt["reusable"] += 1
            else:
                cnt["new_read_needed"] += 1
        if item in seed_items:
            cnt["seed_seen_as_tile"] += 1
    out["pages"].append({"listing": listing, "page": page, "run": p["run"], **cnt})
    by_listing[listing].update(cnt)
out["by_listing"] = {k: dict(v) for k, v in by_listing.items()}
out["seeds_by_listing"] = dict(Counter(q["listing"] for q in queue))
fd_unres = Counter()
for k, r in fd.items():
    u = r["upc_disposition"] in ("budget_deadline_interruption", "not_attempted")
    w = r["weight_disposition"] in ("budget_deadline_interruption",)
    if u or w:
        fd_unres[(r["sub_category"], "reusable" if saved.get(r["item_id"]) else "needs_read")] += 1
out["dataset_unresolved_by_sub_category"] = {f"{a} | {b}": n for (a, b), n in sorted(fd_unres.items())}
out["seeds_with_saved_page"] = sum(1 for i in seed_items if i in saved)
out["seeds_in_dataset"] = sum(1 for i in seed_items if f"wm:{i}" in fd)
with open(sys.argv[1], "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "pages"}, indent=1))
for p in out["pages"]:
    print(p)
