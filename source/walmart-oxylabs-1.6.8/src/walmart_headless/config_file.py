"""The collector's configuration file (``config/collector.yaml``) and what it points to.

Everything an operator used to set in a console is here, outside the source code: the stores file, the
client's category CSV, per-store collection settings (categories, limits, the store-local schedule), the
automated canary, the historical-observation rule and publication. Secrets never go in it: the provider key
and the database password come from the environment (Azure secret references in production).

Relative paths are resolved against the configuration file's own directory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from walmart_headless.collection.config import CollectionConfig
from walmart_headless.core.settings import (
    PrivateLabelConfig,
    Settings,
    StoreConfig,
    StoresFile,
    load_private_label,
    load_settings,
    load_stores,
)


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CanaryConfig(_Model):
    """The automated checks of a run's first recorded page (they replace a person's review)."""

    enabled: bool = True
    min_valid_records: int = Field(1, ge=0)
    min_valid_ratio: float = Field(0.05, ge=0, le=1)  # of the page's recorded products
    required_fields: tuple[str, ...] = (
        "zipcode",
        "store_name",
        "store_location",
        "category",
        "product_title",
        "regular_price",
        "image_url",
        "url",
        "crawl_date",
    )
    # Every valid record of the page equal to the page's own item data, read independently.
    source_check: bool = True


class HistoricalConfig(_Model):
    """Retention of the store's verified products (``collection/retention.py``): a product a run does not
    observe keeps its last verified local observation, carried forward unchanged with its own crawl date and
    its age in the supporting log. A product shown only with a shipping or marketplace offer, or without a
    line for the store, keeps its identity with empty prices (never that other price).

    The client requires verified store products to be kept indefinitely, even when unavailable: there is no
    age limit. ``max_age_days`` (from earlier configurations) must stay empty; a value is refused rather than
    silently dropping verified products."""

    enabled: bool = True
    max_age_days: int | None = Field(None, ge=0)

    @model_validator(mode="after")
    def _indefinite(self) -> HistoricalConfig:
        if self.max_age_days is not None:
            raise ValueError(
                "historical.max_age_days must be empty: verified store products are kept indefinitely "
                "(their age is reported with each carried-forward record)"
            )
        return self


class PublishConfig(_Model):
    """A complete, validated, non-pilot run is published to ``published/<store>/`` (the last successful
    complete dataset). Runs with warnings are published only with ``accept_warnings`` and a reason."""

    auto: bool = True
    accept_warnings_reason: str | None = None


class EditionConfig(_Model):
    """The edition this configuration belongs to (release 1.4.0). One collector serves both providers; an
    edition is that collector built for one of them (``editions.py``): ``providers`` names the providers its
    runs may use. A run, a resumed run or a provider command naming another is refused before any request:
    a run is never sent to another provider. The core (``name: core``) names both."""

    name: str = Field("core", min_length=1)
    providers: tuple[Literal["scrapedo", "oxylabs"], ...] = ("scrapedo", "oxylabs")

    @model_validator(mode="after")
    def _some(self) -> EditionConfig:
        if not self.providers or len(set(self.providers)) != len(self.providers):
            raise ValueError("edition.providers must name each provider of the edition once")
        return self


class StoreCollection(CollectionConfig):
    """One store's collection: what to collect, limits, the store-local schedule, and how a scheduled
    execution treats an unfinished run of the same occurrence."""

    max_auto_resumes: int = Field(3, ge=0)
    # A scheduled execution may start at most this long after the store-local start time (the Azure cron
    # fires at both standard-time and daylight-time UTC hours; the other one is outside this tolerance).
    start_tolerance_minutes: int = Field(45, ge=5, le=240)


class CollectorConfig(_Model):
    retailer: str = "walmart"
    edition: EditionConfig = Field(default_factory=EditionConfig)
    settings_file: str = "settings.yaml"
    stores_file: str = "stores.yaml"
    categories_csv: str = "Walmart_Category_URLs.csv"
    private_label_file: str = "walmart_private_label_brands.yaml"
    collections: dict[str, StoreCollection] = Field(default_factory=dict)
    canary: CanaryConfig = Field(default_factory=CanaryConfig)
    historical: HistoricalConfig = Field(default_factory=HistoricalConfig)
    publish: PublishConfig = Field(default_factory=PublishConfig)

    @model_validator(mode="after")
    def _walmart(self) -> CollectorConfig:
        if self.retailer != "walmart":
            raise ValueError("this collector collects Walmart only (retailer: walmart)")
        for key, coll in self.collections.items():
            if coll.pdp_sample is not None or coll.detail.max_per_run == 0:
                raise ValueError(
                    f"collections.{key}: a setting of zero product detail pages was removed in release "
                    "1.5.0. Production reads every exported product missing a UPC or a size; a pilot says so "
                    "on the command line (run --pilot-detail-pages N, or --pilot-no-detail)"
                )
            if coll.provider not in self.edition.providers:
                raise ValueError(
                    f"collections.{key}.provider is {coll.provider}: the {self.edition.name} edition runs "
                    f"{', '.join(self.edition.providers)} only"
                )
        return self


class LoadedConfig:
    """The configuration file and the files it names, loaded and checked."""

    def __init__(self, path: Path):
        self.path = path.resolve()
        self.base = self.path.parent
        raw: Any = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        self.collector = CollectorConfig.model_validate(raw)
        self.settings: Settings = load_settings(self._p(self.collector.settings_file))
        self.stores: StoresFile = load_stores(self._p(self.collector.stores_file))
        self.private_label: PrivateLabelConfig = load_private_label(
            self._p(self.collector.private_label_file)
        )
        self.categories_csv = self._p(self.collector.categories_csv)
        if not self.categories_csv.is_file():
            raise FileNotFoundError(f"categories CSV not found: {self.categories_csv}")
        unknown = sorted(set(self.collector.collections) - {s.key for s in self.stores.stores})
        if unknown:
            raise ValueError(f"collections for stores not in {self.collector.stores_file}: {unknown}")

    def _p(self, name: str) -> Path:
        p = Path(name)
        return p if p.is_absolute() else self.base / p

    def store(self, key: str) -> StoreConfig:
        for s in self.stores.stores:
            if s.key == key:
                if not s.enabled:
                    raise ValueError(f"store {key} is disabled in {self.collector.stores_file}")
                return s
        raise KeyError(f"unknown store {key!r}; configured: {[s.key for s in self.stores.stores]}")

    def collection(self, key: str) -> StoreCollection:
        """The store's collection settings (defaults: every category, no limit, schedule off)."""
        return self.collector.collections.get(key) or StoreCollection()
