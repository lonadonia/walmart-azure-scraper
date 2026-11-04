"""Result stacks and the listing completion rule (release 1.3.1).

Authentic listing pages of the Azure run of 2026-10-26 (``tests/captures/listing_pages_20261026``):
Citrus, whose page adds an "Available for shipping" carousel after its 21 results, and Apples, whose 39
reported results are 33 organic products and 6 sponsored tiles that repeat 6 of them; and Bath & Body, whose
result grid shows one product twice, the second tile naming options the first does not."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from walmart_headless.collection.walmart import (
    Cursor,
    Listing,
    close_listing,
    listing_outcomes,
    reconcile_listing,
)
from walmart_headless.core import jsonvalues as jv
from walmart_headless.sites.walmart import page_data as wpd
from walmart_headless.sites.walmart import records as wrec

PAGES = Path(__file__).resolve().parents[1] / "captures" / "listing_pages_20261026"


def page(name: str) -> dict[str, Any]:
    return wpd.next_data(gzip.decompress((PAGES / name).read_bytes()).decode("utf-8"))


def test_the_fixtures_match_their_manifest() -> None:
    for entry in json.loads((PAGES / "MANIFEST.json").read_text("utf-8")):
        data = gzip.decompress((PAGES / entry["file"]).read_bytes())
        assert hashlib.sha256(data).hexdigest() == entry["content_sha256"], entry["file"]


def read(name: str, listing_id: str) -> Listing:
    """A listing read from one saved result page the way the collector records it."""
    nd = page(name)
    items = wpd.page_items(nd)
    stacks = wpd.item_stacks(nd)
    pag = wpd.pagination(nd)
    lst = Listing(name, "u", listing_id, status="IN_PROGRESS", total=pag.total_count, max_page=pag.max_page)
    for i in items:
        key = wrec.product_key(i)
        target = lst.sponsored if i.sponsored else lst.seen
        if key not in target:
            target.append(key)
    lst.pages.append(
        {
            "page": 1,
            "products": len(items),
            "reported_total": pag.total_count,
            "other_modules": [{"stack": s.index, "products": s.products} for s in stacks if not s.primary],
        }
    )
    lst.pages_read = 1
    return lst


# -- result stacks ---------------------------------------------------------------------------------------


def test_only_the_result_grid_is_read_not_the_shipping_carousel() -> None:
    nd = page("citrus_page1.html.gz")
    primary, why = wpd.primary_stacks(nd)
    assert primary == [0] and why == "paginationV2.pageProperties.primaryStacksToMatch"
    stacks = wpd.item_stacks(nd)
    assert [(s.layout, s.title, s.products, s.primary) for s in stacks] == [
        ("GRID", 'Results for "citrus"', 21, True),
        ("CAROUSEL", "Available for shipping", 7, False),
    ]
    items = wpd.page_items(nd)
    assert len(items) == 21 and all(".itemStacks[0]." in i.path for i in items)
    carousel = {
        wpd.text(x.get("usItemId"))
        for x in nd["props"]["pageProps"]["initialData"]["searchResult"]["itemStacks"][1]["items"]
    }
    assert len(carousel) == 7 and not carousel & {i.item_id for i in items}
    assert wpd.placements(nd) == stacks[0].entries  # the carousel's tiles are not the listing's


def _nd(stacks: list[dict[str, Any]], named: Any = None) -> dict[str, Any]:
    sr: dict[str, Any] = {"itemStacks": stacks, "aggregatedCount": 1}
    if named is not None:
        sr["paginationV2"] = {"pageProperties": {"primaryStacksToMatch": named}}
    return {"props": {"pageProps": {"initialData": {"searchResult": sr}}}}


ITEM = {"__typename": "Product", "usItemId": "1", "name": "x", "canonicalUrl": "/ip/x/1"}


def test_a_repeated_tile_may_name_options_its_first_tile_does_not() -> None:
    # Bath & Body page 1 shows eos 625527254 twice in its result grid: the first tile names no options, the
    # second its 2-pack and 3-pack, neither of them a tile of its own. Release 1.3.0 kept the options of the
    # tile it recorded (the first) only and never followed the two; release 1.3.1 keeps every tile's options
    # (the collector's ``tile_options`` observations, tests/integration/test_followups.py).
    items = wpd.page_items(page("bath_body_page1.html.gz"))
    eos = [i for i in items if i.item_id == "625527254"]
    assert [i.sponsored for i in eos] == [False, False]
    assert [[(v.item_id, v.value, v.availability) for v in i.variants] for i in eos] == [
        [],
        [("15357773865", "2 Pack", "NOT_AVAILABLE"), ("15349802259", "3 Pack", "NOT_AVAILABLE")],
    ]
    assert not {"15357773865", "15349802259"} & {i.item_id for i in items}


@pytest.mark.parametrize(
    ("stacks", "named"),
    [
        ([{"layoutEnum": "GRID", "items": [ITEM]}, {"layoutEnum": "GRID", "items": [ITEM]}], None),
        ([{"layoutEnum": "CAROUSEL", "items": [ITEM]}, {"layoutEnum": "CAROUSEL", "items": [ITEM]}], None),
        ([{"items": [ITEM]}, {"items": [ITEM]}], None),
        ([{"layoutEnum": "GRID"}, {"layoutEnum": "CAROUSEL"}], [{"isPrimaryStack": True, "matchIndex": 1}]),
        ([{"layoutEnum": "GRID"}, {"layoutEnum": "CAROUSEL"}], [{"isPrimaryStack": True, "matchIndex": 5}]),
        ([{"layoutEnum": "GRID"}, {"layoutEnum": "CAROUSEL"}], [{"isPrimaryStack": False, "matchIndex": 0}]),
    ],
)
def test_a_page_whose_results_cannot_be_told_from_other_modules_is_refused(
    stacks: list[dict[str, Any]], named: Any
) -> None:
    with pytest.raises(wpd.PageShapeUnclear):
        wpd.page_items(_nd(stacks, named))


def test_a_page_without_a_primary_list_reads_its_only_grid_or_its_only_stack() -> None:
    assert wpd.primary_stacks(_nd([{"layoutEnum": "CAROUSEL"}, {"layoutEnum": "GRID"}]))[0] == [1]
    assert wpd.primary_stacks(_nd([{"items": [ITEM]}]))[0] == [0]
    assert wpd.primary_stacks(_nd([])) == ([], "no item stack")


# -- the completion rule ---------------------------------------------------------------------------------


def test_citrus_replayed_with_its_result_grid_only_balances_exactly() -> None:
    lst = read("citrus_page1.html.gz", "976759_976793_9756351_4914029")
    assert (len(lst.seen), lst.sponsored, lst.total) == (21, [], 21)
    close_listing(lst, "LAST_PAGE", 1)
    assert lst.status == "DONE" and lst.reconciliation["basis"] == "organic"
    assert lst.reconciliation["difference"] == 0


def test_the_release_1_3_0_reading_of_citrus_is_an_overcount_never_done() -> None:
    # Release 1.3.0 read the carousel as results: 28 organic identities for 21 reported.
    nd = page("citrus_page1.html.gz")
    stacks = nd["props"]["pageProps"]["initialData"]["searchResult"]["itemStacks"]
    all_ids = [
        wpd.text(x.get("usItemId")) for s in stacks for x in s["items"] if x.get("__typename") == "Product"
    ]
    lst = Listing("Citrus", "u", "c", status="IN_PROGRESS", total=21, max_page=1, pages_read=1)
    lst.seen = [f"wm:{i}" for i in dict.fromkeys(all_ids)]
    lst.pages = [{"page": 1, "products": len(all_ids), "reported_total": 21}]
    assert len(lst.seen) == 28
    close_listing(lst, "LAST_PAGE", 1)
    assert lst.status == "INCOMPLETE" and lst.reason.startswith("overcount")
    assert lst.reconciliation["difference"] == -7  # signed: never clamped to zero


def test_apples_balances_by_its_tiles_with_six_sponsored_repeats() -> None:
    lst = read("apples_page1.html.gz", "976759_976793_9756351_7796396")
    assert (len(lst.seen), len(lst.sponsored), lst.total) == (33, 6, 39)
    assert set(lst.sponsored) <= set(lst.seen)  # every sponsored tile repeats an organic product
    close_listing(lst, "LAST_PAGE", 1)
    r = lst.reconciliation
    assert lst.status == "DONE" and r["basis"] == "placements"
    assert (r["placed"], r["placements"], r["repeat_placements"], r["difference"]) == (33, 39, 6, 6)
    assert "6 sponsored tiles repeat organic products" in lst.reason


def _listing(seen: int, total: int | None, *, sponsored: int = 0, tiles: int | None = None,
             totals: list[int] | None = None) -> Listing:  # fmt: skip
    lst = Listing("L", "u", "l", status="IN_PROGRESS", total=total, pages_read=1)
    lst.seen = [f"wm:{i}" for i in range(seen)]
    lst.sponsored = [f"wm:s{i}" for i in range(sponsored)]
    reported = totals if totals is not None else [total]
    lst.pages = [
        {
            "page": n + 1,
            "products": (tiles if tiles is not None else seen + sponsored) if n == 0 else 0,
            "reported_total": t,
        }
        for n, t in enumerate(reported)
    ]
    return lst


def test_sponsored_only_identities_can_balance_the_total() -> None:
    lst = _listing(27, 29, sponsored=2)
    close_listing(lst, "LAST_PAGE", 1)
    assert lst.status == "DONE" and lst.reconciliation["basis"] == "organic_and_sponsored"


def test_reaching_the_last_page_short_of_the_total_is_a_result_window_never_done() -> None:
    lst = _listing(33, 39)
    close_listing(lst, "LAST_PAGE", 1)
    assert lst.status == "INCOMPLETE" and lst.end == "RESULT_WINDOW"
    assert "accessible pages exhausted; coverage incomplete" in lst.reason
    assert lst.reconciliation["difference"] == 6


def test_a_listing_is_done_only_at_a_final_end_with_a_stable_total() -> None:
    lst = _listing(10, 10)
    close_listing(lst, "REPEATED_PAGE", 2, "result page 2 repeated earlier products")
    assert lst.status == "INCOMPLETE"  # the count balances, but the site repeated a page
    lst = _listing(617, 617, totals=[618, 617])
    close_listing(lst, "LAST_PAGE", 16)
    assert lst.status == "INCOMPLETE" and "reported total changed" in lst.reason
    lst = _listing(10, 10)
    close_listing(lst, "EMPTY_PAGE", 2)
    assert lst.status == "DONE"
    lst = _listing(10, None)
    close_listing(lst, "LAST_PAGE", 1)
    assert lst.status == "INCOMPLETE" and "no result count" in lst.reason


def test_a_moving_total_far_above_what_the_site_served_is_a_result_window_never_done() -> None:
    # Live 2026-11-03, Laundry (release 1.6.1 left it unpartitioned): 615, 613, 614 and 611 reported while it
    # was read, page 11 of the 16 linked empty, 393 served.
    lst = _listing(393, 611, totals=[615, 613, 614, 611])
    close_listing(lst, "EMPTY_PAGE", 11, "result page 11 shows no products")
    assert lst.status == "INCOMPLETE" and lst.end == "RESULT_WINDOW"
    assert lst.reason.startswith("accessible pages exhausted; coverage incomplete")
    assert "between 611 and 615 results" in lst.reason and lst.reason.endswith("not reconciled")
    assert lst.reconciliation["total_stable"] is False and lst.reconciliation["basis"] == ""
    # Live 2026-11-03, Fresh Vegetables: the last linked page reached, 289, 288 and 287 reported, 277 served.
    lst = _listing(277, 287, totals=[289, 288, 287])
    close_listing(lst, "LAST_PAGE", 7)
    assert lst.status == "INCOMPLETE" and lst.end == "RESULT_WINDOW"


def test_a_shortfall_no_larger_than_the_totals_moved_stays_unreconciled_not_a_window() -> None:
    lst = _listing(616, 617, totals=[618, 617])  # 1 short of the smallest total, which moved by 1
    close_listing(lst, "LAST_PAGE", 16)
    assert lst.status == "INCOMPLETE" and lst.end == "LAST_PAGE"
    assert "reported total changed" in lst.reason and "accessible pages" not in lst.reason
    lst = _listing(130, 134, totals=[134, 130])  # the smallest total reached: nothing says it is short
    close_listing(lst, "LAST_PAGE", 4)
    assert lst.status == "INCOMPLETE" and lst.end == "LAST_PAGE"


def test_more_identities_than_reported_is_an_overcount_whatever_the_sponsored_tiles() -> None:
    lst = _listing(21, 21, sponsored=2)  # organic balances: the sponsored-only extras are outside the total
    close_listing(lst, "LAST_PAGE", 1)
    assert lst.status == "DONE" and lst.reconciliation["basis"] == "organic"
    lst = _listing(22, 21)
    close_listing(lst, "LAST_PAGE", 1)
    assert lst.status == "INCOMPLETE" and lst.reason.startswith("overcount")
    lst = _listing(30, 39, tiles=40)  # fewer identities, more tiles: neither a window nor a balance
    close_listing(lst, "LAST_PAGE", 1)
    assert lst.status == "INCOMPLETE" and lst.reason.startswith("unreconciled")


def test_reconcile_listing_reports_the_signed_difference() -> None:
    r = reconcile_listing(({"a", "b", "c"}, {"d"}), [3], 3, 4)
    assert r["basis"] == "organic" and r["difference"] == -1 and r["sponsored_only"] == 1
    assert r["unresolved_difference"] == 0  # the sponsored-only identity is outside the organic total
    r = reconcile_listing(({"a"}, set()), [], None, 1)
    assert r["basis"] == "" and r["difference"] is None and r["unresolved_difference"] is None


def test_a_balanced_listing_leaves_no_unresolved_difference_for_the_coverage_gate() -> None:
    # Release 1.3.1 defect (found 2026-10-27): the coverage gate (G3) read "reported minus placed", so a
    # listing that balanced exactly on its organic identities or its tiles failed it whenever sponsored
    # tiles were served. The gate reads the unresolved difference: 0 when a basis holds, else the signed one.
    apples = read("apples_page1.html.gz", "976759_976793_9756351_7796396")
    close_listing(apples, "LAST_PAGE", 1)
    organic = _listing(21, 21, sponsored=3)  # 3 sponsored-only identities beyond an organic total
    close_listing(organic, "LAST_PAGE", 1)
    over = _listing(22, 21)
    close_listing(over, "LAST_PAGE", 1)
    window = _listing(33, 39)
    close_listing(window, "LAST_PAGE", 1)
    got = [
        (o["status"], o["basis"], o["difference"], o["unresolved_difference"])
        for o in (listing_outcomes([x])[0] for x in (apples, organic, over, window))
    ]
    assert got == [
        ("DONE", "placements", 6, 0),
        ("DONE", "organic", -3, 0),
        ("INCOMPLETE", "", -1, -1),
        ("INCOMPLETE", "", 6, 6),
    ]


def test_a_partitioned_listing_balances_exactly_with_its_child_categories() -> None:
    parent = Listing("Diapering", "u", "5427_486190", status="PARTITIONED", total=4, seen=["a", "b"])
    child = Listing("Diapers", "u1", "5427_486190_1", status="DONE", total=3, seen=["a", "c", "d", "e"],
                    parent=parent.id)  # fmt: skip
    [out] = listing_outcomes([parent, child])
    assert out["status"] == "INCOMPLETE" and out["difference"] == -1  # 5 distinct for 4 reported
    assert out["unresolved_difference"] == -1


# -- checkpoints -----------------------------------------------------------------------------------------


def test_a_checkpoint_of_release_1_3_0_still_reads_and_a_damaged_one_is_refused() -> None:
    old = {"name": "Citrus", "url": "u", "id": "c", "status": "DONE", "pages_read": 1, "total": 21,
           "max_page": 1, "seen": ["wm:1"], "reason": "", "end": "LAST_PAGE", "via": "category_page",
           "parent": "", "depth": 0, "children": [], "pages": [{"page": 1}], "note": ""}  # fmt: skip
    cur = Cursor.from_dict({"listings": [old]})
    assert cur.listings is not None and cur.listings[0].sponsored == []
    with pytest.raises(jv.CorruptJson):
        Cursor.from_dict({"listings": [{**old, "total": "21"}]})
    with pytest.raises(jv.CorruptJson):
        Cursor.from_dict({"listings": [{**old, "unexpected": 1}]})
    with pytest.raises(jv.CorruptJson):
        Cursor.from_dict({"listings": [["not", "an", "object"]]})


def test_the_json_readers_check_shapes() -> None:
    assert jv.obj(None, "x") == {} and jv.objects(None, "x") == [] and jv.text(None, "x") == ""
    assert jv.text(42, "x") == "42" and jv.integer(None, "x") is None and jv.texts(["a"], "x") == ["a"]
    bad: list[Any] = [
        lambda: jv.obj([1], "x"),
        lambda: jv.objects({"a": 1}, "x"),
        lambda: jv.text(True, "x"),
        lambda: jv.integer("1", "x"),
        lambda: jv.texts([1.5], "x"),
        lambda: jv.obj({1: "a"}, "x"),
    ]
    for read_bad in bad:
        with pytest.raises(jv.CorruptJson):
            read_bad()
