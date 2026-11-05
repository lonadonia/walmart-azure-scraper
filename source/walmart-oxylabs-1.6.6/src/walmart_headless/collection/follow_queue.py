"""The store's follow-up queue across runs (``follow_up_queue``, revision 0004; see
:class:`walmart_headless.db.models.FollowUpItem`).

A run's follow-up task (``WalmartCollector.follow_up``) notes every candidate the run names
(:func:`note_seen`), adds the store's candidates that earlier runs of the same lineage left pending on a
listing this run read (:func:`waiting`), and reads them in :func:`ordered` order: the configured seeds, then
the candidates no run has read to a decision, the longest-waiting first (an earlier run's before the run's
own), then those whose page failed before, then those read to a decision before and named again. Each
outcome is written back (:func:`record_outcome`): included, duplicate and excluded resolve the candidate;
not attempted and inaccessible keep it pending, so a pilot budget, a pause or a failed page never drops one
for good. A replay run neither notes nor reads the queue (it requests nothing).
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from walmart_headless.core.timeutil import iso
from walmart_headless.db.models import FollowUpItem

PENDING, RESOLVED = "pending", "resolved"
# Outcomes that decide a candidate from its own page (or its own result tile); the others keep it pending.
RESOLVING = frozenset({"included", "duplicate", "excluded"})

Key = tuple[str, str]  # (kind, item id)


def note_seen(
    s: Session,
    *,
    store_id: str,
    run_id: str,
    lineage: str,
    candidates: Iterable[Mapping[str, Any]],
    now: datetime,
) -> dict[Key, FollowUpItem]:
    """Add or update a queue row for each candidate the run names (its link, listing and naming tile, when
    it was last seen and by how many runs); returns the rows by (kind, item id). Idempotent within a run."""
    want = {(str(c["kind"]), str(c["item_id"])): c for c in candidates}
    rows = rows_of(s, store_id=store_id, lineage=lineage, keys=want)
    for key, c in want.items():
        row = rows.get(key)
        if row is None:
            row = FollowUpItem(
                store_id=store_id,
                kind=key[0],
                item_id=key[1],
                lineage=lineage,
                url=c.get("url"),
                listing=c.get("listing"),
                named_by=c.get("named_by") or None,
                option=c.get("option"),
                origin=f"seed: {c['seed']}" if c.get("seed") else "observed",
                first_seen_run=run_id,
                first_seen_at=now,
                last_seen_run=run_id,
                last_seen_at=now,
                runs_seen=1,
                state=PENDING,
                pages_read=0,
            )
            s.add(row)
            rows[key] = row
        elif row.last_seen_run != run_id:
            row.last_seen_run, row.last_seen_at, row.runs_seen = run_id, now, row.runs_seen + 1
            row.url = c.get("url") or row.url
            row.listing = c.get("listing") or row.listing
            row.named_by = c.get("named_by") or row.named_by
            row.option = c.get("option") or row.option
    s.flush()
    return rows


def rows_of(s: Session, *, store_id: str, lineage: str, keys: Iterable[Key]) -> dict[Key, FollowUpItem]:
    wanted = set(keys)
    if not wanted:
        return {}
    found = s.scalars(
        select(FollowUpItem).where(
            FollowUpItem.store_id == store_id,
            FollowUpItem.lineage == lineage,
            FollowUpItem.item_id.in_(sorted({item for _, item in wanted})),
        )
    )
    return {(r.kind, r.item_id): r for r in found if (r.kind, r.item_id) in wanted}


def waiting(
    s: Session, *, store_id: str, lineage: str, kind: str, listings: Iterable[str], exclude: Iterable[str]
) -> list[FollowUpItem]:
    """The store's pending candidates of this kind and lineage on a listing the run read, that the run did
    not name itself (``exclude``: item ids), oldest first."""
    skip = set(exclude)
    q = (
        select(FollowUpItem)
        .where(
            FollowUpItem.store_id == store_id,
            FollowUpItem.lineage == lineage,
            FollowUpItem.kind == kind,
            FollowUpItem.state == PENDING,
            FollowUpItem.listing.in_(sorted(set(listings))),
        )
        .order_by(FollowUpItem.first_seen_at, FollowUpItem.id)
    )
    return [r for r in s.scalars(q) if r.item_id not in skip]


def ordered(candidates: list[dict[str, Any]], rows: Mapping[Key, FollowUpItem]) -> list[dict[str, Any]]:
    """Seeds first; then the candidates no run has read to a decision and whose page was never read, the
    longest-waiting first; then the pending ones whose page failed before; then those read to a decision
    before and named again (each group in the order it was named)."""

    def rank(pair: tuple[int, dict[str, Any]]) -> tuple[int, int, str, int]:
        i, c = pair
        row = rows.get((str(c["kind"]), str(c["item_id"])))
        if row is None or (row.state == PENDING and row.pages_read == 0):
            group = 0
        elif row.state == PENDING:
            group = 1
        else:
            group = 2
        since = iso(row.first_seen_at) if row is not None else "~"
        return (0 if c.get("seed") else 1, group, since, i)

    return [c for _, c in sorted(enumerate(candidates), key=rank)]


def record_outcome(
    s: Session, *, store_id: str, lineage: str, out: Mapping[str, Any], run_id: str, now: datetime
) -> None:
    """Write one candidate's outcome back to its queue row (a page read counts once per read)."""
    row = rows_of(s, store_id=store_id, lineage=lineage, keys=[(str(out["kind"]), str(out["item_id"]))]).get(
        (str(out["kind"]), str(out["item_id"]))
    )
    if row is None:
        return
    status = str(out["status"])
    row.last_status, row.last_reason = status, str(out.get("reason") or "")
    row.last_run, row.last_at = run_id, now
    if out.get("page_fetch_id"):
        row.pages_read += 1
    row.state = RESOLVED if status in RESOLVING else PENDING


def counts(s: Session, *, store_id: str, lineage: str | None = None) -> dict[str, Any]:
    """The store's queue by kind and state, and the last outcomes of the pending candidates."""
    q = select(FollowUpItem).where(FollowUpItem.store_id == store_id)
    if lineage is not None:
        q = q.where(FollowUpItem.lineage == lineage)
    rows = list(s.scalars(q))
    by_state = Counter(f"{r.kind}:{r.state}" for r in rows)
    pending = Counter(f"{r.kind}:{r.last_status or 'never_considered'}" for r in rows if r.state == PENDING)
    return {
        "total": len(rows),
        "by_kind_and_state": dict(sorted(by_state.items())),
        "pending_by_last_outcome": dict(sorted(pending.items())),
    }


def as_dict(row: FollowUpItem) -> dict[str, Any]:
    return {
        "kind": row.kind,
        "item_id": row.item_id,
        "lineage": row.lineage,
        "state": row.state,
        "url": row.url,
        "listing": row.listing,
        "named_by": row.named_by,
        "option": row.option,
        "origin": row.origin,
        "first_seen_run": row.first_seen_run,
        "first_seen_at": iso(row.first_seen_at),
        "last_seen_run": row.last_seen_run,
        "last_seen_at": iso(row.last_seen_at),
        "runs_seen": row.runs_seen,
        "last_status": row.last_status,
        "last_reason": row.last_reason,
        "last_run": row.last_run,
        "last_at": iso(row.last_at) if row.last_at else None,
        "pages_read": row.pages_read,
    }
