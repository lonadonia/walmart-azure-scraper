"""Stage L9 on the final revision 1.6.3 (W4, and the 1.6.3 correction seen live): the two child listings that L6
(release 1.6.2) left unread when it stopped, read to their end on 1.6.3, directly by their own paths:

- Shampoo's child "Nexxus Shampoo" (1085666_3147628_5752434_9323405): on 2026-11-04 10:43Z it answered with
  Walmart's own not-found page (page data route /404, script id written without quotes), which 1.6.2 called a
  challenge (SITE_REFUSAL, store held). 1.6.3 records such a listing INCOMPLETE (NOT_FOUND) and goes on; if the
  site now serves a result grid there, it is read like any listing.
- Laundry's child "Seventh Generation Laundry Care" (1115193_1071967_8953745): not reached before that stop.

Both are named by their parents' "Departments" facets (L6's coverage report). No product detail request and no
follow-up page (the stage is about coverage); 1.6.3 still uses saved reads for UPC and size at no request.

Sizing: 1 worker x (robots + store page) = 2, Nexxus 1 page, Seventh Generation 1 or 2 pages: about 4 to 6 results.
Ceiling 12 submissions (USD 0.018 at the reserve rate).
"""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

P = Path(r"C:\w9\evidence\live160\stage_steps.json")
steps = json.loads(P.read_text(encoding="utf-8"))
if "l9_run" in steps:
    raise SystemExit("L9 is already there")
ED = Path(r"C:\w9\live\ed\walmart-oxylabs-1.6.3")
REV_ID = json.loads((ED / "BUILD_INFO.json").read_text(encoding="utf-8"))["commit"]
ZIP_SHA = Path(r"C:\w9\live\dist\WALMART_OXYLABS_SOURCE_1.6.3.zip.sha256").read_text(encoding="utf-8").split()[0]
STORE = "walmart-3891-pickup"
CFG = r"C:\w9\evidence\live160\configs\collector.l8_163.yaml"  # the same frozen edition configuration as L8
cfg_sha = hashlib.sha256(Path(CFG).read_bytes()).hexdigest()
STAGE = "W-L9-unread-children-163-20261104"
MAX_REQ, RATE, MAX_USD = 12, "0.0015", "0.018"
deadline = (datetime.now(UTC) + timedelta(hours=1)).replace(microsecond=0).isoformat()
run_args = [
    "run", "--store", STORE, "--provider", "oxylabs", "--categories", "1,3",
    "--subcategory", "1:/browse/household-essentials/seventh-generation-laundry-care/1115193_1071967_8953745",
    "--subcategory", "3:/browse/beauty/nexxus-shampoo/1085666_3147628_5752434_9323405",
    "--pilot-no-detail", "--follow-up-pages", "0", "--workers", "1",
    "--max-credits", str(MAX_REQ), "--max-minutes", "20",
]
common = {"edition": "1.6.3", "config": CFG}
steps.update(
    {
        "l9_trial_open": {
            "kind": "trial_open",
            "stage": {
                "stage_id": STAGE,
                "project": "walmart",
                "objective": "W4 and the 1.6.3 correction seen live: the two child listings L6 (1.6.2) left unread "
                "when it stopped, read to their end on 1.6.3 by their own paths: Nexxus Shampoo (answered with "
                "Walmart's not-found page at 10:43Z; 1.6.3 records NOT_FOUND and goes on) and Seventh Generation "
                "Laundry Care; no product detail and no follow-up page",
                "command": "walmart-collector " + " ".join(run_args),
                "config": {
                    "edition": "oxylabs 1.6.3",
                    "zip_sha256": ZIP_SHA,
                    "stage_config": CFG,
                    "stage_config_sha256": cfg_sha,
                    "workers": 1,
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
        "l9_ceiling": {
            **common,
            "args": [
                "set-ceiling", "--provider", "oxylabs", "--submissions", str(MAX_REQ), "--usd", MAX_USD,
                "--minutes", "20", "--usd-per-result", RATE, "--basis",
                f"Campaign oxylabs-trial-20261103 (shared with Mariano's; USD 5 total), stage {STAGE} on release "
                f"1.6.3 ({REV_ID[:7]}): {MAX_REQ} submissions (USD {MAX_USD} at the reserve rate 0.0015), 20 "
                "minutes, counted from this setting; about 4 to 6 needed; the shared ledger reserves each "
                "submission again before it is sent",
            ],
            "expected": 0,
        },
        "l9_run": {**common, "args": run_args, "expected": -1, "run_stage": "L9", "trial_stage": STAGE},
    }
)
P.write_text(json.dumps(steps, indent=1) + "\n", encoding="utf-8")
print("L9 added; revision", REV_ID, "zip", ZIP_SHA, "deadline", deadline, "config", cfg_sha)
