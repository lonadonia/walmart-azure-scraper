"""Every stored listing page of the campaign's data folder read by an installed release's own page reader (offline).

usage: <release's python> -I replay_totals.py DATA_RUNS_DIR OUT_JSONL

For each stored page copy (runs/<store>/<run>/live/dom/<fetch>.html.gz) whose page data has a search result, writes
one JSON line: the run, the fetch, the release, the listing total, the page's own count, the last page, the listing's
products and result-grid placements on the page, and the branch a first page without products takes. No page content
is written.
"""

import gzip
import json
import sys
from pathlib import Path

import walmart_headless
from walmart_headless.sites.walmart import page_data as wpd

root, out = Path(sys.argv[1]), Path(sys.argv[2])
n = 0
with out.open("w", encoding="utf-8", newline="\n") as f:
    for p in sorted(root.rglob("dom/*.html.gz")):
        try:
            nd = wpd.next_data(gzip.decompress(p.read_bytes()).decode("utf-8", "replace"))
        except Exception:  # noqa: BLE001 - not a page with page data: not a listing page
            continue
        if not isinstance(nd, dict) or not wpd.search_result(nd):
            continue
        try:
            pag = wpd.pagination(nd)
            items = wpd.page_items(nd)
            placements = wpd.placements(nd)
        except wpd.PageShapeUnclear as exc:
            f.write(json.dumps({"run": p.parts[-4], "fetch": p.name.split(".")[0], "error": str(exc)}) + "\n")
            continue
        branch = ("products" if items else
                  "stop" if pag.total_count not in (0, None) or placements else "empty")
        f.write(json.dumps({
            "run": p.parts[-4], "fetch": p.name.split(".")[0], "release": walmart_headless.__version__,
            "total_count": pag.total_count, "page_count": pag.page_count, "max_page": pag.max_page,
            "products": len(items), "placements": placements, "branch": branch,
        }) + "\n")
        n += 1
print(json.dumps({"release": walmart_headless.__version__, "listing_pages": n}))
