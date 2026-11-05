"""The publishable record of the 1.6.x live campaign (offline; no request): the harness that ran every live step (as it
is now, and as it was before each patch), the step generators and stage configurations, the step list, the runs, the
command log with each step's own log, and an extract of the shared trial ledger for Walmart: its envelopes, stages,
every reservation, and the event chain (lease tokens, hosts, process ids, the credential's fingerprint and location
withheld). Workstation paths are left for the publication's redaction step.

usage: python -I assemble_campaign_166.py OUT_DIR   (the harness backups before each patch, 1.6.1 to 1.6.6, and the
       note on the rebuilt before_163 backup)
"""

import csv
import hashlib
import json
import shutil
import sqlite3
import sys
from pathlib import Path

SRC = Path("C:/w9/evidence/live160")
LIVE = Path("C:/w9/live")
LOGS = Path("C:/w9/logs")
TRIAL = Path(r"<projects>\.shared-oxylabs-trial-20261103")
WITHHELD = "<withheld>"


def copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main(argv: list[str]) -> int:
    out = Path(argv[0])
    if out.exists():
        raise SystemExit(f"{out} exists")
    # the harness and its patches
    copy(LIVE / "live160_run.py", out / "harness" / "live160_run.py")
    for name in ("live160_run.before_161.py", "live160_run.before_162.py", "live160_run.before_163.py",
                 "live160_run.before_163.REBUILT.txt", "live160_run.before_164.py", "live160_run.before_165.py",
                 "live160_run.before_166.py"):
        if (LOGS / name).exists():
            copy(LOGS / name, out / "harness" / name)
    for p in sorted((LIVE / "stepdefs").glob("*.py")):
        copy(p, out / "stepdefs" / p.name)
    # the tools: Python and shell (the shell ones ran the 1.6.6 verification, Bicep, last-good and data steps)
    for p in sorted([*(LIVE / "tools").glob("*.py"), *(LIVE / "tools").glob("*.sh")]):
        copy(p, out / "tools" / p.name)
    # the steps, runs, commands and logs
    for name in ("stage_steps.json", "runs.json", "commands.csv"):
        copy(SRC / name, out / name)
    for p in sorted((SRC / "logs").iterdir()):
        copy(p, out / "logs" / p.name)
    for p in sorted((SRC / "configs").iterdir()):
        copy(p, out / "configs" / p.name)
    for p in sorted((SRC / "plan").iterdir()):
        copy(p, out / "plan" / p.name)
    for p in sorted((SRC / "runs").glob("*/*_CHECKS.json")):
        copy(p, out / "checks" / p.name)
    for p in sorted((SRC / "runs").glob("*/close_outcome.txt")):
        copy(p, out / "checks" / f"{p.parent.name}_close_outcome.txt")
    # the shared ledger, Walmart's part
    con = sqlite3.connect(f"file:{TRIAL / 'ledger.sqlite3'}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    led = out / "shared_ledger"
    led.mkdir(parents=True)

    def dump(name: str, sql: str, drop: tuple[str, ...] = ()) -> int:
        rows = [dict(r) for r in con.execute(sql)]
        for r in rows:
            for k in drop:
                if k in r:
                    r[k] = WITHHELD
        with (led / f"{name}.csv").open("w", newline="", encoding="utf-8") as f:
            if rows:
                w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
                w.writeheader()
                w.writerows(rows)
        return len(rows)

    counts = {
        "envelopes": dump("envelopes", "SELECT * FROM envelopes ORDER BY id"),
        "stages": dump("stages", "SELECT * FROM stages WHERE project='walmart' ORDER BY opened_at"),
        "reservations": dump(
            "reservations", "SELECT * FROM reservations WHERE project='walmart' ORDER BY created_at, id"
        ),
        "leases": dump("leases", "SELECT * FROM leases WHERE project='walmart' ORDER BY id", ("token", "host", "pid")),
    }
    events = []
    for r in con.execute("SELECT seq, at, kind, ref, detail, prev_hash, hash FROM events ORDER BY seq"):
        d = json.loads(r["detail"])
        if isinstance(d, dict):
            for k in ("credential_fingerprint", "credential_location", "token", "host", "pid"):
                if k in d:
                    d[k] = WITHHELD
        events.append({**dict(r), "detail": d})
    (led / "events.json").write_text(json.dumps(events, indent=1) + "\n", encoding="utf-8")
    counts["events"] = len(events)
    (led / "README.txt").write_text(
        "An extract of the shared trial ledger (campaign oxylabs-trial-20261103; Walmart and Mariano's share one USD 5 "
        "allowance) for Walmart: its envelopes, stages, every reservation (reserved before dispatch, then settled or "
        "unknown), its leases and the whole hash-chained event log. Withheld: lease tokens, the workstation's host "
        "name and process ids, and the credential's fingerprint and location (events.json keeps each event's "
        "original hash, so the chain cannot be recomputed from this extract; the private ledger verifies it: "
        "`oxytrial_ledger.py verify-chain`). Settlements of kind rule_estimate are the reserve rate (USD 0.0015 per "
        "result, a list price), not an invoice: the provider's dashboard balance is not readable by API.\n",
        encoding="utf-8",
    )
    manifest = []
    for p in sorted(out.rglob("*")):
        if p.is_file():
            manifest.append({"path": p.relative_to(out).as_posix(), "bytes": p.stat().st_size,
                             "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
    with (out / "CAMPAIGN_FILES.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["path", "bytes", "sha256"], lineterminator="\n")
        w.writeheader()
        w.writerows(manifest)
    print(json.dumps({"files": len(manifest), "ledger": counts}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
