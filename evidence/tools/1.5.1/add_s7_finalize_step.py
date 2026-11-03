"""S7's closing steps after its pause at the ceiling: the state and a finalize of the same run, which makes no provider
request. usage: python -I add_s7_finalize_step.py RUN_ID"""

import json
import sys
from pathlib import Path

P = Path(r"C:\w7\evidence\live150\stage_steps.json")
run = sys.argv[1]
steps = json.loads(P.read_text(encoding="utf-8"))
config = steps["s7_run"]["config"]
new = {
    "s7_status_at_ceiling": (["status", "--limit", "2"], 0, None),
    "s7_finalize": (["finalize", "--run", run], -1, None),
}
for label, (args, expected, stage) in new.items():
    steps[label] = {"args": args, "expected": expected, "config": config, "run_stage": stage}
P.write_bytes((json.dumps(steps, indent=1) + "\n").encode("utf-8"))
print(sorted(k for k in steps if k.startswith("s7_")))
