"""W4 coverage tables of the Walmart 1.6.x live stages (offline; no request): row -> root -> child -> page, with the
exact outstanding work. Reads the published 1.5.2 coverage table (the 2026-10-24 navigation and the reads up to
2026-10-31), the coverage reports of this delivery's live runs and their stored result pages (read-only database
query), and writes:

  W4_LISTINGS_1_6_2.csv  one row per (CSV row, listing): where it was named (2026-10-24 navigation, today's census),
                         every 1.6.x read of it, its best read, its state and what is still outstanding
  W4_ROWS_1_6_2.csv      one row per CSV row: listings named, read, complete, incomplete, not attempted, out of scope
  W4_PAGES_1_6_2.csv     one row per result page read in a 1.6.x run: products, organic, sponsored, totals, fetch
  W4_REVISITS_1_6_2.csv  the explicit revisits of the review: the five listings S6 left capped, Fresh Fruits,
                         Strawberries (0 on 2026-10-31) and Dry Dog Food (139/137/138)
  W4_SUMMARY_1_6_2.json  counts, inputs and their SHA-256

usage: python -I w4_coverage_162.py OUT_DIR LABEL=RUN_ID=RELEASE=COVERAGE_JSON ...
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
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
    """The read that went furthest: a complete one (the latest), else the one with most pages (the latest)."""
    done = [x for x in reads if x[2]["status"] in COMPLETE]
    if done:
        return done[-1]
    seen = [x for x in reads if x[2].get("pages_visited")]
    if not seen:
        return None
    return max(enumerate(seen), key=lambda t: (len(t[1][2]["pages_visited"]), t[0]))[1]


def outstanding(best: tuple[str, str, dict[str, Any]] | None, census: dict[str, Any] | None,
                kids: list[str], hist: dict[str, str] | None) -> tuple[str, str]:
    """(state, what is still to read) for one listing."""
    note = (census or {}).get("stop_reason") or ""
    if census is not None and census["status"] == "SKIPPED":
        return "OUT_OF_SCOPE", f"not read by design: {note}"
    if best is None:
        if census is not None and census["status"] == "PENDING":
            return "NOT_ATTEMPTED", "named by today's census, not reached before its ceiling: page 1 onward"
        if census is not None and census["status"] == "INCOMPLETE" and census.get("end") == "CATEGORY_PAGE":
            return "CATEGORY_PAGE", note
        if census is None and hist is not None:
            return "NOT_ATTEMPTED", "named on 2026-10-24, not read in any 1.6.x run (not named by today's census)"
        return "NOT_ATTEMPTED", "not read in any 1.6.x run"
    label, release, r = best
    st, end = r["status"], r.get("end") or ""
    if st in COMPLETE:
        return "COMPLETE", f"none: complete in {label} ({release}), {r.get('stop_reason') or ''}".rstrip(", ")
    if st == "PARTITIONED" or end == "RESULT_WINDOW":
        return "RESULT_WINDOW", (
            f"the site serves no more than {r['placed_identities']} of {r['reported_total']} reported; read through "
            f"its child categories ({len(kids)} named and read: see their rows); never reconcilable while its total "
            "moves" if kids else
            f"the site serves no more than {r['placed_identities']} of {r['reported_total']} reported and its "
            "Departments facet names no child that was read"
        )
    if end == "CATEGORY_PAGE":
        return "CATEGORY_PAGE", r.get("stop_reason") or ""
    last = max(int(p) for p in r["pages_visited"])
    if st == "CAPPED":
        return "PARTIAL", f"pages after {last} not read (a page limit of {label}); {r['reported_total']} reported"
    return "INCOMPLETE", f"{r.get('stop_reason') or ''} ({label})"


def main(argv: list[str]) -> int:
    out = Path(argv[0])
    runs = []
    for spec in argv[1:]:
        label, run_id, release, cov = spec.split("=", 3)
        runs.append((label, run_id, release, Path(cov)))
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
    census_label = runs[-1][0]  # the last run given is today's census
    inputs = {"historical": {"path": str(HIST), "sha256": sha(HIST)}}
    for label, run_id, release, cov in runs:
        d = json.loads(cov.read_text(encoding="utf-8"))
        assert d["run_id"] == run_id, (label, d["run_id"])
        inputs[label] = {"run_id": run_id, "release": release, "coverage_report": str(cov), "sha256": sha(cov)}
        for r in d["rows"]:
            key = (str(r["csv_row"]), r["listing_id"])
            by_key.setdefault(key, {}).update(
                {k: r[k] for k in ("category", "listing_name", "url", "found_via", "parent_listing")}
            )
            if label == census_label:
                census[key] = r
            if r.get("pages_visited") or r["status"] not in ("PENDING", "SKIPPED"):
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
        state, todo = outstanding(best, c, kids, hr)
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
                "state_1_6_2": state,
                "outstanding": todo,
                "revisit": REVISITS.get(key[1], ""),
            }
        )
    with (out / "W4_LISTINGS_1_6_2.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(listing_rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(listing_rows)
    # rows
    rows_out = []
    for row in sorted({k[0] for k in by_key} | set(row_info), key=int):
        mine = [r for r in listing_rows if r["csv_row"] == row]
        st = Counter(r["state_1_6_2"] for r in mine)
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
                   ("COMPLETE", "PARTIAL", "RESULT_WINDOW", "INCOMPLETE", "CATEGORY_PAGE", "NOT_ATTEMPTED",
                    "OUT_OF_SCOPE")},
                "row_complete": "no" if any(r["state_1_6_2"] not in ("COMPLETE", "OUT_OF_SCOPE") for r in mine)
                or not mine else "yes",
            }
        )
    with (out / "W4_ROWS_1_6_2.csv").open("w", newline="", encoding="utf-8") as f:
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
    with (out / "W4_PAGES_1_6_2.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(page_rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(page_rows)
    rev = [r for r in listing_rows if r["revisit"]]
    with (out / "W4_REVISITS_1_6_2.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rev[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rev)
    summary = {
        "inputs": inputs,
        "listings": len(listing_rows),
        "states": dict(Counter(r["state_1_6_2"] for r in listing_rows)),
        "rows": {r["csv_row"]: {k: v for k, v in r.items() if k.startswith("state_") or k == "row_complete"}
                 for r in rows_out},
        "pages": len(page_rows),
        "pages_by_run": dict(Counter(p["run_label"] for p in page_rows)),
        "full_scope_complete": all(r["row_complete"] == "yes" for r in rows_out),
    }
    (out / "W4_SUMMARY_1_6_2.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "inputs"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
