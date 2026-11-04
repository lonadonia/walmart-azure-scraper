"""W3: the decision on each of the 275 distinct products of EXACT_LIVE_READ_QUEUE_1_5_2.csv, from the follow-up
outcomes of this delivery's runs that read them (1.6.0 and 1.6.1) (coverage-report follow_up_outcomes_<run>.csv), with the page each
decision rests on (page fetch, time, HTTP status, the captured body's SHA-256 from the campaign database), and the
client's original 41 cases (11 sponsored-only, 30 tile-only siblings) traced from the 1.5.2 reconciliation.

A product no run of this delivery read keeps its exact 1.5.2 state with the reason; nothing is inferred.

usage: python -I w3_decisions.py OUT_DIR RUN_LABEL=COVERAGE_DIR [RUN_LABEL=COVERAGE_DIR ...]
"""

import csv
import json
import os
import sys
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

REC = Path("C:/w8/repo/evidence/reconciliation/1.5.2/sponsored_and_variant_reconciliation")
QUEUE = REC / "EXACT_LIVE_READ_QUEUE_1_5_2.csv"
RECON = REC / "SPONSORED_AND_VARIANT_RECONCILIATION_1_5_2.csv"
DECIDED = {"included", "excluded", "duplicate"}

out_dir = Path(sys.argv[1])
runs: list[tuple[str, Path]] = []
for arg in sys.argv[2:]:
    label, folder = arg.split("=", 1)
    runs.append((label, Path(folder)))

queue = list(csv.DictReader(QUEUE.open(encoding="utf-8-sig")))
recon = list(csv.DictReader(RECON.open(encoding="utf-8-sig")))
by_item_152 = {}
for r in recon:
    by_item_152.setdefault(r["item_id"], r)

# Every follow-up outcome of this delivery's runs, by item (the last outcome of the last run wins; all are listed).
outcomes: dict[str, list[dict]] = {}
run_ids: dict[str, str] = {}
for label, folder in runs:
    [f] = list(folder.glob("follow_up_outcomes_*.csv"))
    run_ids[label] = f.stem.rsplit("_", 1)[-1]
    for row in csv.DictReader(f.open(encoding="utf-8-sig")):
        outcomes.setdefault(row["item_id"], []).append({**row, "run_label": label, "run_id": run_ids[label]})

fetch_ids = {o["page_fetch_id"] for rows in outcomes.values() for o in rows if o.get("page_fetch_id")}
pages: dict[str, dict] = {}
if fetch_ids:
    eng = create_engine(h.db_url())
    with eng.connect() as c:
        c.execute(text("SET TRANSACTION READ ONLY"))
        cols = {r[0] for r in c.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name='captured_responses'"))}
        sha_col = "sha256" if "sha256" in cols else ("body_sha256" if "body_sha256" in cols else None)
        for pf in c.execute(
            text("SELECT id, http_status, started_at, dom_artifact_id FROM page_fetches WHERE id = ANY(:ids)"),
            {"ids": list(fetch_ids)},
        ):
            pages[pf[0]] = {"http_status": pf[1], "started_at": str(pf[2]), "artifact": pf[3]}
        arts = {p["artifact"] for p in pages.values() if p["artifact"]}
        if arts:
            acols = {r[0] for r in c.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name='artifacts'"))}
            hcol = next((x for x in ("sha256", "content_sha256", "body_sha256") if x in acols), None)
            if hcol:
                for aid, sha in c.execute(
                    text(f"SELECT id, {hcol} FROM artifacts WHERE id = ANY(:ids)"), {"ids": list(arts)}
                ):
                    for p in pages.values():
                        if p["artifact"] == aid:
                            p["artifact_sha256"] = sha

FIELDS = [
    "item_id", "queue_kind", "listing_id", "listing_name", "queue_line", "url", "state_1_5_2", "decision_this_delivery",
    "status", "reason", "decided_by_run", "run_label", "page_fetch_id", "requested_at", "http_status",
    "page_artifact_sha256", "store_context", "category_evidence", "record_status", "record_reasons", "upc",
    "all_outcomes_this_delivery", "client_case", "evidence_class", "remaining_limitation",
]
rows_out = []


def RELEASE_OF(o: dict) -> str:  # noqa: N802
    return "1.6.0" if o.get("run_label") in ("L1", "L2") else "1.6.1"


for n, q in enumerate(queue, start=2):
    item = q["item_id"]
    old = by_item_152.get(item, {})
    seen = outcomes.get(item, [])
    final = next((o for o in reversed(seen) if o["status"] in DECIDED), seen[-1] if seen else None)
    if final is None:
        decision, cls = "not read by a run of this delivery", "NOT TESTED (1.6.0, 1.6.1)"
        limitation = "its own page was not requested by this delivery: the 1.5.2 state stands"
    elif final["status"] in DECIDED:
        decision, cls, limitation = final["status"], f"LIVE VERIFIED ({RELEASE_OF(final)})", ""
    else:
        decision, cls = f"unresolved: {final['status']}", f"LIVE ATTEMPTED ({RELEASE_OF(final)}), UNRESOLVED"
        limitation = final["reason"]
    page = pages.get((final or {}).get("page_fetch_id") or "", {})
    rows_out.append(
        {
            "item_id": item,
            "queue_kind": q["kind"],
            "listing_id": q["listing"].split(" ", 1)[0],
            "listing_name": (final or {}).get("listing_name") or q["listing"].partition(" ")[2].strip("()"),
            "queue_line": n,
            "url": (final or {}).get("url") or q["identity"],
            "state_1_5_2": old.get("outcome_1_5_2", "") + (f" ({old.get('evidence_class_1_5_2')})" if old else ""),
            "decision_this_delivery": decision,
            "status": (final or {}).get("status", ""),
            "reason": (final or {}).get("reason", ""),
            "decided_by_run": (final or {}).get("run_id", ""),
            "run_label": (final or {}).get("run_label", ""),
            "page_fetch_id": (final or {}).get("page_fetch_id", ""),
            "requested_at": (final or {}).get("requested_at", ""),
            "http_status": page.get("http_status", ""),
            "page_artifact_sha256": page.get("artifact_sha256", ""),
            "store_context": (final or {}).get("store_context", ""),
            "category_evidence": (final or {}).get("category_evidence", ""),
            "record_status": (final or {}).get("record_status", ""),
            "record_reasons": (final or {}).get("reasons", ""),
            "upc": (final or {}).get("upc", ""),
            "all_outcomes_this_delivery": "; ".join(f"{o['run_label']}: {o['status']}" for o in seen),
            "client_case": "",
            "evidence_class": cls,
            "remaining_limitation": limitation,
        }
    )
by_id = {r["item_id"]: r for r in rows_out}
cases = []
for r in recon:
    if r["level"] != "case":
        continue
    now = by_id.get(r["item_id"])
    cases.append(
        {
            "case": r["case"],
            "kind": r["kind"],
            "item_id": r["item_id"],
            "identity": r["identity"],
            "listing": r["listing"],
            "state_1_5_2": f"{r['outcome_1_5_2']} ({r['evidence_class_1_5_2']}); 1.5.1: {r['closure_1_5_1']}",
            "decision_this_delivery": now["decision_this_delivery"] if now else "not in the 1.5.2 live-read queue (closed before)",
            "decided_by_run": now["decided_by_run"] if now else "",
            "reason": now["reason"] if now else "",
            "evidence_class": now["evidence_class"] if now else r["evidence_class_1_5_2"],
        }
    )
    if now:
        now["client_case"] = r["case"]
out_dir.mkdir(parents=True, exist_ok=True)
with (out_dir / "W3_DECISIONS_1_6_1.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows_out)
with (out_dir / "W3_CLIENT_CASES_1_6_1.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(cases[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(cases)
summary = {
    "queue_products": len(rows_out),
    "runs": run_ids,
    "by_decision": dict(Counter(r["decision_this_delivery"] for r in rows_out)),
    "by_listing_and_decision": dict(Counter(f"{r['listing_id']} | {r['decision_this_delivery']}" for r in rows_out)),
    "by_record_status": dict(Counter(r["record_status"] for r in rows_out if r["record_status"])),
    "client_cases": dict(Counter(f"{c['kind']} | {c['decision_this_delivery']}" for c in cases)),
    "note": "Aggregates are computed from W3_DECISIONS_1_6_1.csv and W3_CLIENT_CASES_1_6_1.csv rows.",
}
(out_dir / "W3_SUMMARY_1_6_1.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=1))
