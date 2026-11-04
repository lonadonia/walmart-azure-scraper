"""Release 1.6.4: a listing total the page reports as 0 is a total of 0.

Live L7 of 2026-11-04 (run 01M6K7HT3XVV8R8CX79P31KMB4, release 1.6.3): Walmart's "Bidets" listing for store
3891 answered with an empty Pickup result grid (``aggregatedCount`` 0) next to an "Available for shipping"
carousel of 10 products (``searchResult.count`` 10). Release 1.6.3 read the listing's total as
``aggregatedCount or count``: it took the 0 for a missing value and the carousel's 10 for the total, and
stopped the run ("the page reports results but shows no product"). The authentic page is
``tests/captures/listing_pages_20261104``; the other pages here are SYNTHETIC."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from tests import synthetic_walmart as syn
from walmart_headless.sites.walmart import page_data as wpd

PAGES = Path(__file__).resolve().parents[1] / "captures" / "listing_pages_20261104"


def page(name: str) -> dict[str, Any]:
    return wpd.next_data(gzip.decompress((PAGES / name).read_bytes()).decode("utf-8"))


def shape(nd: dict[str, Any]) -> tuple[Any, ...]:
    pag = wpd.pagination(nd)
    loc = wpd.page_location(nd)
    return (
        (pag.total_count, pag.page_count, pag.max_page),
        [(s.layout, s.products, s.primary, s.fulfillment_filter) for s in wpd.item_stacks(nd)],
        len(wpd.page_items(nd)),
        wpd.placements(nd),
        (loc.store_id, loc.intent) if loc else None,
    )


def test_the_fixture_matches_its_manifest() -> None:
    for entry in json.loads((PAGES / "MANIFEST.json").read_text("utf-8")):
        data = (PAGES / entry["file"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry["source_sha256"], entry["file"]
        assert hashlib.sha256(gzip.decompress(data)).hexdigest() == entry["content_sha256"], entry["file"]


def test_the_live_bidets_page_reports_a_total_of_zero_not_the_count_of_its_carousel() -> None:
    nd = page("bidets_page1.html.gz")
    pag = wpd.pagination(nd)
    assert (pag.total_count, pag.page_count, pag.max_page) == (0, 10, 0)
    assert [
        (s.layout, s.title, s.count, s.products, s.primary, s.fulfillment_filter) for s in wpd.item_stacks(nd)
    ] == [
        ("GRID", 'Results for "bidets"', 0, 0, True, "Pickup"),
        ("CAROUSEL", "Available for shipping", 838, 10, False, "Shipping"),
    ]
    assert wpd.page_items(nd) == [] and wpd.placements(nd) == 0  # the carousel's products are not results
    loc = wpd.page_location(nd)
    assert loc is not None and (loc.store_id, loc.postal_code, loc.intent) == ("3891", "60085", "PICKUP")


@pytest.mark.parametrize(
    ("search_result", "total"),
    [
        ({"aggregatedCount": 0, "count": 10}, 0),
        ({"aggregatedCount": "0", "count": 10}, 0),
        ({"aggregatedCount": 25, "count": 10}, 25),
        ({"count": 10}, 10),
        ({"aggregatedCount": None, "count": 10}, 10),
        ({"aggregatedCount": 0, "count": 0}, 0),
    ],
    ids=[
        "zero-beside-a-carousel",
        "zero-written-as-text",
        "a-total-above-zero",
        "no-aggregated-count",
        "a-null-aggregated-count",
        "zero-and-no-product",
    ],
)
def test_a_reported_zero_is_the_total_and_count_is_read_only_without_one(
    search_result: dict[str, Any], total: int
) -> None:
    nd = {"props": {"pageProps": {"initialData": {"searchResult": search_result}}}}
    assert wpd.pagination(nd).total_count == total


def test_the_synthetic_copy_has_the_shape_of_the_live_page() -> None:
    carousel = [
        syn.Item(str(7000 + i), f"Synthetic Shipping Product {i}", "$9.99", lines=(("SHIPPING", "0"),))
        for i in range(10)
    ]
    assert shape(wpd.next_data(syn.empty_pickup_grid_page(carousel, store="3891"))) == shape(
        page("bidets_page1.html.gz")
    )
