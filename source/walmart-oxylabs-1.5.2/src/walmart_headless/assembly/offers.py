"""Deterministic promotion classifier (brief §7, docx §7).

Only displayed text is used. A deal price is set only when the displayed text states the final price
explicitly; nothing is ever computed from "% off", "$ off", BOGO or cash-back wording.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field, replace
from enum import StrEnum

from walmart_headless.core.findings import RecordFlag
from walmart_headless.core.settings import DealDescriptionFormat, OtherPromoTarget, RecordSettings
from walmart_headless.core.text import collapse_ws, normalize_amount_str


class OfferSource(StrEnum):
    ZONE = "zone"  # card savings zone (one offer)
    DRAWER_OFFER = "drawer_offer"  # drawer savings-side-offer ("Sale", "Shop Deal")
    DRAWER_COUPON = "drawer_coupon"  # drawer savings-side-coupon ("Sign In To Clip")
    PDP = "pdp"
    COUPON_CARD = "coupon_card"  # coupon catalogue / carousel card
    JSON_COUPONS = "json_coupons"
    JSON_PRODUCTS = "json_products"


# Display order between sources: zone first, then drawer order (§7.2 step 5).
_SOURCE_RANK = {
    OfferSource.ZONE: 0,
    OfferSource.DRAWER_OFFER: 1,
    OfferSource.DRAWER_COUPON: 1,
    OfferSource.PDP: 2,
    OfferSource.COUPON_CARD: 3,
    OfferSource.JSON_COUPONS: 4,
    OfferSource.JSON_PRODUCTS: 5,
}


class OfferKind(StrEnum):
    CASHBACK = "cashback"
    POINTS = "points"
    DIGITAL = "digital"
    VOLUME = "volume"
    OTHER_PROMO = "other_promo"


@dataclass(frozen=True)
class OfferObservation:
    source: OfferSource
    text: str  # full displayed offer sentence (never a split-price join)
    display_order: int = 0
    tag: str = ""  # displayed tag; "" means the tag was not observed
    clip_checkbox: bool | None = None  # zone only: a coupon checkbox is present
    ctas: tuple[str, ...] = ()
    expiry_text: str = ""
    coupon_type: str | None = None  # coupons JSON: STANDARD | CASH_BACK
    modalities: tuple[str, ...] | None = None  # structured modality list, when known
    extra_tags: tuple[str, ...] = ()  # other displayed tags, e.g. "Pickup & Delivery Only"
    coupon_id: str | None = None
    sources: tuple[OfferSource, ...] = ()  # filled when observations are merged
    # The offer's details as its "View Offer" dialog shows them: quantity, limits, eligibility, dates.
    terms: str = ""
    quantity: int | None = None  # units the offer requires (a coupon's requirementQuantity), if known

    @property
    def sort_key(self) -> tuple[int, int]:
        return _SOURCE_RANK[self.source], self.display_order


@dataclass(frozen=True)
class ClassifiedOffer:
    offer: OfferObservation
    requires_clip: bool
    kind: OfferKind
    explicit_price: str  # "" unless the text states the final price
    per_weight_price: bool
    restricted_to: frozenset[str] | None  # modalities named by a restriction, if any
    flags: tuple[RecordFlag, ...] = ()


_CLIP_TAGS = {"coupon", "weekly digital deal", "digital coupon", "digital deal"}
_NO_CLIP_TAGS = {"sale"}
_CLIP_CTA = re.compile(r"\bclip\b", re.I)
_NO_CLIP_CTA = re.compile(r"^shop deal$", re.I)

# Rewards paid later are never an immediate price reduction (shared requirements §7): cash back, Walmart
# Cash, mail-in or manufacturer rebates.
_CASHBACK = re.compile(r"\bcash\s*back\b|\bwalmart\s+cash\b|\brebate\b", re.I)
_POINTS = re.compile(
    r"\b\d+\s*x\s+(?:fuel\s+)?points\b|\bearn\b[^.]*\bpoints\b|\bfuel\s+points\b|\bpoints\s+event\b"
    r"|\bbonus\s+points\b",
    re.I,
)
# A purchase of two units or more. One unit is no multi-unit condition: "Buy 1 Save $1" is a discount on a
# single pack, while "Buy 1, Get 1 Free" stays a volume offer because it asks for a second unit.
_SEVERAL = r"(?:[2-9]|[1-9]\d+)"
_SEVERAL_WORD = rf"(?:{_SEVERAL}|two|three|four|five|six|seven|eight|nine|ten)"
_VOLUME = [
    re.compile(rf"\b{_SEVERAL}\s*(?:for|/)\s*\$", re.I),
    re.compile(rf"\bbuy\s+{_SEVERAL_WORD}\b", re.I),
    re.compile(r"\bbuy\s+(?:1|one)\b[^.;]*?\bget\b", re.I),
    re.compile(rf"\bwhen you buy\s+{_SEVERAL}\b", re.I),
    re.compile(r"\bmix\s*(?:or|&|and)\s*match\b", re.I),
    re.compile(rf"\bmust buy\s+{_SEVERAL}\b", re.I),
    re.compile(r"\bget\s+\d+\s+free\b", re.I),
    re.compile(r"\bBOGO\b", re.I),
]

_PRICE_NFOR = re.compile(r"^(\d+)\s*(?:for|/)\s*\$(\d+(?:\.\d{2})?)\b", re.I)
_PRICE_EACH_WHEN_BUY = re.compile(r"^\$(\d+\.\d{2})\s*(?:each|ea)?\b.*\bwhen you buy\b", re.I)
_PRICE_MUST_BUY = re.compile(r"must buy\s*\d+\s*:?\s*\$(\d+\.\d{2})\s*each", re.I)
_PRICE_HEADLINE = re.compile(r"^\$(\d+\.\d{2})(\s*/?\s*lb)?\s+(?!off\b)(?!cash back\b)\S", re.I)
_PRICE_EACH_DIGITAL = re.compile(r"\$(\d+\.\d{2})\s*each with digital coupon", re.I)

_RESTRICTIONS: list[tuple[re.Pattern[str], frozenset[str]]] = [
    (re.compile(r"\bpickup\s*(?:or|&|and)\s*delivery\s+only\b", re.I), frozenset({"PICKUP", "DELIVERY"})),
    (re.compile(r"\bdelivery\s*(?:or|&|and)\s*pickup\s+only\b", re.I), frozenset({"PICKUP", "DELIVERY"})),
    (re.compile(r"\bdelivery\s+only\b", re.I), frozenset({"DELIVERY"})),
    (re.compile(r"\bpickup\s+only\b", re.I), frozenset({"PICKUP"})),
    (re.compile(r"\bin[-\s]?store\s+only\b", re.I), frozenset({"IN_STORE"})),
    (re.compile(r"\bship(?:ping)?\s+only\b", re.I), frozenset({"SHIP"})),
]


def requires_clip(offer: OfferObservation) -> bool:
    tag = offer.tag.strip().lower()
    # A merged offer counts as a coupon if any sighting showed it as one (e.g. zone + drawer coupon).
    seen_in = {offer.source, *offer.sources}
    # Explicit negatives (drawer "Sale" offer, "Shop Deal", zone without checkbox) and unknown
    # signals both mean "no clipping shown".
    return (
        bool(seen_in & {OfferSource.DRAWER_COUPON, OfferSource.COUPON_CARD})
        or (OfferSource.ZONE in seen_in and offer.clip_checkbox is True)
        or tag in _CLIP_TAGS
        or any(_CLIP_CTA.search(c) for c in offer.ctas)
        or (offer.coupon_type or "").upper() == "STANDARD"
    )


def states_bundle_price(text: str) -> bool:
    """The text prices several units together ("2 For $5.00", "4/$10 when you buy 4 or more")."""
    return bool(_PRICE_NFOR.search(collapse_ws(text)))


def is_volume_text(text: str) -> bool:
    """The text states a multi-unit condition ("2 For $5.00", "Buy 1, Get 1 Free", "when you buy 5")."""
    return any(rx.search(text) for rx in _VOLUME)


def classify_kind(offer: OfferObservation, clip: bool) -> OfferKind:
    tag = offer.tag.strip().lower()
    if tag == "cash back" or (offer.coupon_type or "").upper() == "CASH_BACK" or _CASHBACK.search(offer.text):
        return OfferKind.CASHBACK
    if tag == "points event" or _POINTS.search(offer.text):
        return OfferKind.POINTS
    if clip:
        return OfferKind.DIGITAL
    if is_volume_text(offer.text):
        return OfferKind.VOLUME
    return OfferKind.OTHER_PROMO


def extract_explicit_price(text: str, kind: OfferKind, quantity: int | None = None) -> tuple[str, bool]:
    """Return ``(price, per_weight)``; price is ``""`` unless the text states the final price.

    A coupon headline price ("$4.99 Kroger Seedless Grapes") is the price of one unit; when the coupon
    requires several units (``quantity`` > 1) the headline does not say what one unit costs, so no price."""
    if kind not in (OfferKind.VOLUME, OfferKind.DIGITAL):
        return "", False
    t = collapse_ws(text)
    m = _PRICE_NFOR.search(t)
    if m:
        return normalize_amount_str(m.group(2)), False
    m = _PRICE_EACH_WHEN_BUY.search(t)
    if m:
        return normalize_amount_str(m.group(1)), False
    m = _PRICE_MUST_BUY.search(t)
    if m:
        return normalize_amount_str(m.group(1)), False
    if kind is OfferKind.DIGITAL:
        m = _PRICE_HEADLINE.search(t)
        if m and (quantity is None or quantity <= 1):
            return normalize_amount_str(m.group(1)), bool(m.group(2))
        m = _PRICE_EACH_DIGITAL.search(t)
        if m:
            return normalize_amount_str(m.group(1)), False
    return "", False


def modality_restriction(offer: OfferObservation) -> frozenset[str] | None:
    if offer.modalities:
        return frozenset(m.upper() for m in offer.modalities)
    for candidate in (offer.text, *offer.extra_tags):
        for rx, allowed in _RESTRICTIONS:
            if rx.search(candidate):
                return allowed
    return None


def classify(offer: OfferObservation, configured_modality: str) -> ClassifiedOffer:
    clip = requires_clip(offer)
    kind = classify_kind(offer, clip)
    price, per_weight = extract_explicit_price(offer.text, kind, offer.quantity)
    restricted = modality_restriction(offer)
    flags: list[RecordFlag] = []
    if restricted is not None and configured_modality.upper() not in restricted:
        flags.append(RecordFlag.MODALITY_RESTRICTED_OFFER)
    if per_weight and price:
        flags.append(RecordFlag.PER_WEIGHT_DEAL_PRICE)
    if kind is OfferKind.DIGITAL and not offer.tag:
        flags.append(RecordFlag.OFFER_TAG_UNOBSERVED)
    return ClassifiedOffer(offer, clip, kind, price, per_weight, restricted, tuple(flags))


def text_key(text: str) -> str:
    return collapse_ws(text).casefold().rstrip(" .")


def merge_observations(offers: Iterable[OfferObservation]) -> list[OfferObservation]:
    """Merge the same offer seen in several places (zone + drawer, card + JSON).

    Offers are matched by their displayed text. The merged offer keeps the earliest display position
    and fills tag, expiry, CTAs and IDs from whichever observation displayed them.
    """
    ordered = sorted(offers, key=lambda o: o.sort_key)
    merged: dict[str, OfferObservation] = {}
    for o in ordered:
        key = text_key(o.text)
        if not key:
            continue
        if key not in merged:
            merged[key] = replace(o, sources=(o.source,))
            continue
        cur = merged[key]
        merged[key] = replace(
            cur,
            tag=cur.tag or o.tag,
            clip_checkbox=cur.clip_checkbox if cur.clip_checkbox is not None else o.clip_checkbox,
            ctas=cur.ctas + tuple(c for c in o.ctas if c not in cur.ctas),
            expiry_text=cur.expiry_text or o.expiry_text,
            coupon_type=cur.coupon_type or o.coupon_type,
            modalities=cur.modalities or o.modalities,
            extra_tags=cur.extra_tags + tuple(t for t in o.extra_tags if t not in cur.extra_tags),
            coupon_id=cur.coupon_id or o.coupon_id,
            sources=(*cur.sources, o.source),
            terms=cur.terms or o.terms,
            quantity=cur.quantity if cur.quantity is not None else o.quantity,
        )
    return list(merged.values())


def format_description(offer: OfferObservation, fmt: DealDescriptionFormat) -> str:
    """``TAG_TEXT_EXPIRY``: "Coupon: $4.99 Kroger Seedless Grapes — <terms> (Exp. 10/20/2026)"; the terms
    (quantity, limits, eligibility, dates) only when the offer's details were read."""
    text = collapse_ws(offer.text)
    if fmt is DealDescriptionFormat.TEXT_ONLY:
        return text
    out = f"{collapse_ws(offer.tag)}: {text}" if offer.tag else text
    terms = collapse_ws(offer.terms)
    if terms and text_key(terms) != text_key(text):
        out += f" — {terms}"
    if offer.expiry_text:
        out += f" ({collapse_ws(offer.expiry_text)})"
    return out


@dataclass(frozen=True)
class DealFields:
    volume_deals_description: str = ""
    volume_deals_price: str = ""
    digital_deals_description: str = ""
    digital_deals_price: str = ""
    flags: tuple[RecordFlag, ...] = ()
    classified: tuple[ClassifiedOffer, ...] = field(default_factory=tuple)


def _pick_price(
    offers: Sequence[ClassifiedOffer], multi_flag: RecordFlag, flags: list[RecordFlag]
) -> tuple[str, ClassifiedOffer | None]:
    priced = [o for o in offers if o.explicit_price]
    if len(priced) == 1:
        return priced[0].explicit_price, priced[0]
    if len(priced) > 1:
        flags.append(multi_flag)
    return "", None


def derive_deal_fields(
    observations: Iterable[OfferObservation], settings: RecordSettings, configured_modality: str
) -> DealFields:
    merged = merge_observations(observations)
    classified = [classify(o, configured_modality) for o in merged]
    flags: list[RecordFlag] = []
    volume: list[ClassifiedOffer] = []
    digital: list[ClassifiedOffer] = []
    volume_text_only: list[ClassifiedOffer] = []
    digital_text_only: list[ClassifiedOffer] = []

    for c in classified:
        if c.kind is OfferKind.CASHBACK:
            if settings.include_cashback_in_digital:
                digital_text_only.append(c)
            else:
                flags.append(RecordFlag.CASHBACK_OFFER_EXCLUDED)
            continue
        if c.kind is OfferKind.POINTS:
            if settings.include_points_offers_in_deals:
                digital_text_only.append(c)
            else:
                flags.append(RecordFlag.POINTS_OFFER_EXCLUDED)
            continue
        if c.kind is OfferKind.OTHER_PROMO:
            flags.append(RecordFlag.OTHER_PROMO_UNCLASSIFIED)
            if settings.other_promo_target is OtherPromoTarget.VOLUME_DESCRIPTION:
                volume_text_only.append(c)
            continue
        flags.extend(c.flags)
        (digital if c.kind is OfferKind.DIGITAL else volume).append(c)

    fmt = settings.deal_description_format
    sep = settings.deal_description_separator

    def describe(items: Sequence[ClassifiedOffer]) -> str:
        ordered = sorted(items, key=lambda c: c.offer.sort_key)
        return sep.join(format_description(c.offer, fmt) for c in ordered)

    volume_price, _ = _pick_price(volume, RecordFlag.MULTIPLE_VOLUME_PRICES, flags)
    digital_price, chosen = _pick_price(digital, RecordFlag.MULTIPLE_DIGITAL_PRICES, flags)
    if chosen is None or not chosen.per_weight_price:
        flags = [f for f in flags if f is not RecordFlag.PER_WEIGHT_DEAL_PRICE]

    return DealFields(
        volume_deals_description=describe([*volume, *volume_text_only]),
        volume_deals_price=volume_price,
        digital_deals_description=describe([*digital, *digital_text_only]),
        digital_deals_price=digital_price,
        flags=tuple(dict.fromkeys(flags)),
        classified=tuple(classified),
    )
