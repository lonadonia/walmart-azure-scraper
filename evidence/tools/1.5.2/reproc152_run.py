"""OFFLINE REPLAY of the 1.5.0/1.5.1 live campaign's runs by release 1.5.2, in the order the campaign ran them,
so each run's replay carries the replayed rows of the runs before it (retention.verified_local: a replayed
LIVE run counts through its replay, and history stops where the source run started).

The source of truth is the campaign's stored pages. Nothing here touches the campaign's own database or data:
it works on a copy of both (C:/w7/r152 and, for the same-version repeat, C:/w7/r152b), and the original exports
under C:/w7/evidence/live150 are read only by the comparison tools.

Every step is a `walmart-collector` command of the worktree's committed release, run with:
  WALMART_COLLECTOR_DATABASE_URL  the local copy (pgserver, no password)
  WALMART_COLLECTOR_DATA_DIR      the copy of the campaign's data
  no provider key variable at all, so a provider request could not authenticate
  HTTP_PROXY/HTTPS_PROXY/ALL_PROXY a closed local port, so any HTTP request would fail
The output of each step goes to OUT/logs/<nn>_<label>.jsonl and one row of commands.csv. A step's log is never
overwritten. The script stops at the first unexpected exit.

usage: <worktree venv python> -I reproc152_run.py WORK OUT
  WORK  C:/w7/r152 (pgdata, data)    OUT  a new evidence folder
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
RUNS = json.loads(Path(r"C:\w7\evidence\live150\runs.json").read_text("utf-8"))
ORDER = ("S1", "S2", "S3", "S4", "S5b_serial", "S5b_parallel", "S5a", "S6", "S7")
DB = "walmart_live150"
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


class Steps:
    def __init__(self, out: Path, env: dict[str, str]) -> None:
        self.out, self.env = out, env
        self.logs = out / "logs"
        self.logs.mkdir(parents=True, exist_ok=False)
        self.n = 0
        self.table = (out / "commands.csv").open("w", newline="", encoding="utf-8")
        self.w = csv.writer(self.table, lineterminator="\n")
        self.w.writerow(
            ["step", "label", "utc_start", "utc_end", "seconds", "command", "exit_code", "expected", "log"]
        )

    def run(self, label: str, args: list[str], expected: int = 0) -> Path:
        self.n += 1
        log = self.logs / f"{self.n:03d}_{label}.jsonl"
        if log.exists():
            raise SystemExit(f"{log} exists: a step's log is never overwritten")
        start = datetime.now(UTC)
        t0 = time.monotonic()
        with log.open("wb") as f:
            rc = subprocess.run(
                [str(CLI), *args], cwd=PROJECT, env=self.env, stdout=f, stderr=subprocess.STDOUT, check=False
            ).returncode
        secs = round(time.monotonic() - t0, 1)
        cmd = "walmart-collector " + " ".join(a if " " not in a else f'"{a}"' for a in args)
        self.w.writerow(
            [self.n, label, start.isoformat(timespec="seconds"), datetime.now(UTC).isoformat(timespec="seconds"),
             secs, cmd, rc, expected, log.name]
        )
        self.table.flush()
        print(f"step {self.n} {label}: exit {rc} (expected {expected}) in {secs} s", flush=True)
        if expected != -1 and rc != expected:
            raise SystemExit(f"unexpected exit at step {self.n} {label}")
        return log


def db_url(pgdata: Path) -> str:
    import pgserver
    from sqlalchemy.engine import make_url

    srv = pgserver.get_server(str(pgdata), cleanup_mode=None)
    return make_url(srv.get_uri()).set(database=DB).render_as_string(hide_password=False)


def main() -> int:
    work, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=False)
    env = {k: v for k, v in os.environ.items() if k not in NO_KEYS and not k.upper().endswith("_PROXY")}
    env.update(
        {
            "WALMART_COLLECTOR_DATABASE_URL": db_url(work / "pgdata"),
            "WALMART_COLLECTOR_DATA_DIR": str(work / "data"),
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
    s = Steps(out, env)
    s.run("validate_config_before_upgrade", ["validate-config", "--check-db"], -1)
    s.run("db_upgrade", ["db-upgrade"])
    s.run("validate_config_after_upgrade", ["validate-config", "--check-db"])
    s.run("status_before", ["status", "--limit", "20"])
    replays: dict[str, str] = {}
    for stage in ORDER:
        src = RUNS[stage]
        log = s.run(f"replay_{stage}", ["replay", "--run", src], -1)
        text = log.read_text(encoding="utf-8", errors="replace")
        ids = [i for i in dict.fromkeys(re.findall(r'"run(?:_id)?": ?"(01[0-9A-Z]{24})"', text)) if i != src]
        if not ids:
            raise SystemExit(f"{stage}: no replay run id in {log}")
        rp = ids[0]
        replays[stage] = rp
        (out / "replay_runs.json").write_text(json.dumps(replays, indent=1), encoding="utf-8")
        base = out / "runs" / stage
        s.run(f"status_{stage}", ["status", "--run", rp])
        s.run(f"validate_export_{stage}", ["validate-export", "--run", rp], -1)
        s.run(f"export_{stage}", ["export", "--run", rp, "--out", str(base / "exports")])
        s.run(
            f"field_dispositions_{stage}",
            ["field-dispositions", "--run", rp, "--csv", str(base / f"field_dispositions_{rp}.csv")],
        )
        s.run(f"coverage_{stage}", ["coverage-report", "--run", rp, "--out", str(base / "coverage")])
    s.run("status_after", ["status", "--limit", "30"])
    s.run("follow_ups_all", ["follow-ups", "--store", "walmart-3891-pickup", "--state", "all"])
    print("replays", json.dumps(replays))
    return 0


if __name__ == "__main__":
    sys.exit(main())
