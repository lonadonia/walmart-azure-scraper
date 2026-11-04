"""Staged, bounded live qualification of Walmart release 1.6.0 (the handoff of 2026-11-03, W5), on the frozen revision
56f078efce4df3b40165dbeafcfe49e6c6f581eb as built by deploy/build_edition.py into WALMART_OXYLABS_SOURCE_1.6.0.zip
(SHA-256 5a70e4616c8a37875103787323e99943a74237024bcf58ee2322c17a1da1febd), extracted under C:/w9/live/ed and
installed from its lock (uv sync --frozen).

Every step is a `walmart-collector` command of that installed edition, run in its own process with:
  WALMART_COLLECTOR_DATABASE_URL  the isolated campaign database (a copy of C:/w7/live/pgdata at C:/w9/live/pgdata)
  WALMART_COLLECTOR_DATA_DIR      C:/w9/live/data (a copy of C:/w7/live/data)
  WALMART_COLLECTOR_CONFIG        the edition's config/collector.yaml, or a stage's copy (named per step)
  OXYLABS_WEB_API_KEY_FILE        the owner's Oxylabs Web API key file (read by the collector's load_key() only;
                                  never printed: the collector logs a fingerprint)
  no Scrape.do key, no proxy variable
and, in that process, the collector's account-wide gate (OxylabsTransport.account_gate_factory, release 1.6.0) set
to the shared trial ledger (<projects>/.shared-oxylabs-trial-20261103, campaign oxylabs-trial-20261103, project
walmart): every Oxylabs submission is reserved there at its worst case and marked dispatched before it is sent, then
settled or held as unknown. The process holds the campaign's exclusive lease (renewed every 30 s, 120 s TTL), so a
killed step's lease expires and its rows are recovered by the ledger (never-dispatched: released; dispatched: unknown).

Steps are defined in C:/w9/evidence/live160/stage_steps.json:
  {label: {"args": [...], "expected": n (-1: any), "config": path|null, "run_stage": "L1"|null,
           "trial_stage": stage_id|null, "kill_after_s": seconds|null, "pause_after_s": seconds|null}}
(kill_after_s: a forced kill of the step's process tree, taskkill /F /T; pause_after_s: a graceful Ctrl+Break, which
the collector handles as a termination signal (run left interrupted, exit 75), with a forced kill only if the process
has not ended PAUSE_GRACE_S later; the commands table records which, and when)
and two parent-only kinds: {"kind": "trial_open", "stage": {...open_stage keywords...}} and
{"kind": "trial_close", "stage_id": ..., "outcome": ...}.
Each step's output goes to C:/w9/evidence/live160/logs/<nn>_<label>.jsonl and one row of commands.csv. A step's log
is never overwritten; the script stops at the first unexpected exit.

usage: python -I live160_run.py STEP_LABEL [STEP_LABEL...]
"""

from __future__ import annotations

import csv
import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

EDITIONS = {  # a step names its edition ("edition"); 1.6.0 when it names none (every step before 1.6.1)
    "1.6.0": Path(r"C:\w9\live\ed\walmart-oxylabs-1.6.0"),
    "1.6.1": Path(r"C:\w9\live\ed\walmart-oxylabs-1.6.1"),
}
PROJECT = EDITIONS["1.6.0"]
PYTHON = PROJECT / ".venv" / "Scripts" / "python.exe"
OUT = Path(r"C:\w9\evidence\live160")
LOGS = OUT / "logs"
PGDATA = Path(r"C:\w9\live\pgdata")
DB = "walmart_live150"
DATA_DIR = r"C:\w9\live\data"
CONFIG = str(PROJECT / "config" / "collector.yaml")
KEY_FILE = r"<projects>\marianos-scraper\data\local\oxylabs.env"
TRIAL_DIR = r"<projects>\.shared-oxylabs-trial-20261103"
CAMPAIGN = "oxylabs-trial-20261103"
PROJECT_NAME = "walmart"
LEASE_TTL_S = 120.0
LEASE_RENEW_S = 30.0
PAUSE_GRACE_S = 600.0
DROP = (
    "SCRAPEDO_API_KEY",
    "SCRAPEDO_API_KEY_FILE",
    "OXYLABS_WEB_API_KEY",
    "OXYLABS_API_KEY",
    "OXYLABS_USERNAME",
    "OXYLABS_PASSWORD",
)
RUNS = OUT / "runs.json"


def trial() -> Any:
    sys.path.insert(0, TRIAL_DIR)
    import oxytrial_ledger as otl  # the shared ledger: stdlib only

    return otl


def runs() -> dict[str, str]:
    return json.loads(RUNS.read_text(encoding="utf-8")) if RUNS.is_file() else {}


def steps() -> dict[str, dict[str, Any]]:
    p = OUT / "stage_steps.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def db_url() -> str:
    import pgserver
    from sqlalchemy.engine import make_url

    srv = pgserver.get_server(str(PGDATA), cleanup_mode=None)
    return make_url(srv.get_uri()).set(database=DB).render_as_string(hide_password=False)


# -- the child: one collector command with the gate --------------------------------------------------------------


class TrialGate:
    """The collector's AccountGate over the shared trial ledger (one lease for the process)."""

    def __init__(self, otl: Any, ledger: Any, lease: Any, stage_id: str) -> None:
        self.otl, self.ledger, self.lease, self.stage_id = otl, ledger, lease, stage_id

    def reserve(self, *, purpose: str, endpoint: str, target_url: str, attempt: int, usd: float, key: str) -> str:
        from walmart_headless.acquisition.oxylabs import GateRefused

        try:
            return str(
                self.ledger.reserve(
                    self.lease,
                    stage_id=self.stage_id,
                    purpose=f"{purpose} (attempt {attempt})",
                    endpoint=endpoint,
                    target=target_url,
                    worst_results=1,
                    worst_usd=str(Decimal(str(usd))),
                    dispatch_key=f"{self.stage_id}:{key}",
                )
            )
        except self.otl.LedgerError as exc:
            raise GateRefused(str(exc)) from None

    def dispatched(self, ref: str) -> None:
        self.ledger.mark_dispatched(self.lease, ref)

    def unsent(self, ref: str, reason: str) -> None:
        self.ledger.release_unsent(self.lease, ref, reason=reason)

    def settled(self, ref: str, *, status: int, kind: str | None, charged: bool | None, usd: float) -> None:
        if charged is True:
            self.ledger.settle(
                ref,
                results=1,
                usd_amount=str(Decimal(str(usd))),
                kind="rule_estimate",
                basis="an answer with a page: one result at the reservation rate USD 0.0015 (the price page's "
                "highest non-AI row, a list price; not an invoice)",
                http_status=status,
            )
        elif charged is False:
            self.ledger.settle(
                ref,
                results=0,
                usd_amount="0",
                kind="documented_free",
                basis=f"{kind}: documented by Oxylabs as not charged (Web API Troubleshooting)",
                http_status=status,
            )
        else:
            self.ledger.mark_unknown(ref, reason=f"HTTP {status} {kind}: the charge is not known", http_status=status)

    def unknown(self, ref: str, reason: str) -> None:
        self.ledger.mark_unknown(ref, reason=reason)


def child(label: str) -> int:
    spec = steps()[label]
    stage_id = spec.get("trial_stage")
    if spec["args"] and spec["args"][0] in ("run", "resume") and not stage_id:
        # A run could reach the provider: never without the account-wide gate.
        print(json.dumps({"event": "TRIAL_GATE_MISSING", "message": f"{label}: no trial stage"}), flush=True)
        return 71
    print(json.dumps({"event": "HARNESS_EDITION", "edition": spec.get("edition", "1.6.0"),
                      "python": sys.executable}), flush=True)
    otl = trial()
    lease = None
    stop = threading.Event()
    ledger = None
    if stage_id:
        ledger = otl.open_ledger(TRIAL_DIR, CAMPAIGN)
        deadline = time.monotonic() + LEASE_TTL_S + 30
        while True:
            try:
                lease = ledger.acquire_lease(PROJECT_NAME, f"live160:{label}:{os.getpid()}", LEASE_TTL_S)
                break
            except otl.LedgerError as exc:
                if time.monotonic() > deadline:
                    print(json.dumps({"event": "TRIAL_LEASE_REFUSED", "message": str(exc)}), flush=True)
                    return 70
                time.sleep(5)

        def renew() -> None:
            while not stop.wait(LEASE_RENEW_S):
                try:
                    ledger.renew_lease(lease, LEASE_TTL_S)
                except Exception as exc:  # recorded; the gate refuses once the lease is gone
                    print(json.dumps({"event": "TRIAL_LEASE_RENEW_FAILED", "message": str(exc)}), flush=True)
                    return

        threading.Thread(target=renew, daemon=True).start()
        from walmart_headless.acquisition import oxylabs

        gate = TrialGate(otl, ledger, lease, stage_id)
        oxylabs.OxylabsTransport.account_gate_factory = lambda: gate
        print(json.dumps({"event": "TRIAL_GATE_SET", "stage": stage_id, "lease": lease.id}), flush=True)
    from walmart_headless import cli

    code = 1
    try:
        code = int(cli.main(list(spec["args"])) or 0)
    except SystemExit as exc:
        code = int(exc.code or 0) if isinstance(exc.code, int) else 1
    finally:
        stop.set()
        if lease is not None and ledger is not None:
            try:
                ledger.release_lease(lease, f"step {label} ended with exit code {code}")
            except Exception as exc:
                print(json.dumps({"event": "TRIAL_LEASE_RELEASE_FAILED", "message": str(exc)}), flush=True)
    return code


# -- the parent: the steps, their logs and the command table ------------------------------------------------------


def kill_tree(pid: int) -> None:
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True, check=False)


def parent(labels: list[str]) -> int:
    LOGS.mkdir(parents=True, exist_ok=True)
    env = {k: v for k, v in os.environ.items() if k not in DROP and not k.upper().endswith("_PROXY")}
    env.update(
        {
            "WALMART_COLLECTOR_DATABASE_URL": db_url(),
            "WALMART_COLLECTOR_DATA_DIR": DATA_DIR,
            "OXYLABS_WEB_API_KEY_FILE": KEY_FILE,
            "PSYCOPG_IMPL": "python",
            "PYTHONUTF8": "1",
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
                ["step", "label", "utc_start", "utc_end", "seconds", "command", "config", "trial_stage", "exit_code",
                 "expected", "killed_after_s", "log"]
            )
        for label in labels:
            all_steps = steps()
            if label not in all_steps:
                raise SystemExit(f"unknown step {label}")
            spec = all_steps[label]
            if list(LOGS.glob(f"*_{label}.jsonl")):
                raise SystemExit(f"a log of step {label} exists: a step's log is never overwritten")
            n += 1
            log = LOGS / f"{n:02d}_{label}.jsonl"
            start = datetime.now(UTC)
            t0 = time.monotonic()
            kind = spec.get("kind", "cli")
            killed: float | str = ""
            if kind in ("trial_open", "trial_close"):
                otl = trial()
                led = otl.open_ledger(TRIAL_DIR, CAMPAIGN)
                try:
                    if kind == "trial_open":
                        led.open_stage(**spec["stage"])
                        result = {"opened": spec["stage"]["stage_id"]}
                    else:
                        led.close_stage(spec["stage_id"], spec["outcome"])
                        result = {"closed": spec["stage_id"], "outcome": spec["outcome"]}
                    result["summary"] = led.summary()
                    rc = 0
                except otl.LedgerError as exc:
                    result, rc = {"refused": str(exc)}, 2
                log.write_text(json.dumps(result, default=str) + "\n", encoding="utf-8")
                cmd, config = f"trial ledger {kind}", ""
            else:
                ed = EDITIONS[spec.get("edition", "1.6.0")]
                config = spec.get("config") or str(ed / "config" / "collector.yaml")
                step_env = dict(env, WALMART_COLLECTOR_CONFIG=config)
                with log.open("wb") as fh:
                    proc = subprocess.Popen(
                        [str(ed / ".venv" / "Scripts" / "python.exe"), "-I", str(Path(__file__).resolve()),
                         "--child", label],
                        cwd=ed,
                        env=step_env,
                        stdout=fh,
                        stderr=subprocess.STDOUT,
                        # Its own process group: a Ctrl+Break reaches the step alone, never this harness.
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    )
                    kill_after = spec.get("kill_after_s")
                    pause_after = spec.get("pause_after_s")
                    limit = kill_after or pause_after
                    try:
                        rc = proc.wait(timeout=float(limit) if limit else None)
                    except subprocess.TimeoutExpired:
                        at = round(time.monotonic() - t0, 1)
                        if pause_after:
                            os.kill(proc.pid, signal.CTRL_BREAK_EVENT)
                            try:
                                rc = proc.wait(PAUSE_GRACE_S)
                                killed = f"ctrl_break@{at}s;ended@{round(time.monotonic() - t0, 1)}s"
                            except subprocess.TimeoutExpired:
                                kill_tree(proc.pid)
                                rc = proc.wait(60)
                                killed = f"ctrl_break@{at}s;not_ended;forced_kill@{round(time.monotonic() - t0, 1)}s"
                        else:
                            kill_tree(proc.pid)
                            rc = proc.wait(60)
                            killed = f"forced_kill@{at}s"
                cmd = "walmart-collector " + " ".join(a if " " not in a else f'"{a}"' for a in spec["args"])
            secs = round(time.monotonic() - t0, 1)
            expected = int(spec.get("expected", 0))
            w.writerow(
                [n, label, start.isoformat(timespec="seconds"), datetime.now(UTC).isoformat(timespec="seconds"), secs,
                 cmd, config, spec.get("trial_stage") or "", rc, expected, killed, str(log)]
            )
            f.flush()
            print(f"step {n} {label}: exit {rc} (expected {expected}) in {secs} s" + (f", {killed}" if killed else ""))
            stage = spec.get("run_stage")
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
    if len(sys.argv) >= 3 and sys.argv[1] == "--child":
        sys.exit(child(sys.argv[2]))
    sys.exit(parent(sys.argv[1:]))
