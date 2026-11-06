"""Daylight saving on the store's schedule (release 1.5.2). America/Chicago left daylight time on 2026-11-01
and enters it on 2027-03-14. No clock is faked for a run here: these are computed occurrences, an accelerated
offline check, not an observed unattended execution."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from walmart_headless.collection.config import Schedule
from walmart_headless.collection.schedule import day_bounds, occurrence_on

CHICAGO = ZoneInfo("America/Chicago")


def schedule(start: str = "06:00", weekdays: list[int] | None = None) -> Schedule:
    return Schedule.model_validate(
        {"enabled": True, "weekdays": [1, 4] if weekdays is None else weekdays, "start_time": start}
    )


@pytest.mark.parametrize(
    ("day", "utc_hour"),
    [
        (date(2026, 10, 27), 11),  # Tuesday before the change: daylight time, UTC-5
        (date(2026, 10, 30), 11),  # Friday before the change
        (date(2026, 11, 3), 12),  # Tuesday after the change: standard time, UTC-6
        (date(2027, 3, 12), 12),  # Friday before the March change
        (date(2027, 3, 16), 11),  # Tuesday after the March change
    ],
)
def test_a_start_stays_at_its_local_hour_on_both_sides_of_each_change(day: date, utc_hour: int) -> None:
    occ = occurrence_on(schedule(), day, CHICAGO)
    assert occ is not None
    assert occ.start.astimezone(UTC) == datetime(day.year, day.month, day.day, utc_hour, tzinfo=UTC)
    assert occ.start.astimezone(CHICAGO).strftime("%H:%M") == "06:00"


@pytest.mark.parametrize("monday", [date(2026, 10, 26), date(2027, 3, 8)])
def test_the_weeks_of_each_change_keep_their_two_starts(monday: date) -> None:
    for week in range(2):
        days = [monday + timedelta(days=7 * week + i) for i in range(7)]
        starts = [d for d in days if occurrence_on(schedule(), d, CHICAGO) is not None]
        assert [d.weekday() for d in starts] == [1, 4]


def test_a_start_in_the_repeated_hour_happens_once() -> None:
    """01:30 happens twice on 2026-11-01: one occurrence, at the first of them."""
    occ = occurrence_on(schedule("01:30", [6]), date(2026, 11, 1), CHICAGO)
    assert occ is not None and occ.start.astimezone(UTC) == datetime(2026, 11, 1, 6, 30, tzinfo=UTC)


def test_a_start_in_the_missing_hour_still_happens_on_its_day() -> None:
    """02:30 does not exist on 2027-03-14: the occurrence is not lost and stays on its local day."""
    occ = occurrence_on(schedule("02:30", [6]), date(2027, 3, 14), CHICAGO)
    assert occ is not None and occ.start.astimezone(CHICAGO).date() == date(2027, 3, 14)


@pytest.mark.parametrize(("day", "hours"), [(date(2026, 11, 1), 25), (date(2027, 3, 14), 23)])
def test_the_daily_limits_use_the_real_length_of_the_local_day(day: date, hours: int) -> None:
    start, end = day_bounds(day, CHICAGO)
    assert end.astimezone(UTC) - start.astimezone(UTC) == timedelta(hours=hours)
