"""Read-only: why the 1.6.8 replay of L12 names some carried and fresh rows differently from the 1.6.6 export. For each
sub_category rename the L12 diff found, the listing views that a stored category page names with the old or the new
name, and every link of every stored SUBCATEGORIES_FOUND event that names the same view, in event order: run, node
(the CSV row's category page), position, name, whether the link narrows the listing (a filtered view), and what the
rule of each release picks. Release 1.6.8 (navigation.category_page_names of commit 85c29e7): per page, the first link
to a view names it; a later page replaces an earlier one; the row's own page wins over another row's page. Up to the
second 1.6.8 candidate, the later link of a page won. No write (default_transaction_read_only); no request.

usage: <the 1.6.0 campaign venv's python> -I -X utf8 names_probe_168d.py DB_NAME RUN_LABELS_FILE OUT_JSON
  RUN_LABELS_FILE: lines LABEL=RUN_ID=RELEASE=... (the W4 arguments)
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

os.environ["PSYCOPG_IMPL"] = "python"
os.environ["PATH"] = ("C:/w9/live/ed/walmart-oxylabs-1.6.0/.venv/Lib/site-packages/pgserver/pginstall/bin"
                      + os.pathsep + os.environ.get("PATH", ""))
sys.path.insert(0, "C:/w9/live")
sys.path.insert(0, "C:/w9/wt/headless/walmart-azure-headless/src")
import live160_run as h  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from walmart_headless.collection import navigation as nav  # noqa: E402
from walmart_headless.sites.walmart import page_data as wpd  # noqa: E402

RENAMES = [("Laundry", "Shop All Laundry Supplies"), ("Fabric Softener", "Fabric Softeners"),
           ("Dry Dog Food", "Dry dog food"), ("Laundry Detergents", "Laundry Detergent"),
           ("Laundry Scent Boosters", "Scent Boosters"), ("Great Value Pantry", "Pantry")]


def main(db: str, labels_file: Path, out: Path) -> int:
    labels = {}
    for line in labels_file.read_text(encoding="utf-8").split():
        p = line.split("=")
        labels[p[1]] = f"{p[0]} ({p[2]})"
    url = make_url(h.db_url()).set(database=db)
    eng = create_engine(url, connect_args={"options": "-c default_transaction_read_only=on"})
    with eng.connect() as c:
        stores = c.execute(text("select id, key from stores")).all()
        store_id = next(i for i, k in stores if k == "walmart-3891-pickup")
        rows = c.execute(text(
            "select e.id, e.run_id, e.ts, e.data from events e join runs r on r.id = e.run_id "
            "where r.store_id = :s and e.code = :code order by e.ts, e.id"), {"s": store_id, "code": nav.FOUND_CODE}).all()
    links_by_view: dict[str, list[dict]] = defaultdict(list)
    for eid, rid, ts, data in rows:
        node = str(data.get("node") or "")
        allx = [*(("listing", x) for x in data.get("listings") or []),
                *(("filtered_view", x) for x in data.get("filtered_views") or [])]
        for i, (kind, link) in enumerate(allx):
            name = " ".join(str(link.get("name") or "").split())
            u = str(link.get("url") or "")
            key = nav.view_key(u) if u else ""
            if not name or not key:
                continue
            links_by_view[key].append({
                "event": str(eid), "run": labels.get(str(rid), str(rid)), "at": ts.isoformat(), "node": node,
                "position": i, "recorded_as": kind, "name": name, "listing_id": wpd.listing_id(u),
                "narrows": [list(f) for f in nav.narrowing(u)], "url": u,
            })

    def pick(links: list[dict], first: bool) -> dict | None:
        """Per event, the first (1.6.8) or last link to the view; the latest event wins."""
        chosen = None
        for ev in dict.fromkeys(x["event"] for x in links):
            here = [x for x in links if x["event"] == ev]
            chosen = here[0] if first else here[-1]
        return chosen

    result = []
    for old, new in RENAMES:
        views = sorted({k for k, v in links_by_view.items() if any(x["name"] in (old, new) for x in v)})
        entry = {"old": old, "new": new, "views": []}
        for k in views:
            v = links_by_view[k]
            first, last = pick(v, True), pick(v, False)
            entry["views"].append({
                "view_key": k, "links": v,
                "rule_1_6_8_first_link_per_page": first and {x: first[x] for x in ("run", "node", "position", "name")},
                "rule_until_second_candidate_last_link_per_page": last and {x: last[x] for x in ("run", "node", "position", "name")},
            })
        result.append(entry)
    out.write_text(json.dumps({"db": db, "events": len(rows), "renames": result}, indent=1) + "\n", encoding="utf-8")
    for e in result:
        print(f"== {e['old']!r} -> {e['new']!r}")
        for v in e["views"]:
            names = [(x["run"].split()[0], x["node"], x["position"], x["name"], "filtered" if x["narrows"] else "itself")
                     for x in v["links"]]
            seen = []
            for n in names:
                if n not in seen:
                    seen.append(n)
            print("  view", v["view_key"][:70], "| 1.6.8:", v["rule_1_6_8_first_link_per_page"]["name"],
                  "| last-link:", v["rule_until_second_candidate_last_link_per_page"]["name"])
            for n in seen[:14]:
                print("     ", n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])))
