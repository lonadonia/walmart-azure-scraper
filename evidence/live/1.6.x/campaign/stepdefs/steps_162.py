"""Step definitions for the stages on release 1.6.2 (a copy of steps_161.py naming that edition), added to C:/w9/evidence/live160/stage_steps.json (each refuses a
label that already exists). The run of a stage is the one runs.json names for its run_stage label (L3, L2b, ...).

usage: python -I steps_162.py resume STAGE_LABEL STEP CONFIG_NAME TRIAL_STAGE WORKERS [KILL_AFTER_S]
       python -I steps_162.py status STEP CONFIG_NAME
       python -I steps_162.py after STAGE_LABEL PREFIX CONFIG_NAME
       python -I steps_162.py close STEP TRIAL_STAGE OUTCOME_TEXT_FILE

CONFIG_NAME is a file of C:/w9/evidence/live160/configs (collector.l3_161.yaml, ...). "after" adds PREFIX_status_final,
PREFIX_export, PREFIX_validate_export, PREFIX_field_dispositions, PREFIX_coverage_report and PREFIX_provider_balance
(read-only: no request but the provider-balance call, which the collector makes without a billable result).
"""

import json
import sys
from pathlib import Path

EDITION = "1.6.2"
P = Path(r"C:\w9\evidence\live160\stage_steps.json")
CONFIGS = Path(r"C:\w9\evidence\live160\configs")
OUT = Path(r"C:\w9\evidence\live160\runs")


def run_of(stage: str) -> str:
    return json.loads(Path(r"C:\w9\evidence\live160\runs.json").read_text(encoding="utf-8"))[stage]


def main(argv: list[str]) -> int:
    steps = json.loads(P.read_text(encoding="utf-8"))
    add: dict[str, dict] = {}
    if argv[0] == "resume" and len(argv) in (6, 7):
        stage, step, cfg, trial, workers = argv[1:6]
        spec = {
            "edition": EDITION,
            "config": str(CONFIGS / cfg),
            "args": ["resume", "--run", run_of(stage), "--workers", workers],
            "expected": -1,
            "run_stage": stage,
            "trial_stage": trial,
        }
        if len(argv) == 7:
            spec["kill_after_s"] = float(argv[6])
        add[step] = spec
    elif argv[0] == "status" and len(argv) == 3:
        add[argv[1]] = {"edition": EDITION, "config": str(CONFIGS / argv[2]), "args": ["status", "--limit", "3"],
                        "expected": 0}
    elif argv[0] == "after" and len(argv) == 4:
        stage, prefix, cfg = argv[1:4]
        run, out = run_of(stage), OUT / stage
        common = {"edition": EDITION, "config": str(CONFIGS / cfg)}
        add = {
            f"{prefix}_status_final": {**common, "args": ["status", "--limit", "3"], "expected": 0},
            f"{prefix}_export": {**common, "args": ["export", "--run", run, "--out", str(out / "exports")],
                                 "expected": -1},
            f"{prefix}_validate_export": {**common, "args": ["validate-export", "--run", run], "expected": -1},
            f"{prefix}_field_dispositions": {
                **common,
                "args": ["field-dispositions", "--run", run, "--csv", str(out / "field_dispositions.csv")],
                "expected": -1,
            },
            f"{prefix}_coverage_report": {
                **common, "args": ["coverage-report", "--run", run, "--out", str(out / "coverage")], "expected": -1
            },
            f"{prefix}_provider_balance": {**common, "args": ["provider-balance", "--provider", "oxylabs"],
                                           "expected": -1},
        }
    elif argv[0] == "close" and len(argv) == 4:
        step, trial, text_file = argv[1:4]
        outcome = Path(text_file).read_text(encoding="utf-8").strip()
        add[step] = {"kind": "trial_close", "stage_id": trial, "outcome": outcome}
    else:
        raise SystemExit(__doc__)
    clash = sorted(set(add) & set(steps))
    if clash:
        raise SystemExit(f"already there: {clash}")
    steps.update(add)
    P.write_text(json.dumps(steps, indent=1) + "\n", encoding="utf-8")
    print("added", ", ".join(add))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
