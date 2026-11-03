"""Walmart's Pickup grid and the store's unfiltered grid (release 1.4.1).

Authentic pages (``tests/captures/listing_pages_20261028``): the Strawberries listing of store #3891 read half
an hour apart on 2026-10-28 through Scrape.do's store endpoint, which sets the store only (the store's
unfiltered grid), and through the Oxylabs Web API with ``fulfillment_type`` pickup (Walmart's Pickup grid).
Release 1.4.1 requests the Scrape.do edition's result pages with Walmart's own facet and records each grid's
filter."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from walmart_headless.acquisition import scrapedo_session as sds
from walmart_headless.sites.walmart import page_data as wpd

PAGES = Path(__file__).resolve().parents[1] / "captures" / "listing_pages_20261028"
LISTING = "https://www.walmart.com/browse/food/strawberries/976759_976793_9756351_3521037"
PICKUP = sds.FULFILLMENT_FACETS["PICKUP"]


def page(name: str) -> dict[str, Any]:
    return wpd.next_data(gzip.decompress((PAGES / name).read_bytes()).decode("utf-8"))


def test_the_fixtures_match_their_manifest() -> None:
    for entry in json.loads((PAGES / "MANIFEST.json").read_text("utf-8")):
        data = gzip.decompress((PAGES / entry["file"]).read_bytes())
        assert hashlib.sha256(data).hexdigest() == entry["content_sha256"], entry["file"]


def test_the_store_endpoints_grid_names_no_filter_and_the_web_apis_is_the_pickup_grid() -> None:
    sd, ox = page("strawberries_scrapedo_page1.html.gz"), page("strawberries_oxylabs_page1.html.gz")
    [sd_grid], [ox_grid] = wpd.item_stacks(sd), wpd.item_stacks(ox)
    assert (sd_grid.primary, sd_grid.fulfillment_filter, sd_grid.count) == (True, "", 5)
    assert (ox_grid.primary, ox_grid.fulfillment_filter, ox_grid.count) == (True, "Pickup", 2)
    assert (wpd.pagination(sd).total_count, wpd.pagination(ox).total_count) == (5, 2)
    unfiltered = {i.item_id: i.availability for i in wpd.page_items(sd)}
    pickup = {i.item_id: i.availability for i in wpd.page_items(ox)}
    # The unfiltered grid's reported total counts the store's out-of-stock products too.
    assert sorted(k for k, v in unfiltered.items() if v == "OUT_OF_STOCK") == [
        "1175460573",
        "45618183",
        "649701131",
    ]
    assert (
        pickup
        == {k: v for k, v in unfiltered.items() if v == "IN_STOCK"}
        == {
            "44391605": "IN_STOCK",
            "22660282": "IN_STOCK",
        }
    )


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (LISTING, f"{LISTING}?facet=fulfillment_method%3APickup"),
        (f"{LISTING}?page=2", f"{LISTING}?page=2&facet=fulfillment_method%3APickup"),
        # Joined to the URL's own facets as Walmart's filter links join them ("||").
        (
            f"{LISTING}?facet=brand%3AFresh+Produce&page=3",
            f"{LISTING}?page=3&facet=brand%3AFresh+Produce%7C%7Cfulfillment_method%3APickup",
        ),
        (f"{LISTING}?facet=&page=2", f"{LISTING}?page=2&facet=fulfillment_method%3APickup"),
        # Already there: the URL is kept as it is.
        (
            f"{LISTING}?facet=fulfillment_method%3APickup&page=2",
            f"{LISTING}?facet=fulfillment_method%3APickup&page=2",
        ),
    ],
)
def test_the_facet_joins_the_urls_own_facets_and_keeps_its_page(url: str, expected: str) -> None:
    assert sds.with_facet(url, PICKUP) == expected
    assert wpd.listing_id(expected) == wpd.listing_id(url)


def _session(facet: str | None) -> sds.ScrapeDoWalmartSession:
    return sds.ScrapeDoWalmartSession(
        None,  # type: ignore[arg-type]  # no request is sent
        None,  # type: ignore[arg-type]
        "runs/synthetic",
        store_id="3891",
        zipcode="60085",
        store_page_url="https://www.walmart.com/store/3891-waukegan-il",
        sanitizer=lambda html: (html, None),
        listing_facet=facet,
    )


def test_only_result_pages_are_requested_with_the_facet() -> None:
    s = _session(PICKUP)
    req = s._request(f"{LISTING}?page=2", "listing")
    assert req.endpoint == sds.WALMART_STORE_ENDPOINT
    assert req.params == {
        "url": f"{LISTING}?page=2&facet=fulfillment_method%3APickup",
        "storeid": "3891",
        "zipcode": "60085",
    }
    # A product page is the store's page of one product: no grid, no facet.
    product = s._request("https://www.walmart.com/ip/22660282", "product_page")
    assert product.params["url"] == "https://www.walmart.com/ip/22660282"
    for url, purpose in (
        ("https://www.walmart.com/robots.txt", "robots"),
        ("https://www.walmart.com/store/3891-waukegan-il", "store_page"),
        ("https://www.walmart.com/cp/food/976759", "category_page"),
        ("https://www.walmart.com/ip/22660282", "product_detail"),
    ):
        req = s._request(url, purpose)
        assert (req.endpoint, req.params["url"]) == (sds.GENERAL_ENDPOINT, url)
    # Without a facet (a fulfillment that has none) a result page is requested as the collector names it.
    assert _session(None)._request(LISTING, "listing").params["url"] == LISTING
