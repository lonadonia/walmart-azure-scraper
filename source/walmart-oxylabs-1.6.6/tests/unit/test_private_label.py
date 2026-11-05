"""Walmart's own brands (config/walmart_private_label_brands.yaml) give store_brand "yes"."""

from __future__ import annotations

import pytest

from walmart_headless.assembly.private_label import PrivateLabelDetector
from walmart_headless.core.findings import RecordFlag
from walmart_headless.core.settings import PrivateLabelConfig


@pytest.fixture
def detector(private_label: PrivateLabelConfig) -> PrivateLabelDetector:
    return PrivateLabelDetector(private_label)


@pytest.mark.parametrize(
    ("title", "brand", "expected"),
    [
        ("Great Value Whole Vitamin D Milk, Gallon, 128 fl oz", "Great Value", "yes"),
        ("Equate Beauty Micellar Cleansing Water, 13.5 fl oz", "Equate Beauty", "yes"),
        ("Parent's Choice Newborn Diapers, 84 Count", None, "yes"),  # title only
        ("Parent’s Choice Baby Wipes, 3 Packs", None, "yes"),  # curly apostrophe
        ("Pen+Gear Composition Book, Wide Ruled", "Pen+Gear", "yes"),
        ("Pampers Swaddlers Diapers, Size 1, 84 Count", "Pampers", "no"),
        ("Great Valley Farms Honey", None, "no"),  # the brand must end on a word boundary
    ],
)
def test_brand_and_title_signals(
    detector: PrivateLabelDetector, title: str, brand: str | None, expected: str
) -> None:
    assert detector.detect(title=title, upc=None, brand=brand).value == expected


# AUTHENTIC titles of the stored result pages (the campaign of 2026-10-31 and the 1.4.1 evidence). Until 1.5.0
# each of the "yes" rows gave "no", since the brand is not the title's first word.
@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("(2 pack) Ol' Roy Natural Large Beef Femur Dog Chew for Healthy Teeth, 1 Pack", "yes"),
        ("(4 pack) Parent's Choice Maximum Strength Diaper Rash Ointment with Zinc Oxide, 4 oz", "yes"),
        ("(3 pack) Equate Liquid Hand Soap, Clear, 50 fl oz, Compare to Softsoap® Aquarium Series Hand Soap",
         "yes"),
        ("Organic Marketside Fresh Baby Peeled Carrots, 1 lb Bag", "yes"),
        ("Children's Equate Cough & Cold Relief DM, Multi-Symptom Liquid for Kids, Grape Flavor, 4 fl oz",
         "yes"),
        # Release 1.5.2: the USPTO's record names Walmart Apollo, LLC as the owner (docs/PRIVATE_LABEL.md).
        ("(2 pack) Pure Balance Pro+ Large Breed Chicken & Brown Rice Recipe Dry Dog Food, 16 lbs", "yes"),
        # A multipack of another brand stays "no", and a brand only compared to stays "no".
        ("(3 pack) Purina Dog Chow Complete, Dry Dog Food for Adult Dogs High Protein, Real Chicken, "
         "44 lb Bag", "no"),
    ],
)  # fmt: skip
def test_a_brand_after_a_bracketed_multipack_or_a_listed_wording(
    detector: PrivateLabelDetector, title: str, expected: str
) -> None:
    assert detector.detect(title=title, upc=None, brand=None).value == expected


@pytest.mark.parametrize(
    "brand", ["Prima Della", "Clear American", "ReliOn", "Special Kitty", "Vibrant Life", "Pure Balance"]
)
def test_a_brand_confirmed_at_the_uspto_is_private_label(detector: PrivateLabelDetector, brand: str) -> None:
    """Until 1.5.1 these six were left out as unconfirmed, so every product of theirs read "no"."""
    assert detector.detect(title=f"{brand} Sample Product, 1 Count", upc=None, brand=brand).value == "yes"
    assert detector.detect(title=f"{brand} Sample Product, 1 Count", upc=None, brand=None).value == "yes"


@pytest.mark.parametrize("brand", ["Scent Theory", "Millie Moon", "Fresh Produce", "Unbranded"])
def test_a_brand_with_no_evidence_of_walmart_ownership_stays_no(
    detector: PrivateLabelDetector, brand: str
) -> None:
    assert detector.detect(title=f"{brand} Sample Product", upc=None, brand=brand).value == "no"


@pytest.mark.parametrize(
    ("title", "brand"),
    [
        ("Ol' Roy Complete Dog Food, 15 lbs", "Ol'Roy"),  # page data's spelling against the title's
        ("Pure Balance Pro+ Salmon Dry Dog Food, 16 lbs", "Pure Balance Pro+"),
    ],
)
def test_walmarts_spelling_of_a_listed_brand_is_no_signal_conflict(
    detector: PrivateLabelDetector, title: str, brand: str
) -> None:
    result = detector.detect(title=title, upc=None, brand=brand)
    assert result.value == "yes" and not result.flags


def test_a_title_that_only_mentions_a_listed_brand_further_along_is_no_signal(
    detector: PrivateLabelDetector,
) -> None:
    """SYNTHETIC wording: a comparison with a store brand says nothing about the product's own brand."""
    assert detector.detect(title="Example Soap, Compare to Equate Hand Soap", upc=None).value == "no"
    assert detector.title_brand("(two pack) Great Value Crackers") is None  # no number: not a multipack


def test_a_brand_outside_the_list_wins_over_a_title_signal_and_is_flagged(
    detector: PrivateLabelDetector,
) -> None:
    r = detector.detect(title="Great Value Style Crackers", upc=None, brand="Nabisco")
    assert r.value == "no"
    assert RecordFlag.PRIVATE_LABEL_SIGNAL_CONFLICT in r.flags


def test_the_longest_brand_wins(detector: PrivateLabelDetector) -> None:
    assert detector.title_brand("Equate Beauty Facial Wipes") == "equate beauty"
    assert detector.title_brand("Equate Ibuprofen Tablets") == "equate"
