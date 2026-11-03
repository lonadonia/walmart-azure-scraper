"""Every scheduled occurrence keeps its identity until it has been run (``schedule_occurrences``, revision
0006).

Until release 1.4.1 an occurrence existed only inside one firing: a firing past the start tolerance found
nothing due, a run still open meant the occurrence was skipped with a log line or a run event, and a hold
returned with no record at all. The requirement is the full scope twice a week per store, so a start that
could not happen has to stay visible and still be run.

Each firing calls :func:`register`. Every scheduled start that has passed since the last one known becomes a
row, whether or not a firing happened at its time (a machine that was off leaves a backlog, not a gap). The
oldest waiting occurrence is the next to start (:func:`next_waiting`), one at a time, so writes never overlap
(the store lock still guards the run itself). What could not start is marked :func:`defer` with the reason. An
occurrence still waiting at the next occurrence's start has missed its deadline: it is recorded and reported,
never dropped, and :func:`status` states the capacity gap when runs do not fit the cadence. Queuing alone does
not satisfy the cadence, and nothing here narrows what a run collects.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from walmart_headless.collection.config import Schedule
from walmart_headless.collection.schedule import Occurrence, local_day, next_occurrence, occurrence_on
from walmart_headless.core.timeutil import iso
from walmart_headless.db.models import Run, ScheduleOccurrence

DUE, DEFERRED, RUNNING, COMPLETED, SUPERSEDED = "due", "deferred", "running", "completed", "superseded"
WAITING = (DUE, DEFERRED)
# Run statuses after which a run writes nothing more.
RUN_FINISHED = ("validated", "rejected", "published", "cancelled")
EARLY = timedelta(minutes=5)  # a firing a little before the start time counts as on time


def rows_of(s: Session, store_id: str) -> list[ScheduleOccurrence]:
    return list(
        s.scalars(
            select(ScheduleOccurrence)
            .where(ScheduleOccurrence.store_id == store_id)
            .order_by(ScheduleOccurrence.due_at)
        )
    )


def register(
    s: Session, store_id: str, schedule: Schedule, tz: ZoneInfo, now: datetime
) -> list[ScheduleOccurrence]:
    """Give every start that has passed its row, settle finished runs, mark missed deadlines, and return the
    occurrences still waiting, oldest first. With no row yet, the count starts at ``schedule.start_date``, or
    without one at today: enabling a schedule creates no backlog of the days before it."""
    rows = rows_of(s, store_id)
    today = local_day(now + EARLY, tz)
    day = date.fromisoformat(rows[-1].day) + timedelta(days=1) if rows else schedule.start_date or today
    if schedule.start_date and day < schedule.start_date:
        day = schedule.start_date
    while day <= today:
        occ = occurrence_on(schedule, day, tz)
        if occ is not None and occ.start - EARLY <= now:
            rows.append(_new_row(s, store_id, occ, schedule, tz, now))
        day += timedelta(days=1)
    s.flush()
    settle(s, rows)
    waiting = [r for r in rows if r.state in WAITING]
    for r in waiting:
        if r.deadline_at is not None and r.deadline_missed_at is None and r.deadline_at <= now:
            r.deadline_missed_at = now
    return waiting


def _new_row(
    s: Session, store_id: str, occ: Occurrence, schedule: Schedule, tz: ZoneInfo, now: datetime
) -> ScheduleOccurrence:
    following = next_occurrence(schedule, occ.start, tz)
    row = ScheduleOccurrence(
        store_id=store_id,
        day=occ.day.isoformat(),
        due_at=occ.start,
        window=occ.as_dict(),
        state=DUE,
        noticed_at=now,
        deadline_at=following.start if following is not None else None,
    )
    s.add(row)
    return row


def settle(s: Session, rows: list[ScheduleOccurrence]) -> None:
    """An occurrence whose run has finished is completed (also when the execution ended before saying so)."""
    for r in rows:
        if r.state != RUNNING or r.run_id is None:
            continue
        run = s.get(Run, r.run_id)
        if run is None:  # its run is gone: it waits again, it is not dropped
            r.state, r.run_id, r.reason = DUE, None, "its run no longer exists"
        elif run.status in RUN_FINISHED:
            r.state = SUPERSEDED if run.stop_code == "SUPERSEDED" else COMPLETED
            r.finished_at = run.finished_at or r.finished_at


def occurrence_of(row: ScheduleOccurrence) -> Occurrence:
    """The occurrence as it was registered, even if the schedule has changed since."""
    w = row.window
    return Occurrence(
        date.fromisoformat(w["day"]),
        datetime.fromisoformat(w["start"]),
        datetime.fromisoformat(w["window_start"]),
        datetime.fromisoformat(w["window_end"]),
    )


def next_waiting(waiting: list[ScheduleOccurrence]) -> ScheduleOccurrence | None:
    return waiting[0] if waiting else None


def defer(rows: list[ScheduleOccurrence], reason: str) -> None:
    """These occurrences could not start now: each keeps waiting, with the reason."""
    for r in rows:
        r.state, r.reason = DEFERRED, reason


def started(row: ScheduleOccurrence, run_id: str, now: datetime) -> None:
    row.state, row.run_id, row.reason = RUNNING, run_id, None
    if row.started_at is None:
        row.started_at = now


def finished(s: Session, store_id: str, run_id: str, now: datetime) -> None:
    """The occurrence of a run that has just ended, when the run really finished (an interrupted run goes
    on)."""
    run = s.get(Run, run_id)
    if run is None or run.status not in RUN_FINISHED:
        return
    for r in s.scalars(
        select(ScheduleOccurrence).where(
            ScheduleOccurrence.store_id == store_id,
            ScheduleOccurrence.run_id == run_id,
            ScheduleOccurrence.state == RUNNING,
        )
    ):
        r.state = SUPERSEDED if run.stop_code == "SUPERSEDED" else COMPLETED
        r.finished_at = run.finished_at or now


def lateness_minutes(row: ScheduleOccurrence, now: datetime) -> float:
    """How long after its scheduled start the occurrence started, or has waited so far."""
    return round(((row.started_at or now) - row.due_at).total_seconds() / 60, 1)


def as_dict(row: ScheduleOccurrence, now: datetime) -> dict[str, Any]:
    return {
        "occurrence": row.day,
        "state": row.state,
        "due_at": iso(row.due_at),
        "noticed_at": iso(row.noticed_at),
        "run_id": row.run_id,
        "started_at": iso(row.started_at) if row.started_at else None,
        "finished_at": iso(row.finished_at) if row.finished_at else None,
        "lateness_minutes": lateness_minutes(row, now),
        "deadline_at": iso(row.deadline_at) if row.deadline_at else None,
        "deadline_missed_at": iso(row.deadline_missed_at) if row.deadline_missed_at else None,
        "reason": row.reason,
    }


def status(
    s: Session, store_id: str, schedule: Schedule, tz: ZoneInfo, now: datetime, *, enabled: bool
) -> dict[str, Any]:
    """The store's occurrences, backlog and capacity gap (``schedule-status``). The gap compares the measured
    time between a run's scheduled start and its end with the interval to the next start. No measured
    full-scope run means the capacity is unknown, and it is reported as unknown."""
    rows = rows_of(s, store_id)
    settle(s, rows)
    waiting = [r for r in rows if r.state in WAITING]
    done = [
        r for r in rows if r.state == COMPLETED and r.finished_at is not None and r.started_at is not None
    ]
    # Only a run that collected its full scope measures the time the cadence needs.
    measured = [
        r
        for r in done
        if (run := s.get(Run, r.run_id or "")) is not None and (run.counts or {}).get("collection_complete")
    ]
    gaps = []
    for r in done:
        if r.deadline_at is not None and r.finished_at is not None and r.finished_at > r.deadline_at:
            gaps.append(
                {
                    "occurrence": r.day,
                    "finished_at": iso(r.finished_at),
                    "next_start": iso(r.deadline_at),
                    "over_by_minutes": round((r.finished_at - r.deadline_at).total_seconds() / 60, 1),
                }
            )
    missed = [r.day for r in rows if r.deadline_missed_at is not None]
    if gaps or missed:
        capacity = (
            f"GAP: {len(gaps)} run(s) ended after the next start and {len(missed)} occurrence(s) missed "
            "their deadline. Queuing keeps them but does not meet the cadence: the required scope and "
            "cadence stand, so more capacity (parallel workers, provider throughput) is needed"
        )
    elif not measured:
        capacity = (
            "UNKNOWN: no scheduled run of this store has collected its full scope, so the runtime is "
            "not measured"
        )
    else:
        capacity = "NO GAP MEASURED: every finished scheduled run ended before the next start"
    return {
        "schedule_enabled": enabled,
        "occurrences": [
            {**as_dict(r, now), "run_status": run.status if (run := s.get(Run, r.run_id or "")) else None}
            for r in rows
        ],
        "waiting": [r.day for r in waiting],
        "backlog": len(waiting),
        "oldest_waiting_minutes": lateness_minutes(waiting[0], now) if waiting else 0,
        "deadlines_missed": missed,
        "runs_past_next_start": gaps,
        "capacity": capacity,
    }
