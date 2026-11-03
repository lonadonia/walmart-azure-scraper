"""The assemble spec of the Walmart 1.5.1 delivery folder (offline; reads files, writes one JSON).

python -I -X utf8 assemble_spec_151.py DELIVERY_FOLDER SPEC.json

Each delivered path is named with its source and that source's SHA-256, and the builder's `assemble` refuses a source
that differs. The product files are the runs' exports, byte for byte: RUN_SUMMARY.json lists their hashes, and this
script refuses a staged copy that differs from that list.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

STAGE = Path(r"C:\w7\stage151")
PLAN = Path(r"C:\w7\plan")
PACK = Path(r"C:\w7\pack151")
REC = Path(r"C:\w7\evidence\reconciliation_151")
REPLAY = Path(r"C:\w7\evidence\reprocessing_b3_1_5_1")

TOP_FROM_STAGE = (
    "DELIVERY_INDEX.md", "CLIENT_SUMMARY.pdf", "<client-message draft>", "ACCEPTANCE_MATRIX.csv", "ACCEPTANCE_RUNBOOK.md",
    "VIDEO_STORYBOARD.md", "CLASSIC_TEST_PLAN.md", "COST_AND_RUNTIME_REPORT.md", "LINKED_EXAMPLES.csv",
    "THIRD_PARTY_LICENSES.csv", "SOURCE_AND_RUN_MANIFEST.json", "live/RUN_SUMMARY.json",
    "offline_reprocessing/README.txt",
)  # fmt: skip


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(delivery: str, out: Path) -> int:
    files: dict[str, Path] = {name: STAGE / name for name in TOP_FROM_STAGE}
    files["CAMPAIGN_BUDGET.json"] = PLAN / "CAMPAIGN_BUDGET.json"
    files["TEST_PLAN.md"] = PLAN / "TEST_PLAN_150.md"
    for name in ("COVERAGE_RECONCILIATION", "SPONSORED_AND_VARIANT_RECONCILIATION", "FOLLOW_UP_QUEUE_RECONCILIATION"):
        files[f"{name}.csv"] = REC / f"{name}_1_5_1.csv"
    files["WALMART_SOURCE_1.5.1.zip"] = PACK / "source" / "WALMART_SOURCE_1.5.1.zip"
    files["WALMART_EVIDENCE_1.5.1.zip"] = PACK / "evidence" / "WALMART_EVIDENCE_1.5.1.zip"
    files["OXYLABS_CLASSIC_OFFLINE_PROBE_1.5.0.zip"] = PACK / "probe" / "OXYLABS_CLASSIC_OFFLINE_PROBE_1.5.0.zip"
    for x in ("json", "csv"):
        files[f"offline_reprocessing/products_fresh_OFFLINE_REPROCESSING.{x}"] = REPLAY / "export_replay_1_5_1" / f"products_fresh.{x}"
        files[f"offline_reprocessing/products_retained_OFFLINE_REPROCESSING.{x}"] = REPLAY / "export_replay_1_5_1" / f"products.{x}"
    for name in ("B3_CORRECTION_MAP.csv", "B3_FIELD_DISPOSITIONS_662.csv", "B3_FIELD_DISPOSITIONS_662.json"):
        files[f"offline_reprocessing/{name}"] = REPLAY / "reconciliation" / name

    summary = json.loads((STAGE / "live" / "RUN_SUMMARY.json").read_text(encoding="utf-8"))
    problems: list[str] = []
    for stage in summary["stages"]:
        for name, info in stage["delivered_files"].items():
            source = STAGE / name
            want = info["sha256"] if isinstance(info, dict) else info
            if not source.is_file():
                problems.append(f"{name}: not staged")
            elif sha256(source) != want:
                problems.append(f"{name}: differs from RUN_SUMMARY.json")
            files[name] = source
    for name, source in files.items():
        if not source.is_file():
            problems.append(f"{name}: source {source} missing")
    if problems:
        raise SystemExit("\n".join(problems))
    spec = {
        "delivery": delivery,
        "files": {name: {"from": str(source), "sha256": sha256(source)} for name, source in sorted(files.items())},
    }
    out.write_text(json.dumps(spec, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{out}: {len(files)} files for {delivery}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], Path(sys.argv[2])))
