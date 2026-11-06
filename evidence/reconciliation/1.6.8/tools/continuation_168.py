"""What the outstanding full-scope work would cost, priced piece by piece from the 1.6.8 coverage table (offline; no
request). From continuation_165.py, whose USD 4.07 priced the known listing pages only. Four parts, each with its own
basis, never added into one figure that hides an assumption:

  1. known_listing_pages: the listings the table knows: the pages after those read (PARTIAL), read again (INCOMPLETE),
     the listing itself where only a filtered view was read (FILTERED_VIEW) and those never reached (NOT_ATTEMPTED).
  2. new_branches: what is known only once it is read. The category pages of their own that no run read (one result
     each, a count); the listings those pages name (not known: priced per listing, with labelled assumptions); and the
     pages beyond the result window of the listings reporting more than it serves (from their reported totals).
  3. product_pages: one result per exported product whose result page states no UPC or no size and which has no saved
     read of the last 30 days. Counted for the products known today (L12's records); estimated for those not yet seen.
  4. retries: the measured share of attempts after the first, by kind of page, in the 15 live runs of the 1.6.x campaign.

Measured inputs come from the campaign database in one read-only session: provider_usage (attempts, outcomes, times)
and detail_observations (saved reads). A figure that rests on an assumption says so where it stands.

usage: python -I continuation_168.py W4_LISTINGS_1_6_8.csv OUT.json
"""

from __future__ import annotations

import csv
import json
import math
import os
import statistics
import sys
from collections import Counter, defaultdict
from decimal import Decimal
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

PER_PAGE, WINDOW = 40, 25
RATE = Decimal("0.0015")  # the shared trial's reserve rate per result: a list price, not an invoice
PAGES_PER_ACTIVE_MIN = 10.19  # L10, two workers, detail off (review/COST_AND_RUNTIME_REPORT.md, section 3)
OVERHEAD_PER_EXECUTION = 4  # robots.txt and the store page, per worker, two workers
PAGES_PER_EXECUTION = 440  # L10 read 441 pages in one execution at its ceiling
# the 15 live runs of the 1.6.x campaign, by their W4 labels
LIVE_RUNS = {
    "L1": "01M6H5TX7R4ZWV8W3NTH0QN6HF", "L2": "01M6H72J86K5TF7A1874N7BJ2R", "L3": "01M6HA74X4QYMW45SVD62JQDSQ",
    "L2b": "01M6HAXEP6495EGWT91JQS09SS", "L4r": "01M6HCF2YSD7N18W7JMH6EHK23", "L4": "01M6HCZXM0WGMRCFDTCNZ7218K",
    "L5": "01M6K1HG154683NAAFXQZX33C6", "L6": "01M6K25T57WW4BJBJ3RQGWN26G", "L8": "01M6K6P21BW509BMRTN1FSB9H7",
    "L9": "01M6K7AB85824HHKD17VNEHASS", "L7": "01M6K7HT3XVV8R8CX79P31KMB4", "L10": "01M6KA3CKYJSD6WDY4TDAAV73Y",
    "L11": "01M6KF4RDC2MKR5Q26ZY5D727P", "L11b": "01M6KFRFEX31W014SW9ZTT4Y54", "L12": "01M6MC7YE4PBXV88G3PJ5ENW4B",
}
# fresh valid products per listing page read, two measured runs (review/COST_AND_RUNTIME_REPORT.md, section 1):
# L10 read page 1 of many listings; L4r read further into a few
FRESH_VALID = {"L10": 7055, "L4r": 1600}
NEW_LISTINGS_PER_PAGE_ASSUMED = (5, 15, 30)  # no subcategory page has been read live: an assumption, labelled
AS_OF = "2026-11-06"  # the saved reads counted are those a run started on this date could use (detail.reuse_days: 30)


def usd(n: float) -> str:
    return str((RATE * Decimal(str(n))).quantize(Decimal("0.01")))


def pages_read(s: str) -> int:
    if not s:
        return 0
    if "-" in s:
        a, b = s.split("-")
        return int(b) - int(a) + 1
    return len(s.split(";"))


def pages_needed(total: int) -> int:
    return max(1, min(math.ceil(total / PER_PAGE), WINDOW)) if total > 0 else 1


def measured() -> dict[str, object]:
    runs = list(LIVE_RUNS.values())
    eng = create_engine(h.db_url())
    with eng.connect() as c:
        c.execute(text("SET TRANSACTION READ ONLY"))
        rows = c.execute(
            text("SELECT purpose, attempt, outcome, count(*) AS n, sum(credits) AS credits, avg(elapsed_ms) AS ms "
                 "FROM provider_usage WHERE run_id = ANY(:r) GROUP BY 1, 2, 3"), {"r": runs}).fetchall()
        saved = c.execute(
            text("SELECT count(DISTINCT item_id) FROM detail_observations WHERE status IN ('extracted', 'absent_in_source')")
        ).scalar()
        newest = c.execute(text("SELECT min(observed_at), max(observed_at) FROM detail_observations")).fetchone()
        known = c.execute(
            text("""
              WITH r AS (
                SELECT status, coalesce(record->>'upc', '') = '' AS no_upc, coalesce(record->>'weight', '') = '' AS no_size,
                       upc AS key
                FROM records WHERE run_id = :r AND status IN ('valid', 'historical'))
              SELECT count(*) AS exported,
                     count(*) FILTER (WHERE no_upc) AS no_upc,
                     count(*) FILTER (WHERE no_size) AS no_size,
                     count(*) FILTER (WHERE no_upc OR no_size) AS either,
                     count(*) FILTER (WHERE (no_upc OR no_size) AND EXISTS (
                       SELECT 1 FROM detail_observations d
                       WHERE 'wm:' || d.item_id = r.key AND d.observed_at >= CAST(:as_of AS timestamptz) - interval '30 days'
                     )) AS either_with_a_saved_read
              FROM r"""), {"r": LIVE_RUNS["L12"], "as_of": AS_OF}).one()
        fresh_needed = dict(
            c.execute(text("SELECT run_id, count(*) FROM records WHERE status = 'valid' AND run_id = ANY(:r) "
                           "AND coalesce(provenance->'upc_detail'->>'status', '') = 'not_attempted' GROUP BY 1"),
                      {"r": [LIVE_RUNS["L4r"], LIVE_RUNS["L10"]]}).fetchall())
        fresh_all = dict(
            c.execute(text("SELECT run_id, count(*) FROM records WHERE status = 'valid' AND run_id = ANY(:r) GROUP BY 1"),
                      {"r": [LIVE_RUNS["L4r"], LIVE_RUNS["L10"]]}).fetchall())
        pages_by_run = dict(
            c.execute(text("SELECT run_id, count(*) FROM provider_usage WHERE purpose = 'listing' AND outcome = 'ok' "
                           "AND run_id = ANY(:r) GROUP BY 1"), {"r": runs}).fetchall())
    kinds: dict[str, dict[str, object]] = {}
    groups = {"listing": ("listing",), "product page": ("product_detail", "product_page"),
              "category page": ("category_page",), "robots and store page": ("robots", "store_page")}
    for name, purposes in groups.items():
        mine = [r for r in rows if r.purpose in purposes]
        attempts = sum(r.n for r in mine)
        later = [r for r in mine if r.attempt > 1]
        ok_first = [r for r in mine if r.attempt == 1 and r.outcome == "ok"]
        kinds[name] = {
            "attempts": attempts,
            "attempts_after_the_first": sum(r.n for r in later),
            "billed_results_of_attempts_after_the_first": int(sum(r.credits for r in later)),
            "billed_results": int(sum(r.credits for r in mine)),
            "share_of_billed_results_that_are_retries": round(
                float(sum(r.credits for r in later)) / max(1.0, float(sum(r.credits for r in mine))), 4),
            "free_provider_failures": sum(r.n for r in mine if r.outcome == "provider_failed_free"),
            "billed_with_no_answer": int(sum(r.credits for r in mine if r.outcome != "ok")),
            "mean_seconds_of_a_first_attempt_answered": round(
                sum(float(r.ms) * r.n for r in ok_first) / max(1, sum(r.n for r in ok_first)) / 1000, 2),
        }
    per_page = {label: round(FRESH_VALID[label] / pages_by_run[LIVE_RUNS[label]], 2) for label in FRESH_VALID}
    return {"kinds": kinds, "items_with_a_saved_read": saved,
            "known_products": {
                "run": "L12", "exported": known.exported, "no_upc": known.no_upc, "no_size": known.no_size,
                "no_upc_or_no_size": known.either, "of_which_a_saved_read_of_the_last_30_days": known.either_with_a_saved_read,
                "own_pages_needed": known.either - known.either_with_a_saved_read,
            },
            "fresh_products_whose_result_page_left_the_upc_or_size_to_their_own_page": {
                label: {"valid": fresh_all.get(LIVE_RUNS[label], 0), "own_page_not_read_in_a_run_with_detail_off":
                        fresh_needed.get(LIVE_RUNS[label], 0)} for label in ("L4r", "L10")
            },
            "saved_reads_from": newest[0].isoformat(), "saved_reads_to": newest[1].isoformat(),
            "listing_pages_answered_by_run": {k: pages_by_run.get(v, 0) for k, v in LIVE_RUNS.items()},
            "fresh_valid_products_per_listing_page": per_page}


def main(argv: list[str]) -> int:
    rows = list(csv.DictReader(Path(argv[0]).open(encoding="utf-8", newline="")))
    state = "state_1_6_8"
    by_row_needed: dict[str, list[int]] = defaultdict(list)
    for r in rows:
        if r["best_reported_total"] and r[state] in ("PARTIAL", "COMPLETE", "INCOMPLETE", "RESULT_WINDOW"):
            by_row_needed[r["csv_row"]].append(pages_needed(int(r["best_reported_total"])))
    all_needed = [n for v in by_row_needed.values() for n in v]

    def row_mean(row: str) -> float:
        return statistics.mean(by_row_needed.get(row) or all_needed)

    known: dict[str, dict[str, object]] = {}
    part = [r for r in rows if r[state] == "PARTIAL"]
    rem = [max(0, pages_needed(int(r["best_reported_total"])) - pages_read(r["best_pages"])) for r in part]
    known["PARTIAL"] = {"listings": len(part), "pages": sum(rem), "basis": "measured: each listing's reported total"}
    inc = [r for r in rows if r[state] == "INCOMPLETE"]
    known["INCOMPLETE"] = {"listings": len(inc), "pages": sum(pages_needed(int(r["best_reported_total"] or 0)) for r in inc),
                           "basis": "measured: each listing's last reported total, read again from page 1"}
    fil = [r for r in rows if r[state] == "FILTERED_VIEW"]
    fil_pages = sum(max(pages_needed(int(r["best_reported_total"] or 0)), row_mean(r["csv_row"])) for r in fil)
    known["FILTERED_VIEW"] = {
        "listings": len(fil), "pages": round(fil_pages),
        "basis": "ESTIMATE: the listing itself from page 1. Only a filtered view's total is known, a lower bound; the "
                 "larger of its pages and the mean of the reached listings of the same CSV row"}
    na = [r for r in rows if r[state] == "NOT_ATTEMPTED"]
    na_rows: dict[str, dict[str, object]] = {}
    for row in sorted({r["csv_row"] for r in na}, key=int):
        group = [r for r in na if r["csv_row"] == row]
        na_rows[row] = {"listings": len(group), "mean_pages_of_reached_listings": round(row_mean(row), 2),
                        "reached_listings_in_the_mean": len(by_row_needed.get(row) or all_needed),
                        "pages": round(len(group) * row_mean(row))}
    known["NOT_ATTEMPTED"] = {"listings": len(na), "pages": round(sum(len([r for r in na if r["csv_row"] == row]) * row_mean(row)
                                                                      for row in na_rows)),
                              "basis": "ESTIMATE: no total is known; the mean of the reached listings of the same CSV row",
                              "by_csv_row": na_rows}
    for s, why in (("RESULT_WINDOW", "read as far as the site serves them; the rest is in new_branches"),
                   ("CATEGORY_PAGE", "the site serves a category page; its linked listings are listings of their own"),
                   ("NOT_FOUND", "the site answers with its not-found page")):
        known[s] = {"listings": sum(1 for r in rows if r[state] == s), "pages": 0, "basis": why}
    listing_pages = sum(int(v["pages"]) for v in known.values())  # type: ignore[call-overload]
    executions = math.ceil(listing_pages / PAGES_PER_EXECUTION)
    submissions = listing_pages + OVERHEAD_PER_EXECUTION * executions

    # 2. new branches
    cp = [r for r in rows if r[state] == "SUBCATEGORY_PAGE_NOT_READ"]
    cp_by_row = Counter(r["csv_row"] for r in cp)
    per_listing = {row: row_mean(row) for row in cp_by_row}
    scenarios = {}
    for n in NEW_LISTINGS_PER_PAGE_ASSUMED:
        pages = sum(cp_by_row[row] * n * per_listing[row] for row in cp_by_row)
        scenarios[str(n)] = {"new_listings": sum(cp_by_row.values()) * n, "listing_pages": round(pages), "usd": usd(pages)}
    over = []
    for r in rows:
        total = int(r["best_reported_total"] or 0)
        if total > PER_PAGE * WINDOW and r[state] in ("PARTIAL", "RESULT_WINDOW"):
            over.append({"csv_row": r["csv_row"], "listing": r["listing_name"], "reported_total": total, "state": r[state],
                         "pages_beyond_the_window": math.ceil(total / PER_PAGE) - WINDOW})
    over.sort(key=lambda x: -int(x["pages_beyond_the_window"]))  # type: ignore[call-overload]
    beyond = sum(int(x["pages_beyond_the_window"]) for x in over)  # type: ignore[call-overload]
    largest = int(over[0]["pages_beyond_the_window"]) if over else 0  # type: ignore[call-overload]

    # 3 and 4, from the campaign's records
    m = measured()
    kinds = m["kinds"]
    assert isinstance(kinds, dict)
    fresh = m["fresh_valid_products_per_listing_page"]
    assert isinstance(fresh, dict)
    low, high = min(fresh.values()), max(fresh.values())
    product_seconds = float(kinds["product page"]["mean_seconds_of_a_first_attempt_answered"])
    listing_seconds = float(kinds["listing"]["mean_seconds_of_a_first_attempt_answered"])
    known_products = m["known_products"]
    assert isinstance(known_products, dict)
    known_pages = int(known_products["own_pages_needed"])
    new_low = listing_pages * low
    new_high = listing_pages * high
    product_low = known_pages + new_low
    product_high = known_pages + new_high
    retry_product = float(kinds["product page"]["share_of_billed_results_that_are_retries"])
    # one scheduled run of the whole scope reads every listing page, not only those outstanding
    full_run = 0.0
    for r in rows:
        if r[state] in ("COMPLETE", "PARTIAL", "INCOMPLETE"):
            full_run += pages_needed(int(r["best_reported_total"] or 0))
        elif r[state] == "RESULT_WINDOW":
            full_run += WINDOW
        elif r[state] in ("FILTERED_VIEW", "NOT_ATTEMPTED"):
            full_run += row_mean(r["csv_row"])
    full_run_submissions = round(full_run) + OVERHEAD_PER_EXECUTION * math.ceil(full_run / PAGES_PER_EXECUTION)
    result = {
        "tool": "continuation_168.py",
        "rate_usd_per_result": str(RATE),
        "per_page": PER_PAGE,
        "window_pages": WINDOW,
        "known_listing_pages": {
            "states": known,
            "listing_pages": listing_pages,
            "executions_of_about_440_pages": executions,
            "submissions_with_overhead": submissions,
            "usd": usd(submissions),
            "active_hours_at_the_L10_rate": round(listing_pages / PAGES_PER_ACTIVE_MIN / 60, 1),
            "excludes": "new_branches, product_pages, retries",
        },
        "new_branches": {
            "category_pages_not_read": {
                "pages": len(cp), "usd": usd(len(cp)), "by_csv_row": dict(sorted(cp_by_row.items(), key=lambda x: int(x[0]))),
                "basis": "a count: one result per page. Reading them replaces the assumption below with a measured count",
            },
            "listings_those_pages_name": {
                "basis": "ASSUMPTION: no subcategory page has been read live, so how many new listings they name is not "
                         "known. Each new listing is priced at the mean pages of the reached listings of its CSV row",
                "by_new_listings_per_page": scenarios,
            },
            "beyond_the_result_window": {
                "listings": len(over),
                "pages_beyond_the_window": beyond,
                "usd": usd(beyond),
                "of_which_the_largest": over[0] if over else None,
                "pages_without_the_largest": beyond - largest,
                "usd_without_the_largest": usd(beyond - largest),
                "basis": "from reported totals: a listing above the window is read through its child categories, at about "
                         "total/40 pages if the children do not overlap. A lower bound on pages when they do; a child "
                         "above the window goes a level deeper",
                "listings_above_the_window": over,
            },
        },
        "product_pages": {
            "usd_per_1000_products": usd(1000),
            "items_with_a_saved_read_today": m["items_with_a_saved_read"],
            "saved_reads_from_to": [m["saved_reads_from"], m["saved_reads_to"]],
            "saved_reads_counted_for_a_run_started_on": AS_OF,
            "saved_reads_last": "30 days from their own date (detail.reuse_days), so the oldest run out on 2026-11-27 and "
                                "the newest on 2026-12-04",
            "result_pages_measured": m["fresh_products_whose_result_page_left_the_upc_or_size_to_their_own_page"],
            "known_products": dict(known_products, usd=usd(known_pages),
                                   basis="a count: L12's exported records. No UPC or no size, and no saved read"),
            "products_not_yet_seen": {
                "fresh_valid_products_per_listing_page_measured": fresh,
                "products": {"low": round(new_low), "high": round(new_high)},
                "usd": {"low": usd(new_low), "high": usd(new_high)},
                "basis": "ESTIMATE: the known listing pages times the fresh valid products per page of L10 (low) and L4r "
                         "(high); the continuation counts them. Listings overlap, and more so as they are read further, "
                         "so even the low figure can be high. New branches add more",
            },
            "total_estimate": {"low": usd(product_low), "high": usd(product_high)},
            "active_hours_with_two_workers": {
                "low": round(product_low * product_seconds / 2 / 3600, 1),
                "high": round(product_high * product_seconds / 2 / 3600, 1),
                "seconds_per_product_page_measured": product_seconds,
            },
        },
        "retries": {
            "measured_in_the_15_live_runs": kinds,
            "on_known_listing_pages_usd": usd(submissions * float(kinds["listing"]["share_of_billed_results_that_are_retries"])),
            "on_product_pages_usd": {"low": usd(product_low * retry_product), "high": usd(product_high * retry_product)},
            "basis": "the share of billed results that were attempts after the first; a provider failure that is documented "
                     "free costs time, not money. An unknown outcome stays reserved until settled",
        },
        "listing_page_seconds_measured": listing_seconds,
        "one_later_scheduled_run": {
            "listing_pages": round(full_run),
            "submissions_with_overhead": full_run_submissions,
            "usd": usd(full_run_submissions),
            "active_hours_at_the_L10_rate": round(full_run / PAGES_PER_ACTIVE_MIN / 60, 1),
            "basis": "ESTIMATE from the same table, every listing page once: known totals capped at the window, the row "
                     "mean where none is known, new branches excluded. A saved read serves 30 days, so product pages are "
                     "paid once per product per 30 days, not per run: at two runs a week, about one full product-page "
                     "bill (the figures above) in each 30 days",
        },
        "does_not_price": "Scrape.do, a later change in how the site lists products, and anything in the client's Azure "
                          "environment",
    }
    Path(argv[1]).write_bytes((json.dumps(result, indent=1) + "\n").encode("utf-8"))
    print(json.dumps({
        "known_listing_pages": {k: v for k, v in result["known_listing_pages"].items() if k != "states"},
        "states": {k: {"listings": v["listings"], "pages": v["pages"]} for k, v in known.items()},
        "category_pages": result["new_branches"]["category_pages_not_read"]["pages"],
        "scenarios": scenarios,
        "beyond": {k: v for k, v in result["new_branches"]["beyond_the_result_window"].items()
                   if k not in ("listings_above_the_window", "basis")},
        "product_pages": result["product_pages"],
        "one_later_scheduled_run": {k: v for k, v in result["one_later_scheduled_run"].items() if k != "basis"},
        "retries": {k: v for k, v in result["retries"].items() if k != "basis"},
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
