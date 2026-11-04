"""The outer bound of a whole session (1.7.0, finding C2).

A request's worker is killed and reaped at the request's own deadline (transport.py). This module bounds the
rest: a campaign session runs in its own process, and the supervisor kills it, with every process it started,
at the session's hard end, reaps it, and then recovers in its own process. Rows the session left reserved or
sent are kept as unknown (``Ledger.recover``: their reservations stay held), capture files are indexed or
removed (``CaptureStore.recover``), and an evidence manifest marked incomplete is written from the durable
index. A wedged lock, a hung export or a stuck worker therefore cannot hold a session open past its end.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from classic_probe import ledger as ledger_mod
from classic_probe.campaign import write_json
from classic_probe.captures import CaptureStore

REAP_TIMEOUT_S = 10.0


@dataclass
class SupervisedSession:
    returncode: int | None
    killed: bool
    elapsed_s: float
    stdout_tail: str = ""
    recovery: dict[str, Any] = field(default_factory=dict)


def _kill_tree(proc: subprocess.Popen[bytes]) -> None:
    """The session and everything it started: a request worker must not outlive its session."""
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            capture_output=True,
            timeout=REAP_TIMEOUT_S,
            check=False,
        )
        if proc.poll() is None:
            proc.kill()
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)  # the session leads its own process group
        except ProcessLookupError:
            pass


def run_session(
    command: Sequence[str],
    *,
    hard_end_s: float,
    manifest: Path,
    out_dir: Path,
    retailer: str,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> SupervisedSession:
    """Run one session's command and kill it, with its children, ``hard_end_s`` seconds after it starts."""
    t0 = time.monotonic()
    proc = subprocess.Popen(
        list(command),
        cwd=cwd,
        env=None if env is None else dict(env),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=sys.platform != "win32",
    )
    killed = False
    try:
        out, _ = proc.communicate(timeout=max(0.0, hard_end_s))
    except subprocess.TimeoutExpired:
        killed = True
        _kill_tree(proc)
        out, _ = proc.communicate(timeout=REAP_TIMEOUT_S)
    session = SupervisedSession(
        returncode=proc.returncode,
        killed=killed,
        elapsed_s=round(time.monotonic() - t0, 3),
        stdout_tail=out.decode("utf-8", "replace")[-4000:],
    )
    if killed or proc.returncode not in (0, None):
        reason = (
            f"killed by the supervisor at the session's hard end ({hard_end_s:.1f} s)"
            if killed
            else f"the session ended with exit code {proc.returncode}"
        )
        session.recovery = recover_session(manifest, out_dir, retailer, reason=reason)
    return session


def recover_session(manifest: Path, out_dir: Path, retailer: str, *, reason: str) -> dict[str, Any]:
    """After a session that did not end by itself: what it left, made safe and written down."""
    led = ledger_mod.open_from_manifest(manifest)
    try:
        unfinished = led.recover()
        store = CaptureStore(out_dir, retailer)
        captures = store.recover(led)
        responses, checked = store.verify(led, time_left=lambda: float("inf"), min_left_s=0.0)
        data = {
            "campaign_id": led.campaign_id,
            "ledger_genesis_id": led.genesis_id,
            "offline": led.offline,
            "complete": False,
            "ended_by": reason,
            "captures_checked": checked,
            "rows_recovered_as_unknown": unfinished,
            "capture_recovery": captures,
            "totals": led.totals().as_dict(),
            "dispatches": led.rows(),
            "events": led.events(),
            "responses": responses,
        }
        out_dir.mkdir(parents=True, exist_ok=True)
        write_json(out_dir / "campaign_evidence.recovered.json", data)
        return {
            "rows_recovered_as_unknown": unfinished,
            "capture_recovery": captures,
            "manifest": "campaign_evidence.recovered.json",
        }
    finally:
        led.close()
