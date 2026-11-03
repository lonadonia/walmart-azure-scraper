"""Where a run's pages came from: the lineage that keeps synthetic observations apart from authentic ones
(release 1.3.1).

A LIVE run reads its pages from the network through a provider transport (Scrape.do's ``Transport``,
Oxylabs' ``OxylabsTransport``). Tests and the operator's fault-injection harness replace a transport's
HTTP client (its ``client_factory``) with one that answers with synthetic or recorded pages; the collector
then runs exactly as it does live, so its observations look live. The lineage tells them apart:

* ``network``: no provider transport of the process had its client replaced;
* ``substituted``: at least one had (the replaced transports are named);
* ``unrecorded``: a run made before release 1.3.1 (no lineage recorded) that no operator attested.

A run records the lineage of the process that creates it (``config_snapshot.lineage``), and every
collection segment the lineage of the process that runs it (``collection_segments.stats.lineage``); a
segment whose lineage differs from its run's does not start (``LINEAGE_MISMATCH``), and a run with a
segment of another lineage counts as ``substituted``. A REPLAY run has the lineage of the LIVE run whose
pages it reads. A run made before 1.3.1 counts as ``network`` only after ``walmart-collector
attest-lineage`` has recorded an operator's attestation with its evidence (audit log ``lineage_attested``),
and only while none of its segments recorded another lineage.

What the lineage controls:

* retention (``collection/retention.py``): a run takes earlier observations only from runs of its own
  lineage, so synthetic observations never become a real run's history or carried records;
* validation: a carried record whose source run is not of the run's lineage fails G13 (integrity);
* publication: a run whose lineage is not ``network`` is published only to a target configured as a test
  target (``publication.test_target``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from walmart_headless.core import jsonvalues as jv
from walmart_headless.core.findings import DataMode
from walmart_headless.db.models import AuditLog, CollectionSegment, Run

NETWORK = "network"
SUBSTITUTED = "substituted"
UNRECORDED = "unrecorded"
ATTEST_ACTION = "lineage_attested"


def current() -> dict[str, Any]:
    """The lineage of this process's provider transports (recorded with each run and segment)."""
    from walmart_headless.acquisition import oxylabs, scrapedo  # the transports import nothing from here

    replaced = [
        name
        for name, factory in (
            ("scrapedo", scrapedo.Transport.client_factory),
            ("oxylabs", oxylabs.OxylabsTransport.client_factory),
        )
        if factory is not None
    ]
    return {"transport": SUBSTITUTED if replaced else NETWORK, "replaced": replaced}


@dataclass(frozen=True)
class RunLineage:
    run_id: str
    lineage: str  # network | substituted | unrecorded
    basis: str  # how it is known: recorded by the run, attested by an operator, a replay's source run
    problems: tuple[str, ...] = ()  # segments that ran with another lineage


def _segments(s: Session, run_id: str) -> list[tuple[str, str]]:
    """(segment id, recorded lineage or "") of the run's collection segments."""
    out = []
    for seg_id, stats in s.execute(
        select(CollectionSegment.id, CollectionSegment.stats)
        .where(CollectionSegment.run_id == run_id)
        .order_by(CollectionSegment.started_at)
    ):
        lin = jv.obj(jv.obj(stats, f"segment {seg_id}: stats").get("lineage"), f"segment {seg_id}: lineage")
        out.append((seg_id, jv.text(lin.get("transport"), f"segment {seg_id}: lineage.transport")))
    return out


def attestation(s: Session, run_id: str) -> AuditLog | None:
    return s.scalars(
        select(AuditLog)
        .where(AuditLog.action == ATTEST_ACTION, AuditLog.target == run_id)
        .order_by(AuditLog.ts.desc(), AuditLog.id.desc())
        .limit(1)
    ).first()


def of_run(s: Session, run_id: str, *, _seen: frozenset[str] = frozenset()) -> RunLineage:
    """The lineage of a run, from its own records (see the module docstring)."""
    run = s.get(Run, run_id)
    if run is None:
        return RunLineage(run_id, UNRECORDED, "unknown run")
    snap = jv.obj(run.config_snapshot, f"run {run_id}: config_snapshot")
    if run.mode == DataMode.REPLAY.value:
        src = jv.text(jv.obj(snap.get("replay"), f"run {run_id}: replay").get("source_run"), f"run {run_id}")
        if not src or src in _seen:
            return RunLineage(run_id, UNRECORDED, "a replay that names no readable source run")
        inner = of_run(s, src, _seen=_seen | {run_id})
        return RunLineage(run_id, inner.lineage, f"replay of {src}: {inner.basis}", inner.problems)
    if run.mode != DataMode.LIVE.value:
        return RunLineage(run_id, SUBSTITUTED, f"a {run.mode} run (synthetic fixture pages)")
    recorded = jv.text(
        jv.obj(snap.get("lineage"), f"run {run_id}: lineage").get("transport"), f"run {run_id}"
    )
    segments = _segments(s, run_id)
    if recorded:
        problems = tuple(f"segment {sid} ran with lineage {x}" for sid, x in segments if x and x != recorded)
        if problems:
            return RunLineage(
                run_id, SUBSTITUTED, f"recorded {recorded}, mixed with other segments", problems
            )
        return RunLineage(run_id, recorded, "recorded by the run")
    problems = tuple(f"segment {sid} ran with lineage {x}" for sid, x in segments if x and x != NETWORK)
    att = attestation(s, run_id)
    if att is not None and not problems:
        data = jv.obj(att.data, f"audit {att.id}: data")
        lin = jv.text(data.get("lineage"), f"audit {att.id}: lineage") or UNRECORDED
        return RunLineage(run_id, lin, f"attested by {att.actor} at {att.ts.isoformat()}: {att.reason or ''}")
    if problems:
        return RunLineage(
            run_id, SUBSTITUTED, "made before release 1.3.1, with segments of another lineage", problems
        )
    return RunLineage(run_id, UNRECORDED, "no lineage recorded (a run made before release 1.3.1)")


class LineageRefused(ValueError):
    pass


def attest(s: Session, run_id: str, *, actor: str, reason: str, evidence: str) -> dict[str, Any]:
    """Record an operator's attestation that a run made before release 1.3.1 read its pages from the
    network. Refused for a run that records its own lineage, a run that is not LIVE, a run whose segments
    recorded another lineage, and without a reason and evidence. The caller commits."""
    run = s.get(Run, run_id)
    if run is None:
        raise LineageRefused(f"unknown run {run_id}")
    if run.mode != DataMode.LIVE.value:
        raise LineageRefused(
            f"run {run_id} is a {run.mode} run: only a LIVE run reads pages from the network"
        )
    snap = jv.obj(run.config_snapshot, f"run {run_id}: config_snapshot")
    if jv.obj(snap.get("lineage"), f"run {run_id}: lineage"):
        raise LineageRefused(f"run {run_id} records its own lineage: nothing to attest")
    other = [f"{sid}: {x}" for sid, x in _segments(s, run_id) if x and x != NETWORK]
    if other:
        raise LineageRefused(f"segments of run {run_id} ran with another lineage: {other}")
    if not reason.strip() or not evidence.strip():
        raise LineageRefused("an attestation needs a reason and the evidence it rests on")
    data = {"lineage": NETWORK, "evidence": evidence.strip()}
    s.add(AuditLog(actor=actor, action=ATTEST_ACTION, target=run_id, reason=reason.strip(), data=data))
    s.flush()
    return {"run_id": run_id, **data, "reason": reason.strip()}
