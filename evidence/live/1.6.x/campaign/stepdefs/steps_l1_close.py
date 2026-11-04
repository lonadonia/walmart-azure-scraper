"""Closes stage W-L1-canary-20261103 in the shared trial ledger (a parent-only step)."""

import json
from pathlib import Path

P = Path(r"C:\w9\evidence\live160\stage_steps.json")
steps = json.loads(P.read_text(encoding="utf-8"))
if "l1_trial_close" in steps:
    raise SystemExit("already there")
steps["l1_trial_close"] = {
    "kind": "trial_close",
    "stage_id": "W-L1-canary-20261103",
    "outcome": (
        "PASSED (run 01M6H5TX7R4ZWV8W3NTH0QN6HF, a pilot by design, never published: exit 6 with G3 (one listing "
        "page by design) and G4 (677 carried against 32 fresh: carried records never count as yield)). Store 3891 "
        "Pickup verified; canary page 40 tiles, 32 valid, source check 32/32; one product page read; export of 709 "
        "rows passes the 22-field contract with the four deal fields '' in every row; 4 submissions, 4 results, "
        "USD 0.006 at the reserve rate, the collector's ledger and this ledger agree"
    ),
}
P.write_text(json.dumps(steps, indent=1) + "\n", encoding="utf-8")
print("added")
