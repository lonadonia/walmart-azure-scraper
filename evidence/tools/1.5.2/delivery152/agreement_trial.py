"""The verifier's own agreement function on the final replays, before the package exists. Reads only."""

import json
import sys
from pathlib import Path

sys.path.insert(0, "C:/w7/wt/scripts")
import verify_walmart_152_delivery as v  # noqa: E402

runs = json.loads(Path("C:/w7/evidence/live150/runs.json").read_text("utf-8"))
index = json.loads(Path("C:/w7/b/detail_capture_index_150.json").read_text("utf-8"))
earlier = {str(r["run_id"]) for r in index}
live = set(runs.values())
kinds, bad = v.agreement(Path("C:/w7/ev152/final_a1/runs/S6/exports"), runs["S6"], live, earlier)
print("S6", len(bad), bad[:6])
print(dict(sorted(kinds.items())))
copy = set(json.loads(Path("C:/w7/ev152/final_b3/RUNS_OF_THE_COPY.json").read_text("utf-8")))
kinds, bad = v.agreement(Path("C:/w7/ev152/final_b3/export_replay_1_5_2"), "01M60V2DCCWR72BGVVG3EM9R74", {"01M60V2DCCWR72BGVVG3EM9R74"} | copy, earlier)
print("B3", len(bad), bad[:6])
print(dict(sorted(kinds.items())))
