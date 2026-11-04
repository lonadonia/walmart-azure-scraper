"""Stage L4r on the final revision 1.6.1 (W4 revisits): every page of the five listings the reviewed campaign left
capped at 3 pages (S6 on 1.5.1: Fresh Vegetables 287, Laundry 623, Shampoo 600, Shop all Cold Cough & Flu Medicine
350, Dry Dog Food 137 with the totals 139/137/138 of S3 and S4), every page of Fresh Fruits (139 in L2), and page 1 of
Strawberries (0 results in S4, 2 to 5 before): their current totals, distinct identities, exclusions and end against
the totals Walmart reports. No product detail page and no follow-up page: a coverage revisit, not a field run (blank
UPCs and sizes are recorded as not attempted; reads of the last 30 days are reused).

Sizing (L2's totals, 40 tiles a page): 8 + 16 + 16 + 9 + 4 + 4 + 1 = 58 listing pages, plus robots and the store page
per worker and execution (2 workers: 4): about 62 results. The stage and the ceiling allow 80. No listing reaches
Walmart's result window (25 pages), so none is partitioned.
"""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

P = Path(r"C:\w9\evidence\live160\stage_steps.json")
steps = json.loads(P.read_text(encoding="utf-8"))
if "l4r_run" in steps:
    raise SystemExit("L4r is already there")
REV = json.loads(Path(r"C:\w9\live\ed\walmart-oxylabs-1.6.1\BUILD_INFO.json").read_text(encoding="utf-8"))["commit"]
ZIP_SHA = Path(r"C:\w9\live\dist\WALMART_OXYLABS_SOURCE_1.6.1.zip.sha256").read_text(encoding="utf-8").split()[0]
STORE = "walmart-3891-pickup"
CFG = r"C:\w9\evidence\live160\configs\collector.l4r_161.yaml"
cfg_sha = hashlib.sha256(Path(CFG).read_bytes()).hexdigest()
STAGE = "W-L4r-capped-revisits-161-20261103"
MAX_REQ, RATE = 80, "0.0015"
deadline = (datetime.now(UTC) + timedelta(hours=2)).replace(microsecond=0).isoformat()
subs = [
    "0:/browse/food/fresh-vegetables/976759_976793_8910423",
    "0:/browse/food/fresh-fruits/976759_976793_9756351",
    "0:/browse/food/strawberries/976759_976793_9756351_3521037",
    "1:/browse/laundry/1115193_1071967",
    "3:/browse/hair-care/shampoo/1085666_3147628_5752434",
    "6:/browse/health-medicine/shop-all-cold-cough-flu-medicine/976760_4661388_6244277_7158394",
    "7:/browse/pets/dry-dog-food/5440_202072_6432755_1636265",
]
run_args = ["run", "--store", STORE, "--provider", "oxylabs", "--categories", "0,1,3,6,7"]
for s in subs:
    run_args += ["--subcategory", s]
run_args += [
    "--pilot-no-detail", "--follow-up-pages", "0", "--workers", "2",
    "--max-credits", str(MAX_REQ), "--max-minutes", "90",
]
common = {"edition": "1.6.1", "config": CFG}
steps.update(
    {
        "l4r_trial_open": {
            "kind": "trial_open",
            "stage": {
                "stage_id": STAGE,
                "project": "walmart",
                "objective": "W4 revisits on 1.6.1: every page of the five listings S6 left capped at 3 pages and of "
                "Fresh Fruits, and page 1 of Strawberries, with their current totals, distinct identities and "
                "ends; no product detail or follow-up page",
                "command": "walmart-collector " + " ".join(run_args),
                "config": {
                    "edition": "oxylabs 1.6.1",
                    "zip_sha256": ZIP_SHA,
                    "stage_config": CFG,
                    "stage_config_sha256": cfg_sha,
                    "workers": 2,
                },
                "source_revision": REV,
                "max_requests": MAX_REQ,
                "max_results": MAX_REQ,
                "max_usd": "0.120",
                "deadline_utc": deadline,
                "retry_policy": "the collector's: at most 3 submissions per request; 408, 429 and 5xx retried with "
                "backoff and jitter; Retry-After honoured up to 60 s; every submission is a new reservation",
                "stop_conditions": "a store check fails; a block or challenge; the gate, the ceiling, the credit or "
                "time budget or the deadline refuses; repeated pages; any unexpected exit",
            },
        },
        "l4r_ceiling": {
            **common,
            "args": [
                "set-ceiling", "--provider", "oxylabs", "--submissions", str(MAX_REQ), "--usd", "0.12",
                "--minutes", "90", "--usd-per-result", RATE, "--basis",
                f"Campaign oxylabs-trial-20261103 (shared with Mariano's; USD 5 total), stage {STAGE} on release "
                f"1.6.1 ({REV[:7]}): {MAX_REQ} submissions (USD 0.12 at the reserve rate 0.0015), 90 minutes, "
                "counted from this setting; about 62 needed; the shared ledger reserves each submission again "
                "before it is sent",
            ],
            "expected": 0,
        },
        "l4r_run": {**common, "args": run_args, "expected": -1, "run_stage": "L4r", "trial_stage": STAGE},
    }
)
P.write_text(json.dumps(steps, indent=1) + "\n", encoding="utf-8")
print("L4r added; revision", REV, "zip", ZIP_SHA, "deadline", deadline, "config", cfg_sha)
