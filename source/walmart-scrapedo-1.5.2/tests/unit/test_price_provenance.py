"""The price fields' provenance names the path each value was actually read from and every change made to it
(release 1.3.1, defect D of the 2026-10-27 review: release 1.3.0 named ``priceInfo.currentPrice|linePrice``
and ``priceInfo.unitPrice`` while the listings' values came from ``priceInfo.priceDetails.priceLines``).

Every price path of every record built from the saved authentic listing pages is resolved in that page's
data and the stated changes are applied: the result must be the record's value."""

from __future__ import annotations

import gzip
import re
from pathlib import Path
from typing import Any

import pytest

from tests import synthetic_walmart as syn
from walmart_headless.assembly.private_label import PrivateLabelDetector
from walmart_headless.assembly.record_builder import (
    BuiltRecord,
    CategoryAssignment,
    FieldSource,
    StoreFields,
    build_product_record,
)
from walmart_headless.core.settings import RecordSettings, load_private_label
from walmart_headless.core.text import normalize_single_price
from walmart_headless.sites.walmart import page_data as wpd
from walmart_headless.sites.walmart import records as wrec

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT.parent / "config"
CAPTURES = [
    ("listing_pages_20261026/apples_page1.html.gz", "3891"),
    ("listing_pages_20261026/citrus_page1.html.gz", "3891"),
    ("w1_20261021/diapering_page1.html.gz", "5402"),
    ("w1_20261021/diapering_page2.html.gz", "5402"),
]
PRICE_FIELDS = ("regular_price", "sale_price", "ppm")
DETECTOR = PrivateLabelDetector(load_private_label(CONFIG / "walmart_private_label_brands.yaml"))
STORE = StoreFields("60639", "Store", "Address", "")
_STEP = re.compile(r"([^.\[\]]+)|\[(\d+)\]")


def page(name: str) -> dict[str, Any]:
    return wpd.next_data(gzip.decompress((ROOT / "captures" / name).read_bytes()).decode("utf-8"))


def resolve(doc: Any, path: str) -> Any:
    """The value at a dotted JSON path with list indices (``a.b[0].c``)."""
    for key, index in _STEP.findall(path):
        doc = doc[int(index)] if index else doc[key]
    return doc


def apply(value: str, transform: str) -> str:
    """The stated changes, applied to the value read."""
    if wpd.DOLLAR_PREFIXED in transform and re.fullmatch(r"\d+(?:\.\d{1,2})?", value):
        value = "$" + value
    if wrec.PRICE_READ in transform:
        value = normalize_single_price(value)
    return value


def build(item: wpd.WalmartItem, store: str) -> BuiltRecord:
    ev, _, _ = wrec.evidence(
        item, fetch_id="f1", observed_at="2026-10-26T22:13:01Z", store_id=store, modality="PICKUP",
        page_verified=True,
    )  # fmt: skip
    return build_product_record(
        ev,
        store=STORE,
        category=CategoryAssignment("Food", "Apples"),
        crawl_date="2026-10-26",
        settings=RecordSettings(),
        detector=DETECTOR,
        configured_modality="PICKUP",
    )


@pytest.mark.parametrize(("name", "store"), CAPTURES)
def test_each_price_path_resolves_in_the_page_to_the_records_value(name: str, store: str) -> None:
    nd = page(name)
    checked = 0
    for item in wpd.page_items(nd):
        built = build(item, store)
        for field in PRICE_FIELDS:
            value = built.record[field]
            prov = built.provenance.get(field)
            if not value:
                assert prov is None, f"{item.item_id} {field}: an empty field names a source"
                continue
            assert prov is not None, f"{item.item_id} {field}: no source for {value!r}"
            path = prov["selector_or_path"]
            assert "|" not in path and path.startswith(item.path + ".priceInfo.")
            assert apply(resolve(nd, path), prov["transform"]) == value, (item.item_id, field, path)
            checked += 1
    assert checked > 20


def test_a_listing_tile_in_the_price_lines_layout_names_its_lines() -> None:
    nd = page("listing_pages_20261026/apples_page1.html.gz")
    [item] = [x for x in wpd.page_items(nd) if x.item_id == "5315371756"]  # stored by run 01M5X364 (1.3.0)
    assert item.price_source == wpd.ValueSource(
        "priceInfo.priceDetails.priceLines[0].values[0].value",
        "lineType=CURRENT_PRICE, key=PRICE",
        wpd.DOLLAR_PREFIXED,
    )
    assert item.unit_price_source == wpd.ValueSource(
        "priceInfo.priceDetails.priceLines[1].values[0].value", "lineType=UNIT_PRICE, key=UNIT_PRICE"
    )
    assert item.was_price_source is None and item.price_range_source is None
    built = build(item, "3891")
    assert (built.record["regular_price"], built.record["sale_price"], built.record["ppm"]) == (
        "3.97",
        "",
        "33.1 ¢/ea",
    )
    regular = built.provenance["regular_price"]
    assert regular["selector_or_path"] == (
        "props.pageProps.initialData.searchResult.itemStacks[0].items[35]"
        ".priceInfo.priceDetails.priceLines[0].values[0].value"
    )
    assert regular["transform"] == (
        "value of the price line lineType=CURRENT_PRICE, key=PRICE; '$' prefixed to the line's bare amount; "
        "read as one two-decimal price (core.text.normalize_single_price)"
    )
    assert "sale_price" not in built.provenance  # no sale: the field is empty and names no source
    assert built.provenance["ppm"]["transform"] == (
        "value of the price line lineType=UNIT_PRICE, key=UNIT_PRICE, kept as given"
    )


def test_a_sale_in_the_price_lines_layout_reads_the_comparison_and_the_discounted_lines() -> None:
    nd = page("listing_pages_20261026/apples_page1.html.gz")
    sales = [x for x in wpd.page_items(nd) if x.was_price_source is not None]
    assert sales
    for item in sales:
        assert item.price_source is not None and item.was_price_source is not None
        assert item.price_source.selector == "lineType=DISCOUNTED_PRICE, key=PRICE"
        assert item.was_price_source.selector == "lineType=COMPARISON, key=WAS_PRICE"
        built = build(item, "3891")
        assert built.record["sale_price"] and built.record["regular_price"]
        assert built.provenance["regular_price"]["selector_or_path"].endswith(item.was_price_source.path)
        assert built.provenance["sale_price"]["selector_or_path"].endswith(item.price_source.path)
        assert "COMPARISON" in built.provenance["regular_price"]["transform"]
        assert "DISCOUNTED_PRICE" in built.provenance["sale_price"]["transform"]


def test_the_older_layouts_name_their_own_fields() -> None:
    nd = wpd.next_data(
        syn.listing_page(
            [
                syn.Item("1", "Nested Item, 12 oz", "$3.12", was="$3.50", unit="26.0 ¢/oz"),
                syn.Item("2", "Flat Item, 12 oz", "$1.98", was="$2.48", unit="16.5 ¢/oz", flat_price=True),
                syn.Item("3", "Options Item, 10 oz", "", price_range="$3.97 - $5.97", flat_price=True),
            ],
            store="5402",
        )
    )
    nested, flat, options = wpd.page_items(nd)
    assert nested.price_source == wpd.ValueSource("priceInfo.currentPrice.priceString")
    assert nested.was_price_source == wpd.ValueSource("priceInfo.wasPrice.priceString")
    assert nested.unit_price_source == wpd.ValueSource("priceInfo.unitPrice.priceString")
    assert flat.price_source == wpd.ValueSource("priceInfo.linePriceDisplay")
    assert flat.was_price_source == wpd.ValueSource("priceInfo.wasPrice")
    assert options.price_source is None
    assert options.price_range_source == wpd.ValueSource("priceInfo.priceRangeString")
    for item in (nested, flat):
        built = build(item, "5402")
        for field in PRICE_FIELDS:
            prov = built.provenance[field]
            assert apply(resolve(nd, prov["selector_or_path"]), prov["transform"]) == built.record[field]
        assert built.provenance["sale_price"]["transform"] == (
            "displayed text; read as one two-decimal price (core.text.normalize_single_price)"
        )
    built = build(options, "5402")
    assert not any(built.record[f] for f in ("regular_price", "sale_price"))
    assert not any(f in built.provenance for f in ("regular_price", "sale_price"))


def test_a_field_source_without_a_transform_keeps_its_earlier_shape() -> None:
    assert FieldSource("walmart_page_data", "x.name", "f1", None, "t").as_dict() == {
        "source": "walmart_page_data",
        "selector_or_path": "x.name",
        "fetch_id": "f1",
        "response_sha256": None,
        "observed_at": "t",
    }
