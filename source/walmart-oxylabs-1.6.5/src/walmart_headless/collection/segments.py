"""Collection segments a killed process left open, and run statistics from durable observations (release
1.3.1).

``BaseCollector.end`` closes a segment: ``ended_at`` is when the execution stopped and its counters (active
time, credits, steps, products) are final. A killed process (SIGKILL, a lost VM) runs no ``end``: its segment
keeps the counters of its last heartbeat and no end time. When the run's next execution starts
(``BaseCollector.begin``) or the run is recovered (``operations._recover``), such a segment is recorded as
abandoned (:func:`abandon_open`) beside those values, which are never changed:

* ``stats.abandonment``: when and by what it was detected, its last heartbeat, its last durable observation
  (a provider request it reserved or settled, a page it stored, a product it observed) and the bounds of its
  end: after the last durable observation, before the detection. No end time is invented: ``ended_at``
  stays empty;
* a ``SEGMENT_ABANDONED`` event with the same data (the run's earlier events are kept as they are).

Only one execution collects a run at a time (the store lock), so every other open segment of the run is one
whose process ended.

:func:`run_statistics` gives a run's statistics from durable observations: requests and credits from the
provider ledger (one row per request, reserved before it is sent, with its segment), products from the
observations (each names its segment), pages by the segment's time window; the active time of an abandoned
segment is a lower bound (its start to its last durable observation, or its recorded active time when that
is larger), and every bound is labelled as one.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from walmart_headless.core import jsonvalues as jv
from walmart_headless.core.timeutil import iso
from walmart_headless.db.models import CollectionSegment, PageFetch, ProductObservation, ProviderUsage
from walmart_headless.worker.runs import event

ABANDONED_EVENT = "SEGMENT_ABANDONED"
RECORDED_COUNTERS = (
    "active_s",
    "credits_estimated",
    "browser_sessions",
    "browsers_closed",
    "steps",
    "products_verified",
    "workers",
)


def _segments(s: Session, run_id: str) -> list[CollectionSegment]:
    return list(
        s.scalars(
            select(CollectionSegment)
            .where(CollectionSegment.run_id == run_id)
            .order_by(CollectionSegment.started_at, CollectionSegment.id)
        )
    )


def _ledger(s: Session, seg_id: str) -> dict[str, Any]:
    """The segment's provider requests: one ledger row each, reserved before it was sent."""
    rows = list(s.scalars(select(ProviderUsage).where(ProviderUsage.segment_id == seg_id)))
    usd = [r.cost_usd for r in rows if r.cost_usd is not None]
    # A settled request ended at its reservation plus its duration; one still reserved was in flight.
    ends = [r.at + timedelta(milliseconds=r.elapsed_ms or 0) for r in rows]
    return {
        "requests": len(rows),
        "by_outcome": dict(sorted(Counter(r.outcome for r in rows).items())),
        "by_purpose": dict(sorted(Counter(r.purpose for r in rows).items())),
        "credits": round(sum(r.credits or 0.0 for r in rows), 6),
        "usd": round(sum(usd), 6) if usd else None,
        "in_flight_when_last_seen": sum(1 for r in rows if r.outcome == "reserved"),
        "last_at": max(ends) if ends else None,
    }


def _observations(s: Session, seg_id: str) -> dict[str, Any]:
    """Products the segment observed (each observation names its segment)."""
    seg_key = ProductObservation.provenance["segment"].as_string()
    count, distinct, last = s.execute(
        select(
            func.count(),
            func.count(func.distinct(ProductObservation.upc)),
            func.max(ProductObservation.observed_at),
        ).where(seg_key == seg_id)
    ).one()
    verified = s.scalar(
        select(func.count(func.distinct(ProductObservation.upc))).where(
            seg_key == seg_id, ProductObservation.provenance["verified"].as_boolean().is_(True)
        )
    )
    return {
        "observations": int(count),
        "products": int(distinct),
        "verified": int(verified or 0),
        "last_at": last,
    }


def _pages(s: Session, seg: CollectionSegment, until: datetime | None) -> dict[str, Any]:
    """Pages stored by the run from the segment's start until the next segment's (only one execution
    collects a run at a time, so the window is the segment's own)."""
    q = select(func.count(), func.max(PageFetch.started_at)).where(
        PageFetch.run_id == seg.run_id, PageFetch.started_at >= seg.started_at
    )
    if until is not None:
        q = q.where(PageFetch.started_at < until)
    count, last = s.execute(q).one()
    return {"pages": int(count), "last_at": last, "attributed_by": "time window"}


def durable(s: Session, seg: CollectionSegment, until: datetime | None) -> dict[str, Any]:
    """What durable observations say about a segment, and its last durable observation."""
    ledger, obs, pages = _ledger(s, seg.id), _observations(s, seg.id), _pages(s, seg, until)
    times = [t for t in (seg.heartbeat_at, ledger["last_at"], obs["last_at"], pages["last_at"]) if t]
    last = max(times) if times else seg.started_at
    out = {
        "ledger": {**ledger, "last_at": iso(ledger["last_at"]) if ledger["last_at"] else None},
        "observations": {**obs, "last_at": iso(obs["last_at"]) if obs["last_at"] else None},
        "pages": {**pages, "last_at": iso(pages["last_at"]) if pages["last_at"] else None},
        "last_observed_at": iso(last),
    }
    return out


def recorded(seg: CollectionSegment) -> dict[str, Any]:
    """The segment row's own counters, as its process last wrote them."""
    return {name: getattr(seg, name) for name in RECORDED_COUNTERS} | {
        "heartbeat_at": iso(seg.heartbeat_at),
        "ended_at": iso(seg.ended_at) if seg.ended_at else None,
        "stop_code": seg.stop_code,
    }


def abandonment(seg: CollectionSegment) -> dict[str, Any] | None:
    stats = jv.obj(seg.stats, f"segment {seg.id}: stats")
    value = stats.get("abandonment")
    return dict(jv.obj(value, f"segment {seg.id}: abandonment")) if value is not None else None


def abandon_open(
    s: Session, run_id: str, *, current: str | None, detected_by: str, now: datetime
) -> list[dict[str, Any]]:
    """Record each open segment of the run other than ``current`` as abandoned (see the module docstring).
    Idempotent: a segment already recorded is left alone. The caller commits."""
    segs = _segments(s, run_id)
    out: list[dict[str, Any]] = []
    for i, seg in enumerate(segs):
        if seg.id == current or seg.ended_at is not None or abandonment(seg) is not None:
            continue
        nxt = next((x.started_at for x in segs[i + 1 :] if x.id != seg.id), None)
        found = durable(s, seg, nxt)
        record = {
            "detected_at": iso(now),
            "detected_by": detected_by,
            "last_heartbeat_at": iso(seg.heartbeat_at),
            "last_observed_at": found["last_observed_at"],
            # Not observed: the process stopped after its last durable observation and before this detection.
            "ended_at": None,
            "ended_between": [found["last_observed_at"], iso(nxt) if nxt and nxt < now else iso(now)],
            "recorded": recorded(seg),
            "durable": found,
        }
        seg.stats = {**jv.obj(seg.stats, f"segment {seg.id}: stats"), "abandonment": record}
        event(
            s,
            run_id,
            "WARN",
            ABANDONED_EVENT,
            f"segment {seg.id} was left open by an execution that ended without closing it (last durable "
            f"observation {found['last_observed_at']}; its end time was not observed)",
            {"segment": seg.id, **record},
        )
        out.append({"segment": seg.id, **record})
    s.flush()
    return out


def run_statistics(s: Session, run_id: str) -> dict[str, Any]:
    """The run's statistics from durable observations, with each segment's recorded counters beside them
    (see the module docstring)."""
    segs = _segments(s, run_id)
    rows: list[dict[str, Any]] = []
    total_active, lower_bound = 0.0, False
    for i, seg in enumerate(segs):
        nxt = segs[i + 1].started_at if i + 1 < len(segs) else None
        found = durable(s, seg, nxt)
        aband = abandonment(seg)
        if seg.ended_at is not None:
            state, active = "closed", float(seg.active_s or 0.0)
        elif aband is not None:
            state = "abandoned"
            last = datetime.fromisoformat(str(found["last_observed_at"]))
            active = max(float(seg.active_s or 0.0), (last - seg.started_at).total_seconds())
            lower_bound = True
        else:
            state, active = "open", float(seg.active_s or 0.0)
            lower_bound = True
        total_active += active
        rows.append(
            {
                "id": seg.id,
                "trigger": seg.trigger,
                "state": state,
                "started_at": iso(seg.started_at),
                "ended_at": iso(seg.ended_at) if seg.ended_at else None,
                "end_observed": seg.ended_at is not None,
                "ended_between": aband.get("ended_between") if aband else None,
                "active_s": round(active, 1),
                "active_s_is_lower_bound": state != "closed",
                "requests": found["ledger"]["requests"],
                "credits": found["ledger"]["credits"],
                "usd": found["ledger"]["usd"],
                "requests_by_outcome": found["ledger"]["by_outcome"],
                "pages": found["pages"]["pages"],
                "products_observed": found["observations"]["products"],
                "products_verified": found["observations"]["verified"],
                "recorded": recorded(seg),
                "abandonment": aband,
            }
        )
    usd = [r["usd"] for r in rows if r["usd"] is not None]
    return {
        "source": "durable observations: the provider ledger (requests, credits, dollars), product "
        "observations (products) and stored pages (by each segment's time window); each segment's own "
        "counters are under 'recorded'",
        "segments": rows,
        "totals": {
            "segments": len(rows),
            "abandoned": sum(1 for r in rows if r["state"] == "abandoned"),
            "requests": sum(r["requests"] for r in rows),
            "credits": round(sum(r["credits"] for r in rows), 6),
            "usd": round(sum(usd), 6) if usd else None,
            "pages": sum(r["pages"] for r in rows),
            "active_s": round(total_active, 1),
            "active_s_is_lower_bound": lower_bound,
        },
    }
