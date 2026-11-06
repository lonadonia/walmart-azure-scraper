"""The Walmart collector with Scrape.do through the run pipeline, against the in-memory mock of Scrape.do's
API serving SYNTHETIC Walmart pages (tests/mock_scrapedo.py). Nothing here reaches Scrape.do or Walmart."""

from __future__ import annotations

import asyncio
import json
from datetime import timedelta
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from tests import mock_scrapedo
from tests import synthetic_walmart as syn
from tests.conftest import CONFIG, STORE_KEY
from tests.integration.helpers import seed
from tests.mock_scrapedo import DIAPERING, MILK, PRIMARY, SNACKS, MockScrapeDo
from tests.mock_scrapedo import product_page as mock_product_page
from walmart_headless.acquisition import scrapedo as sd
from walmart_headless.acquisition import scrapedo_session as sds
from walmart_headless.collection import reconcile
from walmart_headless.collection.config import CollectionConfig, DetailConfig, Limits
from walmart_headless.collection.nodes import Node
from walmart_headless.collection.walmart import WalmartCollector
from walmart_headless.config_file import CanaryConfig
from walmart_headless.core.settings import load_private_label, load_settings, load_stores
from walmart_headless.core.timeutil import utcnow
from walmart_headless.db.models import (
    AuditLog,
    CategorySource,
    Event,
    NodeCoverage,
    PageFetch,
    ProductObservation,
    ProviderKey,
    ProviderUsage,
    RecordRow,
    Run,
    SettingRow,
    StoreAttestation,
    Task,
    ValidationFinding,
)
from walmart_headless.storage.local import LocalStorageAdapter
from walmart_headless.worker import runner
from walmart_headless.worker.pipeline import Pipeline

pytestmark = [pytest.mark.postgres]


@pytest.fixture
def env(migrated_engine: Engine, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    factory, _ = seed(migrated_engine)
    monkeypatch.setenv(sd.ENV_KEY, PRIMARY)
    monkeypatch.setattr(sd, "INFO_MIN_INTERVAL_S", 0.0)
    mock = MockScrapeDo()
    monkeypatch.setattr(
        sd.Transport, "client_factory", lambda: httpx.AsyncClient(transport=httpx.MockTransport(mock.handler))
    )
    store = next(s for s in load_stores(CONFIG / "stores.yaml").stores if s.key == STORE_KEY)
    return {
        "engine": migrated_engine,
        "factory": factory,
        "storage": LocalStorageAdapter(tmp_path / "data"),
        "store": store,
        "private_label": load_private_label(CONFIG / "walmart_private_label_brands.yaml"),
        "mock": mock,
    }


def _nodes(factory: sessionmaker[Session]) -> list[Node]:
    with factory() as s:
        ids = {
            c.category_name: c.id
            for c in s.scalars(select(CategorySource).where(CategorySource.retailer == "walmart"))
        }
    return [
        Node(
            0,
            "Food",
            ids["Food"],
            "",
            "976759",
            "https://www.walmart.com/cp/food/976759",
            kind="landing",
            excluded=("Shop All Foods", "Recipes"),
        ),
        Node(4, "Diapering", ids["Diapering"], "", "5427_486190", DIAPERING),
    ]


def _run(
    env: dict[str, Any],
    *,
    limits: Limits | None = None,
    run_id: str | None = None,
    canary: CanaryConfig | None = None,
    detail: DetailConfig | None = None,
    workers: int = 1,
) -> tuple[str, str]:
    settings = load_settings(CONFIG / "settings.yaml")
    pipe = Pipeline(env["engine"], env["storage"], settings, env["store"], env["private_label"])
    cfg = CollectionConfig(limits=limits or Limits(), detail=detail or DetailConfig())
    resume = run_id is not None
    if run_id is None:
        nodes = _nodes(env["factory"])
        with env["factory"]() as s:
            run_id = pipe.create_live_run(
                s,
                nodes,
                trigger="manual",
                snapshot={
                    "plan": {"nodes": [n.as_dict() for n in nodes], "skipped": []},
                    "started_by": "test",
                    "retailer": "walmart",
                    "provider": "scrapedo",
                    "collection": cfg.model_dump(mode="json"),
                    "pilot": False,
                },
            )
            s.commit()
    collector = WalmartCollector(pipe, run_id, config=cfg, trigger="manual", canary=canary)
    status = asyncio.run(
        pipe.execute(run_id, "test-collector", resume=resume, collector=collector, workers=workers)
    )
    return run_id, status


def _failed_gates(s: Session, run_id: str) -> list[tuple[str, str, str]]:
    return [
        (f.gate, f.code, f.message[:160])
        for f in s.scalars(select(ValidationFinding).where(ValidationFinding.run_id == run_id))
        if f.severity == "FAIL"
    ]


def _usage(factory: sessionmaker[Session]) -> list[ProviderUsage]:
    with factory() as s:
        return list(s.scalars(select(ProviderUsage).order_by(ProviderUsage.at)))


def test_a_run_checks_every_page_against_the_store_and_charges_the_ledger(env: dict[str, Any]) -> None:
    run_id, _ = _run(env)
    with env["factory"]() as s:
        run = s.get(Run, run_id)
        assert run is not None and run.status == "validated", (
            run.status,
            run.stop_code,
            _failed_gates(s, run_id),
        )
        records = {r.upc: r for r in s.scalars(select(RecordRow).where(RecordRow.run_id == run_id))}
        assert {"wm:7101", "wm:7201", "wm:7301"} <= {k for k, r in records.items() if r.status == "valid"}
        assert records["wm:7202"].status == "excluded"  # a marketplace, shipping-only offer
        assert records["wm:7201"].record["sub_category"] == "Snacks"  # "Shop all" takes its group's name
        assert records["wm:7101"].record["sub_category"] == "Milk"
        assert records["wm:7203"].status != "valid" or "OUT_OF_STOCK" in (records["wm:7203"].flags or [])
        att = list(s.scalars(select(StoreAttestation).where(StoreAttestation.run_id == run_id)))
        names = {c["check"]: c["status"] for a in att for c in a.checks["checks"]}
        assert names.get("page_location_store") == "PASS" and names.get("page_intent") == "PASS"
        assert names.get("store_scoped_request") == "PASS"
        assert (run.counts or {})["canary"]["status"] == "passed"
        assert run.counts["collection_complete"] is True
        # The coverage rows of listings not read say why.
        reasons = {
            c.partition["url"]: (c.status, c.partition["reason"])
            for c in s.scalars(select(NodeCoverage).where(NodeCoverage.run_id == run_id))
        }
        # Release 1.6.8: the "Shop All" link of Dairy & Eggs is a category page of its own, read for the
        # listings its navigation names: Milk, which the Food page names too (read once, not twice).
        dairy = reasons["https://www.walmart.com/cp/dairy-eggs/9176907"]
        assert dairy[0] == "EXPANDED" and "names 1 links, 0 not named before in this row" in dairy[1], dairy
        assert all(reason for status, reason in reasons.values() if status == "SKIPPED")
    rows = _usage(env["factory"])
    assert rows and all(r.outcome != "reserved" for r in rows)  # every reservation settled
    assert all(r.cost_source == "header" for r in rows if r.credits)
    assert {r.endpoint for r in rows} == {"/", "/plugin/walmart/store"}
    calls = env["mock"].calls
    assert calls and all(c[0] == "primary" for c in calls)
    # Recipes (excluded by the CSV) was never requested; the Dairy & Eggs category page once, through the
    # general API like every category page, and Milk's one result page once.
    assert not any(urlsplit(c[2]).path == "/i/recipes" for c in calls)
    assert [c[1] for c in calls if urlsplit(c[2]).path == "/cp/dairy-eggs/9176907"] == ["/"]
    assert len([c for c in calls if urlsplit(c[2]).path == "/browse/food/milk/976759_9176907"]) == 1


def test_every_result_page_is_requested_with_walmarts_pickup_filter_and_its_grid_is_recorded(
    env: dict[str, Any],
) -> None:
    # Release 1.4.1 (live 2026-10-28): the store endpoint sets the store only, and its result pages were the
    # store's unfiltered grid (Laundry: 18,682 results reported; 624 in the Pickup grid the Oxylabs Web API
    # returned). Each result page is requested with Walmart's own facet for the store's fulfillment; a
    # product page has no grid and is not. The page is kept under the collector's own URL (a replay finds it).
    run_id, status = _run(env)
    assert status == "validated"
    asked = [(path, u) for _, path, u in env["mock"].calls]
    listings = [u for path, u in asked if "/browse/" in u]
    assert listings and all(path == "/plugin/walmart/store" for path, u in asked if "/browse/" in u)
    assert all(
        "fulfillment_method:Pickup" in parse_qs(urlsplit(u).query)["facet"][0].split("||") for u in listings
    )
    assert all("facet" not in parse_qs(urlsplit(u).query) for _, u in asked if "/browse/" not in u)
    with env["factory"]() as s:
        kept = list(
            s.scalars(select(PageFetch.url).where(PageFetch.run_id == run_id, PageFetch.purpose == "listing"))
        )
        ledger = list(
            s.scalars(
                select(ProviderUsage.target_url).where(
                    ProviderUsage.run_id == run_id, ProviderUsage.purpose == "listing"
                )
            )
        )
        rows = reconcile.reconcile(s, run_id)["rows"]
    assert kept and not any("facet" in parse_qs(urlsplit(u).query) for u in kept)
    assert sorted(ledger) == sorted(listings)  # the spending ledger names the page the provider was asked for
    read = [r for r in rows if r["pages_visited"]]
    assert read and all(r["grid_fulfillment_filter"] == ["Pickup"] * len(r["pages_visited"]) for r in read)


def test_the_key_comes_from_a_mounted_secret_file_and_is_never_stored(
    env: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    secret = tmp_path / "scrapedo-api-key"
    secret.write_text(PRIMARY + "\n", encoding="utf-8")
    monkeypatch.delenv(sd.ENV_KEY)
    monkeypatch.setenv(sd.ENV_KEY_FILE, str(secret))
    _run(env)
    with env["factory"]() as s:
        keys = list(s.scalars(select(ProviderKey)))
        assert [(k.role, k.fingerprint) for k in keys] == [("primary", sd.load_keys()[0].fingerprint)]
        dumped = json.dumps(
            [[r.target_url, r.request_id, r.key_fingerprint] for r in s.scalars(select(ProviderUsage))]
            + [[a.reason, a.data] for a in s.scalars(select(AuditLog))]
            + [[e.message, e.data] for e in s.scalars(select(Event))]
            + [[r.key, r.value] for r in s.scalars(select(SettingRow))],
            default=str,
        )
    assert PRIMARY not in dumped
    for f in Path(env["storage"].root).rglob("*"):
        if f.is_file():
            assert PRIMARY.encode() not in f.read_bytes()


def test_a_page_shown_for_shipping_not_pickup_stops_before_any_record(env: dict[str, Any]) -> None:
    env["mock"].intent = "SHIPPING"
    run_id, status = _run(env)
    with env["factory"]() as s:
        run = s.get(Run, run_id)
        assert run is not None and run.stop_code == "STORE_NOT_VERIFIED" and status == "rejected"
        assert s.scalar(select(func.count()).select_from(RecordRow).where(RecordRow.run_id == run_id)) == 0


def test_an_exhausted_key_stops_the_run_resumably_and_nothing_else_is_tried(env: dict[str, Any]) -> None:
    # robots (1) + store page (1) + two pages (20), then nothing left; release 1.6.8: one credit more for the
    # Dairy & Eggs category page the Food page links (read for the listings it names)
    env["mock"].remaining[PRIMARY] = 26
    run_id, status = _run(env)
    assert status == "interrupted"
    assert {c[0] for c in env["mock"].calls} == {"primary"}
    with env["factory"]() as s:
        run = s.get(Run, run_id)
        assert run is not None and run.stop_code == "CREDITS_EXHAUSTED"
        key = s.get(ProviderKey, ("scrapedo", "primary"))
        assert key is not None and key.exhausted_at is not None
    # Credits again (a new month): the run resumes from its checkpoint and no product is recorded twice.
    env["mock"].remaining[PRIMARY] = 1000
    with env["factory"]() as s:
        key = s.get(ProviderKey, ("scrapedo", "primary"))
        assert key is not None
        key.exhausted_at = None  # what the free /info reading does when it shows credits again
        s.commit()
    _, status = _run(env, run_id=run_id)
    with env["factory"]() as s:
        run = s.get(Run, run_id)
        assert run is not None and run.status == "validated", _failed_gates(s, run_id)
        upcs = list(s.scalars(select(RecordRow.upc).where(RecordRow.run_id == run_id)))
        assert len(upcs) == len(set(upcs))


def test_a_balance_error_the_account_does_not_confirm_never_marks_the_key(env: dict[str, Any]) -> None:
    def refuse(url: str) -> httpx.Response | None:
        if "/browse/" in url:
            return httpx.Response(
                401, json={"Message": "You have no credits"}, headers={"Scrape.do-Request-Cost": "0"}
            )
        return None

    env["mock"].page_override = refuse  # but /info still shows 1000 credits
    run_id, _ = _run(env)
    with env["factory"]() as s:
        exhausted = select(func.count()).select_from(ProviderKey).where(ProviderKey.exhausted_at.is_not(None))
        assert s.scalar(exhausted) == 0
        run = s.get(Run, run_id)
        assert run is not None and run.stop_code == "CREDITS_EXHAUSTED"


def test_a_rate_limit_is_retried_and_a_site_refusal_stops_the_run(
    env: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sd, "MAX_RETRY_AFTER_S", 0.0)
    seen: dict[str, int] = {}

    def flaky(url: str) -> httpx.Response | None:
        if "/cp/food/" in url:
            seen[url] = seen.get(url, 0) + 1
            if seen[url] == 1:  # Scrape.do's concurrency limit, once
                return httpx.Response(
                    429, text="slow down", headers={"Retry-After": "1", "Scrape.do-Request-Cost": "0"}
                )
        if url.startswith(SNACKS):  # Walmart's own refusal, delivered by the provider
            return httpx.Response(200, text=syn.CHALLENGE_PAGE, headers={"Scrape.do-Request-Cost": "10"})
        return None

    env["mock"].page_override = flaky
    run_id, _ = _run(env)
    assert sum(1 for c in env["mock"].calls if "/cp/food/" in c[2]) == 2  # the rate limit, then the page
    with env["factory"]() as s:
        run = s.get(Run, run_id)
        assert run is not None and run.stop_code == "SITE_REFUSAL" and run.status == "rejected"


def test_the_credit_ceiling_stops_a_run_before_a_request_could_pass_it(env: dict[str, Any]) -> None:
    with env["factory"]() as s:
        sd.set_ceiling(s, 15, "test ceiling", "test")
        s.commit()
    run_id, _ = _run(env)
    assert sum(r.credits for r in _usage(env["factory"])) <= 15
    with env["factory"]() as s:
        run = s.get(Run, run_id)
        assert run is not None and run.stop_code == "SPENDING_CEILING", run.stop_code


def test_a_first_page_that_differs_from_its_own_data_fails_the_canary(
    env: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The automated canary compares the first recorded page's valid records with the page's item data,
    read independently of the parser. A parser that misreads a price stops the run before the next page."""
    from walmart_headless.checks import source_check

    real = source_check.compare

    def disagreeing(rec: dict[str, Any], item: dict[str, Any]) -> Any:
        checks, expected = real(rec, item)
        return {**checks, "regular_price": False}, expected

    monkeypatch.setattr(source_check, "compare", disagreeing)
    run_id, status = _run(env)
    with env["factory"]() as s:
        run = s.get(Run, run_id)
        assert run is not None and status == "rejected" and run.stop_code == "CANARY_CHECK_FAILED"
        assert (run.counts or {})["canary"]["status"] == "failed"
        codes = list(s.scalars(select(Event.code).where(Event.run_id == run_id)))
        assert "CANARY_FAILED" in codes
    listings = [c for c in env["mock"].calls if c[1] == "/plugin/walmart/store" and "/browse/" in c[2]]
    assert len(listings) == 1  # nothing after the canary page


def test_a_request_cancelled_in_flight_keeps_its_cost_as_unknown_and_a_stale_one_is_closed(
    env: dict[str, Any],
) -> None:
    factory = env["factory"]
    ledger = sd.Ledger(factory, sd.load_keys())
    sent = asyncio.Event()

    async def never_answers(request: httpx.Request) -> httpx.Response:
        sent.set()
        await asyncio.sleep(30)
        return httpx.Response(200, text="late")

    async def stop_while_in_flight() -> None:
        http = httpx.AsyncClient(transport=httpx.MockTransport(never_answers))
        t = sd.Transport(ledger, run_id=None, retailer="walmart", client=http)
        params = {"url": MILK, "storeid": "3891", "zipcode": "60085"}
        task = asyncio.create_task(t.fetch(sd.Request(sd.WALMART_STORE_ENDPOINT, params, 10.0, "listing")))
        await sent.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        await t.aclose()

    asyncio.run(stop_while_in_flight())
    rows = _usage(factory)
    # The provider may still have answered and charged: the reserved cost stays, marked unknown.
    assert [(r.outcome, r.credits, r.cost_source) for r in rows] == [("cancelled", 10.0, "unknown")]
    with factory() as s:
        s.add(
            ProviderUsage(
                provider="scrapedo",
                key_role="primary",
                key_fingerprint="x",
                purpose="listing",
                endpoint=sd.WALMART_STORE_ENDPOINT,
                target_url=MILK,
                outcome="reserved",
                credits=10.0,
                cost_source="reserved",
                at=utcnow() - timedelta(seconds=sd.STALE_RESERVATION_S + 60),
            )
        )
        s.commit()
    key = sd.load_keys()[0]
    fresh = ledger.reserve(
        key, 10.0, run_id=None, retailer="walmart", purpose="listing", endpoint="/", target_url="", attempt=1
    )
    with factory() as s:
        outcomes = sorted((r.outcome, r.cost_source) for r in s.scalars(select(ProviderUsage)))
        assert outcomes == [("abandoned", "unknown"), ("cancelled", "unknown"), ("reserved", "reserved")]
        assert s.get(ProviderUsage, fresh) is not None


def test_a_slow_answer_keeps_the_task_lease_and_no_page_is_requested_twice(
    env: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runner.Worker.__init__, "__kwdefaults__", {"lease_s": 2.0, "group": None})
    monkeypatch.setattr(sds, "KEEPALIVE_S", 0.3)
    mock: MockScrapeDo = env["mock"]

    async def slow(request: httpx.Request) -> httpx.Response:
        if request.url.params.get("url", "").startswith(MILK):
            await asyncio.sleep(4.0)  # longer than the lease
        return mock.handler(request)

    monkeypatch.setattr(
        sd.Transport, "client_factory", lambda: httpx.AsyncClient(transport=httpx.MockTransport(slow))
    )
    run_id, _ = _run(env)
    with env["factory"]() as s:
        codes = list(s.scalars(select(Event.code).where(Event.run_id == run_id)))
        assert "TASK_LEASE_LOST" not in codes and "TASK_LEASE_RECLAIMED" not in codes
        run = s.get(Run, run_id)
        assert run is not None and run.status == "validated", _failed_gates(s, run_id)
    assert sum(1 for c in mock.calls if c[2].startswith(MILK)) == 1


def _records(env: dict[str, Any], run_id: str) -> dict[str, RecordRow]:
    with env["factory"]() as s:
        return {r.upc: r for r in s.scalars(select(RecordRow).where(RecordRow.run_id == run_id))}


def _detail_calls(env: dict[str, Any]) -> list[tuple[str, str]]:
    """(endpoint, item id) of every product page the mock answered."""
    return [
        (c[1], urlsplit(c[2]).path.rstrip("/").rsplit("/", 1)[-1])
        for c in env["mock"].calls
        if "/ip/" in c[2]
    ]


def test_every_exported_product_gets_the_upc_its_own_page_states_through_the_pipeline(
    env: dict[str, Any],
) -> None:
    run_id, status = _run(env)
    assert status == "validated"
    rows = _records(env, run_id)
    assert rows["wm:7101"].record["upc"] == "078742371245"
    assert rows["wm:7201"].record["upc"] == "028400090896"
    assert rows["wm:7203"].record["upc"] == "001234567890"  # leading zeros exactly as the page writes them
    assert all(r.upc.startswith("wm:") for r in rows.values())  # the identity stays the item id, never a UPC
    d = rows["wm:7101"].provenance["upc_detail"]
    assert d["status"] == "extracted" and d["fresh"] is True and d["source"] == "page_data"
    assert d["path"] == "props.pageProps.initialData.data.product.upc" and d["http_status"] == 200
    assert d["body_sha256"] and d["page_fetch_id"] and d["requested_at"] and d["endpoint"] == "general"
    absent = rows["wm:7301"]  # its page names the item and states no UPC: absent from the source, not failed
    assert absent.record["upc"] == "" and absent.provenance["upc_detail"]["status"] == "absent_in_source"
    assert "upc_detail" not in (rows["wm:7202"].provenance or {})  # not exported: its page is never read
    calls = _detail_calls(env)
    assert sorted(i for _, i in calls) == ["7101", "7201", "7203", "7301"]  # each product page read once
    assert {e for e, _ in calls} == {"/"}  # the general API (1 credit): a UPC is not a store attribute
    detail_rows = [r for r in _usage(env["factory"]) if r.purpose == "product_detail"]
    assert len(detail_rows) == 4 and all(r.credits == 1 for r in detail_rows)
    exports = env["storage"].root / "runs" / STORE_KEY / run_id / "exports"
    products = json.loads((exports / "products.json").read_text("utf-8"))
    assert {p["upc"] for p in products} == {"078742371245", "028400090896", "001234567890", ""}
    log = json.loads((exports / "provenance.json").read_text("utf-8"))
    assert log["counts"]["upc_outcomes_of_fresh_exported"] == {"extracted": 3, "absent_in_source": 1}
    with env["factory"]() as s:
        run = s.get(Run, run_id)
        assert run is not None and run.counts["upc_detail"] == {"extracted": 3, "absent_in_source": 1}


def test_a_refused_failed_or_mismatched_detail_page_is_never_reported_as_absent(env: dict[str, Any]) -> None:
    def pages(url: str) -> httpx.Response | None:
        if "/ip/" not in url:
            return None
        item = urlsplit(url).path.rstrip("/").rsplit("/", 1)[-1]
        if item == "7101":  # a bot-manager page instead of the product
            return httpx.Response(200, text="<html><title>Robot or human?</title></html>")
        if item == "7201":  # a document without Walmart's page data
            return httpx.Response(200, text="<html><body>no data</body></html>")
        if item == "7203":  # another item's page (a redirect to another variant)
            return httpx.Response(200, text=mock_product_page("9999", "012345678905"))
        return httpx.Response(404, text="not found", headers={"Scrape.do-Request-Cost": "1"})

    env["mock"].page_override = pages
    run_id, status = _run(env)
    assert status == "validated"  # the listings' data stands; each product says what happened to its page
    rows = _records(env, run_id)
    outcome = {
        k: rows[k].provenance["upc_detail"]["status"] for k in ("wm:7101", "wm:7201", "wm:7203", "wm:7301")
    }
    assert outcome == {
        "wm:7101": "blocked",
        "wm:7201": "parse_failed",
        "wm:7203": "identity_mismatch",
        "wm:7301": "request_failed",
    }
    assert all(rows[k].record["upc"] == "" for k in outcome)  # never another item's UPC, never invented
    assert rows["wm:7203"].provenance["upc_detail"]["page_item"] == "9999"


def test_a_product_page_the_provider_never_brings_leaves_the_run_validated(env: dict[str, Any]) -> None:
    """Release 1.4.1: the provider fails one product page on every attempt, so no page is stored. That is
    the product's UPC outcome, not an integrity failure of the run (release 1.4.0 failed G13 and rejected
    the complete run, run 01M60JAPKBR4FNK22QMYTHNBSX). A page fetch without a stored document still fails
    G13 when an observation of the run names it as its source."""

    def fail(url: str) -> httpx.Response | None:
        if "/ip/" in url and urlsplit(url).path.rstrip("/").rsplit("/", 1)[-1] == "7101":
            return httpx.Response(502, text="provider failure", headers={"Scrape.do-Request-Cost": "0"})
        return None

    env["mock"].page_override = fail
    run_id, status = _run(env)
    with env["factory"]() as s:
        assert status == "validated", _failed_gates(s, run_id)
        run = s.get(Run, run_id)
        assert run is not None and run.counts["gates"]["G13"] == "PASS"
        bare = [
            pf
            for pf in s.scalars(select(PageFetch).where(PageFetch.run_id == run_id))
            if pf.dom_artifact_id is None
        ]
        assert [(pf.purpose, pf.url.split("?", 1)[0].rsplit("/", 1)[-1]) for pf in bare] == [
            ("product_detail", "7101")
        ]
    rows = _records(env, run_id)
    detail = rows["wm:7101"].provenance["upc_detail"]
    assert detail["status"] == "request_failed" and "502" in detail["reason"]
    assert rows["wm:7101"].status == "valid" and rows["wm:7101"].record["upc"] == ""
    assert sum(1 for _, i in _detail_calls(env) if i == "7101") == 3  # every attempt was made
    pipe = Pipeline(
        env["engine"],
        env["storage"],
        load_settings(CONFIG / "settings.yaml"),
        env["store"],
        env["private_label"],
    )
    with env["factory"]() as s:
        assert pipe.integrity(s, run_id) == (True, True, True)
        named = s.scalars(
            select(ProductObservation.page_fetch_id).where(ProductObservation.run_id == run_id)
        ).first()
        pf = s.get(PageFetch, named)
        assert pf is not None
        pf.dom_artifact_id = None  # an observation's page without its document
        s.flush()
        assert pipe.integrity(s, run_id) == (True, False, True)
        s.rollback()


def test_repeated_refusals_pause_detail_reading_and_say_so(env: dict[str, Any]) -> None:
    def refuse(url: str) -> httpx.Response | None:
        if "/ip/" in url:
            return httpx.Response(200, text="<html><title>Robot or human?</title></html>")
        return None

    env["mock"].page_override = refuse
    run_id, status = _run(env, detail=DetailConfig(pause_after_failures=3))
    # Since 1.5.0 a stopped product-page path fails the access check: the run is kept, never published.
    assert status == "rejected"
    with env["factory"]() as s:
        failed = {(g, c) for g, c, _ in _failed_gates(s, run_id)}
        assert ("G2", "DETAIL_PAUSED") in failed
        assert not {g for g, _ in failed} - {"G2", "G14"}  # G14 is the old contest check, never blocking
    rows = _records(env, run_id)
    statuses = sorted(r.provenance["upc_detail"]["status"] for r in rows.values() if r.status != "excluded")
    assert statuses == ["blocked", "blocked", "blocked", "not_attempted"]
    paused = next(
        r
        for r in rows.values()
        if r.provenance and r.provenance.get("upc_detail", {}).get("status") == "not_attempted"
    )
    assert paused.provenance["upc_detail"]["reason"].startswith("detail reading paused")
    assert len(_detail_calls(env)) == 3


def test_the_detail_limit_and_reuse_of_an_earlier_runs_upc_are_explicit(env: dict[str, Any]) -> None:
    first, _ = _run(env, detail=DetailConfig(max_per_run=2))
    rows = _records(env, first)
    outcomes = sorted(r.provenance["upc_detail"]["status"] for r in rows.values() if r.status != "excluded")
    assert outcomes.count("not_attempted") == 2 and len(_detail_calls(env)) == 2
    limited = [
        r for r in rows.values() if r.provenance and r.provenance["upc_detail"]["status"] == "not_attempted"
    ]
    assert all("detail limit (2 pages)" in r.provenance["upc_detail"]["reason"] for r in limited)
    env["mock"].calls.clear()
    second, _ = _run(env)
    again = _records(env, second)
    reused = [
        r for r in again.values() if r.provenance and r.provenance.get("upc_detail", {}).get("reused_from")
    ]
    fresh_reads = _detail_calls(env)
    assert len(reused) + len(fresh_reads) == 4 - 0 and len(fresh_reads) == 2  # only the pages not read before
    for r in reused:
        d = r.provenance["upc_detail"]
        assert d["status"] == "extracted" and d["fresh"] is False and d["reused_from"]["run_id"] == first
        assert r.record["upc"] == d["value"]


# -- release 1.6.8: subcategories linked as category pages of their own ------------------------------------

EGGS = "https://www.walmart.com/browse/food/eggs/976759_9176907_1001470"
CHEESE = "https://www.walmart.com/browse/food/shredded-cheese/976759_9176907_1001468_5"
DAIRY_PAGE = "https://www.walmart.com/cp/dairy-eggs/9176907"
CHEESE_PAGE = "https://www.walmart.com/cp/cheese/1001468"


def _dairy_tree(monkeypatch: pytest.MonkeyPatch) -> None:
    """SYNTHETIC. Dairy & Eggs, a category page of its own the Food page links ("Shop All"), names Milk (the
    Food page names it too), Eggs, a shop page, Recipes (the client's CSV excludes it) and Cheese, a category
    page of its own again, which names Shredded Cheese and links back to Dairy & Eggs."""
    pages = mock_scrapedo.CATEGORY_PAGES
    monkeypatch.setitem(
        pages,
        "/cp/dairy-eggs/9176907",
        mock_scrapedo.nav_page(
            [
                ("Milk", [("Milk", MILK)]),
                ("Eggs", [("Eggs", EGGS)]),
                ("Deals", [("Dairy deals", "/shop/dairy-deals")]),
                ("Recipes", [("Shop All", "/i/recipes")]),
                ("Cheese", [("Shop All", "/cp/cheese/1001468")]),
            ]
        ),
    )
    monkeypatch.setitem(
        pages,
        "/cp/cheese/1001468",
        mock_scrapedo.nav_page(
            [("Cheese", [("Shredded Cheese", CHEESE), ("Dairy & Eggs", "/cp/dairy-eggs/9176907")])]
        ),
    )
    eggs = syn.Item("7401", "Large White Eggs, 12 ct", "$2.98", unit="24.8 ¢/ea")
    cheese = syn.Item("7501", "Shredded Mozzarella Cheese, 8 oz", "$2.24", unit="28.0 ¢/oz")
    monkeypatch.setitem(mock_scrapedo.PAGES, EGGS, [[eggs]])
    monkeypatch.setitem(mock_scrapedo.PAGES, CHEESE, [[cheese]])
    monkeypatch.setitem(
        mock_scrapedo.LISTING_CATS, EGGS, ("Eggs", ["976759", "976759_9176907", "976759_9176907_1001470"])
    )
    monkeypatch.setitem(
        mock_scrapedo.LISTING_CATS,
        CHEESE,
        ("Shredded Cheese", ["976759", "976759_9176907", "976759_9176907_1001468_5"]),
    )
    monkeypatch.setitem(mock_scrapedo.PRODUCT_UPCS, "7401", "011110038364")
    monkeypatch.setitem(mock_scrapedo.PRODUCT_UPCS, "7501", "078742132723")


def test_a_subcategory_with_a_category_page_of_its_own_is_read_through_the_listings_it_names(
    env: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Release 1.6.8 (the coverage review of 1.6.7): a link of a row's navigation to a category page of its
    own (/cp/: Food's "Chips", "Cookies", "Soda", "Water" live) was skipped as "a category page or other page,
    not a product listing", so the listings only that page names were never read. The page is now read for
    the listings its own navigation names, each read as a listing of the row found on it; a page or listing
    named twice is read once, and a subcategory page of the page is read in turn."""
    _dairy_tree(monkeypatch)
    run_id, status = _run(env)
    calls = [urlsplit(c[2]).path for c in env["mock"].calls]
    with env["factory"]() as s:
        run = s.get(Run, run_id)
        assert run is not None and status == "validated", (status, _failed_gates(s, run_id))
        assert run.counts["collection_complete"] is True
        records = {r.upc: r for r in s.scalars(select(RecordRow).where(RecordRow.run_id == run_id))}
        for upc, sub in (("wm:7401", "Eggs"), ("wm:7501", "Shredded Cheese"), ("wm:7101", "Milk")):
            assert records[upc].status == "valid", (upc, records[upc].status)
            assert (records[upc].record["category"], records[upc].record["sub_category"]) == ("Food", sub)
        cov = {
            c.partition["url"]: c
            for c in s.scalars(select(NodeCoverage).where(NodeCoverage.run_id == run_id))
        }
        dairy, cheese_page = cov[DAIRY_PAGE], cov[CHEESE_PAGE]
        assert dairy.status == cheese_page.status == "EXPANDED"
        assert dairy.total_count is None and dairy.organic_upcs == 0  # a navigation page, never products
        # Milk and Recipes were named by the Food page: only what it did not name is added
        assert dairy.partition["children_named"] == ["976759_9176907_1001470", "dairy-deals", "1001468"]
        assert dairy.partition["reason"] == (
            "a category page of its own: its navigation names 5 links, 3 not named before in this row "
            "(2 to read)"
        )
        eggs, shredded = cov[EGGS], cov[CHEESE]
        assert (eggs.status, eggs.partition["via"], eggs.partition["found_on"]) == (
            "DONE",
            "subcategory_page",
            "9176907",
        )
        assert (shredded.status, shredded.partition["found_on"], shredded.partition["depth"]) == (
            "DONE",
            "1001468",
            2,
        )
        deals = cov["https://www.walmart.com/shop/dairy-deals"]
        assert (deals.status, deals.partition["reason"]) == (
            "SKIPPED",
            "a shop, brand, search, product or account page, not a category or result listing",
        )
        codes = [e.code for e in s.scalars(select(Event).where(Event.run_id == run_id))]
        assert codes.count("SUBCATEGORY_PAGE_READ") == 2 and "SUBCATEGORY_PAGE_NOT_READ" not in codes
        report = reconcile.reconcile(s, run_id)
    # each page once: Cheese's link back to Dairy & Eggs is not followed, Milk (named twice) is read once
    assert calls.count("/cp/dairy-eggs/9176907") == calls.count("/cp/cheese/1001468") == 1
    assert calls.count("/browse/food/milk/976759_9176907") == 1
    assert "/shop/dairy-deals" not in calls and "/i/recipes" not in calls
    food = next(r for r in report["csv_rows"] if r["csv_row"] == 0)
    assert food["complete"] is True and food["effective_status_counts"]["EXPANDED"] == 2, food
    row = next(r for r in report["rows"] if r["listing_id"] == "976759_9176907_1001470")
    assert (row["found_via"], row["found_on"], row["parent_listing"]) == ("subcategory_page", "9176907", None)
    assert row["navigation_evidence"].startswith(
        f"named by the subcategory page {DAIRY_PAGE} (listing 9176907)"
    )
    page_row = next(r for r in report["rows"] if r["listing_id"] == "9176907")
    assert page_row["status"] == page_row["status_rule_1_3_1"] == page_row["effective_status"] == "EXPANDED"


def test_a_subcategory_page_the_site_does_not_serve_keeps_its_row_incomplete(
    env: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Release 1.6.8: the listings a subcategory page names are part of the row, so a page the site answers
    with its not-found page is recorded with why and the row is never complete (the row's other listings
    are still read). Never an empty page, never a refusal."""
    monkeypatch.setitem(mock_scrapedo.CATEGORY_PAGES, "/cp/dairy-eggs/9176907", syn.not_found_page())
    run_id, _ = _run(env)
    with env["factory"]() as s:
        run = s.get(Run, run_id)
        assert run is not None and run.stop_code is None
        assert run.counts["collection_complete"] is False and run.counts["gates"]["G3"] == "FAIL"
        cov = {
            c.partition["url"]: c
            for c in s.scalars(select(NodeCoverage).where(NodeCoverage.run_id == run_id))
        }
        dairy = cov[DAIRY_PAGE]
        assert (dairy.status, dairy.partition["end"]) == ("INCOMPLETE", "NOT_FOUND")
        assert dairy.partition["reason"] == (
            "not read: the site answered this subcategory page with its not-found page "
            "(page data route /404, HTTP 200)"
        )
        assert cov[MILK].status == "DONE"  # the row's other listings are still read
        codes = [
            (e.code, (e.data or {}).get("listing"))
            for e in s.scalars(select(Event).where(Event.run_id == run_id))
        ]
        report = reconcile.reconcile(s, run_id)
    assert ("SUBCATEGORY_PAGE_NOT_READ", "9176907") in codes
    assert not [c for c, _ in codes if c == "CHALLENGE_DETECTED"]
    food = next(r for r in report["csv_rows"] if r["csv_row"] == 0)
    assert food["complete"] is False and "9176907 INCOMPLETE" in food["why_not_complete"], food


def test_a_subcategory_page_an_earlier_release_skipped_keeps_its_row_open_in_the_coverage_report(
    env: dict[str, Any],
) -> None:
    """Release 1.6.8: the coverage report of a run made by release 1.6.7 or earlier, whose Food row skipped
    its Dairy & Eggs category page as "a category page or other page, not a product listing" (simulated here
    by writing that 1.6.7 record into the run's checkpoint), does not call the row complete: the page was
    never read for the listings it names. Until 1.6.7 that skip counted as a complete outcome."""
    run_id, status = _run(env)
    assert status == "validated"
    with env["factory"]() as s:
        assert reconcile.reconcile(s, run_id)["csv_rows"][0]["complete"] is True  # as 1.6.8 read it
        task = next(
            t
            for t in s.scalars(select(Task).where(Task.run_id == run_id, Task.kind == "listing_node"))
            if any(x.get("id") == "9176907" for x in (t.cursor or {}).get("listings") or [])
        )
        legacy = "a category page or other page, not a product listing"
        task.cursor = {
            **task.cursor,
            "listings": [
                {**x, "status": "SKIPPED", "note": legacy, "reason": "", "end": "", "children": []}
                if x.get("id") == "9176907"
                else x
                for x in task.cursor["listings"]
            ],
        }
        s.commit()
        report = reconcile.reconcile(s, run_id)
    food = report["csv_rows"][0]
    assert food["csv_row"] == 0 and food["complete"] is False, food
    assert "9176907 INCOMPLETE" in food["why_not_complete"]
    page = next(r for r in report["rows"] if r["listing_id"] == "9176907")
    assert (page["status"], page["effective_status"]) == ("SKIPPED", "INCOMPLETE")
    assert page["effective_reason"].startswith("a subcategory page of its own that this run did not read")
    assert report["coverage_complete"] is False
