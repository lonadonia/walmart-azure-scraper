"""Closes stage W-L2-highvalue-demo-20261103 in the shared trial ledger (a parent-only step). The figures are those of
runs/L2/L2_CHECKS.json and commands.csv (steps 21 to 31)."""

import json
from pathlib import Path

P = Path(r"C:\w9\evidence\live160\stage_steps.json")
steps = json.loads(P.read_text(encoding="utf-8"))
if "l2_trial_close" in steps:
    raise SystemExit("already there")
steps["l2_trial_close"] = {
    "kind": "trial_close",
    "stage_id": "W-L2-highvalue-demo-20261103",
    "outcome": (
        "PASSED (run 01M6H72J86K5TF7A1874N7BJ2R on release 1.6.0, a pilot by design, never published: final exit 0, "
        "the only failed check G3 (3 result pages per listing by design)). Store 3891 Pickup verified at preflight "
        "and at every task start; 707 fresh valid products from 6 listings (>= 500); UPC 702 of 707 (279 from "
        "product pages read in this run, 423 from reads of the last 30 days, 3 absent in the source, 2 identity "
        "mismatches), size 695 of 707; the four deal fields '' in all 806 exported rows (707 fresh, 99 carried); all "
        "177 queue seeds resolved (as variants 161 excluded, 14 included, 2 duplicates; 1 sponsored excluded; 2 "
        "detail rows included); recovery: a graceful pause (Ctrl+Break at 480 s, exit 75), a forced kill at 420 s "
        "of the first resume (recovered: segment abandoned, task lease reclaimed) and a second resume to the end. "
        "524 reservations in this ledger: 514 settled results (USD 0.771 at the reserve rate), 6 documented free, "
        "4 unknown held at USD 0.006 (2 cancelled at the pause, 2 abandoned at the kill); the collector's ledger "
        "agrees (514 ok, 2 cancelled, 2 abandoned)"
    ),
}
P.write_text(json.dumps(steps, indent=1) + "\n", encoding="utf-8")
print("added")
