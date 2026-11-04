"""Walmart listing items as record evidence (the 22 fields' inputs) and the local-offer decision.

Store assortment, availability and the local price are three separate questions (shared requirements
§3), answered from the page's data for that item:

* a fulfillment line of the configured kind (Pickup) for the configured store: the product is the store's
  and its displayed price is the store's price for that fulfillment, even when other sellers also list the
  product (the item shown is Walmart's own offer); out of stock with such a line: still the store's price,
  flagged ``OUT_OF_STOCK``;
* another local line for the configured store (Delivery from the store) and no line of the configured
  kind: the product is the store's, but the displayed price is not shown for the configured fulfillment, so
  it is not taken as the store's Pickup price (the collector exports the product without prices);
* a named seller that is not Walmart: a marketplace offer, excluded (``MARKETPLACE_OFFER``). A listing tile
  names its seller in ``sellerName``, a product page in ``sellerDisplayName`` with ``sellerType`` (INTERNAL
  or EXTERNAL); a product page that names no seller but states EXTERNAL is a marketplace offer too;
* only shipping lines: a shipping-only offer, excluded (``SHIP_ONLY``); a shipping price is never used;
* a line of the configured kind for another store: a wrong-store price; the page fails its store check;
* no line for the store at all (for example ``OUT_OF_STOCK`` with no fulfillment): the page does not show
  the product as the store's. Out of stock alone proves neither the store's assortment nor its price; the
  collector looks for independent evidence (an earlier verified observation at the store).

Sizes. Walmart's listing shows the size inside the product title ("Great Value Whole Milk, Gallon,
128 fl oz"), not in a field of its own (``averageWeight`` is empty on the listings read). In order: the
title's trailing comma-separated segments that read as a quantity with a unit; else the one group of
comma-separated size segments anywhere in the title ("Fresh Cranberries, 12 oz Bag, Whole Fruit"); else the
one quantity with a weight, volume or count unit written inside the title ("Medjool Dates 8oz Pouch",
"Paste 4 oz (Pack of 4)"). The text is kept as written, never normalized or calculated. Several separate
expressions ("10 Pack ... 100 Pcs") are ambiguous and give no size, except a bracketed multipack beside one
size ("(2 pack) ... 18.5 lb Bag" keeps both) and a medicine's strength beside its count ("60mg ... 14 Tablets"
is 14 Tablets) since release 1.5.0; dimensions ("65 Inch") and designations ("Size 4") are not package sizes.
A size read from the comma-separated segments keeps the multipack the title states outside them, the pack
first ("(2 pack) Pure Balance ... Dry Dog Food, 16 lbs" gives "2 pack, 16 lbs", "Play-Doh 8-Pack ..., 3 oz
Cans" gives "8-Pack, 3 oz Cans"; release 1.5.1): the displayed price is for the whole pack. Never multiplied.
Also since release 1.5.1, what a title says about the product is not the size of its package: a measure in
inches ("2.9 in, 6 Pack" is 6 Pack, "9 Inch" alone gives no size), what the product bears ("Holds Up to 300
lbs") and a strength beside what the package holds ("1200 mg, 14 Count" is 14 Count). A weight or volume that
ends the segment before size segments stating none stays with them ("... Detergent 105 fl oz, 105 Loads").
A size segment ends at the first word that names neither the quantity nor its package (release 1.3.1): "3 lb
Bag - Naturally Ripened Citrus Fruit" gives "3 lb Bag", "60 Sheets Easy Tear" gives "60 Sheets", "8 oz Clam
Shell" stays whole; a quantity followed by a nutrient ("10g Protein") is a nutrition claim, not a size. The
size is still the title's own text, a prefix of its segment.

Approximate weights (shared requirements §5). A product is excluded when its source weight wording is
approximate: an approximate word next to a quantity with a weight or volume unit, in the title or in a
source size field, before it ("approx. 1.5 lb", "about 2 lb") or after it in the same clause ("2.25
lbs/Bag Est."), whether or not the size reached ``weight``. An approximate word elsewhere (a brand such as
"About Time", "Best") is not approximate-weight wording. The exact text and field are logged.

Deals. Only displayed promotion wording reaches the shared classifier: multi-unit offers, coupons, and
rewards paid later (Walmart Cash, rebates, cash back), which never become a price. Promotion wording is
kept whole, with its fulfillment, membership and quantity conditions (a fulfillment word never drops an
offer). Sale badges (Rollback, Clearance, Reduced price), fulfillment lines and merchandising badges ("Best
seller") are not deals; a family-size or multipack label is not a volume offer. Structured promotion data
without displayed wording (``promoDiscount``) is logged, never turned into a description or a price.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, replace
from decimal import Decimal, InvalidOperation
from typing import Any

from walmart_headless.assembly.offers import OfferObservation, OfferSource
from walmart_headless.assembly.prices import PriceDisplay, PriceDisplayKind
from walmart_headless.assembly.record_builder import BuiltRecord, FieldSource, ProductEvidence, SourceCheck
from walmart_headless.core.findings import RecordFlag
from walmart_headless.core.text import normalize_single_price
from walmart_headless.sites.walmart.page_data import AS_GIVEN, ValueSource, WalmartItem

SOURCE = "walmart_page_data"  # FieldSource.source for values read from a page's __NEXT_DATA__
PRICE_READ = "read as one two-decimal price (core.text.normalize_single_price)"
KEY_PREFIX = "wm:"
WALMART_SELLERS = frozenset({"walmart.com", "walmart", "walmart inc.", "walmart inc"})
SHIP_KINDS = frozenset({"SHIPPING", "SHIP", "SHIP_TO_HOME"})
OUT_OF_STOCK = frozenset({"OUT_OF_STOCK", "NOT_AVAILABLE", "UNAVAILABLE"})
_UNIT = (
    r"(?:fl\.?\s?oz|fl\.?\s?ounces?|fluid\s+ounces?|oz|lbs?|ct|counts?|pk|packs?|g|kg|mg|ml|l|liters?|litres?"
    r"|gal|gallons?|qt|quarts?|pt|pints?|sq\.?\s?ft|ft|in|inch(?:es)?|each|ea|sheets?|rolls?|pieces?|pcs?|pc"
    r"|bags?|cans?|bottles?|tablets?|tabs?|capsules?|caplets?|softgels?|gummies|lozenges?|drops?|wipes|diapers"
    r"|pairs?|boxes|box|jars?|cups?|tubes?|sticks?|bars?|servings?|pods?|pacs?|packets?|pouch(?:es)?|loads?"
    r"|kits?|bunch(?:es)?|yds?|yards?|ounces?|pounds?|items?)"
)
# The quantity that opens a size segment ("12 oz", "approx 1.5 lb", "24-Pack", "Pack of 4").
_SIZE_HEAD = (
    r"(?:(?:approx\.?|approximately|about|avg\.?|average|est\.?|estimated)\s*)?"
    rf"\d+(?:\.\d+)?(?:\s*(?:-|–|to|x)\s*\d+(?:\.\d+)?)?(?:\s*{_UNIT}|-(?:packs?|pk|ct|count))\b(?!\s*\d)"
)
_SIZE_SEGMENT = re.compile(
    rf"^{_SIZE_HEAD}"
    r"[\w\s().,/+&'-]{0,40}$"
    r"|^(?:pack|case|box|set|bag|bundle) of \d+\b[\w\s().,/+&'-]{0,20}$",
    re.I,
)
_SIZE_START = re.compile(rf"^(?:{_SIZE_HEAD}|(?:pack|case|box|set|bag|bundle) of \d+\b)", re.I)
# Words that may follow the quantity inside a size segment: its units, its package and how the package is
# counted or sized ("12 oz Bag", "8 oz Clam Shell", "4 Pack Gift Box", "36.6 oz XL Value Can", "168 Wipes
# Total"). The first other word ends the size: what follows describes the product (release 1.3.1).
_PACKAGE_WORD = re.compile(
    r"(?:bags?|box(?:es)?|packages?|packs?|pk|pouch(?:es)?|bottles?|cans?|jars?|containers?|cartons?|cases?"
    r"|tubs?|trays?|clamshells?|clams?|shells?|bowls?|bunch(?:es)?|cups?|tubes?|jugs?|canisters?|tins?"
    r"|packets?|sachets?|sleeves?|loaf|loaves|nets?|sacks?|buckets?|pails?|crates?|baskets?|shakers?"
    r"|dispensers?|spray|pump|squeeze|aerosol|sticks?|bars?|rolls?|sheets?|pods?|pacs?|loads?|wipes|diapers"
    r"|counts?|ct|each|ea|pieces?|pcs?|dozen|servings?|tablets?|capsules?|caplets?|softgels?|gummies|lozenges?"
    r"|drops?|tabs?|cartridges?|envelopes?|refills?|combo|kits?|sets?|pairs?|items?|total|half|plastic|glass"
    r"|aluminum|resealable|single|individual|individually|wrapped|minis?|large|small|medium|regular|gift"
    r"|club|family|value|size|bulk|mega|giant|jumbo|big|party|sharing|king|fun|snack|travel|bonus|twin"
    r"|multi|multipack|variety|economy|bundle|xl|xxl|of|x|per|and|fl|fluid|oz|ounces?|lbs?|pounds?|g|grams?|kg"
    r"|mg|ml|l|liters?|litres?|gal|gallons?|qt|quarts?|pt|pints?|in|inch(?:es)?|ft|sq|cm|mm|m|yds?|yards?)",
    re.I,
)
# A quantity followed by a nutrient is a nutrition claim, not a size ("10g Protein, 2.6 oz Pouch").
_NUTRIENT = re.compile(r"\s*(?:protein|fiber|fibre|sugars?|carbs?|calories|cal|fat|sodium|caffeine)\b", re.I)
_SIZE_TOKEN = re.compile(r"\s*(\([^()]*\)|[^\W\d_]+\.?|\d+(?:\.\d+)?|[,/+&×x-]|\S)")
_SIZE_JOINER = re.compile(r"[,/+&×x-]", re.I)
# Badges that mark the price itself (a sale shown with a struck-through price): never deals of their own.
SALE_BADGES = frozenset({"rollback", "clearance", "reduced price", "price drop", "special buy"})
# Wording that marks a promotion (as opposed to merchandising or fulfillment badges).
_PROMO = re.compile(
    r"\b\d+\s*(?:for|/)\s*\$|\bbuy\s+\d+|\bget\s+\d+\s+free\b|\bbogo\b|\bmix\s*(?:&|and|or)\s*match\b"
    r"|\bwhen you buy\b|\bcoupon\b|\bwalmart\s+cash\b|\bcash\s*back\b|\brebate\b|\bclip\b"
    r"|\bsave\s+\$\d|\b\d+%\s*off\b|\$\d+(?:\.\d{2})?\s*off\b",
    re.I,
)
_CLIP = re.compile(
    r"\b(?:clip|activate|add (?:the )?(?:coupon|offer)|save (?:the )?(?:coupon|offer))\b", re.I
)

# Approximate-weight wording inside a weight expression (see the module docstring).
_APPROX_WORD = r"(?:approx\.?|approximately|about|avg\.?|average|est\.?|estimated|~)"
_WEIGHT_UNIT = (
    r"(?:fl\.?\s?oz|fl\.?\s?ounces?|fluid\s+ounces?|oz|ounces?|lbs?|pounds?|g|grams?|kg|kilograms?|mg|ml|l"
    r"|liters?|litres?|gal|gallons?|qt|quarts?|pt|pints?)"
)
_QTY = r"\d+(?:\.\d+)?(?:\s*(?:-|–|to)\s*\d+(?:\.\d+)?)?"
_APPROX_WEIGHT = re.compile(
    rf"(?<!\w){_APPROX_WORD}\s*{_QTY}\s*{_WEIGHT_UNIT}\b"
    rf"|\b{_QTY}\s*{_WEIGHT_UNIT}\b[^,;()\d]{{0,24}}?(?<!\w){_APPROX_WORD}(?!\w)",
    re.I,
)
# An estimate word in Walmart's wording next to a price ("each (est.)": the price of one piece, whose weight
# is estimated; its final cost is charged by weight).
_ESTIMATE_WORD = re.compile(
    r"(?<!\w)(?:est\.?|estimated|approx\.?|approximately|avg\.?|average|about)(?!\w)|~", re.I
)
# Walmart's wording next to the price of a product sold by weight that names the weight the price is for
# ("$0.25 / 0.14lb"): the quantity is the displayed size of what that price buys.
_PRICE_FOR_WEIGHT = re.compile(rf"/\s*(\d+(?:\.\d+)?\s*{_WEIGHT_UNIT})", re.I)
# A quantity with a weight, volume or count unit written inside a title (not a dimension: inches, feet and
# yards describe the product, not its package). "Size 4" is a designation, not a quantity, and "Holds Up to
# 300 lbs" says what the product bears, not what its package holds.
_COUNT_UNIT = (
    r"(?:ct|counts?|pk|packs?|pcs?|pieces?|sheets?|rolls?|wipes|diapers|pods?|pacs?|packets?|pouch(?:es)?|loads?"
    r"|tablets?|tabs?|capsules?|caplets?|softgels?|gummies|lozenges?|drops?|kits?|bunch(?:es)?|servings?)"
)
_IN_TITLE = re.compile(
    r"(?<![\w.#/-])(?<!size )(?<!stage )(?<!step )(?<!up to )"
    rf"(?:{_QTY}\s?-?\s?(?:{_WEIGHT_UNIT}|{_COUNT_UNIT})\b"
    r"|(?:pack|case|box|set|bag|bundle) of \d+\b)",
    re.I,
)
# What may stand between two parts of one size expression ("4 oz (Pack of 4)", "12 fl oz, 12 Pack",
# "2 lbs. (Pack of 2)").
_JOINER = re.compile(r"^[\s,.()x×/+&-]*$", re.I)
_DIMENSION = re.compile(r"\d+(?:\.\d+)?\s?-?\s?(?:in|inch(?:es)?|ft|feet|yds?|yards?|cm|mm)\b", re.I)
# A medicine's strength ("60mg", "20mg/400mg", "500 mg + 200 mg Tablets"): not the size of the pack, when the
# title also states one ("14 Tablets").
_STRENGTH = re.compile(
    r"^\d+(?:\.\d+)?\s?-?\s?mg(?:\s?[/+&]\s?\d+(?:\.\d+)?\s?-?\s?mg)*"
    r"(?:\s+(?:tablets?|tabs?|caplets?|capsules?|softgels?|gummies|lozenges?))?$",
    re.I,
)
# A measure in inches describes the product ("9 Inch", "2.9 in"), not what its package holds.
_INCHES = re.compile(r"^\d+(?:\.\d+)?\s?-?\s?(?:in|inch(?:es)?)\.?$", re.I)
# A weight or volume that ends the segment before the size segments ("... Detergent 105 fl oz, 105 Loads").
_ENDS_WITH_MEASURE = re.compile(rf"(?<![\w.#/-])({_QTY}\s?-?\s?{_WEIGHT_UNIT})\.?$", re.I)
_HAS_MEASURE = re.compile(rf"(?<![\w.#/-]){_QTY}\s?-?\s?{_WEIGHT_UNIT}\b", re.I)
# A genuine multipack the title brackets ("(2 pack) ... 18.5 lb Bag").
_BRACKETED_PACK = re.compile(r"^(?:\d+\s?-?\s?(?:pk|packs?)|pack of \d+)$", re.I)
# A pack quantity anywhere in a title ("(2 pack)", "8-Pack", "Pack of 3").
_PACK_IN_TITLE = re.compile(r"(?<![\w.#/-])(\d+\s?-?\s?(?:pk|packs?)|pack of \d+)\b", re.I)
# A size that says only "one": beside a bracketed multipack it adds nothing ("(2 pack) ..., 1 Pack").
_ONE_PACK = re.compile(r"^1\s?-?\s?(?:pk|packs?|ct|counts?)\.?$", re.I)
# Two different packages of a set in one segment ("12.5 oz shampoo + 10.6 oz conditioner"): one size alone
# misstates what the price buys. A medicine's two strengths ("500 mg + 200 mg") are not packages.
_TWO_PACKAGES = re.compile(
    rf"^{_QTY}\s?-?\s?{_WEIGHT_UNIT}\.?(?:\s+[^\d,+&]+?)?\s*(?:\+|&|\band\b)\s*"
    rf"{_QTY}\s?-?\s?{_WEIGHT_UNIT}\.?(?:\s+[^\d,+&]+)?$",
    re.I,
)
_MILLIGRAMS = re.compile(r"\d\s?-?\s?mg\b", re.I)


def product_key(item: WalmartItem) -> str:
    """The record's identity: the UPC when the page states one, else Walmart's item ID (never exported
    as ``upc``). Each size, pack and variant is its own item, so they never merge."""
    return item.upc or f"{KEY_PREFIX}{item.item_id}"


# A trailing note in brackets without a number ("(Select for More Options)", "(Shelf-Stable)"): not a size.
_NOTE = re.compile(r"\s*\([^\d()]*\)\s*$")


@dataclass(frozen=True)
class SizeEvidence:
    """Where the product's size was read, as written, or why none was."""

    value: str
    # trailing_segments | title_segments | in_title | multipack_in_title | ambiguous | dimension_only | none
    outcome: str
    candidates: tuple[str, ...] = ()  # every size expression the title holds, as written

    @property
    def found(self) -> bool:
        return bool(self.value)


def _segments(title: str) -> list[str]:
    """The title's comma-separated segments; a comma inside brackets ("(14 Ounce, 1 Count)") does not
    split."""
    parts: list[str] = []
    depth, start = 0, 0
    for i, ch in enumerate(title):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif ch == "," and depth == 0:
            parts.append(title[start:i].strip())
            start = i + 1
    parts.append(title[start:].strip())
    return parts


def _segment_size(segment: str) -> str:
    """The size a comma-separated title segment states, as written up to the first word that names neither
    the quantity nor its package, or "" when the segment is not a size."""
    segment = _NOTE.sub("", segment)
    if _TWO_PACKAGES.match(segment) and not _MILLIGRAMS.search(segment):
        return segment
    start = _SIZE_START.match(segment)
    if not _SIZE_SEGMENT.match(segment) or start is None or _NUTRIENT.match(segment, start.end()):
        return ""
    end = start.end() + (segment[start.end() : start.end() + 1] == ".")  # "13 lb. Bag", "40 oz."
    pos = end
    while pos < len(segment) and (m := _SIZE_TOKEN.match(segment, pos)) is not None:
        token = m.group(1)
        joiner = bool(_SIZE_JOINER.fullmatch(token))
        if token.startswith("("):
            if not re.search(r"\d", token):  # a bracket with a number belongs to the size: "(Pack of 4)"
                break
        elif not joiner and not token[0].isdigit() and not _PACKAGE_WORD.fullmatch(token.rstrip(".")):
            break
        pos = m.end()
        if not joiner:
            end = pos
    return segment[:end]


def _size_groups(parts: list[str]) -> list[list[str]]:
    """Runs of consecutive comma-separated segments (after the first) that read as sizes."""
    groups: list[list[str]] = []
    current: list[str] = []
    for p in parts[1:]:
        size = _segment_size(p)
        if size:
            current.append(size)
        elif current:
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    return groups


def _package_parts(sizes: list[str]) -> list[str]:
    """The parts of a size that state what the package holds (release 1.5.1): a measure in inches never does,
    and a medicine's strength only when nothing else does ("1200 mg, 14 Count" is 14 Count)."""
    kept = [s for s in sizes if not _INCHES.match(s)]
    return [s for s in kept if not _STRENGTH.match(s)] or kept


def _squeezed(text: str) -> str:
    return re.sub(r"[\s-]+", "", text).casefold()


def _with_multipack(title: str, size: str, outcome: str) -> SizeEvidence:
    """The size the title's segments state, beside the multipack the title states outside them: "(2 pack) Pure
    Balance ... Dry Dog Food, 16 lbs" sells two 16 lb bags at the displayed price (the page's own unit price
    says so), so "16 lbs" alone misstates what the price buys. Both are kept, the pack first, as written and
    never multiplied. A bracketed pack is a multipack whatever its number; an unbracketed one needs more than
    one pack. Two different pack quantities with nothing to tell them apart are not chosen between: the
    segments' size stands and the candidates are kept. A segment that says only "one" adds nothing to a
    multipack ("(2 pack) ..., 1 Pack" is "2 pack"; release 1.5.2)."""
    own = {_squeezed(m.group(1)) for m in _PACK_IN_TITLE.finditer(size)}
    bracketed: list[str] = []
    plain: list[str] = []
    for m in _PACK_IN_TITLE.finditer(title):
        pack = m.group(1)
        if _squeezed(pack) in own:
            continue
        if title[m.start() - 1 : m.start()] == "(" and title[m.end() : m.end() + 1] == ")":
            bracketed.append(pack)
        elif int(re.sub(r"\D+", "", pack)) > 1:
            plain.append(pack)
    chosen = bracketed or plain
    if len({_squeezed(c) for c in chosen}) == 1:
        value = chosen[0] if _ONE_PACK.match(size) else f"{chosen[0]}, {size}"
        return SizeEvidence(value, "multipack_in_title", (chosen[0], size))
    return SizeEvidence(size, outcome, tuple(chosen))


def size_from_title(title: str) -> SizeEvidence:
    """The product's size as the title writes it (see the module docstring), with the rule that found it."""
    parts = _segments(title)
    read: list[str] = []
    for p in reversed(parts[1:]):
        size = _segment_size(p)
        if not size:
            break
        read.insert(0, size)
    tail = _package_parts(read)
    if tail:
        # The weight or volume that ends the segment before them, when they state none ("... 105 fl oz, 105
        # Loads").
        before = _ENDS_WITH_MEASURE.search(parts[len(parts) - len(read) - 1])
        if before and not _STRENGTH.match(before.group(1)) and not any(_HAS_MEASURE.search(s) for s in tail):
            tail.insert(0, before.group(1))
        return _with_multipack(title, ", ".join(tail), "trailing_segments")
    groups = [g for g in (_package_parts(g) for g in _size_groups(parts)) if g]
    if len(groups) == 1:
        return _with_multipack(title, ", ".join(groups[0]), "title_segments")
    if len(groups) > 1:
        return SizeEvidence("", "ambiguous", tuple(", ".join(g) for g in groups))
    matches = list(_IN_TITLE.finditer(title))
    merged: list[tuple[int, int]] = []
    for m in matches:
        if merged and _JOINER.match(title[merged[-1][1] : m.start()]):
            merged[-1] = (merged[-1][0], m.end())
        else:
            merged.append((m.start(), m.end()))
    texts = []
    for start, end in merged:
        text = title[start:end]
        if text.count("(") > text.count(")") and title[end : end + 1] == ")":
            text += ")"
        texts.append(text.strip(" ,"))
    if len(texts) > 1:
        # A strength beside a pack size is not a second size.
        texts = [t for t in texts if not _STRENGTH.match(t)] or texts
    if len(texts) == 1:
        return SizeEvidence(texts[0], "in_title")
    if len(texts) == 2:
        # A bracketed multipack beside one size: both kept, the pack first, never multiplied.
        for pack, other in ((texts[0], texts[1]), (texts[1], texts[0])):
            if _BRACKETED_PACK.match(pack) and f"({pack})" in title:
                return SizeEvidence(f"{pack}, {other}", "multipack_in_title", tuple(texts))
    if len(texts) > 1:
        return SizeEvidence("", "ambiguous", tuple(texts))
    if _DIMENSION.search(title):
        return SizeEvidence("", "dimension_only", tuple(m.group(0) for m in _DIMENSION.finditer(title)))
    return SizeEvidence("", "none")


def title_size(title: str) -> str:
    """The size the title states ("128 fl oz", "16.9 fl oz, 24 Pack Bottles", "approx 1.5 lb", "8oz"), or ""
    (:func:`size_from_title`)."""
    return size_from_title(title).value


def approx_weight_text(text: str) -> str:
    """The approximate-weight wording in ``text`` (a title or a size field), or ""."""
    m = _APPROX_WEIGHT.search(text or "")
    return m.group(0) if m else ""


def estimated_price_wording(text: str) -> str:
    """The estimate word in Walmart's wording next to a price ("est." in "each (est.)"), or ""."""
    m = _ESTIMATE_WORD.search(text or "")
    return m.group(0) if m else ""


def approx_weight(item: WalmartItem) -> dict[str, str] | None:
    """Approximate- or estimated-weight wording the item displays, with the exact text, the whole value it
    was read in and its path; ``None`` when there is none. Its own size wording (its title or a source size
    field) or, since release 1.4.0, Walmart's wording next to its price when that states an estimate ("each
    (est.)": the price of one piece, whose weight is estimated). Being sold or charged by weight, or a
    "/lb" price per measure, is not such wording: it never excludes a product by itself."""
    for field_name, ref, value in (
        ("product_title", f"{item.path}.name", item.name),
        ("averageWeight", f"{item.path}.averageWeight", item.average_weight),
    ):
        m = _APPROX_WEIGHT.search(value or "")
        if m:
            return {"field": field_name, "path": ref, "text": m.group(0), "value": value}
    shown = estimated_price_wording(item.price_condition)
    if shown and item.price_condition_source is not None:
        return {
            "field": "price_display_condition",
            "path": f"{item.path}.{item.price_condition_source.path}",
            "text": shown,
            "value": item.price_condition,
            "weight_priced_by": "; ".join(item.weight_priced_by),
        }
    return None


def price_for_weight(item: WalmartItem) -> str:
    """The weight Walmart's wording next to the price of a product sold by weight names ("0.14lb" in "/
    0.14lb"), as given, or ""."""
    m = _PRICE_FOR_WEIGHT.fullmatch(item.price_condition.strip()) if item.weight_priced else None
    return m.group(1) if m else ""


def _price(text: str) -> str:
    try:
        return normalize_single_price(text)
    except ValueError:
        return ""  # several amounts: not one price


def price_display(item: WalmartItem) -> tuple[PriceDisplay, tuple[RecordFlag, ...]]:
    """The displayed price, and the struck-through price when there is a sale; never computed."""
    current, was = _price(item.price_string), _price(item.was_price_string)
    if "hidePriceForSOI" in item.price_codes and not current:
        return PriceDisplay(PriceDisplayKind.NOT_DISPLAYED, "", "", "", "see price in cart", "", ""), ()
    if not current:
        if item.price_range or item.price_string:
            shown = item.price_range or item.price_string
            return (
                PriceDisplay(PriceDisplayKind.NOT_DISPLAYED, "", "", "", shown, "", ""),
                (RecordFlag.PRICE_RANGE,),
            )
        return PriceDisplay(PriceDisplayKind.MISSING, "", "", "", "", "", ""), ()
    sale = False
    if was:
        try:
            sale = Decimal(was) > Decimal(current)
        except InvalidOperation:
            sale = False
    # The final cost depends on the weight: a relative price, flagged. Since release 1.4.0 that alone keeps
    # no product out (records.exclude_relative_price_items is false): an estimate stated next to the price
    # ("each (est.)") excludes it, by the approximate-weight rule (approx_weight).
    if item.weight_priced:
        kind = PriceDisplayKind.RELATIVE_SALE if sale else PriceDisplayKind.RELATIVE
    else:
        kind = PriceDisplayKind.SALE if sale else PriceDisplayKind.REGULAR
    regular, sale_price = (was, current) if sale else (current, "")
    original = item.was_price_string if sale else ""
    return PriceDisplay(kind, item.price_string, original, "", "", regular, sale_price), ()


def deal_texts(item: WalmartItem) -> tuple[list[str], list[str]]:
    """(promotion texts, other badge texts): only wording that states a promotion is a deal candidate. A
    promotion that also names a fulfillment, a membership or a limit ("2 for $5, Pickup only") stays a deal
    candidate, whole: those words are its conditions."""
    deals: list[str] = []
    other: list[str] = []
    for t in (*item.promo_texts, *item.badge_texts):
        low = t.casefold().strip()
        if low in SALE_BADGES or not _PROMO.search(t):
            other.append(t)
        else:
            deals.append(t)
    return list(dict.fromkeys(deals)), list(dict.fromkeys(other))


def offers(item: WalmartItem) -> list[OfferObservation]:
    """Promotion wording the page shows for the item, for the shared classifier (multi-unit offers to
    the volume fields, offers that need clipping or activation to the digital fields, rewards paid later
    never to a price)."""
    deals, _ = deal_texts(item)
    return [
        OfferObservation(
            source=OfferSource.JSON_PRODUCTS,
            text=t,
            display_order=i,
            tag="Coupon" if _CLIP.search(t) and "coupon" in t.casefold() else "",
            ctas=("Clip",) if _CLIP.search(t) else (),
        )
        for i, t in enumerate(deals)
    ]


@dataclass(frozen=True)
class LocalOffer:
    """Does the page show the item as the configured store's (assortment), and is its displayed price the
    store's price for the configured fulfillment? Availability is a third, separate fact."""

    lines: tuple[tuple[str, str], ...]  # every (fulfillment, store id) line the page states
    for_store: bool  # a line of the configured kind for the configured store
    from_store: bool  # another local line (delivery from the store) for the configured store
    other_store: str | None  # a line of the configured kind for another store (wrong-store price)
    walmart_seller: bool | None  # None: the page names no seller
    marketplace: bool
    ship_only: bool
    out_of_stock: bool
    note: str
    # The source names Walmart as the seller (sellerName or sellerDisplayName, or an unnamed INTERNAL seller).
    seller_verified: bool = True

    @property
    def store_line(self) -> bool:
        """A fulfillment line of the page names the configured store."""
        return self.for_store or self.from_store

    @property
    def accepted(self) -> bool:
        """The page shows the product as the store's: a line for the store, and no marketplace,
        shipping-only or other-store offer. Out of stock without a store line is not enough."""
        return not (self.marketplace or self.ship_only or self.other_store) and self.store_line

    @property
    def pickup_price(self) -> bool:
        """The displayed price is the store's price for the configured fulfillment: a line of that kind for
        the store, sold by Walmart (release 1.5.0: a page that names no seller does not establish a price). A
        Delivery line alone does not establish it."""
        return self.accepted and self.for_store and self.seller_verified


def local_offer(item: WalmartItem, store_id: str, modality: str) -> LocalOffer:
    wanted = modality.upper()
    lines = tuple((f.kind, f.store_id) for f in item.fulfillment)
    for_store = any(k == wanted and sid == store_id for k, sid in lines)
    from_store = any(k not in SHIP_KINDS and sid == store_id for k, sid in lines)
    other = next((sid for k, sid in lines if k == wanted and sid and sid != store_id), None)
    seller = item.seller_name.casefold().strip()
    walmart_seller = None if not seller else seller in WALMART_SELLERS
    marketplace = walmart_seller is False or (walmart_seller is None and item.seller_type == "EXTERNAL")
    seller_verified = walmart_seller is True or (walmart_seller is None and item.seller_type == "INTERNAL")
    out_of_stock = item.availability in OUT_OF_STOCK
    ship_only = bool(lines) and all(k in SHIP_KINDS for k, _ in lines)
    if marketplace:
        who = repr(item.seller_name) if item.seller_name else "an external seller (sellerType EXTERNAL)"
        note = f"sold by {who}, a marketplace seller: no local store price"
    elif other is not None:
        note = f"the page's {wanted} line is for store {other}, not {store_id}"
    elif ship_only:
        note = "only shipping is offered: no local store price"
    elif for_store and not seller_verified:
        note = (
            f"{wanted} line for store {store_id}, but the page names no seller: the displayed price is not "
            "accepted as Walmart's"
        )
    elif for_store:
        note = f"{wanted} at store {store_id} (the item's fulfillment line)" + (
            "; out of stock there now" if out_of_stock else ""
        )
    elif from_store:
        note = (
            f"no {wanted} line; another local line for store {store_id}: {list(lines)} (the store's product; "
            f"its displayed price is not shown as the {wanted} price)"
        )
    elif out_of_stock:
        note = (
            f"out of stock, and no fulfillment line for store {store_id}: the page alone shows neither the "
            "store's assortment nor its price"
        )
    elif lines:
        note = f"no line for store {store_id}: {list(lines)}"
    else:
        note = "the page states no fulfillment for this item"
    return LocalOffer(
        lines,
        for_store,
        from_store,
        other,
        walmart_seller,
        marketplace,
        ship_only,
        out_of_stock,
        note,
        seller_verified,
    )


def displayed(item: WalmartItem) -> dict[str, Any]:
    """The item as the page's data states it (kept with the observation)."""
    d = asdict(item)
    d["fulfillment"] = [list(x) for x in d["fulfillment"]]
    d["badges"] = [list(x) for x in d["badges"]]
    return d


def evidence(
    item: WalmartItem,
    *,
    fetch_id: str,
    observed_at: str,
    store_id: str,
    modality: str,
    page_verified: bool,
) -> tuple[ProductEvidence, LocalOffer, dict[str, Any]]:
    """The record inputs of one item, its local-offer decision, and what the supporting log keeps."""
    display, price_flags = price_display(item)
    offer = local_offer(item, store_id, modality)
    flags: list[RecordFlag] = list(price_flags)
    if offer.out_of_stock:
        flags.append(RecordFlag.OUT_OF_STOCK)
    size_ev = size_from_title(item.name)
    size = size_ev.value
    # A product sold by weight whose title states no size: the weight its price is for, as displayed.
    per_weight = "" if size else price_for_weight(item)
    size = size or per_weight
    approx = approx_weight(item)
    deals, other_badges = deal_texts(item)

    def src(ref: str, source: str = SOURCE, transform: str | None = None) -> FieldSource:
        return FieldSource(source, f"{item.path}.{ref}", fetch_id, None, observed_at, transform)

    def read(at: ValueSource, then: str = "") -> FieldSource:
        """The exact path a displayed value was read from, what it is and each change made to it."""
        what = f"value of the price line {at.selector}" if at.selector else "displayed text"
        steps = [x for x in (at.transform if at.transform != AS_GIVEN else "", then) if x]
        return src(at.path, transform="; ".join([what, *steps]) if steps else f"{what}, kept as given")

    # The price fields name the path their value was actually read from (release 1.3.1): the price lines
    # of the current listing layout or the older display fields; an empty field names none.
    prices = {
        "regular_price": (
            display.regular_price,
            item.was_price_source if display.original_text else item.price_source,
        ),
        "sale_price": (display.sale_price, item.price_source),
    }
    provenance = {
        "product_title": src("name"),
        "weight": (
            read(item.price_condition_source, "the weight after the '/', kept as given")
            if per_weight and item.price_condition_source is not None
            else src(f"name ({size_ev.outcome})", "walmart_title")
        ),
        **{k: read(at, PRICE_READ) for k, (value, at) in prices.items() if value and at is not None},
        "image_url": src("imageInfo.thumbnailUrl"),
        "url": src("canonicalUrl"),
        **(
            {"ppm": read(item.unit_price_source)} if item.unit_price_string and item.unit_price_source else {}
        ),
        **({"upc": src("upc")} if item.upc else {}),
        "_identity": src(f"usItemId={item.item_id}"),
        "_store_check": src("fulfillmentSummary"),
    }
    check = SourceCheck(
        response={
            "kind": "walmart_next_data",
            "fetch_id": fetch_id,
            "path": item.path,
            "observed_at": observed_at,
        },
        store=store_id,
        modality=modality,
        price_location=store_id if (offer.for_store or offer.from_store) else offer.other_store,
        fulfillment=tuple(dict.fromkeys(k for k, sid in offer.lines if sid == store_id)),
        stock_level=item.availability,
        unit_price_text=(item.unit_price_string,) if item.unit_price_string else (),
        size=size,
        sold_by=item.sales_unit,
    )
    ev = ProductEvidence(
        upc=item.upc or None,
        url=item.url,
        title=item.name,
        size_text=size,
        price=display,
        offers=tuple(offers(item)),
        image_url=item.image_url if item.image_url.startswith(("http://", "https://")) else "",
        ppm_text=item.unit_price_string,
        brand=item.brand or None,
        is_ship_only=offer.ship_only,
        is_marketplace=offer.marketplace,
        source_key=f"{KEY_PREFIX}{item.item_id}",
        location_attested=page_verified and offer.accepted,
        provenance=provenance,
        flags=tuple(dict.fromkeys(flags)),
        source_check=check,
        approx_weight_text=approx["text"] if approx else "",
        approx_weight_source=approx,
    )
    log = {
        "item_id": item.item_id,
        "product_id": item.product_id,
        "json_path": item.path,
        "position": item.position,
        "seller": {
            "name": item.seller_name,
            "id": item.seller_id,
            "type": item.seller_type,
            "walmart": offer.walmart_seller,
        },
        "fulfillment_lines": [list(x) for x in offer.lines],
        "fulfillment_texts": list(item.fulfillment_texts),
        "local_offer": {
            "accepted": offer.accepted,
            "store_line": offer.store_line,
            "pickup_line": offer.for_store,
            "pickup_price": offer.pickup_price,
            "note": offer.note,
        },
        "availability": {"value": item.availability, "display": item.availability_display},
        "deal_texts": deals,
        "other_badges": other_badges,
        # Structured promotion data the page carries without displayed wording: logged, never exported.
        "promotion_data": list(item.promo_structured),
        "price_strings": {
            "current": item.price_string,
            "was": item.was_price_string,
            "range": item.price_range,
            "savings": item.savings_text,
            "codes": list(item.price_codes),
            "data_value": item.price_value,
        },
        "weight_source": "price_condition" if per_weight else "title" if size else None,
        "size": {"value": size, "outcome": size_ev.outcome, "candidates": list(size_ev.candidates)},
        # The exact approximate- or estimated-weight wording and where it was read (the product is excluded).
        "approx_weight": approx,
        "variant_count": item.variant_count,
        "sales_unit": item.sales_unit,
        # Release 1.3.1: whether the final cost depends on the weight and what in the data states it, and
        # Walmart's own wording next to the price ("each (est.)"), exactly as given, with its path.
        "weight_priced": {"value": item.weight_priced, "by": list(item.weight_priced_by)},
        "price_condition": (
            {"text": item.price_condition, "path": f"{item.path}.{item.price_condition_source.path}"}
            if item.price_condition and item.price_condition_source is not None
            else None
        ),
        "sponsored": item.sponsored,
    }
    return ev, offer, log


def explain_missing(
    built: BuiltRecord, item: WalmartItem, offer: LocalOffer, store_logo_note: str
) -> BuiltRecord:
    """Walmart's own reasons for empty fields (the shared reasons describe Mariano's cards)."""
    missing = dict(built.missing)
    if "upc" in missing:
        missing["upc"] = (
            "the listing page's data states no UPC for this item (Walmart shows UPCs on product pages: the "
            "outcome of reading this product's own page is in upc_detail); Walmart's item ID is kept as the "
            "internal identity only"
        )
    if "weight" in missing:
        size = size_from_title(item.name)
        if size.outcome == "ambiguous":
            missing["weight"] = (
                "the title holds several separate size expressions "
                f"({'; '.join(size.candidates)}): none is chosen"
            )
        elif size.outcome == "dimension_only":
            missing["weight"] = (
                f"the title's only measures are dimensions ({'; '.join(size.candidates)}), not a package size"
            )
        else:
            missing["weight"] = "the listing shows no size field and the title states no size"
    if "ppm" in missing:
        missing["ppm"] = "the listing shows no price per measure for this product"
    if "regular_price" in missing:
        if offer.marketplace or offer.ship_only:
            missing["regular_price"] = offer.note
        elif item.price_range:
            missing["regular_price"] = (
                f"the listing shows a price range for several options ({item.price_range!r})"
            )
        elif "hidePriceForSOI" in item.price_codes:
            missing["regular_price"] = "the listing hides the price until the item is in the cart"
        else:
            missing["regular_price"] = "the listing shows no price for this item"
    if "image_url" in missing:
        missing["image_url"] = "the item's data has no http(s) picture address"
    if "store_logo" in missing:
        missing["store_logo"] = store_logo_note
    if "sub_category" in missing:
        missing["sub_category"] = "the client's CSV row is itself the listing page (no subcategory)"
    return replace(built, missing=missing)


_UNIT_ANYWHERE = re.compile(rf"\d+(?:\.\d+)?\s*{_UNIT}\b", re.I)


def missing_kinds(built: BuiltRecord, item: WalmartItem, offer: LocalOffer) -> dict[str, str]:
    """For each empty field: ``rule`` (always empty), ``context_failed`` (the value is not the store's
    local offer), ``extraction_ambiguous`` (the title holds several size expressions), ``extraction_failed``
    (the page shows it but it was not read), or ``source_absent`` (the page does not show it)."""
    out: dict[str, str] = {}
    not_local = offer.marketplace or offer.ship_only or bool(offer.other_store)
    size = size_from_title(item.name)
    for name in built.missing:
        if name in ("gupc", "unit_price"):
            out[name] = "rule"
        elif name in ("regular_price", "sale_price") and not_local:
            out[name] = "context_failed"
        elif name == "weight" and size.outcome == "ambiguous":
            out[name] = "extraction_ambiguous"
        elif (
            name == "weight"
            and not size.found
            and size.outcome != "dimension_only"
            and _UNIT_ANYWHERE.search(item.name)
        ):
            out[name] = "extraction_failed"  # a quantity with a unit the rules did not read
        else:
            out[name] = "source_absent"
    return out
