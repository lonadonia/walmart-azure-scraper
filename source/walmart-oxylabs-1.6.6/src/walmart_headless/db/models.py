"""PostgreSQL data model (brief §10). Migrations live in ``migrations/`` (Alembic).

IDs are ULIDs. Status-like columns are strings with CHECK constraints rather than PG enums, so new
states need only a migration that rewrites the constraint. ``mode`` (LIVE | FIXTURE) is stored on runs
and on every table derived from them so the two can never be blended.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from walmart_headless.core.ids import new_id

NAMING = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

RUN_STATUSES = (
    "queued",
    "preflight",
    "running",
    "interrupted",
    "validating",
    "validated",
    "rejected",
    "published",
    "cancelled",
)
TASK_STATES = ("pending", "leased", "running", "succeeded", "retry_wait", "failed", "blocked", "skipped")
TASK_KINDS = (
    "preflight",
    "attest",
    "census",
    "listing_node",
    "pdp",
    "coupons_catalogue",
    "coupon_items",
    "assemble",
    "validate",
    "export",
    "follow_up",
)
MODES = ("LIVE", "FIXTURE", "REPLAY")
FOLLOW_KINDS = ("sponsored", "variant", "detail")
FOLLOW_STATES = ("pending", "resolved")
DETAIL_STATUSES = ("extracted", "absent_in_source")
DETAIL_ORIGINS = ("fetched", "imported")
OCCURRENCE_STATES = ("due", "deferred", "running", "completed", "superseded")


def _in(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING)
    type_annotation_map: ClassVar[dict[Any, Any]] = {dict[str, Any]: JSONB, list[str]: ARRAY(Text)}


def _id() -> Mapped[str]:
    return mapped_column(String(26), primary_key=True, default=new_id)


def _created() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def _updated() -> Mapped[datetime]:
    return mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


def _mode() -> Mapped[str]:
    return mapped_column(String(8), nullable=False)


class Store(Base):
    __tablename__ = "stores"
    id: Mapped[str] = _id()
    key: Mapped[str] = mapped_column(String(64), unique=True)
    retailer: Mapped[str] = mapped_column(String(32))
    location_id: Mapped[str] = mapped_column(String(8))
    division_number: Mapped[str] = mapped_column(String(3))
    store_number: Mapped[str] = mapped_column(String(5))
    expected_display_name: Mapped[str] = mapped_column(Text)
    expected_postal_code: Mapped[str] = mapped_column(String(10))
    expected_address_line1: Mapped[str | None] = mapped_column(Text)
    modality: Mapped[str] = mapped_column(String(16))
    timezone: Mapped[str] = mapped_column(String(64))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_contest_store: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()
    __table_args__ = (CheckConstraint(_in("modality", ("IN_STORE", "PICKUP")), name="modality"),)


class CategorySource(Base):
    __tablename__ = "category_sources"
    id: Mapped[str] = _id()
    retailer: Mapped[str] = mapped_column(String(32), default="walmart", server_default=text("'walmart'"))
    csv_row_index: Mapped[int] = mapped_column(Integer)
    category_name: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    scope: Mapped[str] = mapped_column(Text)
    notes: Mapped[str] = mapped_column(Text, default="")
    kind: Mapped[str] = mapped_column(String(32))
    landing_slug: Mapped[str | None] = mapped_column(Text)
    taxonomy_id: Mapped[str | None] = mapped_column(String(10))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    csv_sha256: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()
    __table_args__ = (
        UniqueConstraint("retailer", "category_name", name="uq_category_sources_retailer_name"),
    )


class Run(Base):
    __tablename__ = "runs"
    id: Mapped[str] = _id()
    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id"))
    trigger: Mapped[str] = mapped_column(String(16))  # manual | schedule | test
    status: Mapped[str] = mapped_column(String(16), default="queued")
    mode: Mapped[str] = _mode()
    config_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB)
    site_version: Mapped[str | None] = mapped_column(String(64))
    parser_version: Mapped[str] = mapped_column(String(32))
    robots_sha256: Mapped[str | None] = mapped_column(String(64))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    counts: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    resumed_from_run_id: Mapped[str | None] = mapped_column(String(26))
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    pause_requested: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    # Live collection: why the run last stopped (a limit, the operator, the site, the provider) and the
    # operator's requests to the collector service (resume; stop collecting and finalize).
    stop_code: Mapped[str | None] = mapped_column(String(48))
    stop_detail: Mapped[str | None] = mapped_column(Text)
    resume_requested: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    finish_requested: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()
    __table_args__ = (
        CheckConstraint(_in("status", RUN_STATUSES), name="status"),
        CheckConstraint(_in("mode", MODES), name="mode"),
        Index("ix_runs_store_status", "store_id", "status"),
    )


class StoreAttestation(Base):
    __tablename__ = "store_attestations"
    id: Mapped[str] = _id()
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), index=True)
    mode: Mapped[str] = _mode()
    phase: Mapped[str] = mapped_column(String(16))
    observed_location_id: Mapped[str | None] = mapped_column(String(8))
    observed_name: Mapped[str | None] = mapped_column(Text)
    observed_postal_code: Mapped[str | None] = mapped_column(String(10))
    modality: Mapped[str | None] = mapped_column(String(16))
    modality_source: Mapped[str | None] = mapped_column(Text)
    is_trusted: Mapped[bool | None] = mapped_column(Boolean)
    laf_store_id: Mapped[str | None] = mapped_column(String(8))
    cms_scope: Mapped[str | None] = mapped_column(Text)
    result: Mapped[str] = mapped_column(String(8))
    checks: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    evidence_artifact_ids: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _created()
    __table_args__ = (
        CheckConstraint(_in("phase", ("preflight", "task_start", "periodic", "final")), name="phase"),
        CheckConstraint(_in("result", ("PASS", "FAIL")), name="result"),
    )


class RunLock(Base):
    __tablename__ = "run_locks"
    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id"), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"))
    holder: Mapped[str] = mapped_column(Text)
    heartbeat_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[str] = _id()
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"))
    kind: Mapped[str] = mapped_column(String(24))
    idem_key: Mapped[str] = mapped_column(Text)
    category_source_id: Mapped[str | None] = mapped_column(ForeignKey("category_sources.id"))
    taxonomy_id: Mapped[str | None] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(16), default="pending")
    priority: Mapped[int] = mapped_column(Integer, default=100)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    lease_owner: Mapped[str | None] = mapped_column(Text)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    not_before: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cursor: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()
    __table_args__ = (
        UniqueConstraint("run_id", "idem_key", name="uq_tasks_run_idem"),
        CheckConstraint(_in("state", TASK_STATES), name="state"),
        CheckConstraint(_in("kind", TASK_KINDS), name="kind"),
        Index("ix_tasks_run_state", "run_id", "state", "priority"),
    )


class Artifact(Base):
    __tablename__ = "artifacts"
    id: Mapped[str] = _id()
    run_id: Mapped[str | None] = mapped_column(ForeignKey("runs.id"), index=True)
    key: Mapped[str] = mapped_column(Text, unique=True)
    sha256: Mapped[str] = mapped_column(String(64))
    size: Mapped[int] = mapped_column(BigInteger)
    content_type: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = _created()


class PageFetch(Base):
    __tablename__ = "page_fetches"
    id: Mapped[str] = _id()
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), index=True)
    task_id: Mapped[str | None] = mapped_column(ForeignKey("tasks.id"))
    url: Mapped[str] = mapped_column(Text)
    purpose: Mapped[str] = mapped_column(String(32))
    http_status: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    challenge: Mapped[bool] = mapped_column(Boolean, default=False)
    dom_artifact_id: Mapped[str | None] = mapped_column(ForeignKey("artifacts.id"))
    screenshot_artifact_id: Mapped[str | None] = mapped_column(ForeignKey("artifacts.id"))


class CapturedResponse(Base):
    __tablename__ = "captured_responses"
    id: Mapped[str] = _id()
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), index=True)
    page_fetch_id: Mapped[str] = mapped_column(ForeignKey("page_fetches.id"), index=True)
    kind: Mapped[str] = mapped_column(String(32))
    url: Mapped[str] = mapped_column(Text)
    status: Mapped[int] = mapped_column(Integer)
    request_location_id: Mapped[str | None] = mapped_column(String(8))
    request_taxonomies: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    body_sha256: Mapped[str] = mapped_column(String(64))
    artifact_id: Mapped[str | None] = mapped_column(ForeignKey("artifacts.id"))
    schema_ok: Mapped[bool | None] = mapped_column(Boolean)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ProductObservation(Base):
    __tablename__ = "product_observations"
    id: Mapped[str] = _id()
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"))
    mode: Mapped[str] = _mode()
    upc: Mapped[str] = mapped_column(String(40))  # product identity key (see retailers.py)
    page_fetch_id: Mapped[str] = mapped_column(ForeignKey("page_fetches.id"))
    source: Mapped[str] = mapped_column(String(16))
    displayed: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    structured: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    flags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    parser_version: Mapped[str] = mapped_column(String(32))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("run_id", "upc", "page_fetch_id", "source", name="uq_product_observations_key"),
        CheckConstraint(
            _in("source", ("card", "pdp", "coupon_items", "sponsored_card", "tile_options")), name="source"
        ),
        Index("ix_product_observations_run_upc", "run_id", "upc"),
        Index("ix_product_observations_observed_at", "observed_at"),  # per-day product limits
    )


class OfferObservationRow(Base):
    __tablename__ = "offer_observations"
    id: Mapped[str] = _id()
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"))
    mode: Mapped[str] = _mode()
    upc: Mapped[str] = mapped_column(String(40))  # product identity key (see retailers.py)
    page_fetch_id: Mapped[str | None] = mapped_column(ForeignKey("page_fetches.id"))
    source: Mapped[str] = mapped_column(String(16))
    tag: Mapped[str] = mapped_column(Text, default="")
    headline: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    expiry_text: Mapped[str] = mapped_column(Text, default="")
    requires_clip: Mapped[bool] = mapped_column(Boolean)
    kind: Mapped[str] = mapped_column(String(16))
    explicit_price: Mapped[str] = mapped_column(String(16), default="")
    modalities: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    flags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    __table_args__ = (Index("ix_offer_observations_run_upc", "run_id", "upc"),)


class MembershipRow(Base):
    __tablename__ = "memberships"
    id: Mapped[str] = _id()
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"))
    mode: Mapped[str] = _mode()
    upc: Mapped[str] = mapped_column(String(40))  # product identity key (see retailers.py)
    category_source_id: Mapped[str] = mapped_column(ForeignKey("category_sources.id"))
    taxonomy_id: Mapped[str | None] = mapped_column(String(64))
    coupon_id: Mapped[str | None] = mapped_column(Text)
    page_offset: Mapped[int] = mapped_column(Integer)
    position: Mapped[int] = mapped_column(Integer)
    via: Mapped[str] = mapped_column(String(8))
    __table_args__ = (
        CheckConstraint(_in("via", ("organic", "paid", "curated", "coupon")), name="via"),
        Index(
            "uq_memberships_key",
            "run_id",
            "upc",
            "category_source_id",
            text("coalesce(taxonomy_id, '')"),
            text("coalesce(coupon_id, '')"),
            "page_offset",
            "via",  # one page may show a product both as a sponsored and as an organic placement
            unique=True,
        ),
    )


class RecordRow(Base):
    __tablename__ = "records"
    id: Mapped[str] = _id()
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"))
    mode: Mapped[str] = _mode()
    upc: Mapped[str] = mapped_column(String(40))  # product identity key (see retailers.py)
    record: Mapped[dict[str, Any]] = mapped_column(JSONB)
    record_sha256: Mapped[str] = mapped_column(String(64))
    primary_category_source_id: Mapped[str | None] = mapped_column(ForeignKey("category_sources.id"))
    status: Mapped[str] = mapped_column(String(24))
    reasons: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    flags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    # Why a record is what it is beyond its status: a kept earlier local observation (``historical``) and
    # its age, or one too old to keep. Never part of the 22-field product file.
    provenance: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    __table_args__ = (
        UniqueConstraint("run_id", "upc", name="uq_records_run_upc"),
        CheckConstraint(
            _in("status", ("valid", "exported_not_valid", "excluded", "quarantined", "historical")),
            name="status",
        ),
    )


class ValidationFinding(Base):
    __tablename__ = "validation_findings"
    id: Mapped[str] = _id()
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), index=True)
    scope: Mapped[str] = mapped_column(String(16))
    ref: Mapped[str | None] = mapped_column(Text)
    gate: Mapped[str] = mapped_column(String(8))
    severity: Mapped[str] = mapped_column(String(8))
    code: Mapped[str] = mapped_column(String(48))
    message: Mapped[str] = mapped_column(Text)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = _created()
    __table_args__ = (
        CheckConstraint(_in("severity", ("INFO", "WARN", "FAIL")), name="severity"),
        CheckConstraint(_in("scope", ("run", "category", "node", "record")), name="scope"),
    )


class ExportRow(Base):
    __tablename__ = "exports"
    id: Mapped[str] = _id()
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), index=True)
    mode: Mapped[str] = _mode()
    kind: Mapped[str] = mapped_column(String(32))
    artifact_id: Mapped[str] = mapped_column(ForeignKey("artifacts.id"))
    record_count: Mapped[int | None] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = _created()


class Publication(Base):
    __tablename__ = "publications"
    id: Mapped[str] = _id()
    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id"))
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), unique=True)
    mode: Mapped[str] = _mode()
    manifest_sha256: Mapped[str] = mapped_column(String(64))
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    published_by: Mapped[str] = mapped_column(Text)
    previous_publication_id: Mapped[str | None] = mapped_column(ForeignKey("publications.id"))


class PublicationPointer(Base):
    __tablename__ = "publication_pointer"
    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id"), primary_key=True)
    publication_id: Mapped[str] = mapped_column(ForeignKey("publications.id"))
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = _updated()


class Event(Base):
    __tablename__ = "events"
    id: Mapped[str] = _id()
    run_id: Mapped[str | None] = mapped_column(ForeignKey("runs.id"))
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    level: Mapped[str] = mapped_column(String(8))
    code: Mapped[str] = mapped_column(String(48))
    message: Mapped[str] = mapped_column(Text)
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    __table_args__ = (Index("ix_events_run_ts", "run_id", "ts"),)


class SettingRow(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSONB)
    updated_by: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = _updated()


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[str] = _id()
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actor: Mapped[str] = mapped_column(Text)
    action: Mapped[str] = mapped_column(String(48))
    target: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class NodeCoverage(Base):
    """Per-run, per-node listing totals vs captured UPCs (completeness proof, §5.6)."""

    __tablename__ = "node_coverage"
    id: Mapped[str] = _id()
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"))
    category_source_id: Mapped[str] = mapped_column(ForeignKey("category_sources.id"))
    taxonomy_id: Mapped[str] = mapped_column(String(64))
    total_count: Mapped[int | None] = mapped_column(Integer)
    organic_upcs: Mapped[int] = mapped_column(Integer, default=0)
    coverage_ratio: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(16))
    partition: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    __table_args__ = (
        UniqueConstraint("run_id", "category_source_id", "taxonomy_id", name="uq_node_coverage_key"),
    )


class CollectionSegment(Base):
    """One stretch of live collection by the collector service (start or resume until it stops).

    Limits are enforced from these rows: active time per run, provider credits per run
    and per day (``day`` is the local date in the collection timezone when the segment started), and
    the account's remaining credits seen at the start and the end."""

    __tablename__ = "collection_segments"
    id: Mapped[str] = _id()
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), index=True)
    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id"))
    trigger: Mapped[str] = mapped_column(String(16))  # manual | schedule | resume | recovery | finish
    day: Mapped[str] = mapped_column(String(10))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    heartbeat_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    active_s: Mapped[float] = mapped_column(Float, default=0.0)
    credits_estimated: Mapped[float] = mapped_column(Float, default=0.0)
    browser_sessions: Mapped[int] = mapped_column(Integer, default=0)
    browsers_closed: Mapped[int] = mapped_column(Integer, default=0)
    steps: Mapped[int] = mapped_column(Integer, default=0)
    products_verified: Mapped[int] = mapped_column(Integer, default=0)
    account_remaining_start: Mapped[int | None] = mapped_column(Integer)
    account_remaining_end: Mapped[int | None] = mapped_column(Integer)
    stop_code: Mapped[str | None] = mapped_column(String(48))
    stop_detail: Mapped[str | None] = mapped_column(Text)
    # Parallel collection: the workers of this execution and what was measured (requests, pages, products,
    # retries, waits, CPU and memory of the process, per worker), revision 0003.
    workers: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stats: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    __table_args__ = (Index("ix_collection_segments_store_day", "store_id", "day"),)


class ProviderUsage(Base):
    """One billable request to an API provider (Scrape.do, Oxylabs Web API), shared by every worker and
    process: the spending ledger.

    A request reserves its largest possible cost first (``outcome='reserved'``, under the provider's
    advisory lock), then the row is settled to what the provider charged (its cost header, else its
    documented rule). The task's credit ceiling and each key's balance are checked against these rows,
    so concurrent jobs cannot overspend. Never holds a key, only its role and fingerprint."""

    __tablename__ = "provider_usage"
    id: Mapped[str] = _id()
    at: Mapped[datetime] = _created()
    provider: Mapped[str] = mapped_column(String(16))
    key_role: Mapped[str] = mapped_column(String(16))  # primary | secondary
    key_fingerprint: Mapped[str] = mapped_column(String(16))
    run_id: Mapped[str | None] = mapped_column(ForeignKey("runs.id"), index=True)
    retailer: Mapped[str | None] = mapped_column(String(32))
    purpose: Mapped[str] = mapped_column(String(32))
    endpoint: Mapped[str] = mapped_column(String(64))
    target_url: Mapped[str] = mapped_column(Text)
    status: Mapped[int | None] = mapped_column(Integer)
    outcome: Mapped[str] = mapped_column(String(32))  # reserved | ok | not_found | <error kind>
    credits: Mapped[float] = mapped_column(Float, default=0.0)
    # header | rule | reserved | unknown (sent, no answer: the reserved cost is kept as possibly charged)
    cost_source: Mapped[str] = mapped_column(String(16), default="reserved")
    remaining_after: Mapped[int | None] = mapped_column(Integer)
    request_id: Mapped[str | None] = mapped_column(String(96))
    elapsed_ms: Mapped[int] = mapped_column(Integer, default=0)
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    # Revision 0003: the provider's API product and endpoint, the collection segment and worker that sent
    # it, and its dollar figure (None: the provider's price per unit is unknown).
    api_product: Mapped[str | None] = mapped_column(String(64), nullable=True)
    segment_id: Mapped[str | None] = mapped_column(String(26), nullable=True, index=True)
    worker: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    __table_args__ = (Index("ix_provider_usage_provider_at", "provider", "at"),)


class ProviderKey(Base):
    """A provider key by role (``primary``, ``secondary``): its fingerprint, the last measured balance
    (with its time and source) and, once the provider confirmed it, its exhaustion. The key itself stays
    in the server's protected environment."""

    __tablename__ = "provider_keys"
    provider: Mapped[str] = mapped_column(String(16), primary_key=True)
    role: Mapped[str] = mapped_column(String(16), primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(16))
    remaining: Mapped[int | None] = mapped_column(Integer)
    monthly: Mapped[int | None] = mapped_column(Integer)
    concurrency: Mapped[int | None] = mapped_column(Integer)
    is_active_account: Mapped[bool | None] = mapped_column(Boolean)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    read_source: Mapped[str | None] = mapped_column(String(16))  # info | header
    exhausted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    exhausted_reason: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = _created()


class FollowUpItem(Base):
    """A product page the store's follow-ups are to read (revision 0004): a product a run saw only in
    sponsored placements, or a variant sibling a result tile names. One row per store, kind, item and lineage,
    kept across runs. A candidate no run read yet, or whose page was not read to a decision (a pilot budget,
    a pause, an inaccessible page), stays ``pending``: the next run of the store with the same lineage reads
    the longest-waiting first, so a budget never drops one for good. A page read to a decision (included,
    duplicate, excluded) resolves it; a later run that sees it again reads it again."""

    __tablename__ = "follow_up_queue"
    id: Mapped[str] = _id()
    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id"))
    kind: Mapped[str] = mapped_column(String(16))
    item_id: Mapped[str] = mapped_column(String(20))
    # The lineage of the runs that named it (network | substituted): a run takes only its own lineage's.
    lineage: Mapped[str] = mapped_column(String(16))
    url: Mapped[str | None] = mapped_column(Text)
    listing: Mapped[str | None] = mapped_column(String(128))
    named_by: Mapped[str | None] = mapped_column(String(20))
    option: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    origin: Mapped[str] = mapped_column(Text)  # "observed" or "seed: <where an earlier report named it>"
    first_seen_run: Mapped[str] = mapped_column(String(26))
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_run: Mapped[str] = mapped_column(String(26))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    runs_seen: Mapped[int] = mapped_column(Integer, default=1)
    state: Mapped[str] = mapped_column(String(16), default="pending")
    last_status: Mapped[str | None] = mapped_column(String(16))  # the last outcome (FOLLOW_STATUSES)
    last_reason: Mapped[str | None] = mapped_column(Text)
    last_run: Mapped[str | None] = mapped_column(String(26))
    last_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pages_read: Mapped[int] = mapped_column(Integer, default=0)
    __table_args__ = (
        UniqueConstraint("store_id", "kind", "item_id", "lineage", name="uq_follow_up_queue_item"),
        CheckConstraint(_in("kind", FOLLOW_KINDS), name="kind"),
        CheckConstraint(_in("state", FOLLOW_STATES), name="state"),
        Index("ix_follow_up_queue_store_state", "store_id", "state"),
    )


class DetailObservation(Base):
    """What one read of a product's own page established (revision 0006): its UPC or the absence of one and
    its statements about size, with the time, run, source revision and page hash of that read. Kept across
    runs, so that a later run reuses the fields as what they are, an earlier observation, and never as newly
    fetched. Only a page inspected for the right item is kept; a refused or failed read stays on the queue
    (``follow_up_queue``, kind ``detail``). ``origin`` ``imported`` marks a saved capture of an earlier
    delivery loaded by ``import-detail-captures``; its ``run_id`` may belong to another database."""

    __tablename__ = "detail_observations"
    id: Mapped[str] = _id()
    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id"))
    item_id: Mapped[str] = mapped_column(String(20))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    run_id: Mapped[str] = mapped_column(String(26))
    page_fetch_id: Mapped[str | None] = mapped_column(String(26))
    source_revision: Mapped[str | None] = mapped_column(Text)
    origin: Mapped[str] = mapped_column(String(16))
    url: Mapped[str | None] = mapped_column(Text)
    body_sha256: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20))
    upc: Mapped[str | None] = mapped_column(String(14))
    upc_path: Mapped[str | None] = mapped_column(Text)
    size_statements: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = _created()
    __table_args__ = (
        UniqueConstraint("store_id", "item_id", "body_sha256", name="uq_detail_observations_page"),
        CheckConstraint(_in("status", DETAIL_STATUSES), name="status"),
        CheckConstraint(_in("origin", DETAIL_ORIGINS), name="origin"),
        Index("ix_detail_observations_item", "store_id", "item_id", "observed_at"),
    )


class ScheduleOccurrence(Base):
    """One scheduled start of a store (revision 0006): an occurrence has an identity from the moment its start
    time has passed, whether or not anything could start then. ``due`` waits for a firing; ``deferred`` waits
    because the store could not start it (another run active or unfinished, a hold, the window closed), with
    the reason; ``running`` has a run; ``completed`` its run finished; ``superseded`` its run was closed as
    partial by ``schedule.on_overlap: supersede``. ``deadline_missed_at``: the next occurrence's start passed
    while this one was still waiting, which is a capacity gap reported by ``schedule-status``."""

    __tablename__ = "schedule_occurrences"
    id: Mapped[str] = _id()
    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id"))
    day: Mapped[str] = mapped_column(String(10))  # the store-local date of its start
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    window: Mapped[dict[str, Any]] = mapped_column(JSONB)  # Occurrence.as_dict() when it was registered
    state: Mapped[str] = mapped_column(String(16), default="due")
    noticed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    run_id: Mapped[str | None] = mapped_column(String(26))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deadline_missed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        UniqueConstraint("store_id", "day", name="uq_schedule_occurrences_day"),
        CheckConstraint(_in("state", OCCURRENCE_STATES), name="state"),
        Index("ix_schedule_occurrences_store_state", "store_id", "state"),
    )
