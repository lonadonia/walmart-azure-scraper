from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from walmart_headless.core.schema import (
    DEAL_FIELDS,
    OUTPUT_FIELDS,
    RecordShapeError,
    apply_output_policy,
    build_record,
    format_violations,
    shape_violations,
)


def test_output_fields_exact_order() -> None:
    assert OUTPUT_FIELDS == (
        "zipcode",
        "store_name",
        "store_location",
        "store_logo",
        "store_brand",
        "category",
        "sub_category",
        "product_title",
        "weight",
        "regular_price",
        "sale_price",
        "volume_deals_description",
        "volume_deals_price",
        "digital_deals_description",
        "digital_deals_price",
        "image_url",
        "url",
        "upc",
        "gupc",
        "ppm",
        "unit_price",
        "crawl_date",
    )
    assert len(OUTPUT_FIELDS) == 22
    assert OUTPUT_FIELDS[-1] == "crawl_date"
    assert OUTPUT_FIELDS.index("gupc") == OUTPUT_FIELDS.index("upc") + 1


def test_build_record_fills_empty_strings_in_order() -> None:
    rec = build_record({"upc": "0004900006722", "product_title": "Diet Coke® Soda Mini Cans"})
    assert list(rec) == list(OUTPUT_FIELDS)
    assert all(isinstance(v, str) for v in rec.values())
    assert rec["gupc"] == "" and rec["unit_price"] == ""
    assert rec["zipcode"] == ""
    assert shape_violations(rec) == []


def test_build_record_rejects_unknown_and_forbidden_keys() -> None:
    with pytest.raises(RecordShapeError):
        build_record({"remarks": "x"})
    with pytest.raises(RecordShapeError):
        build_record({"gupc14": "x"})


@pytest.mark.parametrize("key", ["gupc", "unit_price"])
def test_always_empty_fields_cannot_be_set(key: str) -> None:
    with pytest.raises(RecordShapeError):
        build_record({key: "123"})


def test_none_is_not_a_valid_value() -> None:
    with pytest.raises(RecordShapeError):
        build_record({"ppm": None})  # type: ignore[dict-item]


def test_shape_violations_detects_order_types_and_extras() -> None:
    rec = build_record({})
    reordered = dict(reversed(list(rec.items())))
    assert shape_violations(reordered)
    bad_type = {**rec, "regular_price": 1.5}
    assert any("not str" in p for p in shape_violations(bad_type))
    extra = {**rec, "remarks": ""}
    assert any("forbidden" in p for p in shape_violations(extra))


@pytest.mark.parametrize(
    ("field", "value", "ok"),
    [
        ("regular_price", "34.99", True),
        ("regular_price", "5.00", True),
        ("regular_price", "$5.00", False),
        ("regular_price", "5", False),
        ("regular_price", "1,234.00", False),
        ("ppm", "$0.25/oz", True),
        ("ppm", "$0.18/fl oz", True),
        ("ppm", "$3.99/lb", True),
        ("ppm", "0.25/oz", False),
        ("upc", "0004900006722", True),
        ("upc", "4900006722", False),
        ("crawl_date", "2026-10-17", True),
        ("crawl_date", "10/17/2026", False),
    ],
)
def test_format_violations(field: str, value: str, ok: bool) -> None:
    rec = build_record({field: value})
    assert (format_violations(rec) == []) is ok


@given(
    st.dictionaries(
        st.sampled_from([f for f in OUTPUT_FIELDS if f not in ("gupc", "unit_price", *DEAL_FIELDS)]),
        st.text(max_size=20),
    )
)
def test_build_record_property_all_strings_in_order(values: dict[str, str]) -> None:
    rec = build_record(values)
    assert list(rec) == list(OUTPUT_FIELDS)
    assert all(isinstance(v, str) for v in rec.values())
    assert all(rec[f] == "" for f in DEAL_FIELDS)


@given(st.sampled_from(DEAL_FIELDS), st.text(min_size=1, max_size=20))
def test_build_record_refuses_any_walmart_deal_value(field: str, value: str) -> None:
    """Release 1.6.0, the client's clarification: the four deal fields are always "" for Walmart."""
    with pytest.raises(RecordShapeError, match="client rule for Walmart's deal fields"):
        build_record({field: value})
    full = {**build_record({}), field: value}
    assert f"{field} must be empty (client rule for Walmart's deal fields)" in shape_violations(full)


def test_apply_output_policy_blanks_the_deal_fields_and_returns_what_it_held() -> None:
    legacy = {k: "" for k in reversed(OUTPUT_FIELDS)}  # stored order, as JSONB returns it
    legacy.update(volume_deals_description="2 for $5.00", volume_deals_price="5.00", regular_price="2.50")
    kept, withheld = apply_output_policy(legacy)
    assert list(kept) == list(OUTPUT_FIELDS)
    assert [kept[f] for f in DEAL_FIELDS] == ["", "", "", ""]
    assert kept["regular_price"] == "2.50"  # the other fields keep their own rules
    assert withheld == {"volume_deals_description": "2 for $5.00", "volume_deals_price": "5.00"}
    assert shape_violations(kept) == []
