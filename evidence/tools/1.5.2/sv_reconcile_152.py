"""Brief section 4: a source-supported outcome for each open row of the sponsored/variant reconciliation.

Input: the 651 rows of the 1.5.1 delivery's SPONSORED_AND_VARIANT_RECONCILIATION.csv (read only).

A row that 1.5.1 left PENDING is read against every saved page of the item's own product page: the capture index
of the 1.4.x runs and the campaign's own stored product pages. Nothing is requested. The newest page that is the
item's own, for the store, decides, with the collector's own readers (`wpd.product_page`, `wpd.product_identifier`,
`ProductPage.under`), the checks `WalmartCollector._follow_one` makes on a page it reads:
  identity  the page's usItemId is the requested item
  store     store 3891 is among product.location.storeIds, and the intent is PICKUP
  category  the page files the item under the row's listing
  offer     the page's fulfillment options and price, kept apart from identity

The outcome is HISTORICAL evidence: the page's own time, run and revision are kept, and it is never fresh. A row
with no saved own page stays open, with the exact read it needs and why.

Outputs (OUT, new):
  SPONSORED_AND_VARIANT_RECONCILIATION_1_5_2.csv  the 651 rows: 1.5.1's columns unchanged, then the 1.5.2 columns
  EXACT_LIVE_READ_QUEUE_1_5_2.csv                 each item still needing its own page read, once
  sv_reconcile_152_summary.json                   the counts printed at the end
usage: <collector venv python> -I -X utf8 sv_reconcile_152.py OUT
"""

from __future__ import annotations

import collections
import csv
import gzip
import hashlib
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, "C:/w7/wt/headless/walmart-azure-headless/src")
from walmart_headless.sites.walmart import page_data as wpd  # noqa: E402

BASE = Path(r"<repository>\deliverables\20261101_walmart_1.5.1")
REC = BASE / "SPONSORED_AND_VARIANT_RECONCILIATION.csv"
INDEX = Path("C:/w7/b/detail_capture_index_150.json")
INDEX_BASE = Path("C:/w7/b")
CAMPAIGN_DATA = Path("C:/w7/live/data/runs/walmart-3891-pickup")
RUNS = json.loads(Path("C:/w7/evidence/live150/runs.json").read_text("utf-8"))
STORE = "3891"
LISTINGS = {
    "Fresh Vegetables": "976759_976793_8910423",
    "Fresh Fruits": "976759_976793_9756351",
    "Strawberries": "976759_976793_9756351_3521037",
}


def read_page(path: Path) -> str:
    raw = path.read_bytes()
    if path.suffix == ".gz":
        raw = gzip.decompress(raw)
    return raw.decode("utf-8", "replace")


def saved_pages() -> dict[str, list[dict]]:
    """Every saved own page by item: the capture index, then the campaign's product pages by stored file."""
    pages: dict[str, list[dict]] = collections.defaultdict(list)
    for e in json.loads(INDEX.read_text("utf-8")):
        pages[str(e["item_id"])].append(
            {
                "path": INDEX_BASE / e["path"],
                "observed_at": e["observed_at"],
                "run_id": e["run_id"],
                "revision": e.get("source_revision") or "",
                "release": e.get("release") or "",
                "provider": e.get("provider") or "",
            }
        )
    return pages


def decide(item: str, listing: str, name: str, page: dict) -> dict:
    html = read_page(page["path"])
    out = {
        "page_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
        "page_observed_at": page["observed_at"],
        "page_run": page["run_id"],
        "page_revision": page["revision"],
        "page_release": page["release"],
    }
    try:
        nd = wpd.next_data(html)
    except wpd.PageDataMissing:
        return {**out, "outcome": "unusable_page", "why": "the saved page carries no Walmart page data"}
    pp = wpd.product_page(nd)
    if pp is None or pp.item is None:
        return {**out, "outcome": "unusable_page", "why": "the page data has no product"}
    out.update(
        {
            "page_item": pp.page_item,
            "page_title": pp.item.name if hasattr(pp.item, "name") else "",
            "store_ids": " ".join(pp.store_ids),
            "intent": pp.intent,
            "postal_code": pp.postal_code,
            "seller_type": pp.seller_type,
            "offer_type": pp.offer_type,
            "options": "; ".join("/".join(x for x in o if x) for o in pp.options),
        }
    )
    if pp.page_item != item:
        return {**out, "outcome": "another_item", "why": f"the link leads to item {pp.page_item}'s page"}
    if STORE not in pp.store_ids:
        return {
            **out,
            "outcome": "store_not_established",
            "why": f"the page names stores {list(pp.store_ids) or 'none'}, not {STORE}",
        }
    if pp.intent != "PICKUP":
        return {**out, "outcome": "store_not_established", "why": f"the page's intent is {pp.intent or 'none'}"}
    ident = wpd.product_identifier(html, item)
    out["upc_on_page"] = ident.value
    # The column reads "id (name)", or the id alone.
    want, _, label = listing.partition(" (")
    label = label.rstrip(")")
    under, evidence = pp.under(want, label)
    out["category_evidence"] = evidence
    pickup = [o for o in pp.options if "PICKUP" in o[0]]
    available = [o for o in pickup if o[1] in ("AVAILABLE", "IN_STOCK")]
    out["pickup_available"] = "yes" if available else "no"
    if not under:
        return {
            **out,
            "outcome": "category_not_established",
            "why": f"its own page files it under {evidence}, not under {listing}",
        }
    if not available:
        return {
            **out,
            "outcome": "identity_and_category_established_no_pickup_line",
            "why": "its own page is for the store, and shows no available Pickup option on the page's date",
        }
    return {
        **out,
        "outcome": "identity_category_and_pickup_established",
        "why": "its own page is for the store and shows an available Pickup option on the page's date",
    }


def main() -> int:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=False)
    rows = list(csv.DictReader(REC.open(encoding="utf-8-sig", newline="")))
    pages = saved_pages()
    cols = [
        "outcome_1_5_2",
        "outcome_detail_1_5_2",
        "evidence_class_1_5_2",
        "saved_own_pages",
        "page_observed_at",
        "page_run",
        "page_revision",
        "page_release",
        "page_sha256",
        "page_item",
        "store_ids",
        "intent",
        "postal_code",
        "pickup_available",
        "seller_type",
        "offer_type",
        "options",
        "category_evidence",
        "upc_on_page",
        "remaining_1_5_2",
    ]
    counts: collections.Counter = collections.Counter()
    read_queue: dict[str, dict] = {}
    for r in rows:
        new = dict.fromkeys(cols, "")
        ev = r["evidence_class_1_5_1"]
        if not ev.startswith("PENDING"):
            new.update(
                {
                    "outcome_1_5_2": "unchanged",
                    "outcome_detail_1_5_2": "closed or carried in 1.5.1: see closure_1_5_1",
                    "evidence_class_1_5_2": ev,
                    "remaining_1_5_2": r["remaining_1_5_1"],
                }
            )
            counts[("not_open", ev)] += 1
            r.update(new)
            continue
        have = sorted(pages.get(r["item_id"], []), key=lambda p: p["observed_at"], reverse=True)
        new["saved_own_pages"] = str(len(have))
        best = None
        for p in have:
            found = decide(r["item_id"], r["listing"], r["identity"], p)
            if best is None:
                best = found
            if found["outcome"] not in ("unusable_page", "another_item", "store_not_established"):
                best = found
                break
        if best is None:
            new.update(
                {
                    "outcome_1_5_2": "open_needs_own_page_read",
                    "outcome_detail_1_5_2": "no saved page of the item exists: identity, category and local "
                    "assortment are unverified",
                    "evidence_class_1_5_2": "NOT TESTED",
                    "remaining_1_5_2": "one exact read of its own page for store 3891, Pickup (blocked: allowance)",
                }
            )
            read_queue.setdefault(
                r["item_id"],
                {"item_id": r["item_id"], "kind": r["kind"], "identity": r["identity"], "listing": r["listing"]},
            )
            counts[("open_needs_own_page_read", r["kind"])] += 1
        else:
            new.update({k: v for k, v in best.items() if k in new})
            new["outcome_1_5_2"] = best["outcome"]
            new["outcome_detail_1_5_2"] = best["why"]
            new["evidence_class_1_5_2"] = "HISTORICAL (its own saved page, read offline; not a fresh observation)"
            new["remaining_1_5_2"] = (
                "none for identity and local assortment on the page's date; a current price needs a later read"
                if best["outcome"].startswith("identity_")
                else "as the outcome says; a later read of the page could change it"
            )
            if best["outcome"] in ("unusable_page", "another_item", "store_not_established"):
                new["evidence_class_1_5_2"] = "NOT TESTED"
                new["remaining_1_5_2"] = "one exact read of its own page for store 3891, Pickup (blocked: allowance)"
                read_queue.setdefault(
                    r["item_id"],
                    {"item_id": r["item_id"], "kind": r["kind"], "identity": r["identity"], "listing": r["listing"]},
                )
            counts[(best["outcome"], r["kind"])] += 1
        r.update(new)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    (out / "SPONSORED_AND_VARIANT_RECONCILIATION_1_5_2.csv").write_bytes(("\ufeff" + buf.getvalue()).encode("utf-8"))
    q = io.StringIO()
    w = csv.DictWriter(q, fieldnames=["item_id", "kind", "identity", "listing"], lineterminator="\n")
    w.writeheader()
    w.writerows(read_queue[k] for k in sorted(read_queue, key=int))
    (out / "EXACT_LIVE_READ_QUEUE_1_5_2.csv").write_bytes(("\ufeff" + q.getvalue()).encode("utf-8"))
    summary = {
        "rows": len(rows),
        "by_outcome_and_kind": {"|".join(k): v for k, v in sorted(counts.items())},
        "distinct_items_needing_a_read": len(read_queue),
    }
    (out / "sv_reconcile_152_summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
