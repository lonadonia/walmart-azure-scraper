"""Offline steps on release 1.6.5 (no provider request), added to C:/w9/evidence/live160/stage_steps.json: the 1.6.5
edition validates the census configuration, and validate-export --run checks L10's export (run 01M6KA3CKYJSD6WDY4TDAAV73Y,
collected by release 1.6.4) again: the 22-field contract, the manifest and every export file from storage, and each
record against the stored pages with the 1.6.5 source check. The run's collection stays attributed to 1.6.4.

usage: python -I steps_165_offline.py
"""

import json
from pathlib import Path

P = Path(r"C:\w9\evidence\live160\stage_steps.json")
CFG = r"C:\w9\evidence\live160\configs\collector.census_164.yaml"
L10 = json.loads(Path(r"C:\w9\evidence\live160\runs.json").read_text(encoding="utf-8"))["L10"]
steps = json.loads(P.read_text(encoding="utf-8"))
add = {
    "h165_validate_config": {"edition": "1.6.5", "config": CFG, "args": ["validate-config"], "expected": 0},
    "h165_status": {"edition": "1.6.5", "config": CFG, "args": ["status", "--limit", "3"], "expected": 0},
    "l10_validate_export_165": {"edition": "1.6.5", "config": CFG, "args": ["validate-export", "--run", L10],
                                "expected": -1},
}
clash = sorted(set(add) & set(steps))
if clash:
    raise SystemExit(f"already there: {clash}")
steps.update(add)
P.write_text(json.dumps(steps, indent=1) + "\n", encoding="utf-8")
print("added", ", ".join(add), "for", L10)
