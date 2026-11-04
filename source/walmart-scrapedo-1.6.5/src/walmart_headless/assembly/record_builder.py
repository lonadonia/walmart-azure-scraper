"""Assemble the 22-field record from displayed observations (brief §5.9, §6.2, §6.4)."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from decimal import Decimal
from enum import StrEnum
from typing import Any

from walmart_headless.assembly.exclusions import (
    approx_weight_match,
    exclusion_reasons,
    is_plu_code,
    size_slot_is_unit_price,
)
from walmart_headless.assembly.offers import (
    DealFields,
    OfferKind,
    OfferObservation,
    derive_deal_fields,
    states_bundle_price,
)
from walmart_headless.assembly.prices import PriceDisplay, PriceDisplayKind
from walmart_headless.assembly.private_label import PrivateLabelDetector
from walmart_headless.core.findings import RecordFlag
from walmart_headless.core.schema import (
    ALWAYS_EMPTY,
    POLICY_EMPTY,
    POLICY_EMPTY_REASON,
    build_record,
    format_violations,
    shape_violations,
)
from walmart_headless.core.settings import RecordSettings
from walmart_headless.core.text import collapse_ws

# Text the size slot sometimes shows that is not a size: the name of a product picture's view (the
# retailer's own size field holds "Front" for some products, live 2026-10-20) or a control's label.
_PICTURE_VIEWS = frozenset(
    {"front", "back", "left", "right", "top", "bottom", "side", "angle", "detail", "nutrition",
     "ingredients", "label", "image", "photo", "picture", "default", "main", "hero", "thumbnail"}
)  # fmt: skip
_CONTROL_LABEL = re.compile(
    r"^(?:sign in(?: to (?:add|clip))?|add(?: to (?:cart|list))?|view (?:offer|details)"
    r"|see (?:details|options|more)|shop (?:all )?items?|select|\d+ more (?:sizes?|options?|flavors?))$",
    re.I,
)


def size_text_problem(size_text: str, title: str = "") -> str:
    """Why the text in the size slot is not a size ("" when it can be one)."""
    text = collapse_ws(size_text)
    if not text:
        return ""
    if text.casefold() in _PICTURE_VIEWS:
        return f"the size slot shows {text!r}, the name of a product picture's view, not a size"
    if _CONTROL_LABEL.match(text):
        return f"the size slot shows {text!r}, a control's label, not a size"
    if title and text.casefold() == collapse_ws(title).casefold():
        return "the size slot repeats the product name"
    return ""


class RecordStatus(StrEnum):
    VALID = "valid"
    EXPORTED_NOT_VALID = "exported_not_valid"
    EXCLUDED = "excluded"
    QUARANTINED = "quarantined"


@dataclass(frozen=True)
class StoreFields:
    zipcode: str
    store_name: str
    store_location: str
    store_logo: str


@dataclass(frozen=True)
class FieldSource:
    source: str  # dom_card | dom_pdp | dom_header | json_products | json_coupons | state | config
    ref: str  # selector or JSON path
    fetch_id: str | None = None
    response_sha256: str | None = None
    observed_at: str | None = None
    # What the value read at ``ref`` is and each change made to it on the way to the field (release 1.3.1:
    # the price fields); recorded only when given.
    transform: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "selector_or_path": self.ref,
            "fetch_id": self.fetch_id,
            "response_sha256": self.response_sha256,
            "observed_at": self.observed_at,
        } | ({"transform": self.transform} if self.transform is not None else {})


@dataclass(frozen=True)
class SourceCheck:
    """What the site's own product response says about one product at the configured store.

    Used to verify the store and fulfillment of the displayed values and to explain missing ones; it
    never fills a displayed field. ``response`` is ``None`` when no product response was captured."""

    response: dict[str, Any] | None = None  # kind, fetch_id, sha256, observed_at of the response
    store: str = ""  # the configured store's location ID
    modality: str = ""  # the configured fulfillment
    price_location: str | None = None  # the store the response's price is for (None: no price stated)
    fulfillment: tuple[str, ...] = ()  # fulfillment types the response offers the product for
    stock_level: str = ""  # stock level at the configured store, as stated
    unit_price_text: tuple[str, ...] = ()  # the site's own unit-price text ("$0.29/fl oz"), if any
    size: str = ""  # the response's customer-facing size
    sold_by: str = ""  # "<sellBy>/<orderBy>", e.g. "Unit/Unit", "Weight/Unit"

    @property
    def location_ok(self) -> bool | None:
        return None if not self.price_location else self.price_location == self.store

    @property
    def modality_ok(self) -> bool | None:
        return None if not self.fulfillment else self.modality.upper() in self.fulfillment

    def as_dict(self) -> dict[str, Any]:
        if self.response is None:
            return {
                "result": "N/A",
                "note": "no product response for it was captured before its card was recorded",
            }
        failed = self.location_ok is False or self.modality_ok is False
        return {
            "result": "FAIL" if failed else "PASS",
            "response": self.response,
            "price_location": self.price_location,
            "location_ok": self.location_ok,
            "fulfillment": list(self.fulfillment),
            "modality_ok": self.modality_ok,
            "stock_level": self.stock_level,
            "unit_price_text": list(self.unit_price_text),
            "size": self.size,
            "sold_by": self.sold_by,
        }


@dataclass(frozen=True)
class ProductEvidence:
    """Displayed values for one product, already chosen by precedence PDP > card > drawer."""

    upc: str | None
    url: str
    title: str
    size_text: str
    price: PriceDisplay
    offers: tuple[OfferObservation, ...]
    image_url: str
    ppm_text: str = ""  # PPM exactly as displayed, "" if not displayed
    pdp_size_text: str = ""  # size from the PDP when the card's size slot shows a unit price
    brand: str | None = None
    is_ship_only: bool = False
    # The offer is a marketplace seller's, not the retailer's own local offer (Walmart): no local price.
    is_marketplace: bool = False
    # The product's identity when the retailer shows no UPC (Walmart item id, "wm:123"): used to keep
    # products apart and never exported as ``upc``.
    source_key: str | None = None
    location_attested: bool = True
    provenance: dict[str, FieldSource] = field(default_factory=dict)
    flags: tuple[RecordFlag, ...] = ()
    source_check: SourceCheck | None = None  # the site's product response for this product, if read
    offer_notes: tuple[str, ...] = ()  # offers the details listed but the record leaves out, and why
    # Approximate- or estimated-weight wording the product displays (its title, a source size field, or
    # since release 1.4.0 an estimate stated next to its price), even when no size reached ``weight``: the
    # product is excluded (shared requirements §5). ``approx_weight_source`` traces it: the field, its path,
    # the exact text and the whole value it was read in.
    approx_weight_text: str = ""
    approx_weight_source: Mapping[str, str] | None = None


@dataclass(frozen=True)
class CategoryAssignment:
    category: str
    sub_category: str


@dataclass(frozen=True)
class BuiltRecord:
    upc: str | None
    record: dict[str, str]
    status: RecordStatus
    reasons: tuple[RecordFlag, ...]
    flags: tuple[RecordFlag, ...]
    deals: DealFields
    provenance: dict[str, dict[str, Any]]
    missing: dict[str, str] = field(default_factory=dict)  # empty field -> why it is empty
    source_check: dict[str, Any] = field(default_factory=dict)

    @property
    def exported(self) -> bool:
        return self.status in (RecordStatus.VALID, RecordStatus.EXPORTED_NOT_VALID)


def _check_coupon_price(deals: DealFields, price: PriceDisplay) -> DealFields:
    """A coupon's headline price ("$4.99 Kroger Seedless Grapes") is a final price only below the price the
    card shows; otherwise it cannot be what the product costs with the coupon, and no price is set."""
    shelf = price.sale_price or price.regular_price
    if not deals.digital_deals_price or not shelf or RecordFlag.PER_WEIGHT_DEAL_PRICE in deals.flags:
        return deals
    chosen = next(
        (
            c
            for c in deals.classified
            if c.kind is OfferKind.DIGITAL and c.explicit_price == deals.digital_deals_price
        ),
        None,
    )
    if chosen is None or states_bundle_price(chosen.offer.text):
        return deals
    if Decimal(deals.digital_deals_price) < Decimal(shelf):
        return deals
    return replace(deals, digital_deals_price="", flags=(*deals.flags, RecordFlag.DEAL_PRICE_NOT_BELOW_PRICE))


def _offer_texts(deals: DealFields, kinds: tuple[OfferKind, ...]) -> str:
    return "; ".join(repr(c.offer.text) for c in deals.classified if c.kind in kinds)


def missing_reasons(
    record: dict[str, str],
    *,
    evidence: ProductEvidence,
    size_problem: str,
    size_is_unit_price: bool,
    deals: DealFields,
    settings: RecordSettings,
) -> dict[str, str]:
    """Why each empty field of the record is empty, in the record's field order."""
    price, check = evidence.price, evidence.source_check
    stock = (
        f"; the site's product response states stock level {check.stock_level}"
        if check and check.stock_level
        else ""
    )
    volume_offers = [c for c in deals.classified if c.kind is OfferKind.VOLUME]
    digital_offers = [c for c in deals.classified if c.kind is OfferKind.DIGITAL]
    out: dict[str, str] = {}
    for name, value in record.items():
        if value:
            continue
        if name in ALWAYS_EMPTY:
            reason = "always empty (client rule)"
        elif name in POLICY_EMPTY:
            reason = POLICY_EMPTY_REASON
        elif name == "weight":
            if size_problem:
                reason = size_problem
            elif size_is_unit_price:
                reason = (
                    f"the size slot shows a price per unit ({evidence.size_text!r}); no size is displayed"
                )
            else:
                reason = "the card shows no size"
        elif name == "regular_price":
            if price.kind is PriceDisplayKind.NOT_DISPLAYED:
                reason = f"the card shows {price.placeholder_text!r} instead of a price{stock}"
            else:
                reason = f"the card shows no price{stock}"
        elif name == "sale_price":
            reason = "no sale price is displayed"
        elif name == "volume_deals_description":
            other = _offer_texts(deals, (OfferKind.OTHER_PROMO,))
            reason = "no multi-unit offer is displayed" + (
                f" (offer {other} is not a multi-unit offer)" if other else ""
            )
        elif name == "volume_deals_price":
            if not volume_offers:
                reason = "no multi-unit offer is displayed"
            elif RecordFlag.MULTIPLE_VOLUME_PRICES in deals.flags:
                reason = "several multi-unit offers state different prices"
            else:
                reason = (
                    "the offer text states no final price (" + _offer_texts(deals, (OfferKind.VOLUME,)) + ")"
                )
        elif name == "digital_deals_description":
            left_out = []
            if not settings.include_points_offers_in_deals and (
                p := _offer_texts(deals, (OfferKind.POINTS,))
            ):
                left_out.append(f"points offer {p} left out (include_points_offers_in_deals is off)")
            if not settings.include_cashback_in_digital and (c := _offer_texts(deals, (OfferKind.CASHBACK,))):
                left_out.append(f"cash-back offer {c} left out (include_cashback_in_digital is off)")
            reason = "no digital coupon is displayed" + (f"; {'; '.join(left_out)}" if left_out else "")
        elif name == "digital_deals_price":
            if not digital_offers:
                reason = "no digital coupon is displayed"
            elif RecordFlag.MULTIPLE_DIGITAL_PRICES in deals.flags:
                reason = "several coupons state different prices"
            elif RecordFlag.DEAL_PRICE_NOT_BELOW_PRICE in deals.flags:
                reason = "the coupon's price is not below the displayed price, so it is not a final price"
            else:
                reason = (
                    "the coupon states a discount or no final price ("
                    + _offer_texts(deals, (OfferKind.DIGITAL,))
                    + ")"
                )
        elif name == "ppm":
            if check is None:
                reason = "the card shows no price per measure (no product response was captured to compare)"
            elif check.unit_price_text:
                reason = "the card shows no price per measure, although the site's product response has one"
            else:
                reason = (
                    "the card shows no price per measure, and the site's product response has none either"
                )
        elif name == "image_url":
            reason = "the card's picture has no http(s) address"
        elif name == "store_logo":
            reason = "the page header shows no logo image"
        else:
            reason = "not displayed"
        out[name] = reason
    return out


def build_product_record(
    evidence: ProductEvidence,
    *,
    store: StoreFields,
    category: CategoryAssignment,
    crawl_date: str,
    settings: RecordSettings,
    detector: PrivateLabelDetector,
    configured_modality: str,
    store_provenance: dict[str, FieldSource] | None = None,
) -> BuiltRecord:
    flags: list[RecordFlag] = list(evidence.flags)
    price = evidence.price
    check = evidence.source_check

    # Weight: displayed size; for relative-price items the size slot holds "$0.69/lb" instead. Text that
    # is not a size ("Front", a picture's view name the retailer put in its size field) is left out.
    size_is_unit_price = size_slot_is_unit_price(evidence.size_text)
    weight = evidence.pdp_size_text if size_is_unit_price else evidence.size_text
    size_problem = size_text_problem(weight, evidence.title)
    if size_problem:
        weight = ""
        flags.append(RecordFlag.SIZE_TEXT_NOT_A_SIZE)

    # PPM: displayed only (DOM_ONLY). The relative-price size slot is itself a displayed $/unit.
    ppm = evidence.ppm_text
    if not ppm and size_is_unit_price:
        ppm = evidence.size_text
    if not ppm:
        flags.append(RecordFlag.PPM_NOT_DISPLAYED)
    elif (
        evidence.ppm_text and check is not None and check.unit_price_text and ppm not in check.unit_price_text
    ):
        flags.append(RecordFlag.PPM_DOM_JSON_MISMATCH)

    # The store and fulfillment of the displayed values, as the site's own product response states them.
    location_attested = evidence.location_attested
    if check is not None and check.location_ok is False:
        location_attested = False
    if check is not None and check.modality_ok is False:
        flags.append(RecordFlag.MODALITY_NOT_OFFERED)

    if price.kind is PriceDisplayKind.NOT_DISPLAYED or price.kind is PriceDisplayKind.MISSING:
        flags.append(RecordFlag.PRICE_NOT_DISPLAYED)
    if price.is_relative:
        flags.append(RecordFlag.RELATIVE_PRICE)
        flags.append(RecordFlag.SOLD_BY_WEIGHT)
    if is_plu_code(evidence.upc):
        flags.append(RecordFlag.PLU_CODE)

    deals = derive_deal_fields(evidence.offers, settings, configured_modality)
    deals = _check_coupon_price(deals, price)
    flags.extend(deals.flags)

    pl = detector.detect(title=evidence.title, upc=evidence.upc, brand=evidence.brand)
    flags.extend(pl.flags)

    record = build_record(
        {
            "zipcode": store.zipcode,
            "store_name": store.store_name,
            "store_location": store.store_location,
            "store_logo": store.store_logo,
            "store_brand": pl.value,
            "category": category.category,
            "sub_category": category.sub_category,
            "product_title": evidence.title,
            "weight": weight,
            "regular_price": price.regular_price,
            "sale_price": price.sale_price,
            # Release 1.6.0: never filled for Walmart (core/schema.DEAL_FIELDS); the classified offers stay in
            # ``deals`` and reach offers.json and the provenance, never the exported record.
            "volume_deals_description": "",
            "volume_deals_price": "",
            "digital_deals_description": "",
            "digital_deals_price": "",
            "image_url": evidence.image_url,
            "url": evidence.url,
            "upc": evidence.upc or "",
            "ppm": ppm,
            "crawl_date": crawl_date,
        }
    )

    problems = shape_violations(record) + format_violations(record)
    if problems:
        flags.append(RecordFlag.SCHEMA_INVALID)

    identity = evidence.upc or evidence.source_key
    reasons = exclusion_reasons(
        flags=flags,
        weight=weight,
        is_relative_price=price.is_relative,
        is_ship_only=evidence.is_ship_only,
        location_attested=location_attested,
        upc=identity,
        settings=settings,
        is_marketplace=evidence.is_marketplace,
        approx_text=evidence.approx_weight_text,
    )

    if reasons:
        status = RecordStatus.EXCLUDED
    elif (
        not all(record[k] for k in ("product_title", "url", "category"))
        or not identity
        or not (record["regular_price"] or record["sale_price"])
    ):
        status = RecordStatus.EXPORTED_NOT_VALID
    else:
        status = RecordStatus.VALID

    provenance = {k: v.as_dict() for k, v in {**(store_provenance or {}), **evidence.provenance}.items()}
    provenance["_store_brand_signals"] = {"signals": pl.signals}
    if problems:
        provenance["_schema_problems"] = {"problems": problems}
    if evidence.offer_notes:
        provenance["_offers_left_out"] = {"notes": list(evidence.offer_notes)}
    derived = {
        "volume_deals_description": deals.volume_deals_description,
        "volume_deals_price": deals.volume_deals_price,
        "digital_deals_description": deals.digital_deals_description,
        "digital_deals_price": deals.digital_deals_price,
    }
    if any(derived.values()):
        # What the 1.5.x rules would have exported from the displayed offers: evidence only (release 1.6.0).
        provenance["_deal_fields_not_exported"] = {"rule": POLICY_EMPTY_REASON, "derived": derived}
    # Every approximate-weight exclusion names the wording that qualifies it and where it was read.
    weight_wording = approx_weight_match(weight, settings)
    if evidence.approx_weight_source:
        provenance["_approx_weight"] = dict(evidence.approx_weight_source)
    elif evidence.approx_weight_text:
        provenance["_approx_weight"] = {"text": evidence.approx_weight_text}
    elif weight_wording:
        provenance["_approx_weight"] = {
            "field": "weight",
            "path": str(provenance.get("weight", {}).get("selector_or_path", "")),
            "text": weight_wording,
            "value": weight,
        }

    return BuiltRecord(
        upc=identity,
        record=record,
        status=status,
        reasons=tuple(reasons),
        flags=tuple(dict.fromkeys(flags)),
        deals=deals,
        provenance=provenance,
        missing=missing_reasons(
            record,
            evidence=evidence,
            size_problem=size_problem,
            size_is_unit_price=size_is_unit_price,
            deals=deals,
            settings=settings,
        ),
        source_check=check.as_dict() if check is not None else {},
    )
