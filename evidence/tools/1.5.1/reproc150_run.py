"""Offline reprocessing of Oxylabs B3 (run 01M60V2DCCWR72BGVVG3EM9R74, release 1.4.1, commit 37ffca8) with
release 1.5.0 as committed (the replay run records the commit it ran), on the local copy of the VM's
walmart_oxylabs database and B3's stored pages (C:\\w7\\tools\\reproc150_setup.py: dump of
2026-10-31T20:26:48Z, SHA-256 61c6e346..., row counts equal to the VM's; 33 of 33 artifacts checked).

Saved product pages: C:\\w7\\b\\detail_capture_index_150.json (1,441 stored product pages of the delivered 1.4.1
edition evidence ZIPs, extracted under C:\\w7\\b; every source run LIVE with network lineage, store
walmart-3891-pickup). A replay counts only what was observed before the run it reads started (B3:
2026-10-28T08:47:16.914Z), within detail.reuse_days (30).

Every step is a `walmart-collector` command of the worktree's release, run with:
  WALMART_COLLECTOR_DATABASE_URL  the local restored database (pgserver, no password)
  WALMART_COLLECTOR_DATA_DIR      C:\\w7\\reproc\\data (B3's stored pages, SHA-256 checked)
  no provider key variable at all (removed from the environment: a provider request could not authenticate)
  HTTP_PROXY/HTTPS_PROXY/ALL_PROXY a closed local port (127.0.0.1:9): any HTTP request would fail
Each step's output goes to C:\\w7\\evidence\\reprocessing_b3\\logs\\<nn>_<label>.jsonl and one row of
commands.csv (UTC start and end, seconds, the command, the exit code). A step's exit code is checked against
the expected one (-1: recorded, any exit); the script stops at the first unexpected exit.

usage: python -I reproc150_run.py <first step number> [<last step number>]
"""

from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

PROJECT = Path(r"C:\w7\wt\headless\walmart-azure-headless")
CLI = PROJECT / ".venv" / "Scripts" / "walmart-collector.exe"
# Attempt 1 (commit 2489013, database walmart_reproc150, replay run 01M69TZZA4DA50PGYVCZ0CSYBG) completed; it
# filled "Fresh Navel Orange, Each" with 4 Pound from a page that declares that statement in "Each" (fixed in
# 7b6f325): its database is kept and its outputs are in C:\w7\evidence\reprocessing_b3_attempt1_parent_net_content.
# Attempt 2: REPROC_DB=walmart_reproc150_a2 REPROC_OUT=C:\w7\evidence\reprocessing_b3 on a new restore.
# Attempt 3 (release 1.5.1, commit 488a033): REPROC_DB=walmart_reproc151_a3 REPROC_OUT=C:\w7\evidence\reprocessing_b3_1_5_1 REPROC_EXPORT_NAME=export_replay_1_5_1 on a new restore.
OUT = Path(os.environ.get("REPROC_OUT", r"C:\w7\evidence\reprocessing_b3"))
LOGS = OUT / "logs"
PGDATA = Path(r"C:\w7\reproc\pgdata")
DB = os.environ.get("REPROC_DB", "walmart_reproc150")  # attempt 1: walmart_reproc150
DATA_DIR = r"C:\w7\reproc\data"
SOURCE = "01M60V2DCCWR72BGVVG3EM9R74"
STORE = "walmart-3891-pickup"
INDEX = r"C:\w7\b\detail_capture_index_150.json"
NO_KEYS = (
    "SCRAPEDO_API_KEY",
    "SCRAPEDO_API_KEY_FILE",
    "OXYLABS_WEB_API_KEY",
    "OXYLABS_WEB_API_KEY_FILE",
    "OXYLABS_API_KEY",
    "OXYLABS_USERNAME",
    "OXYLABS_PASSWORD",
)
CLOSED = "http://127.0.0.1:9"


def steps(replay_run: str | None) -> list[tuple[str, list[str], int]]:
    """(label, arguments, expected exit code), numbered from 1."""
    r = replay_run or "<replay run>"
    exports = str(OUT / os.environ.get("REPROC_EXPORT_NAME", "export_replay_1_5_0"))
    coverage = str(OUT / "coverage")
    return [
        ("validate_config_before_upgrade", ["validate-config", "--check-db"], -1),
        ("db_upgrade", ["db-upgrade"], 0),
        ("validate_config_after_upgrade", ["validate-config", "--check-db"], 0),
        ("status_before", ["status", "--limit", "10"], 0),
        ("field_dispositions_source_before", ["field-dispositions", "--run", SOURCE], -1),
        ("import_detail_captures", ["import-detail-captures", "--store", STORE, "--index", INDEX], 0),
        ("replay_b3", ["replay", "--run", SOURCE], -1),  # -1: recorded, any exit (the run's own outcome)
        ("status_replay", ["status", "--run", r], 0),
        ("validate_export_replay", ["validate-export", "--run", r], -1),
        ("export_replay", ["export", "--run", r, "--out", exports], 0),
        (
            "field_dispositions_replay",
            ["field-dispositions", "--run", r, "--csv", str(OUT / f"field_dispositions_{r}.csv")],
            0,
        ),
        ("coverage_replay", ["coverage-report", "--run", r, "--out", coverage], 0),
        ("follow_ups_detail", ["follow-ups", "--store", STORE, "--state", "all", "--kind", "detail"], 0),
        ("status_after", ["status", "--limit", "10"], 0),
        # Attempt 1: step 9 stopped on a stored page of 01M60F6GHNXCTZPJ6G1PRM7KW7 (the 200 carried records are
        # compared with their own runs' pages, not laid out yet); step 15 repeated it once they were.
        ("validate_export_replay_with_carried_pages", ["validate-export", "--run", r], -1),
        (
            "field_dispositions_source",
            ["field-dispositions", "--run", SOURCE, "--csv", str(OUT / f"field_dispositions_{SOURCE}.csv")],
            0,
        ),
        ("validate_export_source", ["validate-export", "--run", SOURCE], -1),
        ("coverage_source", ["coverage-report", "--run", SOURCE, "--out", coverage], 0),
    ]


def db_url() -> str:
    import pgserver
    from sqlalchemy.engine import make_url

    srv = pgserver.get_server(str(PGDATA), cleanup_mode=None)
    return make_url(srv.get_uri()).set(database=DB).render_as_string(hide_password=False)


def main() -> int:
    first = int(sys.argv[1])
    last = int(sys.argv[2]) if len(sys.argv) > 2 else first
    replay_file = OUT / "replay_run_id.txt"
    replay_run = replay_file.read_text().strip() if replay_file.is_file() else None
    LOGS.mkdir(parents=True, exist_ok=True)
    env = {k: v for k, v in os.environ.items() if k not in NO_KEYS and not k.upper().endswith("_PROXY")}
    env.update(
        {
            "WALMART_COLLECTOR_DATABASE_URL": db_url(),
            "WALMART_COLLECTOR_DATA_DIR": DATA_DIR,
            "WALMART_COLLECTOR_CONFIG": str(PROJECT / "config" / "collector.yaml"),
            "PSYCOPG_IMPL": "python",
            "HTTP_PROXY": CLOSED,
            "HTTPS_PROXY": CLOSED,
            "ALL_PROXY": CLOSED,
            "PATH": str(PROJECT / ".venv" / "Lib" / "site-packages" / "pgserver" / "pginstall" / "bin")
            + os.pathsep
            + env.get("PATH", ""),
        }
    )
    table = OUT / "commands.csv"
    new = not table.is_file()
    with table.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        if new:
            w.writerow(["step", "label", "utc_start", "utc_end", "seconds", "command", "exit_code", "expected", "log"])
        for n, (label, args, expected) in enumerate(steps(replay_run), start=1):
            if not first <= n <= last:
                continue
            if "<replay run>" in args or any("<replay run>" in a for a in args):
                raise SystemExit(f"step {n} needs the replay run id ({replay_file} not written yet)")
            log = LOGS / f"{n:02d}_{label}.jsonl"
            if log.exists():
                raise SystemExit(f"{log} exists: a step's log is never overwritten")
            start = datetime.now(UTC)
            t0 = time.monotonic()
            with log.open("wb") as out:
                rc = subprocess.run(
                    [str(CLI), *args], cwd=PROJECT, env=env, stdout=out, stderr=subprocess.STDOUT
                ).returncode
            secs = round(time.monotonic() - t0, 1)
            cmd = "walmart-collector " + " ".join(a if " " not in a else f'"{a}"' for a in args)
            w.writerow(
                [n, label, start.isoformat(timespec="seconds"), datetime.now(UTC).isoformat(timespec="seconds"),
                 secs, cmd, rc, expected, str(log)]
            )
            f.flush()
            print(f"step {n} {label}: exit {rc} (expected {expected}) in {secs} s")
            if label == "replay_b3":
                text = log.read_text(encoding="utf-8", errors="replace")
                ids = re.findall(r'"run(?:_id)?": ?"(01[0-9A-Z]{24})"', text)
                found = [i for i in dict.fromkeys(ids) if i != SOURCE]
                if found:
                    replay_file.write_text(found[0] + "\n", encoding="utf-8")
                    replay_run = found[0]
                    print("replay run", replay_run)
            if expected != -1 and rc != expected:
                print(f"unexpected exit at step {n}: stopping")
                return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
