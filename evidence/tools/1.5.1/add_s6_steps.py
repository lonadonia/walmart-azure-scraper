"""Adds stage S6 (amendment A1 of C:/w7/plan/CAMPAIGN_BUDGET.json) to the campaign's stage_steps.json. No request."""
import json
from pathlib import Path

P = Path(r"C:\w7\evidence\live150\stage_steps.json")
CONFIG = r"C:\w7\live\ed\walmart-oxylabs-1.5.1\config\collector.yaml"

steps = json.loads(P.read_text(encoding="utf-8"))
if "s6_run" in steps:
    raise SystemExit("S6 is already there")
steps["s6_validate_config"] = {
    "args": ["validate-config", "--check-db", "--require-credentials"],
    "expected": 0,
    "config": CONFIG,
    "run_stage": None,
}
steps["s6_status_before"] = {"args": ["status", "--limit", "3"], "expected": 0, "config": CONFIG, "run_stage": None}
steps["s6_ceiling"] = {
    "args": [
        "set-ceiling", "--provider", "oxylabs", "--submissions", "22", "--usd", "0.033", "--minutes", "30",
        "--usd-per-result", "0.0015", "--basis",
        "Campaign walmart-1.5.0, amendment A1, stage S6 on release 1.5.1: the >=500 demonstration again, multipack "
        "weights and store_brand on live pages, reuse behind a page budget: 22 submissions (USD 0.033 at the reserve "
        "rate 0.0015), 30 minutes, counted from this setting (CAMPAIGN_BUDGET.json amendments A1); the campaign "
        "budget of USD 0.18 stays in force",
    ],
    "expected": 0,
    "config": CONFIG,
    "run_stage": None,
}
steps["s6_run"] = {
    "args": [
        "run", "--store", "walmart-3891-pickup", "--provider", "oxylabs", "--categories", "0,1,3,6,7",
        "--subcategory", "0:/browse/food/fresh-vegetables/976759_976793_8910423",
        "--subcategory", "1:/browse/laundry/1115193_1071967",
        "--subcategory", "3:/browse/hair-care/shampoo/1085666_3147628_5752434",
        "--subcategory", "6:/browse/health-medicine/shop-all-cold-cough-flu-medicine/976760_4661388_6244277_7158394",
        "--subcategory", "7:/browse/pets/dry-dog-food/5440_202072_6432755_1636265",
        "--max-pages-per-listing", "3", "--pilot-detail-pages", "3", "--follow-up-pages", "0", "--workers", "1",
        "--max-credits", "22", "--max-minutes", "30",
    ],
    "expected": -1,
    "config": CONFIG,
    "run_stage": "S6",
}
P.write_text(json.dumps(steps, indent=1) + "\n", encoding="utf-8")
print("S6 added:", [k for k in steps if k.startswith("s6_")])
