"""Stage L2 (W5 stages 2 and 3 joined): the high-value product pages and the >= 500 fresh demonstration in one
run on the frozen revision, with a graceful pause (Ctrl+Break) and later a forced kill, each resumed.

Scope: six listings, at most 3 result pages each (the S6 pages that hold the W2 UPC/size gaps, and Fresh Fruits),
product detail in production mode (every exported product missing a UPC or a size: its own page, or an earlier
read within 30 days), and the 177 seeds of the 1.5.2 exact live-read queue on four of these listings (W3), read
first by the variant follow-up; at most 200 follow-up pages per kind (a pilot budget: 2 workers x 100, the
larger worker's share of the seeds). Sizing: C:/w9/evidence/live160/plan/l2_sizing.json (about 520 results).
"""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

P = Path(r"C:\w9\evidence\live160\stage_steps.json")
steps = json.loads(P.read_text(encoding="utf-8"))
if "l2_run" in steps:
    raise SystemExit("L2 is already there")
REV = "56f078efce4df3b40165dbeafcfe49e6c6f581eb"
STORE = "walmart-3891-pickup"
CFG = r"C:\w9\evidence\live160\configs\collector.l2.yaml"
cfg_sha = hashlib.sha256(Path(CFG).read_bytes()).hexdigest()
STAGE = "W-L2-highvalue-demo-20261103"
MAX_REQ, RATE = 600, "0.0015"
deadline = (datetime.now(UTC) + timedelta(hours=4)).replace(microsecond=0).isoformat()
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
    "--max-pages-per-listing", "3", "--follow-up-pages", "200", "--workers", "2",
    "--max-credits", str(MAX_REQ), "--max-minutes", "240",
]
steps.update(
    {
        "l2_trial_open": {
            "kind": "trial_open",
            "stage": {
                "stage_id": STAGE,
                "project": "walmart",
                "objective": "W5 stages 2+3 joined (W2/W3/W5): re-read the six listings (3 pages each) that hold the "
                "store's unresolved UPC/size rows with product detail in production mode, read the 177 queue seeds "
                "on four of them, and demonstrate >= 500 fresh valid products from one run with truthful new-versus-"
                "reused field evidence; a graceful pause and a forced kill, each resumed",
                "command": "walmart-collector " + " ".join(run_args),
                "config": {
                    "edition": "oxylabs 1.6.0",
                    "zip_sha256": "5a70e4616c8a37875103787323e99943a74237024bcf58ee2322c17a1da1febd",
                    "stage_config": CFG,
                    "stage_config_sha256": cfg_sha,
                    "workers": 2,
                },
                "source_revision": REV,
                "max_requests": MAX_REQ,
                "max_results": MAX_REQ,
                "max_usd": "0.900",
                "deadline_utc": deadline,
                "retry_policy": "the collector's: at most 3 submissions per request; 408, 429 and 5xx retried with "
                "backoff and jitter; Retry-After honoured up to 60 s; every submission is a new reservation",
                "stop_conditions": "a store check fails; a block or challenge; the gate, the ceiling, the credit or "
                "time budget or the deadline refuses; repeated pages; any unexpected exit",
            },
        },
        "l2_ceiling": {
            "args": [
                "set-ceiling", "--provider", "oxylabs", "--submissions", str(MAX_REQ), "--usd", "0.90",
                "--minutes", "240", "--usd-per-result", RATE, "--basis",
                f"Campaign oxylabs-trial-20261103 (shared with Mariano's; USD 5 total), stage {STAGE} on release "
                f"1.6.0 (56f078e): {MAX_REQ} submissions (USD 0.90 at the reserve rate 0.0015), 240 minutes, counted "
                "from this setting; sized from l2_sizing.json (about 520); the shared ledger reserves each "
                "submission again before it is sent",
            ],
            "expected": 0,
        },
        "l2_run": {
            "args": run_args,
            "config": CFG,
            "expected": -1,
            "run_stage": "L2",
            "trial_stage": STAGE,
            "pause_after_s": 480,
        },
    }
)
P.write_text(json.dumps(steps, indent=1) + "\n", encoding="utf-8")
print("L2 added; deadline", deadline, "config", cfg_sha)
