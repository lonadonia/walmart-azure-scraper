"""L1's read-only checks (no request) and the stage's close, added to C:/w9/evidence/live160/stage_steps.json."""

import json
from pathlib import Path

P = Path(r"C:\w9\evidence\live160\stage_steps.json")
steps = json.loads(P.read_text(encoding="utf-8"))
RUN = json.loads(Path(r"C:\w9\evidence\live160\runs.json").read_text(encoding="utf-8"))["L1"]
OUT = r"C:\w9\evidence\live160\runs\L1"
if "l1_export" in steps:
    raise SystemExit("already there")
steps.update(
    {
        "l1_export": {"args": ["export", "--run", RUN, "--out", OUT + r"\exports"], "expected": -1},
        "l1_validate_export": {"args": ["validate-export", "--run", RUN], "expected": -1},
        "l1_field_dispositions": {
            "args": ["field-dispositions", "--run", RUN, "--csv", OUT + r"\field_dispositions.csv"], "expected": -1
        },
        "l1_coverage_report": {"args": ["coverage-report", "--run", RUN, "--out", OUT + r"\coverage"], "expected": -1},
        "l1_provider_balance": {"args": ["provider-balance", "--provider", "oxylabs"], "expected": -1},
    }
)
P.write_text(json.dumps(steps, indent=1) + "\n", encoding="utf-8")
print("L1 checks added for run", RUN)
