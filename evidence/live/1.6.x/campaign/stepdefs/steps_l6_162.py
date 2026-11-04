"""Stage L6 on the final revision 1.6.2 (W4: the correction of 1.6.2 seen live): Laundry and Shampoo, the two listings
whose totals moved a little while the site served far fewer results (L4r on 1.6.1: Laundry 615/613/614/611 reported,
393 served, page 11 of 16 empty; Shampoo 608/607 reported, 399 served, page 12 empty), read to their end and then,
past their result window, through the child categories their own "Departments" facets name (Laundry 12, Shampoo 8),
as deep as those facets go. No product detail and no follow-up page: the stage is about coverage.

Sizing: the two parents to their end (about 23 result pages), the 20 children's pages (their products overlap the
parents': about 30 to 45 pages), robots and the store page per worker: about 60 to 80 results. Ceiling 100
submissions (USD 0.150 at the reserve rate); the collector stops at the ceiling (exit 4) if more is needed, and the
unread children are then the exact continuation.
"""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

P = Path(r"C:\w9\evidence\live160\stage_steps.json")
steps = json.loads(P.read_text(encoding="utf-8"))
if "l6_run" in steps:
    raise SystemExit("L6 is already there")
ED = Path(r"C:\w9\live\ed\walmart-oxylabs-1.6.2")
REV_ID = json.loads((ED / "BUILD_INFO.json").read_text(encoding="utf-8"))["commit"]
ZIP_SHA = Path(r"C:\w9\live\dist\WALMART_OXYLABS_SOURCE_1.6.2.zip.sha256").read_text(encoding="utf-8").split()[0]
STORE = "walmart-3891-pickup"
CFG = r"C:\w9\evidence\live160\configs\collector.l6_162.yaml"
cfg_sha = hashlib.sha256(Path(CFG).read_bytes()).hexdigest()
STAGE = "W-L6-partition-check-162-20261104"
MAX_REQ, RATE, MAX_USD = 100, "0.0015", "0.150"
deadline = (datetime.now(UTC) + timedelta(hours=2)).replace(microsecond=0).isoformat()
run_args = [
    "run", "--store", STORE, "--provider", "oxylabs", "--categories", "1,3",
    "--subcategory", "1:/browse/laundry/1115193_1071967",
    "--subcategory", "3:/browse/hair-care/shampoo/1085666_3147628_5752434",
    "--pilot-no-detail", "--follow-up-pages", "0", "--workers", "2",
    "--max-credits", str(MAX_REQ), "--max-minutes", "90",
]
common = {"edition": "1.6.2", "config": CFG}
steps.update(
    {
        "l6_validate_config": {**common, "args": ["validate-config", "--check-db", "--require-credentials"],
                               "expected": 0},
        "l6_trial_open": {
            "kind": "trial_open",
            "stage": {
                "stage_id": STAGE,
                "project": "walmart",
                "objective": "W4 on the final revision 1.6.2: Laundry and Shampoo read to their end and, past their "
                "result window (the 1.6.2 rule for a total that moved while far more results were reported than "
                "served), through their own child categories; every page, no detail or follow-up page",
                "command": "walmart-collector " + " ".join(run_args),
                "config": {
                    "edition": "oxylabs 1.6.2",
                    "zip_sha256": ZIP_SHA,
                    "stage_config": CFG,
                    "stage_config_sha256": cfg_sha,
                    "workers": 2,
                },
                "source_revision": REV_ID,
                "max_requests": MAX_REQ,
                "max_results": MAX_REQ,
                "max_usd": MAX_USD,
                "deadline_utc": deadline,
                "retry_policy": "the collector's: at most 3 submissions per request; 408, 429 and 5xx retried with "
                "backoff and jitter; Retry-After honoured up to 60 s; every submission is a new reservation",
                "stop_conditions": "a store check fails; a block or challenge; the gate, the ceiling, the credit or "
                "time budget or the deadline refuses; repeated pages; any unexpected exit",
            },
        },
        "l6_ceiling": {
            **common,
            "args": [
                "set-ceiling", "--provider", "oxylabs", "--submissions", str(MAX_REQ), "--usd", MAX_USD,
                "--minutes", "90", "--usd-per-result", RATE, "--basis",
                f"Campaign oxylabs-trial-20261103 (shared with Mariano's; USD 5 total), stage {STAGE} on release "
                f"1.6.2 ({REV_ID[:7]}): {MAX_REQ} submissions (USD {MAX_USD} at the reserve rate 0.0015), 90 "
                "minutes, counted from this setting; about 60 to 80 needed; the shared ledger reserves each "
                "submission again before it is sent",
            ],
            "expected": 0,
        },
        "l6_run": {**common, "args": run_args, "expected": -1, "run_stage": "L6", "trial_stage": STAGE},
    }
)
P.write_text(json.dumps(steps, indent=1) + "\n", encoding="utf-8")
print("L6 added; revision", REV_ID, "zip", ZIP_SHA, "deadline", deadline, "config", cfg_sha)
