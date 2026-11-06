"""Read-only: every stored SUBCATEGORIES_FOUND link to the given listing IDs, in event order, with the view key and
filters of release 1.6.8 (commit 85c29e7). usage: <campaign venv python> -I -X utf8 links_of_168d.py DB ARGS_LINES LISTING_ID..."""
import os, sys
os.environ["PSYCOPG_IMPL"] = "python"
os.environ["PATH"] = ("C:/w9/live/ed/walmart-oxylabs-1.6.0/.venv/Lib/site-packages/pgserver/pginstall/bin" + os.pathsep + os.environ.get("PATH", ""))
sys.path.insert(0, "C:/w9/live")
sys.path.insert(0, "C:/w9/wt/headless/walmart-azure-headless/src")
import live160_run as h
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from walmart_headless.collection import navigation as nav
from walmart_headless.sites.walmart import page_data as wpd
labels = {l.split("=")[1]: l.split("=")[0] for l in open(sys.argv[2], encoding="utf-8").read().split()}
eng = create_engine(make_url(h.db_url()).set(database=sys.argv[1]), connect_args={"options": "-c default_transaction_read_only=on"})
with eng.connect() as c:
    rows = c.execute(text("select e.id, e.run_id, e.ts, e.data from events e where e.code = 'SUBCATEGORIES_FOUND' order by e.ts, e.id")).all()
want = set(sys.argv[3:])
seen = set()
for eid, rid, ts, d in rows:
    links = [*(("listing", x) for x in d.get("listings") or []), *(("filtered_view", x) for x in d.get("filtered_views") or [])]
    for i, (kind, l) in enumerate(links):
        u = l.get("url") or ""
        lid = wpd.listing_id(u) if u else ""
        if lid in want:
            row = (labels.get(rid, rid), d.get("node"), i + 1, " ".join((l.get("name") or "").split()), nav.view_key(u), nav.narrowing(u))
            if row[1:] not in seen:
                seen.add(row[1:])
                print(row)
