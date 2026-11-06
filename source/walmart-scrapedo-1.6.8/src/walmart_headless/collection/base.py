"""The provider-neutral part of a live collection on the run pipeline's tasks.

A live run has a ``preflight`` task, one ``listing_node`` task per planned category row, then
``assemble``, ``validate`` and ``export``. Before every request the run's limits are checked (verified
products per run and per day, active minutes, provider credits per run and per day, the account's
reserve, the schedule window) and a stop request. A limit stops the run resumably (:class:`RunStop`); a
refusal by the site, a page not priced for the store, or an abnormal page stops it for review; nothing is
retried with another identity, and no other provider is ever used.

The retailer's collector (:class:`walmart_headless.collection.walmart.WalmartCollector`) supplies the
provider session, the store selection and verification, and the listing handlers.

Parallel workers. An execution may run several workers in one process (``parallel.workers``): each has
its own collector (its own provider session, store check and task leases) and the collectors form a
:class:`Crew` that shares one collection segment, the run's recorded products, the process's request
limiter and a stop seen by every worker. The run's limits count every worker's requests, including the ones
in flight (at their largest cost), and the provider ledgers reserve each request's cost in the database
before it is sent, across workers and processes.
"""

from __future__ import annotations

import asyncio
import hashlib
import sys
import time
from collections.abc import Awaitable, Callable, Mapping
from datetime import datetime, timedelta
from time import monotonic
from typing import Any, TypeVar
from zoneinfo import ZoneInfo

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from walmart_headless.acquisition import lineage
from walmart_headless.acquisition.errors import ProviderError, ProviderErrorKind
from walmart_headless.acquisition.pages import (
    ChallengeDetected,
    NoDocumentResponse,
    PageFetch,
    RobotsDisallowed,
    RobotsUnreachable,
)
from walmart_headless.acquisition.scrapedo_session import RequestLimiter, ScrapeDoWalmartSession
from walmart_headless.assembly.offers import format_description
from walmart_headless.assembly.record_builder import BuiltRecord, RecordStatus
from walmart_headless.collection import retention, segments
from walmart_headless.collection.config import CollectionConfig
from walmart_headless.collection.limits import (
    StopCode,
    Usage,
    credit_room,
    first_stop,
    segment_totals,
    verified_in_run,
    verified_on_day,
)
from walmart_headless.collection.nodes import Node
from walmart_headless.collection.schedule import day_bounds, local_day
from walmart_headless.collection.verification import StoreVerification
from walmart_headless.core import jsonvalues as jv
from walmart_headless.core.findings import DataMode
from walmart_headless.core.schema import ordered_record
from walmart_headless.core.settings import Settings, StoreConfig
from walmart_headless.core.timeutil import utcnow
from walmart_headless.db import queue
from walmart_headless.db.models import (
    Artifact,
    CategorySource,
    CollectionSegment,
    RecordRow,
    Run,
    StoreAttestation,
    Task,
)
from walmart_headless.db.models import CapturedResponse as CapturedRow
from walmart_headless.db.models import PageFetch as PageFetchRow
from walmart_headless.validation.gates import (
    AttestationSummary,
    CategoryOutcome,
    RunEvidence,
    field_completeness,
    run_gates,
)
from walmart_headless.worker.runner import CancelledByOperator, Handler, RunStop, TaskContext, WorkerGroup
from walmart_headless.worker.runs import event, record_validation, transition

T = TypeVar("T")

# Stops where the provider account's remaining room binds.
ACCOUNT_STOPS = frozenset({StopCode.CREDITS_EXHAUSTED, StopCode.CREDIT_RESERVE})
MIN_SESSION_CREDITS = 12.0  # no provider session is opened with less credit room than this
MAX_RECONNECTS = 2  # per segment, when the provider session goes away
FINISHED_NODE = ("DONE", "EMPTY", "INCOMPLETE", "SKIPPED")
EXPORTED_STATUSES = ("valid", "exported_not_valid", "historical")


def offer_summaries(built: BuiltRecord, settings: Settings) -> list[dict[str, Any]]:
    fmt = settings.records.deal_description_format
    return [
        {
            "sources": [s.value for s in (c.offer.sources or (c.offer.source,))],
            "kind": c.kind.value,
            "tag": c.offer.tag,
            "text": c.offer.text,
            "terms": c.offer.terms,
            "expiry_text": c.offer.expiry_text,
            "requires_clip": c.requires_clip,
            "explicit_price": c.explicit_price,
            "modalities": sorted(c.restricted_to) if c.restricted_to else [],
            "description": format_description(c.offer, fmt),
            "flags": [f.value for f in c.flags],
        }
        for c in built.deals.classified
    ]


def segment_window_end(occ: Mapping[str, Any], now: datetime, tz: ZoneInfo) -> datetime:
    """When this execution of a scheduled run must stop: the end of its occurrence's daily window on the
    occurrence's own day; on a later day (a continuation), the same daily window's end on that day (local
    clock times; daylight-saving changes handled by ``zoneinfo``)."""
    end = datetime.fromisoformat(str(occ["window_end"])).astimezone(tz)
    if now.astimezone(tz) < end:
        return end
    start = datetime.fromisoformat(str(occ.get("window_start") or occ["start"])).astimezone(tz)
    day = now.astimezone(tz).date()
    days_after = (end.date() - start.date()).days  # 1 when the window ends at midnight
    return datetime.combine(day + timedelta(days=days_after), end.time(), tzinfo=tz)


def last_good_run(s: Session, store_id: str, run_id: str) -> str | None:
    """The run whose yield run ``run_id`` is measured against (abnormal yield, G4): the store's last LIVE run
    that read every page it planned and passed its checks (validated or published), never a bounded (pilot)
    run nor one stopped early (release 1.4.0; release 1.3.1 took the last validated run of any kind). A run
    whose pages come from the network is measured against a run whose pages came from the network
    (``acquisition/lineage.py``): a test's synthetic pages never set what a real run must reach. A test's run
    is measured against a network run or one of its own lineage."""
    here = lineage.of_run(s, run_id).lineage
    for cand, counts, snap in s.execute(
        select(Run.id, Run.counts, Run.config_snapshot)
        .where(
            Run.store_id == store_id,
            Run.id != run_id,
            Run.status.in_(("validated", "published")),
            Run.mode == DataMode.LIVE.value,
        )
        .order_by(Run.created_at.desc())
    ):
        if (snap or {}).get("pilot") or not (counts or {}).get("collection_complete"):
            continue
        if lineage.of_run(s, cand).lineage in (lineage.NETWORK, here):
            return str(cand)
    return None


def process_usage() -> dict[str, Any]:
    """CPU time and peak memory of this process (Linux: ``getrusage``; elsewhere CPU time only)."""
    if sys.platform == "win32":  # development machines
        return {"cpu_s": round(time.process_time(), 2), "max_rss_mb": None}
    import resource

    ru = resource.getrusage(resource.RUSAGE_SELF)
    return {"cpu_s": round(ru.ru_utime + ru.ru_stime, 2), "max_rss_mb": round(ru.ru_maxrss / 1024, 1)}


class Crew:
    """The collectors of one execution (see the module docstring)."""

    def __init__(self, limiter: RequestLimiter):
        self.members: list[BaseCollector] = []
        self.limiter = limiter
        self.workers: WorkerGroup | None = None
        self.cpu_start = process_usage()["cpu_s"]
        # Records whose own page a worker of this execution is reading (one reader per product).
        self.claims: set[str] = set()
        # Pages being read now for a product's missing fields: a page budget counts them before they end.
        self.detail_in_flight = 0
        # One reader at a time for a product two follow-up candidates name (a sponsored tile and a variant).
        self.follow_locks: dict[str, asyncio.Lock] = {}

    def follow_lock(self, key: str) -> asyncio.Lock:
        return self.follow_locks.setdefault(key, asyncio.Lock())


class SessionLost(Exception):
    """The provider session went away (it stopped answering)."""


class AbnormalPage(Exception):
    pass


class BaseCollector:
    # The site's own data responses kept with the run.
    CAPTURE_KINDS: tuple[str, ...] = ()
    # Fields every exported record must fill (validation G8).
    REQUIRED_FIELDS: tuple[str, ...] = ("product_title", "url", "category")

    def __init__(
        self,
        pipe: Any,  # walmart_headless.worker.pipeline.Pipeline
        run_id: str,
        *,
        config: CollectionConfig,
        trigger: str,
        clock: Callable[[], datetime] = utcnow,
    ):
        self.pipe = pipe
        self.run_id = run_id
        self.cfg = config
        self.trigger = trigger
        self.clock = clock
        self.store: StoreConfig = pipe.store_cfg
        self.factory = pipe.factory
        self.storage = pipe.storage
        self.settings: Settings = pipe.settings
        self.session: ScrapeDoWalmartSession | None = None
        self.session_opened: float | None = None
        self.segment_id: str | None = None
        self.segment_started = monotonic()
        self.closed_credits = 0.0
        self.closed_requests = 0
        self.closed_usd = 0.0
        self.sessions_opened = 0
        self.sessions_closed = 0
        self.steps = 0
        self.tasks_done = 0
        par = config.parallel
        self.crew = Crew(RequestLimiter(par.max_in_flight, par.min_interval_s))
        self.crew.members.append(self)
        self.worker_name = "w0"
        self.account_start: int | None = None
        self.reconnects = 0
        self.binding: StopCode | None = None
        self.persisted: set[str] = set()
        self.verified_at_start = 0
        self.window_end: datetime | None = None
        # The lineage of the execution running the current segment (recorded with the segment).
        self.segment_lineage: dict[str, Any] = {}
        with self.factory() as s:
            run = s.get(Run, run_id)
            assert run is not None
            self.store_id = run.store_id
            snap = run.config_snapshot or {}
            occ = snap.get("occurrence") or {}
            if run.trigger == "schedule" and occ.get("window_end"):
                self.window_end = segment_window_end(occ, self.clock(), self.cfg.tz)
            self.plan = [Node.from_dict(n) for n in (snap.get("plan") or {}).get("nodes", [])]
            self.pilot = bool(snap.get("pilot"))
            self.recorded: set[str] = set(s.scalars(select(RecordRow.upc).where(RecordRow.run_id == run_id)))

    # -- parallel workers -----------------------------------------------------------------------

    def sibling(self, index: int) -> BaseCollector:
        """Another collector of this execution's crew (its own session), for worker ``index``."""
        raise NotImplementedError

    def adopt(self, primary: BaseCollector, index: int) -> None:
        """Join ``primary``'s crew: its segment, its account reading, its recorded products."""
        self.crew = primary.crew
        self.crew.members.append(self)
        self.worker_name = f"w{index}"
        self.segment_id, self.segment_started = primary.segment_id, primary.segment_started
        self.account_start, self.verified_at_start = primary.account_start, primary.verified_at_start
        self.window_end, self.binding = primary.window_end, primary.binding
        self.segment_lineage = primary.segment_lineage
        self.recorded = primary.recorded  # one process, one event loop: shared without locks

    @property
    def owner_name(self) -> str:
        return f"{self.pipe.store_cfg.key}:{self.worker_name}"

    def own_credits(self) -> float:
        current = self.session.meter.estimate().credits if self.session else 0.0
        return self.closed_credits + current

    def worker_stats(self) -> dict[str, Any]:
        meter = self.session.meter if self.session else None
        return {
            "worker": self.worker_name,
            "requests": self.closed_requests + (meter.requests if meter else 0),
            "credits": round(self.own_credits(), 3),
            "usd": round(self.closed_usd + (meter.usd if meter else 0.0), 6),
            "steps": self.steps,
            "tasks": self.tasks_done,
            "sessions": self.sessions_opened,
            "reconnects": self.reconnects,
        }

    def segment_stats(self) -> dict[str, Any]:
        proc = process_usage()
        return {
            "workers": [m.worker_stats() for m in self.crew.members],
            "process": {
                "cpu_s": round(proc["cpu_s"] - self.crew.cpu_start, 2),
                "max_rss_mb": proc["max_rss_mb"],
            },
            "limiter": {
                "max_in_flight": self.crew.limiter.max_in_flight,
                "min_interval_s": self.crew.limiter.min_interval_s,
                "waited_s": round(self.crew.limiter.waited_s, 1),
            },
            "lineage": self.segment_lineage,
        }

    # -- wiring ---------------------------------------------------------------------------------

    def handlers(self) -> dict[str, Handler]:
        return {
            "preflight": self.h_preflight,
            "listing_node": self.h_listing,
            "assemble": self.h_assemble,
            "validate": self.h_validate,
            "export": self.pipe.h_export,
        }

    async def h_preflight(self, ctx: TaskContext) -> dict[str, Any]:
        raise NotImplementedError

    async def h_listing(self, ctx: TaskContext) -> dict[str, Any]:
        raise NotImplementedError

    @property
    def prefix(self) -> str:
        return f"{self.pipe.prefix(self.run_id)}/live"

    def _read(self, key: str) -> bytes:
        data: bytes = self.storage.get_bytes(key)
        return data

    def html(self, fetch: PageFetch) -> str:
        import gzip

        return gzip.decompress(self._read(fetch.dom_key)).decode("utf-8") if fetch.dom_key else ""

    # -- segment --------------------------------------------------------------------------------

    def _collection_left(self, s: Session) -> bool:
        return (
            s.scalar(
                select(Task.id)
                .where(
                    Task.run_id == self.run_id,
                    Task.kind.in_(("preflight", "listing_node", "follow_up")),
                    Task.state.not_in(tuple(queue.TERMINAL_STATES)),
                )
                .limit(1)
            )
            is not None
        )

    async def begin(self) -> tuple[str, str] | None:
        """Before the worker starts. With listing work left: the key, the account (reachable, credits
        left) and the limits; then a collection segment is opened. Returns a stop."""
        with self.factory() as s:
            if not self._collection_left(s):
                return None  # only assembling, checking and exporting are left: the stop reason stays
            run = s.get(Run, self.run_id)
            assert run is not None
            run.stop_code, run.stop_detail = None, None  # a new stretch of collection starts
            mode = run.mode
            snap = jv.obj(run.config_snapshot, f"run {self.run_id}: config_snapshot")
            recorded = jv.text(jv.obj(snap.get("lineage"), "lineage").get("transport"), "lineage.transport")
            s.commit()
        if mode == DataMode.LIVE.value:
            self.segment_lineage = lineage.current()
            here = str(self.segment_lineage["transport"])
            if recorded and here != recorded:
                return (
                    StopCode.LINEAGE_MISMATCH.value,
                    f"the run records lineage {recorded}; this execution's provider transports are {here} "
                    f"({', '.join(self.segment_lineage['replaced']) or 'none replaced'})",
                )
        else:
            self.segment_lineage = {"transport": "replay", "replaced": []}
        stop = await self.open_account()
        if stop is not None:
            return stop
        now = self.clock()
        with self.factory() as s:
            seg = CollectionSegment(
                run_id=self.run_id,
                store_id=self.store_id,
                trigger=self.trigger[:16],
                day=local_day(now, self.cfg.tz).isoformat(),
                started_at=now,
                heartbeat_at=now,
                account_remaining_start=self.account_start,
                # The lineage is known from the start (the full statistics follow at the segment's end).
                stats={"lineage": self.segment_lineage},
            )
            s.add(seg)
            s.flush()
            self.segment_id = seg.id
            # A segment of the run still open belongs to an execution that ended without closing it (a
            # killed process): recorded as abandoned, its own values kept (collection/segments.py).
            segments.abandon_open(
                s, self.run_id, current=seg.id, detected_by=f"the start of segment {seg.id}", now=now
            )
            self.verified_at_start = verified_in_run(s, self.run_id)
            s.commit()
        self.segment_started = monotonic()
        stop = self.limit_stop(opening=True)
        if stop is not None:
            await self.end(stop[0], stop[1])
            return stop
        return None

    async def open_account(self) -> tuple[str, str] | None:
        """The provider account before a collection segment; sets :attr:`account_start`; returns a stop."""
        raise NotImplementedError

    async def account_remaining_now(self) -> int | None:
        """The account's remaining credits when a segment ends (None when they cannot be read)."""
        raise NotImplementedError

    async def end(self, code: str | None = None, detail: str | None = None) -> None:
        """Always: close the provider session, read the account, close the segment."""
        await self.close_session()
        if self.segment_id is None:
            return
        remaining_end = await self.account_remaining_now()
        with self.factory() as s:
            seg = s.get(CollectionSegment, self.segment_id)
            run = s.get(Run, self.run_id)
            if seg is not None:
                crew = self.crew.members
                seg.ended_at = self.clock()
                seg.heartbeat_at = seg.ended_at
                seg.active_s = monotonic() - self.segment_started
                seg.credits_estimated = self.segment_credits()
                seg.browser_sessions = sum(m.sessions_opened for m in crew)
                seg.browsers_closed = sum(m.sessions_closed for m in crew)
                seg.steps = sum(m.steps for m in crew)
                seg.workers = len(crew)
                seg.stats = self.segment_stats()
                seg.products_verified = verified_in_run(s, self.run_id) - self.verified_at_start
                seg.account_remaining_end = remaining_end
                seg.stop_code = code or (run.stop_code if run else None)
                seg.stop_detail = ((detail or (run.stop_detail if run else None) or "")[:2000]) or None
            s.commit()
        self.segment_id = None

    def heartbeat(self, s: Session) -> None:
        if self.segment_id is None:
            return
        crew = self.crew.members
        s.execute(
            update(CollectionSegment)
            .where(CollectionSegment.id == self.segment_id)
            .values(
                heartbeat_at=self.clock(),
                active_s=monotonic() - self.segment_started,
                credits_estimated=self.segment_credits(),
                browser_sessions=sum(m.sessions_opened for m in crew),
                browsers_closed=sum(m.sessions_closed for m in crew),
                steps=sum(m.steps for m in crew),
                workers=len(crew),
                stats=self.segment_stats(),
                products_verified=verified_in_run(s, self.run_id) - self.verified_at_start,
            )
        )

    # -- limits -----------------------------------------------------------------------------------

    def segment_credits(self) -> float:
        """Every worker's charged credits in this segment, with the requests in flight at their largest
        cost."""
        return sum(m.own_credits() for m in self.crew.members)

    def usage(self) -> Usage:
        day = local_day(self.clock(), self.cfg.tz)
        start, end = day_bounds(day, self.cfg.tz)
        with self.factory() as s:
            run_products = verified_in_run(s, self.run_id)
            day_products = verified_on_day(s, self.store_id, start, end)
            active, credits, day_credits = segment_totals(
                s, self.run_id, self.store_id, day.isoformat(), exclude=self.segment_id
            )
        live = self.segment_credits()
        return Usage(
            run_products,
            day_products,
            active + (monotonic() - self.segment_started),
            credits + live,
            day_credits + live,
            monotonic() - self.segment_started,
        )

    def account_remaining(self) -> float | None:
        return None if self.account_start is None else self.account_start - self.segment_credits()

    def step_credits(self) -> float:
        raise NotImplementedError

    def min_session_credits(self) -> float:
        """No provider session is opened with less credit room than this (robots, store page, a page)."""
        return MIN_SESSION_CREDITS

    def account_stop(self, code: StopCode, detail: str) -> tuple[StopCode, str]:
        """The stop when the account's remaining room binds. A provider whose room is the operator's
        spending ceiling (no readable balance) says so instead (see the Walmart collector)."""
        return code, detail

    def limit_stop(self, *, opening: bool = False) -> tuple[str, str] | None:
        if self.window_end is not None and self.clock() >= self.window_end:
            return StopCode.SCHEDULE_WINDOW_END, f"the daily window ended at {self.window_end.isoformat()}"
        usage = self.usage()
        need = self.min_session_credits() if opening or self.session is None else self.step_credits()
        stop = first_stop(
            self.cfg.limits, usage, account_remaining=self.account_remaining(), min_step_credits=need
        )
        if stop is not None:
            if stop[0] in ACCOUNT_STOPS:
                return self.account_stop(StopCode(stop[0]), stop[1])
            return stop
        room, self.binding = credit_room(self.cfg.limits, usage, self.account_remaining())
        if self.binding in ACCOUNT_STOPS:
            self.binding = self.account_stop(self.binding, "")[0]
        if self.session is not None:
            # The session refuses a request that could cross the remaining room.
            self.session.max_credits = None if room is None else self.session.meter.estimate().credits + room
        return None

    def check(self, ctx: TaskContext) -> None:
        """Before every request: a stop request (an operator's, or another worker's stop), then the
        limits."""
        if self.crew.workers is not None and self.crew.workers.stopping:
            raise CancelledByOperator()
        if ctx.cancelled():
            raise CancelledByOperator()
        stop = self.limit_stop()
        if stop is not None:
            raise RunStop(stop[0], stop[1], resumable=True)
        ctx.heartbeat()

    # -- provider session -------------------------------------------------------------------------

    async def open_session(self, ctx: TaskContext) -> None:
        raise NotImplementedError

    async def select_store(self, ctx: TaskContext, node: Node) -> None:
        raise NotImplementedError

    def _store_selected(self) -> bool:
        raise NotImplementedError

    def verify(self, fetch: PageFetch) -> StoreVerification:
        raise NotImplementedError

    def attest(self, s: Session, v: StoreVerification, phase: str) -> None:
        raise NotImplementedError

    async def close_session(self) -> None:
        if self.session is None:
            return
        session, self.session = self.session, None
        try:
            await session.__aexit__(None, None, None)
        finally:
            charged = session.meter.estimate().credits
            self.closed_credits += charged
            self.closed_requests += session.meter.requests
            self.closed_usd += session.meter.usd
            if session.closed_at is not None:
                self.sessions_closed += 1
            with self.factory() as s:
                event(
                    s,
                    self.run_id,
                    "INFO",
                    "PROVIDER_SESSION_CLOSED",
                    "provider session closed",
                    {"credits_charged": round(charged, 1), "requests": session.pacer.count},
                )
                s.commit()

    async def ensure_session(self, ctx: TaskContext, node: Node) -> bool:
        """A session with robots.txt loaded and the store selected. Returns False when robots.txt does not
        allow ``node`` (the caller skips it)."""
        if self.session is None:
            await self.open_session(ctx)
        assert self.session is not None and self.session.robots is not None
        if not self.session.robots.allowed(node.url):
            return False
        if not self._store_selected():
            await self.select_store(ctx, node)
        return True

    async def _with_reconnects(self, ctx: TaskContext, work: Callable[[], Awaitable[T]]) -> T:
        """Run ``work`` with failures mapped to stops; when the provider session goes away, a new session
        (at most MAX_RECONNECTS per segment) and ``work`` again from the task's checkpoint."""
        while True:
            try:
                return await self._guard(ctx, work())
            except SessionLost as lost:
                await self.close_session()
                self.reconnects += 1
                with self.factory() as s:
                    event(
                        s,
                        self.run_id,
                        "WARN",
                        "PROVIDER_RECONNECT",
                        str(lost)[:300],
                        {"reconnects": self.reconnects},
                    )
                    s.commit()
                if self.reconnects > MAX_RECONNECTS:
                    raise RunStop(
                        StopCode.PROVIDER_ERROR,
                        f"the provider session went away {self.reconnects} times; last: {lost}",
                        resumable=True,
                    ) from None

    def redact(self, text: str) -> str:
        return text

    async def _guard(self, ctx: TaskContext, work: Awaitable[T]) -> T:
        """Site and provider failures as stops (session losses as :class:`SessionLost`)."""
        try:
            return await work
        except (RunStop, CancelledByOperator, SessionLost):
            raise
        except ChallengeDetected as exc:
            self._persist_now(ctx)
            raise RunStop(StopCode.SITE_REFUSAL, str(exc)[:500], resumable=False) from None
        except NoDocumentResponse as exc:
            raise RunStop(StopCode.PROVIDER_ERROR, str(exc), resumable=True) from None
        except RobotsUnreachable as exc:
            raise RunStop(StopCode.SITE_REFUSAL, str(exc), resumable=False) from None
        except RobotsDisallowed as exc:
            raise RunStop(StopCode.ABNORMAL_RESULT, str(exc), resumable=False) from None
        except ProviderError as exc:
            text = self.redact(str(exc))[:500]
            if exc.kind is ProviderErrorKind.BUDGET:
                raise RunStop(self.binding or StopCode.RUN_CREDIT_LIMIT, text, resumable=True) from None
            if exc.kind is ProviderErrorKind.CEILING:
                raise RunStop(StopCode.SPENDING_CEILING, text, resumable=True) from None
            if exc.kind is ProviderErrorKind.AUTH:
                raise RunStop(StopCode.PROVIDER_AUTH, text, resumable=True) from None
            if exc.kind is ProviderErrorKind.QUOTA:
                raise RunStop(StopCode.CREDITS_EXHAUSTED, text, resumable=True) from None
            if exc.kind is ProviderErrorKind.SESSION:
                raise SessionLost(text) from None
            raise RunStop(StopCode.PROVIDER_ERROR, text, resumable=True) from None
        except AbnormalPage as exc:
            raise RunStop(StopCode.ABNORMAL_RESULT, str(exc), resumable=False) from None

    # -- evidence and records in the database -------------------------------------------------------

    def _artifact(self, s: Session, key: str | None, content_type: str) -> str | None:
        if not key:
            return None
        art = s.scalar(select(Artifact).where(Artifact.key == key))
        if art is None:
            data = self._read(key)
            art = Artifact(
                run_id=self.run_id,
                key=key,
                sha256=hashlib.sha256(data).hexdigest(),
                size=len(data),
                content_type=content_type,
            )
            s.add(art)
            s.flush()
        return art.id

    def _persist_now(self, ctx: TaskContext) -> None:
        with self.factory() as s:
            self.persist(s, ctx)
            s.commit()

    def persist(self, s: Session, ctx: TaskContext) -> None:
        """Page fetches of this session not yet in the database (robots, store page, pages)."""
        if self.session is None:
            return
        for f in self.session.fetches:
            if f.fetch_id in self.persisted:
                continue
            dom_type = "application/gzip" if (f.dom_key or "").endswith(".gz") else "text/plain"
            s.add(
                PageFetchRow(
                    id=f.fetch_id,
                    run_id=self.run_id,
                    task_id=ctx.lease.task_id,
                    url=(f.final_url or f.url)[:4000],
                    purpose=f.purpose[:32],
                    http_status=f.status,
                    started_at=datetime.fromisoformat(f.started_at.replace("Z", "+00:00")),
                    duration_ms=f.duration_ms,
                    challenge=f.challenge.is_challenge,
                    dom_artifact_id=self._artifact(s, f.dom_key, dom_type),
                    screenshot_artifact_id=None,
                )
            )
            s.flush()
            for c in f.captured:
                if c.kind not in self.CAPTURE_KINDS or not c.artifact_key or not c.body_sha256:
                    continue
                s.add(
                    CapturedRow(
                        run_id=self.run_id,
                        page_fetch_id=f.fetch_id,
                        kind=c.kind,
                        url=c.url[:4000],
                        status=c.status,
                        request_location_id=c.request_location_id,
                        request_taxonomies=list(c.request_taxonomies),
                        body_sha256=c.body_sha256,
                        artifact_id=self._artifact(s, c.artifact_key, "application/gzip"),
                        schema_ok=c.json_ok,
                        observed_at=datetime.fromisoformat(c.observed_at.replace("Z", "+00:00")),
                    )
                )
            self.persisted.add(f.fetch_id)

    def _attested(self, s: Session) -> bool:
        found = s.scalar(select(StoreAttestation.id).where(StoreAttestation.run_id == self.run_id).limit(1))
        return found is not None

    def _contract(self, s: Session, problem: str | None) -> None:
        run = s.get(Run, self.run_id)
        assert run is not None
        contract = dict((run.counts or {}).get("contract") or {"pages": 0, "problems": []})
        contract["pages"] = int(contract.get("pages", 0)) + 1
        if problem:
            contract["problems"] = [*contract.get("problems", []), problem][-20:]
        run.counts = {**(run.counts or {}), "contract": contract}

    # -- assemble / validate ----------------------------------------------------------------------

    def prior_good(self, s: Session, last: str | None) -> dict[str, int]:
        """Valid records per category of run ``last``, the store's last good run (``last_good_run``)."""
        if last is None:
            return {}
        out: dict[str, int] = {}
        for r in s.scalars(
            select(RecordRow).where(RecordRow.run_id == last, RecordRow.status == RecordStatus.VALID.value)
        ):
            cat = str(r.record.get("category", ""))
            out[cat] = out.get(cat, 0) + 1
        return out

    def node_outcomes(self, s: Session) -> list[dict[str, Any]]:
        out = []
        tasks = s.scalars(
            select(Task)
            .where(Task.run_id == self.run_id, Task.kind == "listing_node")
            .order_by(Task.idem_key)
        )
        for t in tasks:
            cur = t.cursor or {}
            status = str(cur.get("status") or "")
            if t.state != "succeeded":
                status = "NOT_COLLECTED"
            elif status not in FINISHED_NODE:
                status = "INCOMPLETE"
            out.append(
                {
                    "node": cur.get("node") or {},
                    "status": status,
                    "seen": len(cur.get("seen") or []),
                    "total": cur.get("total"),
                    "listings": self.listing_coverage(cur),
                }
            )
        return out

    def listing_coverage(self, cursor: Mapping[str, Any]) -> list[dict[str, Any]] | None:
        """Each listing's own coverage of a category row (``None``: the row is one listing)."""
        return None

    async def h_assemble(self, ctx: TaskContext) -> dict[str, Any]:
        with ctx.session() as s:
            run = s.get(Run, self.run_id)
            assert run is not None
            statuses = {
                str(k): int(v)
                for k, v in s.execute(
                    select(RecordRow.status, func.count())
                    .where(RecordRow.run_id == self.run_id)
                    .group_by(RecordRow.status)
                ).all()
            }
            nodes = self.node_outcomes(s)
            complete = bool(nodes) and all(n["status"] in ("DONE", "EMPTY") for n in nodes)
            by_status: dict[str, int] = {}
            for n in nodes:
                by_status[n["status"]] = by_status.get(n["status"], 0) + 1
            run.counts = {
                **(run.counts or {}),
                "records_by_status": statuses,
                "verified": verified_in_run(s, self.run_id),
                "nodes": by_status,
                "collection_complete": complete,
            }
            event(
                s,
                self.run_id,
                "INFO",
                "RECORDS_ASSEMBLED",
                f"{sum(statuses.values())} products ({statuses.get('valid', 0)} verified)"
                + ("" if complete else "; collection incomplete"),
                {"records_by_status": statuses, "collection_complete": complete},
            )
            s.commit()
        return {**ctx.cursor, "collection_complete": complete}

    async def h_validate(self, ctx: TaskContext) -> dict[str, Any]:
        with ctx.session() as s:
            run = s.get(Run, self.run_id)
            assert run is not None
            last = s.scalars(
                select(StoreAttestation)
                .where(StoreAttestation.run_id == self.run_id)
                .order_by(StoreAttestation.created_at.desc(), StoreAttestation.id.desc())
                .limit(1)
            ).first()
            if last is not None:  # the final attestation repeats the last page the collector checked
                s.add(
                    StoreAttestation(
                        run_id=self.run_id,
                        mode=last.mode,
                        phase="final",
                        observed_location_id=last.observed_location_id,
                        observed_name=last.observed_name,
                        observed_postal_code=last.observed_postal_code,
                        modality=last.modality,
                        modality_source=last.modality_source,
                        is_trusted=last.is_trusted,
                        laf_store_id=last.laf_store_id,
                        cms_scope=last.cms_scope,
                        result=last.result,
                        checks=last.checks,
                        evidence_artifact_ids=last.evidence_artifact_ids,
                        observed_at=last.observed_at,
                    )
                )
                s.flush()
            tasks_terminal, artifacts_ok, records_ok = self.pipe.integrity(s, self.run_id)
            atts = [
                AttestationSummary(
                    a.phase,
                    a.result == "PASS",
                    tuple(
                        c["check"] for c in (a.checks or {}).get("checks", []) if c.get("status") == "FAIL"
                    ),
                )
                for a in s.scalars(select(StoreAttestation).where(StoreAttestation.run_id == self.run_id))
            ]
            recs = list(s.scalars(select(RecordRow).where(RecordRow.run_id == self.run_id)))
            # Fresh observations only: a historical observation carried into the export is not checked again.
            exported_rows = [r for r in recs if r.status in ("valid", "exported_not_valid")]
            exported = [ordered_record(r.record) for r in exported_rows]
            names = {c.id: c.category_name for c in s.scalars(select(CategorySource))}
            valid_by_cat: dict[str, int] = {}
            for r in recs:
                if r.status == RecordStatus.VALID.value:
                    cat = str(r.record.get("category", ""))
                    valid_by_cat[cat] = valid_by_cat.get(cat, 0) + 1
            per_cat: dict[str, dict[str, Any]] = {}
            for n in self.node_outcomes(s):
                node = n["node"]
                cat = names.get(node.get("category_source_id", ""), node.get("category", ""))
                entry = per_cat.setdefault(
                    cat, {"statuses": [], "difference": {}, "row": node.get("row_index", -1)}
                )
                entry["statuses"].append(n["status"])
                listings = n.get("listings")
                if listings:
                    # Each listing against its own reported total (a partitioned listing with its child
                    # categories' distinct products): overlapping listings' totals are never added up. The
                    # gate reads what the total leaves unresolved: 0 when an exact balance holds (a listing
                    # balanced by its organic identities still places sponsored-only ones beyond its total).
                    for lo in listings:
                        entry["difference"][str(lo["id"])] = lo.get("unresolved_difference")
                    continue
                total = n["total"]
                entry["difference"][str(node.get("taxonomy_id"))] = (
                    None if total is None else int(total) - int(n["seen"])
                )
            # Abnormal yield (G4): each category against the store's last good run (``last_good_run``); a
            # bounded (pilot) run is not compared.
            baseline = None if self.pilot else last_good_run(s, self.store_id, self.run_id)
            prior = self.prior_good(s, baseline)
            # The retained products published with the fresh ones (G4 weighs them against the fresh valid
            # records): a bounded run counts those of the listings it read (a product of a listing outside its
            # limits is carried by design), a complete run every one.
            read = retention.coverage_status(s, self.run_id) if self.pilot else None
            retained_by_cat: dict[str, int] = {}
            for r in recs:
                if r.status != retention.CARRIED_STATUS:
                    continue
                listing = ((r.provenance or {}).get("historical") or {}).get("listing")
                if read is not None and listing not in read:
                    continue
                cat = str(r.record.get("category", ""))
                retained_by_cat[cat] = retained_by_cat.get(cat, 0) + 1
            cats = [
                CategoryOutcome(
                    int(e["row"]),
                    cat,
                    "DONE" if all(st in ("DONE", "EMPTY") for st in e["statuses"]) else "INCOMPLETE",
                    valid_by_cat.get(cat, 0),
                    prior.get(cat),
                    zero_rule_holds=all(st == "EMPTY" for st in e["statuses"]),
                    node_difference=e["difference"],
                    retained_records=retained_by_cat.get(cat, 0),
                )
                for cat, e in per_cat.items()
            ]
            contract = (run.counts or {}).get("contract") or {}
            # A refused product detail page (read only for an identifier) leaves the listings' data intact:
            # its product says so ("blocked"); the run's challenge check counts the pages the data came from.
            challenges = s.scalar(
                select(func.count())
                .select_from(PageFetchRow)
                .where(
                    PageFetchRow.run_id == self.run_id,
                    PageFetchRow.challenge.is_(True),
                    PageFetchRow.purpose != "product_detail",
                )
            )
            evidence = RunEvidence(
                mode=DataMode(run.mode),
                attestations=atts,
                challenges_detected=int(challenges or 0),
                categories=cats,
                exported_records=exported,
                exported_keys=[r.upc for r in exported_rows],
                valid_upcs=frozenset(r.upc for r in recs if r.status == RecordStatus.VALID.value),
                required_fields=self.REQUIRED_FIELDS,
                contract_canary_ok=bool(contract.get("pages")) and not contract.get("problems"),
                tasks_all_terminal=tasks_terminal,
                artifact_hashes_verified=artifacts_ok,
                manifest_complete=records_ok,
                carried_problems=tuple(retention.carried_problems(s, self.run_id)),
                product_detail_paused=str((run.counts or {}).get("upc_detail_paused") or ""),
            )
            outcome = run_gates(evidence, self.settings)
            transition(s, self.run_id, "validating")
            status = record_validation(s, self.run_id, outcome, apply_status=False)
            run.counts = {
                **(run.counts or {}),
                "gates": {r.gate: r.status.value for r in outcome.results},
                "completeness": field_completeness(exported),
                "outcome": status,
                "yield_baseline": baseline,
            }
            event(s, self.run_id, "INFO", "CHECKS_COMPLETE", status, run.counts["gates"])
            s.commit()
        return {**ctx.cursor, "status": status}
