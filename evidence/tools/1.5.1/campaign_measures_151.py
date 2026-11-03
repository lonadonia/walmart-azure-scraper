"""What the owner-funded campaign of 2026-10-31 measured, for COST_AND_RUNTIME_REPORT.md: answer times per purpose, failures and
retries, session and restart costs, products per page and per unit, detail outcomes, from walmart_live150 and each stage's exports.
Read only; no request. usage: <edition venv python> -I -X utf8 campaign_measures_151.py OUT_DIR
"""

from __future__ import annotations

import collections
import csv
import json
import statistics
import sys
from pathlib import Path

import pgserver
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

EV = Path(r"C:\w7\evidence\live150")
RELEASE = {"S6": "1.5.1", "S7": "1.5.1"}


def pct(values: list[float], q: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(q * len(ordered)))]


def main() -> int:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=False)
    srv = pgserver.get_server(r"C:\w7\live\pgdata", cleanup_mode=None)
    url = make_url(srv.get_uri()).set(drivername="postgresql+psycopg", database="walmart_live150")
    runs = json.loads((EV / "runs.json").read_text("utf-8"))
    stages = {v: k for k, v in runs.items()}
    result: dict = {"evidence_class": "LIVE VERIFIED (measurements of the campaign's own ledger and stored pages; no request)"}
    with create_engine(url).connect() as c:
        c.execute(text("begin read only"))
        usage = [dict(r._mapping) for r in c.execute(text(
            "select at, run_id, purpose, outcome, status, credits, elapsed_ms, attempt, target_url, worker, segment_id from provider_usage order by at"))]
        segments = [dict(r._mapping) for r in c.execute(text(
            "select id, run_id, trigger, started_at, ended_at, active_s, credits_estimated, stop_code, workers from collection_segments order by started_at"))]
        fetches = [dict(r._mapping) for r in c.execute(text(
            "select run_id, purpose, http_status, duration_ms from page_fetches where run_id = any(:r)"), {"r": list(stages)})]
        run_times = {r.id: (r.created_at, r.started_at, r.finished_at, r.status, r.stop_code) for r in c.execute(text(
            "select id, created_at, started_at, finished_at, status, stop_code from runs where id = any(:r)"), {"r": list(stages)})}
        sizes = {r.purpose: (int(r.n), int(r.b)) for r in c.execute(text(
            "select pf.purpose, count(*) n, coalesce(sum(a.size_bytes), 0) b from page_fetches pf left join artifacts a on a.id = pf.dom_artifact_id where pf.run_id = any(:r) group by 1"), {"r": list(stages)})} if False else {}
    by_purpose: dict[str, list[float]] = collections.defaultdict(list)
    for u in usage:
        if u["outcome"] == "ok" and u["elapsed_ms"] is not None:
            by_purpose[u["purpose"]].append(u["elapsed_ms"] / 1000)
    result["answer_seconds_ok_by_purpose"] = {
        k: {"n": len(v), "median": round(statistics.median(v), 2), "mean": round(statistics.mean(v), 2), "p90": round(pct(v, 0.9), 2), "max": round(max(v), 2)}
        for k, v in sorted(by_purpose.items())
    }
    result["answer_seconds_by_release"] = {}
    for release in ("1.5.0", "1.5.1"):
        got: dict[str, list[float]] = collections.defaultdict(list)
        for u in usage:
            if u["outcome"] == "ok" and u["elapsed_ms"] is not None and RELEASE.get(stages[u["run_id"]], "1.5.0") == release:
                got[u["purpose"]].append(u["elapsed_ms"] / 1000)
        result["answer_seconds_by_release"][release] = {k: {"n": len(v), "median": round(statistics.median(v), 2), "mean": round(statistics.mean(v), 2)} for k, v in sorted(got.items())}
    result["not_ok_rows"] = [
        {"stage": stages[u["run_id"]], "at": u["at"].isoformat(), "purpose": u["purpose"], "outcome": u["outcome"], "status": u["status"], "credits": float(u["credits"] or 0), "elapsed_ms": u["elapsed_ms"], "attempt": u["attempt"], "target_url": (u["target_url"] or "")[:120]}
        for u in usage if u["outcome"] != "ok"
    ]
    result["retries_answered"] = [
        {"stage": stages[u["run_id"]], "at": u["at"].isoformat(), "purpose": u["purpose"], "attempt": u["attempt"], "elapsed_ms": u["elapsed_ms"], "target_url": (u["target_url"] or "")[:120]}
        for u in usage if u["outcome"] == "ok" and (u["attempt"] or 1) > 1
    ]
    rows = []
    for stage, run in runs.items():
        mine = [u for u in usage if u["run_id"] == run]
        pages = collections.Counter(f["purpose"] for f in fetches if f["run_id"] == run)
        segs = [s for s in segments if s["run_id"] == run]
        fresh = json.loads((EV / "runs" / stage / "exports" / "products_fresh.json").read_text("utf-8"))
        everything = json.loads((EV / "runs" / stage / "exports" / "products.json").read_text("utf-8"))
        disp = json.loads((EV / "runs" / stage / "exports" / "field_dispositions.json").read_text("utf-8"))
        upc = collections.Counter(d["upc"]["disposition"] for d in disp if d.get("observation_kind") == "fresh")
        weight = collections.Counter(d["weight"]["disposition"] for d in disp if d.get("observation_kind") == "fresh")
        active = sum(float(s["active_s"] or 0) for s in segs)
        listing_answers = [u["elapsed_ms"] / 1000 for u in mine if u["purpose"] == "listing" and u["outcome"] == "ok" and u["elapsed_ms"] is not None]
        created, started, finished, status, stop = run_times[run]
        rows.append({
            "stage": stage, "release": RELEASE.get(stage, "1.5.0"), "run_id": run, "status": status, "stop_code": stop or "",
            "started_at": started.isoformat() if started else "", "finished_at": finished.isoformat() if finished else "",
            "segments": len(segs), "workers": ",".join(str(s["workers"]) for s in segs), "active_seconds": round(active, 1),
            "ledger_rows": len(mine), "listing_pages": pages["listing"], "product_detail_pages": pages["product_detail"], "follow_up_pages": pages["product_page"],
            "robots_reads": pages["robots"], "store_reads": pages["store_page"], "valid_fresh": len(fresh), "carried": len(everything) - len(fresh),
            "valid_fresh_per_listing_page": round(len(fresh) / pages["listing"], 1) if pages["listing"] else "",
            "rows_per_1000_valid_fresh": round(len(mine) / len(fresh) * 1000, 1) if fresh else "",
            "usd_per_1000_valid_fresh_at_0_0010": round(len(mine) * 0.0010 / len(fresh) * 1000, 3) if fresh else "",
            "usd_per_1000_valid_fresh_at_0_0015": round(len(mine) * 0.0015 / len(fresh) * 1000, 3) if fresh else "",
            "listing_answer_mean_s": round(statistics.mean(listing_answers), 2) if listing_answers else "",
            "upc_outcomes": "; ".join(f"{k} {v}" for k, v in sorted(upc.items())),
            "weight_outcomes": "; ".join(f"{k} {v}" for k, v in sorted(weight.items())),
        })
    result["stages"] = rows
    result["segments"] = [
        {"stage": stages[s["run_id"]], "id": s["id"], "trigger": s["trigger"], "started_at": s["started_at"].isoformat(), "ended_at": s["ended_at"].isoformat() if s["ended_at"] else "", "active_s": float(s["active_s"] or 0), "credits_estimated": float(s["credits_estimated"] or 0), "stop_code": s["stop_code"] or "", "workers": s["workers"]}
        for s in segments if s["run_id"] in stages
    ]
    with (out / "CAMPAIGN_MEASURES_BY_STAGE.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    (out / "CAMPAIGN_MEASURES.json").write_bytes((json.dumps(result, indent=1, ensure_ascii=False, default=str) + "\n").encode("utf-8"))
    print(json.dumps({k: result[k] for k in ("answer_seconds_ok_by_purpose", "answer_seconds_by_release", "not_ok_rows", "retries_answered", "segments")}, indent=0, default=str))
    for r in rows:
        print({k: r[k] for k in ("stage", "ledger_rows", "listing_pages", "valid_fresh", "carried", "active_seconds", "valid_fresh_per_listing_page", "rows_per_1000_valid_fresh", "usd_per_1000_valid_fresh_at_0_0010", "listing_answer_mean_s", "status", "stop_code")})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
