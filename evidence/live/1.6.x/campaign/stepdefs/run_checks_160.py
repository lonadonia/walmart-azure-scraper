"""The checks of one 1.6.0 live stage (offline; no request), from the stage's exports, the collector's database and
the shared trial ledger: release 1.6.0's version of the published S6_CHECKS.json (C:/w7/tools/s6_verify.py), with
the 1.6.0 additions: the four deal fields in every row (W1), the offers file, new versus reused product-detail
evidence, the follow-up outcomes, the run's segments (pause, kill and resumes) and the stage's rows in the shared
ledger.

usage: <edition venv python> -I -X utf8 run_checks_160.py LABEL STAGE_ID OUT.json
"""

from __future__ import annotations

import collections
import csv
import json
import os
import re
import sys
from pathlib import Path

os.environ["PSYCOPG_IMPL"] = "python"
os.environ["PATH"] = (
    "C:/w9/live/ed/walmart-oxylabs-1.6.0/.venv/Lib/site-packages/pgserver/pginstall/bin"
    + os.pathsep
    + os.environ.get("PATH", "")
)
sys.path.insert(0, "C:/w9/live")
LEDGER_DIR = Path("<projects>/.shared-oxylabs-trial-20261103")
sys.path.insert(0, str(LEDGER_DIR))
import live160_run as h  # noqa: E402
import oxytrial_ledger  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402

EV = Path("C:/w9/evidence/live160")
FIELDS = (
    "zipcode store_name store_location store_logo store_brand category sub_category product_title weight regular_price "
    "sale_price volume_deals_description volume_deals_price digital_deals_description digital_deals_price image_url url "
    "upc gupc ppm unit_price crawl_date"
).split()
DEALS = ("volume_deals_description", "volume_deals_price", "digital_deals_description", "digital_deals_price")
PRICE = re.compile(r"^\d+\.\d{2}$")


def item(url: str) -> str:
    return url.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1]


def main() -> int:
    label, stage_id, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    run = json.loads((EV / "runs.json").read_text("utf-8"))[label]
    base = EV / "runs" / label / "exports"
    fresh = json.loads((base / "products_fresh.json").read_text("utf-8"))
    every = json.loads((base / "products.json").read_text("utf-8"))
    disp = json.loads((base / "field_dispositions.json").read_text("utf-8"))
    manifest = json.loads((base / "manifest.json").read_text("utf-8"))
    offers = json.loads((base / "offers.json").read_text("utf-8"))
    report: dict = {"stage": label, "run_id": run, "evidence_class": "LIVE VERIFIED", "manifest_keys": sorted(manifest)}
    report["manifest"] = {
        k: manifest[k]
        for k in manifest
        if k in ("run_id", "mode", "source_revision", "version", "parser_version", "dataset", "provider", "store",
                 "edition", "collector_version", "build", "site_version", "fresh_record_count", "record_count")
    }
    ids = [item(p["url"]) for p in fresh]
    report["fresh_rows"] = len(fresh)
    report["fresh_distinct_items"] = len(set(ids))
    report["export_rows_with_carried"] = len(every)
    report["by_category"] = dict(collections.Counter(p["category"] for p in fresh))
    report["by_sub_category"] = dict(collections.Counter(p["sub_category"] for p in fresh))
    report["contract"] = {
        "field_order_ok": all(list(p) == FIELDS for p in every),
        "all_strings": all(isinstance(v, str) for p in every for v in p.values()),
        "gupc_empty": all(not p["gupc"] for p in every),
        "unit_price_empty": all(not p["unit_price"] for p in every),
        "deal_fields_empty_in_every_row": all(p[f] == "" for p in every for f in DEALS),
        "rows_checked_for_deal_fields": len(every),
        "crawl_dates_fresh": dict(collections.Counter(p["crawl_date"] for p in fresh)),
        "regular_price_format_ok": all(PRICE.match(p["regular_price"]) for p in fresh if p["regular_price"]),
        "sale_price_format_ok": all(PRICE.match(p["sale_price"]) for p in fresh if p["sale_price"]),
        "sale_below_regular": all(
            float(p["sale_price"]) < float(p["regular_price"]) for p in fresh if p["sale_price"] and p["regular_price"]
        ),
    }
    report["store_context_fresh"] = {
        "zipcode": dict(collections.Counter(p["zipcode"] for p in fresh)),
        "store_name": dict(collections.Counter(p["store_name"] for p in fresh)),
        "store_location": dict(collections.Counter(p["store_location"] for p in fresh)),
        "store_logo_filled": sum(1 for p in fresh if p["store_logo"]),
    }
    report["filled_fresh"] = {f: sum(1 for p in fresh if p[f]) for f in FIELDS}
    report["store_brand_fresh"] = dict(collections.Counter(p["store_brand"] for p in fresh))
    fresh_disp = [d for d in disp if d.get("observation_kind") == "fresh"]
    report["upc_outcomes_fresh"] = dict(collections.Counter(d["upc"]["disposition"] for d in fresh_disp))
    report["weight_outcomes_fresh"] = dict(collections.Counter(d["weight"]["disposition"] for d in fresh_disp))
    report["upc_outcomes_all_rows"] = dict(collections.Counter(d["upc"]["disposition"] for d in disp))
    report["weight_outcomes_all_rows"] = dict(collections.Counter(d["weight"]["disposition"] for d in disp))
    report["offers"] = {
        "entries": len(offers),
        "kinds": dict(collections.Counter(str(o.get("kind") or o.get("type") or "?") for o in offers))
        if isinstance(offers, list)
        else {},
        "note": "offers.json lists the deal offers the run observed; by the W1 output policy none reaches the four "
        "deal fields, which are empty in every row",
    }
    cov = EV / "runs" / label / "coverage"
    fu = sorted(cov.glob("follow_up_outcomes_*.csv"))
    if fu:
        rows = list(csv.DictReader(fu[0].open(encoding="utf-8-sig")))
        report["follow_up_outcomes"] = dict(collections.Counter(f"{r.get('kind')} | {r.get('status')}" for r in rows))
    with create_engine(h.db_url()).connect() as c:
        c.execute(text("SET TRANSACTION READ ONLY"))
        q = lambda sql, **kw: c.execute(text(sql), {"r": run, **kw}).all()  # noqa: E731
        report["run"] = {
            k: str(v)
            for k, v in c.execute(
                text("select status, stop_code, stop_detail, started_at, finished_at, parser_version, site_version, "
                     "attempt from runs where id = :r"),
                {"r": run},
            ).mappings().one().items()
        }
        report["ledger_run"] = [
            {"outcome": a, "submissions": int(b), "credits": float(d or 0), "usd": str(u), "first": str(e), "last": str(f)}
            for a, b, d, u, e, f in q(
                "select outcome, count(*), sum(credits), sum(cost_usd), min(at), max(at) from provider_usage "
                "where run_id = :r group by 1 order by 1"
            )
        ]
        report["ledger_run_by_purpose"] = [
            {"purpose": a, "outcome": b, "submissions": int(n)}
            for a, b, n in q("select purpose, outcome, count(*) from provider_usage where run_id = :r group by 1, 2 "
                             "order by 1, 2")
        ]
        report["pages"] = [
            {"purpose": a, "fetches": int(b), "distinct_urls": int(d)}
            for a, b, d in q("select purpose, count(*), count(distinct url) from page_fetches where run_id = :r "
                             "group by 1 order by 1")
        ]
        report["detail_observations_this_run"] = [
            {"origin": a, "status": b, "rows": int(n), "with_upc": int(u)}
            for a, b, n, u in q("select origin, status, count(*), count(nullif(upc, '')) from detail_observations "
                                "where run_id = :r group by 1, 2 order by 1, 2")
        ]
        report["segments"] = [
            {"id": a, "started": str(b), "ended": str(d), "active_s": float(e or 0), "stop_code": f,
             "stop_detail": g, "credits_estimated": float(k or 0), "workers": w}
            for a, b, d, e, f, g, k, w in q(
                "select id, started_at, ended_at, active_s, stop_code, stop_detail, credits_estimated, workers "
                "from collection_segments where run_id = :r order by started_at"
            )
        ]
        report["coverage"] = [
            dict(zip(("category_source_id", "taxonomy_id", "status", "total_count", "organic_upcs", "coverage_ratio",
                      "partition"), row, strict=True))
            for row in q("select category_source_id, taxonomy_id, status, total_count, organic_upcs, coverage_ratio, "
                         "partition from node_coverage where run_id = :r order by id")
        ]
        report["gate_findings"] = [
            dict(zip(("gate", "severity", "code", "scope", "ref", "message"), row, strict=True))
            for row in q("select gate, severity, code, scope, ref, message from validation_findings where run_id = :r "
                         "order by gate, severity, code")
        ]
        report["store_attestations"] = [
            dict(zip(("phase", "observed_location_id", "observed_name", "observed_postal_code", "modality", "result"),
                     [str(x) for x in row], strict=True))
            for row in q("select phase, observed_location_id, observed_name, observed_postal_code, modality, result "
                         "from store_attestations where run_id = :r order by observed_at")
        ]
    led = oxytrial_ledger.open_ledger(LEDGER_DIR, "oxylabs-trial-20261103")
    srows = led.rows(stage_id=stage_id)
    agg: dict[str, dict] = {}
    for r in srows:
        k = f"{r['state']} | {r['settlement_kind'] or ''}"
        a = agg.setdefault(k, {"rows": 0, "worst_usd": 0.0, "settled_usd": 0.0, "settled_results": 0})
        a["rows"] += 1
        a["worst_usd"] += float(r["worst_usd"])
        a["settled_usd"] += float(r["settled_usd"] or 0)
        a["settled_results"] += int(r["settled_results"] or 0)
    report["shared_ledger_stage"] = {"stage_id": stage_id, "rows": len(srows),
                                     "by_state_and_settlement": {k: {kk: round(vv, 6) if isinstance(vv, float) else vv
                                                                     for kk, vv in v.items()} for k, v in agg.items()}}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1, ensure_ascii=False, default=str) + "\n", "utf-8")
    keys = ("fresh_rows", "fresh_distinct_items", "export_rows_with_carried", "by_sub_category", "contract",
            "upc_outcomes_fresh", "weight_outcomes_fresh", "offers", "follow_up_outcomes", "run", "ledger_run",
            "pages", "detail_observations_this_run", "segments", "shared_ledger_stage")
    print(json.dumps({k: report.get(k) for k in keys}, indent=0, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
