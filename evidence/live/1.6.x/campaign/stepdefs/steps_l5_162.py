"""Stage L5 on the final revision 1.6.2 (W5 stage 3 on the final revision, the repeat of L3, and W6 recovery): the
store's hold after the 1.6.1 census stop is released first with its reason (no request), then the >= 500 fresh
demonstration runs again on the frozen 1.6.2 build, with the scope of L3 (the six L2 listings, at most 3 result pages
each), detail extraction active (production mode: every exported product missing a UPC or a size gets its own page,
or an earlier read within 30 days), and the recovery path: a graceful pause, a refused overlapping run while the
paused run is unfinished, a forced kill, and resumes to the end. It repeats L3's scope a day later, so it is also the
recurring-run measurement: what a second run of the same scope costs when earlier reads are reused.

Sizing: 3 executions x 2 workers x (robots + store page) = 12, 18 listing pages, and the product pages no read of
the last 30 days answers for (L2 and L3 read these listings' products on 2026-11-03): about 35 to 60 results. Ceiling
70 submissions (USD 0.105 at the reserve rate).
"""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

P = Path(r"C:\w9\evidence\live160\stage_steps.json")
steps = json.loads(P.read_text(encoding="utf-8"))
if "l5_run" in steps or "h162_release_hold" in steps:
    raise SystemExit("L5 is already there")
ED = Path(r"C:\w9\live\ed\walmart-oxylabs-1.6.2")
REV_ID = json.loads((ED / "BUILD_INFO.json").read_text(encoding="utf-8"))["commit"]
ZIP_SHA = Path(r"C:\w9\live\dist\WALMART_OXYLABS_SOURCE_1.6.2.zip.sha256").read_text(encoding="utf-8").split()[0]
STORE = "walmart-3891-pickup"
CFG = r"C:\w9\evidence\live160\configs\collector.l5_162.yaml"
cfg_sha = hashlib.sha256(Path(CFG).read_bytes()).hexdigest()
STAGE = "W-L5-final-demo-162-20261104"
MAX_REQ, RATE, MAX_USD = 70, "0.0015", "0.105"
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
HOLD_REASON = (
    "Hold of 2026-11-03 19:11Z after run 01M6HCZXM0WGMRCFDTCNZ7218K (release 1.6.1, census pilot) stopped with "
    "ABNORMAL_RESULT: the Food navigation link 'Fresh Flowers' (/browse/food/flowers/976759_1089004_2424807) served "
    "Walmart's category page 'Flower Shop' (/cp/flower-shop/5098771: links, no result grid; stored page "
    "01M6HD4YPXT7MS40NNRJDS3BCR reviewed). Not a block, not another store: release 1.6.2 records such a listing as "
    "CATEGORY_PAGE and goes on. Released by the delivery's engineer for the 1.6.2 stages of campaign "
    "oxylabs-trial-20261103."
)
common = {"edition": "1.6.2", "config": CFG}
steps.update(
    {
        "h162_validate_config": {**common, "args": ["validate-config", "--check-db", "--require-credentials"],
                                 "expected": 0},
        "h162_status_held": {**common, "args": ["status", "--limit", "3"], "expected": 0},
        "h162_release_hold": {**common, "args": ["release-hold", "--store", STORE, "--reason", HOLD_REASON],
                              "expected": 0},
        "h162_status_released": {**common, "args": ["status", "--limit", "3"], "expected": 0},
        "l5_trial_open": {
            "kind": "trial_open",
            "stage": {
                "stage_id": STAGE,
                "project": "walmart",
                "objective": "W5 stage 3 on the final revision 1.6.2, the repeat of L3 (recurring-run cost) and W6: "
                ">= 500 fresh valid products from the six L2 listings (3 pages each) with detail extraction active "
                "and new-versus-reused field evidence; a graceful pause, a refused overlapping run, a forced kill and "
                "resumes to the end",
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
        "l5_ceiling": {
            **common,
            "args": [
                "set-ceiling", "--provider", "oxylabs", "--submissions", str(MAX_REQ), "--usd", MAX_USD,
                "--minutes", "120", "--usd-per-result", RATE, "--basis",
                f"Campaign oxylabs-trial-20261103 (shared with Mariano's; USD 5 total), stage {STAGE} on release "
                f"1.6.2 ({REV_ID[:7]}): {MAX_REQ} submissions (USD {MAX_USD} at the reserve rate 0.0015), 120 "
                "minutes, counted from this setting; about 35 to 60 needed; the shared ledger reserves each "
                "submission again before it is sent",
            ],
            "expected": 0,
        },
        "l5_run": {**common, "args": run_args, "expected": -1, "run_stage": "L5", "trial_stage": STAGE,
                   "pause_after_s": 45},
        "l5_status_paused": {**common, "args": ["status", "--limit", "3"], "expected": 0},
        "l5_overlap_refused": {**common, "args": overlap_args, "expected": 9, "trial_stage": STAGE},
    }
)
P.write_text(json.dumps(steps, indent=1) + "\n", encoding="utf-8")
print("L5 added; revision", REV_ID, "zip", ZIP_SHA, "deadline", deadline, "config", cfg_sha)
