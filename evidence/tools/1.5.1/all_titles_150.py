"""Every distinct product title on every stored result page available offline: the delivered 1.4.1 edition evidence
under C:/w7/b and the campaign's own pages under C:/w7/live/data. Written once to a JSON file so that size rules can be
compared on the same authentic titles. No request.
usage: <edition venv python> -I -X utf8 all_titles_150.py OUT.json
"""
import csv, glob, gzip, json, sys
from pathlib import Path
from walmart_headless.sites.walmart import page_data as wpd

titles = {}
pages = []
for pf in glob.glob("C:/w7/b/*/*/*_new_live_*/runs/*/*/db/page_fetches.csv"):
    run_dir = Path(pf).parent.parent
    for r in csv.DictReader(open(pf, encoding="utf-8", newline="")):
        if r["purpose"] == "listing":
            p = run_dir / "pages" / "dom" / f"{r['id']}.html.gz"
            if p.is_file():
                pages.append(("1.4.1", run_dir.name, r["id"], p))
for p in glob.glob(r"C:/w7/live/data/runs/walmart-3891-pickup/*/live/dom/*.html.gz"):
    p = Path(p)
    pages.append(("campaign", p.parent.parent.parent.name, p.name.split(".")[0], p))
n = 0
for src, run, fid, p in pages:
    nd = wpd.next_data(gzip.decompress(p.read_bytes()).decode("utf-8", "replace"))
    if not nd:
        continue
    for it in wpd.page_items(nd):
        e = titles.setdefault(it.name, {"sources": set(), "items": set(), "first": [src, run, fid]})
        e["sources"].add(src)
        e["items"].add(it.item_id)
    n += 1
out = {"pages_read": n, "titles": {t: {"sources": sorted(e["sources"]), "items": sorted(e["items"]), "first": e["first"]} for t, e in titles.items()}}
Path(sys.argv[1]).write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")
print(n, len(titles))
