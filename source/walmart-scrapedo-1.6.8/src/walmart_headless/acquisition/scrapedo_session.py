"""Walmart pages through Scrape.do, for the application's Walmart collector (no browser).

The session offers what the collector uses: ``load_robots``, ``navigate``, ``fetches``, ``robots``, the
stored page evidence and a meter of the credits the provider charged. Two Scrape.do endpoints, by the page:

* ``/plugin/walmart/store`` with the configured store's ``storeid`` and ``zipcode`` (the documented
  matching pair) for every Walmart page whose prices or fulfillment matter: listings and store-scoped
  product pages. The provider returns Walmart's own response verbatim, and the collector checks each page
  against the store from Walmart's own data (page location, Pickup lines), never from these request
  parameters; the store the provider says the response reflects (its ``Scrape.do-Walmart-Store-Id``
  header, documented) is recorded and must not name another store;
* the general API (``/``, datacenter, 1 credit) for robots.txt and the store's own page, which describes
  the store by itself and says nothing about prices (the store endpoint answers 502 on /store/ pages,
  observed 2026-10-21); for category pages (``/cp/``), read only for the subcategory listings their
  navigation names, never for a price or a product (the store endpoint answered every /cp/ page with its
  own "Walmart-store plugin failure." 502 on 2026-10-23: a provider error, not Walmart's answer); and for
  product detail pages read only for the product's identifiers (purpose ``product_detail``): a UPC is an
  attribute of the product, not of the store, and no price is taken from those pages (answered with the
  item's page data at 1 credit, observed 2026-10-23; Walmart served them for its default store).

Every answer is kept: the sanitized page (``dom/``) and the exact body
(``raw/``, gzip, in the run's private storage), with the provider's request id, cost, key role and
remaining credits in the fetch's notes. A challenge page or a document without its page data is a
challenge (:class:`ChallengeDetected`); a provider failure is a
:class:`ProviderError`.
"""

from __future__ import annotations

import asyncio
import gzip
import hashlib
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from time import monotonic
from typing import Any, ClassVar
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from walmart_headless.acquisition.challenge import WALMART_STATE_MARKER, detect_document_challenge
from walmart_headless.acquisition.errors import ProviderError, ProviderErrorKind
from walmart_headless.acquisition.pages import ChallengeDetected, PageFetch, RobotsDisallowed
from walmart_headless.acquisition.robots import RobotsPolicy, parse_robots
from walmart_headless.acquisition.scrapedo import (
    GENERAL_ENDPOINT,
    WALMART_STORE_ENDPOINT,
    Answer,
    Request,
    Transport,
)
from walmart_headless.core.ids import new_id
from walmart_headless.core.timeutil import iso, utcnow
from walmart_headless.storage.base import StorageAdapter

STORE_PAGE_COST = 1.0  # general API, datacenter (Request Costs: walmart.com has no per-domain profile)
# Pages requested through the general API, without the store's parameters: robots.txt, the store's own page
# (it describes its store by itself), category pages (read for their navigation only) and a product's own
# page read for its UPC.
GENERAL_PURPOSES = frozenset({"robots", "store_page", "product_detail", "category_page"})
WALMART_PAGE_COST = 10.0  # Walmart Scraper API: each successful request
# Walmart's own result-grid filter for the store's fulfillment (release 1.4.1), the facet its Pickup result
# pages state (``pageProperties.facet``; their filter links join facets with ``||``) and its grid's
# ``meta.fulfillmentIntent`` names. The store endpoint sets the store only: without the filter its listings
# are the store's unfiltered grid,
# out-of-stock, shipping-only and marketplace items too (live 2026-10-28: Laundry reported 18,682 results
# there, 624 in the Pickup grid the Oxylabs Web API returned half an hour later). The Oxylabs Web API applies
# the same filter from its ``fulfillment_type``.
FULFILLMENT_FACETS = {"PICKUP": "fulfillment_method:Pickup"}
# A request with its retries can outlast the task's lease (120 s): the lease is renewed meanwhile.
KEEPALIVE_S = 30.0
_KIND_ERRORS = {
    "auth": ProviderErrorKind.AUTH,
    "balance": ProviderErrorKind.QUOTA,
    "rate_limit": ProviderErrorKind.CONCURRENCY,
    "bad_parameters": ProviderErrorKind.CONFIG,
    "store_pair": ProviderErrorKind.CONFIG,
}


@dataclass
class Estimate:
    credits: float
    bytes_seen: int


@dataclass
class Meter:
    """Credits (Scrape.do) or results (Oxylabs) the provider charged in this session, measured from its
    answers, with the requests in flight counted at their largest cost (``pending``) so parallel workers
    see each other's commitments before the answers arrive."""

    credits: float = 0.0
    bytes_seen: int = 0
    requests: int = 0
    overhead: float = 1.0
    rate_per_mb: float = 1.0
    usd: float = 0.0
    pending: float = 0.0

    def estimate(self, extra_bytes: int = 0, extra_s: float = 0.0) -> Estimate:
        return Estimate(self.credits + self.pending, self.bytes_seen + max(0, extra_bytes))


class RequestLimiter:
    """Provider requests of one process (every worker): at most ``max_in_flight`` at once, and starts at
    least ``min_interval_s`` apart. The provider's own limits still apply; this keeps the collector below
    them and spaces its requests."""

    def __init__(self, max_in_flight: int = 1, min_interval_s: float = 0.0):
        self.max_in_flight, self.min_interval_s = max(1, max_in_flight), max(0.0, min_interval_s)
        self._sem: asyncio.Semaphore | None = None
        self._lock: asyncio.Lock | None = None
        self._next = 0.0
        self.waited_s = 0.0

    @asynccontextmanager
    async def slot(self) -> AsyncIterator[None]:
        if self._sem is None or self._lock is None:
            self._sem, self._lock = asyncio.Semaphore(self.max_in_flight), asyncio.Lock()
        t0 = monotonic()
        async with self._sem:
            async with self._lock:
                wait = self._next - monotonic()
                if wait > 0:
                    await asyncio.sleep(wait)
                self._next = monotonic() + self.min_interval_s
            self.waited_s += monotonic() - t0
            yield


@dataclass
class Pacer:
    count: int = 0


@dataclass
class Event:
    ts: str
    level: str
    code: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)


def store_scoped(url: str, purpose: str, general: frozenset[str] = GENERAL_PURPOSES) -> bool:
    """Whether a provider requests this page with the store's parameters (its store endpoint): every page
    but robots.txt, a store page and the provider's ``general`` purposes. The replay of a run uses the same
    rule to record the parameters its source run's pages were requested with."""
    path = urlsplit(url).path
    return not (purpose in general or path.startswith("/store/") or path == "/robots.txt")


def with_facet(url: str, facet: str) -> str:
    """``url`` with ``facet`` among its ``facet`` parameter's values (joined by ``||``, as Walmart's own facet
    links join them); its other parameters (``page``) kept. A URL that has the facet already is unchanged."""
    parts = urlsplit(url)
    query = parse_qsl(parts.query, keep_blank_values=True)
    facets = [f for k, v in query if k == "facet" for f in v.split("||") if f]
    if facet in facets:
        return url
    query = [(k, v) for k, v in query if k != "facet"] + [("facet", "||".join([*facets, facet]))]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


class ScrapeDoWalmartSession:
    provider = "scrapedo"
    label = "Scrape.do"
    KIND_ERRORS: ClassVar[dict[str, ProviderErrorKind]] = _KIND_ERRORS
    # Answers that are a usable page although not a success (the target's own 404 for a product page).
    USABLE_KINDS: frozenset[str] = frozenset({"not_found"})

    def __init__(
        self,
        transport: Transport,
        storage: StorageAdapter,
        run_prefix: str,
        *,
        store_id: str,
        zipcode: str,
        store_page_url: str,
        sanitizer: Callable[[str], tuple[str, Any]],
        listing_facet: str | None = None,
    ):
        self.session_id = new_id()
        self.transport, self.storage, self.prefix = transport, storage, run_prefix.rstrip("/")
        self.store_id, self.zipcode, self.store_page_url = store_id, zipcode, store_page_url
        # Walmart's grid filter for the store's fulfillment (FULFILLMENT_FACETS), added to every result page.
        self.listing_facet = listing_facet
        self.sanitizer = sanitizer
        self.fetches: list[PageFetch] = []
        self.events: list[Event] = []
        self.captured: list[Any] = []
        self.documents: list[dict[str, Any]] = []
        self.robots: RobotsPolicy | None = None
        self.robots_text: str | None = None
        self.meter = Meter()
        self.pacer = Pacer()
        self.closed_at: str | None = None
        self.routed = 0
        self.byte_ceiling: int | None = None
        self.max_credits: float | None = None
        self.cdp_bytes = 0
        # Renews the current task's lease while a request is in flight (set by the collector).
        self.keepalive: Callable[[], None] | None = None
        # Shared by every worker of the process (set by the collector): concurrency and spacing.
        self.limiter: RequestLimiter | None = None

    # -- lifecycle (nothing to open: every request stands alone) ------------------------------------

    async def __aenter__(self) -> ScrapeDoWalmartSession:
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self.closed_at is None:
            self.closed_at = iso(utcnow())
            await self.transport.aclose()

    def event(self, level: str, code: str, message: str, data: dict[str, Any] | None = None) -> None:
        self.events.append(Event(iso(utcnow()), level, code, message, data or {}))

    def cost_snapshot(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "requests": self.meter.requests,
            "credits_charged": self.meter.credits,
            "usd": round(self.meter.usd, 6),
            "bytes_received": self.meter.bytes_seen,
        }

    # -- the browser session's other controls do not apply ----------------------------------------

    async def set_resource_policy(self, policy: Any) -> None:
        return None

    async def set_byte_ceiling(self, ceiling: int | None) -> None:
        self.byte_ceiling = ceiling

    def start_trace(self, match: Callable[[str], bool]) -> None:
        return None

    def stop_trace(self) -> list[dict[str, Any]]:
        return []

    def projected_step_bytes(self) -> int:
        return 0

    async def act(self, purpose: str, action: Any, **_: Any) -> PageFetch:
        raise ProviderError(
            ProviderErrorKind.CONFIG,
            f"{purpose}: page interactions are not available through {self.label}'s API",
        )

    def max_cost(self, req: Any) -> float:
        """The largest cost of one request in the meter's unit (credits)."""
        return float(req.max_cost)

    # -- requests -----------------------------------------------------------------------------------

    def _request(self, url: str, purpose: str) -> Request:
        host = urlsplit(url).hostname or ""
        if not store_scoped(url, purpose):
            return Request(GENERAL_ENDPOINT, {"url": url, "geoCode": "us"}, STORE_PAGE_COST, purpose)
        if not host.endswith("walmart.com"):
            raise ProviderError(ProviderErrorKind.CONFIG, f"not a walmart.com page: {url}")
        if purpose == "listing" and self.listing_facet:
            url = with_facet(url, self.listing_facet)
        return Request(
            WALMART_STORE_ENDPOINT,
            {"url": url, "storeid": self.store_id, "zipcode": self.zipcode},
            WALMART_PAGE_COST,
            purpose,
        )

    def _new_fetch(self, purpose: str, url: str) -> PageFetch:
        f = PageFetch(fetch_id=new_id(), purpose=purpose, url=url, started_at=iso(utcnow()))
        self.fetches.append(f)
        return f

    def _notes(self, fetch: PageFetch, req: Request, a: Answer) -> None:
        fetch.notes.update(
            {
                "provider": "scrape.do",
                "endpoint": req.endpoint,
                "store_scope": {"storeid": self.store_id, "zipcode": self.zipcode}
                if req.endpoint == WALMART_STORE_ENDPOINT
                else None,
                "request_id": a.request_id,
                "credits": a.credits,
                "cost_source": a.cost_source,
                "remaining_after": a.remaining,
                "key_role": a.key_role,
                "key_fingerprint": a.key_fingerprint,
                "attempts": a.attempts,
                "failovers": a.failovers,
                "bytes_received": len(a.body),
                "provider_headers": {
                    k: v
                    for k, v in a.headers.items()
                    if k
                    in (
                        "scrape.do-initial-status-code",
                        "scrape.do-resolved-url",
                        "scrape.do-walmart-store-id",
                    )
                },
            }
        )

    async def _fetch(self, req: Any) -> Answer:
        if self.limiter is None:
            return await self._fetch_alive(req)
        async with self.limiter.slot():
            return await self._fetch_alive(req)

    async def _fetch_alive(self, req: Any) -> Answer:
        beat = self.keepalive
        if beat is None:
            return await self.transport.fetch(req)

        async def renew() -> None:
            while True:
                await asyncio.sleep(KEEPALIVE_S)
                beat()

        renewing = asyncio.create_task(renew())
        try:
            return await self.transport.fetch(req)
        finally:
            renewing.cancel()
            try:
                await renewing
            except asyncio.CancelledError:
                # The helper's own cancellation is expected; a cancellation of this task (a termination
                # signal arriving while the helper stops) must go on, never be swallowed here.
                current = asyncio.current_task()
                if current is not None and current.cancelling():
                    raise
            except Exception:
                pass  # a failed lease renewal is noticed by the next checkpoint

    async def _get(self, url: str, purpose: str) -> tuple[PageFetch, Answer, str]:
        req = self._request(url, purpose)
        cost = self.max_cost(req)
        if self.max_credits is not None and self.meter.credits + self.meter.pending + cost > self.max_credits:
            raise ProviderError(ProviderErrorKind.BUDGET, "the run's credit room is used up")
        fetch = self._new_fetch(purpose, url)
        t0 = monotonic()
        self.meter.pending += cost
        try:
            a = await self._fetch(req)
        except ProviderError as exc:
            fetch.duration_ms = int((monotonic() - t0) * 1000)
            fetch.notes.update(
                {"provider": self.provider, "endpoint": req.endpoint, "error_side": "provider"}
            )
            self.meter.credits += exc.units
            self.meter.usd += exc.usd
            raise
        except BaseException:
            # Cancelled in flight: the provider may still charge it (the ledger keeps it as possibly
            # charged); the run's own accounting counts its largest cost.
            self.meter.credits += cost
            raise
        finally:
            self.meter.pending -= cost
        self.pacer.count += 1
        self.meter.requests += 1
        self.meter.credits += a.credits
        self.meter.usd += a.cost_usd or 0.0
        self.meter.bytes_seen += len(a.body)
        fetch.duration_ms = int((monotonic() - t0) * 1000)
        fetch.status = a.status
        fetch.final_url = url
        self._notes(fetch, req, a)
        raw_key = f"{self.prefix}/raw/{fetch.fetch_id}.{purpose}.body.gz"
        self.storage.put_bytes(raw_key, gzip.compress(a.body, mtime=0), "application/gzip")
        fetch.notes["raw_key"] = raw_key
        fetch.notes["raw_sha256"] = hashlib.sha256(a.body).hexdigest()
        if a.kind is not None and a.kind not in self.USABLE_KINDS:
            kind = self.KIND_ERRORS.get(a.kind, ProviderErrorKind.PROVIDER)
            text = a.body[:300].decode("utf-8", "replace")
            fetch.notes["provider_error"] = {"kind": a.kind, "status": a.status, "body": text}
            self.event("WARN", "PROVIDER_ERROR", url, {"kind": a.kind, "status": a.status})
            raise ProviderError(
                kind, f"{self.label} {req.endpoint} answered HTTP {a.status} ({a.kind}): {text[:200]}"
            )
        return fetch, a, a.body.decode("utf-8", "replace")

    async def load_robots(self, url: str) -> RobotsPolicy:
        # A provider failure stays a provider failure (never a refusal by the site).
        fetch, a, body = await self._get(url, "robots")
        key = f"{self.prefix}/robots/{fetch.fetch_id}.status{a.status}.txt"
        self.storage.put_bytes(key, body.encode("utf-8"), "text/plain")
        fetch.dom_key = key
        if a.status != 200:
            fetch.challenge = detect_document_challenge(a.status, body, expect_initial_state=False)
            if fetch.challenge.is_challenge:
                raise ChallengeDetected(fetch)
            raise RobotsDisallowed(f"robots.txt unavailable (HTTP {a.status}); refusing to crawl")
        self.robots_text = body
        self.robots = parse_robots(body)
        self.event("INFO", "ROBOTS_FETCHED", url, {"sha256": self.robots.sha256})
        return self.robots

    def check_allowed(self, url: str) -> None:
        if self.robots is None:
            raise RobotsDisallowed("robots.txt not loaded; refusing to navigate")
        if not self.robots.allowed(url):
            raise RobotsDisallowed(f"robots.txt disallows {url}")

    async def navigate(
        self, url: str, purpose: str, *, settle_ms: int = 0, expect_initial_state: bool = True
    ) -> PageFetch:
        self.check_allowed(url)
        fetch, a, html = await self._get(url, purpose)
        fetch.challenge = detect_document_challenge(
            a.status, html, expect_initial_state=expect_initial_state, state_marker=WALMART_STATE_MARKER
        )
        sanitized, _ = self.sanitizer(html)
        dom_key = f"{self.prefix}/dom/{fetch.fetch_id}.html.gz"
        self.storage.put_bytes(dom_key, gzip.compress(sanitized.encode("utf-8"), mtime=0), "application/gzip")
        fetch.dom_key = dom_key
        data: dict[str, Any] = {"fetch_id": fetch.fetch_id, "status": a.status, "credits": a.credits}
        data["key"] = a.key_role
        if fetch.challenge.reasons:
            # The signals of a challenge, or the wording seen on a page that was read (``ambiguous_wording``,
            # ``in_page_data``): kept with the page so a reviewer can check the decision.
            data["challenge"] = list(fetch.challenge.reasons)
        self.event(
            "WARN" if fetch.challenge.is_challenge else "INFO",
            "CHALLENGE_DETECTED" if fetch.challenge.is_challenge else "PAGE_CAPTURED",
            url,
            data,
        )
        if fetch.challenge.is_challenge:
            raise ChallengeDetected(fetch)
        return fetch

    async def current_html(self) -> str:
        return ""
