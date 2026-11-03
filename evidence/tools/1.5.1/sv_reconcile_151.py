"""Section 5 of the brief: the earlier 11 sponsored-only placements, the 30 tile-only variant siblings and the 610
variant identities of the 1.4.1 reconciliation, carried into release 1.5.1 with their latest dispositions.

Inputs (all read-only):
  - the 1.4.1 delivery's SPONSORED_AND_VARIANT_RECONCILIATION.csv (651 rows: 41 cases, 610 identities);
  - the 1.4.1 case file (SPONSORED_AND_VARIANT_CASES_1_4_1.csv) for each case's 1.3.1 stored-page reading;
  - the VM edition databases' follow-up queues, exported read-only (C:/w7/evidence/vm_followup_export_2026-10-31.txt);
  - the owner-funded campaign database walmart_live150 (read-only transaction): its follow-up queue now, the
    queue as each stage's follow-ups report printed it (S2 after S2, S4 after S4, S6 after S6, S7 after S7), the records of every campaign
    run and the follow-up product pages it read.

Outputs (C:/w7/evidence/reconciliation_151), written after the last live stage:
  - SPONSORED_AND_VARIANT_RECONCILIATION_1_5_1.csv: the 651 rows, the 1.4.1 columns unchanged, then the 1.5.1
    columns (the VM queues as read on 2026-10-31, the campaign's outcome run by run, the closure and what remains);
  - FOLLOW_UP_QUEUE_RECONCILIATION_1_5_1.csv: every queue (two VM editions, the campaign) by kind, state and last
    outcome, with how many of the 651 rows each holds;
  - sv_reconcile_151_summary.json: the counts printed at the end.
Nothing is inferred: a row the campaign did not observe keeps its 1.4.1 decision, labelled as carried.
usage: <edition venv python> -I -X utf8 sv_reconcile_151.py
"""

import collections
import csv
import json
import re
from pathlib import Path

import pgserver
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

BASE = Path(r"<repository>")
REC_141 = BASE / "deliverables" / "20261028_walmart_1.4.1_dual_provider" / "SPONSORED_AND_VARIANT_RECONCILIATION.csv"
CASES = Path(
    r"C:\w7\b\sh\walmart-shared-evidence-1.4.1\4_offline_reprocessing\final_1_4_1\sv_cases"
    r"\SPONSORED_AND_VARIANT_CASES_1_4_1.csv"
)
VM_EXPORT = Path(r"C:\w7\evidence\vm_followup_export_2026-10-31.txt")
LIVE = Path(r"C:\w7\evidence\live150")
OUT = Path(r"C:\w7\evidence\reconciliation_151")
SNAPSHOTS = {
    "S2": LIVE / "logs" / "24_S2_follow_ups.jsonl",
    "S4": LIVE / "logs" / "42_S4_follow_ups.jsonl",
    "S6": LIVE / "logs" / "78_S6_follow_ups.jsonl",
    "S7": LIVE / "logs" / "88_S7_follow_ups.jsonl",
}
LISTING_NAMES = {
    "976759_976793_8910423": "Fresh Vegetables",
    "976759_976793_9756351": "Fresh Fruits",
    "976759_976793_9756351_3521037": "Strawberries",
    "1115193_1071967": "Laundry",
    "1085666_3147628_5752434": "Shampoo",
    "976760_4661388_6244277_7158394": "Cold, cough & flu",
    "5440_202072_6432755_1636265": "Dry dog food",
}


def stage_of() -> dict[str, str]:
    runs = json.loads((LIVE / "runs.json").read_text(encoding="utf-8"))
    return {v: k for k, v in runs.items()}


def vm_queues() -> tuple[str, dict[str, dict[tuple[str, str], dict]]]:
    lines = VM_EXPORT.read_text(encoding="utf-8").splitlines()
    read_at = lines[0].strip()
    out: dict[str, dict[tuple[str, str], dict]] = {}
    db = None
    header: list[str] | None = None
    for line in lines[1:]:
        if line.startswith("== "):
            db, header = line[3:].strip(), None
            out[db] = {}
            continue
        if line == "SET" or re.fullmatch(r"\(\d+ rows?\)", line):
            continue
        cells = line.split("|")
        if header is None:
            header = cells
            continue
        assert db is not None and len(cells) == len(header), line[:200]
        row = dict(zip(header, cells))
        out[db][(row["kind"], row["item_id"])] = row
    return read_at, out


def engine():
    srv = pgserver.get_server(str(Path(r"C:\w7\live\pgdata")), cleanup_mode=None)
    url = make_url(srv.get_uri()).set(database="walmart_live150").render_as_string(hide_password=False)
    return create_engine(url.replace("postgresql://", "postgresql+psycopg://", 1))


def snapshot(path: Path) -> dict[tuple[str, str], dict]:
    d = json.loads(path.read_text(encoding="utf-8").strip().splitlines()[-1])
    return {(c["kind"], c["item_id"]): c for c in d["result"]["candidates"]}


def item_of(url: str) -> str:
    m = re.search(r"/(\d+)(?:[?#]|$)", url)
    return m.group(1) if m else ""


def vm_text(row: dict | None) -> str:
    if row is None:
        return "not in the queue"
    s = f"{row['state']}"
    if row["last_status"]:
        s += f" ({row['last_status']})"
    if row["last_run"]:
        s += f", last run {row['last_run']} at {row['last_at']}"
    s += f"; named by {row['runs_seen']} run(s), {row['pages_read']} page(s) read"
    return s


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    stages = stage_of()
    vm_read_at, vm = vm_queues()
    rows = list(csv.DictReader(open(REC_141, encoding="utf-8-sig", newline="")))
    cases = {r["case"]: r for r in csv.DictReader(open(CASES, encoding="utf-8-sig", newline=""))}
    assert len(rows) == 651, len(rows)
    snaps = {k: snapshot(p) for k, p in SNAPSHOTS.items()}
    run_ids = list(stages)
    items = sorted({r["item_id"] for r in rows})
    keys = ["wm:" + i for i in items]
    eng = engine()
    with eng.connect() as c:
        c.execute(text("set default_transaction_read_only = on"))
        c.execute(text("begin read only"))
        read_at = c.execute(text("select to_char(now() at time zone 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"')")).scalar()
        queue_now = {
            (r.kind, r.item_id): dict(r._mapping)
            for r in c.execute(text("select kind, item_id, listing, state, last_status, last_run, last_at, runs_seen,"
                                    " pages_read, first_seen_run, origin, last_reason from follow_up_queue"))
        }
        recs: dict[tuple[str, str], tuple[str, list]] = {}
        for r in c.execute(text("select run_id, upc, status, reasons from records where run_id = any(:runs) and"
                                " upc = any(:keys)"), {"runs": run_ids, "keys": keys}):
            recs[(r.run_id, r.upc[3:])] = (r.status, r.reasons or [])
        reads: dict[str, list[tuple[str, str, str, int]]] = collections.defaultdict(list)
        for r in c.execute(text("select id, run_id, url, http_status, to_char(started_at at time zone 'UTC',"
                                " 'HH24:MI:SS\"Z\"') as fetched from page_fetches where purpose = 'product_page' and"
                                " run_id = any(:runs) order by started_at"), {"runs": run_ids}):
            reads[item_of(r.url)].append((stages[r.run_id], r.id, r.fetched, r.http_status))
        queue_counts = [dict(r._mapping) for r in c.execute(text(
            "select kind, state, coalesce(last_status, '') as last_status, count(*) as n from follow_up_queue"
            " group by 1, 2, 3 order by 1, 2, 3"))]
    kinds = {"sponsored_only": "sponsored", "tile_only_variant_sibling": "variant", "variant": "variant"}
    new_cols = [
        "vm_oxylabs_queue_2026_10_31", "vm_scrapedo_queue_2026_10_31", "campaign_runs_naming_it",
        "campaign_product_page_reads", "campaign_outcome_by_stage", "campaign_record_status_by_stage",
        "campaign_queue_now", "closure_1_5_1", "evidence_class_1_5_1", "remaining_1_5_1",
    ]
    out_rows = []
    tally: collections.Counter = collections.Counter()
    for r in rows:
        kind = kinds[r["kind"]]
        item = r["item_id"]
        key = (kind, item)
        oxy = vm["walmart_oxylabs"].get(key)
        sdo = vm["walmart_scrapedo"].get(key)
        now = queue_now.get(key)
        named = []
        if now is not None:
            named.append(f"first {stages.get(now['first_seen_run'], now['first_seen_run'])}")
            named.append(f"last {stages.get(now['last_run'], now['last_run'])}")
            named.append(f"{now['runs_seen']} run(s)")
        page_reads = reads.get(item, [])
        outcome = []
        for st, snap in snaps.items():
            s = snap.get(key)
            if s is not None and s.get("last_run") and stages.get(s["last_run"]) == st:
                outcome.append(f"{st}: {s['last_status']}: {s['last_reason']}")
        if now is not None and now["last_run"]:
            last_stage = stages.get(now["last_run"], now["last_run"])
            if not any(o.startswith(last_stage + ":") for o in outcome):
                outcome.append(f"{last_stage}: {now['last_status']}: {now['last_reason']}")
        record_status = []
        carried = []
        for run_id, st in stages.items():
            got = recs.get((run_id, item))
            if got is not None:
                status, reasons = got
                if status == "historical":
                    carried.append(st)
                    continue
                record_status.append(f"{st}: {status}" + (f" ({';'.join(reasons)})" if reasons else ""))
        if carried:
            record_status.append("carried forward (historical, not fresh) by " + ", ".join(carried))
        now_text = ("not in the queue" if now is None else
                    f"{now['state']} ({now['last_status']}), last {stages.get(now['last_run'], now['last_run'])}")
        listing = r["listing"].split(" ")[0]
        lname = LISTING_NAMES.get(listing, "")
        own_tile = [o for o in outcome if ": duplicate:" in o and "its own result tile (an organic placement)" in o]
        to_sponsored = [o for o in outcome if ": duplicate:" in o and "only as a sponsored tile" in o]
        if page_reads:
            st0, pf, t, http = page_reads[0]
            decision = next((o for o in outcome if o.startswith(st0 + ":")), "")
            closure = f"closed live: decided by its own product page in {st0} ({pf}, {t}, HTTP {http})"
            if decision and ": not_attempted:" in (outcome[-1] if outcome else ""):
                closure += "; a later stage named it again and, with a follow-up limit of 0, left it pending for that run"
            ev = "LIVE VERIFIED"
            remaining = ("none for the decision; each run that publishes it reads its page again (per-run follow-up)"
                         if kind == "sponsored" else "none")
            tally["closed_live_product_page"] += 1
        elif own_tile:
            closure = "closed live: seen as its own organic result tile; recorded from that placement"
            ev = "LIVE VERIFIED"
            remaining = "none"
            tally["closed_live_own_tile"] += 1
        elif to_sponsored:
            sp = queue_now.get(("sponsored", item))
            sp_text = "not in the queue" if sp is None else f"{sp['state']} ({sp['last_status']}: {sp['last_reason']})"
            closure = (f"handed to the sponsored follow-up (the run saw it only as a sponsored tile); the sponsored "
                       f"candidate is {sp_text}")
            if sp is not None and sp["state"] == "resolved":
                ev = "LIVE VERIFIED"
                remaining = "none"
                tally["closed_live_via_sponsored"] += 1
            else:
                ev = "PENDING"
                remaining = (f"1 product page ({item}) read through the sponsored follow-up by a run that reads "
                             f"{lname or listing} with a follow-up limit of at least 1 per kind")
                tally["open_via_sponsored_not_read"] += 1
        elif now is not None:
            was = [f"{e} {r[e + '_decided_by']}: {r[e + '_outcome']}" for e in ("oxylabs", "scrapedo")
                   if r[e + "_state"] == "decided"]
            closure = (f"open in the campaign: named on {lname or listing}, its page not read "
                       f"({now['last_status']}: {now['last_reason']})")
            if was:
                closure += "; 1.4.1's decision is carried as historical: " + " / ".join(was)
                ev = "PENDING (1.4.1 decision carried)"
                tally["open_named_not_read_decided_1_4_1"] += 1
            else:
                ev = "PENDING"
                tally["open_named_not_read"] += 1
            remaining = (f"1 product page ({item}) read by a run that reads {lname or listing} with a follow-up "
                         f"limit of at least 1 per kind")
        else:
            decided = [x for x in (r["oxylabs_state"], r["scrapedo_state"]) if x == "decided"]
            if decided:
                closure = "carried: decided in 1.4.1 (2026-10-28); not observed by the campaign of 2026-10-31"
                ev = "HISTORICAL (carried)"
                remaining = "none for 1.4.1's decision; not re-observed on 2026-10-31"
                tally["carried_decided_1_4_1"] += 1
            else:
                closure = f"open: not observed by the campaign of 2026-10-31 (listing {lname or listing} not read)"
                ev = "PENDING"
                remaining = (f"a run that reads listing {listing} and names it, then 1 product page read with a "
                             f"follow-up limit of at least 1")
                tally["open_not_observed"] += 1
        out = dict(r)
        out.update({
            "vm_oxylabs_queue_2026_10_31": vm_text(oxy),
            "vm_scrapedo_queue_2026_10_31": vm_text(sdo),
            "campaign_runs_naming_it": ", ".join(named),
            "campaign_product_page_reads": "; ".join(f"{a} {b} {c} HTTP {d}" for a, b, c, d in page_reads),
            "campaign_outcome_by_stage": " | ".join(outcome),
            "campaign_record_status_by_stage": "; ".join(record_status),
            "campaign_queue_now": now_text,
            "closure_1_5_1": closure,
            "evidence_class_1_5_1": ev,
            "remaining_1_5_1": remaining,
        })
        out_rows.append(out)
        tally[f"{r['level']}:{ev}"] += 1
    path = OUT / "SPONSORED_AND_VARIANT_RECONCILIATION_1_5_1.csv"
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) + new_cols, lineterminator="\r\n")
        w.writeheader()
        w.writerows(out_rows)
    # The queues: two VM editions as read, the campaign now; how many of the 651 rows each holds by state.
    in_rows = {(kinds[r["kind"]], r["item_id"]) for r in rows}
    qrows = []
    for db, q in vm.items():
        cnt = collections.Counter((k[0], v["state"], v["last_status"]) for k, v in q.items())
        held = collections.Counter((k[0], v["state"], v["last_status"]) for k, v in q.items() if k in in_rows)
        for (kind, state, status), n in sorted(cnt.items()):
            qrows.append({"queue": f"VM {db}", "read_at": vm_read_at, "kind": kind, "state": state,
                          "last_outcome": status or "(none recorded)", "rows": n,
                          "of_which_1_4_1_reconciliation_rows": held[(kind, state, status)]})
    held_now = collections.Counter((k[0], v["state"], v["last_status"]) for k, v in queue_now.items() if k in in_rows)
    for q in queue_counts:
        qrows.append({"queue": "campaign walmart_live150", "read_at": read_at, "kind": q["kind"], "state": q["state"],
                      "last_outcome": q["last_status"] or "(none recorded)", "rows": q["n"],
                      "of_which_1_4_1_reconciliation_rows": held_now[(q["kind"], q["state"], q["last_status"])]})
    qpath = OUT / "FOLLOW_UP_QUEUE_RECONCILIATION_1_5_1.csv"
    with open(qpath, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(qrows[0].keys()), lineterminator="\r\n")
        w.writeheader()
        w.writerows(qrows)
    summary = {"read_at_campaign": read_at, "read_at_vm": vm_read_at, "rows": len(out_rows), "tally": dict(tally),
               "outputs": [str(path), str(qpath)]}
    (OUT / "sv_reconcile_151_summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
