"""The campaign database's tables as CSV for the evidence package: one set per run, one set for the campaign. Read only; no request.
A column that could hold a credential does not exist in these tables (provider_keys holds a fingerprint); the package's secret scan still reads every file.
usage: <edition venv python> -I -X utf8 export_campaign_db_151.py OUT_DIR
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pgserver
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

EV = Path(r"C:\w7\evidence\live150")
PER_RUN = {
    "page_fetches": "select id, run_id, task_id, url, purpose, http_status, started_at, duration_ms, challenge, dom_artifact_id, screenshot_artifact_id from page_fetches where run_id = :r order by started_at",
    "provider_usage": "select id, at, provider, key_role, key_fingerprint, run_id, retailer, purpose, endpoint, target_url, status, outcome, credits, cost_source, remaining_after, request_id, elapsed_ms, attempt, api_product, segment_id, worker, cost_usd from provider_usage where run_id = :r order by at",
    "collection_segments": "select * from collection_segments where run_id = :r order by started_at",
    "tasks": "select id, run_id, kind, idem_key, category_source_id, taxonomy_id, state, priority, attempts, lease_owner, lease_expires_at, not_before, cursor, last_error, created_at, updated_at from tasks where run_id = :r order by created_at",
    "events": "select id, run_id, ts, level, code, message, data from events where run_id = :r order by ts",
    "validation_findings": "select id, run_id, scope, ref, gate, severity, code, message, metrics, created_at from validation_findings where run_id = :r order by created_at",
    "node_coverage": "select id, run_id, category_source_id, taxonomy_id, total_count, organic_upcs, coverage_ratio, status, partition from node_coverage where run_id = :r",
    "artifacts": "select * from artifacts where run_id = :r",
}
CAMPAIGN = {
    "runs": "select id, store_id, trigger, status, mode, site_version, parser_version, robots_sha256, started_at, finished_at, counts, attempt, resumed_from_run_id, cancel_requested, pause_requested, stop_code, stop_detail, resume_requested, finish_requested, created_at, updated_at from runs order by created_at",
    "provider_usage_all": "select id, at, provider, key_role, key_fingerprint, run_id, retailer, purpose, endpoint, target_url, status, outcome, credits, cost_source, remaining_after, request_id, elapsed_ms, attempt, api_product, segment_id, worker, cost_usd from provider_usage order by at",
    "follow_up_queue": "select * from follow_up_queue order by kind, item_id",
    "detail_observations_fetched_in_campaign": "select id, store_id, item_id, observed_at, run_id, page_fetch_id, source_revision, origin, url, body_sha256, status, upc, upc_path, size_statements, created_at from detail_observations where origin = 'fetched' order by observed_at",
    "detail_observations_imported": "select id, store_id, item_id, observed_at, run_id, page_fetch_id, source_revision, origin, url, body_sha256, status, upc, upc_path, created_at from detail_observations where origin <> 'fetched' order by item_id, observed_at",
    "settings": "select * from settings order by key",
    "stores": "select * from stores",
    "store_attestations": "select * from store_attestations",
    "publications": "select * from publications",
    "publication_pointer": "select * from publication_pointer",
    "schedule_occurrences": "select * from schedule_occurrences",
    "alembic_version": "select * from alembic_version",
}


def cell(v: object) -> object:
    return json.dumps(v, ensure_ascii=False, default=str) if isinstance(v, (dict, list)) else v


def write(c, sql: str, path: Path, params: dict) -> int:
    res = c.execute(text(sql), params)
    keys = list(res.keys())
    rows = res.all()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(keys)
        for r in rows:
            w.writerow([cell(v) for v in r])
    return len(rows)


def main() -> int:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=False)
    srv = pgserver.get_server(r"C:\w7\live\pgdata", cleanup_mode=None)
    url = make_url(srv.get_uri()).set(drivername="postgresql+psycopg", database="walmart_live150")
    runs = json.loads((EV / "runs.json").read_text("utf-8"))
    counts: dict[str, int] = {}
    with create_engine(url).connect() as c:
        c.execute(text("begin read only"))
        for name, sql in CAMPAIGN.items():
            counts[f"campaign/{name}"] = write(c, sql, out / "campaign" / f"{name}.csv", {})
        for stage, run in runs.items():
            for name, sql in PER_RUN.items():
                counts[f"{run}/{name}"] = write(c, sql, out / "runs" / run / f"{name}.csv", {"r": run})
    (out / "DB_EXPORT_COUNTS.json").write_bytes((json.dumps({"runs": runs, "rows": counts}, indent=1) + "\n").encode("utf-8"))
    print(json.dumps({k: v for k, v in counts.items() if k.startswith("campaign/")}, indent=0))
    print(len(counts), "tables written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
