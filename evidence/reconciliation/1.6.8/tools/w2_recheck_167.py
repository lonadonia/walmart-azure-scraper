"""W2 recheck (release 1.6.7 tool, offline; no request): every UPC and size S6's 706 delivered rows still lacked in
L8's export (W2_FIELD_CORRECTIONS_1_6_3.csv: 52 UPCs, 14 sizes), checked again against

  * every read of a product's own page the store's campaign database holds (``detail_observations``: all runs, all
    origins, including captures imported from earlier deliveries), read-only;
  * the store's follow-up queue (``follow_up_queue``: state, last outcome, reason, run), read-only;
  * L12's export (the latest live run, release 1.6.6): its field dispositions (public) and, for a blank value,
    the record's own provenance (``historical.recovery_withheld``), read-only.

Each value gets its state as of L12 and the class of what is known about it:
  filled_in_l12_export      L12's export states the value; the source is named (its disposition, run, page)
  recoverable_by_1_6_7      a saved read of the item's own page states the UPC; 1.6.6 withheld it only because the
                            same read's statements about size conflict (1.6.7 decides the two separately)
  withheld_by_check         a saved read states the value; a check of the record withheld it (reason given)
  absent_at_source          the item's own page was read and states no such value
  conflicting               the item's own page states sizes that conflict (the statements given)
  wrong_identity            the page read was of another item
  failed / blocked          a read was attempted and failed or was refused (the queue's outcome)
  never_attempted           no read of the item's own page exists in any run; the queue's state says where it is

Nothing is guessed: a value is only ever what a named read of the item's own page states.

usage: python -I w2_recheck_167.py PUBLICATION_ROOT OUT_DIR
(run with the campaign's own environment: C:/w9/live/ed/walmart-oxylabs-1.6.0/.venv/Scripts/python.exe)
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

os.environ["PSYCOPG_IMPL"] = "python"
os.environ["PATH"] = (
    "C:/w9/live/ed/walmart-oxylabs-1.6.0/.venv/Lib/site-packages/pgserver/pginstall/bin"
    + os.pathsep
    + os.environ.get("PATH", "")
)
sys.path.insert(0, "C:/w9/live")
import live160_run as h  # noqa: E402
from sqlalchemy import bindparam, create_engine, text  # noqa: E402

L12 = "01M6MC7YE4PBXV88G3PJ5ENW4B"
STORE_KEY = "walmart-3891-pickup"
FIELD = {"upc": "upc", "size (weight)": "weight"}
COLUMNS = [
    "item_id",
    "field",
    "s6_row",
    "sub_category",
    "product_title",
    "outcome_1_6_3",
    "reason_1_6_3",
    "l12_key_present",
    "l12_value",
    "l12_disposition",
    "l12_reason",
    "l12_source_run",
    "l12_page_fetch_id",
    "l12_body_sha256",
    "l12_conflicts",
    "l12_recovery_withheld",
    "reads_of_own_page",
    "reads",
    "saved_read_value",
    "queue",
    "class_1_6_7",
    "explanation",
    "evidence_class",
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(argv: list[str]) -> int:
    root, out = Path(argv[1]), Path(argv[2])
    out.mkdir(parents=True, exist_ok=True)
    w2_path = root / "evidence/reconciliation/1.6.3/w2/W2_FIELD_CORRECTIONS_1_6_3.csv"
    w2 = [r for r in csv.DictReader(w2_path.open(encoding="utf-8", newline="")) if not r["value_1_6_3"]]
    counts_in = Counter(r["field"] for r in w2)
    assert counts_in == {"upc": 52, "size (weight)": 14}, counts_in
    ids = sorted({r["item_id"] for r in w2})
    keys = {f"wm:{i}" for i in ids}
    runs_dir = root / "evidence/live/1.6.x/runs"
    labels = {p.name.split("_", 1)[1]: p.name.split("_", 1)[0] for p in runs_dir.iterdir() if "_" in p.name}
    disp_path = runs_dir / f"L12_{L12}" / f"field_dispositions_{L12}.csv"
    l12: dict[str, dict[str, str]] = {}
    with disp_path.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r["key"] in keys:
                l12[r["key"]] = r
    inputs = {
        str(w2_path.relative_to(root)).replace("\\", "/"): sha(w2_path),
        str(disp_path.relative_to(root)).replace("\\", "/"): sha(disp_path),
    }

    engine = create_engine(h.db_url(), connect_args={"options": "-c default_transaction_read_only=on"})
    with engine.connect() as c:
        assert c.execute(text("show default_transaction_read_only")).scalar() == "on"
        store_id = c.execute(text("select id from stores where key = :k"), {"k": STORE_KEY}).scalar_one()
        reads = c.execute(
            text(
                "select item_id, observed_at, run_id, page_fetch_id, source_revision, origin, body_sha256, status,"
                " upc, upc_path, size_statements from detail_observations"
                " where store_id = :s and item_id in :ids order by item_id, observed_at, id"
            ).bindparams(bindparam("ids", expanding=True)),
            {"s": store_id, "ids": ids},
        ).all()
        queue = c.execute(
            text(
                "select item_id, kind, lineage, state, last_status, last_reason, last_run, last_at, pages_read,"
                " runs_seen from follow_up_queue where store_id = :s and item_id in :ids order by item_id, kind"
            ).bindparams(bindparam("ids", expanding=True)),
            {"s": store_id, "ids": ids},
        ).all()
        held = c.execute(
            text(
                "select upc, status, record->>'upc', record->>'weight',"
                " provenance->'historical'->'recovery_withheld' from records"
                " where run_id = :r and upc in :keys"
            ).bindparams(bindparam("keys", expanding=True)),
            {"r": L12, "keys": sorted(keys)},
        ).all()
        db_name = c.execute(text("select current_database()")).scalar()
        total_reads = c.execute(
            text("select count(*) from detail_observations where store_id = :s"), {"s": store_id}
        ).scalar()

    by_item: dict[str, list[dict[str, Any]]] = {}
    for r in reads:
        by_item.setdefault(r.item_id, []).append(
            {
                "observed_at": r.observed_at.isoformat(),
                "run": r.run_id,
                "label": labels.get(r.run_id, "earlier delivery" if r.origin == "imported" else ""),
                "revision": r.source_revision,
                "origin": r.origin,
                "status": r.status,
                "upc": r.upc or "",
                "upc_path": r.upc_path or "",
                "size_statements": [
                    {"path": s.get("path"), "value": s.get("value"), "measures": s.get("measures")}
                    for s in (r.size_statements or [])
                ],
                "page_fetch_id": r.page_fetch_id or "",
                "body_sha256": r.body_sha256,
            }
        )
    q_by_item: dict[str, list[dict[str, Any]]] = {}
    for q in queue:
        q_by_item.setdefault(q.item_id, []).append(
            {
                "kind": q.kind,
                "lineage": q.lineage,
                "state": q.state,
                "last_status": q.last_status,
                "last_reason": (q.last_reason or "")[:200],
                "last_run": q.last_run,
                "last_label": labels.get(q.last_run or "", ""),
                "last_at": q.last_at.isoformat() if q.last_at else "",
                "pages_read": q.pages_read,
                "runs_seen": q.runs_seen,
            }
        )
    withheld = {k: w for k, _status, _u, _w, w in held}

    rows: list[dict[str, Any]] = []
    for r in w2:
        item, field = r["item_id"], FIELD[r["field"]]
        key = f"wm:{item}"
        d = l12.get(key, {})
        value = d.get(field, "")
        disp = d.get(f"{field}_disposition", "")
        item_reads = by_item.get(item, [])
        q = q_by_item.get(item, [])
        detail_q = [x for x in q if x["kind"] == "detail"]
        held_reason = withheld.get(key)
        saved = ""
        if field == "upc":
            saved = next((x["upc"] for x in reversed(item_reads) if x["status"] == "extracted" and x["upc"]), "")
        if value:
            cls = "filled_in_l12_export"
            why = f"L12's export states it ({disp}" + (
                f", read by run {d.get(f'{field}_source_run')})" if d.get(f"{field}_source_run") else ")"
            )
        elif not d:
            cls = "not_in_l12_export"
            why = "the item is not among L12's exported rows"
        elif field == "upc" and saved:
            reason = (held_reason or {}).get("reason", "") if isinstance(held_reason, dict) else ""
            if "size conflict" in reason:
                cls = "recoverable_by_1_6_7"
                why = (
                    f"a saved read states UPC {saved}; 1.6.6 withheld it because the same read's statements about "
                    "size conflict; 1.6.7 fills the UPC and leaves the size blank with that reason (no request)"
                )
            else:
                cls = "withheld_by_check"
                why = f"a saved read states UPC {saved}; withheld: {reason or disp}"
        elif (
            field == "weight"
            and isinstance(held_reason, dict)
            and "size conflict" in str(held_reason.get("reason", ""))
        ):
            cls = "conflicting"
            why = (
                f"{len(item_reads)} saved read(s) of the item's own page; their statements about size conflict "
                f"(1.6.6 withheld the read: {held_reason.get('reason')}); the size stays blank with that reason"
            )
        elif disp == "absent_in_source" or (item_reads and all(x["status"] == "absent_in_source" for x in item_reads)):
            cls = "absent_at_source"
            why = d.get(f"{field}_reason") or "the item's own page was read and states no such value"
        elif disp == "unresolved_conflict":
            cls = "conflicting"
            why = d.get(f"{field}_reason") or "the item's own page states sizes that conflict"
        elif disp == "identity_mismatch":
            cls = "wrong_identity"
            why = d.get(f"{field}_reason", "")
        elif disp in ("request_failed", "parse_failure"):
            cls = "failed"
            why = d.get(f"{field}_reason", "")
        elif disp == "blocked":
            cls = "blocked"
            why = d.get(f"{field}_reason", "")
        elif not item_reads:
            cls = "never_attempted"
            state = "; ".join(
                f"{x['kind']} queue {x['state']}"
                + (f", last {x['last_status']} in {x['last_label'] or x['last_run']}" if x["last_status"] else "")
                for x in q
            )
            why = (
                "no read of the item's own page exists in any run of the campaign database"
                + (f" ({state})" if state else " (not on the store's follow-up queue)")
                + f"; L12: {disp}: {d.get(f'{field}_reason', '')}"
            )
        else:
            cls = "unresolved_other"
            why = f"L12: {disp}: {d.get(f'{field}_reason', '')}; {len(item_reads)} saved read(s)"
        rows.append(
            {
                "item_id": item,
                "field": r["field"],
                "s6_row": r["s6_row"],
                "sub_category": r["sub_category"],
                "product_title": r["product_title"],
                "outcome_1_6_3": r["outcome_1_6_3"],
                "reason_1_6_3": r["reason_1_6_3"],
                "l12_key_present": "yes" if d else "no",
                "l12_value": value,
                "l12_disposition": disp,
                "l12_reason": d.get(f"{field}_reason", ""),
                "l12_source_run": d.get(f"{field}_source_run", ""),
                "l12_page_fetch_id": d.get(f"{field}_page_fetch_id", ""),
                "l12_body_sha256": d.get(f"{field}_body_sha256", ""),
                "l12_conflicts": d.get(f"{field}_conflicts", ""),
                "l12_recovery_withheld": json.dumps(held_reason, sort_keys=True) if held_reason else "",
                "reads_of_own_page": len(item_reads),
                "reads": json.dumps(item_reads, sort_keys=True) if item_reads else "",
                "saved_read_value": saved,
                "queue": json.dumps(detail_q or q, sort_keys=True) if q else "",
                "class_1_6_7": cls,
                "explanation": why,
                "evidence_class": "LIVE reads (campaign database), checked again offline; no request",
            }
        )

    classes = {f: dict(Counter(x["class_1_6_7"] for x in rows if x["field"] == f)) for f in FIELD}
    never_upc = [x for x in rows if x["field"] == "upc" and x["class_1_6_7"] == "never_attempted"]
    summary = {
        "about": "W2 recheck, release 1.6.7 tool, offline: S6's blank UPCs and sizes against every saved read",
        "inputs_sha256": inputs,
        "database": {
            "name": db_name,
            "access": "read-only session (default_transaction_read_only=on)",
            "reads_of_own_pages_of_this_store": total_reads,
        },
        "values": dict(counts_in),
        "classes": classes,
        "never_attempted_upc_items": sorted(x["item_id"] for x in never_upc),
        "never_attempted_upc_count": len(never_upc),
        "recoverable_by_1_6_7": sorted(
            (x["item_id"], x["saved_read_value"]) for x in rows if x["class_1_6_7"] == "recoverable_by_1_6_7"
        ),
    }
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    (out / "W2_RECHECK_1_6_7.csv").write_bytes(buf.getvalue().encode("utf-8"))
    (out / "W2_RECHECK_SUMMARY_1_6_7.json").write_bytes((json.dumps(summary, indent=1) + "\n").encode("utf-8"))
    print(json.dumps({k: summary[k] for k in ("database", "values", "classes", "never_attempted_upc_count")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
