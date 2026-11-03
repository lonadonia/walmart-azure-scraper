"""Regressions of release 1.5.0: pack size against serving size, unit price and sibling variants. The page
shapes come from saved product pages of the 1.4.1 evidence (item numbers named where one is the real case)."""

from __future__ import annotations

from typing import Any

import pytest

from walmart_headless.sites.walmart import pack_size as wps
from walmart_headless.sites.walmart import records as wrec


def page(
    specs: dict[str, str] | None = None,
    variants: dict[str, list[tuple[str, bool]]] | None = None,
    unit_price: str = "",
    serving: Any = None,
) -> dict[str, Any]:
    product: dict[str, Any] = {
        "usItemId": "1",
        "variantCriteria": [
            {"id": cid, "variantList": [{"id": f"{cid}-{n}", "name": n, "selected": s} for n, s in options]}
            for cid, options in (variants or {}).items()
        ],
    }
    if unit_price:
        product["priceInfo"] = {"unitPrice": {"priceString": unit_price}}
    idml: dict[str, Any] = {"specifications": [{"name": k, "value": v} for k, v in (specs or {}).items()]}
    if serving is not None:
        idml["nutritionFacts"] = {"servingInfo": serving}
    return {"props": {"pageProps": {"initialData": {"data": {"product": product, "idml": idml}}}}}


def test_two_packages_of_a_set_are_both_kept_and_do_not_conflict_with_themselves() -> None:
    """1.5.1 limitation 4: a real title of 1.4.1's pages gave "12.5 oz", with the second package lost."""
    title = "Shampoo and Conditioner Dual Pack, 12.5 oz shampoo + 10.6 oz conditioner"
    assert wrec.title_size(title) == "12.5 oz shampoo + 10.6 oz conditioner"
    d = wps.pack_size(page({"Size": "12.5 oz"}), wrec.title_size(title))
    assert d.outcome == "title_kept"
    # A medicine's strengths are no packages, and neither is one size with a word after it.
    assert wrec.title_size("Pain Relief, 500 mg + 200 mg Tablets, 24 Count") == "24 Count"
    assert wrec.title_size("Great Value Salsa, 16 oz Jar") == "16 oz Jar"


def test_a_multipack_is_not_repeated_by_a_size_that_says_only_one() -> None:
    """1.5.1 limitation 5: a real S6 title gave "2 pack, 1 Pack", and 1.5.0 gave "1 Pack"."""
    title = "(2 pack) Ol' Roy Natural Large Beef Femur Dog Chew for Healthy Teeth, 1 Pack"
    assert wrec.title_size(title) == "2 pack"
    assert wrec.title_size("(2 pack) Pure Balance Salmon Dry Dog Food, 16 lbs") == "2 pack, 16 lbs"


def test_a_net_content_label_does_not_hide_the_statement_and_stays_in_the_value() -> None:
    assert wps.is_quantity("NET WT 7oz (198g)") and wps.is_quantity("NT WT 2.6 oz")
    assert not wps.is_quantity("65") and not wps.is_quantity("4.43 x 4.43 x 6.36 Inches")
    d = wps.pack_size(page({"Net content statement": "NET WT 7oz (198g)"}))
    assert (d.value, d.outcome) == ("NET WT 7oz (198g)", "single_statement")
    d = wps.pack_size(page({"Net content statement": "NT WT 3 oz", "Size": "5 oz"}))
    assert d.value == "" and d.outcome == "conflict"


def test_the_size_specification_fills_an_empty_size_as_written() -> None:
    d = wps.pack_size(page({"Size": "16 oz", "Net content statement": "16 oz"}))
    assert (d.value, d.outcome, d.rule) == ("16 oz", "agreed", "spec_size")
    assert d.path.endswith("specifications[0].value")


def test_serving_size_unit_price_and_sibling_variants_are_kept_but_never_used() -> None:
    d = wps.pack_size(
        page(
            {"Serving size": "1 mL"},
            variants={"size": [("4.8 oz", False), ("16 oz", False)]},
            unit_price="$0.16/oz",
            serving=[{"name": "Serving Size", "value": "2 tbsp (30 g)"}],
        )
    )
    assert d.value == "" and d.outcome == "none"
    kinds = {o.kind for o in d.observations}
    assert {"serving", "unit_price_denominator", "sibling_variant_size"} <= kinds
    assert all(o.measures == wps.NEVER for o in d.observations)


def test_the_selected_variant_is_the_pack_not_its_siblings() -> None:
    d = wps.pack_size(
        page({"Size": "10.7 oz"}, variants={"size": [("4.8 oz", False), ("10.7 oz", True), ("16 oz", False)]})
    )
    assert (d.value, d.rule) == ("10.7 oz", "selected_variant_size")


@pytest.mark.parametrize(
    ("item", "parent"),
    [("162577028", "4 Pound"), ("51259387", "7 Pound"), ("40347953", "8 Pound")],
)
def test_real_cases_a_parent_net_content_against_its_own_declared_unit_is_a_conflict(
    item: str, parent: str
) -> None:
    """Found reprocessing Oxylabs B3 (2026-10-31): the saved pages of "Fresh Navel Orange, Each" (162577028),
    "Fresh Grapefruit, Each" (51259387) and "Fresh Kale Greens, Bunch" (40347953) state "Product net content
    parent" in pounds while their own "Product net content uom" and "Sales unit" are "Each". Release 1.5.0 as
    first committed filled the empty size with the pounds (a bag's weight for one orange). The page
    contradicts itself, so nothing is chosen: the size stays empty, flagged, with both statements kept."""
    d = wps.pack_size(
        page({"Product net content parent": parent, "Product net content uom": "Each", "Sales unit": "Each"})
    )
    assert (d.value, d.outcome) == ("", "conflict"), item
    assert parent in d.conflicts[0] and "Each" in d.conflicts[0]
    assert {o.kind for o in d.observations} >= {"spec_net_content_parent", "spec_net_content_uom"}


def test_a_parent_net_content_that_agrees_with_its_declared_unit_still_fills_the_size() -> None:
    # Fresh Plantain, Each (34143814): "1" with "Each"; Fresh Bosc Pears, 3 lb Bag (157184028) states its
    # size in the title, which is kept whatever the page says.
    d = wps.pack_size(page({"Product net content parent": "16", "Product net content uom": "Ounce"}))
    assert (d.value, d.outcome) == ("16 Ounce", "single_statement")
    d = wps.pack_size(page({"Product net content parent": "11 Ounces", "Product net content uom": "Ounce"}))
    assert (d.value, d.outcome) == ("11 Ounces", "single_statement")
    d = wps.pack_size(
        page({"Product net content parent": "3 Pound", "Product net content uom": "Each"}), "3 lb Bag"
    )
    assert d.outcome == "title_kept"
    # Dove deodorant 19963859025: the declared unit "Count" is wrong, but "Size" states the same 2.6 oz.
    d = wps.pack_size(
        page(
            {"Size": "2.6 oz", "Product net content parent": "2.6 Ounces", "Product net content uom": "Count"}
        )
    )
    assert (d.value, d.outcome) == ("2.6 oz", "agreed")


def test_a_conflict_is_kept_and_no_value_is_chosen() -> None:
    d = wps.pack_size(page({"Size": "16 oz", "Net content statement": "24 oz"}))
    assert d.value == "" and d.outcome == "conflict" and d.conflict
    assert "16 oz" in d.conflicts[0] and "24 oz" in d.conflicts[0]
    assert len(d.observations) == 2


def test_real_case_item_49986668_title_and_page_disagree_on_loads() -> None:
    nd = page({"Size": "141 oz", "Number of loads": "88", "Count per pack": "88"})
    d = wps.pack_size(nd, "141 oz, 66 Loads")
    assert d.outcome == "title_conflict" and d.value == ""
    assert any("66 Loads" in n and "88 Loads" in n for n in d.conflicts)


def test_a_pack_the_title_states_explains_a_larger_size_on_the_page_and_nothing_else() -> None:
    """Release 1.5.1: the title's size keeps its multipack ("2 pack, 16 lbs"). A page's "32 lb" differs from
    it by that pack; checked only, nothing is computed. SYNTHETIC page shape."""
    d = wps.pack_size(page({"Size": "32 lb"}), "2 pack, 16 lbs")
    assert (d.value, d.outcome, d.conflicts) == ("", "title_kept", ())
    d = wps.pack_size(page({"Size": "16 lb"}), "2 pack, 16 lbs")
    assert (d.value, d.outcome, d.conflicts) == ("", "title_kept", ())
    # A difference the pack does not explain stays a conflict, and so does the same size without a pack.
    d = wps.pack_size(page({"Size": "40 lb"}), "2 pack, 16 lbs")
    assert d.outcome == "title_conflict" and "40 lb" in d.conflicts[0]
    d = wps.pack_size(page({"Size": "32 lb"}), "16 lbs")
    assert d.outcome == "title_conflict"
    # A pack quantity on the page that contradicts the title's is still a conflict.
    d = wps.pack_size(page({"Multipack quantity": "3"}), "2 pack, 16 lbs")
    assert d.outcome == "title_conflict" and "pack" in d.conflicts[0]


def test_units_are_converted_only_to_compare() -> None:
    d = wps.pack_size(page({"Size": "16 oz", "Net content statement": "1 Pound"}))
    assert (d.value, d.outcome) == ("16 oz", "agreed")
    d = wps.pack_size(page({"Net content statement": "26.46 oz (750 g)", "Size": "750 g"}))
    assert d.outcome == "agreed" and d.value == "26.46 oz (750 g)"


def test_a_multipack_stays_beside_the_size_and_is_never_multiplied() -> None:
    d = wps.pack_size(page({"Size": "4.5 fl oz", "Multipack quantity": "6"}))
    assert d.value == "4.5 fl oz, 6 Pack"
    d = wps.pack_size(
        page({"Size": "4.5 fl oz", "Net content statement": "27 fl oz", "Multipack quantity": "6"})
    )
    assert d.outcome == "agreed" and "27" not in d.value


def test_a_count_takes_its_unit_from_its_own_label() -> None:
    assert wps.pack_size(page({"Count per pack": "76"})).value == "76 Count"
    assert wps.pack_size(page({"Number of loads": "45"})).value == "45 Loads"
    d = wps.pack_size(page({"Count per pack": "5", "Total count": "25"}))
    assert d.value == "" and d.outcome == "conflict"


def test_words_that_are_no_quantity_are_never_a_size() -> None:
    d = wps.pack_size(page({"Size": "Medium Apples", "Net content statement": "Blueberries"}))
    assert d.value == "" and d.outcome == "none"


def test_one_each_is_only_used_when_nothing_else_is_stated_and_never_conflicts() -> None:
    assert wps.pack_size(page({"Net content statement": "1 Each"})).outcome == "default_only"
    d = wps.pack_size(page({"Net content statement": "1 Count", "Size": "32 oz"}))
    assert (d.value, d.outcome) == ("32 oz", "single_statement")
    d = wps.pack_size(page({"Product net content parent": "1", "Product net content uom": "Each"}))
    assert d.value == "1 Each"


def test_a_shipping_or_assembled_weight_is_not_a_pack() -> None:
    d = wps.pack_size(page({"Weight": "2.9237 POUNDS", "Assembled product weight": "6.15 lb"}))
    assert d.value == "" and d.outcome == "none"
    assert {o.kind for o in d.observations} == {"spec_weight", "spec_assembled_weight"}


def test_a_page_without_page_data_states_nothing() -> None:
    assert wps.pack_size({}).outcome == "none"


@pytest.mark.parametrize(
    ("title", "page_size"),
    [("16.9 fl oz, 24 Pack Bottles", "16.9 fl oz"), ("12 oz Bag", "12 oz"), ("Pack of 4", "")],
)
def test_a_title_that_agrees_keeps_its_own_text(title: str, page_size: str) -> None:
    d = wps.pack_size(page({"Size": page_size} if page_size else {}), title)
    assert d.outcome == "title_kept" and d.value == ""
