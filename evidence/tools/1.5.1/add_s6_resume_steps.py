"""S6's steps after the forced kill: the state, the resume of the same run, the state after it, and the steps that record
the stage's outputs. No request here. usage: python -I add_s6_resume_steps.py RUN_ID"""

import json
import sys
from pathlib import Path

P = Path(r"C:\w7\evidence\live150\stage_steps.json")
run = sys.argv[1]
steps = json.loads(P.read_text(encoding="utf-8"))
config = steps["s6_run"]["config"]
new = {
    "s6_status_after_kill": (["status", "--limit", "3"], 0, None),
    "s6_resume": (["resume", "--run", run, "--workers", "1"], -1, None),
    "s6_status_after_resume": (["status", "--limit", "3"], 0, None),
}
for label, (args, expected, stage) in new.items():
    steps[label] = {"args": args, "expected": expected, "config": config, "run_stage": stage}
P.write_text(json.dumps(steps, indent=1) + "\n", encoding="utf-8")
print(sorted(k for k in steps if k.startswith("s6_")))
