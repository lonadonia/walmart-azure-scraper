"""Lists the records of a run's export that the collector's source check reports as mismatches (offline; no
request): the same inputs as `validate-export --run` (operations.validate_export: the run's products.json, and the
stored pages of the run and of every run its carried rows name), the collector's own checks/source_check.check,
and its full per-record result for each mismatch. Run with the 1.6.4 edition's Python.

usage: python -I -X utf8 source_mismatch_164.py RUN_ID OUT.json
"""

from __future__ import annotations

import gzip
import json
import os
import sys
import tempfile
from collections import Counter
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
from walmart_headless.checks import source_check  # noqa: E402

DATA = Path(r"C:\w9\live\data")


def main() -> int:
    run_id, out = sys.argv[1], Path(sys.argv[2])
    eng = create_engine(h.db_url())
    with eng.connect() as c:
        rows = c.execute(text("SELECT status, provenance FROM records WHERE run_id=:r"), {"r": run_id}).all()
        source_runs = {run_id} | {
            str(((p or {}).get("historical") or {}).get("run_id") or "") for st, p in rows if st == "historical"
        } - {""}
        keys = [
            k
            for (k,) in c.execute(
                text(
                    "SELECT a.key FROM page_fetches pf JOIN artifacts a ON a.id = pf.dom_artifact_id "
                    "WHERE pf.run_id = ANY(:rs) AND pf.dom_artifact_id IS NOT NULL"
                ),
                {"rs": sorted(source_runs)},
            )
        ]
        man = f"runs/walmart-3891-pickup/{run_id}/exports/manifest.json"  # the store's export folder
        loc = c.execute(
            text("SELECT s.location_id FROM runs r JOIN stores s ON s.id = r.store_id WHERE r.id=:r"), {"r": run_id}
        ).scalar_one()
    prefix = man.rsplit("/", 1)[0]
    records = json.loads((DATA / prefix / "products.json").read_text("utf-8"))
    with tempfile.TemporaryDirectory(prefix="w164src-") as tmp:
        pages_dir = Path(tmp)
        names = {}
        for i, key in enumerate(keys):
            data = (DATA / key).read_bytes()
            name = f"{i:04d}.html.gz"
            (pages_dir / name).write_bytes(data if data[:2] == b"\x1f\x8b" else gzip.compress(data))
            names[name] = key
        res = source_check.check(records, pages_dir, loc)
    bad = [r for r in res["results"] if r.get("result") == "mismatch"]
    for r in bad:
        r["source"]["page_key"] = names.get(r["source"]["page"], "")
    out.write_text(json.dumps({"run": run_id, "summary": res["summary"], "mismatched_fields": res["mismatched_fields"],
                               "source_runs": sorted(source_runs), "pages": len(keys), "mismatches": bad},
                              indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"summary": res["summary"], "fields": res["mismatched_fields"],
                      "by_status": Counter(r.get("status") for r in bad)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
