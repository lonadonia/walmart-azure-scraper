"""Release 1.3.0 operations through the command line, against SYNTHETIC pages (tests/mock_scrapedo.py,
tests/mock_oxylabs.py): parallel workers of one run (the same records as one worker, no page requested
twice, a termination and a resume with workers), the Oxylabs Web API as the run's provider (the store's
parameters on every store-scoped request, the key only in the Authorization header), the operator's ceiling
(nothing is sent without one; never crossed; a resume after it is raised), the task's money budget across
providers, and the migrated schema against the models. Nothing here reaches Scrape.do, Oxylabs or Walmart."""

from __future__ import annotations

from collections import Counter
from typing import Any

import httpx
import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import Engine, select
from sqlalchemy.orm import sessionmaker

from tests.integration.test_operations import STORE_KEY, Env, _raise_sigterm_on, env  # noqa: F401
from tests.mock_oxylabs import OXY_KEY, MockOxylabs
from tests.mock_scrapedo import SNACKS
from walmart_headless.acquisition import oxylabs
from walmart_headless.collection import reconcile
from walmart_headless.db.models import (
    Base,
    CollectionSegment,
    Event,
    ProviderUsage,
    RecordRow,
    Run,
    StoreAttestation,
)

pytestmark = [pytest.mark.postgres]


def records(e: Env, run_id: str) -> dict[str, str]:
    with sessionmaker(e.engine)() as s:
        return {r.upc: r.status for r in s.scalars(select(RecordRow).where(RecordRow.run_id == run_id))}


def usage(e: Env, provider: str) -> list[ProviderUsage]:
    with sessionmaker(e.engine, expire_on_commit=False)() as s:
        return list(s.scalars(select(ProviderUsage).where(ProviderUsage.provider == provider)))


@pytest.fixture
def oxy(env: Env, monkeypatch: pytest.MonkeyPatch) -> MockOxylabs:  # noqa: F811
    monkeypatch.setenv(oxylabs.ENV_KEY, OXY_KEY)
    mock = MockOxylabs(env.mock)
    monkeypatch.setattr(
        oxylabs.OxylabsTransport,
        "client_factory",
        lambda: httpx.AsyncClient(transport=httpx.MockTransport(mock.handler)),
    )
    return mock


def test_two_workers_collect_what_one_worker_collects_without_requesting_a_page_twice(
    env: Env,  # noqa: F811
) -> None:
    code, _ = env.result("run", "--store", STORE_KEY)
    assert code == 0
    one = env.runs()[-1]
    before = len(env.mock.calls)
    code, _ = env.result("run", "--store", STORE_KEY, "--workers", "2")
    assert code == 0
    two = env.runs()[-1]
    assert two.status == "published" and records(env, two.id) == records(env, one.id)
    listing_calls = Counter(
        url for _, path, url in env.mock.calls[before:] if path == "/plugin/walmart/store"
    )
    assert listing_calls and max(listing_calls.values()) == 1
    with sessionmaker(env.engine)() as s:
        seg = s.scalars(select(CollectionSegment).where(CollectionSegment.run_id == two.id)).one()
        assert seg.workers == 2
        assert [w["worker"] for w in seg.stats["workers"]] == ["w0", "w1"]
        assert sum(w["requests"] for w in seg.stats["workers"]) == len(env.mock.calls) - before
        started = s.scalars(
            select(Event).where(Event.run_id == two.id, Event.code == "WORKERS_STARTED")
        ).one()
        assert len(started.data["workers"]) == 2
        one_seg = s.scalars(select(CollectionSegment).where(CollectionSegment.run_id == one.id)).one()
        assert one_seg.workers == 1


def test_a_terminated_run_with_two_workers_resumes_and_finishes(env: Env) -> None:  # noqa: F811
    env.mock.page_override = _raise_sigterm_on(SNACKS)
    code, _ = env.result("run", "--store", STORE_KEY, "--workers", "2")
    assert code == 75
    [run] = env.runs()
    assert run.status == "interrupted" and run.stop_code == "TERMINATED"
    env.mock.page_override = None
    code, _ = env.result("resume", "--store", STORE_KEY, "--workers", "2")
    assert code == 0
    with sessionmaker(env.engine)() as s:
        done = s.get(Run, run.id)
        assert done is not None and done.status == "published"
        upcs = list(s.scalars(select(RecordRow.upc).where(RecordRow.run_id == run.id)))
        assert len(upcs) == len(set(upcs))


def test_an_oxylabs_run_sends_nothing_without_a_ceiling(env: Env, oxy: MockOxylabs) -> None:  # noqa: F811
    code, _ = env.result("run", "--store", STORE_KEY, "--provider", "oxylabs")
    assert code == 4
    [run] = env.runs()
    assert run.status == "interrupted" and run.stop_code == "SPENDING_CEILING"
    assert run.config_snapshot["provider"] == "oxylabs"
    assert oxy.calls == [] and usage(env, "oxylabs") == []


def test_an_oxylabs_run_collects_the_store_within_its_ceiling_and_never_shows_the_key(
    env: Env,  # noqa: F811
    oxy: MockOxylabs,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, res = env.result(
        "set-ceiling",
        "--provider",
        "oxylabs",
        "--submissions",
        "200",
        "--usd",
        "0.30",
        "--minutes",
        "15",
        "--usd-per-result",
        "0.0015",
        "--basis",
        "test ceiling",
    )
    assert code == 0 and res["max_submissions"] == 200
    code, lines = env.cli("run", "--store", STORE_KEY, "--provider", "oxylabs")
    assert code == 0, [(x["event"], x.get("message", "")[:120]) for x in lines]
    [run] = env.runs()
    assert run.status == "published" and run.config_snapshot["provider"] == "oxylabs"
    rows = usage(env, "oxylabs")
    assert len(rows) == len(oxy.calls) <= 200
    assert all(r.cost_usd == 0.0015 and r.outcome != "reserved" for r in rows)
    assert all((r.api_product or "").startswith("oxylabs web api") for r in rows)
    assert set(oxy.authorizations) == {f"Bearer {OXY_KEY}"}
    walmart = [b for endpoint, b in oxy.calls if endpoint == "/v1/scrape/walmart"]
    assert walmart and all(b["store_id"] == "3891" and b["fulfillment_type"] == "pickup" for b in walmart)
    assert all("/browse/" not in b["url"] for endpoint, b in oxy.calls if endpoint == "/v1/scrape")
    # The Web API applies Walmart's Pickup filter from its fulfillment_type: the URL it is sent names no facet
    # (release 1.4.1 adds the facet to the Scrape.do edition's result pages only), and each grid states it.
    assert not any("facet=" in b["url"] for b in walmart)
    with sessionmaker(env.engine)() as s:
        read = [r for r in reconcile.reconcile(s, run.id)["rows"] if r["pages_visited"]]
    assert read and all(set(r["grid_fulfillment_filter"]) == {"Pickup"} for r in read)
    valid = {k for k, v in records(env, run.id).items() if v == "valid"}
    assert {"wm:7101", "wm:7201", "wm:7301"} <= valid
    # The key is in no log line, stored page, export or database row.
    assert all(OXY_KEY not in str(x) for x in lines)
    for f in env.data.rglob("*"):
        if f.is_file():
            assert OXY_KEY.encode() not in f.read_bytes(), f
    with env.engine.connect() as conn:
        dump = (
            conn.exec_driver_sql(
                "SELECT string_agg(t::text, '') FROM (SELECT * FROM page_fetches) t"
            ).scalar()
            or ""
        )
        assert OXY_KEY not in dump
        dump = conn.exec_driver_sql("SELECT string_agg(t::text, '') FROM (SELECT * FROM events) t").scalar()
        assert OXY_KEY not in (dump or "")
    code, res = env.result("provider-balance", "--provider", "oxylabs")
    assert code == 0 and res["room_submissions"] == 200 - len(rows)
    assert OXY_KEY not in capsys.readouterr().out


def test_an_oxylabs_run_is_replayed_with_the_store_parameters_its_requests_carried(
    env: Env,  # noqa: F811
    oxy: MockOxylabs,
) -> None:
    # Release 1.3.1: the replay recorded Scrape.do's store parameters (storeid, zipcode) for every page, so
    # the replay of an Oxylabs run stopped at its first listing page (STORE_NOT_VERIFIED, exit 7). Found by
    # the offline reprocessing of the 2026-10-26 Azure run 01M5X364ZR83MZ9M60QGPFR7TX.
    env.result("set-ceiling", "--provider", "oxylabs", "--submissions", "200", "--basis", "test ceiling")
    code, _ = env.result("run", "--store", STORE_KEY, "--provider", "oxylabs")
    assert code == 0
    [source] = env.runs()
    calls = len(oxy.calls)
    code, lines = env.cli("replay", "--run", source.id)
    assert code == 0, [(x["event"], x.get("message", "")[:160]) for x in lines]
    assert len(oxy.calls) == calls  # the replay requested nothing
    replay = next(r for r in env.runs() if r.id != source.id)
    assert replay.mode == "REPLAY" and replay.config_snapshot["provider"] == "oxylabs"
    with sessionmaker(env.engine)() as s:
        listing_checks = [
            c
            for a in s.scalars(
                select(StoreAttestation).where(
                    StoreAttestation.run_id == replay.id, StoreAttestation.phase == "task_start"
                )
            )
            for c in a.checks["checks"]
            if c["name"] == "store_scoped_request"
        ]
    assert listing_checks
    assert all(
        c["status"] == "PASS" and c["observed"] == {"store_id": "3891", "fulfillment_type": "pickup"}
        for c in listing_checks
    )
    # The same products as the source run, read from its stored pages.
    assert {k for k, v in records(env, replay.id).items() if v != "historical"} == {
        k for k, v in records(env, source.id).items() if v != "historical"
    }
    # The replay's log names the source run's stored pages, never requests of the provider. The offline
    # reprocessing of 2026-10-27 (replay 01M5Z7VN6KFW40M87ZX8YY3EGT) logged "requests of the closed Oxylabs
    # Web API session" and "Oxylabs Web API applies it on every page" for pages it only read again.
    with sessionmaker(env.engine)() as s:
        said = {
            (e.run_id, e.code): (e.message, e.data)
            for e in s.scalars(select(Event).where(Event.code.in_(("STORE_SELECTED", "PROVIDER_TRAFFIC"))))
        }
    assert said[(source.id, "PROVIDER_TRAFFIC")][0].startswith(
        "requests of the closed Oxylabs Web API session"
    )
    assert "Oxylabs Web API applies it on every page" in said[(source.id, "STORE_SELECTED")][0]
    for code in ("STORE_SELECTED", "PROVIDER_TRAFFIC"):
        message = said[(replay.id, code)][0]
        assert source.id in message and "no request" in message, message
        assert "requests of the closed" not in message and "applies it on every page" not in message
    method = said[(replay.id, "STORE_SELECTED")][1]["result"]["method"]
    assert method.startswith(f"replay of run {source.id}: its stored pages are read again"), method


def test_the_oxylabs_ceiling_is_never_crossed_and_a_raised_ceiling_resumes_the_run(
    env: Env,  # noqa: F811
    oxy: MockOxylabs,
) -> None:
    env.result("set-ceiling", "--provider", "oxylabs", "--submissions", "6", "--basis", "test")
    code, _ = env.result("run", "--store", STORE_KEY, "--provider", "oxylabs")
    assert code == 4
    [run] = env.runs()
    assert run.status == "interrupted" and run.stop_code == "SPENDING_CEILING"
    # Stopped before a request could cross the ceiling (a request is one submission, or up to three).
    assert len(usage(env, "oxylabs")) == len(oxy.calls) <= 6
    assert "Oxylabs submissions left" in (run.stop_detail or "")
    env.result("set-ceiling", "--provider", "oxylabs", "--submissions", "200", "--basis", "raised")
    code, _ = env.result("resume", "--store", STORE_KEY)
    assert code == 0
    with sessionmaker(env.engine)() as s:
        done = s.get(Run, run.id)
        assert done is not None and done.status == "published"


def test_the_task_budget_bounds_every_provider_before_a_request_is_sent(
    env: Env,  # noqa: F811
    oxy: MockOxylabs,
) -> None:
    env.result(
        "set-ceiling",
        "--provider",
        "oxylabs",
        "--submissions",
        "200",
        "--usd-per-result",
        "0.0015",
        "--basis",
        "t",
    )
    code, res = env.result("set-budget", "--usd", "0.006", "--basis", "test budget")
    assert code == 0 and res["max_usd"] == 0.006
    code, _ = env.result("run", "--store", STORE_KEY, "--provider", "oxylabs")
    assert code == 4
    [run] = env.runs()
    assert run.stop_code == "SPENDING_CEILING" and "money budget" in (run.stop_detail or "")
    rows = usage(env, "oxylabs")
    assert len(rows) == len(oxy.calls) <= 4  # $0.006 at $0.0015 a submission: never crossed
    assert round(sum(r.cost_usd or 0.0 for r in rows), 6) <= 0.006


def test_the_migrated_schema_matches_the_models(migrated_engine: Engine) -> None:
    with migrated_engine.connect() as conn:
        diff: list[Any] = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    assert diff == []
