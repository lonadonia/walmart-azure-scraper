"""Run limits and stop reasons for live collection.

Usage is read from the database, so it holds across segments, service restarts and reconnects:

* verified products: distinct UPCs whose observation was recorded as verified (a priced card on a page
  that passed the store check and became a valid record) — per run, and per store and local day over
  every live run (a product collected again the same day is not counted twice);
* active time and estimated API credits: the run's collection segments, plus the segment in progress;
* the account balance: the provider's remaining credits read when the segment started, minus what the
  segment has used since.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from walmart_headless.collection.config import Limits
from walmart_headless.db.models import CollectionSegment, ProductObservation, ProviderUsage, Run


class StopCode(StrEnum):
    RUN_PRODUCT_LIMIT = "RUN_PRODUCT_LIMIT"
    DAILY_PRODUCT_LIMIT = "DAILY_PRODUCT_LIMIT"
    RUN_DURATION_LIMIT = "RUN_DURATION_LIMIT"
    SEGMENT_DURATION_LIMIT = "SEGMENT_DURATION_LIMIT"
    RUN_CREDIT_LIMIT = "RUN_CREDIT_LIMIT"
    DAILY_CREDIT_LIMIT = "DAILY_CREDIT_LIMIT"
    CREDIT_RESERVE = "CREDIT_RESERVE"
    CREDITS_EXHAUSTED = "CREDITS_EXHAUSTED"
    SCHEDULE_WINDOW_END = "SCHEDULE_WINDOW_END"
    OPERATOR_PAUSE = "OPERATOR_PAUSE"
    OPERATOR_STOP = "OPERATOR_STOP"
    SERVICE_RESTART = "SERVICE_RESTART"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    PROVIDER_AUTH = "PROVIDER_AUTH"
    ACCOUNT_UNAVAILABLE = "ACCOUNT_UNAVAILABLE"
    NO_API_KEY = "NO_API_KEY"
    SPENDING_CEILING = "SPENDING_CEILING"
    SITE_REFUSAL = "SITE_REFUSAL"
    STORE_NOT_VERIFIED = "STORE_NOT_VERIFIED"
    CANARY_CHECK_FAILED = "CANARY_CHECK_FAILED"
    TERMINATED = "TERMINATED"
    ABNORMAL_RESULT = "ABNORMAL_RESULT"
    NOTHING_TO_COLLECT = "NOTHING_TO_COLLECT"
    SUPERSEDED = "SUPERSEDED"
    COLLECTION_COMPLETE = "COLLECTION_COMPLETE"
    LINEAGE_MISMATCH = "LINEAGE_MISMATCH"


STOP_TEXT: dict[StopCode, str] = {
    StopCode.RUN_PRODUCT_LIMIT: "Stopped at the limit of verified products per run",
    StopCode.DAILY_PRODUCT_LIMIT: "Stopped at the limit of verified products per day",
    StopCode.RUN_DURATION_LIMIT: "Stopped at the maximum run duration",
    StopCode.SEGMENT_DURATION_LIMIT: "Paused at this execution's time limit: the next execution continues "
    "the run from its checkpoints",
    StopCode.RUN_CREDIT_LIMIT: "Stopped at the run's provider-credit budget",
    StopCode.DAILY_CREDIT_LIMIT: "Stopped at the daily provider-credit budget",
    StopCode.CREDIT_RESERVE: "Stopped to keep the minimum provider-credit reserve",
    StopCode.CREDITS_EXHAUSTED: "Stopped: the provider has no API credits left (every configured key)",
    StopCode.SCHEDULE_WINDOW_END: "Stopped at the end of the daily collection window",
    StopCode.OPERATOR_PAUSE: "Paused by an operator (stop request)",
    StopCode.OPERATOR_STOP: "Stopped by an operator",
    StopCode.SERVICE_RESTART: "Interrupted by a restart of the collector",
    StopCode.PROVIDER_ERROR: "Stopped by a provider error (connection, session, rate limit or concurrency)",
    StopCode.PROVIDER_AUTH: "Stopped: the provider refused the API key",
    StopCode.ACCOUNT_UNAVAILABLE: "Stopped: the provider account balance could not be read",
    StopCode.NO_API_KEY: "Not started: no provider API key is configured",
    StopCode.SPENDING_CEILING: "Stopped: the provider spending ceiling set by the operator is used up or not "
    "set (no request is sent without one)",
    StopCode.SITE_REFUSAL: "Stopped: the website refused access (HTTP 403/429, challenge or CAPTCHA page)",
    StopCode.STORE_NOT_VERIFIED: "Stopped: a page was not priced for the configured store and fulfillment",
    StopCode.CANARY_CHECK_FAILED: "Stopped: the first recorded page failed the automated canary checks",
    StopCode.TERMINATED: "Interrupted by a termination signal (the job was stopped or timed out)",
    StopCode.ABNORMAL_RESULT: "Stopped: a page did not show the content it must have",
    StopCode.NOTHING_TO_COLLECT: "Nothing to collect: no listing page is known for the chosen categories",
    StopCode.SUPERSEDED: "Closed when the next scheduled run started",
    StopCode.COLLECTION_COMPLETE: "Every planned listing page was collected",
    StopCode.LINEAGE_MISMATCH: "Not started: this execution's provider transports are not those the run "
    "recorded (a run never mixes pages from the network with substituted ones)",
}
# Stops after which the run waits, resumable (Resume or the schedule continue it from its checkpoint).
RESUMABLE = frozenset(
    {
        StopCode.RUN_PRODUCT_LIMIT,
        StopCode.DAILY_PRODUCT_LIMIT,
        StopCode.RUN_DURATION_LIMIT,
        StopCode.SEGMENT_DURATION_LIMIT,
        StopCode.RUN_CREDIT_LIMIT,
        StopCode.DAILY_CREDIT_LIMIT,
        StopCode.CREDIT_RESERVE,
        StopCode.CREDITS_EXHAUSTED,
        StopCode.SCHEDULE_WINDOW_END,
        StopCode.OPERATOR_PAUSE,
        StopCode.SERVICE_RESTART,
        StopCode.TERMINATED,
        StopCode.LINEAGE_MISMATCH,
        StopCode.PROVIDER_ERROR,
        StopCode.PROVIDER_AUTH,
        StopCode.ACCOUNT_UNAVAILABLE,
        StopCode.NO_API_KEY,
        StopCode.SPENDING_CEILING,
    }
)
# The run's own limits: a run they stopped keeps that reason when an administrator then finalizes it.
LIMIT_STOPS = frozenset(
    {
        StopCode.RUN_PRODUCT_LIMIT,
        StopCode.DAILY_PRODUCT_LIMIT,
        StopCode.RUN_DURATION_LIMIT,
        StopCode.RUN_CREDIT_LIMIT,
        StopCode.DAILY_CREDIT_LIMIT,
        StopCode.CREDIT_RESERVE,
        StopCode.CREDITS_EXHAUSTED,
        StopCode.SCHEDULE_WINDOW_END,
    }
)
# Resumable stops the next scheduled execution continues by itself (a few times).
TRANSIENT = frozenset(
    {StopCode.SERVICE_RESTART, StopCode.TERMINATED, StopCode.PROVIDER_ERROR, StopCode.ACCOUNT_UNAVAILABLE}
)
# Stops that hold the store's scheduled collection until an operator releases it (``release-hold``): the
# website refused access, its pages no longer look as expected, or the automated canary failed. Nothing
# is retried automatically after these.
SUSPENDS_SCHEDULE = frozenset(
    {
        StopCode.SITE_REFUSAL,
        StopCode.STORE_NOT_VERIFIED,
        StopCode.ABNORMAL_RESULT,
        StopCode.PROVIDER_AUTH,
        StopCode.CANARY_CHECK_FAILED,
    }
)


def stop_text(code: str | None) -> str | None:
    if code is None:
        return None
    try:
        return STOP_TEXT[StopCode(code)]
    except ValueError:
        return code


@dataclass
class Usage:
    run_products: int = 0
    day_products: int = 0
    run_active_s: float = 0.0
    run_credits: float = 0.0
    day_credits: float = 0.0
    segment_active_s: float = 0.0  # this execution (segment) only


def verified_in_run(session: Session, run_id: str) -> int:
    return int(
        session.scalar(
            select(func.count(func.distinct(ProductObservation.upc))).where(
                ProductObservation.run_id == run_id,
                ProductObservation.provenance["verified"].as_boolean().is_(True),
            )
        )
        or 0
    )


def verified_on_day(session: Session, store_id: str, start: datetime, end: datetime) -> int:
    return int(
        session.scalar(
            select(func.count(func.distinct(ProductObservation.upc)))
            .join(Run, Run.id == ProductObservation.run_id)
            .where(
                Run.store_id == store_id,
                Run.mode == "LIVE",
                ProductObservation.mode == "LIVE",
                ProductObservation.observed_at >= start,
                ProductObservation.observed_at < end,
                ProductObservation.provenance["verified"].as_boolean().is_(True),
            )
        )
        or 0
    )


def segment_totals(
    session: Session, run_id: str, store_id: str, day: str, *, exclude: str | None = None
) -> tuple[float, float, float]:
    """(run active seconds, run credits, store-day credits) over finished and running segments, except
    ``exclude`` (the segment in progress, which the caller adds live). A segment's credits are the larger of
    its own counter and its provider ledger rows: a killed process's counter stops at its last heartbeat,
    while each request it sent was reserved in the ledger first."""
    seg = CollectionSegment
    ledger = (
        select(func.coalesce(func.sum(ProviderUsage.credits), 0.0))
        .where(ProviderUsage.segment_id == seg.id)
        .scalar_subquery()
    )
    credits = func.greatest(seg.credits_estimated, ledger)
    run_q = select(func.coalesce(func.sum(seg.active_s), 0.0), func.coalesce(func.sum(credits), 0.0)).where(
        seg.run_id == run_id
    )
    day_q = select(func.coalesce(func.sum(credits), 0.0)).where(seg.store_id == store_id, seg.day == day)
    if exclude is not None:
        run_q = run_q.where(seg.id != exclude)
        day_q = day_q.where(seg.id != exclude)
    active, credits = session.execute(run_q).one()
    return float(active), float(credits), float(session.scalar(day_q) or 0.0)


def product_room(limits: Limits, usage: Usage) -> int | None:
    """How many more verified products may be recorded now (None: no product limit)."""
    rooms = [
        cap - used
        for cap, used in (
            (limits.max_products_per_run, usage.run_products),
            (limits.max_products_per_day, usage.day_products),
        )
        if cap is not None
    ]
    return max(0, min(rooms)) if rooms else None


def product_limit_code(limits: Limits, usage: Usage) -> StopCode | None:
    if limits.max_products_per_run is not None and usage.run_products >= limits.max_products_per_run:
        return StopCode.RUN_PRODUCT_LIMIT
    if limits.max_products_per_day is not None and usage.day_products >= limits.max_products_per_day:
        return StopCode.DAILY_PRODUCT_LIMIT
    return None


def credit_room(
    limits: Limits, usage: Usage, account_remaining: float | None
) -> tuple[float | None, StopCode | None]:
    """The credits the run may still spend, and which budget binds (None, None: no credit limit)."""
    rooms: list[tuple[float, StopCode]] = []
    if limits.max_credits_per_run is not None:
        rooms.append((limits.max_credits_per_run - usage.run_credits, StopCode.RUN_CREDIT_LIMIT))
    if limits.max_credits_per_day is not None:
        rooms.append((limits.max_credits_per_day - usage.day_credits, StopCode.DAILY_CREDIT_LIMIT))
    if account_remaining is not None:
        code = StopCode.CREDIT_RESERVE if limits.min_credit_reserve > 0 else StopCode.CREDITS_EXHAUSTED
        rooms.append((account_remaining - limits.min_credit_reserve, code))
    if not rooms:
        return None, None
    room, code = min(rooms, key=lambda r: r[0])
    return max(0.0, room), code


def first_stop(
    limits: Limits, usage: Usage, *, account_remaining: float | None, min_step_credits: float = 0.0
) -> tuple[StopCode, str] | None:
    """The first limit that forbids another step, with a sentence for the operator."""
    code = product_limit_code(limits, usage)
    if code is StopCode.RUN_PRODUCT_LIMIT:
        return (
            code,
            f"{usage.run_products} verified products in this run (limit {limits.max_products_per_run})",
        )
    if code is StopCode.DAILY_PRODUCT_LIMIT:
        return code, f"{usage.day_products} verified products today (limit {limits.max_products_per_day})"
    if limits.max_segment_minutes is not None and usage.segment_active_s >= limits.max_segment_minutes * 60:
        return (
            StopCode.SEGMENT_DURATION_LIMIT,
            f"{usage.segment_active_s / 60:.0f} minutes in this execution "
            f"(limit {limits.max_segment_minutes}); the next execution continues the run",
        )
    if limits.max_run_minutes is not None and usage.run_active_s >= limits.max_run_minutes * 60:
        return (
            StopCode.RUN_DURATION_LIMIT,
            f"{usage.run_active_s / 60:.0f} minutes of collection (limit {limits.max_run_minutes})",
        )
    room, binding = credit_room(limits, usage, account_remaining)
    if room is not None and binding is not None and room <= min_step_credits:
        left = account_remaining or 0
        detail = {
            StopCode.RUN_CREDIT_LIMIT: f"about {usage.run_credits:.0f} API credits used by this run "
            f"(budget {limits.max_credits_per_run})",
            StopCode.DAILY_CREDIT_LIMIT: f"about {usage.day_credits:.0f} API credits used today "
            f"(budget {limits.max_credits_per_day})",
            StopCode.CREDIT_RESERVE: f"about {left:.0f} API credits left on the account "
            f"(reserve {limits.min_credit_reserve})",
            StopCode.CREDITS_EXHAUSTED: f"about {left:.0f} API credits left on the account",
        }[binding]
        return binding, detail
    return None
