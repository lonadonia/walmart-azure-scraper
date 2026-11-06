"""Release 1.6.8: a subcategory linked as a category page of its own (/cp/) is read for the listings it
names (EXPANDED); those listings are judged each on their own, and the page keeps its row open until it
is read."""

from __future__ import annotations

from walmart_headless.collection import reconcile
from walmart_headless.collection.walmart import (
    NOT_A_CATEGORY,
    Listing,
    listing_outcomes,
    subcategory_page,
)


def test_only_a_category_page_link_is_a_subcategory_page() -> None:
    assert subcategory_page("https://www.walmart.com/cp/chips/1001390?povid=976759_LHNCP")
    assert not subcategory_page("https://www.walmart.com/browse/food/milk/976759_9176907")
    assert not subcategory_page("https://www.walmart.com/shop/only-at-walmart")
    assert not subcategory_page("https://www.walmart.com/brand/post-it/10017935")
    assert "not a category or result listing" in NOT_A_CATEGORY


def _done(name: str, lid: str, **kw: object) -> Listing:
    return Listing(name, f"https://www.walmart.com/browse/food/{name}/{lid}", lid, status="DONE", **kw)  # type: ignore[arg-type]


def test_an_expanded_page_is_no_listing_its_listings_are_judged_each_on_their_own() -> None:
    page = Listing("Chips", "https://www.walmart.com/cp/chips/1001390", "1001390", status="EXPANDED")
    found = _done("potato-chips", "976759_976787_1001390_1", via="subcategory_page", found_on="1001390")
    other = _done("milk", "976759_9176907", via="category_page")
    outcomes = listing_outcomes([page, found, other])
    assert [o["id"] for o in outcomes] == ["976759_976787_1001390_1", "976759_9176907"]
    assert {o["status"] for o in outcomes} == {"DONE"}


def test_a_subcategory_page_not_read_keeps_its_row_open() -> None:
    for status in ("PENDING", "IN_PROGRESS", "INCOMPLETE", "CAPPED"):
        page = Listing("Chips", "https://www.walmart.com/cp/chips/1001390", "1001390", status=status)
        outcomes = listing_outcomes([page, _done("milk", "976759_9176907")])
        assert [o["status"] for o in outcomes if o["id"] == "1001390"] == [status]


def test_the_coverage_report_counts_an_expanded_page_as_read_and_keeps_its_status() -> None:
    assert "EXPANDED" in reconcile.COMPLETE_OUTCOMES and "EXPANDED" in reconcile.NOT_DECIDED
    page = Listing("Chips", "https://www.walmart.com/cp/chips/1001390", "1001390", status="EXPANDED")
    status, _ = reconcile.rule_status(page, set(), set())
    assert status == "EXPANDED"
    assert reconcile.COLUMNS[-3:] == ("found_on", "filtered_view", "filtered_view_of")


def test_the_page_a_listing_was_found_on_is_kept_in_its_checkpoint() -> None:
    lst = Listing("Potato Chips", "u", "976759_976787_1001390_1", via="subcategory_page", found_on="1001390")
    d = {k: v for k, v in lst.__dict__.items()}
    assert Listing.from_dict(d, "test").found_on == "1001390"
    del d["found_on"]  # a checkpoint of release 1.6.7 or earlier
    assert Listing.from_dict(d, "test").found_on == ""
