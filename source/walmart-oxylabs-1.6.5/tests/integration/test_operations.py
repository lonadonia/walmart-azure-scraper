"""The headless collector through its command line, end to end: a throwaway PostgreSQL, a local storage
folder and the in-memory mock of Scrape.do serving SYNTHETIC Walmart pages (tests/mock_scrapedo.py).
Nothing here reaches Scrape.do or Walmart."""

from __future__ import annotations

import asyncio
import csv
import io
import json
import shutil
import signal
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import httpx
import pytest
import yaml
from sqlalchemy import Engine, func, select, text
from sqlalchemy.orm import sessionmaker

from tests import synthetic_walmart as syn
from tests.conftest import CONFIG, STORE_KEY, declare_test_target
from tests.mock_scrapedo import MILK, PAGES, PRIMARY, SNACKS, MockScrapeDo
from walmart_headless import operations
from walmart_headless.acquisition import scrapedo as sd
from walmart_headless.cli import Terminated, main, run_async
from walmart_headless.core.schema import OUTPUT_FIELDS
from walmart_headless.db.locks import StoreRunLock
from walmart_headless.db.models import (
    CollectionSegment,
    Event,
    ProductObservation,
    PublicationPointer,
    RecordRow,
    Run,
    ScheduleOccurrence,
    Store,
)

pytestmark = [pytest.mark.postgres]


@dataclass
class Env:
    config: Path
    mock: MockScrapeDo
    engine: Engine
    data: Path
    capsys: pytest.CaptureFixture[str]

    def cli(self, *args: str) -> tuple[int, list[dict[str, Any]]]:
        self.capsys.readouterr()
        code = main(["--config", str(self.config), *args])
        out = self.capsys.readouterr().out
        return code, [json.loads(line) for line in out.splitlines() if line.startswith("{")]

    def result(self, *args: str) -> tuple[int, Any]:
        code, lines = self.cli(*args)
        res = [x for x in lines if x["event"] == "RESULT"]
        return code, (res[-1]["result"] if res else lines)

    def edit(self, **collection: Any) -> None:
        data = yaml.safe_load(self.config.read_text(encoding="utf-8"))
        data["collections"][STORE_KEY].update(collection)
        self.config.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    def runs(self) -> list[Run]:
        with sessionmaker(self.engine, expire_on_commit=False)() as s:
            return list(s.scalars(select(Run).order_by(Run.created_at)))


@pytest.fixture
def env(
    migrated_engine: Engine,
    pg_url: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> Env:
    cfg_dir = tmp_path / "config"
    shutil.copytree(CONFIG, cfg_dir)
    declare_test_target(cfg_dir)  # the mock's runs are published to this test target only
    monkeypatch.setenv("WALMART_COLLECTOR_DATABASE_URL", pg_url)
    monkeypatch.setenv(sd.ENV_KEY, PRIMARY)
    monkeypatch.setenv("WALMART_COLLECTOR_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(sd, "INFO_MIN_INTERVAL_S", 0.0)
    monkeypatch.setattr(operations, "AUTO_RESUME_WAIT_S", 0.0)
    mock = MockScrapeDo()
    monkeypatch.setattr(
        sd.Transport, "client_factory", lambda: httpx.AsyncClient(transport=httpx.MockTransport(mock.handler))
    )
    e = Env(cfg_dir / "collector.yaml", mock, migrated_engine, tmp_path / "data", capsys)
    e.edit(categories=[0, 4], limits={"max_run_minutes": None})  # Food and Diapering: the mock's pages
    return e


def test_the_schema_is_checked_and_upgraded_and_the_configuration_validated(env: Env) -> None:
    with env.engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    code, res = env.result("validate-config", "--check-db")
    assert code == 2 and res["database"] == {"revision": None, "head": "0006", "current": False}
    code, _ = env.result("status")
    assert code == 2  # every command but db-upgrade refuses an old schema
    code, res = env.result("db-upgrade")
    assert code == 0 and res == {"before": None, "after": "0006"}
    code, lines = env.cli("validate-config", "--check-db", "--require-credentials")
    assert code == 0
    assert PRIMARY not in json.dumps(lines)
    res = lines[-1]["result"]
    assert res["environment"]["scrapedo_key"]["configured"] is True
    assert res["stores"][0]["fulfillment"] == "PICKUP" and res["stores"][0]["store_id"] == "3891"


def test_a_pilot_run_is_exported_labelled_and_never_published(env: Env, tmp_path: Path) -> None:
    code, _ = env.result("run", "--store", STORE_KEY, "--categories", "0", "--max-products", "1")
    assert code == 0
    [run] = env.runs()
    assert run.config_snapshot["pilot"] is True and run.stop_code == "RUN_PRODUCT_LIMIT"
    code, status = env.result("status", "--store", STORE_KEY)
    entry = status["stores"][0]
    assert entry["published"] is None and entry["runs"][0]["dataset"] == "pilot"
    exports = env.data / "runs" / STORE_KEY / run.id / "exports"
    manifest = json.loads((exports / "manifest.json").read_text("utf-8"))
    assert manifest["dataset"] == "pilot" and manifest["record_count"] >= 1
    rows = list(csv.reader(io.StringIO((exports / "products.csv").read_bytes().decode("utf-8-sig"))))
    assert tuple(rows[0]) == OUTPUT_FIELDS and len(rows) - 1 == manifest["record_count"]
    products = json.loads((exports / "products.json").read_text("utf-8"))
    assert all(
        list(p) == list(OUTPUT_FIELDS) and all(isinstance(v, str) for v in p.values()) for p in products
    )
    code, res = env.result("validate-export", "--run", run.id)
    assert code == 0, res
    assert res["source_check"]["summary"]["verified"] == len(products) and res["contract"]["passed"]
    code, res = env.result("export", "--run", run.id, "--out", str(tmp_path / "out"))
    assert code == 0 and (tmp_path / "out" / "products.csv").is_file()
    assert not (env.data / "published").exists()


def test_a_row_narrowed_to_listings_under_its_category_reads_them_without_the_category_page(env: Env) -> None:
    """Food narrowed to its Milk listing by path: the listing is read directly (its id 976759_9176907 is
    under Food, 976759), named by its own page, which places it under Food; the category page is not read.
    A listing outside the category (Diapering, 5427_486190) is not read directly: the category page is."""
    milk = "0:/browse/food/milk/976759_9176907"
    code, _ = env.result("run", "--store", STORE_KEY, "--categories", "0", "--subcategory", milk)
    assert code == 0
    run = env.runs()[-1]
    with sessionmaker(env.engine)() as s:
        purposes = [
            p for (p,) in s.execute(text("select purpose from page_fetches where run_id = :r"), {"r": run.id})
        ]
        configured = s.scalar(
            select(func.count())
            .select_from(Event)
            .where(Event.run_id == run.id, Event.code == "SUBCATEGORIES_CONFIGURED")
        )
    assert "category_page" not in purposes and purposes.count("listing") == 1 and configured == 1
    exports = env.data / "runs" / STORE_KEY / run.id / "exports"
    products = json.loads((exports / "products.json").read_text("utf-8"))
    assert [(p["category"], p["sub_category"]) for p in products] == [("Food", "Milk")]
    code, _ = env.result(
        "run", "--store", STORE_KEY, "--categories", "0", "--subcategory", "0:/browse/diapering/5427_486190"
    )
    other = env.runs()[-1]
    with sessionmaker(env.engine)() as s:
        purposes = [
            p
            for (p,) in s.execute(text("select purpose from page_fetches where run_id = :r"), {"r": other.id})
        ]
    assert other.id != run.id and "category_page" in purposes


def test_a_complete_run_is_published_and_a_partial_run_never_replaces_it(env: Env, tmp_path: Path) -> None:
    code, _ = env.result("run", "--store", STORE_KEY)
    assert code == 0
    [first] = env.runs()
    assert first.status == "published"
    latest = json.loads((env.data / "published" / STORE_KEY / "latest.json").read_text("utf-8"))
    assert latest["run_id"] == first.id
    env.mock.remaining[PRIMARY] = 25  # robots (1) + store page (1) + two pages (20), then nothing left
    code, _ = env.result("run", "--store", STORE_KEY)
    assert code == 4  # the provider's credits ran out
    second = env.runs()[-1]
    assert second.stop_code == "CREDITS_EXHAUSTED" and second.status == "rejected"
    manifest = json.loads(
        (env.data / "runs" / STORE_KEY / second.id / "exports" / "manifest.json").read_text("utf-8")
    )
    assert manifest["dataset"] == "partial"
    latest = json.loads((env.data / "published" / STORE_KEY / "latest.json").read_text("utf-8"))
    assert latest["run_id"] == first.id  # the last complete dataset stays the published one
    code, res = env.result("export", "--store", STORE_KEY, "--out", str(tmp_path / "published"))
    assert code == 0 and res["run_id"] == first.id


def test_a_store_check_failure_holds_the_store_until_an_operator_releases_it(env: Env) -> None:
    env.mock.intent = "SHIPPING"
    code, _ = env.result("run", "--store", STORE_KEY)
    assert code == 7
    calls = len(env.mock.calls)
    code, lines = env.cli("run", "--store", STORE_KEY)
    assert code == 8 and len(env.mock.calls) == calls  # held: no request at all
    assert any(x["event"] == "COMMAND_REFUSED" for x in lines)
    code, status = env.result("status", "--store", STORE_KEY)
    assert status["stores"][0]["hold"]["stop_code"] == "STORE_NOT_VERIFIED"
    code, res = env.result("release-hold", "--store", STORE_KEY, "--reason", "store context checked")
    assert code == 0 and res["released"] is True
    env.mock.intent = "PICKUP"
    code, _ = env.result("run", "--store", STORE_KEY)
    assert code == 0


def test_missing_key_bad_configuration_and_missing_database_have_their_own_exit_codes(
    env: Env, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(sd.ENV_KEY)
    code, _ = env.result("run", "--store", STORE_KEY)
    assert code == 3 and env.runs() == [] and env.mock.calls == []
    monkeypatch.setenv(sd.ENV_KEY, PRIMARY)
    env.edit(schedule={"enabled": True, "weekdays": [9]})
    code, _ = env.result("validate-config")
    assert code == 2
    env.edit(schedule={"enabled": False, "weekdays": []})
    monkeypatch.delenv("WALMART_COLLECTOR_DATABASE_URL")
    code, _ = env.result("status")
    assert code == 2


def _raise_sigterm_on(url_part: str) -> Any:
    sent: list[str] = []

    def override(url: str) -> httpx.Response | None:
        if url_part in url and not sent:
            sent.append(url)
            signal.raise_signal(signal.SIGTERM)
        return None

    return override


def test_a_termination_signal_leaves_the_run_resumable_and_resume_finishes_it(env: Env) -> None:
    env.mock.page_override = _raise_sigterm_on(SNACKS)
    code, lines = env.cli("run", "--store", STORE_KEY)
    assert code == 75, [(x["event"], x.get("message", "")[:80]) for x in lines]
    assert any(x["event"] == "SIGNAL_RECEIVED" and x["signal"] == "SIGTERM" for x in lines)
    [run] = env.runs()
    assert run.status == "interrupted" and run.stop_code == "TERMINATED"
    factory = sessionmaker(env.engine, expire_on_commit=False)
    with factory() as s:
        segs = list(s.scalars(select(CollectionSegment).where(CollectionSegment.run_id == run.id)))
        assert segs and all(seg.ended_at is not None for seg in segs)  # the segment was closed
        assert "RUN_INTERRUPTED" in set(s.scalars(select(Event.code).where(Event.run_id == run.id)))
    with StoreRunLock(env.engine, run.store_id, run.id, "probe"):  # the store lock was released
        pass
    env.mock.page_override = None
    code, _ = env.result("resume", "--store", STORE_KEY)
    assert code == 0
    with factory() as s:
        done = s.get(Run, run.id)
        assert done is not None and done.status == "published"
        upcs = list(s.scalars(select(RecordRow.upc).where(RecordRow.run_id == run.id)))
        assert len(upcs) == len(set(upcs))


def test_a_terminated_run_closed_by_finalize_reports_its_outcome_not_the_resumable_code(env: Env) -> None:
    env.mock.page_override = _raise_sigterm_on(SNACKS)
    assert env.cli("run", "--store", STORE_KEY)[0] == 75  # interrupted: resume would continue it
    env.mock.page_override = None
    code, _ = env.result("finalize", "--store", STORE_KEY)
    [run] = env.runs()
    assert run.status == "rejected" and run.stop_code == "TERMINATED"
    assert code == 6  # closed as a partial dataset: never 75 once nothing can continue it


def test_stop_then_finalize_keeps_what_was_collected_as_a_partial_export(env: Env) -> None:
    env.mock.page_override = _raise_sigterm_on(SNACKS)
    assert env.cli("run", "--store", STORE_KEY)[0] == 75
    env.mock.page_override = None
    calls = len(env.mock.calls)
    code, res = env.result("stop", "--store", STORE_KEY, "--reason", "end of test window")
    assert code == 0 and res["worker_running"] is False
    code, _ = env.result("finalize", "--store", STORE_KEY)
    assert code in (0, 6)
    assert len(env.mock.calls) == calls  # finalizing requests nothing
    [run] = env.runs()
    assert run.status in ("validated", "rejected") and run.stop_code == "OPERATOR_STOP"
    manifest = json.loads((env.data / "runs" / STORE_KEY / run.id / "exports" / "manifest.json").read_text())
    assert manifest["dataset"] == "partial"
    assert not (env.data / "published").exists()


def _ctx(env: Env, now: datetime) -> operations.Context:
    ctx = operations.Context(env.config)
    start = datetime.now(UTC)
    ctx.clock = lambda: now + (datetime.now(UTC) - start)
    return ctx


def _occurrences(env: Env) -> dict[str, ScheduleOccurrence]:
    with sessionmaker(env.engine, expire_on_commit=False)() as s:
        return {r.day: r for r in s.scalars(select(ScheduleOccurrence).order_by(ScheduleOccurrence.due_at))}


def _scheduled(env: Env, now: datetime) -> int:
    ctx = _ctx(env, now)
    try:
        return int(asyncio.run(operations.scheduled_run(ctx, STORE_KEY)))
    finally:
        ctx.close()


def test_a_scheduled_execution_acts_only_on_the_due_local_occurrence_once(env: Env) -> None:
    env.edit(schedule={"enabled": True, "weekdays": [1], "start_time": "06:00"})  # Tuesdays 06:00 Chicago
    summer = datetime(2026, 7, 14, tzinfo=UTC)
    # Azure's cron fires at 11:00 and 12:00 UTC; in July 06:00 Chicago is 11:00 UTC (CDT).
    assert _scheduled(env, summer.replace(hour=10)) == 0 and env.runs() == []  # 05:00 local: not due
    assert _scheduled(env, summer.replace(hour=11)) == 0
    [run] = env.runs()
    assert run.trigger == "schedule" and run.config_snapshot["occurrence"]["day"] == "2026-07-14"
    calls = len(env.mock.calls)
    assert _scheduled(env, summer.replace(hour=11, minute=10)) == 0  # an Azure retry: done already
    assert _scheduled(env, summer.replace(hour=12)) == 0  # the cron's other hour: done already
    assert len(env.runs()) == 1 and len(env.mock.calls) == calls
    # Wednesday is not a scheduled day.
    assert _scheduled(env, datetime(2026, 7, 15, 11, tzinfo=UTC)) == 0 and len(env.runs()) == 1


def test_a_winter_occurrence_is_due_at_its_local_time(env: Env) -> None:
    env.edit(schedule={"enabled": True, "weekdays": [1], "start_time": "06:00"})
    winter = datetime(2026, 1, 13, tzinfo=UTC)
    # In January 06:00 Chicago is 12:00 UTC (CST): the 11:00 firing is 05:00 local.
    assert _scheduled(env, winter.replace(hour=11)) == 0 and env.runs() == []
    assert _scheduled(env, winter.replace(hour=12)) == 0
    assert [r.config_snapshot["occurrence"]["day"] for r in env.runs()] == ["2026-01-13"]


def test_a_scheduled_execution_is_held_after_a_refusal(env: Env) -> None:
    env.edit(schedule={"enabled": True, "weekdays": [1], "start_time": "06:00"})
    env.mock.intent = "SHIPPING"
    assert _scheduled(env, datetime(2026, 7, 14, 11, tzinfo=UTC)) == 7
    calls = len(env.mock.calls)
    assert _scheduled(env, datetime(2026, 7, 21, 11, tzinfo=UTC)) == 8 and len(env.mock.calls) == calls
    # The hold does not lose the occurrence: it waits with the reason, and runs after the release.
    row = _occurrences(env)["2026-07-21"]
    assert row.state == "deferred" and "held" in str(row.reason)
    assert env.result("release-hold", "--store", STORE_KEY, "--reason", "store context fixed")[0] == 0
    env.mock.intent = "PICKUP"
    assert _scheduled(env, datetime(2026, 7, 21, 11, 30, tzinfo=UTC)) == 0
    assert _occurrences(env)["2026-07-21"].state == "completed"
    assert [r.config_snapshot["occurrence"]["day"] for r in env.runs()] == ["2026-07-14", "2026-07-21"]


def test_an_unfinished_scheduled_run_is_closed_when_the_next_occurrence_starts(env: Env) -> None:
    # The release 1.3.0 behaviour, kept as an option (schedule.on_overlap: supersede).
    env.edit(schedule={"enabled": True, "weekdays": [1], "start_time": "06:00", "on_overlap": "supersede"})
    env.mock.page_override = _raise_sigterm_on(SNACKS)
    ctx = _ctx(env, datetime(2026, 7, 14, 11, tzinfo=UTC))
    with pytest.raises(Terminated):  # the CLI's signal handling, as in a scheduled execution
        run_async(operations.scheduled_run(ctx, STORE_KEY))
    ctx.close()
    env.mock.page_override = None
    [old] = env.runs()
    assert old.status == "interrupted"
    assert _scheduled(env, datetime(2026, 7, 21, 11, tzinfo=UTC)) == 0
    old_now, new = env.runs()
    assert (
        old_now.id == old.id
        and old_now.stop_code == "SUPERSEDED"
        and old_now.status in ("validated", "rejected")
    )
    assert new.status == "published" and new.config_snapshot["occurrence"]["day"] == "2026-07-21"


def test_an_unfinished_scheduled_run_goes_on_when_the_next_occurrence_starts(env: Env) -> None:
    """Release 1.3.1 default (schedule.on_overlap: continue): the next occurrence finds the scheduled run of
    the previous one unfinished and lets it go on (OCCURRENCE_DEFERRED) instead of closing it as partial, so a
    run longer than the interval between two starts is never cut short. Release 1.5.0: that next occurrence is
    no longer lost. It stays waiting and starts once the run ends, before any later one, with its missed
    deadline on record. SYNTHETIC pages through the Scrape.do mock."""
    env.edit(schedule={"enabled": True, "weekdays": [1], "start_time": "06:00"})
    env.mock.page_override = _raise_sigterm_on(SNACKS)
    ctx = _ctx(env, datetime(2026, 7, 14, 11, tzinfo=UTC))
    with pytest.raises(Terminated):  # the CLI's signal handling, as in a scheduled execution
        run_async(operations.scheduled_run(ctx, STORE_KEY))
    ctx.close()
    env.mock.page_override = None
    [old] = env.runs()
    assert old.status == "interrupted"
    assert _scheduled(env, datetime(2026, 7, 21, 11, tzinfo=UTC)) == 0
    [same] = env.runs()  # no new run
    assert same.id == old.id and same.status == "published" and same.stop_code != "SUPERSEDED"
    assert same.config_snapshot["occurrence"]["day"] == "2026-07-14"  # the same logical run and scope
    with sessionmaker(env.engine)() as s:
        deferred = list(
            s.scalars(select(Event).where(Event.run_id == old.id, Event.code == "OCCURRENCE_DEFERRED"))
        )
    assert [(e.data["occurrence"], e.data["run_occurrence"]) for e in deferred] == [
        ("2026-07-21", "2026-07-14")
    ]
    rows = _occurrences(env)
    assert rows["2026-07-14"].state == "completed" and rows["2026-07-21"].state == "deferred"
    assert _scheduled(env, datetime(2026, 7, 28, 11, tzinfo=UTC)) == 0
    first, second = env.runs()
    assert first.id == old.id and second.config_snapshot["occurrence"]["day"] == "2026-07-21"
    assert second.status == "published"
    rows = _occurrences(env)
    assert rows["2026-07-21"].state == "completed" and rows["2026-07-21"].deadline_missed_at is not None
    assert rows["2026-07-28"].state == "due"
    assert _scheduled(env, datetime(2026, 7, 28, 11, 30, tzinfo=UTC)) == 0  # the cron's next firing
    days = [r.config_snapshot["occurrence"]["day"] for r in env.runs()]
    assert days == ["2026-07-14", "2026-07-21", "2026-07-28"]
    assert _occurrences(env)["2026-07-28"].state == "completed"


def _exported(env: Env, run_id: str) -> tuple[dict[str, dict[str, str]], dict[str, Any]]:
    exports = env.data / "runs" / STORE_KEY / run_id / "exports"
    products = json.loads((exports / "products.json").read_text("utf-8"))
    log = json.loads((exports / "provenance.json").read_text("utf-8"))
    by_title = {p["product_title"]: p for p in products}
    assert all(list(p) == list(OUTPUT_FIELDS) for p in products)  # never an extra field
    return by_title, log


def test_a_verified_product_without_a_local_offer_keeps_its_identity_never_another_price(
    env: Env, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SYNTHETIC transitions: a verified product shown later only by a marketplace seller (shipping), and a
    verified product shown out of stock with no price; a product never seen with a local offer stays out."""
    env.edit(categories=[0])
    assert env.result("run", "--store", STORE_KEY)[0] == 0
    first = env.runs()[0]
    marketplace = syn.Item(
        "7201", "Chips, 8 oz", "$1.50", seller="Other Seller LLC", lines=(("SHIPPING", "0"),)
    )
    gone = syn.Item("7101", "Milk, Gallon, 128 fl oz", "", lines=(), availability="OUT_OF_STOCK")
    monkeypatch.setitem(PAGES, SNACKS, [[marketplace, PAGES[SNACKS][0][1]], PAGES[SNACKS][1]])
    still = syn.Item("7102", "Milk, Half Gallon, 64 fl oz", "$1.99", unit="3.1 ¢/fl oz")
    monkeypatch.setitem(PAGES, MILK, [[still, gone]])  # the page keeps a priced product (the canary)
    assert env.result("run", "--store", STORE_KEY)[0] in (0, 6)
    second = env.runs()[-1]
    factory = sessionmaker(env.engine, expire_on_commit=False)
    with factory() as s:
        rows = {r.upc: r for r in s.scalars(select(RecordRow).where(RecordRow.run_id == second.id))}
        obs = {
            o.upc: o
            for o in s.scalars(select(ProductObservation).where(ProductObservation.run_id == second.id))
        }
    chips = rows["wm:7201"]
    assert chips.status == "exported_not_valid" and "NO_LOCAL_OFFER" in chips.flags
    assert chips.record["regular_price"] == "" and chips.record["ppm"] == ""  # never the marketplace $1.50
    assert chips.record["product_title"] == "Chips, 8 oz" and chips.record["weight"] == "8 oz"
    assort = obs["wm:7201"].provenance["assortment"]
    assert assort["status"] == "verified_earlier" and assort["verified"]["run_id"] == first.id
    assert assort["verified"]["regular_price"] == "2.12"  # the earlier observation, kept apart, dated
    milk = rows["wm:7101"]  # available -> unavailable at the store: kept, flagged, no price
    assert (
        milk.status == "exported_not_valid"
        and "OUT_OF_STOCK" in milk.flags
        and milk.record["regular_price"] == ""
    )
    market = rows["wm:7202"]  # a marketplace item never offered locally: not claimed as the store's
    assert market.status == "excluded" and "ASSORTMENT_UNRESOLVED" in market.reasons
    by_title, log = _exported(env, second.id)
    assert (
        by_title["Chips, 8 oz"]["regular_price"] == "" and by_title["Milk, Gallon, 128 fl oz"]["crawl_date"]
    )
    assert log["records"]["wm:7201"]["observation_kind"] == "fresh"
    assert log["records"]["wm:7201"]["assortment"]["status"] == "verified_earlier"
    assert "Market Snack, 1 ct" not in by_title
    with factory() as s:
        stores = s.scalar(select(func.count()).select_from(Store))
        pointer = s.get(PublicationPointer, first.store_id)
    assert stores == 1 and pointer is not None and pointer.publication_id  # the first run stays published


def test_products_missing_from_a_partial_run_are_carried_forward_and_repeated_runs_keep_identities(
    env: Env,
) -> None:
    """SYNTHETIC: a complete run, then a run narrowed to one category (a pilot) that does not observe the
    other category's products, then a complete run again."""
    assert env.result("run", "--store", STORE_KEY)[0] == 0
    first = env.runs()[0]
    assert env.result("run", "--store", STORE_KEY, "--categories", "4")[0] == 0
    partial = env.runs()[-1]
    factory = sessionmaker(env.engine, expire_on_commit=False)
    with factory() as s:
        before = {r.upc: r for r in s.scalars(select(RecordRow).where(RecordRow.run_id == first.id))}
        rows = {r.upc: r for r in s.scalars(select(RecordRow).where(RecordRow.run_id == partial.id))}
    assert rows["wm:7301"].status == "valid"  # observed by the partial run
    for key in ("wm:7101", "wm:7201", "wm:7203"):  # verified earlier, not observed now: carried forward
        row = rows[key]
        assert row.status == "historical" and "CARRIED_FORWARD" in row.flags
        assert row.record == before[key].record  # unchanged, its own crawl date and prices
        hist = row.provenance["historical"]
        assert hist["run_id"] == first.id and "was not read by this run" in hist["why_not_observed"]
    assert "wm:7202" not in rows  # never verified: nothing to carry
    by_title, log = _exported(env, partial.id)
    assert {"Milk, Gallon, 128 fl oz", "Chips, 8 oz", "Pretzels, 16 oz", "Diapers, Size 1, 84 Count"} <= set(
        by_title
    )
    assert log["records"]["wm:7101"]["observation_kind"] == "carried_forward"
    assert log["counts"]["observed"]["carried_forward"] == 3 and log["counts"]["observed"]["fresh"] == 1
    # The carried-forward records are checked against the pages of the run that observed them.
    code, res = env.result("validate-export", "--run", partial.id)
    assert code == 0, res
    assert res["source_check"]["summary"] == {"records": 4, "verified": 4, "mismatch": 0, "unverified": 0}
    assert res["source_check"]["runs_whose_pages_were_read"] == sorted({first.id, partial.id})
    assert env.result("run", "--store", STORE_KEY)[0] == 0
    third = env.runs()[-1]
    with factory() as s:
        again = {r.upc: r for r in s.scalars(select(RecordRow).where(RecordRow.run_id == third.id))}
    assert {k for k, r in again.items() if r.status in ("valid", "exported_not_valid")} == {
        k for k, r in before.items() if r.status in ("valid", "exported_not_valid")
    }  # a repeated complete run observes the same identities again, fresh
    assert not any(r.status == "historical" for r in again.values())


def test_an_export_task_stopped_half_way_never_blocks_the_partial_export(
    env: Env, monkeypatch: pytest.MonkeyPatch
) -> None:
    from walmart_headless.worker.pipeline import Pipeline

    async def half_written(self: Pipeline, ctx: Any) -> dict[str, Any]:
        self.storage.put_bytes(
            f"{self.prefix(ctx.run_id)}/exports/provenance.json", b"{}", "application/json"
        )
        raise RuntimeError("the export task stopped half-way")

    monkeypatch.setattr(Pipeline, "h_export", half_written)
    code, lines = env.cli("run", "--store", STORE_KEY)
    assert code == 6 and not any(x["event"] == "UNEXPECTED" for x in lines)
    [run] = env.runs()
    assert run.status == "rejected"
    partial = [x for x in lines if x["event"] == "PARTIAL_EXPORT"]
    assert partial and "/exports-" in partial[0]["data"]["manifest"]
    code, res = env.result("validate-export", "--run", run.id)
    assert res["manifest"]["problems"] == []


def test_a_run_narrowed_on_the_command_line_is_a_pilot_and_never_published(env: Env) -> None:
    code, _ = env.result("run", "--store", STORE_KEY, "--categories", "4")  # no limit, one category
    assert code == 0
    [run] = env.runs()
    assert run.config_snapshot["pilot"] is True and run.status != "published"
    assert not (env.data / "published").exists()


def test_a_follow_up_page_budget_makes_the_run_a_pilot_and_never_published(env: Env) -> None:
    """Release 1.3.1: the follow-up page budget is a named pilot budget (1.3.0 did not count it)."""
    code, _ = env.result("run", "--store", STORE_KEY, "--follow-up-pages", "1")
    assert code == 0
    [run] = env.runs()
    assert run.config_snapshot["pilot"] is True
    assert run.config_snapshot["pilot_budgets"] == {"follow_up.max_pages": 1}
    assert run.status != "published" and not (env.data / "published").exists()
    code, res = env.result("follow-ups", "--store", STORE_KEY, "--state", "all")
    assert code == 0 and res["store"] == STORE_KEY and res["listed"]["rows"] == res["total"]
    assert len(res["candidates"]) == res["total"]


class _ExecutionClock:
    """An injected monotonic clock for one test (SYNTHETIC time: a page can "take" an hour)."""

    def __init__(self) -> None:
        self.t = 1000.0

    def __call__(self) -> float:
        return self.t


def _slow_first_page(clock: _ExecutionClock, url_prefix: str, seconds: float) -> Any:
    def override(url: str) -> httpx.Response | None:
        if url.startswith(url_prefix):
            clock.t += seconds
        return None

    return override


def test_an_execution_limit_pauses_the_run_and_the_next_execution_continues_the_same_run(
    env: Env, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SYNTHETIC: one execution is limited to 60 minutes; the first listing page advances the injected
    execution clock past it. The run pauses resumably (not finalized, not published); ``resume`` continues
    the same run: its checkpoints, counters and pending product pages carry over, nothing is read twice."""
    from walmart_headless.collection import base as base_mod

    clock = _ExecutionClock()
    monkeypatch.setattr(base_mod, "monotonic", clock)
    env.edit(limits={"max_run_minutes": 2880, "max_segment_minutes": 60})
    env.mock.page_override = _slow_first_page(clock, MILK, 3601)
    code, _ = env.result("run", "--store", STORE_KEY)
    [run] = env.runs()
    assert code == 75 and run.status == "interrupted" and run.stop_code == "SEGMENT_DURATION_LIMIT"
    assert not (env.data / "published").exists()  # never finalized or published at a segment's end
    env.mock.page_override = None
    code, _ = env.result("resume", "--store", STORE_KEY)
    [same] = env.runs()
    assert code == 0 and same.id == run.id and same.status == "published"
    factory = sessionmaker(env.engine, expire_on_commit=False)
    with factory() as s:
        segs = list(s.scalars(select(CollectionSegment).where(CollectionSegment.run_id == run.id)))
        rows = list(s.scalars(select(RecordRow).where(RecordRow.run_id == run.id)))
    assert len(segs) == 2 and segs[0].stop_code == "SEGMENT_DURATION_LIMIT"
    assert len({r.upc for r in rows}) == len(rows)  # no product recorded twice
    listing_calls = [c[2] for c in env.mock.calls if c[1] == "/plugin/walmart/store" and "/browse/" in c[2]]
    assert len(listing_calls) == len(set(listing_calls))  # no result page requested twice
    detail_calls = [c[2] for c in env.mock.calls if "/ip/" in c[2]]
    assert len(detail_calls) == len(set(detail_calls)) == 4  # each product page read once, across both
    assert {r.provenance["upc_detail"]["status"] for r in rows if r.status != "excluded"} <= {
        "extracted",
        "absent_in_source",
    }


def test_a_scheduled_run_longer_than_one_execution_is_continued_by_later_firings_inside_the_window(
    env: Env, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SYNTHETIC: the occurrence's first execution pauses at its 60-minute limit; a firing outside the
    daily window does nothing; a firing inside the next day's window continues the same run (its original
    occurrence and scope) to its end; the next occurrence starts a new run."""
    from walmart_headless.collection import base as base_mod

    clock = _ExecutionClock()
    monkeypatch.setattr(base_mod, "monotonic", clock)
    env.edit(
        schedule={"enabled": True, "weekdays": [1], "start_time": "06:00", "window_end": "18:00"},
        limits={"max_run_minutes": 2880, "max_segment_minutes": 60},
    )
    env.mock.page_override = _slow_first_page(clock, MILK, 3601)
    tuesday = datetime(2026, 7, 14, 11, tzinfo=UTC)  # 06:00 in Chicago (CDT)
    assert _scheduled(env, tuesday) == 75
    [run] = env.runs()
    assert run.status == "interrupted" and run.stop_code == "SEGMENT_DURATION_LIMIT"
    env.mock.page_override = None
    calls = len(env.mock.calls)
    assert _scheduled(env, datetime(2026, 7, 15, 3, tzinfo=UTC)) == 0  # 22:00 local: window closed
    assert len(env.mock.calls) == calls and env.runs()[0].status == "interrupted"
    assert _scheduled(env, datetime(2026, 7, 15, 14, tzinfo=UTC)) == 0  # Wednesday 09:00 local: continue
    [same] = env.runs()
    assert same.id == run.id and same.status == "published"
    assert same.config_snapshot["occurrence"]["day"] == "2026-07-14"  # the same logical run and scope
    with sessionmaker(env.engine)() as s:
        segs = list(s.scalars(select(CollectionSegment).where(CollectionSegment.run_id == run.id)))
    assert len(segs) == 2
    assert _scheduled(env, datetime(2026, 7, 21, 11, tzinfo=UTC)) == 0  # the next occurrence: a new run
    first, second = env.runs()
    assert first.id == run.id and second.id != run.id
    assert second.config_snapshot["occurrence"]["day"] == "2026-07-21"


# -- release 1.5.0: a scheduled occurrence keeps its identity until it has run
# ---------------------------------


def test_a_firing_after_the_tolerance_starts_the_occurrence_late_and_says_so(env: Env) -> None:
    """Before 1.5.0 a firing past the start tolerance found nothing due and the occurrence was gone."""
    env.edit(schedule={"enabled": True, "weekdays": [1], "start_time": "06:00"})
    assert _scheduled(env, datetime(2026, 7, 14, 13, tzinfo=UTC)) == 0  # 08:00 local: 120 minutes late
    [run] = env.runs()
    assert run.config_snapshot["occurrence"]["day"] == "2026-07-14" and run.status == "published"
    with sessionmaker(env.engine)() as s:
        [late] = s.scalars(select(Event).where(Event.run_id == run.id, Event.code == "OCCURRENCE_LATE"))
    assert 120 <= late.data["lateness_minutes"] < 125
    row = _occurrences(env)["2026-07-14"]
    assert row.state == "completed" and row.run_id == run.id


def test_starts_with_no_firing_wait_oldest_first_and_their_missed_deadlines_are_reported(env: Env) -> None:
    """The machine was off for two scheduled starts: each keeps its identity, the oldest runs first, and the
    status says how far behind the store is. Queuing does not meet the cadence: it reports the gap."""
    env.edit(schedule={"enabled": True, "weekdays": [1], "start_time": "06:00"})
    assert _scheduled(env, datetime(2026, 7, 14, 11, tzinfo=UTC)) == 0
    assert _scheduled(env, datetime(2026, 7, 29, 15, tzinfo=UTC)) == 0  # Wednesday: Tuesdays 21 and 28 passed
    assert [r.config_snapshot["occurrence"]["day"] for r in env.runs()] == ["2026-07-14", "2026-07-21"]
    rows = _occurrences(env)
    assert rows["2026-07-21"].state == "completed" and rows["2026-07-21"].deadline_missed_at is not None
    assert rows["2026-07-28"].state == "due" and rows["2026-07-28"].deadline_missed_at is None
    calls = len(env.mock.calls)
    code, status = env.result("schedule-status", "--store", STORE_KEY)
    assert code == 0 and len(env.mock.calls) == calls  # the status reads only
    assert status["waiting"] == ["2026-07-28"] and status["backlog"] == 1
    assert status["deadlines_missed"] == ["2026-07-21"] and status["capacity"].startswith("GAP")
    listed = {o["occurrence"]: o for o in status["occurrences"]}
    assert (
        listed["2026-07-21"]["run_status"] == "published" and listed["2026-07-21"]["lateness_minutes"] > 11000
    )
    assert _scheduled(env, datetime(2026, 7, 29, 15, 30, tzinfo=UTC)) == 0
    days = [r.config_snapshot["occurrence"]["day"] for r in env.runs()]
    assert days == ["2026-07-14", "2026-07-21", "2026-07-28"]
    assert env.result("schedule-status", "--store", STORE_KEY)[1]["backlog"] == 0


def test_a_backlog_across_a_clock_change_keeps_each_start_at_its_local_time(env: Env) -> None:
    """The machine was off across the change of 2026-11-01: the starts it missed are all there, each at 06:00
    local, so the two on standard time are an hour later in UTC than the one before."""
    env.edit(schedule={"enabled": True, "weekdays": [1], "start_time": "06:00"})
    assert _scheduled(env, datetime(2026, 10, 27, 11, tzinfo=UTC)) == 0
    assert _scheduled(env, datetime(2026, 11, 11, 15, tzinfo=UTC)) == 0  # Wednesday: Nov 3 and 10 have passed
    rows = _occurrences(env)
    assert [r.due_at.astimezone(UTC).hour for _, r in sorted(rows.items())] == [11, 12, 12]
    assert rows["2026-11-03"].deadline_missed_at is not None  # its deadline, Nov 10, passed while it waited
    assert rows["2026-11-10"].state == "due" and rows["2026-11-10"].deadline_missed_at is None


def test_an_unfinished_manual_run_defers_the_occurrence_with_the_reason(env: Env) -> None:
    env.edit(schedule={"enabled": True, "weekdays": [1], "start_time": "06:00"})
    env.mock.page_override = _raise_sigterm_on(SNACKS)
    assert env.cli("run", "--store", STORE_KEY)[0] == 75
    env.mock.page_override = None
    [manual] = env.runs()
    calls = len(env.mock.calls)
    assert _scheduled(env, datetime(2026, 7, 14, 11, tzinfo=UTC)) == 9
    assert len(env.mock.calls) == calls and [r.id for r in env.runs()] == [manual.id]
    row = _occurrences(env)["2026-07-14"]
    assert row.state == "deferred" and manual.id in str(row.reason)
    env.result("finalize", "--store", STORE_KEY)
    assert _scheduled(env, datetime(2026, 7, 14, 11, 30, tzinfo=UTC)) == 0
    assert _occurrences(env)["2026-07-14"].state == "completed"


def test_a_closed_window_defers_the_occurrence_to_the_next_window(env: Env) -> None:
    env.edit(schedule={"enabled": True, "weekdays": [1], "start_time": "06:00", "window_end": "18:00"})
    assert _scheduled(env, datetime(2026, 7, 15, 3, tzinfo=UTC)) == 0 and env.runs() == []  # 22:00 local
    row = _occurrences(env)["2026-07-14"]
    assert row.state == "deferred" and "window" in str(row.reason)
    assert _scheduled(env, datetime(2026, 7, 15, 14, tzinfo=UTC)) == 0  # Wednesday 09:00 local
    [run] = env.runs()
    assert run.config_snapshot["occurrence"]["day"] == "2026-07-14" and run.status == "published"


def test_registering_twice_adds_nothing_and_each_store_has_its_own_occurrences(env: Env) -> None:
    from walmart_headless.collection import occurrences
    from walmart_headless.collection.config import Schedule

    schedule = Schedule(enabled=True, weekdays=[1], start_time="06:00")
    tz = ZoneInfo("America/Chicago")
    now = datetime(2026, 7, 14, 11, tzinfo=UTC)
    assert env.result("sync-config")[0] == 0
    with sessionmaker(env.engine)() as s:
        store = s.scalar(select(Store).where(Store.key == STORE_KEY))
        assert store is not None
        other = Store(
            key="walmart-other-pickup",
            retailer=store.retailer,
            location_id="9999",
            division_number=store.division_number,
            store_number=store.store_number,
            expected_display_name="Another store",
            expected_postal_code="60000",
            modality=store.modality,
            timezone=store.timezone,
            enabled=False,
        )
        s.add(other)
        s.flush()
        for _ in range(2):
            assert [r.day for r in occurrences.register(s, store.id, schedule, tz, now)] == ["2026-07-14"]
        assert [r.day for r in occurrences.register(s, other.id, schedule, tz, now)] == ["2026-07-14"]
        rows = list(s.scalars(select(ScheduleOccurrence)))
        assert sorted(r.store_id for r in rows) == sorted([store.id, other.id])
        s.rollback()


def test_the_capacity_gap_is_measured_only_from_real_runs(env: Env) -> None:
    from walmart_headless.collection import occurrences
    from walmart_headless.collection.config import Schedule

    schedule = Schedule(enabled=True, weekdays=[1], start_time="06:00")
    tz = ZoneInfo("America/Chicago")
    assert env.result("sync-config")[0] == 0
    with sessionmaker(env.engine)() as s:
        store = s.scalar(select(Store).where(Store.key == STORE_KEY))
        assert store is not None
        now = datetime(2026, 7, 14, 11, tzinfo=UTC)
        assert occurrences.status(s, store.id, schedule, tz, now, enabled=True)["capacity"].startswith(
            "UNKNOWN"
        )
        [row] = occurrences.register(s, store.id, schedule, tz, now)
        row.state, row.started_at = "completed", now
        row.finished_at = now + timedelta(days=8)  # ended a day after the next start
        got = occurrences.status(s, store.id, schedule, tz, now, enabled=True)
        assert got["capacity"].startswith("GAP") and got["runs_past_next_start"][0]["over_by_minutes"] == 1440
        row.finished_at = now + timedelta(days=1)
        got = occurrences.status(s, store.id, schedule, tz, now, enabled=True)
        assert got["capacity"].startswith("UNKNOWN")  # no run of its full scope measured the time it takes
        s.rollback()


def test_a_schedule_never_runs_a_narrowed_scope_and_the_zero_page_setting_is_gone(env: Env) -> None:
    env.edit(schedule={"enabled": True, "weekdays": [1], "start_time": "06:00"}, detail={"enabled": False})
    assert env.cli("run", "--store", STORE_KEY, "--scheduled")[0] == 2
    assert env.runs() == [] and env.mock.calls == []
    assert env.result("validate-config")[0] == 2
    env.edit(detail={"max_per_run": 0})
    assert env.cli("validate-config")[0] == 2  # the configuration file refuses it
    env.edit(detail={"max_per_run": None})
    assert env.result("validate-config")[0] == 0
    env.edit(schedule={"enabled": False})
    code, _ = env.result("run", "--store", STORE_KEY, "--pdp-sample", "0")
    assert code == 2 and env.mock.calls == []
    with pytest.raises(SystemExit):
        main(["--config", str(env.config), "run", "--store", STORE_KEY, "--pilot-detail-pages", "0"])
    assert env.runs() == [] and env.mock.calls == []


def test_a_pilot_budget_is_named_on_the_run_and_never_published(env: Env) -> None:
    code, _ = env.result("run", "--store", STORE_KEY, "--pilot-detail-pages", "1")
    assert code == 0
    [run] = env.runs()
    assert run.config_snapshot["pilot"] is True and run.status == "validated"
    assert run.config_snapshot["pilot_budgets"] == {"detail.max_per_run": 1}
    code, table = env.result("field-dispositions", "--run", run.id)
    assert code == 0 and table["counts"]["upc"] == {"budget_deadline_interruption": 3, "fetched_detail": 1}
    [read] = [r for r in table["rows"] if r["upc"]["disposition"] == "fetched_detail"]
    calls = len(env.mock.calls)
    code, _ = env.result("run", "--store", STORE_KEY, "--pilot-no-detail")
    assert code == 0
    last = env.runs()[-1]
    assert last.config_snapshot["pilot_budgets"] == {"detail.enabled": "off"}
    assert [c for c in env.mock.calls[calls:] if "/ip/" in c[-1]] == []  # no product page: (role, path, url)
    code, table = env.result("field-dispositions", "--run", last.id)
    # Release 1.6.3: reading off requests no product page, but the product whose page the first run read keeps
    # that read's UPC, named as that read (its run); the three that no read answers for are not attempted, and
    # say why. Until 1.6.2 all four were "not attempted": the UPC the first run read was exported blank.
    assert code == 0 and table["counts"]["upc"] == {"not_attempted": 3, "recovered_from_saved_detail": 1}
    unread = [r for r in table["rows"] if r["upc"]["disposition"] == "not_attempted"]
    assert {r["upc"]["reason"] for r in unread} == {"product detail reading is off"}
    [kept] = [r for r in table["rows"] if r["upc"]["disposition"] == "recovered_from_saved_detail"]
    assert kept["key"] == read["key"] and kept["upc"]["value"] == read["upc"]["value"] != ""
    assert kept["upc"]["source_run"] == run.id
    # The store's queue: the three unread products wait for a run that reads product pages; the product the
    # saved read answers for is resolved by it, as production's reuse resolves it (until 1.6.2 the reading-off
    # run put it back to pending, having set its read aside).
    code, res = env.result("follow-ups", "--store", STORE_KEY, "--kind", "detail")
    assert code == 0 and res["by_kind_and_state"] == {"detail:pending": 3, "detail:resolved": 1}
