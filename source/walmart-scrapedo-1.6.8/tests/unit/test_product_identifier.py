"""UPC/GTIN from a product page (SYNTHETIC pages shaped like walmart.com's): only what the page states for
the item, as written, never the item id."""

from __future__ import annotations

import json

from tests import synthetic_walmart as syn
from walmart_headless.sites.walmart import page_data as wpd


def _page(product: dict[str, object], ld: dict[str, object] | None = None) -> str:
    data = {"props": {"pageProps": {"initialData": {"data": {"product": product}}}}}
    ld_html = f'<script type="application/ld+json">{json.dumps(ld)}</script>' if ld else ""
    return f"<!doctype html><html><head>{ld_html}</head><body>{syn.next_data_script(data)}</body></html>"


def test_the_upc_in_the_items_page_data_is_taken_as_written() -> None:
    ident = wpd.product_identifier(_page({"usItemId": "7101", "upc": "007874201234"}), "7101")
    assert (ident.value, ident.source) == ("007874201234", "page_data")  # leading zeros kept
    assert ident.path.endswith(".upc")


def test_a_gtin_of_the_json_ld_product_is_used_when_the_page_data_has_none() -> None:
    page = _page(
        {"usItemId": "7101", "name": "Milk"}, {"@type": "Product", "sku": "7101", "gtin13": "0078742012345"}
    )
    ident = wpd.product_identifier(page, "7101")
    assert (ident.value, ident.source) == ("0078742012345", "json_ld")


def test_another_items_identifier_the_item_id_and_short_codes_are_never_taken() -> None:
    other = _page({"usItemId": "9999", "upc": "012345678905"})
    assert wpd.product_identifier(other, "7101").value == ""
    item_id_only = _page({"usItemId": "123456789012", "upc": "123456789012"})
    assert wpd.product_identifier(item_id_only, "123456789012").value == ""
    short = _page({"usItemId": "7101", "upc": "12345"})
    ident = wpd.product_identifier(short, "7101")
    assert ident.value == "" and ident.candidates  # what was seen stays visible for the supporting log


def test_a_page_without_page_data_gives_nothing() -> None:
    assert wpd.product_identifier("<html><body>Robot or human?</body></html>", "7101").value == ""
