"""The live Bidets answer of L7 judged by an installed release's own code (offline: no request).

usage: <release's python> -I empty_grid_check.py RAW_BODY_GZ STORED_COPY_GZ

Prints, as JSON: the release (walmart_headless.__version__), the SHA-256 of the private raw answer (the .gz file and
the body it holds) and of the stored copy, and for each of the two documents what that release reads from the page
data: the listing's total, the page's own count, the last page, the result stacks and other modules, the products of
the listing, the result-grid placements, the page location, and what the collector does with such a first page (the
branch of WalmartCollector._page for a first page without products: "stop: the page reports results but shows no
product" when the total is neither 0 nor missing or the result grid has placements, else "empty listing, once the
page's own store check passes"). No page content is printed.
"""

import gzip
import hashlib
import json
import sys
from pathlib import Path

import walmart_headless
from walmart_headless.sites.walmart import page_data as wpd


def judge(html: str) -> dict:
    nd = wpd.next_data(html)
    pag = wpd.pagination(nd)
    stacks = wpd.item_stacks(nd)
    items = wpd.page_items(nd)
    loc = wpd.page_location(nd)
    placements = wpd.placements(nd)
    if items:
        branch = "a listing page with products"
    elif pag.total_count not in (0, None) or placements:
        branch = "stop: the page reports results but shows no product (ABNORMAL_RESULT)"
    else:
        branch = "empty listing (EMPTY, 'the listing shows 0 results'), once the page's own store check passes"
    return {
        "total_count": pag.total_count,
        "page_count": pag.page_count,
        "max_page": pag.max_page,
        "stacks": [
            {"index": s.index, "layout": s.layout, "title": s.title, "count": s.count, "products": s.products,
             "primary": s.primary, "fulfillment": s.fulfillment_filter}
            for s in stacks
        ],
        "listing_products": len(items),
        "result_grid_placements": placements,
        "page_location": {"store_id": loc.store_id, "postal_code": loc.postal_code, "intent": loc.intent}
        if loc else None,
        "first_page_without_products": branch,
    }


raw_path, stored_path = Path(sys.argv[1]), Path(sys.argv[2])
raw_gz, stored_gz = raw_path.read_bytes(), stored_path.read_bytes()
raw, stored = gzip.decompress(raw_gz), gzip.decompress(stored_gz)
print(
    json.dumps(
        {
            "release": walmart_headless.__version__,
            "raw_file": raw_path.name,
            "raw_file_sha256": hashlib.sha256(raw_gz).hexdigest(),
            "raw_body_sha256": hashlib.sha256(raw).hexdigest(),
            "stored_copy_file": stored_path.name,
            "stored_copy_file_sha256": hashlib.sha256(stored_gz).hexdigest(),
            "stored_copy_content_sha256": hashlib.sha256(stored).hexdigest(),
            "raw_answer": judge(raw.decode("utf-8")),
            "stored_copy": judge(stored.decode("utf-8")),
        },
        indent=1,
    )
)
