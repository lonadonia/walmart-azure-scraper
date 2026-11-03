"""Compare two campaign runs' fresh exports (products_fresh.json, the 22-field records each run observed itself),
product by product, keyed by the Walmart item id in the record's link. Used for S5b (serial against parallel on
the same slice) and S5a (the time-separated repeat against S4's same pages). Only fields of products both runs
observed are compared; a product only one run observed is listed as such, never as a change. Nothing is
inferred about stock: a product is "present" in a run only if that run exported a fresh record for it.
Optionally restricted to the listings (sub_category values) the later run read, so that a run that read more
listings than the other does not count the extra listings as "missing".
With --first-page-of-b-listings, both runs are restricted to the products their own memberships place on page 1
of the listings run B read (memberships.json of each run's exports), so that a repeat of first pages is compared
with the same pages of a run that read more pages.
usage: python -I -X utf8 compare_runs_150.py RUN_A RUN_B LABEL [--same-subcategories] [--first-page-of-b-listings]
writes C:/w7/evidence/live150/compare/<LABEL>_products.csv and <LABEL>_summary.json
"""

import collections
import csv
import json
import re
import sys
from pathlib import Path

DATA = Path(r"C:\w7\live\data\runs\walmart-3891-pickup")
OUT = Path(r"C:\w7\evidence\live150\compare")
FIELDS = ["product_title", "weight", "regular_price", "sale_price", "volume_deals_description", "volume_deals_price",
          "digital_deals_description", "digital_deals_price", "image_url", "upc", "ppm", "category", "sub_category"]


def item_of(url: str) -> str:
    m = re.search(r"/(\d+)(?:[?#]|$)", url)
    assert m, url
    return m.group(1)


def load(run: str) -> dict[str, dict]:
    recs = json.loads((DATA / run / "exports" / "products_fresh.json").read_text(encoding="utf-8"))
    out = {}
    for r in recs:
        out[item_of(r["url"])] = r
    assert len(out) == len(recs), f"{run}: duplicate items"
    return out


def main() -> None:
    a_run, b_run, label = sys.argv[1], sys.argv[2], sys.argv[3]
    same_sub = "--same-subcategories" in sys.argv[4:]
    first_page = "--first-page-of-b-listings" in sys.argv[4:]
    a, b = load(a_run), load(b_run)
    if same_sub:
        subs = {r["sub_category"] for r in b.values()}
        a = {k: v for k, v in a.items() if v["sub_category"] in subs}
    page1_listings: list[str] = []
    if first_page:
        mem_a = json.loads((DATA / a_run / "exports" / "memberships.json").read_text(encoding="utf-8"))
        mem_b = json.loads((DATA / b_run / "exports" / "memberships.json").read_text(encoding="utf-8"))
        page1_listings = sorted({m["listing"] for m in mem_b})
        keep_a = {m["key"][3:] for m in mem_a if m["listing"] in page1_listings and m["page"] == 1}
        keep_b = {m["key"][3:] for m in mem_b if m["listing"] in page1_listings and m["page"] == 1}
        a = {k: v for k, v in a.items() if k in keep_a}
        b = {k: v for k, v in b.items() if k in keep_b}
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    changed = collections.Counter()
    for item in sorted(set(a) | set(b)):
        ra, rb = a.get(item), b.get(item)
        if ra is None or rb is None:
            rows.append({"item_id": item, "presence": "only in A" if rb is None else "only in B",
                         "sub_category": (ra or rb)["sub_category"], "product_title": (ra or rb)["product_title"],
                         "field": "", "value_a": "", "value_b": ""})
            continue
        diffs = [f for f in FIELDS if ra[f] != rb[f]]
        if not diffs:
            rows.append({"item_id": item, "presence": "both", "sub_category": ra["sub_category"],
                         "product_title": ra["product_title"], "field": "(none differs)", "value_a": "", "value_b": ""})
        for f in diffs:
            changed[f] += 1
            rows.append({"item_id": item, "presence": "both", "sub_category": ra["sub_category"],
                         "product_title": ra["product_title"], "field": f, "value_a": ra[f], "value_b": rb[f]})
    path = OUT / f"{label}_products.csv"
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)
    both = set(a) & set(b)
    summary = {
        "label": label, "run_a": a_run, "run_b": b_run, "restricted_to_b_subcategories": same_sub,
        "restricted_to_page_1_of": page1_listings,
        "fresh_a": len(a), "fresh_b": len(b), "in_both": len(both), "only_in_a": len(set(a) - set(b)),
        "only_in_b": len(set(b) - set(a)),
        "products_in_both_with_any_difference": len({r["item_id"] for r in rows if r["presence"] == "both"
                                                     and r["field"] not in ("", "(none differs)")}),
        "differences_by_field": dict(changed),
        "by_subcategory": {s: {"a": sum(1 for r in a.values() if r["sub_category"] == s),
                               "b": sum(1 for r in b.values() if r["sub_category"] == s)}
                           for s in sorted({r["sub_category"] for r in list(a.values()) + list(b.values())})},
        "output": str(path),
    }
    (OUT / f"{label}_summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
