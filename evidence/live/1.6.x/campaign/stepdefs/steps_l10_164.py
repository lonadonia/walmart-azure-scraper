"""Stage L10 on release 1.6.4 (W4/W5: the census continued as funded). The census L7 on 1.6.3 read the Food and
Household Essentials category pages and 76 listing pages, then stopped (ABNORMAL_RESULT, store held) at the Household
Essentials link "Bidets", whose page reports 0 Pickup results for store 3891 beside an "Available for shipping"
carousel: 1.6.3 took the 0 for a missing total. Release 1.6.4 reads the 0. L10 reads, on 1.6.4, that listing (row 1
narrowed to it: the 1.6.4 correction seen live) and then rows 2 to 10 in full (Personal Care, Beauty, Diapering,
Feeding, Health & Wellness, Pets, Balloons, Art Supplies, Office Supplies: every listing their category pages name
today, the client's exclusions applied), page 1 of each listing, no product detail request and no follow-up page. The
units L7 left PENDING in rows 0 and 1 stay outstanding (W4 reports them with L7's coverage). Never published: a
bounded run is a pilot.

Sizing: unknown before the run (rows 0 and 1 alone named 321 units in L7, more than the 2026-10-24 estimate of 645
results for all 11 rows implied). The ceiling is what the shared ledger leaves in Walmart's envelope when this is
generated, less a reserve of USD 0.030 (unknown outcomes), at the reserve rate 0.0015 per result. If the rows need
more, the collector stops at the ceiling (exit 4); the run is then finalized (no request) and its unread listings are
the exact continuation.

usage: python -I steps_l10_164.py   (reads the shared ledger read-only; writes the L10 steps)
"""

import hashlib
import json
import sys
from datetime import UTC, datetime, timedelta
from decimal import ROUND_FLOOR, Decimal
from pathlib import Path

P = Path(r"C:\w9\evidence\live160\stage_steps.json")
steps = json.loads(P.read_text(encoding="utf-8"))
if "l10_run" in steps or "h164_release_hold" in steps:
    raise SystemExit("L10 is already there")
TRIAL_DIR = r"<projects>\.shared-oxylabs-trial-20261103"
sys.path.insert(0, TRIAL_DIR)
import oxytrial_ledger as otl  # noqa: E402

status = otl.open_ledger(TRIAL_DIR, "oxylabs-trial-20261103").summary()
left = Decimal(status["projects"]["walmart"]["spendable_in_envelope_usd"])
RESERVE, RATE = Decimal("0.030"), Decimal("0.0015")
MAX_REQ = int(((left - RESERVE) / RATE).to_integral_value(rounding=ROUND_FLOOR))
MAX_REQ = min(MAX_REQ, 700)
if MAX_REQ < 50:
    raise SystemExit(f"only {left} left in the envelope: no census")
max_usd = (RATE * MAX_REQ).quantize(Decimal("0.001"))
ED = Path(r"C:\w9\live\ed\walmart-oxylabs-1.6.4")
REV = json.loads((ED / "BUILD_INFO.json").read_text(encoding="utf-8"))["commit"]
ZIP_SHA = Path(r"C:\w9\live\dist\WALMART_OXYLABS_SOURCE_1.6.4.zip.sha256").read_text(encoding="utf-8").split()[0]
STORE = "walmart-3891-pickup"
CFG = r"C:\w9\evidence\live160\configs\collector.census_164.yaml"
cfg_sha = hashlib.sha256(Path(CFG).read_bytes()).hexdigest()
STAGE = "W-L10-census-continued-164-20261104"
deadline = (datetime.now(UTC) + timedelta(hours=3)).replace(microsecond=0).isoformat()
run_args = [
    "run", "--store", STORE, "--provider", "oxylabs", "--categories", "1,2,3,4,5,6,7,8,9,10",
    "--subcategory", "1:/browse/home-improvement/bidets/1072864_1045879_5533759_6108305",
    "--max-pages-per-listing", "1", "--pilot-no-detail", "--follow-up-pages", "0", "--workers", "2",
    "--max-credits", str(MAX_REQ), "--max-minutes", "150",
]
common = {"edition": "1.6.4", "config": CFG}
HOLD_REASON = (
    "Hold of 2026-11-04 12:19Z after run 01M6K7HT3XVV8R8CX79P31KMB4 (release 1.6.3, L7 census) stopped with "
    "ABNORMAL_RESULT: the Household Essentials link 'Bidets' "
    "(/browse/home-improvement/bidets/1072864_1045879_5533759_6108305, fetch 01M6K7Z4E1EMC2ZYJW0F7VA458, raw answer "
    "reviewed offline) reports 0 Pickup results for store 3891 (aggregatedCount 0, empty result grid, page location "
    "3891/60085/PICKUP) beside an 'Available for shipping' carousel of 10 products. Not a site refusal and not "
    "another store: release 1.6.3 took the reported 0 for a missing total; release 1.6.4 reads it and records the "
    "listing EMPTY. Released by the delivery's engineer for the L10 census continuation on 1.6.4."
)
steps.update(
    {
        "h164_validate_config": {**common, "args": ["validate-config", "--check-db", "--require-credentials"],
                                 "expected": 0},
        "h164_status_held": {**common, "args": ["status", "--limit", "3"], "expected": 0},
        "h164_release_hold": {**common, "args": ["release-hold", "--store", STORE, "--reason", HOLD_REASON],
                              "expected": 0},
        "h164_status_released": {**common, "args": ["status", "--limit", "3"], "expected": 0},
        "l10_validate_config": {**common, "args": ["validate-config", "--check-db", "--require-credentials"],
                               "expected": 0},
        "l10_trial_open": {
            "kind": "trial_open",
            "stage": {
                "stage_id": STAGE,
                "project": "walmart",
                "objective": "W4/W5 census continued as funded on release 1.6.4: the Household Essentials "
                "listing Bidets (where L7 stopped on 1.6.3: the 1.6.4 correction seen live), then every listing the "
                "category pages of rows 2 to 10 name today (the client's exclusions applied), page 1 of each, no "
                "product detail and no follow-up page; today's roots, reported totals and first-page identities; "
                "never published",
                "command": "walmart-collector " + " ".join(run_args),
                "config": {
                    "edition": "oxylabs 1.6.4",
                    "zip_sha256": ZIP_SHA,
                    "stage_config": CFG,
                    "stage_config_sha256": cfg_sha,
                    "workers": 2,
                },
                "source_revision": REV,
                "max_requests": MAX_REQ,
                "max_results": MAX_REQ,
                "max_usd": str(max_usd),
                "deadline_utc": deadline,
                "retry_policy": "the collector's: at most 3 submissions per request; 408, 429 and 5xx retried with "
                "backoff and jitter; Retry-After honoured up to 60 s; every submission is a new reservation",
                "stop_conditions": "a store check fails; a block or challenge; the gate, the ceiling, the credit or "
                "time budget or the deadline refuses; repeated pages; any unexpected exit",
            },
        },
        "l10_ceiling": {
            **common,
            "args": [
                "set-ceiling", "--provider", "oxylabs", "--submissions", str(MAX_REQ), "--usd", str(max_usd),
                "--minutes", "150", "--usd-per-result", str(RATE), "--basis",
                f"Campaign oxylabs-trial-20261103 (shared with Mariano's; USD 5 total), stage {STAGE} on release "
                f"1.6.4 ({REV[:7]}): {MAX_REQ} submissions (USD {max_usd} at the reserve rate {RATE}): Walmart's "
                f"envelope had USD {left} left, less a reserve of USD {RESERVE}; rows 2 to 10 need an unknown number "
                "(page 1 of each listing their category pages name); the shared "
                "ledger reserves each submission again before it is sent",
            ],
            "expected": 0,
        },
        "l10_run": {**common, "args": run_args, "expected": -1, "run_stage": "L10", "trial_stage": STAGE},
    }
)
P.write_text(json.dumps(steps, indent=1) + "\n", encoding="utf-8")
print(json.dumps({"left_usd": str(left), "max_requests": MAX_REQ, "max_usd": str(max_usd), "deadline": deadline,
                  "revision": REV, "config_sha256": cfg_sha}))
