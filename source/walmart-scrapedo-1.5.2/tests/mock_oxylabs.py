"""An in-memory mock of the Oxylabs Web API (``httpx.MockTransport``) as its documentation describes it:
``POST /v1/scrape/walmart`` (``url``, ``store_id``, ``fulfillment_type``) and ``POST /v1/scrape`` (``url``,
``location``), Bearer authentication, the answer ``{results[{html, metadata}], params, metadata{request_id,
timestamp}}``. The pages are the SYNTHETIC Walmart pages of the Scrape.do mock (tests/mock_scrapedo.py),
looked up as that mock would serve the same page. Nothing here reaches Oxylabs or Walmart; the key is
invented."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx

from tests.mock_scrapedo import PRIMARY, MockScrapeDo

OXY_KEY = "SyntheticOxylabsKey0000000000000000000000000"  # SYNTHETIC: 44 characters, like a Web API key


class MockOxylabs:
    def __init__(self, site: MockScrapeDo | None = None):
        self.site = site or MockScrapeDo(primary_credits=10**6)
        self.calls: list[tuple[str, dict[str, Any]]] = []  # (endpoint, request body)
        self.authorizations: list[str] = []
        self.answer_override: Callable[[str, dict[str, Any]], httpx.Response | None] | None = None

    def handler(self, request: httpx.Request) -> httpx.Response:
        endpoint = request.url.path
        body = json.loads(request.content or b"{}")
        self.calls.append((endpoint, body))
        self.authorizations.append(request.headers.get("authorization", ""))
        if request.headers.get("authorization") != f"Bearer {OXY_KEY}":
            return httpx.Response(401, json={"message": "Unauthorized"})
        if self.answer_override is not None:
            r = self.answer_override(endpoint, body)
            if r is not None:
                return r
        url = str(body.get("url") or "")
        if endpoint == "/v1/scrape/walmart":
            path = "/plugin/walmart/store"
            if body.get("fulfillment_type") == "pickup" and "/browse/" in url:
                # The Web API asks Walmart for its Pickup grid (live 2026-10-28: the page's own search
                # request carried facet=fulfillment_method:Pickup).
                url += ("&" if "?" in url else "?") + "facet=fulfillment_method%3APickup"
            params = {
                "token": PRIMARY,
                "url": url,
                "storeid": str(body.get("store_id") or ""),
                "zipcode": "60085",
            }
            if "/ip/" in url and self.site.page_override is None:
                path, params = "/", {"token": PRIMARY, "url": url}  # the mock's product pages
        elif endpoint == "/v1/scrape":
            path, params = "/", {"token": PRIMARY, "url": url}
        else:
            return httpx.Response(404, json={"message": "Not found"})
        html, status = self._page(path, params)
        n = len(self.calls)
        return httpx.Response(
            200,
            json={
                "results": [{"html": html, "metadata": {"status_code": status}}],
                "params": {k: v for k, v in body.items() if k != "url"},
                "metadata": {"request_id": f"oxy-{n:05d}", "timestamp": "2026-10-26T12:00:00Z"},
            },
        )

    def _page(self, path: str, params: dict[str, str]) -> tuple[str, int]:
        if self.site.page_override is not None:
            r = self.site.page_override(params["url"])
            if r is not None:
                return r.text, r.status_code
        request = httpx.Request("GET", httpx.URL(f"https://api.scrape.do{path}", params=params))
        return self.site.page(path, request)
