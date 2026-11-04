"""The publishable evidence of one 1.6.0 live run (offline; no request), in the layout of the 1.5.2 publication
(evidence/live/runs/<run>/): the run's export files, its sanitized stored pages and robots answers, its
coverage report and field dispositions, CSV extracts of its database rows, the list of the provider's unsanitized
answer bodies (RAW_ORIGINALS_MANIFEST.csv: kept private, never packaged) and PAGE_LINEAGE.csv, which ties each
page fetch to its private original (SHA-256 of the raw body) and its public sanitized copy (SHA-256 of the
packaged page).

usage: python -I assemble_run_evidence.py RUN_ID LABEL OUT_DIR [COVERAGE_DIR] [FIELD_DISPOSITIONS_CSV]
"""

import csv
import gzip
import hashlib
import json
import os
import shutil
import sys
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

DATA = Path("C:/w9/live/data/runs/walmart-3891-pickup")
TABLES = {
    "page_fetches": "SELECT * FROM page_fetches WHERE run_id=:r ORDER BY started_at, id",
    "provider_usage": "SELECT * FROM provider_usage WHERE run_id=:r ORDER BY at, id",
    "events": "SELECT * FROM events WHERE run_id=:r ORDER BY ts, id",
    "tasks": "SELECT * FROM tasks WHERE run_id=:r ORDER BY id",
    "node_coverage": "SELECT * FROM node_coverage WHERE run_id=:r ORDER BY id",
    "validation_findings": "SELECT * FROM validation_findings WHERE run_id=:r ORDER BY id",
    "artifacts": "SELECT * FROM artifacts WHERE run_id=:r ORDER BY created_at, id",
    "collection_segments": "SELECT * FROM collection_segments WHERE run_id=:r ORDER BY started_at, id",
    "captured_responses": "SELECT * FROM captured_responses WHERE run_id=:r ORDER BY observed_at, id",
    "store_attestations": "SELECT * FROM store_attestations WHERE run_id=:r ORDER BY observed_at, id",
    "detail_observations": "SELECT * FROM detail_observations WHERE run_id=:r ORDER BY observed_at, id",
    "follow_up_queue_touched": "SELECT * FROM follow_up_queue WHERE last_run=:r OR first_seen_run=:r OR "
    "last_seen_run=:r ORDER BY kind, item_id",
    "runs": "SELECT id, store_id, trigger, status, mode, site_version, parser_version, robots_sha256, started_at, "
    "finished_at, counts, attempt, resumed_from_run_id, stop_code, stop_detail, created_at, updated_at, "
    "config_snapshot FROM runs WHERE id=:r",
}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def cell(v: object) -> str:
    if v is None:
        return ""
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True, default=str)
    return str(v)


def main() -> int:
    run_id, label, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    cov = Path(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4] else None
    fd = Path(sys.argv[5]) if len(sys.argv) > 5 and sys.argv[5] else None
    src = DATA / run_id
    if out.exists():
        raise SystemExit(f"{out} exists: an evidence folder is never rewritten")
    (out / "db").mkdir(parents=True)
    shutil.copytree(src / "exports", out / "exports")
    for sub, dest in (("dom", "pages"), ("robots", "robots")):
        if (src / "live" / sub).is_dir():
            shutil.copytree(src / "live" / sub, out / dest)
    if cov is not None:
        shutil.copytree(cov, out / "coverage")
    if fd is not None:
        shutil.copy2(fd, out / f"field_dispositions_{run_id}.csv")
    raws = sorted((src / "live" / "raw").glob("*")) if (src / "live" / "raw").is_dir() else []
    with (out / "RAW_ORIGINALS_MANIFEST.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["raw_file_on_the_workstation", "sha256", "bytes", "body_sha256"])
        for p in raws:
            b = p.read_bytes()
            w.writerow([f"runs/walmart-3891-pickup/{run_id}/live/raw/{p.name}", sha(b), len(b),
                        sha(gzip.decompress(b))])
    raw_by_fetch = {p.name.split(".", 1)[0]: p for p in raws}
    eng = create_engine(h.db_url())
    with eng.connect() as c:
        c.execute(text("SET TRANSACTION READ ONLY"))
        fetches = []
        for name, sql in TABLES.items():
            res = c.execute(text(sql), {"r": run_id})
            cols = list(res.keys())
            rows = res.fetchall()
            with (out / "db" / f"{name}.csv").open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f, lineterminator="\n")
                w.writerow(cols)
                for r in rows:
                    w.writerow([cell(v) for v in r])
            if name == "page_fetches":
                fetches = [dict(zip(cols, r, strict=True)) for r in rows]
    with (out / "PAGE_LINEAGE.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["page_fetch_id", "purpose", "url", "http_status", "started_at", "challenge",
                    "private_original_file", "private_original_file_sha256", "private_original_body_sha256",
                    "public_copy", "public_copy_file_sha256", "public_copy_body_sha256"])
        for pf in fetches:
            raw = raw_by_fetch.get(pf["id"])
            rb = raw.read_bytes() if raw else b""
            dom = out / "pages" / f"{pf['id']}.html.gz"
            rob = sorted((out / "robots").glob(f"{pf['id']}.*")) if (out / "robots").is_dir() else []
            pub = dom if dom.is_file() else (rob[0] if rob else None)
            pb = pub.read_bytes() if pub else b""
            w.writerow([
                pf["id"], pf["purpose"], pf["url"], cell(pf["http_status"]), cell(pf["started_at"]),
                cell(pf["challenge"]), raw.name if raw else "", sha(rb) if raw else "",
                sha(gzip.decompress(rb)) if raw else "",
                pub.relative_to(out).as_posix() if pub else "", sha(pb) if pub else "",
                (sha(gzip.decompress(pb)) if pub.name.endswith(".gz") else sha(pb)) if pub else "",
            ])
    (out / "STAGE.txt").write_text(label + "\n", encoding="utf-8")
    files = sorted(p for p in out.rglob("*") if p.is_file())
    print(json.dumps({"run": run_id, "label": label, "files": len(files),
                      "bytes": sum(p.stat().st_size for p in files), "raw_originals": len(raws),
                      "page_fetches": len(fetches)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
