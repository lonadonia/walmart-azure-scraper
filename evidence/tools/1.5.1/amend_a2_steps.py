"""Amendment A2 of C:/w7/plan/CAMPAIGN_BUDGET.json, before any S6 request: S6 reads one product page and is killed and
resumed; S7 repeats a slice on the same revision at least 30 minutes after S6 ends. No request."""
import json
from pathlib import Path

P = Path(r"C:\w7\evidence\live150\stage_steps.json")
CONFIG = r"C:\w7\live\ed\walmart-oxylabs-1.5.1\config\collector.yaml"
RUN_PLACEHOLDER = "S6_RUN_ID"

logs = list(Path(r"C:\w7\evidence\live150\logs").glob("*_s6_*.jsonl"))
if logs:
    raise SystemExit(f"S6 has started ({logs}): it is not amended")
steps = json.loads(P.read_text(encoding="utf-8"))

run = steps["s6_run"]["args"]
run[run.index("--pilot-detail-pages") + 1] = "1"
run[run.index("--max-credits") + 1] = "23"
steps["s6_ceiling"]["args"][-1] = (
    "Campaign walmart-1.5.0, amendments A1 and A2, stage S6 on release 1.5.1: the >=500 demonstration again, multipack "
    "weights and store_brand on live pages, reuse behind a page budget, a forced kill and a resume: 22 submissions "
    "(USD 0.033 at the reserve rate 0.0015), 30 minutes, counted from this setting (CAMPAIGN_BUDGET.json amendments); "
    "the campaign budget of USD 0.18 stays in force"
)
steps["s7_ceiling"] = {
    "args": [
        "set-ceiling", "--provider", "oxylabs", "--submissions", "4", "--usd", "0.006", "--minutes", "10",
        "--usd-per-result", "0.0015", "--basis",
        "Campaign walmart-1.5.0, amendment A2, stage S7 on release 1.5.1: time-separated repeat of a small slice, at "
        "least 30 minutes after S6: 4 submissions (USD 0.006 at the reserve rate 0.0015), 10 minutes, counted from this "
        "setting (CAMPAIGN_BUDGET.json amendments); the campaign budget of USD 0.18 stays in force",
    ],
    "expected": 0,
    "config": CONFIG,
    "run_stage": None,
}
steps["s7_run"] = {
    "args": [
        "run", "--store", "walmart-3891-pickup", "--provider", "oxylabs", "--categories", "0",
        "--subcategory", "0:/browse/food/fresh-vegetables/976759_976793_8910423",
        "--max-pages-per-listing", "1", "--pilot-detail-pages", "1", "--follow-up-pages", "0", "--workers", "1",
        "--max-credits", "5", "--max-minutes", "10",
    ],
    "expected": -1,
    "config": CONFIG,
    "run_stage": "S7",
}
P.write_text(json.dumps(steps, indent=1) + "\n", encoding="utf-8")
print("amended:", " ".join(steps["s6_run"]["args"][-12:]))
print("added:", [k for k in steps if k.startswith("s7_")])
