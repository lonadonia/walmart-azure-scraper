"""The collector's operations, one per command. Each runs once and returns an exit code.

Nothing here schedules anything. Azure Container Apps starts the job (one scheduled trigger per store) and
the job exits when its run has finished or stopped. ``run --scheduled`` checks three things:

* the execution is the store's due occurrence, in store-local time, so a daylight-saving change never
  shifts it;
* the store's schedule is not held;
* whether the occurrence already has a run. An Azure retry or the second UTC firing then does nothing
  twice.

Retries are bounded inside one execution: a page is retried as ``settings.retries`` allows, and a run
stopped by a transient provider failure is resumed at most ``max_auto_resumes`` times. A run stopped by a
limit, or by an operator's stop request, is finalized: its records are checked and exported as a pilot or
partial dataset, kept under the run, and never published. Only a complete, validated run is published as
the store's latest dataset.
"""

from __future__ import annotations

import asyncio
import gzip
import json
import os
import shutil
import socket
import tempfile
from collections import Counter
from collections.abc import Callable
from datetime import datetime, time, timedelta
from enum import IntEnum
from functools import cached_property
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session, sessionmaker

from walmart_headless.acquisition import budget, lineage, oxylabs
from walmart_headless.acquisition.scrapedo import load_keys
from walmart_headless.checks import contract, source_check
from walmart_headless.collection import (
    control,
    detail_captures,
    follow_queue,
    occurrences,
    reconcile,
    scrapedo_account,
    segments,
)
from walmart_headless.collection.config import parse_hhmm
from walmart_headless.collection.limits import (
    LIMIT_STOPS,
    SUSPENDS_SCHEDULE,
    StopCode,
    stop_text,
)
from walmart_headless.collection.schedule import Occurrence, local_day, next_occurrence, occurrence_on
from walmart_headless.collection.walmart import WalmartCollector
from walmart_headless.config_file import LoadedConfig, StoreCollection
from walmart_headless.core import logs
from walmart_headless.core.jsonio import dumps_bytes
from walmart_headless.core.settings import Settings, StorageSettings
from walmart_headless.core.timeutil import iso, utcnow
from walmart_headless.db import migrate
from walmart_headless.db.locks import RunLockHeld, worker_alive
from walmart_headless.db.models import (
    Artifact,
    AuditLog,
    Event,
    ExportRow,
    FollowUpItem,
    PageFetch,
    Publication,
    PublicationPointer,
    RecordRow,
    Run,
    SettingRow,
    Store,
    ValidationFinding,
)
from walmart_headless.db.repo import import_category_sources, sync_stores
from walmart_headless.db.session import make_engine
from walmart_headless.publishing import dispositions
from walmart_headless.publishing.exports import manifest_files, verify_manifest
from walmart_headless.publishing.publish import (
    NON_BLOCKING_GATES,
    PublicationRefused,
    latest_key,
    publish_run,
)
from walmart_headless.publishing.supporting_log import field_dispositions
from walmart_headless.sites.walmart.csv_sources import load_category_csv
from walmart_headless.storage.base import ImmutableWriteError, StorageAdapter
from walmart_headless.storage.factory import make_storage
from walmart_headless.worker.pipeline import FINISHED_STATES, Pipeline
from walmart_headless.worker.runs import event, transition


class Exit(IntEnum):
    OK = 0  # finished (validated or published), or nothing was due
    UNEXPECTED = 1
    CONFIG = 2  # configuration or database schema
    CREDENTIALS = 3  # no provider key, or the provider refused it
    CREDITS = 4  # provider credits or a credit budget ran out
    SITE_REFUSAL = 5  # the website refused access (403/429, challenge)
    REJECTED = 6  # the run's checks rejected it, or an export did not verify
    NOT_VERIFIED = 7  # the store, fulfillment or the canary checks failed
    HELD = 8  # the store's collection is held until an operator releases it
    BUSY = 9  # another execution holds the store, or an unfinished run must be resumed or finalized
    INTERRUPTED = 75  # stopped resumably (termination signal, provider failure); resume continues it


STOP_EXIT: dict[str, Exit] = {
    StopCode.NO_API_KEY: Exit.CREDENTIALS,
    StopCode.PROVIDER_AUTH: Exit.CREDENTIALS,
    StopCode.CREDITS_EXHAUSTED: Exit.CREDITS,
    StopCode.CREDIT_RESERVE: Exit.CREDITS,
    StopCode.RUN_CREDIT_LIMIT: Exit.CREDITS,
    StopCode.DAILY_CREDIT_LIMIT: Exit.CREDITS,
    StopCode.SPENDING_CEILING: Exit.CREDITS,
    StopCode.SITE_REFUSAL: Exit.SITE_REFUSAL,
    StopCode.STORE_NOT_VERIFIED: Exit.NOT_VERIFIED,
    StopCode.CANARY_CHECK_FAILED: Exit.NOT_VERIFIED,
    StopCode.ABNORMAL_RESULT: Exit.REJECTED,
    StopCode.TERMINATED: Exit.INTERRUPTED,
}
CREDIT_STOPS = frozenset(
    {
        StopCode.CREDITS_EXHAUSTED,
        StopCode.CREDIT_RESERVE,
        StopCode.RUN_CREDIT_LIMIT,
        StopCode.DAILY_CREDIT_LIMIT,
        StopCode.SPENDING_CEILING,
    }
)
# Stopped by its own bounds or an operator: the run is finalized with what it collected.
FINALIZE_ON = frozenset({*LIMIT_STOPS, StopCode.OPERATOR_STOP, StopCode.SUPERSEDED})
# Stopped by a transient failure: resumed in the same execution, a bounded number of times.
AUTO_RESUME_ON = frozenset({StopCode.PROVIDER_ERROR, StopCode.ACCOUNT_UNAVAILABLE, StopCode.SERVICE_RESTART})
AUTO_RESUME_WAIT_S = 60.0
EARLY_START = timedelta(minutes=5)  # a scheduled execution a little before the start time counts as on time
HOLD_PREFIX = "hold:"
ENV_STORAGE = "WALMART_COLLECTOR_STORAGE"
ENV_DATA_DIR = "WALMART_COLLECTOR_DATA_DIR"
ENV_BLOB_URL = "WALMART_COLLECTOR_BLOB_ACCOUNT_URL"
ENV_BLOB_CONTAINER = "WALMART_COLLECTOR_BLOB_CONTAINER"


class CommandError(Exception):
    """A command refused with a reason and an exit code (nothing was changed)."""

    def __init__(self, code: Exit, message: str, **data: Any):
        super().__init__(message)
        self.code = code
        self.data = data


# -- context ------------------------------------------------------------------------------------------


class Context:
    """The configuration, and lazily the database and storage of one command."""

    def __init__(self, config_path: Path, *, environ: dict[str, str] | None = None):
        self.environ = dict(os.environ if environ is None else environ)
        self.config = LoadedConfig(config_path)
        self.owner = f"{socket.gethostname()}:{os.getpid()}"
        self.clock: Callable[[], datetime] = utcnow  # tests replace it to simulate a store-local time
        self._engine: Engine | None = None

    @cached_property
    def storage_settings(self) -> StorageSettings:
        base = self.config.settings.storage
        update: dict[str, Any] = {}
        if self.environ.get(ENV_STORAGE):
            update["backend"] = self.environ[ENV_STORAGE]
        if self.environ.get(ENV_DATA_DIR):
            update["local_root"] = self.environ[ENV_DATA_DIR]
        if self.environ.get(ENV_BLOB_URL):
            update["azure_account_url"] = self.environ[ENV_BLOB_URL]
        if self.environ.get(ENV_BLOB_CONTAINER):
            update["azure_container"] = self.environ[ENV_BLOB_CONTAINER]
        return StorageSettings.model_validate({**base.model_dump(), **update})

    @cached_property
    def settings(self) -> Settings:
        return self.config.settings.model_copy(update={"storage": self.storage_settings})

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            self._engine = make_engine()
        return self._engine

    @cached_property
    def factory(self) -> sessionmaker[Session]:
        return sessionmaker(self.engine, expire_on_commit=False)

    @cached_property
    def storage(self) -> StorageAdapter:
        return make_storage(self.storage_settings, base_dir=Path.cwd())

    def pipeline(self, store_key: str) -> Pipeline:
        store = self.config.store(store_key)
        return Pipeline(self.engine, self.storage, self.settings, store, self.config.private_label)

    def close(self) -> None:
        if self._engine is not None:
            self._engine.dispose()

    def require_schema(self) -> None:
        current, head = migrate.state(self.engine)
        if current != head:
            raise CommandError(
                Exit.CONFIG,
                "the database schema is not current: run 'walmart-collector db-upgrade'",
                current=current,
                head=head,
            )


# -- configuration ---------------------------------------------------------------------------------


def masked_key() -> dict[str, Any]:
    keys = load_keys()
    return {
        "configured": bool(keys),
        "fingerprint": scrapedo_account.masked(keys[0].fingerprint) if keys else None,
        "source": "SCRAPEDO_API_KEY_FILE"
        if os.environ.get("SCRAPEDO_API_KEY_FILE")
        else ("SCRAPEDO_API_KEY" if keys else None),
    }


def masked_oxylabs_key() -> dict[str, Any]:
    key = oxylabs.load_key()
    return {
        "configured": key is not None,
        "fingerprint": scrapedo_account.masked(key.fingerprint) if key else None,
        "source": oxylabs.ENV_KEY_FILE
        if os.environ.get(oxylabs.ENV_KEY_FILE)
        else (oxylabs.ENV_KEY if key else None),
        "api": "Oxylabs Web API (Bearer key); the Classic Web Scraper API is another product",
    }


def utc_cron(coll: StoreCollection, year: int | None = None) -> dict[str, Any]:
    """The Azure cron expression (UTC) that covers the store-local schedule in standard and daylight time.

    Azure evaluates cron in UTC. The expression fires at the UTC time of the local start for both offsets
    of the timezone; ``run --scheduled`` then acts only on the firing that is the due local occurrence."""
    sched = coll.schedule
    tz = ZoneInfo(coll.timezone)
    year = year or utcnow().year
    hh, mm = (int(x) for x in sched.start_time.split(":"))
    minutes: set[int] = set()
    hours: set[int] = set()
    days: set[int] = set()
    offsets: dict[str, str] = {}
    for label, month in (("january", 1), ("july", 7)):
        local = datetime(year, month, 15, hh, mm, tzinfo=tz)
        utc = local.astimezone(ZoneInfo("UTC"))
        offsets[label] = f"local {sched.start_time} = {utc:%H:%M} UTC (UTC{local:%z})"
        shift = (utc.date() - local.date()).days
        minutes.add(utc.minute)
        hours.add(utc.hour)
        for wd in sched.weekdays:
            days.add(((wd + shift) % 7 + 1) % 7)  # cron: 0 = Sunday
    expr = (
        f"{','.join(map(str, sorted(minutes)))} {','.join(map(str, sorted(hours)))} * * "
        f"{','.join(map(str, sorted(days)))}"
        if sched.weekdays
        else None
    )
    out: dict[str, Any] = {"cron_utc": expr, "offsets": offsets, "timezone": coll.timezone}
    if sched.continue_unfinished:
        # Continuation firings (a run longer than one execution): the job fires every 30 minutes; each firing
        # starts the due occurrence, continues the store's unfinished scheduled run inside the daily window,
        # or exits in seconds. This expression replaces the start-only one above.
        out["cron_utc_with_continuation"] = "*/30 * * * *"
    return out


def describe_config(ctx: Context) -> dict[str, Any]:
    cfg = ctx.config
    sources, csv_sha = load_category_csv(cfg.categories_csv)
    names = {s.row_index: s.category_name for s in sources}
    stores = []
    for st in cfg.stores.stores:
        coll = cfg.collection(st.key)
        unknown = [r for r in coll.categories if r not in names]
        if unknown:
            raise CommandError(Exit.CONFIG, f"{st.key}: category rows not in the CSV: {unknown}")
        tz = ZoneInfo(coll.timezone)
        nxt = next_occurrence(coll.schedule, utcnow(), tz) if coll.schedule.enabled else None
        stores.append(
            {
                "key": st.key,
                "enabled": st.enabled,
                "store_id": st.location_id,
                "zipcode": st.expected.postal_code,
                "name": st.expected.display_name,
                "address": st.expected.address_line1,
                "fulfillment": st.modality.value,
                "provider": coll.provider,
                "workers": coll.parallel.workers,
                "categories": [names[r] for r in coll.categories] or "all",
                "limits": coll.limits.model_dump(exclude_none=True),
                "pilot_by_limits": coll.bounded(),
                "pilot_budgets": coll.pilot_budgets(),
                "scheduled_scope_problem": (
                    f"the schedule is on and the configuration narrows the scope: "
                    f"{sorted(coll.pilot_budgets())}"
                    if coll.schedule.enabled and coll.bounded()
                    else None
                ),
                "schedule": {
                    **coll.schedule.model_dump(mode="json"),
                    **utc_cron(coll),
                    "next_local_start": nxt.start.isoformat() if nxt else None,
                },
            }
        )
    return {
        "config": str(cfg.path),
        "edition": cfg.collector.edition.model_dump(mode="json"),
        "categories_csv": {"path": str(cfg.categories_csv), "rows": len(sources), "sha256": csv_sha},
        "stores": stores,
        "canary": cfg.collector.canary.model_dump(),
        "historical": cfg.collector.historical.model_dump(),
        "publish": cfg.collector.publish.model_dump(),
        "storage": {"backend": ctx.storage_settings.backend},
        "environment": {
            "database_url_set": bool(ctx.environ.get("WALMART_COLLECTOR_DATABASE_URL")),
            "database_auth": ctx.environ.get("WALMART_COLLECTOR_DATABASE_AUTH") or "password",
            "scrapedo_key": masked_key(),
            "oxylabs_key": masked_oxylabs_key(),
        },
    }


def sync_config(ctx: Context, actor: str) -> dict[str, Any]:
    """Stores and the category CSV into the database (idempotent; rows no longer in the CSV are disabled)."""
    sources, csv_sha = load_category_csv(ctx.config.categories_csv)
    with ctx.factory() as s:
        stores = sync_stores(s, ctx.config.stores, actor)
        cats = import_category_sources(s, sources, csv_sha, actor)
        s.commit()
    return {
        "stores": vars(stores),
        "categories": {**vars(cats), "csv_sha256": csv_sha},
    }


# -- holds ----------------------------------------------------------------------------------------------


def get_hold(s: Session, store_key: str) -> dict[str, Any] | None:
    row = s.get(SettingRow, HOLD_PREFIX + store_key)
    return dict(row.value) if row is not None and row.value.get("held") else None


def set_hold(s: Session, store_key: str, run: Run) -> None:
    value = {
        "held": True,
        "stop_code": run.stop_code,
        "reason": f"{stop_text(run.stop_code)}: {run.stop_detail or ''}"[:500],
        "run_id": run.id,
        "at": iso(utcnow()),
    }
    row = s.get(SettingRow, HOLD_PREFIX + store_key)
    if row is None:
        s.add(SettingRow(key=HOLD_PREFIX + store_key, value=value, updated_by="collector"))
    else:
        row.value, row.updated_by = value, "collector"
    s.add(AuditLog(actor="collector", action="collection_held", target=store_key, data=value))
    event(
        s,
        run.id,
        "WARN",
        "COLLECTION_HELD",
        f"{store_key}: collection held until an operator runs release-hold",
        {"stop_code": run.stop_code},
    )


def release_hold(ctx: Context, store_key: str, reason: str, actor: str) -> dict[str, Any]:
    ctx.config.store(store_key)
    if not reason.strip():
        raise CommandError(Exit.CONFIG, "a reason is required to release a hold")
    with ctx.factory() as s:
        hold = get_hold(s, store_key)
        if hold is None:
            return {"store": store_key, "held": False, "released": False}
        row = s.get(SettingRow, HOLD_PREFIX + store_key)
        assert row is not None
        row.value = {
            **hold,
            "held": False,
            "released_at": iso(utcnow()),
            "released_by": actor,
            "reason": reason,
        }
        s.add(AuditLog(actor=actor, action="hold_released", target=store_key, reason=reason, data=hold))
        s.commit()
    logs.log("INFO", "HOLD_RELEASED", store=store_key, reason=reason, previous=hold)
    return {"store": store_key, "held": False, "released": True, "previous": hold}


# -- runs -----------------------------------------------------------------------------------------------


# A bounded (pilot) run fails the coverage check by design: the pages its limits left out were not read.
PILOT_EXPECTED_GATES = frozenset({"G3"})


def failed_gates(s: Session, run_id: str) -> list[str]:
    """The blocking checks that failed (G14, the readiness marker, never blocks)."""
    return sorted(
        {
            f.gate
            for f in s.scalars(
                select(ValidationFinding).where(
                    ValidationFinding.run_id == run_id, ValidationFinding.severity == "FAIL"
                )
            )
            if f.gate not in NON_BLOCKING_GATES
        }
    )


def exit_for(s: Session, run: Run) -> Exit:
    code = run.stop_code
    if run.status in ("validated", "published"):
        return Exit.CREDITS if code in CREDIT_STOPS else Exit.OK
    if run.status == "rejected":
        # A finished run is never "stopped resumably" (75): nothing can continue it any more.
        if code in STOP_EXIT and STOP_EXIT[code] is not Exit.INTERRUPTED:
            return STOP_EXIT[code]
        pilot = bool((run.config_snapshot or {}).get("pilot"))
        if pilot and set(failed_gates(s, run.id)) <= PILOT_EXPECTED_GATES:
            return Exit.OK  # the pilot collected what its limits allowed and every record check passed
        return Exit.REJECTED
    if run.status == "interrupted":
        return STOP_EXIT.get(code or "", Exit.INTERRUPTED)
    if run.status == "cancelled":
        return Exit.OK
    return Exit.UNEXPECTED


def run_summary(pipe: Pipeline | None, run: Run) -> dict[str, Any]:
    counts = run.counts or {}
    snap = run.config_snapshot or {}
    return {
        "run_id": run.id,
        "status": run.status,
        "trigger": run.trigger,
        "dataset": pipe.dataset_label(run) if pipe is not None else None,
        "pilot": bool(snap.get("pilot")),
        "occurrence": (snap.get("occurrence") or {}).get("day"),
        "stop_code": run.stop_code,
        "stop_detail": run.stop_detail,
        "created_at": iso(run.created_at) if run.created_at else None,
        "started_at": iso(run.started_at) if run.started_at else None,
        "finished_at": iso(run.finished_at) if run.finished_at else None,
        "outcome": counts.get("outcome"),
        "records_by_status": counts.get("records_by_status"),
        "collection_complete": counts.get("collection_complete"),
        "canary": counts.get("canary"),
        "historical": counts.get("historical"),
    }


def collection_of(run: Run) -> StoreCollection:
    """The collection settings recorded with the run (a resumed run keeps its limits)."""
    return StoreCollection.model_validate((run.config_snapshot or {}).get("collection") or {})


def check_key(provider: str = "scrapedo") -> None:
    if provider == "oxylabs":
        if oxylabs.load_key() is None:
            raise CommandError(
                Exit.CREDENTIALS,
                f"no Oxylabs Web API key: set {oxylabs.ENV_KEY} or {oxylabs.ENV_KEY_FILE} (a secret file)",
            )
        return
    if not load_keys():
        raise CommandError(
            Exit.CREDENTIALS,
            "no Scrape.do key: set SCRAPEDO_API_KEY or SCRAPEDO_API_KEY_FILE (an Azure secret)",
        )


def check_edition(ctx: Context, provider: str) -> None:
    """Only the edition's providers: a run (or a provider command) naming another is refused before any
    request, never sent to another provider."""
    edition = ctx.config.collector.edition
    if provider not in edition.providers:
        raise CommandError(
            Exit.CONFIG,
            f"the {edition.name} edition runs {', '.join(edition.providers)} only: provider {provider} "
            "refused",
            edition=edition.name,
        )


def provider_of(run: Run) -> str:
    return str((run.config_snapshot or {}).get("provider") or "scrapedo")


def _store_row(s: Session, store_key: str) -> Store:
    row = s.scalar(select(Store).where(Store.key == store_key))
    if row is None:
        raise CommandError(Exit.CONFIG, f"store {store_key} is not in the database: run sync-config")
    return row


async def _execute(
    ctx: Context, store_key: str, run_id: str, *, trigger: str, resume: bool, workers: int | None = None
) -> str:
    pipe = ctx.pipeline(store_key)
    with ctx.factory() as s:
        run = s.get(Run, run_id)
        assert run is not None
        cfg = collection_of(run)
        replay = run.mode == "REPLAY"
    if replay:
        raise CommandError(Exit.CONFIG, f"run {run_id} is a replay: it is continued by resume alone")
    collector = WalmartCollector(
        pipe,
        run_id,
        config=cfg,
        trigger=trigger,
        canary=ctx.config.collector.canary,
        historical=ctx.config.collector.historical,
        clock=ctx.clock,
    )
    n = workers or cfg.parallel.workers
    status: str = await pipe.execute(run_id, ctx.owner, collector=collector, resume=resume, workers=n)
    return status


async def drive(
    ctx: Context, store_key: str, run_id: str, *, trigger: str, resume: bool, workers: int | None = None
) -> Exit:
    """Execute a run to its end in this execution: finalize it after a limit or an operator's stop, resume
    it (bounded) after a transient failure, then hold, publish or keep the partial result."""
    finalized = False
    while True:
        logs.log("INFO", "RUN_EXECUTING", run_id=run_id, store=store_key, trigger=trigger, resume=resume)
        try:
            await _execute(ctx, store_key, run_id, trigger=trigger, resume=resume, workers=workers)
        except RunLockHeld as exc:
            logs.log("WARN", "STORE_BUSY", run_id=run_id, store=store_key, message=str(exc))
            return Exit.BUSY
        resume = True
        with ctx.factory() as s:
            run = s.get(Run, run_id)
            assert run is not None
            code = run.stop_code
            if (
                run.status == "interrupted"
                and not finalized
                and (run.finish_requested or (code in FINALIZE_ON and not continues_later(run, code)))
            ):
                control.prepare_finish(s, run)
                s.commit()
                finalized, trigger = True, "finish"
                continue
            if run.status == "interrupted" and code in AUTO_RESUME_ON:
                counts = dict(run.counts or {})
                attempts = int(counts.get("auto_resumes", 0))
                limit = collection_of(run).max_auto_resumes
                if attempts < limit:
                    counts["auto_resumes"] = attempts + 1
                    run.counts = counts
                    event(
                        s,
                        run_id,
                        "INFO",
                        "RUN_AUTO_RESUMED",
                        f"automatic resume {attempts + 1} of {limit} after: {stop_text(code)}",
                    )
                    s.commit()
                    await asyncio.sleep(AUTO_RESUME_WAIT_S * (attempts + 1))
                    trigger = "auto"
                    continue
        break
    return after_run(ctx, store_key, run_id)


def continues_later(run: Run, code: str | None) -> bool:
    """A run paused at its execution's time limit is continued by the next execution (``resume`` or the
    schedule), never finalized there; a scheduled run that reached its daily window's end is continued on
    a later day when the schedule continues unfinished runs."""
    if code == StopCode.SEGMENT_DURATION_LIMIT.value:
        return True
    if code == StopCode.SCHEDULE_WINDOW_END.value and run.trigger == "schedule":
        return collection_of(run).schedule.continue_unfinished
    return False


def daily_window_open(coll: StoreCollection, now: datetime) -> bool:
    """Inside the schedule's daily window today (any weekday: a continuation day)."""
    tz = ZoneInfo(coll.timezone)
    local = now.astimezone(tz)
    sched = coll.schedule
    start = datetime.combine(local.date(), parse_hhmm(sched.window_start or sched.start_time), tzinfo=tz)
    end = (
        datetime.combine(local.date(), parse_hhmm(sched.window_end), tzinfo=tz)
        if sched.window_end
        else datetime.combine(local.date() + timedelta(days=1), time(0, 0), tzinfo=tz)
    )
    return start <= local < end


async def continue_scheduled(
    ctx: Context, store_key: str, coll: StoreCollection, now: datetime
) -> Exit | None:
    """A firing that is not an occurrence's start: continue the store's unfinished scheduled run (an earlier
    execution paused it at its time limit or the window's end, or it was interrupted) when the schedule
    continues unfinished runs and the daily window is open. ``None``: nothing to continue now."""
    if not coll.schedule.continue_unfinished or not daily_window_open(coll, now):
        return None
    with ctx.factory() as s:
        row = s.scalar(select(Store).where(Store.key == store_key))
        if row is None:  # never synced, so never run: nothing to continue
            return None
        current = control.open_run(s, row.id)
        if current is None or current.trigger != "schedule":
            return None
        if current.status in control.ACTIVE and worker_alive(s, row.id, current.id):
            logs.log("WARN", "STORE_BUSY", store=store_key, run_id=current.id)
            return Exit.BUSY
        if get_hold(s, store_key) is not None:
            logs.log("WARN", "COLLECTION_HELD", store=store_key, run_id=current.id)
            return Exit.HELD
        day = ((current.config_snapshot or {}).get("occurrence") or {}).get("day")
        _recover(s, current)
        s.commit()
        run_id = current.id
        provider = provider_of(current)
    check_edition(ctx, provider)
    check_key(provider)
    logs.log(
        "INFO", "OCCURRENCE_CONTINUED", store=store_key, occurrence=day, run_id=run_id, continuation=True
    )
    return await drive(ctx, store_key, run_id, trigger="schedule", resume=True)


def after_run(ctx: Context, store_key: str, run_id: str) -> Exit:
    """Hold the store after a refusal or a failed source check; keep a stopped run's records as a partial
    export; publish a complete validated run.

    Release 1.6.6: a complete validated run whose automatic publication is refused is an error, never a quiet
    success. The refusal is recorded on the run and logged at ERROR (``PUBLICATION_REFUSED``), the run's
    summary says so (``publication``), and the execution exits 6 (rejected: nothing was published), so an
    alert on an ERROR line or on a non-zero exit code fires. The last published dataset stays published.
    1.6.5 logged the refusal at WARN and exited 0."""
    pipe = ctx.pipeline(store_key)
    with ctx.factory() as s:
        run = s.get(Run, run_id)
        assert run is not None
        if run.stop_code in {c.value for c in SUSPENDS_SCHEDULE} and get_hold(s, store_key) is None:
            set_hold(s, store_key, run)
        s.commit()
        if (
            run.status == "rejected"
            and s.scalar(select(ExportRow.id).where(ExportRow.run_id == run_id, ExportRow.kind == "manifest"))
            is None
        ):
            try:
                try:
                    ex = pipe.write_run_exports(s, run)
                except ImmutableWriteError:
                    # An export task stopped half-way left files behind: this export goes next to them.
                    stamp = ctx.clock().strftime("%Y%m%dT%H%M%SZ")
                    ex = pipe.write_run_exports(s, run, prefix=f"{pipe.prefix(run_id)}/exports-{stamp}")
                event(
                    s,
                    run_id,
                    "INFO",
                    "PARTIAL_EXPORT",
                    "the stopped run's records are kept as a partial export (never published)",
                    {"manifest": ex.manifest.key, "records": ex.manifest_body["record_count"]},
                )
                s.commit()
            except Exception as exc:  # the run's outcome stands; its records stay in the database
                s.rollback()
                logs.log(
                    "WARN",
                    "PARTIAL_EXPORT_FAILED",
                    run_id=run_id,
                    error=type(exc).__name__,
                    message=str(exc)[:300],
                )
            run = s.get(Run, run_id)
            assert run is not None
        label = pipe.dataset_label(run)
        status = run.status
    publication: dict[str, Any] | None = None
    if status == "validated" and label == "complete" and ctx.config.collector.publish.auto:
        try:
            pub = publish_run(
                ctx.factory,
                ctx.storage,
                run_id,
                "collector",
                warn_override_reason=ctx.config.collector.publish.accept_warnings_reason,
                test_target=ctx.settings.publication.test_target,
            )
            publication = {"automatic": True, "published": True, "version": pub.version}
            logs.log("INFO", "RUN_PUBLISHED", run_id=run_id, store=store_key, version=pub.version)
        except PublicationRefused as exc:
            publication = {"automatic": True, "published": False, "refused": str(exc)}
            with ctx.factory() as s:
                event(
                    s,
                    run_id,
                    "ERROR",
                    "PUBLICATION_REFUSED",
                    f"the complete validated run was not published: {exc}; the last published dataset stays",
                    {"store": store_key, "reason": str(exc)},
                )
                s.commit()
    with ctx.factory() as s:
        run = s.get(Run, run_id)
        assert run is not None
        summary = run_summary(pipe, run)
        code = exit_for(s, run)
        if publication is not None:
            summary["publication"] = publication
            if not publication["published"] and code is Exit.OK:
                code = Exit.REJECTED  # 1.6.6: nothing was published, so the execution does not end as OK
        summary["failed_checks"] = failed_gates(s, run.id)
    logs.log(
        "INFO" if code is Exit.OK else "WARN", "RUN_FINISHED", store=store_key, exit_code=int(code), **summary
    )
    return code


def _overrides(coll: StoreCollection, overrides: dict[str, Any]) -> StoreCollection:
    if not overrides:
        return coll
    data = coll.model_dump(mode="json")
    limits = dict(data["limits"])
    for key, value in overrides.items():
        if key in ("categories", "subcategories", "provider"):
            data[key] = value
        elif key == "pilot_detail_pages":
            data["detail"] = {**data["detail"], "max_per_run": value}
        elif key == "pilot_no_detail":
            data["detail"] = {**data["detail"], "enabled": False}
        elif key == "workers":
            data["parallel"] = {**data["parallel"], "workers": value}
        elif key == "follow_up_pages":
            data["follow_up"] = {**data["follow_up"], "max_pages": value}
        else:
            limits[key] = value
    data["limits"] = limits
    return StoreCollection.model_validate(data)


def _recover(s: Session, run: Run) -> None:
    """A run left active by an execution that ended (its worker no longer holds the store lock): its open
    segment is recorded as abandoned, with no end time invented (collection/segments.py)."""
    if run.status in ("preflight", "running") and not worker_alive(s, run.store_id, run.id):
        run.stop_code = StopCode.SERVICE_RESTART.value
        run.stop_detail = "the execution that collected it ended without closing it"
        transition(s, run.id, "interrupted")
        event(s, run.id, "WARN", "RUN_RECOVERED", run.stop_detail)
        segments.abandon_open(s, run.id, current=None, detected_by="the run's recovery", now=utcnow())


async def start_run(ctx: Context, store_key: str, overrides: dict[str, Any], actor: str) -> Exit:
    """A manual run (an operator, or the small verification) of one store."""
    ctx.config.store(store_key)
    coll = _overrides(ctx.config.collection(store_key), overrides)
    with ctx.factory() as s:
        hold = get_hold(s, store_key)
    if hold is not None:
        raise CommandError(
            Exit.HELD, f"{store_key} is held: {hold['reason']} (release-hold first)", hold=hold
        )
    check_edition(ctx, coll.provider)
    check_key(coll.provider)
    sync_config(ctx, actor)
    pipe = ctx.pipeline(store_key)
    # Narrowed on the command line (categories or listings) or by a limit or a page budget: a pilot, never
    # published as the store's dataset.
    pilot = coll.bounded() or bool(overrides.get("categories") or overrides.get("subcategories"))
    with ctx.factory() as s:
        row = _store_row(s, store_key)
        current = control.open_run(s, row.id)
        if current is not None:
            _recover(s, current)
            s.commit()
            raise CommandError(
                Exit.BUSY,
                f"{store_key} has an unfinished run {current.id} ({current.status}): resume or finalize it",
                run_id=current.id,
            )
        try:
            run_id = control.create_run(
                s,
                pipe=pipe,
                store=ctx.config.store(store_key),
                cfg=coll,
                trigger="manual",
                started_by=actor,
                pilot=pilot,
                overrides=overrides,
                edition=ctx.config.collector.edition.name,
            )
        except control.StartRefused as exc:
            raise CommandError(Exit.CONFIG, str(exc)) from None
        s.commit()
    logs.log(
        "INFO",
        "RUN_CREATED",
        run_id=run_id,
        store=store_key,
        pilot=pilot,
        overrides=overrides,
    )
    return await drive(ctx, store_key, run_id, trigger="manual", resume=False)


def due_occurrence(coll: StoreCollection, now: datetime) -> Occurrence | None:
    """Today's occurrence when ``now`` is its start time (a few minutes early, or up to the tolerance
    late)."""
    tz = ZoneInfo(coll.timezone)
    occ = occurrence_on(coll.schedule, local_day(now + EARLY_START, tz), tz)
    if occ is None:
        return None
    if occ.start - EARLY_START <= now <= occ.start + timedelta(minutes=coll.start_tolerance_minutes):
        return occ
    return None


async def scheduled_run(ctx: Context, store_key: str, now: datetime | None = None) -> Exit:
    """One scheduled execution for a store (a timer or Azure's cron fired). Every start that has passed gets
    its identity first (collection/occurrences.py); the oldest occurrence still waiting is the one acted on,
    and one that cannot start stays waiting with its reason."""
    now = now or ctx.clock()
    ctx.config.store(store_key)
    coll = ctx.config.collection(store_key)
    tz = ZoneInfo(coll.timezone)
    if not coll.schedule.enabled:
        logs.log("INFO", "SCHEDULE_OFF", store=store_key)
        return Exit.OK
    if coll.bounded():
        raise CommandError(
            Exit.CONFIG,
            f"{store_key}: a scheduled run collects the store's full scope, and the configuration narrows it "
            f"({', '.join(coll.pilot_budgets())}): pilot budgets belong on a manual run",
        )
    with ctx.factory() as s:
        row = s.scalar(select(Store).where(Store.key == store_key))
    if row is None and _started_today(coll, now):
        sync_config(ctx, "schedule")
        with ctx.factory() as s:
            row = s.scalar(select(Store).where(Store.key == store_key))
    head_day: str | None = None
    if row is not None:
        with ctx.factory() as s:
            waiting = occurrences.register(s, row.id, coll.schedule, tz, now)
            head_day = waiting[0].day if waiting else None
            s.commit()
    if head_day is None:
        done = _done_occurrence(ctx, store_key, coll, now)
        if done is not None:
            return done
        continued = await continue_scheduled(ctx, store_key, coll, now)
        if continued is not None:
            _settle_occurrences(ctx, store_key)
            return continued
        nxt = next_occurrence(coll.schedule, now, tz)
        logs.log(
            "INFO",
            "NOT_DUE",
            store=store_key,
            local_now=now.astimezone(tz).isoformat(),
            next_local_start=nxt.start.isoformat() if nxt else None,
        )
        return Exit.OK
    day = head_day
    with ctx.factory() as s:
        hold = get_hold(s, store_key)
        if hold is not None:
            occurrences.defer(
                occurrences.register(s, _store_row(s, store_key).id, coll.schedule, tz, now),
                f"the store's collection is held: {hold.get('reason') or hold}",
            )
            s.commit()
    if hold is not None:
        logs.log("WARN", "COLLECTION_HELD", store=store_key, occurrence=day, hold=hold)
        return Exit.HELD
    if not daily_window_open(coll, now):
        with ctx.factory() as s:
            occurrences.defer(
                occurrences.register(s, _store_row(s, store_key).id, coll.schedule, tz, now),
                "the daily window is closed: it starts inside the next window",
            )
            s.commit()
        logs.log("INFO", "OCCURRENCE_WAITING", store=store_key, occurrence=day, reason="window closed")
        return Exit.OK
    check_edition(ctx, coll.provider)
    check_key(coll.provider)
    sync_config(ctx, "schedule")
    pipe = ctx.pipeline(store_key)
    resume = False
    with ctx.factory() as s:
        row = _store_row(s, store_key)
        waiting = occurrences.register(s, row.id, coll.schedule, tz, now)
        head = waiting[0]
        occ = occurrences.occurrence_of(head)
        mine = s.scalars(
            select(Run).where(
                Run.store_id == row.id,
                Run.mode == "LIVE",
                Run.trigger == "schedule",
                Run.config_snapshot["occurrence"]["day"].astext == day,
            )
        ).first()
        if mine is not None:
            if mine.status in FINISHED_STATES:
                # A run from before the occurrence had a row: this firing only records it.
                occurrences.started(head, mine.id, mine.started_at or now)
                occurrences.finished(s, row.id, mine.id, now)
                logs.log(
                    "INFO", "OCCURRENCE_DONE", store=store_key, occurrence=day, run=run_summary(pipe, mine)
                )
                code = exit_for(s, mine)
                s.commit()
                return code
            if mine.status in control.ACTIVE and worker_alive(s, row.id, mine.id):
                occurrences.defer(waiting, f"its own run {mine.id} is active in another execution")
                s.commit()
                logs.log("WARN", "STORE_BUSY", store=store_key, run_id=mine.id)
                return Exit.BUSY
            _recover(s, mine)
            occurrences.started(head, mine.id, now)
            s.commit()
            logs.log("INFO", "OCCURRENCE_CONTINUED", store=store_key, occurrence=day, run_id=mine.id)
            run_id, resume = mine.id, True
        else:
            current = control.open_run(s, row.id)
            if (
                current is not None
                and current.status in control.ACTIVE
                and worker_alive(s, row.id, current.id)
            ):
                occurrences.defer(waiting, f"run {current.id} is active: it starts when that run ends")
                s.commit()
                logs.log("WARN", "STORE_BUSY", store=store_key, run_id=current.id, occurrence=day)
                return Exit.BUSY
            if current is not None and current.trigger != "schedule":
                occurrences.defer(
                    waiting, f"manual run {current.id} is unfinished: it starts when that run is finalized"
                )
                s.commit()
                logs.log(
                    "WARN",
                    "MANUAL_RUN_OPEN",
                    store=store_key,
                    run_id=current.id,
                    occurrence=day,
                    message="a manual run is unfinished: resume or finalize it; the occurrence waits",
                )
                return Exit.BUSY
            if current is not None and coll.schedule.on_overlap == "continue":
                # The scheduled run of an earlier occurrence is unfinished: it goes on and this occurrence
                # waits for it, so a run longer than the interval between starts is never cut short and no
                # start is lost (it runs after that run ends).
                was = ((current.config_snapshot or {}).get("occurrence") or {}).get("day")
                _recover(s, current)
                occurrences.defer(waiting, f"the scheduled run of {was} is unfinished ({current.id})")
                event(
                    s,
                    current.id,
                    "INFO",
                    "OCCURRENCE_DEFERRED",
                    f"the occurrence of {day} found the scheduled run of {was} unfinished: that run goes on, "
                    "and this occurrence starts when it ends",
                    {"store": store_key, "occurrence": day, "run_occurrence": was},
                )
                s.commit()
                run_id, resume = current.id, True
            else:
                superseded = None
                if current is not None:
                    _recover(s, current)
                    current.stop_code = StopCode.SUPERSEDED.value
                    current.stop_detail = f"the scheduled run of {day} started"
                    control.prepare_finish(s, current)
                    superseded = current.id
                s.commit()
                if superseded is not None:
                    logs.log("INFO", "RUN_SUPERSEDED", store=store_key, run_id=superseded, occurrence=day)
                    await drive(ctx, store_key, superseded, trigger="finish", resume=True)
                with ctx.factory() as s2:
                    try:
                        run_id = control.create_run(
                            s2,
                            pipe=pipe,
                            store=ctx.config.store(store_key),
                            cfg=coll,
                            trigger="schedule",
                            started_by="schedule",
                            pilot=coll.bounded(),
                            occurrence=occ,
                            edition=ctx.config.collector.edition.name,
                        )
                    except control.StartRefused as exc:
                        raise CommandError(Exit.CONFIG, str(exc)) from None
                    row2 = _store_row(s2, store_key)
                    head2 = occurrences.register(s2, row2.id, coll.schedule, tz, now)[0]
                    occurrences.started(head2, run_id, now)
                    late = occurrences.lateness_minutes(head2, now)
                    if late > coll.start_tolerance_minutes:
                        event(
                            s2,
                            run_id,
                            "WARN",
                            "OCCURRENCE_LATE",
                            f"the occurrence of {day} started {late} minutes after its scheduled start",
                            {"store": store_key, "occurrence": day, "lateness_minutes": late},
                        )
                    s2.commit()
                logs.log("INFO", "RUN_CREATED", run_id=run_id, store=store_key, occurrence=day)
    code = await drive(ctx, store_key, run_id, trigger="schedule", resume=resume)
    _settle_occurrences(ctx, store_key)
    return code


def _started_today(coll: StoreCollection, now: datetime) -> bool:
    """Today's occurrence has reached its start time (a few minutes early counts)."""
    tz = ZoneInfo(coll.timezone)
    occ = occurrence_on(coll.schedule, local_day(now + EARLY_START, tz), tz)
    return occ is not None and occ.start - EARLY_START <= now


def _done_occurrence(ctx: Context, store_key: str, coll: StoreCollection, now: datetime) -> Exit | None:
    """A firing at today's start whose occurrence already has a finished run (a retry, or the second UTC
    firing around a daylight-saving change): the run's exit code, and nothing is requested."""
    occ = due_occurrence(coll, now)
    if occ is None:
        return None
    with ctx.factory() as s:
        row = s.scalar(select(Store).where(Store.key == store_key))
        if row is None:
            return None
        mine = s.scalars(
            select(Run).where(
                Run.store_id == row.id,
                Run.mode == "LIVE",
                Run.trigger == "schedule",
                Run.config_snapshot["occurrence"]["day"].astext == occ.day.isoformat(),
            )
        ).first()
        if mine is None or mine.status not in FINISHED_STATES:
            return None
        pipe = ctx.pipeline(store_key)
        code = exit_for(s, mine)
        refused = auto_publication_refused(s, mine)
        extra: dict[str, Any] = {}
        if refused is not None:
            extra["publication"] = {"automatic": True, "published": False, "refused": refused}
            if code is Exit.OK:
                code = Exit.REJECTED  # 1.6.6: a retry of the firing says again that nothing was published
        logs.log(
            "INFO" if code is Exit.OK else "WARN",
            "OCCURRENCE_DONE",
            store=store_key,
            occurrence=occ.day.isoformat(),
            run=run_summary(pipe, mine),
            exit_code=int(code),
            **extra,
        )
        return code


def auto_publication_refused(s: Session, run: Run) -> str | None:
    """Why the run's automatic publication was refused (release 1.6.6), while the run is still
    unpublished: the last ``PUBLICATION_REFUSED`` event recorded on it; None when there is none or it was
    published since."""
    if run.status != "validated":
        return None
    found = s.scalars(
        select(Event)
        .where(Event.run_id == run.id, Event.code == "PUBLICATION_REFUSED")
        .order_by(Event.ts.desc())
    ).first()
    return None if found is None else str((found.data or {}).get("reason") or found.message)


def _settle_occurrences(ctx: Context, store_key: str) -> None:
    """Record the end of a run the firing executed, when it really finished."""
    with ctx.factory() as s:
        row = s.scalar(select(Store).where(Store.key == store_key))
        if row is None:
            return
        occurrences.settle(s, occurrences.rows_of(s, row.id))
        s.commit()


def schedule_status(ctx: Context, store_key: str) -> dict[str, Any]:
    """The store's scheduled occurrences, backlog, lateness and capacity gap. Reads only: it registers no
    occurrence and requests nothing. A schedule that is off is reported as off."""
    ctx.config.store(store_key)
    coll = ctx.config.collection(store_key)
    tz = ZoneInfo(coll.timezone)
    now = ctx.clock()
    nxt = next_occurrence(coll.schedule, now, tz) if coll.schedule.enabled else None
    out: dict[str, Any] = {
        "store": store_key,
        "now": iso(now),
        "next_local_start": nxt.start.isoformat() if nxt else None,
    }
    with ctx.factory() as s:
        row = s.scalar(select(Store).where(Store.key == store_key))
        if row is None:
            return {**out, "schedule_enabled": coll.schedule.enabled, "occurrences": [], "backlog": 0}
        data = occurrences.status(s, row.id, coll.schedule, tz, now, enabled=coll.schedule.enabled)
        s.rollback()
    return {**out, **data}


# What a replay takes from its source run's snapshot (the settings and the code are the current ones).
REPLAY_SNAPSHOT_KEYS = ("retailer", "collection", "plan", "pilot", "provider", "overrides", "store")


def replay_of(s: Session, source_run_id: str) -> Run | None:
    return s.scalars(
        select(Run).where(
            Run.mode == "REPLAY", Run.config_snapshot["replay"]["source_run"].astext == source_run_id
        )
    ).first()


async def replay_run(ctx: Context, source_run_id: str, actor: str) -> Exit:
    """Read an earlier LIVE run's stored pages again with this code (``collection/replay.py``): a REPLAY run
    with the source's plan and limits, whose records keep the source's observation times and crawl dates. No
    request is made and no key is needed. Never published."""
    from walmart_headless.collection.nodes import Node
    from walmart_headless.core.paths import PARSER_VERSION
    from walmart_headless.core.version import source_version

    with ctx.factory() as s:
        src = s.get(Run, source_run_id)
        if src is None:
            raise CommandError(Exit.CONFIG, f"unknown run {source_run_id}")
        if src.mode != "LIVE":
            raise CommandError(Exit.CONFIG, f"run {src.id} is a {src.mode} run: only LIVE runs are replayed")
        if src.status not in FINISHED_STATES:
            raise CommandError(Exit.BUSY, f"run {src.id} is {src.status}: finish or finalize it first")
        earlier = replay_of(s, src.id)
        if earlier is not None:
            raise CommandError(Exit.CONFIG, f"run {src.id} was already replayed by run {earlier.id}")
        store = s.get(Store, src.store_id)
        assert store is not None
        snap = dict(src.config_snapshot or {})
        coll = dict(snap.get("collection") or {})
        # The replay requests nothing: every product page the source run stored is read again.
        coll["detail"] = {**dict(coll.get("detail") or {}), "max_per_run": None}
        coll["pdp_sample"] = None
        nodes = [Node.from_dict(n) for n in (snap.get("plan") or {}).get("nodes", [])]
        snapshot: dict[str, Any] = {
            **{k: snap[k] for k in REPLAY_SNAPSHOT_KEYS if k in snap},
            "collection": coll,
            "started_by": actor,
            "code": {"version": PARSER_VERSION, **source_version()},
            "replay": {
                "source_run": src.id,
                "source_created_at": iso(src.created_at),
                "source_started_at": iso(src.started_at) if src.started_at else None,
                "source_finished_at": iso(src.finished_at) if src.finished_at else None,
                "source_status": src.status,
                "source_stop_code": src.stop_code,
                "source_code": snap.get("code") or {"version": src.parser_version},
                "source_counts": {
                    k: (src.counts or {}).get(k) for k in ("records_by_status", "verified", "upc_detail")
                },
            },
        }
        pipe = ctx.pipeline(store.key)
        run_id = pipe.create_live_run(s, nodes, trigger="replay", snapshot=snapshot, mode="REPLAY")
        s.commit()
        store_key = store.key
    logs.log("INFO", "RUN_CREATED", run_id=run_id, store=store_key, replay_of=source_run_id)
    return await _execute_replay(ctx, store_key, run_id, source_run_id, resume=False)


async def _execute_replay(
    ctx: Context, store_key: str, run_id: str, source_run_id: str, *, resume: bool
) -> Exit:
    """A replay's execution, first or resumed: its stored pages only, no key and no provider, never the
    after-run path (a replay is never published)."""
    from walmart_headless.collection.replay import ReplayCollector

    pipe = ctx.pipeline(store_key)
    with ctx.factory() as s:
        run = s.get(Run, run_id)
        assert run is not None
        cfg = collection_of(run)
    collector = ReplayCollector(
        pipe,
        run_id,
        config=cfg,
        trigger="replay",
        canary=ctx.config.collector.canary,
        historical=ctx.config.collector.historical,
        clock=ctx.clock,
    )
    try:
        await pipe.execute(run_id, ctx.owner, collector=collector, resume=resume)
    except RunLockHeld as exc:
        raise CommandError(Exit.BUSY, str(exc)) from None
    with ctx.factory() as s:
        run = s.get(Run, run_id)
        assert run is not None
        summary = run_summary(pipe, run)
        code = exit_for(s, run)
        summary["failed_checks"] = failed_gates(s, run.id)
        summary["replay_of"] = source_run_id
    logs.log(
        "INFO" if code is Exit.OK else "WARN", "RUN_FINISHED", store=store_key, exit_code=int(code), **summary
    )
    return code


def _find_run(ctx: Context, run_id: str | None, store_key: str | None) -> tuple[str, str]:
    """(run id, store key) of the named run, or of the store's unfinished run."""
    with ctx.factory() as s:
        if run_id:
            run = s.get(Run, run_id)
            if run is None:
                raise CommandError(Exit.CONFIG, f"unknown run {run_id}")
            store = s.get(Store, run.store_id)
            assert store is not None
            return run.id, store.key
        if not store_key:
            raise CommandError(Exit.CONFIG, "name a run (--run) or a store (--store)")
        row = _store_row(s, store_key)
        current = control.open_run(s, row.id)
        if current is None:
            raise CommandError(Exit.CONFIG, f"{store_key} has no unfinished run")
        return current.id, store_key


async def resume_run(
    ctx: Context, run_id: str | None, store_key: str | None, workers: int | None = None
) -> Exit:
    rid, key = _find_run(ctx, run_id, store_key)
    with ctx.factory() as s:
        hold = get_hold(s, key)
        run = s.get(Run, rid)
        assert run is not None
        _recover(s, run)
        s.commit()
        if run.status != "interrupted":
            raise CommandError(
                Exit.BUSY if run.status in control.ACTIVE else Exit.CONFIG, f"run {rid} is {run.status}"
            )
        source_run = str(((run.config_snapshot or {}).get("replay") or {}).get("source_run") or "")
        if run.mode == "REPLAY":
            # Release 1.5.2: a replay stays a replay. It needs no key and no store release, and it requests
            # nothing, whatever key this machine holds.
            logs.log("INFO", "RUN_EXECUTING", run_id=rid, store=key, trigger="resume", resume=True)
            s.commit()
            return await _execute_replay(ctx, key, rid, source_run, resume=True)
    if hold is not None:
        raise CommandError(Exit.HELD, f"{key} is held: {hold['reason']} (release-hold first)", hold=hold)
    check_edition(ctx, provider_of(run))
    check_key(provider_of(run))
    return await drive(ctx, key, rid, trigger="resume", resume=True, workers=workers)


async def finalize_run(ctx: Context, run_id: str | None, store_key: str | None) -> Exit:
    """Check and export what an unfinished run collected, without collecting more (no provider request)."""
    rid, key = _find_run(ctx, run_id, store_key)
    with ctx.factory() as s:
        run = s.get(Run, rid)
        assert run is not None
        _recover(s, run)
        if run.status in FINISHED_STATES:
            raise CommandError(Exit.CONFIG, f"run {rid} has already finished ({run.status})")
        if run.status in control.ACTIVE and run.status != "queued" and worker_alive(s, run.store_id, rid):
            raise CommandError(Exit.BUSY, f"run {rid} is being collected: use stop")
        if run.stop_code is None:
            run.stop_code, run.stop_detail = StopCode.OPERATOR_STOP.value, "finalized by an operator"
        control.prepare_finish(s, run)
        s.commit()
        source_run = str(((run.config_snapshot or {}).get("replay") or {}).get("source_run") or "")
        if run.mode == "REPLAY":
            return await _execute_replay(ctx, key, rid, source_run, resume=True)
    return await drive(ctx, key, rid, trigger="finish", resume=True)


def stop_run(
    ctx: Context, run_id: str | None, store_key: str | None, reason: str, actor: str
) -> dict[str, Any]:
    rid, _key = _find_run(ctx, run_id, store_key)
    with ctx.factory() as s:
        run = s.get(Run, rid)
        assert run is not None
        try:
            control.request_stop(s, run, actor, reason or "stop requested")
        except control.StartRefused as exc:
            raise CommandError(Exit.CONFIG, str(exc)) from None
        alive = worker_alive(s, run.store_id, rid)
        s.commit()
    return {
        "run_id": rid,
        "stop_requested": True,
        "worker_running": alive,
        "next": "the running execution stops at its next checkpoint and finalizes"
        if alive
        else "no execution is collecting it: run 'walmart-collector finalize'",
    }


def publish(ctx: Context, run_id: str, reason: str | None, actor: str) -> dict[str, Any]:
    with ctx.factory() as s:
        run = s.get(Run, run_id)
        if run is None:
            raise CommandError(Exit.CONFIG, f"unknown run {run_id}")
        store = s.get(Store, run.store_id)
        assert store is not None
        label = ctx.pipeline(store.key).dataset_label(run)
    if label != "complete":
        raise CommandError(
            Exit.REJECTED, f"run {run_id} is a {label} dataset: only complete runs are published"
        )
    try:
        pub = publish_run(
            ctx.factory,
            ctx.storage,
            run_id,
            actor,
            warn_override_reason=reason,
            test_target=ctx.settings.publication.test_target,
        )
    except PublicationRefused as exc:
        raise CommandError(Exit.REJECTED, str(exc)) from None
    return {"run_id": run_id, "publication_id": pub.publication_id, "version": pub.version}


# -- status and exports ---------------------------------------------------------------------------


def status(ctx: Context, store_key: str | None, run_id: str | None, limit: int) -> dict[str, Any]:
    out: dict[str, Any] = {"stores": []}
    with ctx.factory() as s:
        if run_id:
            run = s.get(Run, run_id)
            if run is None:
                raise CommandError(Exit.CONFIG, f"unknown run {run_id}")
            store = s.get(Store, run.store_id)
            assert store is not None
            pipe = ctx.pipeline(store.key) if store.key in {x.key for x in ctx.config.stores.stores} else None
            summary = run_summary(pipe, run)
            summary["worker_running"] = worker_alive(s, run.store_id, run.id)
            lin = lineage.of_run(s, run.id)
            summary["lineage"] = {"lineage": lin.lineage, "basis": lin.basis, "problems": list(lin.problems)}
            summary["statistics"] = segments.run_statistics(s, run.id)
            exports = {
                e.kind: s.get(Artifact, e.artifact_id).key  # type: ignore[union-attr]
                for e in s.scalars(select(ExportRow).where(ExportRow.run_id == run.id))
            }
            return {"run": {**summary, "store": store.key, "exports": exports}}
        for st in ctx.config.stores.stores:
            if store_key and st.key != store_key:
                continue
            row = s.scalar(select(Store).where(Store.key == st.key))
            entry: dict[str, Any] = {
                "store": st.key,
                "in_database": row is not None,
                "hold": get_hold(s, st.key),
            }
            if row is not None:
                pipe = ctx.pipeline(st.key)
                runs = list(
                    s.scalars(
                        select(Run).where(Run.store_id == row.id).order_by(Run.created_at.desc()).limit(limit)
                    )
                )
                entry["runs"] = [
                    {
                        **run_summary(pipe, r),
                        "worker_running": worker_alive(s, row.id, r.id)
                        if r.status in control.ACTIVE
                        else False,
                    }
                    for r in runs
                ]
                pointer = s.get(PublicationPointer, row.id)
                if pointer is not None:
                    pub = s.get(Publication, pointer.publication_id)
                    assert pub is not None
                    entry["published"] = {
                        "run_id": pub.run_id,
                        "version": pointer.version,
                        "published_at": iso(pub.published_at),
                        "latest": latest_key(st.key),
                    }
                else:
                    entry["published"] = None
            out["stores"].append(entry)
        try:
            account = scrapedo_account.status(s)
            s.commit()
            out["provider"] = {
                "key_configured": account["key_configured"],
                "keys": account["keys"],
                "charged_total": account["charged_total"],
                "charged_uncertain": account["charged_uncertain"],
            }
        except Exception as exc:  # the status of the runs is still useful
            out["provider"] = {"error": type(exc).__name__}
    return out


def _published_run(ctx: Context, store_key: str) -> str:
    with ctx.factory() as s:
        row = _store_row(s, store_key)
        pointer = s.get(PublicationPointer, row.id)
        if pointer is None:
            raise CommandError(Exit.CONFIG, f"{store_key} has no published dataset yet")
        pub = s.get(Publication, pointer.publication_id)
        assert pub is not None
        return pub.run_id


def export(ctx: Context, run_id: str | None, store_key: str | None, out_dir: Path) -> dict[str, Any]:
    """Copy a run's export files (by default the store's published dataset) to a local folder, after
    verifying every file against its manifest."""
    rid = run_id or _published_run(ctx, store_key or "")
    with ctx.factory() as s:
        run = s.get(Run, rid)
        if run is None:
            raise CommandError(Exit.CONFIG, f"unknown run {rid}")
        manifest = s.scalar(
            select(Artifact)
            .join(ExportRow, ExportRow.artifact_id == Artifact.id)
            .where(ExportRow.run_id == rid, ExportRow.kind == "manifest")
        )
        if manifest is None:
            raise CommandError(Exit.CONFIG, f"run {rid} has no exports ({run.status})")
        mkey, msha = manifest.key, manifest.sha256
    problems = verify_manifest(ctx.storage, mkey, msha)
    if problems:
        raise CommandError(Exit.REJECTED, "the exports do not verify: " + "; ".join(problems))
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = mkey.rsplit("/", 1)[0]
    written = []
    import json

    body = json.loads(ctx.storage.get_bytes(mkey))
    for name in (*manifest_files(body), "manifest.json"):
        data = ctx.storage.get_bytes(f"{prefix}/{name}")
        (out_dir / name).write_bytes(data)
        written.append(name)
    return {"run_id": rid, "out": str(out_dir), "files": written, "verified": True}


def validate_export(
    ctx: Context | None, products: Path | None, run_id: str | None
) -> tuple[Exit, dict[str, Any]]:
    """The 22-field contract of a products file; for a run, also its manifest and an independent check of
    every record against the run's stored pages (offline: no provider request)."""
    if run_id is None:
        if products is None:
            raise CommandError(Exit.CONFIG, "name a products file (--file) or a run (--run)")
        report = contract.check(products)
        return (Exit.OK if report["passed"] else Exit.REJECTED), {"contract": report}
    assert ctx is not None
    with ctx.factory() as s:
        run = s.get(Run, run_id)
        if run is None:
            raise CommandError(Exit.CONFIG, f"unknown run {run_id}")
        store = s.get(Store, run.store_id)
        assert store is not None
        manifest = s.scalar(
            select(Artifact)
            .join(ExportRow, ExportRow.artifact_id == Artifact.id)
            .where(ExportRow.run_id == run_id, ExportRow.kind == "manifest")
        )
        rows = list(s.scalars(select(RecordRow).where(RecordRow.run_id == run_id)))
        # A carried-forward record was observed by an earlier run: it is checked against that run's pages.
        source_runs = {run_id} | {
            str(((r.provenance or {}).get("historical") or {}).get("run_id") or "")
            for r in rows
            if r.status == "historical"
        } - {""}
        pages = [
            s.get(Artifact, pf.dom_artifact_id).key  # type: ignore[union-attr]
            for pf in s.scalars(select(PageFetch).where(PageFetch.run_id.in_(sorted(source_runs))))
            if pf.dom_artifact_id
        ]
        statuses = Counter(r.status for r in rows)
        location_id = store.location_id
    if manifest is None:
        raise CommandError(Exit.CONFIG, f"run {run_id} has no exports")
    problems = verify_manifest(ctx.storage, manifest.key, manifest.sha256)
    prefix = manifest.key.rsplit("/", 1)[0]
    with tempfile.TemporaryDirectory(prefix="walmart-validate-") as tmp:
        root = Path(tmp)
        products_path = root / "products.json"
        products_path.write_bytes(ctx.storage.get_bytes(f"{prefix}/products.json"))
        report = contract.check(products_path)
        pages_dir = root / "pages"
        pages_dir.mkdir()
        for i, key in enumerate(pages):
            data = ctx.storage.get_bytes(key)
            (pages_dir / f"{i:04d}.html.gz").write_bytes(
                data if data[:2] == b"\x1f\x8b" else gzip.compress(data)
            )
        import json

        records = json.loads(products_path.read_text("utf-8"))
        sources = source_check.check(records, pages_dir, location_id)
        shutil.rmtree(pages_dir, ignore_errors=True)
    ok = (
        not problems
        and report["passed"]
        and sources["summary"]["mismatch"] == 0
        and sources["summary"]["unverified"] == 0
    )
    return (Exit.OK if ok else Exit.REJECTED), {
        "run_id": run_id,
        "manifest": {"key": manifest.key, "problems": problems},
        "contract": report,
        "source_check": {
            **{k: sources[k] for k in ("pages_read", "items_in_pages", "summary", "mismatched_fields")},
            "runs_whose_pages_were_read": sorted(source_runs),
        },
        "records_by_status": dict(statuses),
    }


def provider_balance(ctx: Context, actor: str, provider: str = "scrapedo") -> tuple[Exit, dict[str, Any]]:
    """The key's balance read from Scrape.do's ``/info`` (free; no page is requested), or for the Oxylabs
    Web API (no balance or usage API) the operator's ceiling and the ledger's record."""
    check_edition(ctx, provider)
    check_key(provider)
    if provider == "oxylabs":
        key = oxylabs.load_key()
        with ctx.factory() as s:
            room, reading = oxylabs.ceiling_room(s)
            task = budget.get(s)
            spent = budget.spent(s, task.get("since"))
        return Exit.OK, {
            "provider": "oxylabs",
            "api": "Oxylabs Web API",
            "key_fingerprint": scrapedo_account.masked(key.fingerprint) if key else None,
            "balance_api": "none: Oxylabs documents no balance or usage endpoint; the ledger is the record",
            "ceiling": reading or None,
            "room_submissions": room,
            "task_budget": {**task, "spent": spent} if task else None,
        }
    with ctx.factory() as s:
        out = scrapedo_account.refresh(s, actor)
        s.commit()
    errors = out.get("errors") or {}
    code = Exit.OK
    if errors:
        code = Exit.CREDENTIALS if any("401" in e or "403" in e for e in errors.values()) else Exit.UNEXPECTED
    return code, {
        "provider": "scrape.do",
        "keys": out["keys"],
        "errors": errors,
        "charged_total_recorded": out["charged_total"],
    }


def set_ceiling(
    ctx: Context,
    credits: float | None,
    basis: str,
    actor: str,
    *,
    provider: str = "scrapedo",
    usd_per_credit: float | None = None,
    submissions: int | None = None,
    usd: float | None = None,
    minutes: float | None = None,
    usd_per_result: float | None = None,
) -> dict[str, Any]:
    """A provider's spending ceiling across every run and process from now on (no request may cross it):
    Scrape.do credits, or for the Oxylabs Web API submissions and/or US dollars within a time window."""
    if not basis.strip():
        raise CommandError(Exit.CONFIG, "a basis (why this ceiling) is required")
    with ctx.factory() as s:
        if provider == "oxylabs":
            try:
                value = oxylabs.set_ceiling(
                    s,
                    max_submissions=submissions,
                    max_usd=usd,
                    max_minutes=minutes,
                    usd_per_result=usd_per_result,
                    basis=basis,
                    actor=actor,
                )
            except ValueError as exc:
                raise CommandError(Exit.CONFIG, str(exc)) from None
            s.add(AuditLog(actor=actor, action="oxylabs_ceiling", target="oxylabs", data=value))
        else:
            if credits is None:
                raise CommandError(Exit.CONFIG, "a Scrape.do ceiling needs --credits")
            value = scrapedo_account.save_ceiling(s, credits, basis, actor, usd_per_credit=usd_per_credit)
        s.commit()
    return {"provider": provider, **value}


def set_budget(ctx: Context, usd: float, basis: str, actor: str) -> dict[str, Any]:
    """The task's money budget across every provider from now on (reserved before each request)."""
    if not basis.strip():
        raise CommandError(Exit.CONFIG, "a basis (why this budget) is required")
    with ctx.factory() as s:
        try:
            value = budget.put(s, usd, basis, actor)
        except ValueError as exc:
            raise CommandError(Exit.CONFIG, str(exc)) from None
        s.add(AuditLog(actor=actor, action="task_budget", target="all providers", data=value))
        s.commit()
    return value


def attest_lineage(ctx: Context, run_id: str, reason: str, evidence: str, actor: str) -> dict[str, Any]:
    """An operator's attestation that a LIVE run made before release 1.3.1 (which records no lineage)
    read its pages from the network: its observations may then serve later network runs
    (``acquisition/lineage.py``). Recorded in the audit log with its reason and evidence."""
    with ctx.factory() as s:
        try:
            value = lineage.attest(s, run_id, actor=actor, reason=reason, evidence=evidence)
        except lineage.LineageRefused as exc:
            raise CommandError(Exit.CONFIG, str(exc)) from None
        s.commit()
    logs.log("INFO", "LINEAGE_ATTESTED", run_id=run_id, reason=reason.strip())
    return value


def follow_ups(ctx: Context, store_key: str, state: str | None, kind: str | None) -> dict[str, Any]:
    """The store's follow-up queue (collection/follow_queue.py): its counts and its candidates, the pending
    ones by default, oldest first."""
    with ctx.factory() as s:
        store = _store_row(s, store_key)
        q = select(FollowUpItem).where(FollowUpItem.store_id == store.id)
        if state is not None:
            q = q.where(FollowUpItem.state == state)
        if kind is not None:
            q = q.where(FollowUpItem.kind == kind)
        rows = list(
            s.scalars(q.order_by(FollowUpItem.first_seen_at, FollowUpItem.kind, FollowUpItem.item_id))
        )
        return {
            "store": store_key,
            **follow_queue.counts(s, store_id=store.id),
            "listed": {"state": state or "all", "kind": kind or "all", "rows": len(rows)},
            "candidates": [follow_queue.as_dict(r) for r in rows],
        }


def run_field_dispositions(ctx: Context, run_id: str, csv_file: Path | None) -> dict[str, Any]:
    """Why each exported product's UPC and size are filled or empty in the run (publishing/dispositions.py);
    reads only. The table goes to ``csv_file`` when given."""
    with ctx.factory() as s:
        if s.get(Run, run_id) is None:
            raise CommandError(Exit.CONFIG, f"unknown run {run_id}")
        rows = field_dispositions(s, run_id)
    if csv_file is not None:
        csv_file.write_bytes(dispositions.csv_bytes(rows))
    return {"run_id": run_id, "counts": dispositions.counts(rows), "rows": rows}


def import_detail_captures(ctx: Context, store_key: str, index: Path) -> dict[str, Any]:
    """Load saved product pages for later runs to reuse (collection/detail_captures.py); requests nothing."""
    try:
        entries = json.loads(index.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise CommandError(Exit.CONFIG, f"cannot read the index {index}: {exc}") from None
    if not isinstance(entries, list):
        raise CommandError(Exit.CONFIG, f"the index {index} must be a JSON list")
    with ctx.factory() as s:
        store = _store_row(s, store_key)
        try:
            out = detail_captures.load(s, store.id, entries, index.parent)
        except ValueError as exc:
            raise CommandError(Exit.CONFIG, str(exc)) from None
        s.commit()
    logs.log("INFO", "DETAIL_CAPTURES_LOADED", store=store_key, **out["counts"])
    return {"store": store_key, "entries": len(entries), **out}


def coverage_report(ctx: Context, run_id: str, out_dir: Path | None) -> dict[str, Any]:
    """The run's coverage reconciliation (one row per scope unit) and its follow-up outcomes; written as
    CSV and JSON to ``out_dir`` when given."""
    with ctx.factory() as s:
        try:
            data = reconcile.reconcile(s, run_id)
        except ValueError as exc:
            raise CommandError(Exit.CONFIG, str(exc)) from None
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        write_json(out_dir / f"coverage_reconciliation_{run_id}.json", data)
        (out_dir / f"coverage_reconciliation_{run_id}.csv").write_bytes(
            reconcile.as_csv(data["rows"]).encode("utf-8")
        )
        (out_dir / f"follow_up_outcomes_{run_id}.csv").write_bytes(
            reconcile.as_csv(data["follow_ups"], reconcile.FOLLOW_COLUMNS).encode("utf-8")
        )
    return {k: v for k, v in data.items() if k not in ("rows", "follow_ups")} | {
        "follow_up_outcomes": len(data["follow_ups"]),
        "written_to": str(out_dir) if out_dir is not None else None,
    }


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(dumps_bytes(data))
