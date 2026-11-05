"""Audit and finding codes (brief Appendix C) and shared enums."""

from __future__ import annotations

from enum import StrEnum


class DataMode(StrEnum):
    """Every run and everything derived from it is LIVE, FIXTURE or REPLAY. They are never mixed.

    REPLAY: the stored pages of an earlier LIVE run read again offline by the current code (``replay``),
    with their original observation times; corrected evidence about that run, never a fresh observation,
    never published, never contest evidence by itself."""

    LIVE = "LIVE"
    FIXTURE = "FIXTURE"
    REPLAY = "REPLAY"


class Severity(StrEnum):
    INFO = "INFO"
    WARN = "WARN"
    FAIL = "FAIL"


class RecordFlag(StrEnum):
    APPROX_WEIGHT = "APPROX_WEIGHT"
    RELATIVE_PRICE = "RELATIVE_PRICE"
    SOLD_BY_WEIGHT = "SOLD_BY_WEIGHT"
    PRICE_NOT_DISPLAYED = "PRICE_NOT_DISPLAYED"
    PLU_CODE = "PLU_CODE"
    SHIP_ONLY = "SHIP_ONLY"
    LOCATION_UNATTESTED = "LOCATION_UNATTESTED"
    NO_UPC = "NO_UPC"
    UPC_SOURCE_MISMATCH = "UPC_SOURCE_MISMATCH"
    PRICE_DOM_JSON_MISMATCH = "PRICE_DOM_JSON_MISMATCH"
    PPM_NOT_DISPLAYED = "PPM_NOT_DISPLAYED"
    PPM_DOM_JSON_MISMATCH = "PPM_DOM_JSON_MISMATCH"
    PRIVATE_LABEL_SIGNAL_CONFLICT = "PRIVATE_LABEL_SIGNAL_CONFLICT"
    MULTIPLE_DIGITAL_PRICES = "MULTIPLE_DIGITAL_PRICES"
    MULTIPLE_VOLUME_PRICES = "MULTIPLE_VOLUME_PRICES"
    OTHER_PROMO_UNCLASSIFIED = "OTHER_PROMO_UNCLASSIFIED"
    CASHBACK_OFFER_EXCLUDED = "CASHBACK_OFFER_EXCLUDED"
    POINTS_OFFER_EXCLUDED = "POINTS_OFFER_EXCLUDED"
    MODALITY_RESTRICTED_OFFER = "MODALITY_RESTRICTED_OFFER"
    PER_WEIGHT_DEAL_PRICE = "PER_WEIGHT_DEAL_PRICE"
    OFFER_TAG_UNOBSERVED = "OFFER_TAG_UNOBSERVED"
    SPONSORED_ONLY_MEMBERSHIP = "SPONSORED_ONLY_MEMBERSHIP"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    IMAGE_NOT_OBSERVABLE = "IMAGE_NOT_OBSERVABLE"
    SIZE_TEXT_NOT_A_SIZE = "SIZE_TEXT_NOT_A_SIZE"  # e.g. a picture's view name ("Front") in the size slot
    MODALITY_NOT_OFFERED = "MODALITY_NOT_OFFERED"  # the product response omits the configured fulfillment
    DEAL_PRICE_NOT_BELOW_PRICE = "DEAL_PRICE_NOT_BELOW_PRICE"  # a coupon headline price >= the shown price
    MARKETPLACE_OFFER = "MARKETPLACE_OFFER"  # a marketplace seller's offer: no local store price
    OUT_OF_STOCK = "OUT_OF_STOCK"  # the source says the product is unavailable now (kept, never deleted)
    PRICE_RANGE = "PRICE_RANGE"  # only a price range for several options is displayed
    # A product of the store's assortment (a local offer observed earlier) shown this time without a local
    # offer (shipping only, a marketplace seller, no line for the store): kept with its identity and size,
    # its prices empty; a shipping or marketplace price is never used.
    NO_LOCAL_OFFER = "NO_LOCAL_OFFER"
    # The page shows the product as the store's (a Delivery line for the store) but with no line of the
    # configured fulfillment (Pickup): kept with its identity and size, its prices empty.
    NO_PICKUP_OFFER = "NO_PICKUP_OFFER"
    # Shown without a local offer and never observed with one at this store: not claimed as the store's.
    ASSORTMENT_UNRESOLVED = "ASSORTMENT_UNRESOLVED"
    # Not observed by this run: an earlier run's verified local observation kept unchanged (its own date).
    CARRIED_FORWARD = "CARRIED_FORWARD"
    # The same UPC as another product of the run (each genuine product is exported once).
    DUPLICATE_UPC = "DUPLICATE_UPC"
    # A line of the configured fulfillment for the store, on a page that names no seller: no price is taken.
    SELLER_UNVERIFIED = "SELLER_UNVERIFIED"
    # The product's own page states sizes that disagree, or one that disagrees with its title (all are kept).
    SIZE_CONFLICT = "SIZE_CONFLICT"


class RunCode(StrEnum):
    LOCATION_MISMATCH = "LOCATION_MISMATCH"
    CHALLENGE_DETECTED = "CHALLENGE_DETECTED"
    RATE_LIMITED = "RATE_LIMITED"
    ABNORMAL_LATENCY = "ABNORMAL_LATENCY"
    SITE_CONTRACT_DRIFT = "SITE_CONTRACT_DRIFT"
    ZERO_YIELD_SUSPECT = "ZERO_YIELD_SUSPECT"
    LOW_YIELD = "LOW_YIELD"
    RETAINED_MASKS_YIELD = "RETAINED_MASKS_YIELD"
    NODE_INCOMPLETE = "NODE_INCOMPLETE"
    CANARY_MISSING = "CANARY_MISSING"
    INTEGRITY_ERROR = "INTEGRITY_ERROR"
    DETAIL_PAUSED = "DETAIL_PAUSED"


# Flags that keep a record out of the canonical export (brief §6.3), with the setting that gates it.
EXCLUSION_FLAGS: frozenset[RecordFlag] = frozenset(
    {
        RecordFlag.APPROX_WEIGHT,
        RecordFlag.RELATIVE_PRICE,
        RecordFlag.SHIP_ONLY,
        RecordFlag.LOCATION_UNATTESTED,
        RecordFlag.NO_UPC,
        RecordFlag.SCHEMA_INVALID,
        RecordFlag.MARKETPLACE_OFFER,
    }
)
