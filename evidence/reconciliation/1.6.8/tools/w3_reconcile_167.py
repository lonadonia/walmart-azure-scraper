"""W3 at row level (release 1.6.7, offline; no request): the 275 queued sponsored and variant products of
EXACT_LIVE_READ_QUEUE_1_5_2.csv, each with its decision, the class of that decision, and the observations the
decision rests on (run, page fetch, stored page and its SHA-256).

Inputs, all from the 1.6.6 publication (read-only):
  evidence/reconciliation/1.6.1/w3/W3_DECISIONS_1_6_1.csv     the 275 decisions (48 included, 224 excluded, 3
                                                               duplicates)
  evidence/live/1.6.x/runs/<run>/coverage/follow_up_outcomes_*.csv   every follow-up outcome of the 1.6.x runs
  evidence/live/1.6.x/runs/<run>/exports/record_map.json      each run's records with their result pages
  evidence/live/1.6.x/runs/<run>/PAGE_LINEAGE.csv             each page fetch's stored original and its hashes

The classes (the client's review of 1.6.6 asked for these distinctions):
  included                                   its own page shows the store's Pickup offer under the category
  excluded_local_eligibility_not_proven      its own page shows no eligible local offer or assortment
  excluded_category_path_missing             its own page states no category path (categoryPathId -1)
  excluded_category_path_broader             its own page files it only at an ancestor of the listing's
                                             category: neither inside nor outside it is proven
  excluded_alternative_category              its own page files it under another category: positively
                                             identified (the deepest common ancestor and the other branch given)
  duplicate                                  the same identity was decided from another observation, linked
  failed / blocked / unresolved              none of the 275 (each was read, or decided from another observation)

usage: python -I w3_reconcile_167.py PUBLICATION_ROOT OUT_DIR
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

RUNS = {
    "L2": "L2_01M6H72J86K5TF7A1874N7BJ2R",
    "L3": "L3_01M6HA74X4QYMW45SVD62JQDSQ",
    "L2b": "L2b_01M6HAXEP6495EGWT91JQS09SS",
}
COLUMNS = [
    "item_id",
    "queue_kind",
    "listing_id",
    "listing_name",
    "queue_line",
    "decision_1_6_1",
    "outcome_class",
    "listing_path",
    "category_path_on_its_page",
    "common_ancestor",
    "other_branch",
    "reason",
    "decided_by_run",
    "run_label",
    "page_fetch_id",
    "page_artifact_sha256",
    "http_status",
    "store_context",
    "record_status",
    "record_reasons",
    "upc",
    "linked_observations",
    "all_outcomes_this_delivery",
    "client_case",
    "evidence_class",
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def path_of(evidence: str) -> list[str] | None:
    """The category path a product page states (``categoryPathId 0:5440:202072``) as its ids after the root;
    None when the page states none (``-1`` or nothing)."""
    text = evidence.strip()
    if not text.startswith("categoryPathId "):
        return None
    ids = text.removeprefix("categoryPathId ").strip().split(":")
    if ids == ["-1"] or not ids or ids == [""]:
        return None
    return ids[1:] if ids[0] == "0" else ids


def classify(row: dict[str, str]) -> tuple[str, str, str, str]:
    """(class, listing path, common ancestor, other branch) of one decision."""
    listing = row["listing_id"].split("_")
    status = row["status"]
    if status == "included":
        return "included", "_".join(listing), "", ""
    if status == "duplicate":
        return "duplicate", "_".join(listing), "", ""
    assert status == "excluded", row
    if row["record_status"] == "excluded":
        assert row["reason"].startswith("the product page shows no eligible local offer"), row
        return "excluded_local_eligibility_not_proven", "_".join(listing), "", ""
    assert row["reason"].startswith("required category not established"), row
    path = path_of(row["category_evidence"])
    if path is None:
        return "excluded_category_path_missing", "_".join(listing), "", ""
    common = 0
    for a, b in zip(path, listing, strict=False):
        if a != b:
            break
        common += 1
    if common == len(path) and len(path) < len(listing):
        return "excluded_category_path_broader", "_".join(listing), "_".join(path), ""
    # The page names a branch the listing is not on: the listing is never a prefix of it (that is included).
    assert not (common == len(listing)), (row["item_id"], path, listing)
    return "excluded_alternative_category", "_".join(listing), "_".join(path[:common]), "_".join(path[common:])


def main(argv: list[str]) -> int:
    root, out = Path(argv[1]), Path(argv[2])
    out.mkdir(parents=True, exist_ok=True)
    decisions_path = root / "evidence/reconciliation/1.6.1/w3/W3_DECISIONS_1_6_1.csv"
    decisions = list(csv.DictReader(decisions_path.open(encoding="utf-8", newline="")))
    assert len(decisions) == 275, len(decisions)
    runs_dir = root / "evidence/live/1.6.x/runs"
    inputs: dict[str, str] = {str(decisions_path.relative_to(root)).replace("\\", "/"): sha(decisions_path)}

    # Every follow-up outcome of the three runs that decided the queue, and every record they made.
    outcomes: dict[str, list[dict[str, str]]] = defaultdict(list)
    lineage: dict[str, dict[str, str]] = {}
    records: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for label, run in RUNS.items():
        folder = runs_dir / run
        for f in sorted((folder / "coverage").glob("follow_up_outcomes_*.csv")):
            inputs[str(f.relative_to(root)).replace("\\", "/")] = sha(f)
            for r in csv.DictReader(f.open(encoding="utf-8", newline="")):
                outcomes[r["item_id"]].append({**r, "run_label": label})
        lin = folder / "PAGE_LINEAGE.csv"
        inputs[str(lin.relative_to(root)).replace("\\", "/")] = sha(lin)
        for r in csv.DictReader(lin.open(encoding="utf-8", newline="")):
            lineage[r["page_fetch_id"]] = {**r, "run_label": label}
        rm = folder / "exports" / "record_map.json"
        inputs[str(rm.relative_to(root)).replace("\\", "/")] = sha(rm)
        for r in json.loads(rm.read_text(encoding="utf-8"))["rows"]:
            records[str(r.get("item_id"))].append({**r, "run_label": label})

    def page_ref(fetch_id: str) -> dict[str, str]:
        lin = lineage.get(fetch_id, {})
        return {
            "page_fetch_id": fetch_id,
            "run": lin.get("run_label", ""),
            "purpose": lin.get("purpose", ""),
            "http_status": lin.get("http_status", ""),
            "fetched_at": lin.get("started_at", ""),
            "stored_original_body_sha256": lin.get("private_original_body_sha256", ""),
            "public_copy": lin.get("public_copy", ""),
        }

    rows: list[dict[str, Any]] = []
    for d in decisions:
        cls, listing_path, common, other = classify(d)
        linked: list[dict[str, Any]] = []
        if cls == "duplicate":
            # The identity's own decisions: its product-page reads in these runs, then the organic tiles it
            # was recorded from (a record of the run, with its stored result page and that page's hash).
            for o in outcomes[d["item_id"]]:
                if o["page_fetch_id"]:
                    linked.append(
                        {
                            "observation": f"{o['run_label']} {o['kind']} follow-up: {o['status']}",
                            "reason": o["reason"],
                            **page_ref(o["page_fetch_id"]),
                        }
                    )
            for r in records[d["item_id"]]:
                page = r.get("page") or {}
                if r.get("observation_kind") == "fresh":
                    linked.append(
                        {
                            "observation": f"{r['run_label']} record {r.get('key')} ({r.get('status')}), from "
                            f"its own result tile on page {r.get('result_page')} of {r.get('listing')}",
                            "observed_at": r.get("observed_at"),
                            "page_fetch_id": page.get("page_fetch_id"),
                            "stored_page": page.get("stored_page"),
                            "stored_page_sha256": page.get("stored_page_sha256"),
                            "store_check": (page.get("store_check") or {}).get("result"),
                        }
                    )
            assert linked, d["item_id"]
        rows.append(
            {
                "item_id": d["item_id"],
                "queue_kind": d["queue_kind"],
                "listing_id": d["listing_id"],
                "listing_name": d["listing_name"],
                "queue_line": d["queue_line"],
                "decision_1_6_1": d["status"],
                "outcome_class": cls,
                "listing_path": listing_path,
                "category_path_on_its_page": d["category_evidence"].removeprefix("categoryPathId ").strip(),
                "common_ancestor": common,
                "other_branch": other,
                "reason": d["reason"],
                "decided_by_run": d["decided_by_run"],
                "run_label": d["run_label"],
                "page_fetch_id": d["page_fetch_id"],
                "page_artifact_sha256": d["page_artifact_sha256"],
                "http_status": d["http_status"],
                "store_context": d["store_context"],
                "record_status": d["record_status"],
                "record_reasons": d["record_reasons"],
                "upc": d["upc"],
                "linked_observations": json.dumps(linked, sort_keys=True) if linked else "",
                "all_outcomes_this_delivery": d["all_outcomes_this_delivery"],
                "client_case": d["client_case"],
                "evidence_class": d["evidence_class"],
            }
        )

    classes = Counter(r["outcome_class"] for r in rows)
    by_listing: dict[str, Counter[str]] = defaultdict(Counter)
    for r in rows:
        by_listing[f"{r['listing_name']} ({r['listing_id']})"][r["outcome_class"]] += 1
    excluded = sum(v for k, v in classes.items() if k.startswith("excluded"))
    category = sum(v for k, v in classes.items() if k.startswith("excluded_") and "eligibility" not in k)
    summary = {
        "about": "W3 at row level, release 1.6.7 tool, offline: the 275 queued sponsored and variant products",
        "evidence_class": "LIVE VERIFIED (the 1.6.0 and 1.6.1 reads of L2, L3 and L2b), reclassified offline",
        "decisions": dict(Counter(r["decision_1_6_1"] for r in rows)),
        "classes": dict(sorted(classes.items())),
        "excluded": excluded,
        "excluded_without_required_category_proof": category,
        "of_which_missing_or_broader_path": classes["excluded_category_path_missing"]
        + classes["excluded_category_path_broader"],
        "of_which_alternative_category_identified": classes["excluded_alternative_category"],
        "excluded_without_local_eligibility_proof": classes["excluded_local_eligibility_not_proven"],
        "failed": 0,
        "blocked": 0,
        "unresolved": 0,
        "by_listing": {k: dict(sorted(v.items())) for k, v in sorted(by_listing.items())},
        "inputs_sha256": dict(sorted(inputs.items())),
    }
    assert summary["decisions"] == {"included": 48, "excluded": 224, "duplicate": 3}, summary["decisions"]
    assert category == 169 and classes["excluded_local_eligibility_not_proven"] == 55, summary
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    (out / "W3_ROW_LEVEL_1_6_7.csv").write_bytes(buf.getvalue().encode("utf-8"))
    (out / "W3_ROW_LEVEL_SUMMARY_1_6_7.json").write_bytes(
        (json.dumps(summary, indent=1, sort_keys=False) + "\n").encode("utf-8")
    )
    print(json.dumps({k: summary[k] for k in list(summary)[:12]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
