"""Release 1.3.1: a collection segment left open by a killed process (collection/segments.py) is recorded as
abandoned when the run is recovered, with its own counters, its events and an empty end time kept as they
were, and the run's statistics come from durable observations (the provider ledger).

The kill is simulated in the CLI process: the request for the Snacks listing is reserved in the ledger, then
an exception no handler catches stands for SIGKILL, and ``BaseCollector.end`` (which a killed process never
runs) does nothing. SYNTHETIC pages through the Scrape.do mock; nothing reaches a provider."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from tests.integration.test_operations import STORE_KEY, Env, env  # noqa: F401  (env is a fixture)
from tests.mock_scrapedo import SNACKS
from walmart_headless.collection import segments
from walmart_headless.collection.base import BaseCollector
from walmart_headless.collection.limits import segment_totals
from walmart_headless.db.models import CollectionSegment, Event, ProviderUsage, Run

pytestmark = [pytest.mark.postgres]


class SimulatedKill(BaseException):
    """The process is killed: nothing after this point runs in it."""


def test_a_killed_executions_segment_is_recorded_as_abandoned_and_its_own_values_are_kept(
    env: Env,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    killed: list[str] = []

    def override(url: str) -> Any:
        if SNACKS in url and not killed:
            killed.append(url)
            raise SimulatedKill()  # after the request was reserved in the ledger
        return None

    async def no_end(self: BaseCollector, code: str | None = None, detail: str | None = None) -> None:
        return None  # a killed process closes nothing

    env.mock.page_override = override
    real_end = BaseCollector.end
    monkeypatch.setattr(BaseCollector, "end", no_end)
    with pytest.raises(SimulatedKill):
        env.cli("run", "--store", STORE_KEY)
    monkeypatch.setattr(BaseCollector, "end", real_end)
    env.mock.page_override = None

    factory = sessionmaker(env.engine, expire_on_commit=False)
    [run] = env.runs()
    assert run.status == "running"  # nothing closed it
    with factory() as s:
        [seg] = s.scalars(select(CollectionSegment).where(CollectionSegment.run_id == run.id))
        assert seg.ended_at is None and seg.stop_code is None
        before = segments.recorded(seg)
        events_before = list(s.scalars(select(Event.id).where(Event.run_id == run.id)))
        ledger = list(s.scalars(select(ProviderUsage).where(ProviderUsage.segment_id == seg.id)))
        [in_flight] = [r for r in ledger if SNACKS in r.target_url]
        # Python's unwinding let the transport settle the request as cancelled; a real SIGKILL leaves the row
        # as reserved (the VM's killed segment 01M5X54A kept 2 such rows): restore that state.
        assert in_flight.outcome == "cancelled"
        in_flight.outcome, in_flight.cost_source, in_flight.elapsed_ms = "reserved", "reserved", 0
        s.commit()

    code, _ = env.result("resume", "--store", STORE_KEY)
    assert code == 0
    with factory() as s:
        done = s.get(Run, run.id)
        assert done is not None and done.status == "published"
        killed_seg = s.get(CollectionSegment, seg.id)
        assert killed_seg is not None
        assert killed_seg.ended_at is None  # its end was not observed: never invented
        assert segments.recorded(killed_seg) == before  # its own counters kept
        ab = killed_seg.stats["abandonment"]
        assert ab["detected_by"] == "the run's recovery" and ab["ended_at"] is None
        assert ab["recorded"] == before
        assert ab["durable"]["ledger"]["requests"] == len(ledger)
        assert ab["durable"]["ledger"]["in_flight_when_last_seen"] == 1
        later = s.scalars(
            select(CollectionSegment.started_at)
            .where(CollectionSegment.run_id == run.id, CollectionSegment.id != seg.id)
            .order_by(CollectionSegment.started_at)
        ).first()
        assert later is not None
        low, high = (datetime.fromisoformat(x) for x in ab["ended_between"])
        assert ab["last_observed_at"] == ab["ended_between"][0] and low <= high
        assert low >= killed_seg.heartbeat_at
        # The earlier events are all kept, and the abandonment is recorded once (resume detects it, the new
        # segment's start finds it recorded).
        codes = list(s.scalars(select(Event.code).where(Event.run_id == run.id)))
        assert set(events_before) <= set(s.scalars(select(Event.id).where(Event.run_id == run.id)))
        assert codes.count(segments.ABANDONED_EVENT) == 1

        stats = segments.run_statistics(s, run.id)
        assert stats["segments"][0]["state"] == "abandoned"
        assert all(x["state"] == "closed" for x in stats["segments"][1:])
        run_ledger = s.scalar(
            select(func.count()).select_from(ProviderUsage).where(ProviderUsage.run_id == run.id)
        )
        assert stats["totals"]["requests"] == run_ledger  # every request, from the ledger
        assert stats["totals"]["active_s_is_lower_bound"] is True
        first = stats["segments"][0]
        assert first["end_observed"] is False and first["active_s_is_lower_bound"] is True
        assert first["active_s"] >= before["active_s"]
        # The run's credit limit counts what the ledger holds for the killed segment.
        _, credits, _ = segment_totals(s, run.id, done.store_id, killed_seg.day)
        assert (
            credits
            >= sum(r.credits for r in ledger) + sum(x["credits"] for x in stats["segments"][1:]) - 1e-6
        )
