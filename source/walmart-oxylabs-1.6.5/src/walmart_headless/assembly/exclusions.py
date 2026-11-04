"""Record exclusions (brief §6.3). An excluded record is not exported but is counted per reason."""

from __future__ import annotations

import re
from collections.abc import Iterable

from walmart_headless.core.findings import RecordFlag
from walmart_headless.core.settings import RecordSettings

_PLU = re.compile(r"^0{7,8}\d{4,5}$")  # 13-digit form of a 4/5-digit PLU, e.g. 0000000004011
_PER_UNIT_SIZE = re.compile(r"^\$\d+(?:\.\d{1,2})?\s*/\s*[a-z ]+$", re.I)


def is_plu_code(upc: str | None) -> bool:
    return bool(upc and _PLU.match(upc))


def size_slot_is_unit_price(size_text: str) -> bool:
    """For relative-price items the size slot shows "$0.69/lb" instead of a size."""
    return bool(_PER_UNIT_SIZE.match(size_text.strip()))


def approx_weight_match(weight: str, settings: RecordSettings) -> str:
    """The approximate-weight wording in the ``weight`` field (``records.approx_weight_pattern``), or ""."""
    m = re.search(settings.approx_weight_pattern, weight) if weight else None
    return m.group(0) if m else ""


def is_approx_weight(weight: str, settings: RecordSettings) -> bool:
    return bool(approx_weight_match(weight, settings))


def exclusion_reasons(
    *,
    flags: Iterable[RecordFlag],
    weight: str,
    is_relative_price: bool,
    is_ship_only: bool,
    location_attested: bool,
    upc: str | None,
    settings: RecordSettings,
    is_marketplace: bool = False,
    approx_text: str = "",
) -> list[RecordFlag]:
    """All exclusion reasons that apply, in a stable order. Empty means the record is exported.
    ``upc`` is the product's identity: its UPC, or for a retailer that often shows none its source key.
    ``approx_text``: approximate- or estimated-weight wording the product displays (its size wording, or an
    estimate stated next to its price), which excludes it even when no size reached ``weight``. A relative
    price (sold or charged by weight) excludes it only while ``records.exclude_relative_price_items`` is
    true (false since release 1.4.0: being sold by weight, or a "/lb" PPM, keeps no product out)."""
    present = set(flags)
    reasons: list[RecordFlag] = []
    if not upc:
        reasons.append(RecordFlag.NO_UPC)
    if not location_attested:
        reasons.append(RecordFlag.LOCATION_UNATTESTED)
    if is_marketplace:
        reasons.append(RecordFlag.MARKETPLACE_OFFER)
    if is_approx_weight(weight, settings) or approx_text:
        reasons.append(RecordFlag.APPROX_WEIGHT)
    if is_relative_price and settings.exclude_relative_price_items:
        reasons.append(RecordFlag.RELATIVE_PRICE)
    if is_ship_only and settings.exclude_ship_only:
        reasons.append(RecordFlag.SHIP_ONLY)
    if RecordFlag.SCHEMA_INVALID in present:
        reasons.append(RecordFlag.SCHEMA_INVALID)
    return reasons
