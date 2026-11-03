"""Estimated each prices and weight pricing (release 1.3.1, rule changed in release 1.4.0).

Walmart sells some produce by the piece but charges it by weight (sales unit ``EACH_WEIGHT``): the price a
result tile shows is an estimate, worded "each (est.)" next to it, and the product's own page states
``finalCostByWeight``. Release 1.3.0 read a ``WEIGHT`` sales unit and the ``finalCostByWeight`` code only; a
result tile carries that code for no item, so 31 products of the 1.3.0 main run were exported with an
estimated price as if it were fixed. Release 1.3.1 also reads the sales unit and the value-less
``SOLD_BY_WEIGHT`` price line and keeps Walmart's wording exactly as given with its path.

Release 1.3.1 excluded every weight-priced product as a relative price (``RELATIVE_PRICE``,
``records.exclude_relative_price_items`` true). The client's rule (shared requirements §5; the 2026-10-28
brief, section 4) excludes a product for approximate or equivalent estimated-weight wording only, never for
being sold by weight or for a "/lb" price per measure alone, and traces each exclusion to that wording.
Release 1.4.0 therefore excludes the product whose price is stated as an estimate ("each (est.)") as an
approximate weight, naming the wording, its path and the whole value, and keeps a product sold by weight
whose price carries no such wording (a sponsored tile; "$0.25 / 0.14lb"), flagged ``RELATIVE_PRICE`` and
``SOLD_BY_WEIGHT``. ``exclude_relative_price_items`` is false by default; true restores the 1.3.1 rule.

AUTHENTIC pages of the Azure run of 2026-10-26: the Apples and Fresh Vegetables result pages
(``listing_pages_20261026``) and the product page of item 12852163028 (``product_pages_20261026``)."""

from __future__ import annotations

import gzip
import re
from pathlib import Path
from typing import Any

import pytest

from walmart_headless.assembly.prices import PriceDisplayKind
from walmart_headless.assembly.private_label import PrivateLabelDetector
from walmart_headless.assembly.record_builder import (
    BuiltRecord,
    CategoryAssignment,
    StoreFields,
    build_product_record,
)
from walmart_headless.core.findings import RecordFlag
from walmart_headless.core.settings import RecordSettings, load_private_label, load_settings
from walmart_headless.sites.walmart import page_data as wpd
from walmart_headless.sites.walmart import records as wrec

CAPTURES = Path(__file__).resolve().parents[1] / "captures"
CONFIG = CAPTURES.parents[1] / "config"
DETECTOR = PrivateLabelDetector(load_private_label(CONFIG / "walmart_private_label_brands.yaml"))
STORE = StoreFields("60085", "Store", "Address", "")
APPLES = "listing_pages_20261026/apples_page1.html.gz"
VEGETABLES = "listing_pages_20261026/fresh_vegetables_page1.html.gz"
PEAR = "product_pages_20261026/each_estimated_12852163028.html.gz"
_STEP = re.compile(r"([^.\[\]]+)|\[(\d+)\]")

# The Apples page's tiles of products sold by the piece and charged by weight, in page order: (item,
# sponsored, Walmart's wording next to the price). A sponsored tile shows no wording; its sales unit and its
# price line still state how the product is charged.
EACH_WEIGHT = [
    ("43923746", True, ""),
    ("44390950", False, "each (est.)"),
    ("44390953", False, "each (est.)"),
    ("43923182", False, "each (est.)"),
    ("45912954", False, "each (est.)"),
    ("51259330", True, ""),
    ("51259197", False, "each (est.)"),
    ("883640849", False, "each (est.)"),
    ("44390980", False, "each (est.)"),
    ("51259330", False, "each (est.)"),
    ("43923746", False, "each (est.)"),
    ("349351812", False, "each (est.)"),
]


def page(name: str) -> dict[str, Any]:
    return wpd.next_data(gzip.decompress((CAPTURES / name).read_bytes()).decode("utf-8"))


def resolve(doc: Any, path: str) -> Any:
    """The value at a dotted JSON path with list indices (``a.b[0].c``)."""
    for key, index in _STEP.findall(path):
        doc = doc[int(index)] if index else doc[key]
    return doc


def build(item: wpd.WalmartItem, settings: RecordSettings) -> tuple[BuiltRecord, dict[str, Any]]:
    ev, _, log = wrec.evidence(
        item, fetch_id="f1", observed_at="2026-10-26T22:13:01Z", store_id="3891", modality="PICKUP",
        page_verified=True,
    )  # fmt: skip
    built = build_product_record(
        ev,
        store=STORE,
        category=CategoryAssignment("Fresh Produce", "Apples"),
        crawl_date="2026-10-26",
        settings=settings,
        detector=DETECTOR,
        configured_modality="PICKUP",
    )
    return built, log


def test_tiles_sold_by_the_piece_and_charged_by_weight_are_weight_priced() -> None:
    nd = page(APPLES)
    items = wpd.page_items(nd)
    assert [(i.item_id, i.sponsored, i.price_condition) for i in items if i.weight_priced] == EACH_WEIGHT
    assert len(items) - len(EACH_WEIGHT) == 27
    for i in items:
        tile = resolve(nd, i.path)
        # Release 1.3.0's signals are absent from every tile: no finalCostByWeight code is set.
        assert tile["priceInfo"].get("finalCostByWeight") is False
        if i.weight_priced:
            assert tile["salesUnitType"] == "EACH_WEIGHT"
            assert i.weight_priced_by == ("sales unit EACH_WEIGHT", "price line SOLD_BY_WEIGHT")
        else:
            assert tile["salesUnitType"] == "EACH" and i.weight_priced_by == () and i.price_condition == ""
        if i.price_condition:
            # Walmart's wording is kept exactly as given, with the path it was read from.
            assert i.price_condition_source is not None
            assert resolve(tile, i.price_condition_source.path) == i.price_condition


@pytest.mark.parametrize("exclude", [True, False])
def test_an_estimate_next_to_the_price_excludes_the_product_and_names_the_wording(exclude: bool) -> None:
    nd = page(APPLES)
    for item in wpd.page_items(nd):
        if not item.weight_priced:
            continue
        built, log = build(item, RecordSettings(exclude_relative_price_items=exclude))
        display, _ = wrec.price_display(item)
        assert display.kind in (PriceDisplayKind.RELATIVE, PriceDisplayKind.RELATIVE_SALE)
        assert {RecordFlag.RELATIVE_PRICE, RecordFlag.SOLD_BY_WEIGHT} <= set(built.flags)
        # Being sold by weight excludes a product only while relative prices are excluded (not the default).
        assert (RecordFlag.RELATIVE_PRICE in built.reasons) is exclude
        assert log["weight_priced"] == {"value": True, "by": list(item.weight_priced_by)}
        if item.price_condition:
            # "each (est.)": the price of one piece, whose weight is estimated. The whole product is excluded
            # as an approximate weight, traced to the wording, its path and the whole value.
            assert item.price_condition_source is not None
            path = f"{item.path}.{item.price_condition_source.path}"
            assert log["price_condition"] == {"text": "each (est.)", "path": path}
            assert RecordFlag.APPROX_WEIGHT in built.reasons
            assert built.provenance["_approx_weight"] == {
                "field": "price_display_condition",
                "path": path,
                "text": "est.",
                "value": "each (est.)",
                "weight_priced_by": "sales unit EACH_WEIGHT; price line SOLD_BY_WEIGHT",
            }
            assert resolve(nd, path) == "each (est.)"
            assert log["approx_weight"] == built.provenance["_approx_weight"]
        else:
            # A sponsored tile shows no wording next to its price: nothing on it qualifies.
            assert item.sponsored and log["price_condition"] is None
            assert RecordFlag.APPROX_WEIGHT not in built.reasons and wrec.approx_weight(item) is None
            assert "_approx_weight" not in built.provenance
            assert built.reasons == ((RecordFlag.RELATIVE_PRICE,) if exclude else ())


def test_a_product_sold_by_weight_without_estimate_wording_is_kept() -> None:
    """Fresh Jalapenos (44391018): sold by weight (sales unit WEIGHT, a SOLD_BY_WEIGHT price line), its price
    shown for a stated weight ("$0.25 / 0.14lb", was $0.27) with a "$1.76/lb" price per measure. No
    approximate or estimated wording: release 1.3.1 excluded it as a relative price; release 1.4.0 keeps it,
    with the weight its price is for, as displayed."""
    nd = page(VEGETABLES)
    [item] = [i for i in wpd.page_items(nd) if i.item_id == "44391018"]
    assert item.weight_priced_by == ("sales unit WEIGHT", "price line SOLD_BY_WEIGHT")
    assert (item.price_string, item.was_price_string, item.unit_price_string) == (
        "$0.25",
        "$0.27",
        "$1.76/lb",
    )
    assert item.price_condition == "/ 0.14lb" and item.price_condition_source is not None
    built, log = build(item, RecordSettings())
    assert built.reasons == () and built.status.value == "valid"
    assert {RecordFlag.RELATIVE_PRICE, RecordFlag.SOLD_BY_WEIGHT} <= set(built.flags)
    r = built.record
    assert (r["weight"], r["regular_price"], r["sale_price"], r["ppm"]) == (
        "0.14lb",
        "0.27",
        "0.25",
        "$1.76/lb",
    )
    weight = built.provenance["weight"]
    assert resolve(nd, weight["selector_or_path"]) == "/ 0.14lb"
    assert "the weight after the '/', kept as given" in weight["transform"]
    assert log["weight_source"] == "price_condition" and log["approx_weight"] is None
    # The 1.3.1 rule, still available as a setting, excludes it.
    excluded, _ = build(item, RecordSettings(exclude_relative_price_items=True))
    assert excluded.reasons == (RecordFlag.RELATIVE_PRICE,)


def test_the_vegetables_page_excludes_only_the_estimated_prices() -> None:
    weighed = [i for i in wpd.page_items(page(VEGETABLES)) if i.weight_priced]
    outcome = {i.item_id: (i.price_condition, build(i, RecordSettings())[0].reasons) for i in weighed}
    assert len(outcome) == 10
    assert {k: v for k, v in outcome.items() if v[0] != "each (est.)"} == {"44391018": ("/ 0.14lb", ())}
    assert all(v[1] == (RecordFlag.APPROX_WEIGHT,) for v in outcome.values() if v[0] == "each (est.)")


def test_the_default_settings_keep_products_sold_by_weight() -> None:
    assert RecordSettings().exclude_relative_price_items is False
    assert load_settings(CONFIG / "settings.yaml").records.exclude_relative_price_items is False


def test_fixed_price_products_of_the_same_page_are_unchanged() -> None:
    fixed = [i for i in wpd.page_items(page(APPLES)) if not i.weight_priced]
    for item in fixed:
        built, log = build(item, RecordSettings())
        assert RecordFlag.RELATIVE_PRICE not in built.flags and RecordFlag.SOLD_BY_WEIGHT not in built.flags
        assert log["weight_priced"] == {"value": False, "by": []} and log["price_condition"] is None
    bag = next(i for i in fixed if i.name == "Fresh Gala Apples, 3 lb Bag")
    assert build(bag, RecordSettings())[0].record["weight"] == "3 lb Bag"


def test_the_products_own_page_states_that_its_final_cost_depends_on_the_weight() -> None:
    nd = page(PEAR)
    pp = wpd.product_page(nd)
    assert pp is not None and pp.item is not None
    item = pp.item
    assert item.sales_unit == "EACH_WEIGHT"  # a product page states salesUnit, not salesUnitType
    assert item.weight_priced_by == ("sales unit EACH_WEIGHT", "priceDisplayCodes.finalCostByWeight")
    assert item.price_condition == "each (est.)" and item.price_condition_source is not None
    assert item.price_condition_source.path == "priceInfo.priceDisplayCodes.priceDisplayCondition"
    assert (item.price_string, item.was_price_string, item.unit_price_string) == (
        "$0.77",
        "$1.02",
        "$1.72/lb",
    )
    assert wrec.price_display(item)[0].kind is PriceDisplayKind.RELATIVE_SALE
    # Its specifications give an average weight. That is a catalogue attribute, which Walmart also gives
    # products sold at a fixed price and size ("Fresh Blackberries, 6 oz. Container": "6 oz"): it is not
    # read as the product's size wording.
    specs = {
        s["name"]: s["value"]
        for s in nd["props"]["pageProps"]["initialData"]["data"]["idml"]["specifications"]
    }
    assert specs["Average sold by weight"] == specs["Maximum sold by weight"] == "0.6 Pounds"
    # Excluded for the estimate stated next to its price (release 1.4.0; 1.3.1 excluded it as a relative
    # price), the wording traced to its path on the product page.
    built, _ = build(item, RecordSettings())
    assert built.reasons == (RecordFlag.APPROX_WEIGHT,)
    assert built.provenance["_approx_weight"] == {
        "field": "price_display_condition",
        "path": f"{item.path}.priceInfo.priceDisplayCodes.priceDisplayCondition",
        "text": "est.",
        "value": "each (est.)",
        "weight_priced_by": "sales unit EACH_WEIGHT; priceDisplayCodes.finalCostByWeight",
    }
