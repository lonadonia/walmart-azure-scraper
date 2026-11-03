"""Staged, bounded live validation of Walmart release 1.5.0 (brief section 1A; C:/w7/plan/CAMPAIGN_BUDGET.json and
TEST_PLAN_150.md), on the frozen revision 7b6f3258e0f4ab755732605eb88717c592d07073 as built by
deploy/build_edition.py into WALMART_OXYLABS_SOURCE_1.5.0.zip (SHA-256 32abbc06aebcb6d611290597abba1ba7c2fc1d286996
e679ab63e89b94d0cce4), extracted under C:/w7/live/ed and installed from its lock (uv sync --frozen).

Stage S6 (amendment A1 of the budget) runs on release 1.5.1, on the edition LIVE150_EDITION names, built the same way:
that stage's rows in commands.csv name its configuration file, and so the edition. The stages before it stay as above.

Every step is a `walmart-collector` command of that installed edition, run with:
  WALMART_COLLECTOR_DATABASE_URL  the isolated campaign database (local PostgreSQL, pgserver, C:/w7/live/pgdata)
  WALMART_COLLECTOR_DATA_DIR      C:/w7/live/data
  WALMART_COLLECTOR_CONFIG        the edition's config/collector.yaml, or a stage's copy (named per step)
  OXYLABS_WEB_API_KEY_FILE        the owner's Oxylabs Web API key file (read by the collector's load_key() only;
                                  never printed: the collector logs a fingerprint)
  no Scrape.do key, no proxy variable
Each step's output goes to C:/w7/evidence/live150/logs/<nn>_<label>.jsonl and one row of commands.csv (UTC start
and end, seconds, the command, the exit code, the expected exit code). A step's log is never overwritten; the
script stops at the first unexpected exit. Run ids are kept in runs.json by stage label.

usage: python -I live150_run.py STEP_LABEL [STEP_LABEL...]
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

PROJECT = Path(os.environ.get("LIVE150_EDITION") or r"C:\w7\live\ed\walmart-oxylabs-1.5.0")
CLI = PROJECT / ".venv" / "Scripts" / "walmart-collector.exe"
OUT = Path(r"C:\w7\evidence\live150")
LOGS = OUT / "logs"
PGDATA = Path(r"C:\w7\live\pgdata")
DB = "walmart_live150"
DATA_DIR = r"C:\w7\live\data"
CONFIG = str(PROJECT / "config" / "collector.yaml")
KEY_FILE = r"<repository>\data\local\oxylabs.env"
STORE = "walmart-3891-pickup"
INDEX = r"C:\w7\b\detail_capture_index_150.json"
DROP = (
    "SCRAPEDO_API_KEY",
    "SCRAPEDO_API_KEY_FILE",
    "OXYLABS_WEB_API_KEY",
    "OXYLABS_API_KEY",
    "OXYLABS_USERNAME",
    "OXYLABS_PASSWORD",
)
RUNS = OUT / "runs.json"


def runs() -> dict[str, str]:
    return json.loads(RUNS.read_text(encoding="utf-8")) if RUNS.is_file() else {}


def steps() -> dict[str, tuple[list[str], int, str | None]]:
    """label -> (arguments, expected exit code (-1: any, recorded), configuration file or None)."""
    r = runs()
    out = str(OUT)
    S: dict[str, tuple[list[str], int, str | None]] = {
        "validate_config_before_upgrade": (["validate-config", "--check-db"], -1, None),
        "db_upgrade": (["db-upgrade"], 0, None),
        "validate_config_credentials": (["validate-config", "--check-db", "--require-credentials"], 0, None),
        "sync_config": (["sync-config"], 0, None),
        "import_detail_captures": (["import-detail-captures", "--store", STORE, "--index", INDEX], 0, None),
        "status_before": (["status", "--limit", "10"], 0, None),
        "follow_ups_before": (["follow-ups", "--store", STORE, "--state", "all"], 0, None),
    }
    for stage, run_id in r.items():
        base = f"{out}\\runs\\{stage}"
        S[f"{stage}_status"] = (["status", "--run", run_id], 0, None)
        S[f"{stage}_validate_export"] = (["validate-export", "--run", run_id], -1, None)
        S[f"{stage}_export"] = (["export", "--run", run_id, "--out", f"{base}\\exports"], 0, None)
        S[f"{stage}_field_dispositions"] = (
            ["field-dispositions", "--run", run_id, "--csv", f"{base}\\field_dispositions_{run_id}.csv"],
            0,
            None,
        )
        S[f"{stage}_coverage"] = (["coverage-report", "--run", run_id, "--out", f"{base}\\coverage"], 0, None)
        S[f"{stage}_follow_ups"] = (["follow-ups", "--store", STORE, "--state", "all"], 0, None)
    return S


def extra_steps() -> dict[str, tuple[list[str], int, str | None]]:
    """Stage steps written to C:/w7/evidence/live150/stage_steps.json before each stage (ceilings and runs):
    {label: {"args": [...], "expected": n, "config": path|null, "run_stage": "S1"|null}}."""
    p = OUT / "stage_steps.json"
    if not p.is_file():
        return {}
    d = json.loads(p.read_text(encoding="utf-8"))
    return {k: (v["args"], int(v["expected"]), v.get("config")) for k, v in d.items()}


def run_stage_of(label: str) -> str | None:
    p = OUT / "stage_steps.json"
    if not p.is_file():
        return None
    return (json.loads(p.read_text(encoding="utf-8")).get(label) or {}).get("run_stage")


def db_url() -> str:
    import pgserver
    from sqlalchemy.engine import make_url

    srv = pgserver.get_server(str(PGDATA), cleanup_mode=None)
    return make_url(srv.get_uri()).set(database=DB).render_as_string(hide_password=False)


def main() -> int:
    labels = sys.argv[1:]
    LOGS.mkdir(parents=True, exist_ok=True)
    env = {k: v for k, v in os.environ.items() if k not in DROP and not k.upper().endswith("_PROXY")}
    env.update(
        {
            "WALMART_COLLECTOR_DATABASE_URL": db_url(),
            "WALMART_COLLECTOR_DATA_DIR": DATA_DIR,
            "OXYLABS_WEB_API_KEY_FILE": KEY_FILE,
            "PSYCOPG_IMPL": "python",
            "PATH": str(PROJECT / ".venv" / "Lib" / "site-packages" / "pgserver" / "pginstall" / "bin")
            + os.pathsep
            + env.get("PATH", ""),
        }
    )
    table = OUT / "commands.csv"
    new = not table.is_file()
    n = len(list(LOGS.glob("*.jsonl")))
    with table.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        if new:
            w.writerow(
                ["step", "label", "utc_start", "utc_end", "seconds", "command", "config", "exit_code", "expected", "log"]
            )
        for label in labels:
            all_steps = {**steps(), **extra_steps()}
            if label not in all_steps:
                raise SystemExit(f"unknown step {label}")
            args, expected, config = all_steps[label]
            n += 1
            log = LOGS / f"{n:02d}_{label}.jsonl"
            if log.exists() or list(LOGS.glob(f"*_{label}.jsonl")):
                raise SystemExit(f"a log of step {label} exists: a step's log is never overwritten")
            step_env = dict(env, WALMART_COLLECTOR_CONFIG=config or CONFIG)
            start = datetime.now(UTC)
            t0 = time.monotonic()
            with log.open("wb") as fh:
                rc = subprocess.run([str(CLI), *args], cwd=PROJECT, env=step_env, stdout=fh, stderr=subprocess.STDOUT).returncode
            secs = round(time.monotonic() - t0, 1)
            cmd = "walmart-collector " + " ".join(a if " " not in a else f'"{a}"' for a in args)
            w.writerow(
                [n, label, start.isoformat(timespec="seconds"), datetime.now(UTC).isoformat(timespec="seconds"), secs,
                 cmd, config or ("edition config/collector.yaml" if "1.5.0" in CONFIG else CONFIG), rc, expected, str(log)]
            )
            f.flush()
            print(f"step {n} {label}: exit {rc} (expected {expected}) in {secs} s")
            stage = run_stage_of(label)
            if stage:
                text = log.read_text(encoding="utf-8", errors="replace")
                ids = re.findall(r'"run(?:_id)?": ?"(01[0-9A-Z]{24})"', text)
                if ids:
                    r = runs()
                    r.setdefault(stage, ids[0])
                    RUNS.write_text(json.dumps(r, indent=1) + "\n", encoding="utf-8")
                    print(f"{stage} run {r[stage]}")
            if expected != -1 and rc != expected:
                print(f"unexpected exit at step {label}: stopping")
                return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
