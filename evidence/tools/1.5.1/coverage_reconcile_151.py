"""Section 5 of the brief: the coverage reconciliation carried into release 1.5.1 (written after the last live stage).

Every row of the 1.4.1 delivery's COVERAGE_RECONCILIATION.csv is kept unchanged and labelled HISTORICAL (carried
from 1.4.1). For each live listing read of the owner-funded campaign walmart_live150 (2026-10-31, Oxylabs Web
API, S1 to S5 on edition 7b6f325 (1.5.0), S6 and S7 on edition 488a033 (1.5.1)) a 'listing_run' row is added from the collector's own coverage report of that run
(C:/w7/evidence/live150/runs/<stage>/coverage/coverage_reconciliation_<run>.csv), labelled LIVE VERIFIED, with
the stage, run and database named. The 11 'csv_row' rows get two new columns: what the campaign read for that
row on 2026-10-31, and the row's status after the campaign. No row becomes complete: a capped, one-category or first-pages
read is never a full-scope run, and a final accessible page does not prove completeness while the reported
total and the placed products differ.
usage: python -I -X utf8 coverage_reconcile_150.py
"""

import collections
import csv
import glob
import json
from pathlib import Path

BASE = Path(r"<repository>")
COV_141 = BASE / "deliverables" / "20261028_walmart_1.4.1_dual_provider" / "COVERAGE_RECONCILIATION.csv"
LIVE = Path(r"C:\w7\evidence\live150")
OUT = Path(r"C:\w7\evidence\reconciliation_151")
RELEASE = {"S6": "1.5.1 (frozen edition 488a033)", "S7": "1.5.1 (frozen edition 488a033)"}
DEFAULT_RELEASE = "1.5.0 (frozen edition 7b6f325)"
STAGE_NOTE = {
    "S1": "canary, first page only",
    "S2": "targeted follow-ups, 3 pages per listing",
    "S3": "one category, every page the listing showed",
    "S4": "B3's scope, 3 pages per listing, killed and resumed",
    "S5a": "time-separated repeat, first page",
    "S5b_serial": "serial against parallel, first page, 1 worker",
    "S5b_parallel": "serial against parallel, first page, 2 workers",
    "S6": "the demonstration on 1.5.1: 5 subcategories, 3 pages per listing, killed and resumed, closed by finalize at its ceiling",
    "S7": "time-separated repeat on 1.5.1, first page of one listing, closed by finalize at its ceiling",
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    runs = json.loads((LIVE / "runs.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader(open(COV_141, encoding="utf-8-sig", newline="")))
    assert len(rows) == 1154, len(rows)
    cols = list(rows[0].keys())
    extra = ["evidence_class", "campaign_reads_2026_10_31", "status_1_5_1"]
    out = []
    live_rows = []
    for stage, run_id in runs.items():
        files = glob.glob(str(LIVE / "runs" / stage / "coverage" / f"coverage_reconciliation_{run_id}.csv"))
        assert len(files) == 1, (stage, files)
        for r in csv.DictReader(open(files[0], encoding="utf-8-sig", newline="")):
            row = {c: "" for c in cols + extra}
            for k, v in r.items():
                assert k in cols, k
                row[k] = v
            row.update({
                "level": "listing_run", "edition": "oxylabs", "release": RELEASE.get(stage, DEFAULT_RELEASE),
                "phase": f"campaign {stage}: {STAGE_NOTE.get(stage, '')}", "run": run_id,
                "database": "walmart_live150 (local, owner-funded campaign, 2026-10-31)",
                "production_status": "not a production run: a bounded pilot read of the campaign",
                "evidence_class": "LIVE VERIFIED",
            })
            live_rows.append((stage, row))
    by_csv_row: dict[str, list[str]] = collections.defaultdict(list)
    for stage, row in live_rows:
        by_csv_row[row["csv_row"]].append(
            f"{row['listing_name']} [{stage} {row['status']}: pages {row['pages_visited']}, reported total "
            f"{row['reported_total']}, placed {row['placed_identities']}, difference {row['difference_placed']}]")
    for r in rows:
        row = dict(r)
        row["evidence_class"] = "HISTORICAL (carried from 1.4.1)"
        row["campaign_reads_2026_10_31"] = ""
        row["status_1_5_1"] = ""
        if r["level"] == "csv_row":
            reads = by_csv_row.get(r["csv_row"], [])
            row["campaign_reads_2026_10_31"] = "; ".join(reads) if reads else "none (the row was not read on 2026-10-31)"
            row["evidence_class"] = "SUMMARY: the 1.4.1 columns carried; the last two columns from the campaign of 2026-10-31"
            row["status_1_5_1"] = ("INCOMPLETE: no full-scope run of the row's category and every applicable "
                                   "subcategory with every page has been run; the 2026-10-31 reads are bounded "
                                   "pilot reads" if reads else
                                   "INCOMPLETE: not read on 2026-10-31; 1.4.1's status stands")
        out.append(row)
    out.extend(row for _, row in live_rows)
    path = OUT / "COVERAGE_RECONCILIATION_1_5_1.csv"
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols + extra, lineterminator="\r\n")
        w.writeheader()
        w.writerows(out)
    tally = collections.Counter((r["level"], r["evidence_class"]) for r in out)
    status = collections.Counter(row["status"] for _, row in live_rows)
    print(json.dumps({"rows": len(out), "by_level": {f"{a} | {b}": n for (a, b), n in sorted(tally.items())},
                      "live_listing_reads_by_status": dict(status), "output": str(path)}, indent=1))


if __name__ == "__main__":
    main()
