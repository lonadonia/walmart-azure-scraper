"""Stage L2b on the final revision 1.6.1 (W3): the 98 seeds of the 1.5.2 exact live-read queue on Bath & Body (row 2) and Diapering (row 4),
read first by the variant follow-up, with page 1 of each of the two listings (the follow-ups need the listings
read in the same run); no product detail page (a pilot: blank UPCs and sizes are recorded as not attempted).

Sizing: robots 1 + store page 1 + 2 listing pages + at most 100 variant pages (98 seeds first) + at most 100
sponsored pages (in practice the sponsored-only tiles of two page 1s, about 20): about 125 results; the ceiling and
the stage allow 130. One worker (the serial half of the concurrency comparison; L2 used two).
"""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

P = Path(r"C:\w9\evidence\live160\stage_steps.json")
steps = json.loads(P.read_text(encoding="utf-8"))
if "l2b_run" in steps:
    raise SystemExit("L2b is already there")
REV = json.loads(Path(r"C:\w9\live\ed\walmart-oxylabs-1.6.1\BUILD_INFO.json").read_text(encoding="utf-8"))["commit"]
ZIP_SHA = Path(r"C:\w9\live\dist\WALMART_OXYLABS_SOURCE_1.6.1.zip.sha256").read_text(encoding="utf-8").split()[0]
STORE = "walmart-3891-pickup"
CFG = r"C:\w9\evidence\live160\configs\collector.l2b_161.yaml"
cfg_sha = hashlib.sha256(Path(CFG).read_bytes()).hexdigest()
STAGE = "W-L2b-queue-seeds-161-20261103"
MAX_REQ, RATE = 130, "0.0015"
deadline = (datetime.now(UTC) + timedelta(hours=2)).replace(microsecond=0).isoformat()
run_args = [
    "run", "--store", STORE, "--provider", "oxylabs", "--categories", "2,4",
    "--subcategory", "2:/browse/personal-care/1005862_1071969",
    "--max-pages-per-listing", "1", "--pilot-no-detail", "--follow-up-pages", "100", "--workers", "1",
    "--max-credits", str(MAX_REQ), "--max-minutes", "120",
]
steps.update(
    {
        "l2b_trial_open": {
            "kind": "trial_open",
            "stage": {
                "stage_id": STAGE,
                "project": "walmart",
                "objective": "W3: read the 98 seeds of the 1.5.2 exact live-read queue on Bath & Body and Diapering "
                "(their own pages, by the variant follow-up, after page 1 of each listing) and decide each one; no "
                "product detail page; one worker",
                "command": "walmart-collector " + " ".join(run_args),
                "config": {
                    "edition": "oxylabs 1.6.1",
                    "zip_sha256": ZIP_SHA,
                    "stage_config": CFG,
                    "stage_config_sha256": cfg_sha,
                    "workers": 1,
                },
                "source_revision": REV,
                "max_requests": MAX_REQ,
                "max_results": MAX_REQ,
                "max_usd": "0.195",
                "deadline_utc": deadline,
                "retry_policy": "the collector's: at most 3 submissions per request; 408, 429 and 5xx retried with "
                "backoff and jitter; Retry-After honoured up to 60 s; every submission is a new reservation",
                "stop_conditions": "a store check fails; a block or challenge; the gate, the ceiling, the credit or "
                "time budget or the deadline refuses; repeated pages; any unexpected exit",
            },
        },
        "l2b_ceiling": {
            "edition": "1.6.1",
            "config": CFG,
            "args": [
                "set-ceiling", "--provider", "oxylabs", "--submissions", str(MAX_REQ), "--usd", "0.195",
                "--minutes", "120", "--usd-per-result", RATE, "--basis",
                f"Campaign oxylabs-trial-20261103 (shared with Mariano's; USD 5 total), stage {STAGE} on release "
                f"1.6.1 ({REV[:7]}): {MAX_REQ} submissions (USD 0.195 at the reserve rate 0.0015), 120 minutes, "
                "counted from this setting; about 125 needed; the shared ledger reserves each submission again "
                "before it is sent",
            ],
            "expected": 0,
        },
        "l2b_run": {
            "edition": "1.6.1",
            "args": run_args,
            "config": CFG,
            "expected": -1,
            "run_stage": "L2b",
            "trial_stage": STAGE,
        },
    }
)
P.write_text(json.dumps(steps, indent=1) + "\n", encoding="utf-8")
print("L2b added; deadline", deadline, "config", cfg_sha)
