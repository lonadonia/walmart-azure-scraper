"""L2's read-only checks (no request), added to C:/w9/evidence/live160/stage_steps.json; the stage's close is added
after the checks are read (steps_l2_close.py)."""

import json
from pathlib import Path

P = Path(r"C:\w9\evidence\live160\stage_steps.json")
steps = json.loads(P.read_text(encoding="utf-8"))
RUN = json.loads(Path(r"C:\w9\evidence\live160\runs.json").read_text(encoding="utf-8"))["L2"]
OUT = r"C:\w9\evidence\live160\runs\L2"
CFG = r"C:\w9\evidence\live160\configs\collector.l2.yaml"
if "l2_export" in steps:
    raise SystemExit("already there")
steps.update(
    {
        "l2_status_final": {"args": ["status", "--limit", "3"], "config": CFG, "expected": 0},
        "l2_export": {"args": ["export", "--run", RUN, "--out", OUT + r"\exports"], "config": CFG, "expected": -1},
        "l2_validate_export": {"args": ["validate-export", "--run", RUN], "config": CFG, "expected": -1},
        "l2_field_dispositions": {
            "args": ["field-dispositions", "--run", RUN, "--csv", OUT + r"\field_dispositions.csv"],
            "config": CFG,
            "expected": -1,
        },
        "l2_coverage_report": {
            "args": ["coverage-report", "--run", RUN, "--out", OUT + r"\coverage"], "config": CFG, "expected": -1
        },
        "l2_provider_balance": {"args": ["provider-balance", "--provider", "oxylabs"], "config": CFG, "expected": -1},
    }
)
P.write_text(json.dumps(steps, indent=1) + "\n", encoding="utf-8")
print("L2 checks added for run", RUN)
