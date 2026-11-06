"""Release 1.6.8: what a navigation link shows. A link's query can narrow its listing (a facet, a price, a
shelf); two links show the same products only when they show the same view of the same listing. The URLs are
the shapes live category pages recorded (L4, 2026-11-03; L7 and L10, 2026-11-04)."""

from __future__ import annotations

from walmart_headless.collection import navigation
from walmart_headless.collection.walmart import listing_key

W = "https://www.walmart.com"
COUGH = (
    W + "/browse/health-medicine/shop-all-cold-cough-flu-medicine/976760_4661388_6244277_7158394"
    "?facet=health_concern%3aCough&povid=ColdCoughFluCPLHN_Shop_All_Cough"
)
SUBSCRIPTION = (
    W + "/browse/cold-cough-and-flu/shop-all-cold-cough-flu-medicine/976760_4661388_6244277_7158394"
    "?facet=subscription_eligible%3ASubscription+item"
)
DEODORANT = (
    W + "/browse/personal-care/deodorants-antiperspirants/1005862_1001487"
    "?povid=PersonalCare_PCCP_LHN_PERSONAL_CARE_Deodorant_2.9"
)
MENS_DEODORANT = (
    W + "/browse/personal-care/deodorants-antiperspirants/female/1005862_1001487"
    "?cat_id=1005862_1001487&facet=gender%3AMale?povid=PersonalCare_PCCP_LHN_MENS_GROOMING_Men's_Deodorant_2.9"
)
PANTRY = W + "/browse/pantry/great-value-pantry-deals/976759_976794_2002490?povid=FoodCP_Pantry"
GV_PANTRY = W + "/browse/food/great-value-pantry-deals/976759_976794_2002490?povid=FoodCP_GV_Pantry"
FRESH_FRUIT = (
    W + "/browse/pre-cut-fruits/0/0?_refineresult=true&_be_shelf_id=8210692&search_sort=100"
    "&facet=shelf_id%3A8210692&povid=976759_LHNCP_976759_Featuredshops_GrabnGo_FreshFruit_07_26"
)
SNACK_PACKS = (
    W + "/browse/kids-lunches-&-snacks/0/0?_refineresult=true&_be_shelf_id=7195079&search_sort=100"
    "&facet=shelf_id%3A7195079&povid=976759_LHNCP_976759_Featuredshops_GrabnGo_Snackpacks_07_26"
)
CLEARANCE = W + "/browse/household-essentials/1115193?facet=special_offers%3AClearance&povid=HHE_HHECP_LHN"
UNDER_5 = W + "/browse/5440?max_price=5&povid=Pets_CP_LHN_Under5"


def test_tracking_and_the_collectors_own_fulfillment_facet_do_not_narrow_a_listing() -> None:
    assert navigation.narrowing(DEODORANT) == ()
    assert navigation.narrowing(W + "/browse/x/976759_9176907?facet=fulfillment_method%3APickup") == ()
    assert navigation.narrowing(
        W + "/browse/x/976759_9176907?facet=fulfillment_method%3APickup||brand%3AGreat+Value&povid=a"
    ) == (("facet", "brand:Great Value"),)


def test_a_second_question_mark_separates_parameters_and_facets_are_sorted() -> None:
    assert navigation.narrowing(MENS_DEODORANT) == (("facet", "gender:Male"),)
    assert navigation.narrowing(W + "/browse/x/1?facet=b%3A2||a%3A1") == (("facet", "a:1"), ("facet", "b:2"))
    assert navigation.narrowing(UNDER_5) == (("max_price", "5"),)


def test_a_parameter_without_a_value_or_repeating_the_links_own_id_is_no_filter_an_unknown_one_is() -> None:
    assert navigation.narrowing(W + "/browse/x/123?povid=FSA_&_HAS_2.9") == ()  # live: an unencoded "&"
    assert navigation.narrowing(W + "/browse/x/123?facet=") == ()
    assert navigation.narrowing(W + "/browse/x/123?cat_id=123&povid=a") == ()
    assert navigation.narrowing(W + "/browse/x/123?cat_id=456") == (("cat_id", "456"),)
    assert navigation.narrowing(W + "/browse/x/123?not_seen_before=1") == (("not_seen_before", "1"),)
    assert navigation.filtered_listing(W + "/browse/x/123?not_seen_before=1") == W + "/browse/x/123"


def test_two_paths_to_the_same_view_are_one_read_two_filtered_views_are_not() -> None:
    assert listing_key(PANTRY) == listing_key(GV_PANTRY) == "browse:976759_976794_2002490"
    assert listing_key(COUGH) != listing_key(SUBSCRIPTION)
    assert listing_key(COUGH) == "browse:976760_4661388_6244277_7158394?facet=health_concern%3ACough"
    assert listing_key(MENS_DEODORANT) != listing_key(DEODORANT) == "browse:1005862_1001487"
    assert listing_key(FRESH_FRUIT) != listing_key(SNACK_PACKS)
    # A category page of its own is read for its navigation, which no filter changes.
    assert listing_key(W + "/cp/dairy-eggs/9176907?facet=x%3Ay&povid=z") == "cp:9176907"
    assert listing_key(W + "/shop/deals/baby") == ""


def test_a_filtered_view_names_the_listing_it_filters_and_a_shelf_is_a_listing_of_its_own() -> None:
    base = W + "/browse/health-medicine/shop-all-cold-cough-flu-medicine/976760_4661388_6244277_7158394"
    assert navigation.filtered_listing(COUGH) == base
    assert navigation.filtered_listing(MENS_DEODORANT).endswith("/female/1005862_1001487")
    assert listing_key(navigation.filtered_listing(MENS_DEODORANT)) == listing_key(DEODORANT)
    assert navigation.filtered_listing(CLEARANCE) == W + "/browse/household-essentials/1115193"
    assert navigation.filtered_listing(UNDER_5) == W + "/browse/5440"
    for itself in (DEODORANT, PANTRY, FRESH_FRUIT, SNACK_PACKS, W + "/cp/x/9176907?facet=a%3Ab"):
        assert navigation.filtered_listing(itself) == "", itself


def test_a_shelf_is_recorded_under_its_own_id() -> None:
    assert navigation.read_id(FRESH_FRUIT) == "0@shelf_id:8210692"
    assert navigation.read_id(SNACK_PACKS) == "0@shelf_id:7195079"
    assert navigation.read_id(COUGH) == "976760_4661388_6244277_7158394"  # a listing's ID, filtered or not
    assert navigation.read_id(W + "/browse/x/0/0") == "0"
    long = navigation.read_id(W + "/browse/x/0/0?facet=" + "||".join(f"shelf_id%3A{n:08d}" for n in range(9)))
    assert long.startswith("0@") and len(long) == 18, long


def test_view_key_names_a_listing_itself_by_its_id_and_a_filtered_view_with_its_filters() -> None:
    assert navigation.view_key(DEODORANT) == "1005862_1001487"
    assert navigation.view_key(MENS_DEODORANT) == "1005862_1001487?facet=gender%3AMale"
    assert navigation.view_key(W + "/cp/personal-care/1005862?povid=x") == "1005862"
    assert navigation.view_key(W + "/") == ""
