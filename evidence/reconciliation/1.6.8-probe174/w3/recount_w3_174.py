"""The 275 sponsored and variant decisions, recounted from the published rows with missing evidence as unresolved
(the probe 1.7.4 revision; offline, standard library, no request).

Rule: a product is excluded only on affirmative source evidence. Here that evidence is the item's own page placing
it in another category, identified (outcome_class excluded_alternative_category, with other_branch named). A page
that gives no category path (categoryPathId -1) or does not prove local eligibility (LOCATION_UNATTESTED,
ASSORTMENT_UNRESOLVED) is missing evidence, so the product is unresolved. A marketplace offer shown with them does
not show the product absent from the store. Included and duplicate rows are unchanged.

Input: ../../1.6.8/w3/W3_ROW_LEVEL_1_6_7.csv, as published under review-1.6.8-20261106 (unchanged; its SHA-256 is
checked). Outputs, beside this script: W3_275_RECOUNT.csv and W3_275_RECOUNT_SUMMARY.json.

usage (from a clone):  python3 -I evidence/reconciliation/1.6.8-probe174/w3/recount_w3_174.py
                       checks the two outputs against a fresh recount and ends with PASS or FAIL
                       python3 -I evidence/reconciliation/1.6.8-probe174/w3/recount_w3_174.py --write
                       writes them
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent.parent / "1.6.8" / "w3" / "W3_ROW_LEVEL_1_6_7.csv"
SOURCE_SHA256 = "340b49674fe7dbc27028d70f4e2a6ca9c1cfa4bddfc43bdd7f46bd215427a73c"
OUT_CSV = HERE / "W3_275_RECOUNT.csv"
OUT_JSON = HERE / "W3_275_RECOUNT_SUMMARY.json"

RECOUNT = {
    "included": ("included", "included by its own live read (the run in decided_by_run and run_label)"),
    "duplicate": ("duplicate", "the same product as an earlier observation, linked to it"),
    "excluded_alternative_category": (
        "excluded",
        "affirmative: its own page places it under another category, named in other_branch",
    ),
    "excluded_category_path_missing": (
        "unresolved",
        "missing: its own page gives no category path (categoryPathId -1, no breadcrumb), so neither the required "
        "category nor another is shown",
    ),
    "excluded_local_eligibility_not_proven": (
        "unresolved",
        "missing: its own page does not prove local eligibility (record_reasons); nothing shows it absent from the store",
    ),
}
COLUMNS = [
    "item_id",
    "queue_kind",
    "listing_id",
    "listing_name",
    "client_case",
    "outcome_class_1_6_8",
    "outcome_this_revision",
    "basis",
    "other_branch",
    "category_path_on_its_page",
    "record_reasons",
    "decided_by_run",
    "run_label",
    "page_artifact_sha256",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def recount() -> tuple[bytes, bytes]:
    rows = list(csv.DictReader(io.StringIO(SOURCE.read_bytes().decode("utf-8"))))
    if len(rows) != 275 or len({r["item_id"] for r in rows}) != 275:
        raise SystemExit(f"{SOURCE.name}: expected 275 distinct products, found {len(rows)}")
    out = []
    for r in rows:
        cls = r["outcome_class"]
        if cls not in RECOUNT:
            raise SystemExit(f"{r['item_id']}: an outcome class this recount does not know: {cls!r}")
        outcome, basis = RECOUNT[cls]
        if cls == "excluded_alternative_category" and not r["other_branch"]:
            raise SystemExit(f"{r['item_id']}: excluded on another category, but none is named")
        out.append(
            {
                "item_id": r["item_id"],
                "queue_kind": r["queue_kind"],
                "listing_id": r["listing_id"],
                "listing_name": r["listing_name"],
                "client_case": r["client_case"],
                "outcome_class_1_6_8": cls,
                "outcome_this_revision": outcome,
                "basis": basis,
                "other_branch": r["other_branch"],
                "category_path_on_its_page": r["category_path_on_its_page"],
                "record_reasons": r["record_reasons"],
                "decided_by_run": r["decided_by_run"],
                "run_label": r["run_label"],
                "page_artifact_sha256": r["page_artifact_sha256"],
            }
        )
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\n")
    w.writeheader()
    w.writerows(out)
    by_outcome = Counter(r["outcome_this_revision"] for r in out)
    by_class = Counter(r["outcome_class_1_6_8"] for r in out)
    unresolved = [r for r in out if r["outcome_this_revision"] == "unresolved"]
    summary = {
        "about": "the 275 queued sponsored and variant products, recounted with missing evidence as unresolved (offline, no request)",
        "source": "evidence/reconciliation/1.6.8/w3/W3_ROW_LEVEL_1_6_7.csv (published under review-1.6.8-20261106, unchanged)",
        "source_sha256": sha256(SOURCE),
        "rule": "excluded only on affirmative source evidence (the item's own page places it in another category, named); "
        "a missing category path or unproven local eligibility leaves it unresolved",
        "outcomes": {k: by_outcome[k] for k in ("included", "excluded", "duplicate", "unresolved")},
        "outcomes_1_6_8": dict(sorted(by_class.items())),
        "unresolved_by_reason": {
            "no category path on its page": sum(
                1 for r in unresolved if r["outcome_class_1_6_8"] == "excluded_category_path_missing"
            ),
            "local eligibility not proven by its page": sum(
                1 for r in unresolved if r["outcome_class_1_6_8"] == "excluded_local_eligibility_not_proven"
            ),
        },
        "unresolved_record_reasons": dict(
            sorted(Counter(r["record_reasons"] or "(none: no category path)" for r in unresolved).items())
        ),
        "unresolved_client_cases": sorted(r["client_case"] for r in unresolved if r["client_case"]),
        "client_cases": dict(
            sorted(Counter(r["outcome_this_revision"] for r in out if r["client_case"]).items())
        ),
        "not_in_this_count": "the 44 products whose UPC has no read: a separate queue (W2), unchanged",
        "what_settles_the_unresolved": "their own pages read again with the store's context (paid requests); none was made",
    }
    return buf.getvalue().encode("utf-8"), (json.dumps(summary, indent=1) + "\n").encode("utf-8")


def main() -> int:
    found = sha256(SOURCE)
    if SOURCE_SHA256.startswith("@@"):
        raise SystemExit("the source's SHA-256 is not filled in")
    if found != SOURCE_SHA256:
        print(f"FAIL  {SOURCE.name}: SHA-256 {found}, expected {SOURCE_SHA256}")
        return 1
    csv_bytes, json_bytes = recount()
    if "--write" in sys.argv:
        OUT_CSV.write_bytes(csv_bytes)
        OUT_JSON.write_bytes(json_bytes)
        print("written", OUT_CSV.name, OUT_JSON.name)
        print(json.dumps(json.loads(json_bytes)["outcomes"]))
        return 0
    ok = OUT_CSV.read_bytes() == csv_bytes and OUT_JSON.read_bytes() == json_bytes
    print(("ok    " if ok else "FAIL  ") + f"{OUT_CSV.name} and {OUT_JSON.name} equal a fresh recount of {SOURCE.name}")
    print(json.dumps(json.loads(json_bytes)["outcomes"]))
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
