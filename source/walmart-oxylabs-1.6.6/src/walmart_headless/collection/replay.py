"""Replay: an earlier LIVE run's stored pages read again offline by the current code (``walmart-collector
replay --run ID``).

The replay is a run of its own (mode ``REPLAY``) through the normal pipeline (preflight, listings, assemble,
validate, export) with the source run's plan and limits. Its session never contacts Scrape.do or Walmart: it
serves the pages the source run stored (robots.txt, the store page, result pages, product pages), each with
its original request time, HTTP status and stored copy, so every record keeps the observation time and
crawl date of the source run. A page the source run never requested is not fetched: the listing or product
says so (``NOT_IN_SOURCE``). Product pages are replayed for every exported product whose page the source run
read (the source's detail limit does not apply: the replay requests nothing).

Each served page records the store parameters its source request carried, by the source provider's own
rule (``scrapedo_session.store_scoped``): Scrape.do's ``storeid`` and ``zipcode`` on its store endpoint, the
Oxylabs Web API's ``store_id`` and ``fulfillment_type`` on ``/v1/scrape/walmart``. As in a live run they are
recorded, never taken as proof: the page's own data is checked. (Release 1.3.1: the replay recorded
Scrape.do's parameters for every page, so an Oxylabs run's replay failed its first listing page's store
check.)

History (earlier verified products, earlier UPCs) is limited to what was observed before the source run
started, and earlier runs that were replayed count through their replays. A replay is corrected evidence
about its source run: it is never published and never counts as a fresh observation (G14).
"""

from __future__ import annotations

import asyncio
import gzip
import hashlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from time import monotonic
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from walmart_headless.acquisition import oxylabs_session, scrapedo_session
from walmart_headless.acquisition.challenge import WALMART_STATE_MARKER, detect_document_challenge
from walmart_headless.acquisition.pages import ChallengeDetected, NotInSource, PageFetch, RobotsDisallowed
from walmart_headless.acquisition.robots import RobotsPolicy, parse_robots
from walmart_headless.collection.walmart import WalmartCollector
from walmart_headless.core.ids import new_id
from walmart_headless.core.timeutil import iso, utcnow
from walmart_headless.db.models import Artifact, Run
from walmart_headless.db.models import PageFetch as PageFetchRow
from walmart_headless.storage.base import StorageAdapter
from walmart_headless.worker.runner import TaskContext
from walmart_headless.worker.runs import event

# Page purposes that answer the same request.
_SAME = {
    "product_detail": ("product_detail", "product_page"),
    "product_page": ("product_page", "product_detail"),
}


@dataclass
class _Stored:
    fetch_id: str
    url: str
    purpose: str
    status: int | None
    started_at: datetime
    duration_ms: int | None
    dom_key: str | None
    dom_sha256: str | None
    served: int = 0


@dataclass
class _Meter:
    credits: float = 0.0
    requests: int = 0
    usd: float = 0.0
    pending: float = 0.0

    def estimate(self, extra_bytes: int = 0, extra_s: float = 0.0) -> Any:
        return self


@dataclass
class _Pacer:
    count: int = 0


class ReplaySession:
    """The pages a source run stored, served in place of the provider (no request leaves the machine)."""

    provider = "replay"

    def __init__(
        self,
        factory: sessionmaker[Session],
        storage: StorageAdapter,
        source_run: str,
        *,
        request_scope: Callable[[str, str], dict[str, str] | None],
    ):
        self.session_id = new_id()
        self.storage = storage
        self.source_run = source_run
        # The store parameters the source run's provider sent with a page (url, purpose), or None.
        self.request_scope = request_scope
        self.fetches: list[PageFetch] = []
        self.robots: RobotsPolicy | None = None
        self.robots_text: str | None = None
        self.meter = _Meter()
        self.pacer = _Pacer()
        self.closed_at: str | None = None
        self.max_credits: float | None = None
        self.keepalive: Callable[[], None] | None = None
        self.not_in_source: list[dict[str, str]] = []
        with factory() as s:
            rows = s.execute(
                select(PageFetchRow, Artifact.key, Artifact.sha256)
                .outerjoin(Artifact, Artifact.id == PageFetchRow.dom_artifact_id)
                .where(PageFetchRow.run_id == source_run)
                .order_by(PageFetchRow.started_at, PageFetchRow.id)
            ).all()
        self.stored: dict[str, list[_Stored]] = {}
        for pf, key, sha in rows:
            self.stored.setdefault(pf.url, []).append(
                _Stored(pf.id, pf.url, pf.purpose, pf.http_status, pf.started_at, pf.duration_ms, key, sha)
            )

    async def __aenter__(self) -> ReplaySession:
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self.closed_at is None:
            self.closed_at = iso(utcnow())

    def cost_snapshot(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "source_run": self.source_run,
            "requests": self.meter.requests,
            "credits_charged": 0.0,
            "not_in_source": len(self.not_in_source),
        }

    def _take(self, url: str, purpose: str) -> _Stored:
        wanted = _SAME.get(purpose, (purpose,))
        candidates = [x for x in self.stored.get(url, []) if x.purpose in wanted]
        if not candidates:
            self.not_in_source.append({"url": url, "purpose": purpose})
            raise NotInSource(
                f"replay: the source run {self.source_run} did not request this {purpose}: {url}"
            )
        fresh = [x for x in candidates if x.served == 0 and x.dom_key]
        chosen = fresh[0] if fresh else candidates[-1]
        chosen.served += 1
        return chosen

    def _fetch(self, stored: _Stored, purpose: str, url: str) -> PageFetch:
        f = PageFetch(
            fetch_id=new_id(),
            purpose=purpose,
            url=url,
            final_url=stored.url,
            status=stored.status,
            started_at=iso(stored.started_at),
            duration_ms=stored.duration_ms,
            dom_key=stored.dom_key,
        )
        raw_key = (
            f"{stored.dom_key.split('/live/')[0]}/live/raw/{stored.fetch_id}.{stored.purpose}.body.gz"
            if (stored.dom_key and "/live/" in stored.dom_key)
            else None
        )
        raw_sha = None
        if raw_key is not None:
            try:
                raw_sha = hashlib.sha256(gzip.decompress(self.storage.get_bytes(raw_key))).hexdigest()
            except (KeyError, OSError):
                raw_key = None
        f.notes.update(
            {
                "provider": "replay",
                "replay_of": stored.fetch_id,
                "source_run": self.source_run,
                "stored_page_sha256": stored.dom_sha256,
                "raw_key": raw_key,
                "raw_sha256": raw_sha,
                "credits": 0.0,
                "bytes_received": None,
            }
        )
        scope = self.request_scope(stored.url, stored.purpose)
        if scope is not None:
            # The parameters the source run requested its page with; as in a live run they are recorded,
            # never taken as proof: the page's own data is checked.
            f.notes["store_scope"] = scope
        self.fetches.append(f)
        self.meter.requests += 1
        self.pacer.count += 1
        return f

    async def load_robots(self, url: str) -> RobotsPolicy:
        stored = self._take(url, "robots")
        fetch = self._fetch(stored, "robots", url)
        if stored.status != 200 or not stored.dom_key:
            raise RobotsDisallowed(f"replay: the source run's robots.txt answer was HTTP {stored.status}")
        body = self.storage.get_bytes(stored.dom_key).decode("utf-8", "replace")
        self.robots_text = body
        self.robots = parse_robots(body)
        fetch.notes["robots_sha256"] = self.robots.sha256
        return self.robots

    def check_allowed(self, url: str) -> None:
        if self.robots is None:
            raise RobotsDisallowed("robots.txt not loaded; refusing to navigate")
        if not self.robots.allowed(url):
            raise RobotsDisallowed(f"robots.txt disallows {url}")

    async def navigate(
        self, url: str, purpose: str, *, settle_ms: int = 0, expect_initial_state: bool = True
    ) -> PageFetch:
        # Nothing here waits for a network, so give way once per page: a termination signal stops a replay at
        # the next page, as it stops a live run (release 1.5.2; until then it landed after the last page).
        await asyncio.sleep(0)
        self.check_allowed(url)
        stored = self._take(url, purpose)
        fetch = self._fetch(stored, purpose, url)
        html = (
            gzip.decompress(self.storage.get_bytes(stored.dom_key)).decode("utf-8") if stored.dom_key else ""
        )
        fetch.challenge = detect_document_challenge(
            stored.status or 0,
            html,
            expect_initial_state=expect_initial_state,
            state_marker=WALMART_STATE_MARKER,
        )
        if fetch.challenge.is_challenge:
            raise ChallengeDetected(fetch)
        return fetch

    async def current_html(self) -> str:
        return ""


class ReplayCollector(WalmartCollector):
    """The Walmart collector reading a source run's stored pages (see the module docstring)."""

    def __init__(self, pipe: Any, run_id: str, **kw: Any):
        super().__init__(pipe, run_id, keys=[], **kw)
        # A replay requests nothing: no provider key is loaded, whatever provider the source run used.
        self.oxylabs_key, self.oxylabs_ledger = None, None
        with self.factory() as s:
            run = s.get(Run, run_id)
            assert run is not None
            replay = (run.config_snapshot or {}).get("replay") or {}
        self.source_run = str(replay["source_run"])
        self.history_before = datetime.fromisoformat(str(replay["source_created_at"]))

    def sibling(self, index: int) -> WalmartCollector:
        raise NotImplementedError("a replay reads its source run's stored pages in one worker")

    def source_scope(self, url: str, purpose: str) -> dict[str, str] | None:
        """The store parameters the source run's provider (the replay's own, from its snapshot) sent with
        a page: none for a page it reads through its general endpoint."""
        general = (
            oxylabs_session.GENERAL_PURPOSES
            if self.provider == "oxylabs"
            else scrapedo_session.GENERAL_PURPOSES
        )
        return self._store_scope() if scrapedo_session.store_scoped(url, purpose, general) else None

    # Release 1.3.1: the replay's log said "requests of the closed Oxylabs Web API session" and "Oxylabs Web
    # API applies it on every page" of pages it only read again.
    def store_method(self) -> str:
        return (
            f"replay of run {self.source_run}: its stored pages are read again; that run requested them "
            f"through {self.provider_label} store-scoped requests (the provider applied the store; no click)"
        )

    def store_selected_message(self) -> str:
        return (
            f"Walmart store {self.store.location_id} verified on the store page run {self.source_run} stored "
            "(read again: no request); each stored page's own data is checked again"
        )

    def traffic_message(self) -> str:
        return (
            f"pages of run {self.source_run} served from storage by the closed replay session "
            f"({self.worker_name}): no request was made"
        )

    def detail_event_data(self, detail: Mapping[str, Any]) -> dict[str, Any]:
        """A product page the source run requested names that run and the replay, never 'fresh' (release
        1.3.1 logged it fresh, as if the replay had requested it); the record's own ``upc_detail`` keeps the
        flag, by which a later run counts the replay's UPCs."""
        data = {k: v for k, v in super().detail_event_data(detail).items() if k != "fresh"}
        if detail.get("fresh"):
            data.update(observed_by_run=self.source_run, read_again_by_run=self.run_id)
        return data

    async def open_account(self) -> tuple[str, str] | None:
        self.account_start = None  # no provider account: nothing is requested
        return None

    async def account_remaining_now(self) -> int | None:
        return None

    def step_credits(self) -> float:
        return 0.0

    async def open_session(self, ctx: TaskContext) -> None:
        session = ReplaySession(self.factory, self.storage, self.source_run, request_scope=self.source_scope)
        session.keepalive = ctx.heartbeat
        await session.__aenter__()
        self.session, self.session_opened = session, monotonic()  # type: ignore[assignment]
        self.sessions_opened += 1
        policy = await session.load_robots(f"{self.base}/robots.txt")
        with self.factory() as s:
            run = s.get(Run, self.run_id)
            assert run is not None
            run.robots_sha256 = policy.sha256
            self.persist(s, ctx)
            event(
                s,
                self.run_id,
                "INFO",
                "REPLAY_SESSION_OPENED",
                f"replay of run {self.source_run}: its stored pages are read again (no request is made)",
                {"source_run": self.source_run, "pages_stored": sum(len(v) for v in session.stored.values())},
            )
            s.commit()
