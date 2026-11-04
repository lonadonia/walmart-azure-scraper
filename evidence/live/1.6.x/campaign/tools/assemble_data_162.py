"""Write the data/ folder of the 1.6.2 publication (offline; reads the staged run evidence and the 1.5.2 summary).

usage: python -I assemble_data_162.py PUB_ROOT OLD_RUN_SUMMARY LABEL=RELEASE=STAGE_ID[=deliver] ...

PUB_ROOT          the staged publication (its evidence/live/1.6.x/runs/<LABEL>_<run>/ and campaign/shared_ledger/)
OLD_RUN_SUMMARY   data/RUN_SUMMARY.json of review-1.5.2-20261103 (the nine 1.5.x stages, kept with their values)
LABEL=...         one per 1.6.x run, in run order; "=deliver" copies the run's product files to
                  data/<LABEL>-<RELEASE>/: products_fresh.json/.csv (the run's exports/products_fresh.*) and
                  products_retained.json/.csv (its exports/products.*), byte for byte

Writes PUB_ROOT/data/RUN_SUMMARY.json: the 1.5.x stages as 1.5.2 recorded them, with repository paths (their
delivered files in data/<stage>-<release>/, their exports in evidence/live/runs/<run>/exports), then one entry per
1.6.x run computed from its own evidence (database extract, export manifest, validation report) and from the shared
ledger's reservations of its stage. Every count is read from those files; nothing is typed in.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

PROVIDER_PRODUCT = "Oxylabs Web API (Bearer key; not the Classic Web Scraper API)"
# the edition ZIP each 1.6.x release ran from (C:/w9/live/dist/*.sha256; evidence/live/1.6.x/builds/)
EDITION_ZIP = {
    "1.6.0": "5a70e4616c8a37875103787323e99943a74237024bcf58ee2322c17a1da1febd",
    "1.6.1": "805f69211a2bb456c2e30741a9c2d3aa1d8f5125b87549d03e7fc360a61bdf68",
    "1.6.2": "91230d32052a0ab1fb30e98159078c6d2d99cae65c05e8c6930a202c6c2ef97c",
}
OLD_FOLDER = {"live/S6_1.5.1/": "data/S6-1.5.1/", "live/S7_1.5.1/": "data/S7-1.5.1/", "live/S4_1.5.0/": "data/S4-1.5.0/"}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def rows(p: Path) -> list[dict[str, str]]:
    with p.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def count_rows(p: Path) -> int:
    if p.suffix == ".json":
        return len(json.loads(p.read_text("utf-8")))
    with p.open(encoding="utf-8-sig", newline="") as f:
        return sum(1 for _ in csv.DictReader(f))


def old_stage(st: dict) -> dict:
    st = dict(st)
    st["exports"] = f"evidence/live/runs/{st['run']}/exports"
    st["run_folder_in_repository"] = f"evidence/live/runs/{st['run']}"
    files = {}
    for name, info in (st.get("delivered_files") or {}).items():
        for a, b in OLD_FOLDER.items():
            if name.startswith(a):
                files[b + name[len(a):]] = info
                break
        else:
            raise SystemExit(f"no repository folder for {name}")
    st["delivered_files"] = files
    return st


def new_stage(pub: Path, label: str, release: str, stage_id: str, deliver: bool, store: dict,
              ledger: list[dict[str, str]]) -> dict:
    found = sorted((pub / "evidence/live/1.6.x/runs").glob(f"{label}_*"))
    if len(found) != 1:
        raise SystemExit(f"{label}: {len(found)} run folders")
    folder = found[0]
    run = folder.name.split("_", 1)[1]
    rel = folder.relative_to(pub).as_posix()
    (r,) = [x for x in rows(folder / "db/runs.csv") if x["id"] == run]
    manifest = json.loads((folder / "exports/manifest.json").read_text("utf-8"))
    report = json.loads((folder / "exports/validation_report.json").read_text("utf-8"))
    code = manifest["config_snapshot"]["code"]
    if code["version"] != release:
        raise SystemExit(f"{label}: export names release {code['version']}, not {release}")
    segs = rows(folder / "db/collection_segments.csv")
    usage = rows(folder / "db/provider_usage.csv")
    cover = rows(folder / "db/node_coverage.csv")
    fetches = rows(folder / "db/page_fetches.csv")
    counts = report.get("counts", {})
    gates = counts.get("gates", {})
    by_status = counts.get("records_by_status", {})
    mine = [x for x in ledger if x["stage_id"] == stage_id]
    led_state = Counter(x["state"] for x in mine)
    led_usd = {s: str(sum((Decimal(x["settled_usd"] if s == "settled" else x["worst_usd"]) for x in mine if x["state"] == s),
                          Decimal(0)).quantize(Decimal("0.0001"))) for s in led_state}
    entry = {
        "stage": label,
        "trial_stage": stage_id,
        "run": run,
        "release": release,
        "commit": code["commit"],
        "evidence_class": "LIVE VERIFIED",
        "mode": manifest["mode"],
        "dataset": manifest["dataset"],
        "provider": "oxylabs",
        "provider_product": PROVIDER_PRODUCT,
        "edition": "oxylabs",
        "edition_zip_sha256": EDITION_ZIP[release],
        "edition_zip_in_repository": f"evidence/live/1.6.x/builds/WALMART_OXYLABS_SOURCE_{release}.zip",
        "store": store,
        "created_at": r["created_at"],
        "started_at": r["started_at"],
        "finished_at": r["finished_at"],
        "active_seconds": round(sum(float(s["active_s"] or 0) for s in segs), 1),
        "status": r["status"],
        "stop_code": r["stop_code"],
        "gates_failed": "; ".join(g for g, v in sorted(gates.items(), key=lambda kv: int(kv[0][1:])) if v != "PASS"),
        "segments": len(segs),
        "segment_stop_codes": dict(Counter(s["stop_code"] or "(none)" for s in segs)),
        "workers": sorted({int(s["workers"]) for s in segs if s["workers"]}),
        "collector_ledger_rows": len(usage),
        "collector_ledger_by_outcome": dict(sorted(Counter(u["outcome"] for u in usage).items())),
        "collector_ledger_by_purpose": dict(sorted(Counter(u["purpose"] for u in usage).items())),
        "usd_at_reserve_rate_0_0015": str(sum((Decimal(u["cost_usd"] or 0) for u in usage), Decimal(0))
                                          .quantize(Decimal("0.0001"))),
        "shared_ledger_reservations_by_state": dict(led_state),
        "shared_ledger_usd_by_state": led_usd,
        "page_fetches_by_purpose": dict(sorted(Counter(f["purpose"] for f in fetches).items())),
        "page_fetches_http_not_200": sum(1 for f in fetches if f["http_status"] != "200"),
        "challenges": sum(1 for f in fetches if f["challenge"] == "True"),
        "products": {
            "valid_fresh": manifest["fresh_record_count"],
            "export_rows": manifest["record_count"],
            "carried_from_earlier_runs": manifest["record_count"] - manifest["fresh_record_count"],
            "records_by_status": by_status,
        },
        "coverage_by_status": dict(sorted(Counter(c["status"] for c in cover).items())),
        "run_folder": rel,
        "exports": f"{rel}/exports",
        "delivered_files": {},
    }
    if deliver:
        dest = pub / "data" / f"{label}-{release}"
        dest.mkdir(parents=True, exist_ok=False)
        for src_name, dst_name in (("products_fresh.json", "products_fresh.json"),
                                   ("products_fresh.csv", "products_fresh.csv"),
                                   ("products.json", "products_retained.json"),
                                   ("products.csv", "products_retained.csv")):
            src = folder / "exports" / src_name
            shutil.copyfile(src, dest / dst_name)
            data = (dest / dst_name).read_bytes()
            entry["delivered_files"][f"data/{label}-{release}/{dst_name}"] = {
                "copied_from_export": src_name,
                "sha256": sha(data),
                "rows": count_rows(dest / dst_name),
            }
    return entry


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        raise SystemExit(__doc__)
    pub, old_path = Path(argv[0]), Path(argv[1])
    old = json.loads(old_path.read_text("utf-8"))
    store = next(s for s in old["stages"] if s["stage"] == "S6")["store"]
    ledger = rows(pub / "evidence/live/1.6.x/campaign/shared_ledger/reservations.csv")
    stages = [old_stage(s) for s in old["stages"]]
    for spec in argv[2:]:
        parts = spec.split("=")
        label, release, stage_id = parts[:3]
        stages.append(new_stage(pub, label, release, stage_id, parts[3:] == ["deliver"], store, ledger))
    delivered = sum(len(s["delivered_files"]) for s in stages)
    summary = {
        "about": (
            "Every live run of Walmart #3891 Pickup that this repository publishes. The nine 1.5.x stages are the "
            "owner-funded campaign of 2026-10-31 (releases 1.5.0 and 1.5.1), with the values the 1.5.2 publication "
            "gave them and repository paths. The 1.6.x stages are the user-trial campaign oxylabs-trial-20261103 "
            "(2026-11-03/04; releases 1.6.0, 1.6.1 and the final 1.6.2): each entry is computed from the run's own "
            "evidence in evidence/live/1.6.x/runs/ and from the shared trial ledger's reservations of its stage "
            "(evidence/live/1.6.x/campaign/shared_ledger/). A run's status is the collector's: 'rejected' means a "
            "release gate failed (G3, coverage, at least: no run read the whole catalogue), so nothing was published. "
            "products_retained is the run's products.json: its fresh rows plus the rows it carried from earlier runs, "
            "each with its own observation date. USD amounts are at the reserve rate (USD 0.0015 per result, a list "
            "price), not an invoice."
        ),
        "evidence_class": "LIVE VERIFIED",
        "campaigns": {
            "1.5.x": old.get("campaign"),
            "1.6.x": {
                "campaign_id": "oxylabs-trial-20261103",
                "ledger": "evidence/live/1.6.x/campaign/shared_ledger/",
                "allowance": "USD 5 in total for Walmart and Mariano's together (the trial's free credit), envelopes "
                "USD 2.25 each and USD 0.50 headroom",
            },
        },
        "files_delivered": delivered,
        "stages": stages,
    }
    out = pub / "data" / "RUN_SUMMARY.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"stages": len(stages), "files_delivered": delivered,
                      "new": {s["stage"]: {"fresh": s["products"]["valid_fresh"], "files": len(s["delivered_files"])}
                              for s in stages if s["release"].startswith("1.6")}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
