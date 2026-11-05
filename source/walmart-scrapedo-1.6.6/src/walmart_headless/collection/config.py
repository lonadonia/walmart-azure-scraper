"""What one run of a store collects: categories, subcategories, limits, the timezone of its days, and its
store-local schedule (read by the schedule guard of ``run --scheduled``; Azure starts the job).

Empty limits mean no limit: production collects the store's full configured scope. Small test limits are
set in the configuration file or on the command line for one run; they are recorded with the run and a run
they bound is labelled a pilot, never a complete catalogue.
"""

from __future__ import annotations

import re
from datetime import date, time
from typing import Any, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
WEEKDAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Limits(_Model):
    """Empty means no limit. Products are unique verified products of the store (a product seen again in
    the same run, or again on the same day, is not counted twice). Credits are the provider's credits as
    it charged them; the reserve is checked against the account balance."""

    max_products_per_run: int | None = Field(None, ge=1)
    max_products_per_day: int | None = Field(None, ge=1)
    # Total active collection time of the run, over all its executions (segments).
    max_run_minutes: int | None = Field(None, ge=1, le=14 * 24 * 60)
    # One execution (segment) of the run; reaching it pauses the run resumably and the next execution
    # (``resume``, or the schedule's continuation) goes on from the checkpoints. Not a scope limit.
    max_segment_minutes: int | None = Field(None, ge=1, le=7 * 24 * 60)
    max_credits_per_run: int | None = Field(None, ge=5)
    max_credits_per_day: int | None = Field(None, ge=5)
    min_credit_reserve: int = Field(0, ge=0)
    # Bounded (pilot) runs: verified products per client category, result pages read per listing, and
    # subcategory listings read per category page. A run stopped by these is labelled incomplete.
    max_products_per_category: int | None = Field(None, ge=1)
    max_pages_per_listing: int | None = Field(None, ge=1)
    max_subcategories_per_category: int | None = Field(None, ge=1)

    def bounded(self) -> bool:
        """True when a limit narrows the scope (the run is then a pilot, never a complete catalogue)."""
        return any(
            v is not None
            for v in (
                self.max_products_per_run,
                self.max_products_per_category,
                self.max_pages_per_listing,
                self.max_subcategories_per_category,
            )
        )


def parse_hhmm(value: str) -> time:
    h, m = value.split(":")
    return time(int(h), int(m))


class Schedule(_Model):
    """Runs start at ``start_time`` (store-local) on the chosen weekdays, between the optional start and end
    dates. A scheduled run may collect only inside the daily window (``window_start``, default the start
    time, to ``window_end``, default the end of the day); at the window's end it stops resumably. A window
    only paces a run: it never narrows what the run collects."""

    enabled: bool = False
    weekdays: list[int] = Field(default_factory=list)  # 0 = Monday … 6 = Sunday
    start_time: str = "09:00"
    window_start: str | None = None
    window_end: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    # A scheduled run not finished by its first execution (its segment limit, the window's end, an
    # interruption) is continued by later executions, inside the daily window of each day.
    continue_unfinished: bool = True
    # What an occurrence does when the store's scheduled run of an earlier occurrence is still unfinished:
    # ``continue`` (release 1.3.1) goes on with that run and starts none (``OCCURRENCE_DEFERRED``), so a run
    # longer than the interval between two starts is never cut short; ``supersede`` (release 1.3.0) closes it
    # as partial (never published) and starts the new run.
    on_overlap: Literal["continue", "supersede"] = "continue"

    @field_validator("weekdays")
    @classmethod
    def _weekdays(cls, v: list[int]) -> list[int]:
        if any(d < 0 or d > 6 for d in v):
            raise ValueError("weekdays are 0 (Monday) to 6 (Sunday)")
        return sorted(set(v))

    @field_validator("start_time", "window_start", "window_end")
    @classmethod
    def _clock(cls, v: str | None) -> str | None:
        if v is not None and not _HHMM.match(v):
            raise ValueError("times are HH:MM (24-hour)")
        return v

    @model_validator(mode="after")
    def _consistent(self) -> Schedule:
        if self.enabled and not self.weekdays:
            raise ValueError("choose at least one weekday to enable the schedule")
        start = parse_hhmm(self.window_start or self.start_time)
        if parse_hhmm(self.start_time) < start:
            raise ValueError("the start time must be inside the daily window")
        if self.window_end is not None and parse_hhmm(self.window_end) <= parse_hhmm(self.start_time):
            raise ValueError("the daily window must end after the start time")
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("the schedule end date is before its start date")
        return self


class DetailConfig(_Model):
    """Product detail pages, read for the identifiers (UPC/GTIN) and sizes that Walmart's result pages do not
    show.

    Every product the run exports (a local product, or a verified local product without a current local
    offer) whose result page states no UPC or no size gets its own page read once in the run; the UPC that
    page states for the same item is kept exactly as written, and its statements about size are read apart
    (``sites/walmart/pack_size.py``). ``endpoint`` ``general`` reads it through Scrape.do's general API
    (1 credit; a UPC is a product attribute, not a store's), ``store`` through the store endpoint (10
    credits). What an earlier read of the item's own page established may be reused for ``reuse_days``
    (recorded as reused, with its run, time and source revision; 0 = never). After ``pause_after_failures``
    consecutive refused or failed detail requests, detail reading pauses for the run (each product then says
    so); the listings go on. ``max_per_run`` is a pilot's budget (``run --pilot-detail-pages N``); production
    leaves it unset, and a run with a budget is never published as the store's dataset."""

    enabled: bool = True
    endpoint: Literal["general", "store"] = "general"
    # None: every exported product missing a UPC or a size. 0 only loads a run recorded before release 1.5.0.
    max_per_run: int | None = Field(None, ge=0)
    reuse_days: int = Field(30, ge=0)
    pause_after_failures: int = Field(3, ge=1)


class OxylabsOptions(_Model):
    """The store parameters sent with every store-scoped Oxylabs Web API request (``/v1/scrape/walmart``):
    the store is ``stores.yaml``'s location id; ``fulfillment_type`` the configured fulfillment; a
    ``delivery_zip`` only when set. Recorded with each page and never taken as proof of the store."""

    fulfillment_type: Literal["pickup", "delivery", "shipping"] = "pickup"
    delivery_zip: str | None = Field(None, pattern=r"^\d{5}$")


class ParallelConfig(_Model):
    """Workers of one execution (one process, one store): each leases its own tasks from the run's queue,
    opens its own provider session and checks the store on its own pages. ``max_in_flight`` provider
    requests at once in the process, starts ``min_interval_s`` apart. One worker is the default."""

    workers: int = Field(1, ge=1, le=8)
    max_in_flight: int = Field(2, ge=1, le=8)
    min_interval_s: float = Field(0.5, ge=0.0, le=60.0)


class FollowSeed(_Model):
    """An item an earlier report named (a sponsored-only product, a tile-only variant sibling) to be read
    again by this run's follow-up, before the run's own candidates. Only its id, link and the listing it was
    seen on are taken from the report; everything else is observed again."""

    kind: Literal["sponsored", "variant"]
    item_id: str = Field(pattern=r"^\d{1,20}$")
    url: str = Field(pattern=r"^https://www\.walmart\.com/ip/")
    listing_id: str = Field(pattern=r"^\d+(?:_\d+)*$")
    named_by: str = ""  # a variant sibling: the tile's own item id
    source: str = ""  # where the item was named (run id, report)


class FollowUpConfig(_Model):
    """After every listing, the product pages of (a) products the run saw only in sponsored placements and
    (b) the variant siblings that result tiles name without showing them, read in the store's context:
    a product is added only when its own page identifies it, places it in the listing's category and shows
    the store's local offer or assortment. ``max_pages`` is a pilot budget of pages per kind and run (None,
    production: every one): a run with a budget is a pilot, and the candidates it leaves are recorded as not
    attempted and stay in the store's follow-up queue (collection/follow_queue.py) for the next run.
    ``seeds`` are read first."""

    sponsored: bool = True
    variants: bool = True
    max_pages: int | None = Field(None, ge=0)
    seeds: list[FollowSeed] = Field(default_factory=list)


class CollectionConfig(_Model):
    categories: list[int] = Field(default_factory=list)  # client CSV rows; empty = every category
    subcategories: dict[str, list[str]] = Field(default_factory=dict)  # row -> listing URLs; absent = all
    timezone: str = "America/Chicago"
    limits: Limits = Field(default_factory=Limits)
    detail: DetailConfig = Field(default_factory=DetailConfig)
    # Earlier name of ``detail.max_per_run`` (``--pdp-sample N``, removed in release 1.5.0); kept only so that
    # earlier run snapshots load. The configuration file refuses it.
    pdp_sample: int | None = Field(None, ge=0)
    schedule: Schedule = Field(default_factory=Schedule)
    # The page provider of the run (one per run: a change of provider is another run).
    provider: Literal["scrapedo", "oxylabs"] = "scrapedo"
    oxylabs: OxylabsOptions = Field(default_factory=OxylabsOptions)
    parallel: ParallelConfig = Field(default_factory=ParallelConfig)
    follow_up: FollowUpConfig = Field(default_factory=FollowUpConfig)

    def pilot_budgets(self) -> dict[str, Any]:
        """Every setting that narrows what a run collects, by name: its scope limits, and the product pages
        its follow-ups and detail reads may use (a budget, or turned off). A run with any is a pilot, never
        a complete catalogue; production leaves them all unset. Before release 1.3.1 the follow-up and
        detail page budgets narrowed a run without making it a pilot."""
        named: dict[str, Any] = {
            "limits.max_products_per_run": self.limits.max_products_per_run,
            "limits.max_products_per_category": self.limits.max_products_per_category,
            "limits.max_pages_per_listing": self.limits.max_pages_per_listing,
            "limits.max_subcategories_per_category": self.limits.max_subcategories_per_category,
            "follow_up.max_pages": self.follow_up.max_pages,
            "follow_up.sponsored": None if self.follow_up.sponsored else "off",
            "follow_up.variants": None if self.follow_up.variants else "off",
            "detail.max_per_run": self.detail.max_per_run if self.detail.enabled else None,
            "detail.enabled": None if self.detail.enabled else "off",
        }
        return {k: v for k, v in named.items() if v is not None}

    def bounded(self) -> bool:
        """True when a setting narrows what the run collects (:meth:`pilot_budgets`)."""
        return bool(self.pilot_budgets())

    @model_validator(mode="after")
    def _pdp_sample(self) -> CollectionConfig:
        if self.pdp_sample is not None:
            self.detail = self.detail.model_copy(update={"max_per_run": self.pdp_sample})
        return self

    @field_validator("timezone")
    @classmethod
    def _tz(cls, v: str) -> str:
        try:
            ZoneInfo(v)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError(f"unknown timezone {v!r}") from None
        return v

    @field_validator("categories")
    @classmethod
    def _rows(cls, v: list[int]) -> list[int]:
        return sorted(set(v))

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)
