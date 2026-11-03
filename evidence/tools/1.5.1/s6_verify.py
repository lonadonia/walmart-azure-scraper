"""Stage S6's checks on release 1.5.1 (TEST_PLAN_150.md, amendments A1 and A2), from the stage's exports and the campaign's
database. Read only; no request. usage: <edition venv python> -I -X utf8 s6_verify.py STAGE OUT.json
"""

from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

import pgserver
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

EV = Path(r"C:\w7\evidence\live150")
FIELDS = (
    "zipcode store_name store_location store_logo store_brand category sub_category product_title weight regular_price "
    "sale_price volume_deals_description volume_deals_price digital_deals_description digital_deals_price image_url url "
    "upc gupc ppm unit_price crawl_date"
).split()
MULTIPACK_1_5_0 = "13388557389 18491854361 18472720019 20475405083 18468708077 15345264397 18511760810 20636621408 18529653937".split()
PRICE = re.compile(r"^\d+\.\d{2}$")


def item(url: str) -> str:
    return url.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1]


def main() -> int:
    stage, out = sys.argv[1], Path(sys.argv[2])
    run = json.loads((EV / "runs.json").read_text("utf-8"))[stage]
    base = EV / "runs" / stage / "exports"
    fresh = json.loads((base / "products_fresh.json").read_text("utf-8"))
    every = json.loads((base / "products.json").read_text("utf-8"))
    disp = json.loads((base / "field_dispositions.json").read_text("utf-8"))
    manifest = json.loads((base / "manifest.json").read_text("utf-8"))
    report: dict = {"stage": stage, "run_id": run, "evidence_class": "LIVE VERIFIED", "manifest_keys": sorted(manifest)}
    report["manifest"] = {k: manifest[k] for k in manifest if k in ("run_id", "mode", "source_revision", "version", "parser_version", "dataset", "provider", "store", "edition", "collector_version", "build")}
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
        "crawl_dates_fresh": dict(collections.Counter(p["crawl_date"] for p in fresh)),
        "regular_price_format_ok": all(PRICE.match(p["regular_price"]) for p in fresh if p["regular_price"]),
        "sale_price_format_ok": all(PRICE.match(p["sale_price"]) for p in fresh if p["sale_price"]),
        "sale_below_regular": all(float(p["sale_price"]) < float(p["regular_price"]) for p in fresh if p["sale_price"] and p["regular_price"]),
    }
    report["store_context_fresh"] = {
        "zipcode": dict(collections.Counter(p["zipcode"] for p in fresh)),
        "store_name": dict(collections.Counter(p["store_name"] for p in fresh)),
        "store_location": dict(collections.Counter(p["store_location"] for p in fresh)),
        "store_logo_filled": sum(1 for p in fresh if p["store_logo"]),
    }
    report["filled_fresh"] = {f: sum(1 for p in fresh if p[f]) for f in FIELDS}
    report["store_brand_fresh"] = dict(collections.Counter(p["store_brand"] for p in fresh))
    report["upc_outcomes_fresh"] = dict(collections.Counter(d["upc"]["disposition"] for d in disp if d.get("observation_kind") == "fresh"))
    report["weight_outcomes_fresh"] = dict(collections.Counter(d["weight"]["disposition"] for d in disp if d.get("observation_kind") == "fresh"))
    by_item = {item(p["url"]): p for p in every}
    fresh_items = set(ids)
    report["multipack_items_of_1_5_0"] = [
        {"item_id": i, "fresh_in_this_stage": i in fresh_items, "weight": by_item[i]["weight"], "ppm": by_item[i]["ppm"], "regular_price": by_item[i]["regular_price"], "product_title": by_item[i]["product_title"]}
        for i in MULTIPACK_1_5_0 if i in by_item
    ]
    report["multipack_rule_fresh"] = []
    prov = json.loads((base / "provenance.json").read_text("utf-8"))["records"]
    for p in fresh:
        spec = (prov.get(f"wm:{item(p['url'])}", {}).get("fields") or {}).get("weight") or {}
        if "multipack_in_title" in str(spec.get("selector_or_path")):
            report["multipack_rule_fresh"].append({"item_id": item(p["url"]), "weight": p["weight"], "ppm": p["ppm"], "regular_price": p["regular_price"], "product_title": p["product_title"]})
    report["multipack_rule_fresh_count"] = len(report["multipack_rule_fresh"])
    leading = re.compile(r"^\(\s*\d+\s?-?\s?pack\s*\)", re.I)
    report["bracketed_pack_titles_fresh"] = [
        {"item_id": item(p["url"]), "store_brand": p["store_brand"], "weight": p["weight"], "product_title": p["product_title"]}
        for p in fresh if leading.match(p["product_title"])
    ]
    srv = pgserver.get_server(r"C:\w7\live\pgdata", cleanup_mode=None)
    url = make_url(srv.get_uri()).set(drivername="postgresql+psycopg", database="walmart_live150")
    with create_engine(url).connect() as c:
        report["run"] = {k: str(v) for k, v in c.execute(text("select status, stop_code, stop_detail, started_at, finished_at, parser_version, site_version, attempt from runs where id = :r"), {"r": run}).mappings().one().items()}
        report["ledger_run"] = [{"outcome": a, "submissions": int(b), "credits": float(d), "first": str(e), "last": str(f)} for a, b, d, e, f in c.execute(text("select outcome, count(*), sum(credits), min(at), max(at) from provider_usage where run_id = :r group by 1"), {"r": run}).all()]
        report["ledger_campaign"] = [{"outcome": a, "submissions": int(b)} for a, b in c.execute(text("select outcome, count(*) from provider_usage group by 1")).all()]
        report["pages"] = [{"purpose": a, "fetches": int(b), "distinct_urls": int(d)} for a, b, d in c.execute(text("select purpose, count(*), count(distinct url) from page_fetches where run_id = :r group by 1"), {"r": run}).all()]
        report["segments"] = [{"id": a, "started": str(b), "ended": str(d), "active_s": float(e or 0), "stop_code": f, "credits_estimated": float(g or 0)} for a, b, d, e, f, g in c.execute(text("select id, started_at, ended_at, active_s, stop_code, credits_estimated from collection_segments where run_id = :r order by started_at"), {"r": run}).all()]
        report["events"] = dict(c.execute(text("select type, count(*) from events where run_id = :r group by 1 order by 1"), {"r": run}).all()) if False else {}
        report["coverage"] = [dict(zip(("status", "total_count", "organic_upcs", "coverage_ratio", "partition"), row, strict=True)) for row in c.execute(text("select status, total_count, organic_upcs, coverage_ratio, partition from node_coverage where run_id = :r"), {"r": run}).all()]
        report["gate_failures"] = [dict(zip(("gate", "code", "scope", "ref", "message"), row, strict=True)) for row in c.execute(text("select gate, code, scope, ref, message from validation_findings where run_id = :r and severity = 'FAIL' order by gate, code"), {"r": run}).all()]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1, ensure_ascii=False, default=str) + "\n", "utf-8")
    print(json.dumps({k: report[k] for k in ("fresh_rows", "fresh_distinct_items", "export_rows_with_carried", "by_category", "by_sub_category", "contract", "store_context_fresh", "store_brand_fresh", "upc_outcomes_fresh", "weight_outcomes_fresh", "multipack_rule_fresh_count", "run", "ledger_run", "ledger_campaign", "pages", "segments")}, indent=0, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
