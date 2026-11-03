"""One row per run of the owner-funded live campaign of 2026-10-31 (brief sections 1A and 11): release, commit, times,
ledger, pages, records and field outcomes, from the campaign's database and each stage's exports. Read only; no request.
usage: <edition venv python> -I -X utf8 campaign_summary_151.py OUT_DIR
"""

from __future__ import annotations

import collections
import csv
import json
import sys
from decimal import Decimal
from pathlib import Path

import pgserver
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

EV = Path(r"C:\w7\evidence\live150")
RESERVE = Decimal("0.0015")
PUBLISHED = Decimal("0.0010")
RELEASES = {
    "S6": ("1.5.1", "488a033fc22d09db9f6270feae274d8c77963d6f"),
    "S7": ("1.5.1", "488a033fc22d09db9f6270feae274d8c77963d6f"),
}
DEFAULT = ("1.5.0", "7b6f3258e0f4ab755732605eb88717c592d07073")
FIELDS = [
    "stage", "run_id", "release", "source_commit", "evidence_class", "status", "stop_code", "created_at", "started_at",
    "finished_at", "segments", "segments_abandoned", "active_seconds", "submissions_ledger", "submissions_ok",
    "submissions_reserved_or_abandoned", "usd_at_reserve_rate_0_0015", "usd_at_published_rate_0_0010", "listing_pages",
    "product_detail_pages", "product_pages_followups", "robots_reads", "store_reads", "valid_fresh", "excluded", "historical",
    "export_rows", "upc_outcomes_fresh", "weight_outcomes_fresh", "categories_valid", "gates_failed", "coverage_statuses",
    "challenges", "http_not_200",
]


def main() -> int:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    srv = pgserver.get_server(r"C:\w7\live\pgdata", cleanup_mode=None)
    url = make_url(srv.get_uri()).set(drivername="postgresql+psycopg", database="walmart_live150")
    runs = json.loads((EV / "runs.json").read_text("utf-8"))
    rows = []
    with create_engine(url).connect() as c:
        for stage, run in runs.items():
            r = c.execute(text("select * from runs where id = :r"), {"r": run}).mappings().one()
            seg = c.execute(text("select active_s, stop_code, ended_at from collection_segments where run_id = :r"), {"r": run}).all()
            usage = c.execute(text("select outcome, count(*), sum(credits) from provider_usage where run_id = :r group by 1"), {"r": run}).all()
            pages = dict(c.execute(text("select purpose, count(*) from page_fetches where run_id = :r group by 1"), {"r": run}).all())
            bad = c.execute(text("select count(*) from page_fetches where run_id = :r and http_status <> 200"), {"r": run}).scalar()
            chal = c.execute(text("select count(*) from page_fetches where run_id = :r and challenge is not null and challenge::text not in ('', 'null', 'false')"), {"r": run}).scalar()
            status = dict(c.execute(text("select status, count(*) from records where run_id = :r group by 1"), {"r": run}).all())
            gates = c.execute(text("select distinct gate, code from validation_findings where run_id = :r and severity = 'FAIL' order by 1, 2"), {"r": run}).all()
            cov = c.execute(text("select status, count(*) from node_coverage where run_id = :r group by 1 order by 1"), {"r": run}).all()
            base = EV / "runs" / stage / "exports"
            upc: collections.Counter[str] = collections.Counter()
            weight: collections.Counter[str] = collections.Counter()
            export_rows = categories = 0
            cats: set[str] = set()
            disp = base / "field_dispositions.json"
            if disp.is_file():
                for d in json.loads(disp.read_text("utf-8")):
                    if d.get("observation_kind") == "fresh":
                        upc[d["upc"]["disposition"]] += 1
                        weight[d["weight"]["disposition"]] += 1
            products = base / "products.json"
            if products.is_file():
                export_rows = len(json.loads(products.read_text("utf-8")))
            fresh = base / "products_fresh.json"
            if fresh.is_file():
                cats = {p["category"] for p in json.loads(fresh.read_text("utf-8"))}
                categories = len(cats)
            ok = sum(n for o, n, _ in usage if o == "ok")
            total = sum(n for _, n, _ in usage)
            release, commit = RELEASES.get(stage, DEFAULT)
            rows.append({
                "stage": stage, "run_id": run, "release": release, "source_commit": commit, "evidence_class": "LIVE VERIFIED",
                "status": r["status"], "stop_code": r["stop_code"] or "", "created_at": r["created_at"].isoformat(),
                "started_at": r["started_at"].isoformat() if r["started_at"] else "",
                "finished_at": r["finished_at"].isoformat() if r["finished_at"] else "", "segments": len(seg),
                "segments_abandoned": sum(1 for s in seg if s[1] == "ABANDONED" or s[2] is None),
                "active_seconds": round(sum(float(s[0] or 0) for s in seg), 1), "submissions_ledger": total,
                "submissions_ok": ok, "submissions_reserved_or_abandoned": total - ok,
                "usd_at_reserve_rate_0_0015": str(RESERVE * total), "usd_at_published_rate_0_0010": str(PUBLISHED * total),
                "listing_pages": pages.get("listing", 0), "product_detail_pages": pages.get("product_detail", 0),
                "product_pages_followups": pages.get("product_page", 0), "robots_reads": pages.get("robots", 0),
                "store_reads": pages.get("store_page", 0), "valid_fresh": status.get("valid", 0),
                "excluded": status.get("excluded", 0), "historical": status.get("historical", 0), "export_rows": export_rows,
                "upc_outcomes_fresh": "; ".join(f"{k} {v}" for k, v in sorted(upc.items())),
                "weight_outcomes_fresh": "; ".join(f"{k} {v}" for k, v in sorted(weight.items())),
                "categories_valid": categories, "gates_failed": "; ".join(f"{g} {cd}" for g, cd in gates),
                "coverage_statuses": "; ".join(f"{s} {n}" for s, n in cov), "challenges": chal, "http_not_200": bad,
            })
        ledger = c.execute(text("select outcome, count(*), sum(credits), min(at), max(at) from provider_usage group by 1 order by 1")).all()
        ceilings = c.execute(text("select key, value, updated_at from settings where key like '%ceiling%' or key like '%budget%' order by key")).all()
    with (out / "CAMPAIGN_STAGES.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    total = sum(int(x[1]) for x in ledger)
    summary = {
        "evidence_class": "LIVE VERIFIED (the owner-funded campaign's ledger; estimates at the rates named, not invoices)",
        "ledger_by_outcome": {str(x[0]): {"submissions": int(x[1]), "credits": float(x[2]), "first": x[3].isoformat(), "last": x[4].isoformat()} for x in ledger},
        "submissions_total": total,
        "usd_at_reserve_rate": str(RESERVE * total),
        "usd_at_published_rate": str(PUBLISHED * total),
        "campaign_limit": {"submissions": 120, "usd_reserve_rate": "0.18"},
        "settings": {str(k): str(v)[:400] for k, v, _ in ceilings},
        "stages": rows,
    }
    (out / "CAMPAIGN_SUMMARY.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", "utf-8")
    print(json.dumps({k: summary[k] for k in ("ledger_by_outcome", "submissions_total", "usd_at_reserve_rate", "usd_at_published_rate")}, indent=1))
    for row in rows:
        print(row["stage"], row["release"], row["status"], row["submissions_ledger"], row["listing_pages"], row["product_detail_pages"], row["valid_fresh"], row["gates_failed"][:120])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
