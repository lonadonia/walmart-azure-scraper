"""Stage L3 on the final revision 1.6.1 (W5 stage 3 again, W6): the >= 500 fresh demonstration on the frozen 1.6.1
build, with detail extraction active (production mode: every exported product missing a UPC or a size gets its own
page, or an earlier read within 30 days), and the recovery path of the final implementation: a graceful pause
(Ctrl+Break), a refused overlapping run while the paused run is unfinished, a forced kill, and resumes to the end.

Scope: the six listings of L2, at most 3 result pages each; no follow-up page (L2 read the queue's seeds on these
listings). Sizing: 3 executions x 2 workers x (robots + store page) = 12, 18 listing pages, and the product pages
no earlier read answers for (L2 read 254 of these listings' products within the hour): about 40 to 70 results.
"""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

P = Path(r"C:\w9\evidence\live160\stage_steps.json")
steps = json.loads(P.read_text(encoding="utf-8"))
if "l3_run" in steps:
    raise SystemExit("L3 is already there")
REV = json.loads(Path(r"C:\w9\live\ed\walmart-oxylabs-1.6.1\BUILD_INFO.json").read_text(encoding="utf-8"))
REV_ID = REV.get("revision") or REV.get("commit") or REV.get("source_commit")
ZIP_SHA = Path(r"C:\w9\live\dist\WALMART_OXYLABS_SOURCE_1.6.1.zip.sha256").read_text(encoding="utf-8").split()[0]
STORE = "walmart-3891-pickup"
CFG = r"C:\w9\evidence\live160\configs\collector.l3_161.yaml"
cfg_sha = hashlib.sha256(Path(CFG).read_bytes()).hexdigest()
STAGE = "W-L3-final-demo-161-20261103"
MAX_REQ, RATE = 100, "0.0015"
deadline = (datetime.now(UTC) + timedelta(hours=2)).replace(microsecond=0).isoformat()
subs = [
    "0:/browse/food/fresh-vegetables/976759_976793_8910423",
    "0:/browse/food/fresh-fruits/976759_976793_9756351",
    "1:/browse/laundry/1115193_1071967",
    "3:/browse/hair-care/shampoo/1085666_3147628_5752434",
    "6:/browse/health-medicine/shop-all-cold-cough-flu-medicine/976760_4661388_6244277_7158394",
    "7:/browse/pets/dry-dog-food/5440_202072_6432755_1636265",
]
run_args = ["run", "--store", STORE, "--provider", "oxylabs", "--categories", "0,1,3,6,7"]
for s in subs:
    run_args += ["--subcategory", s]
run_args += [
    "--max-pages-per-listing", "3", "--follow-up-pages", "0", "--workers", "2",
    "--max-credits", str(MAX_REQ), "--max-minutes", "120",
]
overlap_args = [
    "run", "--store", STORE, "--provider", "oxylabs", "--categories", "7",
    "--subcategory", "7:/browse/pets/dry-dog-food/5440_202072_6432755_1636265",
    "--max-pages-per-listing", "1", "--pilot-no-detail", "--follow-up-pages", "0", "--workers", "1",
    "--max-credits", "5", "--max-minutes", "10",  # 5: the smallest per-run credit limit the collector accepts
]
common = {"edition": "1.6.1", "config": CFG}
steps.update(
    {
        "l3_validate_config": {**common, "args": ["validate-config", "--check-db", "--require-credentials"],
                               "expected": 0},
        "l3_trial_open": {
            "kind": "trial_open",
            "stage": {
                "stage_id": STAGE,
                "project": "walmart",
                "objective": "W5 stage 3 and W6 on the final revision 1.6.1: >= 500 fresh valid products from the six "
                "L2 listings (3 pages each) with detail extraction active and new-versus-reused field evidence; a "
                "graceful pause, a refused overlapping run, a forced kill and resumes to the end",
                "command": "walmart-collector " + " ".join(run_args),
                "config": {
                    "edition": "oxylabs 1.6.1",
                    "zip_sha256": ZIP_SHA,
                    "stage_config": CFG,
                    "stage_config_sha256": cfg_sha,
                    "workers": 2,
                },
                "source_revision": REV_ID,
                "max_requests": MAX_REQ,
                "max_results": MAX_REQ,
                "max_usd": "0.150",
                "deadline_utc": deadline,
                "retry_policy": "the collector's: at most 3 submissions per request; 408, 429 and 5xx retried with "
                "backoff and jitter; Retry-After honoured up to 60 s; every submission is a new reservation",
                "stop_conditions": "a store check fails; a block or challenge; the gate, the ceiling, the credit or "
                "time budget or the deadline refuses; repeated pages; any unexpected exit",
            },
        },
        "l3_ceiling": {
            **common,
            "args": [
                "set-ceiling", "--provider", "oxylabs", "--submissions", str(MAX_REQ), "--usd", "0.15",
                "--minutes", "120", "--usd-per-result", RATE, "--basis",
                f"Campaign oxylabs-trial-20261103 (shared with Mariano's; USD 5 total), stage {STAGE} on release "
                f"1.6.1 ({REV_ID[:7]}): {MAX_REQ} submissions (USD 0.15 at the reserve rate 0.0015), 120 minutes, "
                "counted from this setting; about 40 to 70 needed; the shared ledger reserves each submission again "
                "before it is sent",
            ],
            "expected": 0,
        },
        "l3_run": {**common, "args": run_args, "expected": -1, "run_stage": "L3", "trial_stage": STAGE,
                   "pause_after_s": 45},
        "l3_status_paused": {**common, "args": ["status", "--limit", "3"], "expected": 0},
        "l3_overlap_refused": {**common, "args": overlap_args, "expected": 9, "trial_stage": STAGE},
    }
)
P.write_text(json.dumps(steps, indent=1) + "\n", encoding="utf-8")
print("L3 added; revision", REV_ID, "zip", ZIP_SHA, "deadline", deadline, "config", cfg_sha)
