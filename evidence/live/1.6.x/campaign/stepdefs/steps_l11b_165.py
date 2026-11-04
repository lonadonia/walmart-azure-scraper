"""Stage L11b on release 1.6.5 (W5): the canary of the final revision, after L11. L11 named Beauty's New Arrivals
listing directly; that page gives no breadcrumb, so the collector could not place it under Beauty, recorded none of
its products (INCOMPLETE, IDENTITY) and no canary ran. L11b reads page 1 of Food's Fresh Fruits listing (CSV row 0,
/browse/food/fresh-fruits/976759_976793_9756351, the listing of the 1.6.0 canary L1, whose stored pages, the latest
from L7 at 12:13Z today, place it under Food 976759), with one worker, no product detail request and no follow-up
page: about 3 submissions (robots.txt, the store page, the listing page), 6 at most. The automated canary and
validate-export apply the 1.6.5 source check. Never published: a bounded run is a pilot.

usage: python -I steps_l11b_165.py   (reads the shared ledger read-only; writes the L11b steps)
"""

import hashlib
import json
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

P = Path(r"C:\w9\evidence\live160\stage_steps.json")
steps = json.loads(P.read_text(encoding="utf-8"))
if "l11b_run" in steps:
    raise SystemExit("L11b is already there")
TRIAL_DIR = r"<projects>\.shared-oxylabs-trial-20261103"
sys.path.insert(0, TRIAL_DIR)
import oxytrial_ledger as otl  # noqa: E402

status = otl.open_ledger(TRIAL_DIR, "oxylabs-trial-20261103").summary()
left = Decimal(status["projects"]["walmart"]["spendable_in_envelope_usd"])
RATE, MAX_REQ = Decimal("0.0015"), 6
max_usd = (RATE * MAX_REQ).quantize(Decimal("0.001"))
if left < max_usd:
    raise SystemExit(f"only {left} left in the envelope")
ED = Path(r"C:\w9\live\ed\walmart-oxylabs-1.6.5")
REV = json.loads((ED / "BUILD_INFO.json").read_text(encoding="utf-8"))["commit"]
ZIP = Path(r"C:\w9\delivery165\source\editions\WALMART_OXYLABS_SOURCE_1.6.5.zip")
ZIP_SHA = hashlib.sha256(ZIP.read_bytes()).hexdigest()
STORE = "walmart-3891-pickup"
CFG = r"C:\w9\evidence\live160\configs\collector.census_164.yaml"
cfg_sha = hashlib.sha256(Path(CFG).read_bytes()).hexdigest()
STAGE = "W-L11b-canary-165-20261104"
deadline = (datetime.now(UTC) + timedelta(hours=1)).replace(microsecond=0).isoformat()
run_args = [
    "run", "--store", STORE, "--provider", "oxylabs", "--categories", "0",
    "--subcategory", "0:/browse/food/fresh-fruits/976759_976793_9756351",
    "--max-pages-per-listing", "1", "--pilot-no-detail", "--follow-up-pages", "0", "--workers", "1",
    "--max-credits", str(MAX_REQ), "--max-minutes", "20",
]
common = {"edition": "1.6.5", "config": CFG}
steps.update(
    {
        "l11b_validate_config": {**common, "args": ["validate-config", "--check-db", "--require-credentials"],
                                "expected": 0},
        "l11b_status_before": {**common, "args": ["status", "--limit", "3"], "expected": 0},
        "l11b_trial_open": {
            "kind": "trial_open",
            "stage": {
                "stage_id": STAGE,
                "project": "walmart",
                "objective": "W5 canary on the final release 1.6.5 (the source check corrected), after L11: the "
                "store's context (3891, Pickup), page 1 of Food's Fresh Fruits listing, the automated canary and "
                "validate-export with the 1.6.5 source check, the four deal fields empty, every submission through "
                "the account-wide gate; never published",
                "command": "walmart-collector " + " ".join(run_args),
                "config": {
                    "edition": "oxylabs 1.6.5",
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
        "l11b_ceiling": {
            **common,
            "args": [
                "set-ceiling", "--provider", "oxylabs", "--submissions", str(MAX_REQ), "--usd", str(max_usd),
                "--minutes", "20", "--usd-per-result", str(RATE), "--basis",
                f"Campaign oxylabs-trial-20261103 (shared with Mariano's; USD 5 total), stage {STAGE} on release "
                f"1.6.5 ({REV[:7]}): {MAX_REQ} submissions (USD {max_usd} at the reserve rate {RATE}), about 3 "
                f"needed; Walmart's envelope had USD {left} left; the shared ledger reserves each submission again "
                "before it is sent",
            ],
            "expected": 0,
        },
        "l11b_run": {**common, "args": run_args, "expected": -1, "run_stage": "L11b", "trial_stage": STAGE},
    }
)
P.write_text(json.dumps(steps, indent=1) + "\n", encoding="utf-8")
print(json.dumps({"left_usd": str(left), "max_requests": MAX_REQ, "max_usd": str(max_usd), "deadline": deadline,
                  "revision": REV, "zip_sha256": ZIP_SHA, "config_sha256": cfg_sha}))
