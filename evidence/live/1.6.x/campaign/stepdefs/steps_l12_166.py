"""Stage L12 on release 1.6.6: the live canary of the final frozen revision WITH product-page reading on, inside what
is left of Walmart's trial envelope (USD 0.0225, 15 submissions at the reserve rate). The >=500-product
demonstration with product pages on needs 28 to 45 submissions and stays BLOCKED_BUDGET; this stage is not it.

L12 reads page 1 of Household Essentials' Fabric Softeners listing (CSV row 1,
/browse/household-essentials/fabric-softener/1115193_1071967_1630538, named with --subcategory; its page 1 was read
by L7 on 1.6.3 today, 49 products, 4 of them in W2's queue of UPCs never read), with one worker, at most 10 product
pages for missing fields (the store's queue order: never read first, oldest first) and no follow-up page: about
13 submissions (robots.txt, the store page, the listing page, 10 product pages), 15 at most. The automated canary
and validate-export run as in L11b. Never published: a bounded run is a pilot.

usage: python -I steps_l12_166.py   (reads the shared ledger read-only; writes the L12 steps)
"""

import hashlib
import json
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

P = Path(r"C:\w9\evidence\live160\stage_steps.json")
steps = json.loads(P.read_text(encoding="utf-8"))
if "l12_run" in steps:
    raise SystemExit("L12 is already there")
TRIAL_DIR = r"<projects>\.shared-oxylabs-trial-20261103"
sys.path.insert(0, TRIAL_DIR)
import oxytrial_ledger as otl  # noqa: E402

status = otl.open_ledger(TRIAL_DIR, "oxylabs-trial-20261103").summary()
left = Decimal(status["projects"]["walmart"]["spendable_in_envelope_usd"])
RATE, MAX_REQ, DETAIL = Decimal("0.0015"), 15, 10
max_usd = (RATE * MAX_REQ).quantize(Decimal("0.0001"))
if left < max_usd:
    raise SystemExit(f"only {left} left in the envelope")
ED = Path(r"C:\w9\live\ed\walmart-oxylabs-1.6.6")
REV = json.loads((ED / "BUILD_INFO.json").read_text(encoding="utf-8"))["commit"]
ZIP = Path(r"C:\w9\delivery166\source\editions\WALMART_OXYLABS_SOURCE_1.6.6.zip")
ZIP_SHA = hashlib.sha256(ZIP.read_bytes()).hexdigest()
STORE = "walmart-3891-pickup"
CFG = r"C:\w9\evidence\live160\configs\collector.l12_166.yaml"
cfg_sha = hashlib.sha256(Path(CFG).read_bytes()).hexdigest()
STAGE = "W-L12-detail-canary-166-20261104"
LISTING = "1:/browse/household-essentials/fabric-softener/1115193_1071967_1630538"
deadline = (datetime.now(UTC) + timedelta(hours=1)).replace(microsecond=0).isoformat()
run_args = [
    "run", "--store", STORE, "--provider", "oxylabs", "--categories", "1", "--subcategory", LISTING,
    "--max-pages-per-listing", "1", "--pilot-detail-pages", str(DETAIL), "--follow-up-pages", "0", "--workers", "1",
    "--max-credits", str(MAX_REQ), "--max-minutes", "30",
]
common = {"edition": "1.6.6", "config": CFG}
steps.update(
    {
        "l12_validate_config": {**common, "args": ["validate-config", "--check-db", "--require-credentials"],
                               "expected": 0},
        "l12_status_before": {**common, "args": ["status", "--limit", "3"], "expected": 0},
        "l12_followups_before": {**common, "args": ["follow-ups", "--store", STORE, "--kind", "detail"],
                                "expected": 0},
        "l12_trial_open": {
            "kind": "trial_open",
            "stage": {
                "stage_id": STAGE,
                "project": "walmart",
                "objective": "Canary of the final frozen release 1.6.6 with product-page reading on (W5; W2's UPC "
                "queue): the store's context (3891, Pickup), page 1 of Household Essentials' Fabric Softeners "
                "listing, at most 10 product pages for missing UPC or size (never read first), the automated canary "
                "and validate-export, the four deal fields empty, every submission through the account-wide gate; "
                "never published. Not the >=500-product demonstration, which stays BLOCKED_BUDGET",
                "command": "walmart-collector " + " ".join(run_args),
                "config": {
                    "edition": "oxylabs 1.6.6",
                    "zip_sha256": ZIP_SHA,
                    "stage_config": CFG,
                    "stage_config_sha256": cfg_sha,
                    "workers": 1,
                },
                "source_revision": REV,
                "max_requests": MAX_REQ,
                "max_results": MAX_REQ,
                "max_usd": str(max_usd),
                "deadline_utc": deadline,
                "retry_policy": "the collector's: at most 3 submissions per request; 408, 429 and 5xx retried with "
                "backoff and jitter; Retry-After honoured up to 60 s; every submission is a new reservation",
                "stop_conditions": "a store check fails; a block or challenge; the canary fails; the gate, the "
                "ceiling, the credit or time budget or the deadline refuses; any unexpected exit",
            },
        },
        "l12_ceiling": {
            **common,
            "args": [
                "set-ceiling", "--provider", "oxylabs", "--submissions", str(MAX_REQ), "--usd", str(max_usd),
                "--minutes", "30", "--usd-per-result", str(RATE), "--basis",
                f"Campaign oxylabs-trial-20261103 (shared with Mariano's; USD 5 total), stage {STAGE} on release "
                f"1.6.6 ({REV[:7]}): {MAX_REQ} submissions (USD {max_usd} at the reserve rate {RATE}), about 13 "
                f"needed; Walmart's envelope had USD {left} left; Hamza's request of 2026-11-04 (use only the "
                "remaining authorized trial credit); the shared ledger reserves each submission again before it is "
                "sent",
            ],
            "expected": 0,
        },
        "l12_run": {**common, "args": run_args, "expected": -1, "run_stage": "L12", "trial_stage": STAGE},
    }
)
P.write_text(json.dumps(steps, indent=1) + "\n", encoding="utf-8")
print(json.dumps({"left_usd": str(left), "max_requests": MAX_REQ, "max_usd": str(max_usd), "deadline": deadline,
                  "revision": REV, "zip_sha256": ZIP_SHA, "config_sha256": cfg_sha}))
