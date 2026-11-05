"""The outer bound of a whole session (1.7.0, finding C2; corrected in 1.7.1).

A request's worker is killed and reaped at the request's own deadline (transport.py). This module bounds the
rest: a campaign session runs in its own process, and the supervisor kills it, with every process it started,
reaps it, and then recovers in its own process. Rows the session left reserved or sent are kept as unknown
(``Ledger.recover``: their reservations stay held), capture files are indexed or removed
(``CaptureStore.recover``), and an evidence manifest marked incomplete is written from the durable index.

1.7.1 (the client's review of 1.7.0, finding C2): in 1.7.0 the recovery ran after the session's end with no
bound of its own: a ledger lock held elsewhere kept it waiting 30 s and then raised, and a killed session that
could not be reaped raised out of the supervisor with nothing recovered. Now the supervisor's whole run ends
by the session's hard end:

- the session's command runs until the hard end less a reserve kept for the recovery
  (:func:`classic_probe.deadline.recovery_reserve`: a third of a short session, 30 s at most);
- its kill and its reap are each bounded by the time left. A process that has not gone when its reap's time
  runs out is recorded (``reaped``: False), and the recovery still runs;
- the recovery runs in its own process, which the supervisor kills if it is still running at the hard end.
  Inside it, every wait for the ledger's lock is bounded by the same end (``Ledger.bind_time_left``), so a
  lock held elsewhere ends the recovery's ledger writes, not the recovery: it writes the manifest of what it
  found and says what it could not do (``completed``: False, and why). A row it could not mark stays as the
  session left it, its money held, for the next recovery to mark. Nothing is assumed.

The supervisor is the bound for a future approved live session. This build's live mode stays disabled: the
tests run it against a stub on 127.0.0.1 only.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sqlite3
import subprocess
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from classic_probe import ledger as ledger_mod
from classic_probe.campaign import write_json
from classic_probe.captures import CaptureStore
from classic_probe.deadline import recovery_reserve

REAP_TIMEOUT_S = 10.0  # the longest a kill or a reap is waited for, when the session has that much time left
MIN_STEP_S = 0.05  # the shortest wait given to a kill or a reap
RECOVERY_MARGIN_S = 0.5  # the recovery's own end comes this long before the supervisor's end
RECOVERY_KILL_S = 0.25  # within that margin: the time to kill and reap a recovery that did not end by itself
FINAL_WRITE_S = 0.25  # the part of the recovery's time its ledger writes leave for writing the manifest
EVIDENCE = "campaign_evidence.json"
RECOVERED = "campaign_evidence.recovered.json"


@dataclass
class SupervisedSession:
    returncode: int | None
    killed: bool
    elapsed_s: float
    stdout_tail: str = ""
    recovery: dict[str, Any] = field(default_factory=dict)
    reaped: bool = True  # 1.7.1: False when the killed session had not gone when its reap's time ran out
    recovery_reserve_s: float = 0.0
    problems: list[str] = field(default_factory=list)


def _step(left: float) -> float:
    """How long a kill or a reap may take: a quarter of what is left, between MIN_STEP_S and
    REAP_TIMEOUT_S."""
    return max(MIN_STEP_S, min(REAP_TIMEOUT_S, left / 4))


def _kill_tree(proc: subprocess.Popen[bytes], seconds: float) -> list[str]:
    """The session and everything it started: a request worker must not outlive its session. Bounded by
    ``seconds`` (1.7.1); returns what did not work."""
    problems: list[str] = []
    if sys.platform == "win32":
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                capture_output=True,
                timeout=seconds,
                check=False,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            problems.append(f"taskkill did not finish in {seconds:.2f} s ({type(exc).__name__})")
        if proc.poll() is None:
            try:
                proc.kill()
            except OSError as exc:
                problems.append(f"the session's process could not be killed: {type(exc).__name__}")
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)  # the session leads its own process group
        except ProcessLookupError:
            pass
        except OSError as exc:
            problems.append(f"the session's process group could not be killed: {type(exc).__name__}")
    return problems


def _evidence_complete(path: Path, since_wall: float) -> bool:
    """The session wrote its own evidence manifest, after it started, and every capture in it was checked."""
    try:
        if path.stat().st_mtime < since_wall - 2.0:
            return False
        return json.loads(path.read_text(encoding="utf-8")).get("complete") is True
    except (OSError, ValueError, AttributeError):
        return False


def run_session(
    command: Sequence[str],
    *,
    hard_end_s: float,
    manifest: Path,
    out_dir: Path,
    retailer: str,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
    recovery_reserve_s: float | None = None,
) -> SupervisedSession:
    """Run one session's command so that all of it, its kill, its reap and its recovery included, ends
    ``hard_end_s`` seconds after it starts (1.7.1, C2). The command has the hard end less the recovery's
    reserve.

    A recovery runs when the session was killed, ended with an error, or left no complete evidence manifest of
    its own."""
    t0 = time.monotonic()
    since_wall = time.time()
    end = t0 + max(0.0, hard_end_s)
    reserve = (
        recovery_reserve(hard_end_s)
        if recovery_reserve_s is None
        else max(0.0, min(recovery_reserve_s, hard_end_s))
    )
    budget = max(0.0, hard_end_s - reserve)

    def left() -> float:
        return end - time.monotonic()

    proc = subprocess.Popen(
        list(command),
        cwd=cwd,
        env=None if env is None else dict(env),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=sys.platform != "win32",
    )
    killed, reaped = False, True
    problems: list[str] = []
    out = b""
    try:
        out, _ = proc.communicate(timeout=budget)
    except subprocess.TimeoutExpired:
        killed = True
        problems += _kill_tree(proc, _step(left()))
        try:
            out, _ = proc.communicate(timeout=_step(left()))
        except subprocess.TimeoutExpired:
            reaped = False
            problems.append(
                "the killed session had not exited when its reap's time ran out: it was not reaped, and the "
                "recovery ran without waiting for it"
            )
    returncode = proc.poll()
    session = SupervisedSession(
        returncode=returncode,
        killed=killed,
        elapsed_s=0.0,
        stdout_tail=(out or b"").decode("utf-8", "replace")[-4000:],
        reaped=reaped,
        recovery_reserve_s=round(reserve, 3),
        problems=problems,
    )
    evidence = Path(out_dir) / EVIDENCE
    if killed or returncode != 0 or not _evidence_complete(evidence, since_wall):
        if killed:
            reason = (
                f"killed by the supervisor {budget:.1f} s after its start, before the session's hard end "
                f"({hard_end_s:.1f} s): the last {reserve:.1f} s are kept for this recovery"
            )
        elif returncode != 0:
            reason = f"the session ended with exit code {returncode}"
        else:
            reason = "the session ended without a complete evidence manifest of its own"
        session.recovery = _recover_in_child(manifest, out_dir, retailer, reason=reason, seconds=left())
    session.elapsed_s = round(time.monotonic() - t0, 3)
    return session


def _recover_in_child(
    manifest: Path, out_dir: Path, retailer: str, *, reason: str, seconds: float
) -> dict[str, Any]:
    """The recovery in its own process, ended by ``seconds`` from now whatever happens in it (1.7.1, C2)."""
    if seconds <= RECOVERY_MARGIN_S:
        return {
            "completed": False,
            "ended_by": reason,
            "problems": [
                f"no time was left for a recovery before the session's end ({max(0.0, seconds):.2f} s): "
                "the rows and files stay as the session left them, their money held, for the next recovery"
            ],
        }
    until = time.time() + seconds - RECOVERY_MARGIN_S
    command = [
        sys.executable,
        "-I",
        "-m",
        "classic_probe.supervisor",
        "recover",
        os.fspath(Path(manifest).resolve()),
        os.fspath(Path(out_dir).resolve()),
        retailer,
        "--reason",
        reason,
        "--until",
        repr(until),
    ]
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        out, err = proc.communicate(timeout=max(MIN_STEP_S, seconds - RECOVERY_KILL_S))
    except subprocess.TimeoutExpired:
        proc.kill()
        try:
            proc.communicate(timeout=RECOVERY_KILL_S)
        except subprocess.TimeoutExpired:
            pass
        return {
            "completed": False,
            "ended_by": reason,
            "problems": [
                f"the recovery had not ended by the session's end and was killed after {seconds:.1f} s: what "
                "it wrote stays, and the next recovery completes it"
            ],
        }
    try:
        result = json.loads(out.decode("utf-8").strip().splitlines()[-1])
    except (ValueError, IndexError):
        result = None
    if not isinstance(result, dict):
        return {
            "completed": False,
            "ended_by": reason,
            "problems": [
                f"the recovery gave no readable result (exit code {proc.returncode}): "
                + err.decode("utf-8", "replace")[-500:]
            ],
        }
    return result


def recover_session(
    manifest: Path, out_dir: Path, retailer: str, *, reason: str, until: float | None = None
) -> dict[str, Any]:
    """After a session that did not end by itself: what it left, made safe and written down.

    ``until`` (seconds since the epoch; None: no bound) bounds all of it (1.7.1, C2): each wait for the
    ledger's lock ends by then, less the time kept to write the manifest. What could not be done is listed in
    ``problems`` and ``completed`` is False; a row not marked keeps its money held for the next recovery."""

    def time_left() -> float:
        return float("inf") if until is None else until - time.time()

    def ledger_time() -> float:
        return time_left() - FINAL_WRITE_S

    bound: Callable[[], float] | None = None if until is None else ledger_time
    problems: list[str] = []
    led = ledger_mod.open_from_manifest(manifest, time_left=bound)
    try:
        unfinished: int | None = None
        try:
            unfinished = led.recover()
        except ledger_mod.LockNotObtained as exc:
            problems.append(
                f"the rows left reserved or sent were not marked unknown ({exc}): they stay as the session "
                "left them, their money held, for the next recovery"
            )
        store = CaptureStore(out_dir, retailer)
        captures = store.recover(led, time_left=ledger_time, min_left_s=0.0)
        for item in captures["not_reached"]:
            problems.append(f"capture file {item['what']} not reached: {item['why']}")
        responses, checked = store.verify(led, time_left=ledger_time, min_left_s=0.0)
        if not checked:
            problems.append("not every capture was checked against its file before the session's end")
        data: dict[str, Any] = {
            "campaign_id": led.campaign_id,
            "ledger_genesis_id": led.genesis_id,
            "offline": led.offline,
            "complete": False,
            "ended_by": reason,
            "captures_checked": checked,
            "rows_recovered_as_unknown": unfinished,
            "capture_recovery": captures,
            "recovery_completed": not problems,
            "recovery_problems": problems,
        }
        try:
            data.update(
                totals=led.totals().as_dict(), dispatches=led.rows(), events=led.events(), responses=responses
            )
        except sqlite3.OperationalError as exc:
            problems.append(f"the ledger could not be read before the session's end: {exc}")
            data.update(responses=responses, recovery_completed=False)
        result: dict[str, Any] = {
            "completed": not problems,
            "ended_by": reason,
            "problems": problems,
            "rows_recovered_as_unknown": unfinished,
            "capture_recovery": captures,
        }
        if time_left() <= 0:
            problems.append("no time was left to write the recovered manifest")
            result["completed"] = False
            return result
        out_dir.mkdir(parents=True, exist_ok=True)
        write_json(out_dir / RECOVERED, data)
        result["manifest"] = RECOVERED
        return result
    finally:
        led.close()


def main(argv: Sequence[str] | None = None) -> int:
    """The supervisor's recovery in its own process (1.7.1), printing its result as one JSON line::

    python -I -m classic_probe.supervisor recover MANIFEST OUT_DIR RETAILER --reason TEXT --until EPOCH
    """
    parser = argparse.ArgumentParser(prog="classic_probe.supervisor")
    sub = parser.add_subparsers(dest="command", required=True)
    rec = sub.add_parser("recover", help="recover a session that did not end by itself (OFFLINE)")
    rec.add_argument("manifest", type=Path)
    rec.add_argument("out_dir", type=Path)
    rec.add_argument("retailer")
    rec.add_argument("--reason", required=True)
    rec.add_argument("--until", type=float, default=None)
    args = parser.parse_args(argv)
    try:
        result = recover_session(
            args.manifest, args.out_dir, args.retailer, reason=args.reason, until=args.until
        )
    except Exception as exc:  # noqa: BLE001 - reported to the supervisor, which records it
        print(
            json.dumps(
                {
                    "completed": False,
                    "ended_by": args.reason,
                    "problems": [f"the recovery failed: {type(exc).__name__}: {exc}"],
                }
            )
        )
        return 1
    print(json.dumps(result, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
