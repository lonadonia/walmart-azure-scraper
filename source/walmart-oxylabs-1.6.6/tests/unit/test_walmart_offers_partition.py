"""Release 1.2.0 parsing on SYNTHETIC pages (``tests/synthetic_walmart.py``): promotion terms are kept whole
with their conditions, structured promotion data without wording is only logged, and a listing's own
"Departments" facet names its child categories. Nothing here is live data."""

from __future__ import annotations

from tests import synthetic_walmart as syn
from walmart_headless.collection.walmart import Listing, listing_outcomes
from walmart_headless.sites.walmart import page_data as wpd
from walmart_headless.sites.walmart import records as wrec

STORE = "3891"
LONG_TERMS = (
    "Buy 2, get 1 free on select items. Limit 1 offer per order; W+ members only; valid through 11/30/2026; "
    "available for Pickup and Delivery from the store only, not for shipping; while supplies last; "
    "the lowest-priced item is free; offer may change without notice."
)


def _item(**kw: object) -> wpd.WalmartItem:
    page = syn.listing_page([syn.Item("51", "Soda, 12 fl oz", "$4.99", **kw)], store=STORE)  # type: ignore[arg-type]
    (it,) = wpd.page_items(wpd.next_data(page))
    return it


def test_long_promotion_terms_are_kept_whole_and_links_are_not_text() -> None:
    assert len(LONG_TERMS) > 200
    it = _item(
        extra={
            "promoData": [{"description": LONG_TERMS, "terms": "walmart://promo/landing", "url": "/promo"}]
        }
    )
    assert it.promo_texts == (LONG_TERMS,)  # earlier releases dropped any string over 200 characters
    deals, _ = wrec.deal_texts(it)
    assert deals == [LONG_TERMS]


def test_an_offer_that_names_a_fulfillment_or_a_membership_stays_an_offer_with_its_conditions() -> None:
    it = _item(badges=(("MULTI", "2 for $6.00, Pickup only"), ("WP", "W+ members: Save $1 when you buy 2")))
    deals, other = wrec.deal_texts(it)
    assert deals == ["2 for $6.00, Pickup only", "W+ members: Save $1 when you buy 2"]
    assert not other


def test_structured_promotion_data_without_wording_is_logged_never_exported() -> None:
    promo = {"discount": 1.89, "type": "CONFIG_PROMO", "state": "UNLOCK", "maxPerTxn": 1, "promoOffer": "1"}
    it = _item(extra={"promoDiscount": promo})
    assert it.promo_texts == () and it.promo_structured[0]["discount"] == 1.89
    _, _, log = wrec.evidence(
        it,
        fetch_id="f",
        observed_at="2026-10-24T05:00:00Z",
        store_id=STORE,
        modality="PICKUP",
        page_verified=True,
    )
    assert log["promotion_data"][0]["state"] == "UNLOCK"
    ev, _, _ = wrec.evidence(
        it,
        fetch_id="f",
        observed_at="2026-10-24T05:00:00Z",
        store_id=STORE,
        modality="PICKUP",
        page_verified=True,
    )
    assert ev.offers == ()  # no description and no price is made from it


def test_a_listings_own_departments_facet_names_its_direct_child_categories() -> None:
    html = syn.listing_page(
        [],
        store=STORE,
        departments=[
            ("5427_486190_1101406", "Diapers", "/browse/baby/diapers/5427_486190_1101406"),
            (
                "5427_486190_1101406_1101408",
                "Disposable Diapers",
                "/browse/baby/x/5427_486190_1101406_1101408",
            ),
            ("5440_1", "Elsewhere", "/browse/pets/5440_1"),
            ("5427_486190_9", "Mismatched link", "/browse/baby/other/5427_486190_8"),
        ],
    )
    children = wpd.child_categories(wpd.next_data(html), "5427_486190")
    assert [c.id for c in children] == ["5427_486190_1101406", "5427_486190_1101406_1101408"]
    assert children[0].url == "https://www.walmart.com/browse/baby/diapers/5427_486190_1101406"
    assert children[0].facet == "cat_id"


def test_a_partitioned_listing_counts_distinct_products_never_added_up_totals() -> None:
    parent = Listing("Diapering", "u", "5427_486190", status="PARTITIONED", total=4, seen=["a", "b"])
    child1 = Listing(
        "Diapers", "u1", "5427_486190_1", status="DONE", total=3, seen=["a", "c", "d"], parent=parent.id
    )
    child2 = Listing(
        "Wipes", "u2", "5427_486190_2", status="DONE", total=2, seen=["c", "d"], parent=parent.id
    )
    [out] = listing_outcomes([parent, child1, child2])
    # 3 + 2 child results would "cover" 4; the distinct products are a, b, c, d: 4 of 4, exactly.
    assert out["status"] == "DONE" and out["distinct_with_children"] == 4
    assert out["difference"] == 0 and out["basis"] == "organic"
    child2.seen = ["c"]
    child1.seen = ["a", "c"]
    [out] = listing_outcomes([parent, child1, child2])
    assert out["status"] == "INCOMPLETE" and out["distinct_with_children"] == 3 and out["difference"] == 1


def test_a_record_kept_without_a_local_price_is_verified_against_a_page_without_the_stores_line(
    tmp_path: object,
) -> None:
    """The validator reads the page itself: a record whose prices are empty because the page shows no Pickup
    line for the store (a verified product now out of stock without fulfillment) is verified on its other
    fields; empty prices while the page has the store's Pickup line are a mismatch."""
    import gzip
    import json as _json
    from pathlib import Path

    from walmart_headless.checks import source_check

    out_of_stock = syn.Item("61", "Fresh Whole Shallots 16oz Bag", "$2.88", unit="18.0 ¢/oz", lines=(),
                            availability="OUT_OF_STOCK")  # fmt: skip
    in_stock = syn.Item("62", "Fresh Garlic, 3 ct", "$1.48")
    folder = Path(str(tmp_path))
    (folder / "p1.html.gz").write_bytes(
        gzip.compress(syn.listing_page([out_of_stock, in_stock], store=STORE).encode())
    )
    nd = wpd.next_data(syn.listing_page([out_of_stock, in_stock], store=STORE))
    a, b2 = wpd.page_items(nd)

    def rec(it: wpd.WalmartItem) -> dict[str, str]:
        return {"product_title": it.name, "url": it.url, "image_url": it.image_url, "regular_price": "",
                "sale_price": "", "ppm": ""}  # fmt: skip

    res = source_check.check([rec(a), rec(b2)], folder, STORE)
    by_url = {r["url"]: r for r in res["results"]}
    assert by_url[a.url]["result"] == "verified_without_local_price"
    assert by_url[b2.url]["result"] == "mismatch" and "regular_price" in by_url[b2.url]["mismatched_fields"]
    assert res["summary"]["verified_without_local_price"] == 1
    assert _json.dumps(res)  # serialisable for validate-export


def test_a_record_without_a_local_price_is_judged_on_the_page_that_shows_it_without_the_stores_line(
    tmp_path: object,
) -> None:
    """Release 1.3.1: the validator chose the best page for a record before it set aside the prices of a page
    without the store's Pickup line, so when the product's earlier page (with the line) scored as well as the
    page that shows it without the line, it could choose the earlier page and report a mismatch. Found with
    Fresh Strawberries 1175460573 (live 2026-10-26: in stock with store 3891's Pickup line at 21:52Z, out of
    stock without it at 23:01Z) in the offline reprocessing of the repeat run 01M5X73P62ZGKT7AZBMFY1JBV5."""
    import gzip
    from pathlib import Path

    from walmart_headless.checks import source_check

    name = "Fresh Strawberries, 8.8 oz Container"
    earlier = syn.Item("71", name, "$1.97", unit="22.4 ¢/oz")
    later = syn.Item("71", name, "$1.97", unit="22.4 ¢/oz", lines=(), availability="OUT_OF_STOCK")
    folder = Path(str(tmp_path))
    # The earlier page sorts first, as the main run's pages did.
    (folder / "a_earlier.html.gz").write_bytes(
        gzip.compress(syn.listing_page([earlier], store=STORE).encode())
    )
    (folder / "b_later.html.gz").write_bytes(gzip.compress(syn.listing_page([later], store=STORE).encode()))
    (it,) = wpd.page_items(wpd.next_data(syn.listing_page([later], store=STORE)))
    record = {"product_title": it.name, "url": it.url, "image_url": it.image_url, "regular_price": "",
              "sale_price": "", "ppm": ""}  # fmt: skip
    [result] = source_check.check([record], folder, STORE)["results"]
    assert result["result"] == "verified_without_local_price"
    assert result["source"]["page"] == "b_later.html.gz" and result["source"]["pages_with_item"] == 2
    assert result["page"]["pickup_at_store"] is False
    # With only the page that shows the store's Pickup line, the empty prices are a mismatch.
    (folder / "b_later.html.gz").unlink()
    [result] = source_check.check([record], folder, STORE)["results"]
    assert result["result"] == "mismatch" and set(result["mismatched_fields"]) == {"regular_price", "ppm"}


def test_the_store_logo_is_the_image_of_the_headers_homepage_link_on_the_captured_store_page() -> None:
    """AUTHENTIC: the store page W1 captured on 2026-10-21 (tests/captures). Its header has two "Walmart
    Homepage" links: a mobile one with an icon-font glyph and a desktop one with the logo image."""
    import gzip
    from pathlib import Path

    capture = Path(__file__).resolve().parents[1] / "captures" / "w1_20261021" / "store_page.html.gz"
    logo, where = wpd.header_logo(gzip.decompress(capture.read_bytes()).decode("utf-8"))
    assert (
        logo
        == "https://i5.walmartimages.com/dfw/63fd9f59-14e2/9d304ce6-96de-4331-b8ec-c5191226d378/v1/spark-icon.svg"
    )
    assert "walmartLogoDesktop" in where
    assert wpd.header_logo(
        "<html><body><a aria-label='Walmart Homepage'><i class='ld'></i></a></body></html>"
    ) == ("", "")
