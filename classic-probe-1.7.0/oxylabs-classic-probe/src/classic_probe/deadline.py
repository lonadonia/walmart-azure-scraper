"""One session deadline for everything a campaign does (1.7.0, findings C2, C3 and C5).

The deadline is durable: it is derived from the campaign's start recorded once in the ledger, so a restart
never grants a new window. Inside a process it is held on the monotonic clock (a wall-clock jump cannot
extend it), and the ledger checks the wall clock again under its write lock. Every wait (lock, request,
backoff) is clamped to the time left before the reserve kept for export and cleanup.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import UTC, datetime


class DeadlinePassed(RuntimeError):
    """No time is left for this step: nothing was started."""


class SessionClock:
    def __init__(
        self,
        end_wall: datetime,
        *,
        export_reserve_s: float,
        wall: Callable[[], datetime] | None = None,
        monotonic: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.wall = wall or (lambda: datetime.now(UTC))
        self.monotonic = monotonic
        self.sleeper = sleeper  # the real sleep unless a test injects a fake one (C5)
        self.export_reserve_s = export_reserve_s
        self.end_wall = end_wall
        self._end_mono = monotonic() + (end_wall - self.wall()).total_seconds()

    def remaining(self) -> float:
        """Seconds until the session's end (export and cleanup included)."""
        return min(self._end_mono - self.monotonic(), (self.end_wall - self.wall()).total_seconds())

    def dispatch_remaining(self) -> float:
        """Seconds a request, a lock wait or a backoff may still use: the end less the export reserve."""
        return self.remaining() - self.export_reserve_s

    def allowance(self, cap_s: float) -> float:
        """A request's whole allowance (connect, read and decode), clamped; raises when none is left."""
        left = min(cap_s, self.dispatch_remaining())
        if left <= 0:
            raise DeadlinePassed("no time is left before the reserve kept for export and cleanup")
        return left

    def sleep(self, seconds: float, *, then_needs_s: float = 0.0) -> bool:
        """A real, bounded backoff. False (and no sleep) when the wait plus what must follow it would end
        past the dispatch deadline: the caller then stops instead of retrying late."""
        if seconds < 0:
            seconds = 0.0
        if seconds + then_needs_s > self.dispatch_remaining():
            return False
        self.sleeper(seconds)
        return self.dispatch_remaining() > then_needs_s


def parse_retry_after(value: str | None, now: datetime) -> float | None:
    """Seconds from a ``Retry-After`` header (delta-seconds or an HTTP-date); None when absent or invalid."""
    if not value:
        return None
    v = value.strip()
    if v.isdigit():
        return float(v)
    from email.utils import parsedate_to_datetime

    try:
        when = parsedate_to_datetime(v)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    return max(0.0, (when - now).total_seconds())
