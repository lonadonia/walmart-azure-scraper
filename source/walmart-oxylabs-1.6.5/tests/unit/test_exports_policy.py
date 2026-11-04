"""Release 1.6.0: the final output boundary. Both products writers (JSON and CSV, used for products.* and
products_fresh.* of every run, replay and edition) refuse a row holding a Walmart deal value, a 23rd field,
a wrong order or a non-string, so no branch can reintroduce one into a file."""

from __future__ import annotations

import pytest

from walmart_headless.core.schema import DEAL_FIELDS, OUTPUT_FIELDS, build_record
from walmart_headless.publishing.exports import canonical_products_bytes, products_csv_bytes


def row() -> dict[str, str]:
    return build_record(
        {
            "product_title": "Synthetic, 12 oz",
            "url": "https://www.walmart.com/ip/x/9001",
            "category": "Food",
            "regular_price": "1.99",
            "crawl_date": "2026-11-03",
        }
    )


@pytest.mark.parametrize("writer", [canonical_products_bytes, products_csv_bytes])
@pytest.mark.parametrize("field", DEAL_FIELDS)
def test_a_deal_value_is_refused_by_both_writers(writer: object, field: str) -> None:
    bad = {**row(), field: "2 for $5.00" if field.endswith("description") else "5.00"}
    with pytest.raises(ValueError, match="client rule for Walmart's deal fields"):
        writer([row(), bad])  # type: ignore[operator]


@pytest.mark.parametrize("writer", [canonical_products_bytes, products_csv_bytes])
def test_order_extra_fields_and_types_are_refused(writer: object) -> None:
    good = row()
    with pytest.raises(ValueError):
        writer([{**good, "points": ""}])  # type: ignore[operator]
    with pytest.raises(ValueError):
        writer([dict(reversed(list(good.items())))])  # type: ignore[operator]
    with pytest.raises(ValueError):
        writer([{**good, "upc": 12345}])  # type: ignore[operator, dict-item]


def test_conforming_rows_are_written_in_the_22_field_order() -> None:
    body = products_csv_bytes([row()]).decode("utf-8-sig").splitlines()
    assert body[0].split(",") == list(OUTPUT_FIELDS)
    assert b'"volume_deals_description": ""' in canonical_products_bytes(
        [row()]
    ) or b'"volume_deals_description":""' in canonical_products_bytes([row()])
