"""Creating, stopping and finishing live runs of one store (command line; no interactive console).

A run collects one store. ``create_run`` refuses while the store has an unfinished run (resume or finalize
it first); the database lock taken by the pipeline also refuses a second worker for the same store, so two
executions (two Azure job replicas, or a manual run during a scheduled one) can never collect it at once.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from walmart_headless.acquisition import lineage
from walmart_headless.collection.config import CollectionConfig
from walmart_headless.collection.limits import LIMIT_STOPS, StopCode, stop_text
from walmart_headless.collection.nodes import Node, plan_walmart_nodes
from walmart_headless.collection.schedule import Occurrence
from walmart_headless.core.paths import PARSER_VERSION
from walmart_headless.core.settings import StoreConfig
from walmart_headless.core.version import source_version
from walmart_headless.db import queue
from walmart_headless.db.models import CategorySource, Run, Store, Task
from walmart_headless.worker.runs import event, transition

RETAILER = "walmart"
ACTIVE = ("queued", "preflight", "running", "validating")
OPEN = (*ACTIVE, "interrupted")


class StartRefused(ValueError):
    pass


def plan(session: Session, cfg: CollectionConfig) -> tuple[list[Node], list[dict[str, Any]]]:
    """The pages of the enabled category rows chosen in ``cfg``, in the CSV's order."""
    rows = list(
        session.scalars(
            select(CategorySource)
            .where(CategorySource.enabled, CategorySource.retailer == RETAILER)
            .order_by(CategorySource.csv_row_index)
        )
    )
    sources = [
        {
            "row_index": c.csv_row_index,
            "category_name": c.category_name,
            "id": c.id,
            "url": c.url,
            "kind": c.kind,
            "landing_slug": c.landing_slug,
            "notes": c.notes,
        }
        for c in rows
    ]
    return plan_walmart_nodes(sources, cfg.categories, cfg.subcategories)


def open_run(session: Session, store_id: str) -> Run | None:
    """The store's live run that is not finished (active or paused), if any."""
    return session.scalars(
        select(Run)
        .where(Run.store_id == store_id, Run.mode == "LIVE", Run.status.in_(OPEN))
        .order_by(Run.created_at.desc())
        .limit(1)
    ).first()


def create_run(
    session: Session,
    *,
    pipe: Any,  # walmart_headless.worker.pipeline.Pipeline
    store: StoreConfig,
    cfg: CollectionConfig,
    trigger: str,
    started_by: str,
    pilot: bool,
    occurrence: Occurrence | None = None,
    overrides: dict[str, Any] | None = None,
    edition: str = "core",
) -> str:
    """One queued run of ``store``. Refused when there is nothing to collect or the store already has an
    unfinished live run. ``pilot`` labels an intentionally bounded run: it never counts as a complete
    catalogue. The caller commits."""
    if store.retailer != RETAILER:
        raise StartRefused(f"store {store.key} is not a Walmart store")
    nodes, skipped = plan(session, cfg)
    if not nodes:
        raise StartRefused("the chosen categories have no page to collect (check categories in the config)")
    row = session.scalar(select(Store).where(Store.key == store.key))
    if row is None:
        raise StartRefused(f"store {store.key} is not in the database (run 'walmart-collector sync-config')")
    current = open_run(session, row.id)
    if current is not None:
        raise StartRefused(
            f"{store.key} already has an unfinished run {current.id} ({current.status}): resume or "
            "finalize it first"
        )
    snapshot: dict[str, Any] = {
        "retailer": RETAILER,
        "collection": cfg.model_dump(mode="json"),
        "plan": {"nodes": [n.as_dict() for n in nodes], "skipped": skipped},
        "started_by": started_by,
        "pilot": pilot,
        # The settings that narrow the run, by name (a scope limit, a follow-up or detail page budget).
        "pilot_budgets": cfg.pilot_budgets(),
        # One page provider per run (a change of provider is another run), of the edition that ran it.
        "provider": cfg.provider,
        "edition": edition,
        # The code that collects: the version and the source revision of this build.
        "code": {"version": PARSER_VERSION, **source_version()},
        # Where its pages come from: the network, or a substituted transport (a test, a fault harness).
        "lineage": lineage.current(),
        "overrides": overrides or {},
        "store": {
            "key": store.key,
            "retailer": store.retailer,
            "name": store.expected.display_name,
            "location_id": store.location_id,
            "modality": store.modality.value,
        },
    }
    if occurrence is not None:
        snapshot["occurrence"] = occurrence.as_dict()
    run_id: str = pipe.create_live_run(
        session, nodes, trigger=trigger, snapshot=snapshot, follow_shards=cfg.parallel.workers
    )
    return run_id


def request_stop(session: Session, run: Run, actor: str, detail: str) -> None:
    """Stop collecting for good and finalize with what was collected (checks and export files). A running
    worker stops at its next checkpoint; ``finalize`` (or the next ``resume``) then finishes the run."""
    if run.status not in OPEN:
        raise StartRefused(f"run {run.id} has already finished ({run.status})")
    run.finish_requested = True
    run.resume_requested = False
    kept = run.status == "interrupted" and run.stop_code in {c.value for c in LIMIT_STOPS}
    if not kept:
        run.stop_code, run.stop_detail = StopCode.OPERATOR_STOP.value, detail[:2000]
    if run.status in ("preflight", "running"):
        run.pause_requested = True
    message = (
        f"finalized by {actor}; the run stays stopped by its limit: {stop_text(run.stop_code)}"
        if kept
        else f"{stop_text(StopCode.OPERATOR_STOP.value)}: {detail}"
    )
    event(session, run.id, "INFO", "STOP_REQUESTED", message[:500], {"by": actor, "kept": kept})


def skip_collection_tasks(session: Session, run_id: str, reason: str) -> int:
    res = session.execute(
        update(Task)
        .where(
            Task.run_id == run_id,
            Task.kind.in_(("preflight", "listing_node", "follow_up")),
            Task.state.in_(("pending", "retry_wait", "leased", "running")),
        )
        .values(state="skipped", last_error=reason[:2000], lease_owner=None, lease_expires_at=None)
    )
    return int(res.rowcount or 0)  # type: ignore[attr-defined]


def prepare_finish(session: Session, run: Run) -> None:
    """Skip the collection left and put the run where the pipeline can assemble, check and export."""
    skipped = skip_collection_tasks(session, run.id, f"collection stopped: {run.stop_code or 'finish'}")
    run.finish_requested = False
    run.pause_requested = False
    run.resume_requested = False
    if run.status == "queued":
        transition(session, run.id, "preflight")
        transition(session, run.id, "running")
    event(
        session,
        run.id,
        "INFO",
        "COLLECTION_CLOSED",
        f"{stop_text(run.stop_code) or 'collection stopped'}; {skipped} page(s) left uncollected",
        {"stop_code": run.stop_code, "skipped_tasks": skipped},
    )
    queue.reclaim_orphans(session, run.id)
