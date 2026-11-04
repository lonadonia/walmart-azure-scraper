"""Stage L7 on the final revision 1.6.3 (W4/W5 census as funded): the full scope of the store (all 11 CSV rows, every
listing their category pages name today, the client's exclusions applied by the collector), page 1 of each listing,
no product detail request and no follow-up page. It establishes, for today, what each row's category page names and
each listing's reported total and first-page identities; it is not the full catalogue (pages after the first are not
read) and it is never published: a bounded run is a pilot. With 1.6.3, product detail reading off still uses what
earlier reads of a product's own page established (no request), and carried rows get an empty UPC or size from such a
read. Release 1.6.1's census (L4) stopped at the category page "Fresh Flowers" served (1.6.2 records it and goes on);
1.6.2's L6 stopped at the site's not-found page (1.6.3 records it NOT_FOUND and goes on).

Sizing: the 2026-10-24 navigation named 628 listings to read (roots after the exclusions); with the 9 category pages,
the 2 configured listing rows and robots and the store page per worker and execution, about 645 results. The ceiling
is what the shared ledger leaves in Walmart's envelope when this is generated, less a reserve of USD 0.030 (unknown
outcomes), at the reserve rate 0.0015 per result. If the census needs more, the collector stops at the ceiling
(exit 4); the run is then finalized (no request) and its unread listings are the exact continuation.

usage: python -I steps_l7_163.py   (reads the shared ledger read-only; writes the L7 steps)
"""

import hashlib
import json
import sys
from datetime import UTC, datetime, timedelta
from decimal import ROUND_FLOOR, Decimal
from pathlib import Path

P = Path(r"C:\w9\evidence\live160\stage_steps.json")
steps = json.loads(P.read_text(encoding="utf-8"))
if "l7_run" in steps:
    raise SystemExit("L7 is already there")
TRIAL_DIR = r"<projects>\.shared-oxylabs-trial-20261103"
sys.path.insert(0, TRIAL_DIR)
import oxytrial_ledger as otl  # noqa: E402

status = otl.open_ledger(TRIAL_DIR, "oxylabs-trial-20261103").summary()
left = Decimal(status["projects"]["walmart"]["spendable_in_envelope_usd"])
RESERVE, RATE = Decimal("0.030"), Decimal("0.0015")
MAX_REQ = int(((left - RESERVE) / RATE).to_integral_value(rounding=ROUND_FLOOR))
MAX_REQ = min(MAX_REQ, 700)
if MAX_REQ < 100:
    raise SystemExit(f"only {left} left in the envelope: no census")
max_usd = (RATE * MAX_REQ).quantize(Decimal("0.001"))
ED = Path(r"C:\w9\live\ed\walmart-oxylabs-1.6.3")
REV = json.loads((ED / "BUILD_INFO.json").read_text(encoding="utf-8"))["commit"]
ZIP_SHA = Path(r"C:\w9\live\dist\WALMART_OXYLABS_SOURCE_1.6.3.zip.sha256").read_text(encoding="utf-8").split()[0]
STORE = "walmart-3891-pickup"
CFG = r"C:\w9\evidence\live160\configs\collector.census_163.yaml"
cfg_sha = hashlib.sha256(Path(CFG).read_bytes()).hexdigest()
STAGE = "W-L7-census-163-20261104"
deadline = (datetime.now(UTC) + timedelta(hours=3)).replace(microsecond=0).isoformat()
run_args = [
    "run", "--store", STORE, "--provider", "oxylabs",
    "--max-pages-per-listing", "1", "--pilot-no-detail", "--follow-up-pages", "0", "--workers", "2",
    "--max-credits", str(MAX_REQ), "--max-minutes", "150",
]
common = {"edition": "1.6.3", "config": CFG}
steps.update(
    {
        "l7_validate_config": {**common, "args": ["validate-config", "--check-db", "--require-credentials"],
                               "expected": 0},
        "l7_trial_open": {
            "kind": "trial_open",
            "stage": {
                "stage_id": STAGE,
                "project": "walmart",
                "objective": "W4/W5 census as funded on the final revision 1.6.3: every listing the 11 rows' "
                "category pages name today (the client's exclusions applied), page 1 of each, no product detail and "
                "no follow-up page; today's roots, reported totals and first-page identities; never published",
                "command": "walmart-collector " + " ".join(run_args),
                "config": {
                    "edition": "oxylabs 1.6.3",
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
        "l7_ceiling": {
            **common,
            "args": [
                "set-ceiling", "--provider", "oxylabs", "--submissions", str(MAX_REQ), "--usd", str(max_usd),
                "--minutes", "150", "--usd-per-result", str(RATE), "--basis",
                f"Campaign oxylabs-trial-20261103 (shared with Mariano's; USD 5 total), stage {STAGE} on release "
                f"1.6.3 ({REV[:7]}): {MAX_REQ} submissions (USD {max_usd} at the reserve rate {RATE}): Walmart's "
                f"envelope had USD {left} left, less a reserve of USD {RESERVE}; about 645 needed; the shared "
                "ledger reserves each submission again before it is sent",
            ],
            "expected": 0,
        },
        "l7_run": {**common, "args": run_args, "expected": -1, "run_stage": "L7", "trial_stage": STAGE},
    }
)
P.write_text(json.dumps(steps, indent=1) + "\n", encoding="utf-8")
print(json.dumps({"left_usd": str(left), "max_requests": MAX_REQ, "max_usd": str(max_usd), "deadline": deadline,
                  "revision": REV, "config_sha256": cfg_sha}))
