"""The record checks a carried record passes again (collection/retention.record_problems): records come
back from PostgreSQL's JSONB without their key order, so the order is restored before the checks, and a
missing or unknown key is a problem, never filled in or dropped."""

from __future__ import annotations

from collections.abc import Mapping

from walmart_headless.collection.retention import record_problems
from walmart_headless.core.schema import OUTPUT_FIELDS, build_record


def stored(record: Mapping[str, object]) -> dict[str, object]:
    """As JSONB returns it: keys sorted by length, then bytewise (not the output order)."""
    return {k: record[k] for k in sorted(record, key=lambda k: (len(k), k))}


def good() -> dict[str, str]:
    return build_record(
        {
            "upc": "078742000000",
            "product_title": "Synthetic Product, 12 oz",
            "category": "Food",
            "url": "https://www.walmart.com/ip/x/9001",
            "regular_price": "1.99",
            "crawl_date": "2026-10-26",
        }
    )


def test_a_valid_record_read_back_from_jsonb_has_no_problem() -> None:
    rec = stored(good())
    assert list(rec) != list(OUTPUT_FIELDS)  # the order JSONB gives back
    assert record_problems(rec) == []


def test_formats_types_and_deal_prices_are_checked() -> None:
    assert record_problems(stored({**good(), "regular_price": "1.9"})) == [
        "regular_price='1.9' is not a two-decimal price"
    ]
    assert "upc is int, not str" in record_problems(stored({**good(), "upc": 78742000000}))
    bad_deal = {**good(), "volume_deals_description": "Buy 1, Get 1 Free", "volume_deals_price": "2.50"}
    assert record_problems(bad_deal) == ["volume_deals_price not in volume_deals_description"]
    assert record_problems({**good(), "gupc": "078742000000"}) == ["gupc must be empty"]


def test_missing_or_unknown_keys_are_problems_never_repaired() -> None:
    rec = good()
    del rec["ppm"]
    assert record_problems(rec) == ["its keys are not the output fields (missing ['ppm'], unknown [])"]
    assert record_problems({**good(), "item_id": "9001"}) == [
        "its keys are not the output fields (missing [], unknown ['item_id'])"
    ]
