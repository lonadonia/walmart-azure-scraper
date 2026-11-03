"""Walmart pages through the Oxylabs Web API, for the application's Walmart collector (no browser).

The same session interface as :class:`ScrapeDoWalmartSession` (``load_robots``, ``navigate``, ``fetches``,
the stored page evidence, a meter), with two Web API endpoints chosen by the page:

* ``POST /v1/scrape/walmart`` with the configured store's ``store_id`` and ``fulfillment_type`` (and
  ``delivery_zip`` when configured) for every page whose prices or fulfillment matter: listings and
  store-scoped product pages. The request parameters are recorded but never taken as proof: the collector
  checks each page against the store from Walmart's own data (the page's location context, the products'
  fulfillment lines), exactly as for Scrape.do;
* ``POST /v1/scrape`` (``location`` US) for robots.txt, the store's own page (it describes the store by
  itself) and category pages (read only for the subcategory listings their navigation names).

Only the page's markup is requested (``output: ["html"]``): Oxylabs' parsed ``json`` output and AI parsing
are never used, and no value comes from a provider summary. The Web API reports no status of Walmart's
own answer, so a page is judged from its content (challenge markers, Walmart's page data). Each answer is
kept like Scrape.do's: the sanitized page (``dom/``), the exact markup (``raw/``, gzip), and in the fetch's
notes the request body (never the key), the answer's request id and timestamp, the submissions and their
cost.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, ClassVar
from urllib.parse import urlsplit

from walmart_headless.acquisition.errors import ProviderError, ProviderErrorKind
from walmart_headless.acquisition.oxylabs import (
    GENERAL_ENDPOINT,
    WALMART_ENDPOINT,
    OxylabsTransport,
    OxyRequest,
)
from walmart_headless.acquisition.pages import PageFetch
from walmart_headless.acquisition.scrapedo import Answer
from walmart_headless.acquisition.scrapedo_session import ScrapeDoWalmartSession, store_scoped
from walmart_headless.storage.base import StorageAdapter

RESULT_COST = 1.0  # one submission: one result (the meter's unit for Oxylabs)
GENERAL_PURPOSES = frozenset({"robots", "store_page", "category_page"})


class OxylabsWalmartSession(ScrapeDoWalmartSession):
    provider = "oxylabs"
    label = "Oxylabs Web API"
    KIND_ERRORS: ClassVar[dict[str, ProviderErrorKind]] = {
        "auth": ProviderErrorKind.AUTH,
        "entitlement": ProviderErrorKind.AUTH,
        "quota": ProviderErrorKind.QUOTA,
        "rate_limit": ProviderErrorKind.CONCURRENCY,
        "bad_request": ProviderErrorKind.CONFIG,
    }
    USABLE_KINDS: frozenset[str] = frozenset()

    def __init__(
        self,
        transport: OxylabsTransport,
        storage: StorageAdapter,
        run_prefix: str,
        *,
        store_id: str,
        zipcode: str,
        store_page_url: str,
        sanitizer: Callable[[str], tuple[str, Any]],
        fulfillment_type: str = "pickup",
        delivery_zip: str | None = None,
    ):
        super().__init__(
            transport,  # type: ignore[arg-type]
            storage,
            run_prefix,
            store_id=store_id,
            zipcode=zipcode,
            store_page_url=store_page_url,
            sanitizer=sanitizer,
        )
        self.fulfillment_type = fulfillment_type
        self.delivery_zip = delivery_zip

    def store_scope(self) -> dict[str, str]:
        """The store parameters every store-scoped request carries (recorded; never the proof)."""
        scope = {"store_id": self.store_id, "fulfillment_type": self.fulfillment_type}
        if self.delivery_zip:
            scope["delivery_zip"] = self.delivery_zip
        return scope

    def max_cost(self, req: Any) -> float:
        return RESULT_COST

    def _request(self, url: str, purpose: str) -> OxyRequest:  # type: ignore[override]
        host = urlsplit(url).hostname or ""
        if not host.endswith("walmart.com"):
            raise ProviderError(ProviderErrorKind.CONFIG, f"not a walmart.com page: {url}")
        if not store_scoped(url, purpose, GENERAL_PURPOSES):
            return OxyRequest(GENERAL_ENDPOINT, {"url": url, "output": ["html"], "location": "US"}, purpose)
        return OxyRequest(WALMART_ENDPOINT, {"url": url, "output": ["html"], **self.store_scope()}, purpose)

    def _notes(self, fetch: PageFetch, req: Any, a: Answer) -> None:
        fetch.notes.update(
            {
                "provider": "oxylabs",
                "api_product": "Oxylabs Web API",
                "endpoint": req.endpoint,
                "request_body": dict(req.body),
                "store_scope": self.store_scope() if req.endpoint == WALMART_ENDPOINT else None,
                "request_id": a.request_id,
                "credits": a.credits,  # results: charged or possibly charged submissions
                "usd": a.cost_usd,
                "cost_source": a.cost_source,
                "remaining_after": None,
                "key_role": a.key_role,
                "key_fingerprint": a.key_fingerprint,
                "attempts": a.attempts,
                "failovers": [],
                "bytes_received": len(a.body),
                # The answer's own metadata (request id, timestamp, applied parameters, the fetched URL).
                "provider_headers": a.headers,
            }
        )
