"""Release 1.6.7: a partition is complete only when every child category ended complete, and a CSV row read
in part is never complete (the client's review of 1.6.6: moving totals, repeated or wrong pages, missing
children and unresolved result windows keep the affected row incomplete). SYNTHETIC listings."""

from __future__ import annotations

import pytest

from walmart_headless.collection import walmart
from walmart_headless.collection.walmart import Listing, listing_outcomes


def partition(child_status: str, child_end: str = "", reason: str = "") -> list[Listing]:
    """Diapering (4 reported) and two child categories whose distinct products are exactly its 4."""
    parent = Listing("Diapering", "u", "5427_486190", status="PARTITIONED", total=4, seen=["a", "b"])
    child1 = Listing(
        "Diapers", "u1", "5427_486190_1", status="DONE", total=3, seen=["a", "c"], parent=parent.id, depth=1
    )
    child2 = Listing(
        "Wipes",
        "u2",
        "5427_486190_2",
        status=child_status,
        total=2,
        seen=["c", "d"],
        parent=parent.id,
        depth=1,
        end=child_end,
        reason=reason,
    )
    return [parent, child1, child2]


def test_a_partition_whose_children_all_ended_complete_and_balance_is_complete() -> None:
    [out] = listing_outcomes(partition("DONE", "LAST_PAGE"))
    assert (out["status"], out["distinct_with_children"], out["difference"]) == ("DONE", 4, 0)


@pytest.mark.parametrize(
    ("end", "reason"),
    [
        ("LAST_PAGE", "the reported total changed while the listing was read ([139, 137, 138])"),
        ("REPEATED_PAGE", "result page 3 repeated page 2"),
        ("IDENTITY", "the listing's own page does not place it under 5427_486190"),
        ("RESULT_WINDOW", "the site served 1,000 of 1,400 results; not partitioned: no child category"),
    ],
    ids=["moving-total", "repeated-page", "wrong-page", "result-window"],
)
def test_a_child_that_did_not_end_complete_keeps_the_partition_incomplete_even_when_identities_balance(
    end: str, reason: str
) -> None:
    """1.6.6 called this partition DONE: its distinct products balance its total exactly, and no child was
    still being read. A child that ended incomplete is evidence the listing's products were not all read
    reliably; the partition stays incomplete and names the child."""
    [out] = listing_outcomes(partition("INCOMPLETE", end, reason))
    assert out["difference"] == 0  # the identities balance ...
    assert out["status"] == "INCOMPLETE"  # ... and the partition is still not complete
    assert "Wipes INCOMPLETE" in out["reason"] and f"({end})" in out["reason"], out["reason"]


def test_a_child_left_by_a_limit_of_the_run_makes_the_partition_capped() -> None:
    [out] = listing_outcomes(partition("CAPPED", "PAGE_LIMIT", "page limit of this run (1) reached"))
    assert out["status"] == "CAPPED"


def test_a_partitioned_child_with_no_child_category_of_its_own_is_not_complete() -> None:
    listings = partition("PARTITIONED")
    [out] = listing_outcomes(listings)
    assert out["status"] == "INCOMPLETE" and "Wipes PARTITIONED" in out["reason"], out


def test_a_partition_with_no_child_recorded_is_not_complete() -> None:
    parent = Listing("Diapering", "u", "5427_486190", status="PARTITIONED", total=2, seen=["a", "b"])
    [out] = listing_outcomes([parent])
    assert out["status"] == "INCOMPLETE" and "no child category" in out["reason"]


def test_a_row_read_through_configured_listings_or_with_listings_not_chosen_is_read_in_part() -> None:
    configured = Listing("Fabric Softeners", "u", "1115193_1071967_1630538", status="DONE", via="configured")
    assert "category page, which names its other listings, was not read" in walmart.row_read_in_part(
        [configured]
    )
    chosen = Listing("Milk", "u1", "976759_9176907", status="DONE", via="category_page")
    left = Listing(
        "Snacks", "u2", "976759_976787", status="SKIPPED", note=walmart.NOT_CHOSEN, via="category_page"
    )
    csv_note = "excluded by the client's CSV"
    excluded = Listing("Recipes", "u3", "976759_1", status="SKIPPED", note=csv_note, via="category_page")
    assert walmart.row_read_in_part([chosen, left, excluded]).startswith("1 of the 3 listings")
    assert walmart.row_read_in_part([chosen, excluded]) == ""  # an exclusion of the client's CSV is not a gap
