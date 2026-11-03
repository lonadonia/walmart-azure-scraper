"""Run pipeline on the task runner: preflight → pages → follow-up → assemble → validate → export.

The collector (:class:`walmart_headless.collection.walmart.WalmartCollector`) supplies the live handlers;
this module creates runs, executes them under the store lock (one execution per store at a time, with one
or more workers), and writes the exports.
"""

from __future__ import annotations

import asyncio
import hashlib
from collections import Counter
from collections.abc import Iterator, Sequence
from typing import Any

from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from walmart_headless.assembly.private_label import PrivateLabelDetector
from walmart_headless.core.findings import DataMode
from walmart_headless.core.paths import PARSER_VERSION
from walmart_headless.core.schema import ordered_record
from walmart_headless.core.settings import PrivateLabelConfig, Settings, StoreConfig
from walmart_headless.core.timeutil import utcnow
from walmart_headless.db import queue
from walmart_headless.db.locks import StoreRunLock
from walmart_headless.db.models import (
    Artifact,
    CategorySource,
    MembershipRow,
    OfferObservationRow,
    PageFetch,
    ProductObservation,
    RecordRow,
    Run,
    Store,
    Task,
)
from walmart_headless.publishing.exports import record_sha256, sort_records, write_exports
from walmart_headless.publishing.supporting_log import (
    EXPORTED_STATUSES,
    RECORD_SOURCES,
    field_dispositions,
    record_map,
    supporting_log,
)
from walmart_headless.storage.base import StorageAdapter
from walmart_headless.worker.runner import Worker, WorkerGroup, WorkerResult
from walmart_headless.worker.runs import create_run, event, register_exports, transition

STAGES = ("preflight", "listing_node", "follow_up", "assemble", "validate", "export")
CARRIED_STATUS = "historical"  # a record carried forward from an earlier run (collection/retention.py)
FINISHED_STATES = frozenset({"validated", "rejected", "published", "cancelled"})
PRIORITY = {
    "preflight": 10,
    "listing_node": 50,
    "follow_up": 60,
    "assemble": 80,
    "validate": 90,
    "export": 95,
}
FOLLOW_UPS = ("sponsored", "variants")  # the follow-up tasks of each kind come after every listing task


def _named_fetches(value: Any) -> Iterator[str]:
    """The page fetch ids a record's provenance names (``fetch_id``, ``page_fetch_id``), at any depth."""
    if isinstance(value, dict):
        for k, v in value.items():
            if k in ("fetch_id", "page_fetch_id") and isinstance(v, str):
                yield v
            else:
                yield from _named_fetches(v)
    elif isinstance(value, list):
        for v in value:
            yield from _named_fetches(v)


class Pipeline:
    def __init__(
        self,
        engine: Engine,
        storage: StorageAdapter,
        settings: Settings,
        store: StoreConfig,
        private_label: PrivateLabelConfig,
    ):
        self.engine = engine
        self.factory = sessionmaker(engine, expire_on_commit=False)
        self.storage = storage
        self.settings = settings
        self.store_cfg = store
        self.detector = PrivateLabelDetector(private_label, settings.records.store_brand_positive_value)

    # -- run setup ---------------------------------------------------------------------------------

    def create_live_run(
        self,
        s: Session,
        nodes: Sequence[Any],
        *,
        trigger: str,
        snapshot: dict[str, Any],
        mode: str = DataMode.LIVE.value,
        follow_shards: int = 1,
    ) -> str:
        """A LIVE run over planned pages (``walmart_headless.collection.nodes.Node``): a preflight
        (robots.txt and the store check), one listing task per category row, then assemble, validate and
        export. ``snapshot`` (collection settings, plan, who started it, the schedule occurrence, the code)
        is recorded with the run. ``mode`` REPLAY: the same tasks over an earlier run's stored pages
        (``collection/replay.py``). ``follow_shards``: the follow-up tasks per kind, one per worker of the
        run, each reading its own share of the candidates. The caller commits."""
        if not nodes:
            raise ValueError("no page to collect")
        store = s.scalar(select(Store).where(Store.key == self.store_cfg.key))
        if store is None:
            raise ValueError(f"store {self.store_cfg.key} is not in the database (run sync-config)")
        run = create_run(s, store, self.settings, mode=mode, trigger=trigger)
        run.config_snapshot = {**run.config_snapshot, **snapshot}
        queue.enqueue(
            s, run.id, "preflight", f"{run.id}/preflight", priority=PRIORITY["preflight"], cursor={}
        )
        for i, node in enumerate(nodes):
            queue.enqueue(
                s,
                run.id,
                "listing_node",
                f"{run.id}/node/{i:04d}-{node.taxonomy_id}",
                priority=PRIORITY["listing_node"],
                category_source_id=node.category_source_id,
                taxonomy_id=node.taxonomy_id[:10],
                cursor={"node": node.as_dict(), "steps_done": 0, "seen": [], "status": "IN_PROGRESS"},
            )
        for name in FOLLOW_UPS:
            for i in range(follow_shards):
                queue.enqueue(
                    s,
                    run.id,
                    "follow_up",
                    f"{run.id}/follow/{name}" + (f"/{i}" if follow_shards > 1 else ""),
                    priority=PRIORITY["follow_up"],
                    cursor={
                        "follow": name,
                        "done": [],
                        **({"shard": i, "shards": follow_shards} if follow_shards > 1 else {}),
                    },
                )
        for kind in ("assemble", "validate", "export"):
            queue.enqueue(s, run.id, kind, f"{run.id}/{kind}", priority=PRIORITY[kind], cursor={})
        return run.id

    def prefix(self, run_id: str) -> str:
        return f"runs/{self.store_cfg.key}/{run_id}"

    async def execute(
        self, run_id: str, owner: str, *, collector: Any, resume: bool = False, workers: int = 1
    ) -> str:
        """Run (or, with ``resume``, continue) a run under the store lock, with ``workers`` workers.

        A paused (``interrupted``) run only continues when explicitly resumed, and a finished or
        cancelled run is never restarted. Tasks leased by a worker that died are reclaimed with their
        checkpoints once the lock is held (the lock proves no other worker is alive).

        The collector's ``begin()`` may refuse to start (no key, no credits, a limit already reached): the
        run then waits, ``interrupted``, with the reason. Its ``end()`` always runs, so the provider
        session is closed and the collection segment recorded whatever happens, including a termination
        signal (the run is then left ``interrupted`` with ``TERMINATED``, resumable from its checkpoint).
        """
        with self.factory() as s:
            run = s.get(Run, run_id)
            assert run is not None
            store_id = run.store_id
            if run.status in FINISHED_STATES or (run.status == "interrupted" and not resume):
                return run.status
        lock = StoreRunLock(self.engine, store_id, run_id, owner).acquire()
        try:
            with self.factory() as s:
                run = s.get(Run, run_id)
                assert run is not None
                if run.status in FINISHED_STATES or (run.status == "interrupted" and not resume):
                    return run.status
                if run.status == "queued":
                    transition(s, run_id, "preflight")
                elif run.status == "interrupted":
                    transition(s, run_id, "running")
                run.resume_requested = False
                reclaimed = queue.reclaim_orphans(s, run_id)
                if reclaimed:
                    event(
                        s,
                        run_id,
                        "WARN",
                        "TASK_LEASE_RECLAIMED",
                        f"{reclaimed} task(s) left by a stopped worker resume from their checkpoints",
                    )
                s.commit()
            handlers = collector.handlers()
            try:
                refused = await collector.begin()
                if refused is not None:
                    return self._refuse_start(run_id, *refused)
                if workers > 1:
                    result = await self._run_crew(run_id, owner, collector, workers)
                else:
                    worker = Worker(self.factory, run_id, owner, handlers, self.settings, self.storage)
                    result = await worker.run()
                    # A task waits for its retry time (backoff or a 429 pause): keep the store lock and
                    # wait, so an unattended run continues on its own instead of stopping half-way.
                    while result.outcome == "waiting" and await self._wait_for_retry(run_id):
                        result = await worker.run()
            except asyncio.CancelledError:
                detail = "the collector received a termination signal during the run"
                await collector.end("TERMINATED", detail)
                self._interrupt(run_id, "TERMINATED", detail)
                raise
            finally:
                await collector.end()
            with self.factory() as s:
                status = s.get(Run, run_id).status  # type: ignore[union-attr]
                if result.outcome in ("aborted",) and status in ("preflight", "running"):
                    transition(s, run_id, "rejected")
                    s.commit()
                elif result.outcome == "idle" and status in ("preflight", "running", "validating"):
                    # Every task is terminal but the run never reached a final state: a task failed
                    # before validation, or exports could not be prepared. Never publishable.
                    transition(s, run_id, "rejected")
                    reason = (
                        "exports could not be prepared"
                        if status == "validating"
                        else "a task failed before the run could be validated"
                    )
                    event(s, run_id, "WARN", "RUN_REJECTED", reason)
                    s.commit()
                return s.get(Run, run_id).status  # type: ignore[union-attr]
        finally:
            lock.release()

    async def _run_crew(self, run_id: str, owner: str, collector: Any, n: int) -> WorkerResult:
        """``n`` workers in this process, each with its own collector of ``collector``'s crew (one
        segment). The run's pause or cancellation is applied once every worker has stopped."""
        members = [collector] + [collector.sibling(i) for i in range(1, n)]
        group = WorkerGroup(n)
        collector.crew.workers = group
        workers = [
            Worker(
                self.factory,
                run_id,
                f"{owner}:w{i}",
                m.handlers(),
                self.settings,
                self.storage,
                group=group,
            )
            for i, m in enumerate(members)
        ]
        with self.factory() as s:
            event(
                s,
                run_id,
                "INFO",
                "WORKERS_STARTED",
                f"{n} workers in one process (each with its own provider session and store check)",
                {"workers": [w.owner for w in workers], "limiter": collector.segment_stats()["limiter"]},
            )
            s.commit()
        try:
            while True:
                group.stopping = None
                results = await self._all(workers)
                for m, w in zip(members, workers, strict=True):
                    m.tasks_done = w.tasks_done
                outcomes = [r.outcome for r in results]
                with self.factory() as s:
                    flags = s.execute(
                        select(Run.cancel_requested, Run.pause_requested).where(Run.id == run_id)
                    ).one()
                if "aborted" in outcomes:
                    workers[0]._skip_pending("run stopped by another worker's stop")
                    return WorkerResult("aborted", sum(r.processed for r in results), results[-1].states)
                if flags[0]:
                    workers[0].apply_cancel()
                    return workers[0]._result("cancelled", sum(r.processed for r in results))
                if flags[1] or "paused" in outcomes:
                    workers[0].apply_pause()
                    return workers[0]._result("paused", sum(r.processed for r in results))
                if all(o == "idle" for o in outcomes):
                    return workers[0]._result("idle", sum(r.processed for r in results))
                if not await self._wait_for_retry(run_id):
                    return workers[0]._result("waiting", sum(r.processed for r in results))
        finally:
            for m in members[1:]:
                await m.close_session()
            collector.crew.workers = None

    @staticmethod
    async def _all(workers: list[Worker]) -> list[WorkerResult]:
        """Every worker to its end; the first failure (or a cancellation) cancels the others and is raised
        as itself."""
        tasks = [asyncio.create_task(w.run(), name=w.owner) for w in workers]
        try:
            await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
            for t in tasks:
                if t.done() and not t.cancelled() and t.exception() is not None:
                    raise t.exception()  # type: ignore[misc]
            return [t.result() for t in tasks]
        finally:
            for t in tasks:
                if not t.done():
                    t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

    def _refuse_start(self, run_id: str, code: str, detail: str) -> str:
        """The collector would not start (no key, no credits, a limit reached): the run waits."""
        with self.factory() as s:
            run = s.get(Run, run_id)
            assert run is not None
            run.stop_code, run.stop_detail = code, detail[:2000]
            if run.status in ("preflight", "running"):
                transition(s, run_id, "interrupted")
            event(s, run_id, "WARN", "RUN_NOT_STARTED", detail[:500], {"stop_code": code})
            s.commit()
            return run.status

    def _interrupt(self, run_id: str, code: str, detail: str) -> None:
        """Leave a live run resumable when its worker is stopped from outside (a termination signal)."""
        with self.factory() as s:
            run = s.get(Run, run_id)
            if run is None or run.status not in ("preflight", "running"):
                return
            queue.reclaim_orphans(s, run_id)
            run.stop_code, run.stop_detail = code, detail
            run.pause_requested = False
            transition(s, run_id, "interrupted")
            event(s, run_id, "WARN", "RUN_INTERRUPTED", detail, {"stop_code": code})
            s.commit()

    async def _wait_for_retry(self, run_id: str) -> bool:
        """Sleep until the run's earliest ``retry_wait`` task is due; wake early for a stop request.

        Returns False when no task is waiting for a retry (nothing to wait for)."""
        with self.factory() as s:
            due = s.scalar(
                select(func.min(Task.not_before)).where(Task.run_id == run_id, Task.state == "retry_wait")
            )
        if due is None:
            return False
        remaining = (due - utcnow()).total_seconds()
        while remaining > 0:
            with self.factory() as s:
                stop = s.execute(
                    select(Run.cancel_requested, Run.pause_requested).where(Run.id == run_id)
                ).one()
            if stop[0] or stop[1]:
                break  # the worker applies the stop at its loop head
            await asyncio.sleep(min(1.0, remaining))
            remaining -= 1.0
        return True

    # -- helpers -----------------------------------------------------------------------------------

    def integrity(self, s: Session, run_id: str) -> tuple[bool, bool, bool]:
        """(acquisition tasks terminal, artifact hashes verify, record hashes verify) for G13. Every stored
        page of the run must match its recorded hash. A request that brought no page (the provider failed it
        after its retries) stores none: it has nothing to verify, and fails the check only when an
        observation or a record of the run names it as a source (release 1.4.1; release 1.4.0 rejected a
        complete run for one product page the provider never brought)."""
        acq = ("preflight", "listing_node")
        open_task = s.scalars(
            select(Task).where(
                Task.run_id == run_id, Task.kind.in_(acq), Task.state.not_in(tuple(queue.TERMINAL_STATES))
            )
        ).first()
        records = list(s.scalars(select(RecordRow).where(RecordRow.run_id == run_id)))
        named = {
            *s.scalars(select(ProductObservation.page_fetch_id).where(ProductObservation.run_id == run_id)),
            *s.scalars(select(OfferObservationRow.page_fetch_id).where(OfferObservationRow.run_id == run_id)),
            *(f for r in records for f in _named_fetches(r.provenance)),
        }
        artifacts_ok = True
        for pf in s.scalars(select(PageFetch).where(PageFetch.run_id == run_id)):
            if pf.dom_artifact_id is None:
                artifacts_ok = artifacts_ok and pf.id not in named
                continue
            art = s.get(Artifact, pf.dom_artifact_id)
            if art is None:
                artifacts_ok = False
                continue
            try:
                data = self.storage.get_bytes(art.key)
            except KeyError:
                artifacts_ok = False
                continue
            artifacts_ok = artifacts_ok and hashlib.sha256(data).hexdigest() == art.sha256
        records_ok = all(record_sha256(ordered_record(r.record)) == r.record_sha256 for r in records)
        return open_task is None, artifacts_ok, records_ok

    # -- export ------------------------------------------------------------------------------------

    async def h_export(self, ctx: Any) -> dict[str, Any]:
        with ctx.session() as s:
            run = s.get(Run, ctx.run_id)
            assert run is not None
            ex = self.write_run_exports(s, run)
            event(
                s,
                ctx.run_id,
                "INFO",
                "EXPORTS_STAGED",
                ex.manifest.key,
                {"records": ex.manifest_body["record_count"]},
            )
            final = (run.counts or {}).get("outcome", "rejected")
            if run.status == "validating":
                transition(s, ctx.run_id, final)  # records RUN_VALIDATED or RUN_REJECTED itself
            s.commit()
        return {**ctx.cursor, "manifest": ex.manifest.key}

    def dataset_label(self, run: Run) -> str:
        """``complete`` (every planned page collected, checks passed), ``pilot`` (bounded by a limit),
        or ``partial`` (stopped early or checks failed). Only a complete, validated run is published."""
        counts = run.counts or {}
        if (run.config_snapshot or {}).get("pilot"):
            return "pilot"
        if counts.get("collection_complete") and counts.get("outcome") == "validated":
            return "complete"
        return "partial"

    def write_run_exports(self, s: Session, run: Run, prefix: str | None = None) -> Any:
        """The run's export files (products JSON and CSV with the 22 fields, memberships, offers, the
        supporting log, the validation report) and its manifest, under ``runs/<store>/<run>/exports/``
        (or ``prefix``)."""
        recs = list(s.scalars(select(RecordRow).where(RecordRow.run_id == run.id).order_by(RecordRow.upc)))
        retailer = s.scalar(select(Store.retailer).where(Store.id == run.store_id)) or "walmart"
        csv_order = {
            c.category_name: c.csv_row_index
            for c in s.scalars(select(CategorySource).where(CategorySource.retailer == retailer))
        }
        exported = sort_records(
            [ordered_record(r.record) for r in recs if r.status in EXPORTED_STATUSES], csv_order
        )
        # Observed by this run itself (any of its segments); the other exported records are carried forward.
        fresh = sort_records(
            [
                ordered_record(r.record)
                for r in recs
                if r.status in EXPORTED_STATUSES and r.status != CARRIED_STATUS
            ],
            csv_order,
        )
        keys = [r.upc for r in recs if r.status in EXPORTED_STATUSES]
        # The offers of the page each record is kept from (release 1.3.1: a record decided again from a later
        # tile of the run holds that tile's offers; the earlier tile's stay in the database with its state).
        kept_from = {
            (o.upc, o.page_fetch_id)
            for o in s.scalars(
                select(ProductObservation).where(
                    ProductObservation.run_id == run.id, ProductObservation.source.in_(RECORD_SOURCES)
                )
            )
        }
        # A total order (memberships in page order, offers by product, page and content), so the same rows
        # always give the same bytes: the database's own order is neither defined nor stable.
        offers = [
            {
                "upc": o.upc,
                "page_fetch_id": o.page_fetch_id,
                "source": o.source,
                "tag": o.tag,
                "text": o.description,
                "expiry_text": o.expiry_text,
                "requires_clip": o.requires_clip,
                "kind": o.kind,
                "explicit_price": o.explicit_price,
                "modalities": o.modalities,
                "flags": o.flags,
            }
            for o in s.scalars(
                select(OfferObservationRow)
                .where(OfferObservationRow.run_id == run.id)
                .order_by(
                    OfferObservationRow.upc,
                    OfferObservationRow.page_fetch_id,
                    OfferObservationRow.source,
                    OfferObservationRow.kind,
                    OfferObservationRow.tag,
                    OfferObservationRow.description,
                    OfferObservationRow.expiry_text,
                    OfferObservationRow.explicit_price,
                    OfferObservationRow.id,
                )
            )
            if (o.upc, o.page_fetch_id) in kept_from
        ]
        report = {
            "run_id": run.id,
            "status": (run.counts or {}).get("outcome", run.status),
            "dataset": self.dataset_label(run),
            "counts": run.counts,
            "excluded_by_reason": dict(sorted(Counter(x for r in recs for x in r.reasons).items())),
            # By product identity (the UPC, or Walmart's own item ID where no UPC is shown).
            "duplicates": len(keys) - len(set(keys)),
        }
        ex = write_exports(
            self.storage,
            store_key=self.store_cfg.key,
            run_id=run.id,
            mode=run.mode,
            products=exported,
            memberships=[
                {
                    "key": m.upc,  # product identity (UPC, or Walmart's own item ID)
                    "category_source_id": m.category_source_id,
                    "listing": m.taxonomy_id,
                    "page": m.page_offset,
                    "position": m.position,
                    "via": m.via,
                }
                for m in s.scalars(
                    select(MembershipRow)
                    .where(MembershipRow.run_id == run.id)
                    .order_by(
                        MembershipRow.category_source_id,
                        MembershipRow.taxonomy_id,
                        MembershipRow.coupon_id,
                        MembershipRow.page_offset,
                        MembershipRow.position,
                        MembershipRow.upc,
                        MembershipRow.via,
                        MembershipRow.id,
                    )
                )
            ],
            offers=offers,
            provenance=supporting_log(s, run.id),
            validation_report=report,
            config_snapshot=run.config_snapshot,
            versions={"collector": PARSER_VERSION},
            site_version=run.site_version,
            dataset=self.dataset_label(run),
            prefix=prefix,
            fresh_products=fresh,
            record_map=record_map(s, run.id),
            field_dispositions=field_dispositions(s, run.id),
        )
        register_exports(s, run.id, run.mode, ex)
        return ex
