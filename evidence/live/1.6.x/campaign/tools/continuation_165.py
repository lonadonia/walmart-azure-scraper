"""The outstanding listing work of W4, counted from the coverage table (offline; no request): for each listing state
of W4_LISTINGS_1_6_5.csv, the listing pages a continuation would request, at Walmart's 40 organic results per page
and at most 25 pages per listing (the result window: a listing reporting more is read through its child
categories, which are rows of their own). Measured inputs: the L10 census (page 1 of each listing it reached, two
workers, detail off), its throughput and the trial's reserve rate. Unreached listings (no page read, no reported
total) are estimated from the reached listings of the same CSV row; the estimate is labelled as such.

usage: python -I continuation_165.py W4_LISTINGS.csv OUT.json
"""

from __future__ import annotations

import csv
import json
import math
import statistics
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

PER_PAGE, WINDOW = 40, 25
RATE = Decimal("0.0015")  # the shared trial's reserve rate per submission (one result each)
PAGES_PER_ACTIVE_MIN = 10.19  # L10, two workers (CONCURRENCY_MEASURED_1_6_5.csv)
OVERHEAD_PER_EXECUTION = 4  # robots.txt and the store page, per worker, two workers


def pages_read(s: str) -> int:
    if not s:
        return 0
    if "-" in s:
        a, b = s.split("-")
        return int(b) - int(a) + 1
    return len(s.split(";"))


def pages_needed(total: int) -> int:
    return max(1, min(math.ceil(total / PER_PAGE), WINDOW)) if total > 0 else 1


def main(argv: list[str]) -> int:
    rows = list(csv.DictReader(Path(argv[0]).open(encoding="utf-8", newline="")))
    by_row_needed: dict[str, list[int]] = defaultdict(list)
    for r in rows:
        if r["best_reported_total"] and r["state_1_6_5"] in ("PARTIAL", "COMPLETE", "INCOMPLETE", "RESULT_WINDOW"):
            by_row_needed[r["csv_row"]].append(pages_needed(int(r["best_reported_total"])))
    all_needed = [n for v in by_row_needed.values() for n in v]
    out: dict[str, dict] = {}
    # 1. PARTIAL: the pages after those read, up to the window
    part = [r for r in rows if r["state_1_6_5"] == "PARTIAL"]
    rem = [max(0, pages_needed(int(r["best_reported_total"])) - pages_read(r["best_pages"])) for r in part]
    over = [r for r in part if int(r["best_reported_total"]) > PER_PAGE * WINDOW]
    out["PARTIAL"] = {"listings": len(part), "pages": sum(rem), "basis": "measured: each listing's reported total",
                      "listings_over_the_window": len(over),
                      "over_the_window": [{"csv_row": r["csv_row"], "listing": r["listing_name"],
                                           "reported_total": int(r["best_reported_total"])} for r in over]}
    # 2. INCOMPLETE: read again in full
    inc = [r for r in rows if r["state_1_6_5"] == "INCOMPLETE"]
    out["INCOMPLETE"] = {"listings": len(inc), "pages": sum(pages_needed(int(r["best_reported_total"] or 0)) for r in inc),
                         "basis": "measured: each listing's last reported total, read again from page 1"}
    # 3. NOT_ATTEMPTED: no reported total; the mean pages needed by the reached listings of the same CSV row
    na = [r for r in rows if r["state_1_6_5"] == "NOT_ATTEMPTED"]
    est_rows = {}
    pages_na = 0.0
    for row, group in sorted(defaultdict(list, {k: [r for r in na if r["csv_row"] == k] for k in {r["csv_row"] for r in na}}).items()):
        basis = by_row_needed.get(row) or all_needed
        mean = statistics.mean(basis)
        est_rows[row] = {"listings": len(group), "mean_pages_of_reached_listings": round(mean, 2),
                         "reached_listings_in_the_mean": len(basis), "pages": round(len(group) * mean)}
        pages_na += len(group) * mean
    out["NOT_ATTEMPTED"] = {"listings": len(na), "pages": round(pages_na), "basis": "ESTIMATE: no total is known",
                            "by_csv_row": est_rows}
    # 4. not part of the continuation's page count
    out["RESULT_WINDOW"] = {"listings": sum(1 for r in rows if r["state_1_6_5"] == "RESULT_WINDOW"), "pages": 0,
                            "basis": "read as far as the site serves them; a full read needs their child categories"}
    out["CATEGORY_PAGE"] = {"listings": sum(1 for r in rows if r["state_1_6_5"] == "CATEGORY_PAGE"), "pages": 0,
                            "basis": "the site serves a category page; its linked listings are rows of their own"}
    out["NOT_FOUND"] = {"listings": sum(1 for r in rows if r["state_1_6_5"] == "NOT_FOUND"), "pages": 0,
                        "basis": "the site answers with its not-found page"}
    listing_pages = sum(v["pages"] for v in out.values())
    executions = math.ceil(listing_pages / 440)  # L10 read 441 pages in one execution at its ceiling
    submissions = listing_pages + OVERHEAD_PER_EXECUTION * executions
    result = {
        "tool": "continuation_165.py",
        "per_page": PER_PAGE, "window_pages": WINDOW,
        "states": out,
        "listing_pages": listing_pages,
        "executions_of_about_440_pages": executions,
        "submissions_with_overhead": submissions,
        "usd_at_the_trial_reserve_rate": str((RATE * submissions).quantize(Decimal("0.01"))),
        "active_hours_at_the_L10_rate": round(listing_pages / PAGES_PER_ACTIVE_MIN / 60, 1),
        "not_included": "product pages (detail reading): one per product without a saved read; retries; the "
                        "listings found only by reading a listing's child categories",
    }
    Path(argv[1]).write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "states"}))
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk in ("listings", "pages", "listings_over_the_window")}
                      for k, v in out.items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
