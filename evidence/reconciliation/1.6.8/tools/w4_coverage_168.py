"""W4 coverage tables of the Walmart 1.6.x live stages (offline; no request): row -> root -> child -> page, with the
exact outstanding work. Reads the published 1.5.2 coverage table (the 2026-10-24 navigation and the reads up to
2026-10-31), the coverage reports of this delivery's live runs and their stored result pages (read-only database
query), and writes:

  W4_LISTINGS_1_6_8.csv  one row per (CSV row, listing): where it was named (2026-10-24 navigation, today's census),
                         every 1.6.x read of it, its best read, its state and what is still outstanding
  W4_ROWS_1_6_8.csv      one row per CSV row: listings named, read, complete, incomplete, not attempted, out of scope
  W4_PAGES_1_6_8.csv     one row per result page read in a 1.6.x run: products, organic, sponsored, totals, fetch
  W4_REVISITS_1_6_8.csv  the explicit revisits of the review: the five listings S6 left capped, Fresh Fruits,
                         Strawberries (0 on 2026-10-31) and Dry Dog Food (139/137/138)
  W4_SUMMARY_1_6_8.json  counts, inputs and their SHA-256

usage (1.6.6): python -I w4_coverage_166.py OUT_DIR LABEL=RUN_ID=RELEASE=COVERAGE_JSON[=census] ...

Release 1.6.5 of this tool (from w4_coverage_164.py): today's census is two runs, L7 (rows 0 and 1, stopped on
1.6.3) and L10 (Bidets of row 1, rows 2 to 10, on 1.6.4). Each run marked "=census" names the listings of its
rows; for a listing two census runs name, the later one given counts. The census column is census_<labels>.

Release 1.6.6 of this tool (from w4_coverage_165.py): only the file names and the state column (1_6_6); the
runs are those of 1.6.5 plus L12 (one page of Fabric Softeners, on 1.6.6), which is not a census run.

Release 1.6.8 of this tool (from w4_coverage_166.py; written by make_w4_168.py): the same runs, each judged by the
coverage report the 1.6.8 collector made of it (the owner VM's container gate, 2026-11-05), by the rules of 1.6.7
and 1.6.8. A read is complete only when its recorded status, its status by the 1.3.1 rule and its effective
status are each DONE or EMPTY (a partition: its effective status, through its child categories). A read takes
precedence over a census skip. A skipped listing is classified by its note: not chosen by its run ->
NOT_ATTEMPTED; a category page of its own (/cp/) that releases up to 1.6.7 skipped as "a category page or other
page" -> SUBCATEGORY_PAGE_NOT_READ (open); a shop, brand, search, product or account link that note covered ->
OUT_OF_SCOPE_NOT_A_CATEGORY (the 1.6.8 rule, for the client to confirm); excluded by the client's CSV ->
OUT_OF_SCOPE_CSV; the row's own page -> OUT_OF_SCOPE_OWN_PAGE; robots.txt -> BLOCKED_ROBOTS (open); any other ->
SKIPPED_OTHER (open). W4_TRANSITIONS_1_6_6_TO_1_6_8.csv sets each listing's 1.6.6 state beside its 1.6.8 state.
A read of a filtered view (a link whose query narrows the listing: a facet, a price; the coverage report's
filtered_view_of) never completes anything. Of a listing with no read of its own: FILTERED_VIEW (open), the listing
itself is still to read. Of the row's own category: OUT_OF_SCOPE_FILTERED_ROW (closed), part of what the row's
subcategories list. The two shelves Food links both carry listing ID 0 in the stored runs, so they share one table row.
usage: python -I w4_coverage_168.py OUT_DIR W4_LISTINGS_1_6_6.csv LABEL=RUN_ID=RELEASE=COVERAGE_JSON[=census] ...
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit
from typing import Any

os.environ["PSYCOPG_IMPL"] = "python"
os.environ["PATH"] = (
    "C:/w9/live/ed/walmart-oxylabs-1.6.0/.venv/Lib/site-packages/pgserver/pginstall/bin"
    + os.pathsep
    + os.environ.get("PATH", "")
)
sys.path.insert(0, "C:/w9/live")
import live160_run as h  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402

HIST = Path("C:/w9/repo/data/COVERAGE_RECONCILIATION.csv")
COMPLETE = {"DONE", "EMPTY"}
LEGACY_SKIPPED_PAGE = "a category page or other page, not a product listing"  # releases up to 1.6.7
NOT_CHOSEN = "not among the subcategories chosen for this run"
NOT_A_CATEGORY = "a shop, brand, search, product or account page, not a category or result listing"  # 1.6.8
CSV_EXCLUDED = "excluded by the client's CSV"
OWN_PAGE = "the row's own category page"  # 1.6.8
ROBOTS = "robots.txt does not allow this page"
OPEN_STATES = {"PARTIAL", "RESULT_WINDOW", "INCOMPLETE", "CATEGORY_PAGE", "NOT_FOUND", "NOT_ATTEMPTED",
               "SUBCATEGORY_PAGE_NOT_READ", "BLOCKED_ROBOTS", "SKIPPED_OTHER", "FILTERED_VIEW"}
CLOSED_STATES = {"COMPLETE", "OUT_OF_SCOPE_CSV", "OUT_OF_SCOPE_NOT_A_CATEGORY", "OUT_OF_SCOPE_OWN_PAGE",
                 "OUT_OF_SCOPE_FILTERED_ROW"}


def complete_read(r: dict[str, Any]) -> bool:
    """The 1.6.7 rule, as coverage-report applies it to a row's listings: a partition through its effective status
    (its child categories); any other listing only when its status, its 1.3.1 status and its effective status are
    each complete."""
    if r["status"] == "PARTITIONED":
        return r.get("effective_status") in COMPLETE
    return (r["status"] in COMPLETE and r.get("status_rule_1_3_1") in COMPLETE
            and r.get("effective_status") in COMPLETE)


def skip_state(r: dict[str, Any]) -> tuple[str, str]:
    """(state, what is outstanding) of a listing a run skipped, by its note."""
    note = r.get("stop_reason") or ""
    cp = urlsplit(r.get("url") or "").path.startswith("/cp/")
    if note == CSV_EXCLUDED:
        return "OUT_OF_SCOPE_CSV", "none: excluded by the client's CSV"
    if note == OWN_PAGE:
        return "OUT_OF_SCOPE_OWN_PAGE", "none: the row's own category page (read as the row)"
    if note == NOT_CHOSEN:
        return "NOT_ATTEMPTED", "not chosen by the run that named it (a run narrowed to some subcategories): page 1 onward"
    if note == LEGACY_SKIPPED_PAGE and cp:
        return "SUBCATEGORY_PAGE_NOT_READ", (
            "a category page of its own that the row's navigation links: releases up to 1.6.7 skipped it, so the "
            "listings only it names were never read; release 1.6.8 reads it")
    if note in (LEGACY_SKIPPED_PAGE, NOT_A_CATEGORY):
        return "OUT_OF_SCOPE_NOT_A_CATEGORY", (
            "none if the client confirms the 1.6.8 rule: a shop, brand, search, product or account page, not a "
            "category or result listing")
    if note == ROBOTS:
        return "BLOCKED_ROBOTS", "robots.txt does not allow this page"
    return "SKIPPED_OTHER", f"skipped: {note}"
REVISITS = {
    "976759_976793_8910423": "capped at 3 pages by S6 (2026-10-31)",
    "1115193_1071967": "capped at 3 pages by S6 (2026-10-31)",
    "1085666_3147628_5752434": "capped at 3 pages by S6 (2026-10-31)",
    "976760_4661388_6244277_7158394": "capped at 3 pages by S6 (2026-10-31)",
    "5440_202072_6432755_1636265": "capped at 3 pages by S6 (2026-10-31); 139/137/138 reported on 2026-11-03",
    "976759_976793_9756351": "Fresh Fruits: read again in full",
    "976759_976793_9756351_3521037": "Strawberries: 0 results on 2026-10-31",
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def pages_text(pages: list[Any]) -> str:
    pages = sorted(int(p) for p in pages)
    if not pages:
        return ""
    if pages == list(range(pages[0], pages[-1] + 1)):
        return f"{pages[0]}-{pages[-1]}" if len(pages) > 1 else str(pages[0])
    return ";".join(map(str, pages))


def read_text(label: str, release: str, r: dict[str, Any]) -> str:
    bits = [f"{label} ({release}) {r['status']}"]
    if r.get("end"):
        bits.append(f"end {r['end']}")
    if r.get("pages_visited"):
        bits.append(f"pages {pages_text(r['pages_visited'])}")
    if r.get("reported_total") is not None:
        bits.append(f"reported {r['reported_total']}")
    if r.get("totals_reported") and len(set(r["totals_reported"])) > 1:
        bits.append(f"totals {'/'.join(map(str, r['totals_reported']))}")
    if r.get("pages_visited"):
        bits.append(f"placed {r['placed_identities']}")
    return ", ".join(bits)


def best_of(reads: list[tuple[str, str, dict[str, Any]]]) -> tuple[str, str, dict[str, Any]] | None:
    """The read that went furthest: a complete one (the latest), else the one with most pages (the latest), a
    read of the listing itself before a read of a filtered view of it."""
    done = [x for x in reads if complete_read(x[2])]
    if done:
        return done[-1]
    seen = [x for x in reads if x[2].get("pages_visited")]
    seen = [x for x in seen if not x[2].get("filtered_view_of")] or seen
    if not seen:
        return None
    return max(enumerate(seen), key=lambda t: (len(t[1][2]["pages_visited"]), t[0]))[1]


UNREAD_ENDS = ("CATEGORY_PAGE", "NOT_FOUND")  # the link answered with another page: recorded, not read


def outstanding(best: tuple[str, str, dict[str, Any]] | None, census: dict[str, Any] | None,
                kids: list[str], hist: dict[str, str] | None,
                reads: list[tuple[str, str, dict[str, Any]]]) -> tuple[str, str]:
    """(state, what is still to read) for one listing."""
    note = (census or {}).get("stop_reason") or ""
    of_row = [r for r in [*(x[2] for x in reads), *([census] if census else [])] if r.get("filtered_view_of") == "row"]
    if of_row and not any(x[2].get("pages_visited") and not x[2].get("filtered_view_of") for x in reads):
        return "OUT_OF_SCOPE_FILTERED_ROW", (
            f"none: a filtered view of the row's own category ({of_row[-1].get('filtered_view')}), part of what the "
            "row's subcategories list")
    if best is None and census is not None and census["status"] == "SKIPPED":
        return skip_state(census)
    if best is None:
        skipped = [x for x in reads if x[2]["status"] == "SKIPPED"]
        if census is None and skipped:  # skipped by a run that is not a census run
            return skip_state(skipped[-1][2])
        if census is not None and census["status"] == "INCOMPLETE" and census.get("end") in UNREAD_ENDS:
            return census["end"], note
        # 1.6.3: a link another run found answered with another page (the not-found page, a category page)
        unread = [x for x in reads if x[2]["status"] == "INCOMPLETE" and x[2].get("end") in UNREAD_ENDS]
        if unread:
            label, release, r = unread[-1]
            return r["end"], f"{r.get('stop_reason') or ''} ({label}, {release})"
        if census is not None and census["status"] == "PENDING":
            return "NOT_ATTEMPTED", "named by today's census, not reached before its ceiling: page 1 onward"
        if census is None and hist is not None:
            return "NOT_ATTEMPTED", "named on 2026-10-24, not read in any 1.6.x run (not named by today's census)"
        return "NOT_ATTEMPTED", "not read in any 1.6.x run"
    label, release, r = best
    st, end = r["status"], r.get("end") or ""
    if r.get("filtered_view_of") == "listing":
        return "FILTERED_VIEW", (
            f"only a filtered view was read ({r.get('filtered_view')}) in {label} ({release}): the listing itself, "
            "page 1 onward")
    if complete_read(r):
        return "COMPLETE", f"none: complete in {label} ({release}), {r.get('stop_reason') or ''}".rstrip(", ")
    if st in COMPLETE:  # complete as recorded, not by the 1.6.7 rule
        return "INCOMPLETE", (
            f"recorded {st} in {label} ({release}), but {r.get('status_rule_1_3_1')} by the 1.3.1 rule and "
            f"{r.get('effective_status')} in effect: {r.get('effective_reason') or 'its products do not balance its total'}"
        )
    if st == "PARTITIONED" or end == "RESULT_WINDOW":
        return "RESULT_WINDOW", (
            f"the site serves no more than {r['placed_identities']} of {r['reported_total']} reported; read through "
            f"its child categories ({len(kids)} named and read: see their rows); never reconcilable while its total "
            "moves" if kids else
            f"the site serves no more than {r['placed_identities']} of {r['reported_total']} reported and its "
            "Departments facet names no child that was read"
        )
    if end in UNREAD_ENDS:
        return end, f"{r.get('stop_reason') or ''} ({label}, {release})"
    if not r.get("pages_visited"):
        return "INCOMPLETE", f"{r.get('stop_reason') or st} ({label})"
    last = max(int(p) for p in r["pages_visited"])
    if st == "CAPPED":
        return "PARTIAL", f"pages after {last} not read (a page limit of {label}); {r['reported_total']} reported"
    return "INCOMPLETE", f"{r.get('stop_reason') or ''} ({label})"


def main(argv: list[str]) -> int:
    out = Path(argv[0])
    old_table = Path(argv[1])
    runs = []
    census_runs = []
    for spec in argv[2:]:
        parts = spec.split("=")
        label, run_id, release, cov = parts[:4]
        runs.append((label, run_id, release, Path(cov)))
        if parts[4:] == ["census"]:
            census_runs.append(label)
        elif parts[4:]:
            raise SystemExit(f"unknown flag in {spec}")
    if not census_runs:
        raise SystemExit("no run is marked =census")
    out.mkdir(parents=True, exist_ok=True)
    hist_rows = list(csv.DictReader(HIST.open(encoding="utf-8")))
    row_info = {r["csv_row"]: r for r in hist_rows if r["level"] == "csv_row"}
    cat2row = {r["category"]: row for row, r in row_info.items()}
    assert len(cat2row) == len(row_info) == 11, "one CSV row per category"
    # The 2026-10-24 navigation rows name their category, not their CSV row.
    hist = {(cat2row[r["category"]], r["listing_id"]): r for r in hist_rows if r["level"] == "listing_20261024"}
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    reads: dict[tuple[str, str], list[tuple[str, str, dict[str, Any]]]] = defaultdict(list)
    census: dict[tuple[str, str], dict[str, Any]] = {}
    census_label = "+".join(census_runs)  # today's census: each listing as the last census run given names it
    inputs = {"historical": {"path": str(HIST), "sha256": sha(HIST)},
              "w4_1_6_6": {"path": str(old_table), "sha256": sha(old_table)}}
    for label, run_id, release, cov in runs:
        d = json.loads(cov.read_text(encoding="utf-8"))
        assert d["run_id"] == run_id, (label, d["run_id"])
        inputs[label] = {"run_id": run_id, "release": release, "coverage_report": str(cov), "sha256": sha(cov)}
        for r in d["rows"]:
            key = (str(r["csv_row"]), r["listing_id"])
            # a later run that read the listing directly (by its own path) knows no parent: never overwrite
            # what an earlier run established with an empty value (1.6.3: L9 read two children of L6 so)
            known = by_key.setdefault(key, {})
            known.update(
                {k: r[k] for k in ("category", "listing_name", "url", "found_via", "parent_listing")
                 if r.get(k) or k not in known}
            )
            if label in census_runs:
                census[key] = r
            if r.get("pages_visited") or r["status"] != "PENDING":
                reads[key].append((label, release, r))
    for key, r in hist.items():
        by_key.setdefault(key, {}).update(
            {k: v for k, v in (("category", r["category"]), ("listing_name", r["listing_name"]), ("url", r["url"]),
                               ("found_via", r["found_via"]), ("parent_listing", r["parent_listing"] or None))
             if not by_key.get(key, {}).get(k)}
        )
    children: dict[tuple[str, str], list[str]] = defaultdict(list)
    for (row, lid), info in by_key.items():
        if info.get("parent_listing"):
            children[(row, info["parent_listing"])].append(lid)
    listing_rows = []
    for key in sorted(by_key, key=lambda k: (int(k[0]), k[1])):
        info, rs, c, hr = by_key[key], reads.get(key, []), census.get(key), hist.get(key)
        kids = [k for k in children.get(key, []) if reads.get((key[0], k))]
        best = best_of(rs)
        state, todo = outstanding(best, c, kids, hr, rs)
        listing_rows.append(
            {
                "csv_row": key[0],
                "category": info.get("category") or row_info.get(key[0], {}).get("category", ""),
                "listing_id": key[1],
                "listing_name": info.get("listing_name") or "",
                "level": "child" if info.get("parent_listing") or (hr or {}).get("explanation", "").startswith(
                    "nested") else "root",
                "parent_listing": info.get("parent_listing") or "",
                "found_via": info.get("found_via") or "",
                "url": info.get("url") or "",
                "named_20261024": "yes" if hr is not None else "no",
                "status_1_5_2": (hr or {}).get("status_1_5_2", ""),
                f"census_{census_label}": "" if c is None else (
                    c["status"] + (f" ({c['stop_reason']})" if c["status"] in ("SKIPPED", "CAPPED") and
                                   c.get("stop_reason") and c["status"] == "SKIPPED" else "")
                ),
                "reads_1_6_x": " | ".join(read_text(lb, rel, r) for lb, rel, r in rs),
                "best_read": "" if best is None else best[0],
                "best_pages": "" if best is None else pages_text(best[2].get("pages_visited") or []),
                "best_reported_total": "" if best is None else best[2].get("reported_total"),
                "best_placed_identities": "" if best is None else best[2].get("placed_identities"),
                "best_with_children": "" if best is None else best[2].get("distinct_with_children"),
                "best_raw_placements": "" if best is None else best[2].get("raw_placements"),
                "best_distinct_identities": "" if best is None else best[2].get("distinct_identities"),
                "best_duplicate_placements": "" if best is None else best[2].get("duplicate_placements"),
                "best_sponsored_placements": "" if best is None else best[2].get("sponsored_placements"),
                "best_sponsored_only_products": "" if best is None else best[2].get("sponsored_only_products"),
                "best_excluded_approx_weight": "" if best is None else best[2].get("approx_weight_exclusions"),
                "best_excluded_other": "" if best is None else json.dumps(best[2].get("other_exclusions") or {},
                                                                          sort_keys=True),
                "best_unresolved_difference": "" if best is None else best[2].get("unresolved_difference"),
                "best_store_checks_passed_failed": "" if best is None else
                f"{best[2].get('store_checks_passed')}/{best[2].get('store_checks_failed')}",
                "best_status": "" if best is None else best[2]["status"],
                "best_end": "" if best is None else (best[2].get("end") or ""),
                "state_1_6_8": state,
                "outstanding": todo,
                "revisit": REVISITS.get(key[1], ""),
            }
        )
    with (out / "W4_LISTINGS_1_6_8.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(listing_rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(listing_rows)
    old = {(r["csv_row"], r["listing_id"]): r for r in csv.DictReader(old_table.open(encoding="utf-8"))}
    assert old and "state_1_6_6" in next(iter(old.values())), "not a W4 1.6.6 listings table"
    trans = []
    for r in listing_rows:
        o = old.get((r["csv_row"], r["listing_id"]))
        trans.append({"csv_row": r["csv_row"], "category": r["category"], "listing_id": r["listing_id"],
                      "listing_name": r["listing_name"], "url": r["url"],
                      "state_1_6_6": o["state_1_6_6"] if o else "(not in the 1.6.6 table)",
                      "outstanding_1_6_6": o["outstanding"] if o else "",
                      "state_1_6_8": r["state_1_6_8"], "outstanding_1_6_8": r["outstanding"]})
    gone = [k for k in old if k not in {(r["csv_row"], r["listing_id"]) for r in listing_rows}]
    for k in gone:
        o = old[k]
        trans.append({"csv_row": k[0], "category": o["category"], "listing_id": k[1], "listing_name": o["listing_name"],
                      "url": o["url"], "state_1_6_6": o["state_1_6_6"], "outstanding_1_6_6": o["outstanding"],
                      "state_1_6_8": "(not in the 1.6.8 table)", "outstanding_1_6_8": ""})
    with (out / "W4_TRANSITIONS_1_6_6_TO_1_6_8.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(trans[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(trans)
    # rows
    rows_out = []
    for row in sorted({k[0] for k in by_key} | set(row_info), key=int):
        mine = [r for r in listing_rows if r["csv_row"] == row]
        st = Counter(r["state_1_6_8"] for r in mine)
        hi = row_info.get(row, {})
        rows_out.append(
            {
                "csv_row": row,
                "category": hi.get("category") or (mine[0]["category"] if mine else ""),
                "category_url": hi.get("url", ""),
                "listings_known": len(mine),
                "roots": sum(1 for r in mine if r["level"] == "root"),
                "children": sum(1 for r in mine if r["level"] == "child"),
                "named_20261024": sum(1 for r in mine if r["named_20261024"] == "yes"),
                f"named_by_census_{census_label}": sum(1 for r in mine if r[f"census_{census_label}"]),
                **{f"state_{k.lower()}": st.get(k, 0) for k in
                   ("COMPLETE", "PARTIAL", "RESULT_WINDOW", "INCOMPLETE", "CATEGORY_PAGE", "NOT_FOUND",
                    "NOT_ATTEMPTED", "SUBCATEGORY_PAGE_NOT_READ", "BLOCKED_ROBOTS", "SKIPPED_OTHER",
                    "FILTERED_VIEW", "OUT_OF_SCOPE_CSV", "OUT_OF_SCOPE_NOT_A_CATEGORY", "OUT_OF_SCOPE_OWN_PAGE",
                    "OUT_OF_SCOPE_FILTERED_ROW")},
                "open_listings": sum(1 for r in mine if r["state_1_6_8"] not in CLOSED_STATES),
                "row_complete": "no" if any(r["state_1_6_8"] not in CLOSED_STATES for r in mine)
                or not mine else "yes",
            }
        )
    with (out / "W4_ROWS_1_6_8.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows_out)
    # pages (stored result pages of each run's listings)
    eng = create_engine(h.db_url())
    page_rows = []
    with eng.connect() as conn:
        conn.execute(text("SET TRANSACTION READ ONLY"))
        for label, run_id, release, _ in runs:
            for tax, part in conn.execute(
                text("SELECT taxonomy_id, partition FROM node_coverage WHERE run_id=:r ORDER BY taxonomy_id"),
                {"r": run_id},
            ):
                for p in (part or {}).get("result_pages") or []:
                    page_rows.append(
                        {
                            "run_label": label, "run_id": run_id, "release": release, "listing_id": tax,
                            "page": p.get("page"), "products": p.get("products"), "organic": p.get("organic"),
                            "sponsored": p.get("sponsored"), "new_identities": p.get("new_keys", ""),
                            "reported_total": p.get("reported_total"), "max_page": p.get("max_page"),
                            "page_count": p.get("page_count"), "grid_filter": p.get("grid_filter"),
                            "fetch_id": p.get("fetch_id"),
                        }
                    )
    with (out / "W4_PAGES_1_6_8.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(page_rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(page_rows)
    rev = [r for r in listing_rows if r["revisit"]]
    with (out / "W4_REVISITS_1_6_8.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rev[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rev)
    summary = {
        "inputs": inputs,
        "listings": len(listing_rows),
        "states": dict(Counter(r["state_1_6_8"] for r in listing_rows)),
        "rows": {r["csv_row"]: {k: v for k, v in r.items() if k.startswith("state_") or k == "row_complete"}
                 for r in rows_out},
        "pages": len(page_rows),
        "pages_by_run": dict(Counter(p["run_label"] for p in page_rows)),
        "full_scope_complete": all(r["row_complete"] == "yes" for r in rows_out),
        "rows_complete": sum(1 for r in rows_out if r["row_complete"] == "yes"),
        "transitions_1_6_6_to_1_6_8": dict(sorted(Counter(f"{t['state_1_6_6']} -> {t['state_1_6_8']}" for t in trans).items())),
    }
    (out / "W4_SUMMARY_1_6_8.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "inputs"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
