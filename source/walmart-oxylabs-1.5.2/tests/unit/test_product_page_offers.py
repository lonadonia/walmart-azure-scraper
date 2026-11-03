"""The local-offer decision on a product's own page (release 1.3.1), read from three authentic product pages
of the Azure run of 2026-10-26 (``tests/captures/product_pages_20261026``). A product page names its seller
in ``sellerDisplayName`` with ``sellerType``; release 1.3.0 read ``sellerName`` (a listing tile's key)
only, so a marketplace seller's product read by a follow-up was recorded as "assortment unresolved", never
as a marketplace offer. Listing tiles name the seller in ``sellerName`` and are read as before."""

from __future__ import annotations

import gzip
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from walmart_headless.sites.walmart import page_data as wpd
from walmart_headless.sites.walmart import records as wrec

CAPTURES = Path(__file__).resolve().parents[1] / "captures"
PAGES = CAPTURES / "product_pages_20261026"


def page_data(name: str) -> dict[str, Any]:
    return wpd.next_data(gzip.decompress((PAGES / name).read_bytes()).decode("utf-8"))


def product(name: str, **changes: Any) -> wpd.ProductPage:
    nd = page_data(name)
    nd["props"]["pageProps"]["initialData"]["data"]["product"].update(changes)
    pp = wpd.product_page(nd)
    assert pp is not None and pp.item is not None
    return pp


def test_the_pages_match_their_manifest() -> None:
    for entry in json.loads((PAGES / "MANIFEST.json").read_text("utf-8")):
        data = gzip.decompress((PAGES / entry["file"]).read_bytes())
        assert hashlib.sha256(data).hexdigest() == entry["content_sha256"], entry["file"]


def test_a_walmart_sold_product_with_a_pickup_line_for_the_store_is_the_stores() -> None:
    pp = product("walmart_seller_15268670678.html.gz")
    assert pp.item is not None
    assert (pp.item.seller_name, pp.item.seller_type, pp.offer_type) == (
        "Walmart.com",
        "INTERNAL",
        "ONLINE_AND_STORE",
    )
    offer = wrec.local_offer(pp.item, "3891", "PICKUP")
    assert offer.walmart_seller is True and not offer.marketplace
    assert offer.accepted and offer.pickup_price


def test_a_marketplace_sellers_product_page_is_a_marketplace_offer() -> None:
    pp = product("marketplace_15163163334.html.gz")
    assert pp.item is not None
    assert (pp.item.seller_name, pp.item.seller_type, pp.offer_type) == (
        "DealZone Inc",
        "EXTERNAL",
        "ONLINE_ONLY",
    )
    offer = wrec.local_offer(pp.item, "3891", "PICKUP")
    assert offer.marketplace and offer.walmart_seller is False and not offer.accepted
    assert offer.note == "sold by 'DealZone Inc', a marketplace seller: no local store price"
    ev, _, log = wrec.evidence(
        pp.item, fetch_id="f", observed_at="2026-10-26T22:32:12Z", store_id="3891", modality="PICKUP",
        page_verified=True,
    )  # fmt: skip
    assert ev.is_marketplace and not ev.location_attested
    assert log["seller"] == {
        "name": "DealZone Inc",
        "id": pp.item.seller_id,
        "type": "EXTERNAL",
        "walmart": False,
    }


def test_an_external_seller_without_a_name_is_still_a_marketplace_offer() -> None:
    pp = product("marketplace_15163163334.html.gz", sellerDisplayName=None)
    assert pp.item is not None and pp.item.seller_name == ""
    offer = wrec.local_offer(pp.item, "3891", "PICKUP")
    assert offer.marketplace and offer.walmart_seller is None
    assert "an external seller (sellerType EXTERNAL)" in offer.note


def test_out_of_stock_without_a_store_line_establishes_neither_assortment_nor_price() -> None:
    # The Pickup option names the store only by name ("Waukegan Supercenter", OUT_OF_STOCK); no line of the
    # page's fulfillmentSummary names store 3891. Out of stock alone is not taken as the store's assortment.
    pp = product("out_of_stock_994998279.html.gz")
    assert pp.item is not None
    assert ("PICKUP", "OUT_OF_STOCK", "Waukegan Supercenter") in pp.options
    offer = wrec.local_offer(pp.item, "3891", "PICKUP")
    assert offer.walmart_seller is True and not offer.marketplace and offer.out_of_stock
    assert not offer.store_line and not offer.accepted
    assert offer.note.startswith("out of stock, and no fulfillment line for store 3891")


@pytest.mark.parametrize(
    "capture",
    [
        "listing_pages_20261026/apples_page1.html.gz",
        "listing_pages_20261026/citrus_page1.html.gz",
        "w1_20261021/diapering_page1.html.gz",
        "w1_20261021/diapering_page2.html.gz",
    ],
)
def test_listing_tiles_name_their_seller_in_seller_name_and_are_read_as_before(capture: str) -> None:
    nd = wpd.next_data(gzip.decompress((CAPTURES / capture).read_bytes()).decode("utf-8"))
    items = wpd.page_items(nd)
    assert items
    raw = {
        str(r.get("usItemId")): r
        for stack in nd["props"]["pageProps"]["initialData"]["searchResult"]["itemStacks"]
        for r in stack.get("items") or []
    }
    for i in items:
        tile = raw[i.item_id]
        # The tile's own seller key, as release 1.3.0 read it; tiles leave sellerDisplayName and sellerType
        # empty, so the product-page fallback never applies to them.
        assert i.seller_name == (tile.get("sellerName") or "") != ""
        assert not tile.get("sellerDisplayName") and not tile.get("sellerType") and i.seller_type == ""


def test_a_page_that_names_no_seller_establishes_the_store_line_but_no_price() -> None:
    """Release 1.5.0: a local price needs Walmart as the seller, from the source. Until 1.4.1 a page with no
    seller at all counted as Walmart's. In the 1.4.1 evidence 1 of 5,470 tiles names no seller, without a
    Pickup line, so no exported price changes; the rule closes the gap for the future."""
    base = product("walmart_seller_15268670678.html.gz")
    assert base.item is not None
    item = replace(base.item, seller_name="", seller_type="")
    offer = wrec.local_offer(item, "3891", "PICKUP")
    assert offer.walmart_seller is None and not offer.seller_verified and not offer.marketplace
    if offer.for_store:
        assert offer.accepted and not offer.pickup_price and "names no seller" in offer.note
    internal = wrec.local_offer(replace(item, seller_type="INTERNAL"), "3891", "PICKUP")
    assert internal.seller_verified
    assert internal.pickup_price == internal.for_store
    external = wrec.local_offer(replace(item, seller_type="EXTERNAL"), "3891", "PICKUP")
    assert external.marketplace and not external.pickup_price
