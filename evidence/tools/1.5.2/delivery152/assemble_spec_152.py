"""The assemble spec of the Walmart 1.5.2 delivery folder (offline; reads files, writes one JSON).

python -I -X utf8 assemble_spec_152.py DELIVERY_FOLDER SPEC.json

Each delivered path is named with its source and that source's SHA-256, and the builder's `assemble` refuses a source that
differs. The live files, CAMPAIGN_BUDGET.json, FOLLOW_UP_QUEUE_RECONCILIATION.csv and THIRD_PARTY_LICENSES.csv come from the
1.5.1 delivery itself, byte for byte. This script refuses a live file that differs from live/RUN_SUMMARY.json, and an
offline product file that differs from the replay's export.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

# A rehearsal only: OVERLAY152 names a folder whose files stand in for stage files that do not exist yet, and EVZIP152 an
# evidence ZIP built elsewhere. The final spec is made with neither set.
OVERLAY = Path(os.environ["OVERLAY152"]) if os.environ.get("OVERLAY152") else None
STAGE = Path(r"C:\w7\stage152")
EV = Path(r"C:\w7\ev152")
OLD = Path(r"<repository>\deliverables\20261101_walmart_1.5.1")
PACK = Path(r"C:\w7\pack152f")
A1 = EV / "final_a1" / "runs" / "S6" / "exports"
B3 = EV / "final_b3" / "export_replay_1_5_2"
MAPS = EV / "correction_maps_final"
B3MAPS = MAPS / "b3_1_4_1_to_1_5_2"
REC = EV / "reconciliation"
AZ = STAGE / "azure_docker_recovery"

TOP_FROM_STAGE = (
    "DELIVERY_INDEX.md", "CLIENT_SUMMARY.pdf", "<client-message draft>", "ACCEPTANCE_MATRIX.csv", "ACCEPTANCE_RUNBOOK.md",
    "TECHNICAL_REPORT.md", "TEST_PLAN.md", "CLASSIC_TEST_PLAN.md", "CLIENT_AZURE_ACCESS_REQUEST.md",
    "COST_AND_RUNTIME_REPORT.md", "LINKED_EXAMPLES.csv", "COVERAGE_RECONCILIATION.csv", "SOURCE_AND_RUN_MANIFEST.json",
    "offline_reprocessing/README.txt", "azure_docker_recovery/README.txt", "azure_docker_recovery/DOCKER_VM_RESULT.json",
    "WALKTHROUGH_1.5.2.mp4", "WALKTHROUGH_1.5.2.cast",
)  # fmt: skip
FROM_OLD = (
    "CAMPAIGN_BUDGET.json", "FOLLOW_UP_QUEUE_RECONCILIATION.csv", "THIRD_PARTY_LICENSES.csv", "live/RUN_SUMMARY.json",
)  # fmt: skip


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(delivery: str, out: Path) -> int:
    files: dict[str, Path] = {name: STAGE / name for name in TOP_FROM_STAGE}
    if OVERLAY:
        for name in TOP_FROM_STAGE:
            if not files[name].is_file() and (OVERLAY / name).is_file():
                files[name] = OVERLAY / name
    for name in FROM_OLD:
        files[name] = OLD / name
    files["WALMART_SOURCE_1.5.2.zip"] = PACK / "src" / "WALMART_SOURCE_1.5.2.zip"
    files["WALMART_EVIDENCE_1.5.2.zip"] = Path(os.environ.get("EVZIP152") or PACK / "evidence" / "WALMART_EVIDENCE_1.5.2.zip")
    # Rebuilt 2026-11-02 from the same revision: pack152f/probe holds the ZIP the VM tested, with the workstation's name.
    files["OXYLABS_CLASSIC_OFFLINE_PROBE_1.5.2.zip"] = Path("C:/w7/pack152g/probe/OXYLABS_CLASSIC_OFFLINE_PROBE_1.5.2.zip")
    files["SPONSORED_AND_VARIANT_RECONCILIATION.csv"] = REC / "SPONSORED_AND_VARIANT_RECONCILIATION_1_5_2.csv"
    files["EXACT_LIVE_READ_QUEUE.csv"] = REC / "EXACT_LIVE_READ_QUEUE_1_5_2.csv"
    o = "offline_reprocessing"
    for x in ("json", "csv"):
        files[f"{o}/S6_products_fresh_OFFLINE_REPLAY.{x}"] = A1 / f"products_fresh.{x}"
        files[f"{o}/S6_products_retained_OFFLINE_REPLAY.{x}"] = A1 / f"products.{x}"
        files[f"{o}/S6_field_dispositions_OFFLINE_REPLAY.{x}"] = A1 / f"field_dispositions.{x}"
        files[f"{o}/B3_products_fresh_OFFLINE_REPROCESSING.{x}"] = B3 / f"products_fresh.{x}"
        files[f"{o}/B3_products_retained_OFFLINE_REPROCESSING.{x}"] = B3 / f"products.{x}"
        files[f"{o}/B3_field_dispositions_OFFLINE_REPROCESSING.{x}"] = B3 / f"field_dispositions.{x}"
        files[f"{o}/B3_FIELD_DISPOSITIONS_662.{x}"] = B3MAPS / f"B3_FIELD_DISPOSITIONS_662.{x}"
    files[f"{o}/S6_CORRECTION_MAP.csv"] = MAPS / "S6_CORRECTION_MAP.csv"
    files[f"{o}/S6_CORRECTION_SUMMARY.json"] = MAPS / "S6_CORRECTION_SUMMARY.json"
    files[f"{o}/B3_CORRECTION_MAP.csv"] = B3MAPS / "B3_CORRECTION_MAP.csv"
    files[f"{o}/B3_1_5_1_TO_1_5_2_CORRECTION_MAP.csv"] = MAPS / "B3_1_5_1_TO_1_5_2_CORRECTION_MAP.csv"

    summary = json.loads((OLD / "live" / "RUN_SUMMARY.json").read_text(encoding="utf-8"))
    problems: list[str] = []
    for stage in summary["stages"]:
        for name, info in stage["delivered_files"].items():
            source = OLD / name
            want = info["sha256"] if isinstance(info, dict) else info
            if not source.is_file():
                problems.append(f"{name}: not in the 1.5.1 delivery")
            elif sha256(source) != want:
                problems.append(f"{name}: differs from RUN_SUMMARY.json")
            files[name] = source
    for name, source in files.items():
        if not source.is_file():
            problems.append(f"{name}: source {source} missing")
    for az in (AZ, *((OVERLAY / "azure_docker_recovery",) if OVERLAY else ())):
        extra = sorted(p.relative_to(az).as_posix() for p in az.rglob("*") if p.is_file()) if az.is_dir() else []
        for rel in extra:
            files.setdefault(f"azure_docker_recovery/{rel}", az / rel)
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
