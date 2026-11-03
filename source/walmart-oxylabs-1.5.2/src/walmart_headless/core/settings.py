"""Typed runtime settings (record rules, retries, gates, storage) and the store definitions. Every run
snapshots the fully resolved settings."""

from __future__ import annotations

import re
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PpmSourcePolicy(StrEnum):
    DOM_ONLY = "DOM_ONLY"
    DOM_THEN_SITE_FORMATTED_JSON = "DOM_THEN_SITE_FORMATTED_JSON"  # only after client approval (Q-05)


class OtherPromoTarget(StrEnum):
    NONE = "NONE"
    VOLUME_DESCRIPTION = "VOLUME_DESCRIPTION"


class DealDescriptionFormat(StrEnum):
    TAG_TEXT_EXPIRY = "TAG_TEXT_EXPIRY"
    TEXT_ONLY = "TEXT_ONLY"


class PrimaryCategoryPolicy(StrEnum):
    CSV_ORDER_COUPONS_LAST = "CSV_ORDER_COUPONS_LAST"
    CSV_ORDER = "CSV_ORDER"


class SubCategoryFormat(StrEnum):
    LEAF = "LEAF"
    PATH = "PATH"


class Modality(StrEnum):
    IN_STORE = "IN_STORE"
    PICKUP = "PICKUP"
    DELIVERY = "DELIVERY"
    SHIP = "SHIP"


class RetrySettings(_Strict):
    max_attempts_per_task: int = 3
    backoff_base_s: float = 10
    backoff_max_s: float = 300
    pause_on_429_s: float = 600  # when a 429 comes without a Retry-After header
    max_retry_after_s: float = 1800  # a site asking for a longer pause stops the category instead


class CircuitBreakerSettings(_Strict):
    consecutive_failures_to_fail_category: int = 5
    challenge_pages_to_abort_run: int = 1


class CoverageSettings(_Strict):
    # A listing is complete only when its distinct organic products reach its reported total: there is no
    # tolerance threshold (a shortfall stays an open difference until source evidence explains it).
    node_min_coverage_ratio: float = Field(1.0, ge=1, le=1)
    # Read by no check (there is no acceptance ratio). Releases up to 1.3.0 recorded 0.90 with each run's
    # settings; kept so those settings load.
    row_fail_below_ratio: float | None = Field(None, gt=0, le=1)
    allow_paid_only_membership: bool = False
    # A listing larger than the site's result window is read through the child categories its own
    # "Departments" facet names, as deep as those facets go: null (the default) sets no depth limit. A
    # number is an explicit cap for a bounded run (release 1.4.0; up to 1.3.1 the default capped at 2): a
    # listing it leaves unpartitioned says so and stays incomplete.
    partition_large_listings: bool = True
    partition_max_depth: int | None = Field(None, ge=0)


class YieldSettings(_Strict):
    warn_drop_vs_last_good: float = 0.30
    fail_drop_vs_last_good: float = 0.50
    # Retained products (verified by earlier runs, not observed by this one, carried forward) are published
    # with a run's fresh products but are never its yield: a category, or the whole run, whose published
    # products are more than this share retained is flagged (release 1.4.0), so that what earlier runs saw
    # cannot mask a run that observed almost nothing.
    warn_retained_share: float = Field(0.30, ge=0, le=1)
    fail_retained_share: float = Field(0.50, ge=0, le=1)


class AttestationSettings(_Strict):
    periodic_every_navigations: int = 25
    # Phase 0 deliverable: the modality `source` value the site reports after an explicit store
    # selection. Empty means "not yet recorded", and A3 fails until it is filled in.
    trusted_modality_sources: tuple[str, ...] = ()
    require_is_trusted_source: bool = True


class RecordSettings(_Strict):
    # A product sold or charged by weight (a relative price) is kept and flagged: only approximate or
    # estimated-weight wording excludes a product ("each (est.)" next to its price, "approx 1.5 lb" in its
    # size wording). Release 1.4.0 changed the default: up to 1.3.1 every weight-priced product was excluded.
    exclude_relative_price_items: bool = False
    exclude_ship_only: bool = True
    approx_weight_pattern: str = r"(?i)\b(approx\.?|approximately|about|avg\.?|average|est\.?|estimated)\b|~"
    store_brand_positive_value: str = "yes"
    store_brand_negative_value: Literal["no"] = "no"
    include_cashback_in_digital: bool = False
    include_points_offers_in_deals: bool = False
    other_promo_target: OtherPromoTarget = OtherPromoTarget.NONE
    deal_description_format: DealDescriptionFormat = DealDescriptionFormat.TAG_TEXT_EXPIRY
    deal_description_separator: str = " | "
    ppm_source_policy: PpmSourcePolicy = PpmSourcePolicy.DOM_ONLY
    primary_category_policy: PrimaryCategoryPolicy = PrimaryCategoryPolicy.CSV_ORDER_COUPONS_LAST
    sub_category_format: SubCategoryFormat = SubCategoryFormat.LEAF
    sub_category_path_separator: str = " > "
    crawl_date: Literal["STORE_LOCAL_DATE"] = "STORE_LOCAL_DATE"
    fail_on_price_mismatch: bool = True

    @field_validator("approx_weight_pattern")
    @classmethod
    def _compiles(cls, v: str) -> str:
        re.compile(v)
        return v


class ContestSettings(_Strict):
    enabled: bool = True
    min_valid_records: int = 500
    min_categories: int = 3


class StorageSettings(_Strict):
    backend: Literal["local", "azure_blob"] = "local"
    local_root: str = "./data"
    azure_account_url: str | None = None
    azure_container: str | None = None


class GateThresholds(_Strict):
    # Read by no check since release 1.3.1 (coverage has no ratio threshold): kept so the settings
    # recorded with earlier runs still load.
    coverage_warn_below: float | None = None
    coverage_fail_below: float | None = None
    price_completeness_warn_below: float = 0.98
    reconciliation_warn_above: float = 0.005
    reconciliation_fail_above: float = 0.02
    canary_missing_is_fail: bool = False


class PublicationSettings(_Strict):
    # A target that may receive runs whose pages did not come from the network (tests, the operator's
    # fault-injection harness): never true where the client's dataset is published.
    test_target: bool = False


class Settings(_Strict):
    retries: RetrySettings = RetrySettings()
    circuit_breaker: CircuitBreakerSettings = CircuitBreakerSettings()
    coverage: CoverageSettings = CoverageSettings()
    yield_: YieldSettings = Field(YieldSettings(), alias="yield")
    attestation: AttestationSettings = AttestationSettings()
    records: RecordSettings = RecordSettings()
    gates: GateThresholds = GateThresholds()
    contest: ContestSettings = ContestSettings()
    storage: StorageSettings = StorageSettings()
    publication: PublicationSettings = PublicationSettings()

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    def snapshot(self) -> dict[str, Any]:
        """JSON-serialisable copy stored on every run (``runs.config_snapshot``)."""
        return self.model_dump(mode="json", by_alias=True)


class StoreExpectation(_Strict):
    display_name: str
    postal_code: str
    address_line1: str | None = None


class StoreConfig(_Strict):
    """One Walmart store (``location_id`` = its store number) and the fulfillment its prices are collected
    for. The same physical store collected for two fulfillment modes is two entries (two keys). The labels
    here are expectations: the run checks them against Walmart's own store page and page data."""

    key: str
    retailer: Literal["walmart"] = "walmart"
    enabled: bool = True
    location_id: str
    division_number: str = ""
    store_number: str = ""
    expected: StoreExpectation
    modality: Modality = Modality.IN_STORE
    timezone: str = "America/Chicago"
    store_page_url: str | None = None  # the store's own page on the banner site (store selection)
    is_contest_store: bool = False
    notes: str | None = None

    @model_validator(mode="after")
    def _walmart_store(self) -> StoreConfig:
        if self.modality not in (Modality.IN_STORE, Modality.PICKUP):
            raise ValueError("store price context must be IN_STORE or PICKUP")
        if not re.fullmatch(r"\d{1,5}", self.location_id):
            raise ValueError("a Walmart store's location_id is its store number (1-5 digits)")
        if self.division_number:
            raise ValueError("Walmart stores have no division_number")
        if self.store_number and self.store_number != self.location_id:
            raise ValueError("a Walmart store's store_number equals its location_id")
        if not re.fullmatch(r"\d{5}", self.expected.postal_code[:5]):
            raise ValueError("expected.postal_code must start with the store's 5-digit ZIP code")
        return self


class StoresFile(_Strict):
    stores: tuple[StoreConfig, ...]

    @model_validator(mode="after")
    def _unique_keys(self) -> StoresFile:
        keys = [s.key for s in self.stores]
        if len(keys) != len(set(keys)):
            raise ValueError("store keys must be unique")
        return self


class PrivateLabelConfig(_Strict):
    brands: tuple[str, ...]
    upc_prefix_signals: tuple[str, ...] = ()


def _load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_settings(path: Path | None) -> Settings:
    if path is None or not path.exists():
        return Settings()
    return Settings.model_validate(_load_yaml(path))


def load_stores(path: Path) -> StoresFile:
    return StoresFile.model_validate(_load_yaml(path))


def load_private_label(path: Path) -> PrivateLabelConfig:
    return PrivateLabelConfig.model_validate(_load_yaml(path))
