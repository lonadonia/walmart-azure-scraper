"""Walmart parsing, local-offer rules, deals, sizes and records, offline on SYNTHETIC pages
(``tests/synthetic_walmart.py``): nothing here is live data."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests import synthetic_walmart as syn
from walmart_headless.acquisition.challenge import (
    WALMART_STATE_MARKER,
    blocked_response,
    detect_document_challenge,
)
from walmart_headless.assembly.private_label import PrivateLabelDetector
from walmart_headless.assembly.record_builder import (
    CategoryAssignment,
    RecordStatus,
    StoreFields,
    build_product_record,
)
from walmart_headless.core.findings import RecordFlag
from walmart_headless.core.schema import OUTPUT_FIELDS, format_violations
from walmart_headless.core.settings import RecordSettings, load_private_label
from walmart_headless.sites.walmart import page_data as wpd
from walmart_headless.sites.walmart import records as wrec
from walmart_headless.sites.walmart.sanitize import REDACTED, sanitize_html

CONFIG = Path(__file__).resolve().parents[2] / "config"
STORE = "5402"
STORE_FIELDS = StoreFields("60639", "Chicago Supercenter", "4650 W North Ave, Chicago, IL 60639", "")
DETECTOR = PrivateLabelDetector(load_private_label(CONFIG / "walmart_private_label_brands.yaml"))


def _items(*items: syn.Item, store: str = STORE) -> list[wpd.WalmartItem]:
    return wpd.page_items(wpd.next_data(syn.listing_page(list(items), store=store)))


def _record(item: wpd.WalmartItem, *, verified: bool = True) -> tuple[object, wrec.LocalOffer]:
    ev, offer, _ = wrec.evidence(
        item, fetch_id="f1", observed_at="2026-10-20T21:00:00Z", store_id=STORE, modality="PICKUP",
        page_verified=verified,
    )  # fmt: skip
    built = build_product_record(
        ev,
        store=STORE_FIELDS,
        category=CategoryAssignment("Diapering", ""),
        crawl_date="2026-10-20",
        settings=RecordSettings(),
        detector=DETECTOR,
        configured_modality="PICKUP",
    )
    return built, offer


CHICAGO = {"city": "Chicago", "state": "IL", "postal": "60639"}
MARKET = syn.Item(
    "32", "Marketplace Item, 1 ct", "$9.99", seller="Some Marketplace Seller", lines=(("SHIPPING", "0"),)
)
MILK = syn.Item(
    "10450114", "Great Value Whole Vitamin D Milk, Gallon, 128 fl oz", "$3.12", unit="2.4 ¢/fl oz",
    brand="Great Value",
)  # fmt: skip


def test_both_price_layouts_are_read_as_displayed() -> None:
    nested, flat = _items(
        MILK, syn.Item("2", "Flat Item, 12 oz", "$1.98", was="$2.48", unit="16.5 ¢/oz", flat_price=True)
    )
    assert (nested.price_string, nested.unit_price_string, nested.was_price_string) == (
        "$3.12",
        "2.4 ¢/fl oz",
        "",
    )
    assert (flat.price_string, flat.was_price_string, flat.unit_price_string) == (
        "$1.98",
        "$2.48",
        "16.5 ¢/oz",
    )
    assert nested.url == "https://www.walmart.com/ip/Great-Value-Whole-Vitamin-D-Milk/10450114"
    assert nested.image_url.startswith(
        "https://i5.walmartimages.com/seo/synthetic_10450114.jpeg?odnHeight=180"
    )
    assert nested.fulfillment[0] == wpd.Fulfillment("PICKUP", STORE)


def test_a_upc_is_kept_only_when_the_page_states_one_and_never_made_from_the_item_id() -> None:
    with_upc, without, odd = _items(
        syn.Item("11", "A, 10 oz", "$1.00", upc="078742370798"),
        syn.Item("12", "B, 10 oz", "$1.00"),
        syn.Item("13", "C, 10 oz", "$1.00", upc="12345"),
    )
    assert with_upc.upc == "078742370798" and wrec.product_key(with_upc) == "078742370798"
    assert without.upc == "" and wrec.product_key(without) == "wm:12"
    assert odd.upc == "" and wrec.product_key(odd) == "wm:13"  # not a UPC: never exported as one


@pytest.mark.parametrize(
    ("title", "size"),
    [
        ("Great Value Whole Vitamin D Milk, Gallon, 128 fl oz", "128 fl oz"),
        ("Coca-Cola Soda Pop, 16.9 fl oz, 24 Pack Bottles", "16.9 fl oz, 24 Pack Bottles"),
        ("Pampers Swaddlers Diapers, Size 1, 84 Count", "84 Count"),
        ("Bananas, approx 1.5 lb", "approx 1.5 lb"),
        ("LEGO Creator Set, 3 in 1", ""),
        # A quantity written inside the title (release 1.2.0; earlier only trailing segments were read).
        ("Gain Flings! 76 Ct Laundry Detergent Pacs, Original Scent", "76 Ct"),
        ("Party Balloons, Pack of 15", "Pack of 15"),
        ("No size here", ""),
        # Live titles of 2026-10-21: a bracketed note without a number is not part of the size.
        ("Pampers Diapers, Size 5, 66 Count (Select for More Options)", "66 Count"),
        ("Pampers Wipes, 9 Pack, 648 Wipes (Select for More Options)", "9 Pack, 648 Wipes"),
        ("Fairlife Chocolate Milk, 32 fl oz (Shelf-Stable)", "32 fl oz"),
        ("Nabisco Snacks, 12.2 oz (6 Multi Snack Packs)", "12.2 oz (6 Multi Snack Packs)"),
        ("20 Mule Team Borax Booster, 65 Ounce", "65 Ounce"),
        ("Johnson's Baby Gift Set, 3 Items", "3 Items"),
        ("Bounty Paper Towels, 24-Pack", "24-Pack"),
        ("Head & Shoulders, 2-in-1 Shampoo", ""),
        ("Great Value Coconut Milk, 13.5 fl oz, Can", "13.5 fl oz"),
    ],
)
def test_the_size_is_the_titles_trailing_size_segments(title: str, size: str) -> None:
    assert wrec.title_size(title) == size


# AUTHENTIC titles of products the 2026-10-23 live runs observed at store #3891 (their stored pages are in
# the campaign evidence): the size each title writes and the rule that reads it, kept exactly as written.
@pytest.mark.parametrize(
    ("title", "size", "outcome"),
    [
        (
            "Fresh Cranberries, 12 oz Bag, Whole Fruit, Perfect for Cooking and Baking",
            "12 oz Bag",
            "title_segments",
        ),
        ("Marketside Cantaloupe Chunks, 10 oz, Pre-Cut (Fresh)", "10 oz", "title_segments"),
        ("Fresh SunGold Kiwi, 1lb, Package", "1lb", "title_segments"),
        ("Taylor Farms Protein Plus Mini Meal Snack Tray with Fresh Fruit 7.5 oz", "7.5 oz", "in_title"),
        ("Natural Delights Pitted Medjool Dates 8oz Pouch", "8oz", "in_title"),
        ("Crunch Pak Family Sized 24oz Bag of Peeled Sweet Sliced Apples", "24oz", "in_title"),
        ("Red Delicious Apples 5 Lb Bag", "5 Lb", "in_title"),
        ("Rambutan Bag 12oz", "12oz", "in_title"),
        ("Similac NeoSure Premature Post-Discharge Baby Formula Powder, 13.1-oz Can", "13.1-oz", "in_title"),
        ("Pampers Swaddlers Newborn Diapers Size N 32 count", "32 count", "in_title"),
        ("Desitin Maximum Strength Diaper Rash Paste 4 oz (Pack of 4)", "4 oz (Pack of 4)", "in_title"),
        (
            "Sun Date Premium Organic California Medjool Dates 2 lbs. (Pack of 2)",
            "2 lbs. (Pack of 2)",
            "in_title",
        ),
        (
            "Freshness Guaranteed Ready-to-Serve Garden Pasta Salad (14 Ounce, 1 Count), Fresh",
            "14 Ounce, 1 Count",
            "in_title",
        ),
        (
            "Huggies Wipes with Aloe & Vitamin E, Unscented, 1 Flip-Top Pack, (56 Wipes)",
            "56 Wipes",
            "in_title",
        ),
        ("Fresh Organic Limes, 1 lb Bag", "1 lb Bag", "trailing_segments"),
        # A bracketed multipack beside one size: both kept, never multiplied (until release 1.4.1 this title
        # gave no size although it states one, while the same words after a comma did).
        (
            "(6 pack) Enfamil Infant Powder Baby Formula with Iron 12.5 oz Can",
            "6 pack, 12.5 oz",
            "multipack_in_title",
        ),
        # Several separate expressions: none is chosen (a protein weight and a bag).
        (
            "Blue Buffalo Wilderness Lamb Chicken-Free Formula 38 g Protein Meat Rich Natural Adult Dry Dog "
            "Food 24 lbs.",
            "",
            "ambiguous",
        ),
        (
            "10 Pack Large Balloon Arch Clips 3.5 Inch Heavy Duty Clip and 100 Pcs Clear 260 Long Balloons",
            "",
            "ambiguous",
        ),
        # Dimensions describe the product, not its package.
        (
            "Gender Reveal Confetti Balloon 36 Inch Big Black Balloons with Pink and Blue Confetti",
            "",
            "dimension_only",
        ),
        ("Fresh Butternut Squash, Each", "", "none"),
    ],
)  # fmt: skip
def test_sizes_written_inside_authentic_titles_are_read_as_written(
    title: str, size: str, outcome: str
) -> None:
    ev = wrec.size_from_title(title)
    assert (ev.value, ev.outcome) == (size, outcome)


# AUTHENTIC titles (release 1.3.1). The first seven are products the release 1.3.0 Azure run of 2026-10-26
# (01M5X364ZR83MZ9M60QGPFR7TX) exported with the product's description in their weight; the others keep
# their package in the size: Gravy Train and the raspberries are products of that run (exported unchanged),
# the lettuce and the wipes are titles of the release 1.2.x runs' stored pages (the 1.2.1 delivery).
@pytest.mark.parametrize(
    ("title", "exported_1_3_0", "size"),
    [
        (
            "Fresh Mandarin Oranges, 3 lb Bag - Naturally Ripened Citrus Fruit",
            "3 lb Bag - Naturally Ripened Citrus Fruit",
            "3 lb Bag",
        ),
        ("Fresh Organic Lemons, 2 lb - Juicy, Non-GMO, Ready-to-Use Citrus Fruits", "2 lb - Juicy", "2 lb"),
        ("Fresh Whole Celery, 1ea Premium Quality, Rich in antioxidants", "1ea Premium Quality", "1ea"),
        (
            "Mainstays Lint Roller, 60 Sheets Easy Tear, Ergonomic Handle, Removes Lint and Pet Hair from "
            "Clothing, Furniture, Crafts, Travel",
            "60 Sheets Easy Tear",
            "60 Sheets",
        ),
        (
            "Xtra Tropical Passion, 84 Loads Liquid Laundry Detergent, 100.8 fl oz",
            "84 Loads Liquid Laundry Detergent, 100.8 fl oz",
            "84 Loads, 100.8 fl oz",
        ),
        # A quantity followed by a nutrient is a nutrition claim, not the package's size.
        # (Release 1.5.1: the title's multipack stays beside the size; until 1.5.0 this gave "2.6 oz Pouch".)
        (
            "(6 pack) StarKist Chicken Creations, Chicken Salad, Gluten Free, 10g Protein, 2.6 oz Pouch",
            "10g Protein, 2.6 oz Pouch",
            "6 pack, 2.6 oz Pouch",
        ),
        (
            "Old Spice Holiday Gift Pack for Men, Fiji, Body Wash, Deodorant, Antiperspirant & Deodorant, "
            "2-in-1 Shampoo + Conditioner, Palm Tree + Coconut Scent, 4 Pack Gift Box for Him",
            "4 Pack Gift Box for Him",
            "4 Pack Gift Box",
        ),
        # Unchanged: the package, its period and its count belong to the size.
        ("Gravy Train Beefy Classic Dry Dog Food, 13 lb. Bag", "13 lb. Bag", "13 lb. Bag"),
        ("Fresh Raspberries, 12 oz. Container", "12 oz. Container", "12 oz. Container"),
        (
            "Little Leaf Farms Baby Crispy Green Leaf Lettuce Salad, 8 oz Clam Shell, Fresh",
            "8 oz Clam Shell",
            "8 oz Clam Shell",
        ),
        (
            "Pampers Wipes, Clean & Calm, Cotton Blossom Scent, 168 Wipes Total (3X Pop-Top Packs)",
            "168 Wipes Total (3X Pop-Top Packs)",
            "168 Wipes Total (3X Pop-Top Packs)",
        ),
    ],
)  # fmt: skip
def test_a_size_segment_ends_where_the_products_description_begins(
    title: str, exported_1_3_0: str, size: str
) -> None:
    assert wrec.title_size(title) == size
    # Still the title's own text, never rewritten: each part of the size begins a segment of the title, and
    # of the value release 1.3.0 read from it. A multipack outside the segments (release 1.5.1) is the title's
    # own bracket, which 1.3.0 did not read.
    for part in size.split(", "):
        if f"({part})" in title:
            continue
        assert any(s.startswith(part) for s in title.split(", "))
        assert any(r.startswith(part) for r in exported_1_3_0.split(", "))


@pytest.mark.parametrize(
    ("title", "wording"),
    [
        # AUTHENTIC: the five products of the 2026-10-23 export whose weight field was empty.
        ("Fresh Black Seedless Grapes, From California, Bag (2.25 lbs/Bag Est.)", "2.25 lbs/Bag Est."),
        ("Fresh Red Globe Seeded Grapes, Bag (2.25 lbs/Bag Est.)", "2.25 lbs/Bag Est."),
        ("Green Seedless Grapes From California, Bag (2.25 lbs/Bag Est.)", "2.25 lbs/Bag Est."),
        ("Red Seedless Grapes, From California, Bag (2.25 lbs/Bag Est.)", "2.25 lbs/Bag Est."),
        ("Fresh Tomato on the Vine, Bag (1.9 lbs/Bag Est.)", "1.9 lbs/Bag Est."),
        # SYNTHETIC wording around a weight.
        ("Bananas, approx 1.5 lb", "approx 1.5 lb"),
        ("Ground Beef, about 2 lb Package", "about 2 lb"),
        ("Fresh Avocado, Each (est. 0.4 lb)", "est. 0.4 lb"),
        ("Pork Shoulder, ~3 lb", "~3 lb"),
        ("Salmon Fillet, 1.25 lb avg.", "1.25 lb avg."),
        # Not approximate weights: a brand, "Best", "Estée", a name, servings that are not a weight.
        ("About Time Protein Bar, 12 ct", ""),
        ("Best Choice Peanut Butter, 16 oz", ""),
        ("Estée Lauder Double Wear, 1 fl oz", ""),
        ("Average Joe's Coffee, 12 oz", ""),
        ("Ground Beef 80/20, 1 lb (approximately 4 servings)", ""),
    ],
)
def test_approximate_weight_wording_is_found_in_the_title_even_without_a_weight(
    title: str, wording: str
) -> None:
    assert wrec.approx_weight_text(title) == wording


def test_a_product_with_an_approximate_title_weight_is_excluded_with_its_evidence() -> None:
    (grapes,) = _items(
        syn.Item(
            "381105260", "Fresh Black Seedless Grapes, From California, Bag (2.25 lbs/Bag Est.)", "$5.97"
        )
    )
    built, _ = _record(grapes)
    assert RecordFlag.APPROX_WEIGHT in built.reasons  # type: ignore[attr-defined]
    # The wording, the field and path it was read from, and the whole value (release 1.4.0).
    assert built.provenance["_approx_weight"] == {  # type: ignore[attr-defined]
        "field": "product_title",
        "path": f"{grapes.path}.name",
        "text": "2.25 lbs/Bag Est.",
        "value": grapes.name,
    }
    ev, _, log = wrec.evidence(
        grapes,
        fetch_id="f1",
        observed_at="2026-10-23T18:18:00Z",
        store_id=STORE,
        modality="PICKUP",
        page_verified=True,
    )
    assert log["approx_weight"]["field"] == "product_title" and ev.approx_weight_text == "2.25 lbs/Bag Est."


def test_a_sale_keeps_both_displayed_prices_and_a_range_is_never_turned_into_a_price() -> None:
    sale, rng, weighed = _items(
        syn.Item("21", "Sale Item, 10 oz", "$2.50", was="$3.00", unit="25.0 ¢/oz"),
        syn.Item("22", "Options Item, 10 oz", "", price_range="$3.97 - $5.97", flat_price=True),
        syn.Item("23", "Weighed Item, 1 lb", "$1.38", unit="$1.38/lb", weight_priced=True),
    )
    d, _ = wrec.price_display(sale)
    assert (d.regular_price, d.sale_price) == ("3.00", "2.50")
    d, flags = wrec.price_display(rng)
    assert (d.regular_price, d.sale_price) == ("", "") and RecordFlag.PRICE_RANGE in flags
    d, _ = wrec.price_display(weighed)
    assert d.is_relative  # final cost by weight: flagged, kept unless an estimate is stated (release 1.4.0)


def test_local_offer_rules() -> None:
    pickup, market, ship, other, oos, delivery = _items(
        syn.Item("31", "Pickup Item, 1 ct", "$1.00"),
        MARKET,
        syn.Item("33", "Ship Item, 1 ct", "$4.00", lines=(("SHIPPING", "0"),)),
        syn.Item("34", "Other Store Item, 1 ct", "$1.00", lines=(("PICKUP", "1234"),)),
        syn.Item("35", "Out Item, 1 ct", "$1.00", lines=(), availability="OUT_OF_STOCK"),
        syn.Item("36", "Delivery Item, 1 ct", "$1.00", lines=(("DELIVERY", "{store}"),)),
    )  # fmt: skip
    offers = {
        i.item_id: wrec.local_offer(i, STORE, "PICKUP") for i in (pickup, market, ship, other, oos, delivery)
    }
    assert offers["31"].accepted and offers["31"].for_store
    assert offers["32"].marketplace and not offers["32"].accepted
    assert offers["33"].ship_only and not offers["33"].accepted
    assert offers["34"].other_store == "1234" and not offers["34"].accepted
    # Out of stock without a line for the store proves neither the store's assortment nor its price.
    assert offers["35"].out_of_stock and not offers["35"].store_line and not offers["35"].accepted
    # A Delivery line of the store: the store's product, but not its Pickup price.
    assert offers["36"].from_store and not offers["36"].for_store and offers["36"].accepted
    assert not offers["36"].pickup_price and offers["31"].pickup_price


def test_out_of_stock_with_the_stores_pickup_line_keeps_the_stores_price() -> None:
    (oos,) = _items(syn.Item("38", "Out Item, 12 oz", "$1.00", availability="OUT_OF_STOCK"))
    offer = wrec.local_offer(oos, STORE, "PICKUP")
    assert offer.out_of_stock and offer.accepted and offer.pickup_price
    built, _ = _record(oos)
    assert built.status is RecordStatus.VALID and RecordFlag.OUT_OF_STOCK in built.flags  # type: ignore[attr-defined]


def test_records_follow_the_22_field_contract_and_the_exclusion_rules() -> None:
    milk, market, ship, oos, approx = _items(
        MILK,
        MARKET,
        syn.Item("33", "Ship Item, 1 ct", "$4.00", lines=(("SHIPPING", "0"),)),
        syn.Item("35", "Out Item, 12 oz", "$1.00", lines=(), availability="OUT_OF_STOCK"),
        syn.Item("37", "Steak, approx 1.5 lb", "$9.00"),
    )  # fmt: skip
    built, _ = _record(milk)
    rec = built.record  # type: ignore[attr-defined]
    assert list(rec) == list(OUTPUT_FIELDS) and all(isinstance(v, str) for v in rec.values())
    assert rec["upc"] == "" and built.upc == "wm:10450114"  # type: ignore[attr-defined]
    assert (rec["gupc"], rec["unit_price"]) == ("", "")
    assert rec["ppm"] == "2.4 ¢/fl oz" and rec["weight"] == "128 fl oz" and rec["store_brand"] == "yes"
    assert rec["regular_price"] == "3.12" and not format_violations(rec)
    assert built.status is RecordStatus.VALID  # type: ignore[attr-defined]
    market_rec, _ = _record(market)
    assert RecordFlag.MARKETPLACE_OFFER in market_rec.reasons  # type: ignore[attr-defined]
    ship_rec, _ = _record(ship)
    assert RecordFlag.SHIP_ONLY in ship_rec.reasons  # type: ignore[attr-defined]
    oos_rec, _ = _record(oos)
    # No line for the store: not located by this page (the collector then looks for earlier evidence).
    assert oos_rec.status is RecordStatus.EXCLUDED  # type: ignore[attr-defined]
    assert RecordFlag.LOCATION_UNATTESTED in oos_rec.reasons  # type: ignore[attr-defined]
    assert RecordFlag.OUT_OF_STOCK in oos_rec.flags  # type: ignore[attr-defined]
    approx_rec, _ = _record(approx)
    assert RecordFlag.APPROX_WEIGHT in approx_rec.reasons  # type: ignore[attr-defined]


def test_an_unverified_page_never_yields_a_located_record() -> None:
    (milk,) = _items(MILK)
    built, _ = _record(milk, verified=False)
    assert RecordFlag.LOCATION_UNATTESTED in built.reasons  # type: ignore[attr-defined]


def test_deal_wording_is_separated_from_sale_merchandising_and_rewards() -> None:
    (it,) = _items(
        syn.Item(
            "41",
            "Deal Item, 12 oz",
            "$2.50",
            was="$3.00",
            badges=(
                ("ROLLBACK", "Rollback"),
                ("BEST_SELLER", "Best seller"),
                ("WPLUS", "Save with W+"),
                ("FF", "Free shipping"),
                ("MULTI", "2 for $5.00"),
                ("CASH", "Earn $2 Walmart Cash"),
                ("CPN", "Clip coupon: Save $1.00"),
            ),
        )
    )
    deals, other = wrec.deal_texts(it)
    assert deals == ["2 for $5.00", "Earn $2 Walmart Cash", "Clip coupon: Save $1.00"]
    assert {"Rollback", "Best seller", "Save with W+", "Free shipping"} <= set(other)
    built, _ = _record(it)
    rec = built.record  # type: ignore[attr-defined]
    assert (rec["volume_deals_description"], rec["volume_deals_price"]) == ("2 for $5.00", "5.00")
    assert rec["digital_deals_description"] == "Coupon: Clip coupon: Save $1.00"
    assert rec["digital_deals_price"] == ""  # "Save $1" states no final price
    assert "Walmart Cash" not in rec["digital_deals_description"]  # a reward paid later, not a price
    assert RecordFlag.CASHBACK_OFFER_EXCLUDED in built.flags  # type: ignore[attr-defined]


def test_a_family_size_or_multipack_title_is_not_a_volume_deal() -> None:
    (it,) = _items(syn.Item("42", "Cereal Family Size, 2 Pack, 19.3 oz", "$6.00"))
    built, _ = _record(it)
    assert built.record["volume_deals_description"] == ""  # type: ignore[attr-defined]


def test_category_page_links_pagination_and_store_page() -> None:
    nd = wpd.next_data(
        syn.category_page(
            [
                ("Shop All Foods", "/browse/food/976759"),
                ("Snacks", "/browse/food/snacks/976759_976787"),
                ("Recipes", "/cp/recipes/123"),
            ]
        )
    )
    links = wpd.subcategory_links(nd)
    assert [(x.name, x.url) for x in links] == [
        ("Shop All Foods", "https://www.walmart.com/browse/food/976759"),
        ("Snacks", "https://www.walmart.com/browse/food/snacks/976759_976787"),
    ]
    pag = wpd.pagination(wpd.next_data(syn.listing_page([MILK], store=STORE, page=2, max_page=7, total=270)))
    assert (pag.current_page, pag.max_page, pag.total_count) == (2, 7, 270)
    assert wpd.page_url("https://www.walmart.com/browse/x/1?povid=a", 3) == (
        "https://www.walmart.com/browse/x/1?povid=a&page=3"
    )
    assert wpd.page_url("https://www.walmart.com/browse/x/1", 1) == "https://www.walmart.com/browse/x/1"
    details = wpd.store_details(
        wpd.next_data(
            syn.store_page(STORE, name="Chicago Supercenter", address="4650 W North Ave", **CHICAGO)
        ),
        STORE,
    )  # fmt: skip
    assert details is not None and details.location_text == "4650 W North Ave, Chicago, IL 60639"


def test_the_sanitizer_keeps_the_page_data_and_removes_session_identifiers() -> None:
    page = syn.store_page(
        STORE,
        name="Chicago Supercenter",
        address="4650 W North Ave",
        city="Chicago",
        state="IL",
        postal="60639",
    )
    out, report = sanitize_html(page)
    assert report.page_data_kept and report.page_data_values_redacted == 3
    for secret in ("sess-secret-abc", "203.0.113.7", "csrf-xyz"):
        assert secret not in out
    data = wpd.next_data(out)
    assert data["props"]["pageProps"]["bootstrapData"]["sessionId"] == REDACTED
    assert wpd.store_details(data, STORE) is not None  # the store's own data is untouched
    listing, _ = sanitize_html(syn.listing_page([MILK], store=STORE))
    assert "inline-token-123" not in listing and "/static/app.js" not in listing
    assert wpd.page_items(wpd.next_data(listing))[0].name == MILK.name
    assert json.loads(json.dumps(data))  # still valid JSON


def test_the_sanitizer_redacts_camel_case_session_and_trace_identifiers() -> None:
    # Release 1.3.1: release 1.3.0 matched session keys only after "_" or "-" (or at the start), so every
    # page it stored kept Walmart's isomorphicSessionId and adSessionId (and the request trace ids).
    data = {
        "props": {
            "isomorphicSessionId": "1ooPcLIyfWyH73KevC9Ie",
            "trace": {"traceId": "6d5a6533a1c8165cfd8f373f", "spanId": "1a8c67ba1414e474"},
            "renderViewId": "ab2ebe48-9ee0-42b4-aef5-8c6b8f70a61d",
            "adContext": {"adSessionId": "132e381a472bf9b3dad8c44cb7bdf900"},
            "pageProps": {"initialData": {"data": {"product": {"usItemId": "15163163334", "name": "Corn"}}}},
        }
    }
    page = (
        '<html><body><script id="__NEXT_DATA__" type="application/json">'
        f"{json.dumps(data)}</script></body></html>"
    )
    out, report = sanitize_html(page)
    assert report.page_data_values_redacted == 5
    for value in ("1ooPcLIyfWyH73KevC9Ie", "6d5a6533", "1a8c67ba", "ab2ebe48", "132e381a"):
        assert value not in out
    props = wpd.next_data(out)["props"]
    assert props["isomorphicSessionId"] == props["adContext"]["adSessionId"] == REDACTED
    assert props["pageProps"]["initialData"]["data"]["product"] == {"usItemId": "15163163334", "name": "Corn"}


def test_walmart_challenge_pages_are_refusals_and_a_page_without_its_data_is_not_content() -> None:
    v = detect_document_challenge(200, syn.CHALLENGE_PAGE, state_marker=WALMART_STATE_MARKER)
    assert v.is_challenge and "perimeterx_robot_or_human" in v.reasons
    v = detect_document_challenge(200, "<html><body>hello</body></html>", state_marker=WALMART_STATE_MARKER)
    assert v.is_challenge and "missing_initial_state" in v.reasons
    ok = detect_document_challenge(
        200, syn.listing_page([MILK], store=STORE), state_marker=WALMART_STATE_MARKER
    )
    assert not ok.is_challenge


def test_a_store_page_without_a_store_object_is_read_from_its_displayed_address() -> None:
    text = "Chicago Supercenter\n4650 W North Ave\nChicago, IL 60639\nOpen today"
    details = wpd.store_details_from_text(text, STORE, "4650", "Chicago Supercenter")
    assert details is not None
    assert (details.address_line1, details.city, details.state, details.postal_code) == (
        "4650 W North Ave",
        "Chicago",
        "IL",
        "60639",
    )
    assert wpd.store_details_from_text("1234 Other St, Elgin, IL 60120", STORE, "4650", "x") is None


def test_a_challenge_dialog_added_at_the_end_of_a_large_page_is_detected() -> None:
    page = syn.store_page(STORE, name="Chicago W N Ave Supercenter", address="4650 W North Ave", **CHICAGO)
    padded = page.replace("</body>", "<div>" + "x" * 450_000 + "</div>" + syn.CHALLENGE_DIALOG + "</body>")
    v = detect_document_challenge(None, padded, expect_initial_state=False, state_marker=WALMART_STATE_MARKER)
    assert v.is_challenge and "perimeterx_robot_or_human" in v.reasons
    clean = detect_document_challenge(
        None, page, expect_initial_state=False, state_marker=WALMART_STATE_MARKER
    )
    assert not clean.is_challenge


def test_a_bot_manager_block_answer_to_a_data_request_is_a_refusal() -> None:
    assert blocked_response(syn.PX_BLOCK_RESPONSE.encode())
    assert not blocked_response(b'{"data":{"setPickupStore":{"storeId":"5402"}}}')


def test_the_sanitizer_removes_third_party_api_keys_embedded_by_the_site() -> None:
    key = "AIza" + "S" * 35  # SYNTHETIC, shaped like a Google browser key
    page = (
        '<html><body><script id="__NEXT_DATA__" type="application/json">'
        f'{{"runtimeConfig":{{"mapsApiKey":"{key}","nested":["{key}"]}}}}</script>'
        f'<div data-config="{key}"></div></body></html>'
    )
    out, report = sanitize_html(page)
    assert key not in out and report.page_data_values_redacted == 2 and report.other_values_redacted == 1


def test_sizes_and_packs_of_one_product_stay_separate_records() -> None:
    small, large, pack = _items(
        syn.Item("51", "Great Value Whole Milk, Half Gallon, 64 fl oz", "$1.98", unit="3.1 ¢/fl oz"),
        syn.Item("52", "Great Value Whole Milk, Gallon, 128 fl oz", "$3.12", unit="2.4 ¢/fl oz"),
        syn.Item("53", "Great Value Whole Milk, Gallon, 128 fl oz, 2 Pack", "$6.24", unit="2.4 ¢/fl oz"),
    )
    keys = [wrec.product_key(i) for i in (small, large, pack)]
    assert keys == ["wm:51", "wm:52", "wm:53"]  # one identity per item: never merged by name
    weights = [wrec.title_size(i.name) for i in (small, large, pack)]
    assert weights == ["64 fl oz", "128 fl oz", "128 fl oz, 2 Pack"]


def test_a_listing_page_states_its_own_name_and_category_path() -> None:
    nd = wpd.next_data(
        syn.listing_page(
            [], store="3891", cat=("Laundry", ["1115193", "1115193_1071967"]), title="Results for Laundry"
        )
    )
    assert wpd.listing_identity(nd) == ("Laundry", ["1115193", "1115193_1071967"])
    assert wpd.listing_identity(wpd.next_data(syn.listing_page([], store="3891"))) == ("", [])


def test_configured_listings_under_the_rows_category_are_read_directly() -> None:
    from walmart_headless.collection.nodes import Node
    from walmart_headless.collection.walmart import direct_listings

    def node(*only: str, kind: str = "landing", tax: str = "1115193") -> Node:
        return Node(
            1, "Household Essentials", "src", "", tax, "https://www.walmart.com/cp/x/1", kind=kind, only=only
        )

    got = direct_listings(
        node("/browse/laundry/1115193_1071967", "https://www.walmart.com/browse/x/1115193_9?a=1")
    )
    assert got is not None
    assert [(x.name, x.url, x.id) for x in got] == [
        ("", "https://www.walmart.com/browse/laundry/1115193_1071967", "1115193_1071967"),
        ("", "https://www.walmart.com/browse/x/1115193_9", "1115193_9"),
    ]
    feeding = node("/browse/feeding/baby-formula/5427_133283_4720344", tax="133283")
    assert direct_listings(feeding) is not None  # the category id is a component, not only a prefix
    assert direct_listings(node()) is None  # nothing configured: the category page names the listings
    assert direct_listings(node("/browse/diapering/5427_486190")) is None  # not under this category
    assert direct_listings(node("1115193_1071967")) is None  # a path id alone: found on the category page
    assert direct_listings(node("/browse/laundry/1115193_1071967", kind="listing")) is None


# Titles exactly as the saved exports of the 2026-10-26/28 live runs hold them (no request): each states its
# own size in a form release 1.4.1 did not read, and its weight field was exported empty.
@pytest.mark.parametrize(
    ("title", "size"),
    [
        ("Clorox No Splash Bleach, 40 Fluid Ounces", "40 Fluid Ounces"),
        (
            "HALLS Cough and Throat Relief Mountain Menthol Sugar Free Cough Drops, Value Pack, 70 Drops",
            "70 Drops",
        ),
        ("Sambucol Cold and Flu Relief Tablets, Homeopathic Black Elderberry, 30 Tabs", "30 Tabs"),
        (
            "Purina Moist and Meaty Rise and Shine Awaken Bacon and Egg Flavor Soft Dog Food, 12 Pouches",
            "12 Pouches",
        ),
        (
            "Equate Cough & Cold 60mg Compare to Maximum Strength Mucinex® DM Active Ingredients 14 Tablets "
            "for Congestion",
            "14 Tablets",
        ),
        ("L'Oreal Paris EverPure Moisture Sulfate Free Shampoo and Conditioner, 1 Kit", "1 Kit"),
        ("Fresh Produce, Whole Red Radish, 1 Bunch", "1 Bunch"),
        ("Fresh Whole Green Onion 1 Bunch, Fresh Produce", "1 Bunch"),
    ],
)
def test_a_size_the_title_states_is_read_as_written(title: str, size: str) -> None:
    assert wrec.size_from_title(title).value == size


def test_a_multipack_in_the_title_keeps_its_count_and_its_unit_size_never_multiplied() -> None:
    title = (
        "(2 pack) Purina Dog Chow Complete Adult Dry Dog Food for Adult Dogs, Kibble Beef Flavor 18.5 lb Bag"
    )
    out = wrec.size_from_title(title)
    assert (out.value, out.outcome) == ("2 pack, 18.5 lb", "multipack_in_title")


# AUTHENTIC titles of 2026-10-31 (the campaign's Dry Dog Food pages, run 01M69Y1J6YWFEZ1DJHAC2MT17M) and of
# the 1.4.1 evidence. Until 1.5.0 these gave only the segment's size, although the price is for the whole
# pack: 50.62 at $1.58/lb buys 32 lb, not the "16 lbs" exported.
@pytest.mark.parametrize(
    ("title", "size_until_1_5_0", "size"),
    [
        (
            "(2 pack) Pure Balance Pro+ Large Breed Chicken & Brown Rice Recipe Dry Dog Food, 16 lbs",
            "16 lbs",
            "2 pack, 16 lbs",
        ),
        (
            "(3 pack) Purina Dog Chow Complete, Dry Dog Food for Adult Dogs High Protein, Real Chicken, "
            "44 lb Bag",
            "44 lb Bag",
            "3 pack, 44 lb Bag",
        ),
        ("(5 pack) Pure Balance Chicken & Brown Rice Recipe Dry Dog Food, 15 lbs", "15 lbs",
         "5 pack, 15 lbs"),
        # A size that says only "one" adds nothing to the multipack (until 1.5.1: "2 pack, 1 Pack").
        ("(2 pack) Ol' Roy Natural Large Beef Femur Dog Chew for Healthy Teeth, 1 Pack", "1 Pack",
         "2 pack"),
        # A size among the segments, not the last one.
        (
            "(3 pack) Equate Liquid Hand Soap, Clear, 50 fl oz, Compare to Softsoap® Aquarium Series "
            "Hand Soap",
            "50 fl oz",
            "3 pack, 50 fl oz",
        ),
        # A word that is no pack quantity ("Value Pack") stays out of it.
        (
            "(6 pack) Ricola Honey Herb Cough Drops for Sore Throat and Cough Relief, Value Pack, 45 Count",
            "45 Count",
            "6 pack, 45 Count",
        ),
        # Without brackets: a pack quantity outside the size's segment.
        (
            "Play-Doh 8-Pack Rainbow Colors Modeling Compound, 3 oz Cans, Classroom Arts & Crafts for "
            "Kids 2+",
            "3 oz Cans",
            "8-Pack, 3 oz Cans",
        ),
    ],
)  # fmt: skip
def test_a_multipack_outside_the_size_segment_stays_beside_the_size(
    title: str, size_until_1_5_0: str, size: str
) -> None:
    out = wrec.size_from_title(title)
    assert out.value != size_until_1_5_0
    assert (out.value, out.outcome) == (size, "multipack_in_title")


@pytest.mark.parametrize(
    ("title", "size", "outcome", "candidates"),
    [
        # SYNTHETIC titles for the rule's limits: the stored pages hold no title of these shapes.
        # The size already holds its pack: nothing is added or repeated.
        ("Example Paste, 4 oz (Pack of 4)", "4 oz (Pack of 4)", "trailing_segments", ()),
        ("Example Soda, 12 fl oz, 12 Pack Cans", "12 fl oz, 12 Pack Cans", "trailing_segments", ()),
        # The same pack quantity on both sides is one statement, in any spelling.
        ("(2-Pack) Example Soda, 2 Pack, 12 oz", "2 Pack, 12 oz", "trailing_segments", ()),
        # "2 pack" is not found inside "12 Pack".
        ("(2 pack) Example Soda, 12 Pack", "2 pack, 12 Pack", "multipack_in_title", ("2 pack", "12 Pack")),
        # Without brackets, one pack is not a multipack.
        ("Example 1-Pack Soap, 12 oz", "12 oz", "trailing_segments", ()),
        # Two different quantities and nothing to tell them apart: neither is chosen, the size stands.
        ("Example 2-Pack Soap 3-Pack Refill, 12 oz", "12 oz", "trailing_segments", ("2-Pack", "3-Pack")),
        # A bracket tells them apart.
        ("(2 pack) Example 3-Pack Soap, 12 oz", "2 pack, 12 oz", "multipack_in_title", ("2 pack", "12 oz")),
        # Not a quantity of packs: a model number and a word.
        ("Example Model#2-Pack Soap, 12 oz", "12 oz", "trailing_segments", ()),
        ("Example Family Pack Soap, 12 oz", "12 oz", "trailing_segments", ()),
    ],
)  # fmt: skip
def test_the_limits_of_keeping_a_multipack_beside_the_size(
    title: str, size: str, outcome: str, candidates: tuple[str, ...]
) -> None:
    out = wrec.size_from_title(title)
    assert (out.value, out.outcome, out.candidates) == (size, outcome, candidates)


# AUTHENTIC titles of the stored result pages (the campaign of 2026-10-31 and the 1.4.1 evidence): every title
# of those 1,470 whose size changed other than by keeping a multipack (pack_fix_151/SIZE_RULE_CHANGES_...csv).
@pytest.mark.parametrize(
    ("title", "size_until_1_5_0", "size", "outcome"),
    [
        # A medicine's strength is not the size of the pack, when the title also states one.
        ("Equate Alcohol-Free Dextromethorphan Guaifenesin Relief Liquid for Chest Congestion, 20mg/400mg, "
         "8 fl oz",
         "20mg/400mg, 8 fl oz", "8 fl oz", "trailing_segments"),
        ("Equate Children's Cough Relief Dextromethorphan HBr Chewable Tablets, Citrus Punch Flavor, 10 mg, "
         "16 Count",
         "10 mg, 16 Count", "16 Count", "trailing_segments"),
        ("Equate Maximum Strength Mucus Relief Guaifenesin Extended-Release Expectorant Tablets,1200 mg, "
         "14 Count",
         "1200 mg, 14 Count", "14 Count", "trailing_segments"),
        ("Equate Mucus Relief DM Guaifenesin Expectorant & Cough Suppressant Tablets, 600 mg, 20 Count",
         "600 mg, 20 Count", "20 Count", "trailing_segments"),
        # "Counts" is a count unit as "Count" is: the title's size, and the strength beside it steps aside.
        ("HealthA2Z® Mucus Relief | Guaifenesin 600 mg | 12 Hour | 300 Counts | No Benzene | Expectorant | "
         "Relieves Chest Congestion | Thins and Loosens Mucus | Extended Release",
         "600 mg", "300 Counts", "in_title"),
        # A measure in inches describes the product: never what its package holds.
        ("S&T INC. XL New Zealand Wool Dryer Balls, Fabric Softener for Laundry, Natural White, 2.9 in, "
         "6 Pack",
         "2.9 in, 6 Pack", "6 Pack", "trailing_segments"),
        ("OFEFE 100 Pcs Diaper Pins, Baby Safety Pins, Diaper Pins for Cloth Diapers, Heavy Duty, "
         "Stainless Steel, ABS Plastic, Colorful (Red, Yellow, Pink, Blue, Green, Purple), 2.2in, "
         "Safe Locking Closures",
         "2.2in", "100 Pcs", "in_title"),
        ("Utopia Home Folding Step Stool with Handle, Black – Anti-Slip, Holds Up to 300 lbs, for Kitchen, "
         "Bathroom & Home Use, 9 Inch",
         "9 Inch", "", "dimension_only"),
        # What a product bears is not what its package holds.
        ("Ingenuity Flip & Sit Potty Seat - For Ages 18 Months, Up to 50 Pounds", "50 Pounds", "", "none"),
        # The volume that ends the segment before a count of loads is part of the size.
        ("ARM & HAMMER Sensitive Skin Plus Fresh Scent Liquid Laundry Detergent 105 fl oz, 105 Loads",
         "105 Loads", "105 fl oz, 105 Loads", "trailing_segments"),
        ("ARM & HAMMER Sensitive Skin Plus Fresh Scent Liquid Laundry Detergent 170 fl oz, 170 Loads",
         "170 Loads", "170 fl oz, 170 Loads", "trailing_segments"),
    ],
)  # fmt: skip
def test_what_a_title_says_about_the_product_is_not_the_size_of_its_package(
    title: str, size_until_1_5_0: str, size: str, outcome: str
) -> None:
    out = wrec.size_from_title(title)
    assert out.value != size_until_1_5_0
    assert (out.value, out.outcome) == (size, outcome)


@pytest.mark.parametrize(
    ("title", "size", "outcome"),
    [
        # SYNTHETIC titles for the rule's limits: the stored pages hold no title of these shapes.
        # A strength with nothing else to state the size stays: it is all the title says.
        ("Example Ibuprofen Tablets, 200 mg", "200 mg", "trailing_segments"),
        # A strength before the size segments is not taken for a measure of the package.
        ("Example Ibuprofen 200 mg, 24 Count", "24 Count", "trailing_segments"),
        # A size segment that already states a measure gets nothing from the segment before it.
        ("Example Detergent 50 fl oz, 32 oz, 20 Loads", "32 oz, 20 Loads", "trailing_segments"),
        # Feet and yards of a real package still count ("Foil, 75 sq ft" is what the box holds).
        ("Example Aluminum Foil, 75 sq ft", "75 sq ft", "trailing_segments"),
        # Only "up to" marks a rating: the quantity without it is still the size.
        ("Example Potty Seat Refill 50 Pounds", "50 Pounds", "in_title"),
    ],
)  # fmt: skip
def test_the_limits_of_what_is_not_the_size_of_a_package(title: str, size: str, outcome: str) -> None:
    out = wrec.size_from_title(title)
    assert (out.value, out.outcome) == (size, outcome)


@pytest.mark.parametrize(
    ("title", "rule"),
    [
        (
            "Theraflu Max Strength Flu Symptom Relief - 20 Caplets Plus Theraflu Max Strength Nighttime Flu "
            "Medicine for Flu Symptom Relief- 20 Caplets Combo Pack",
            "ambiguous",  # two statements: neither is invented into one size
        ),
        ("Fresh Cantaloupe, Each", "none"),  # no size stated: the product page may state it
        ("Fresh Kale Greens, Bunch", "none"),  # no number
    ],
)
def test_a_title_with_no_single_size_stays_empty(title: str, rule: str) -> None:
    out = wrec.size_from_title(title)
    assert (out.value, out.outcome) == ("", rule)
