"""Release 1.2.0 rules through the run pipeline, against the Scrape.do mock serving SYNTHETIC Walmart pages
(tests/mock_scrapedo.py): a listing is complete only when its distinct products reach the total it reports
(result windows, empty and repeated pages, a partition through its own child categories), and store
assortment, availability and the local price are decided apart. Nothing here reaches Scrape.do or Walmart.

The result-window shape is the one Walmart's own listings served on 2026-10-23 (Diapering and Balloons:
page 11 empty with 0 results reported while page 10 reported 30,538 and 45,038 results and 25 linked pages);
the pages here are SYNTHETIC copies of that shape, with invented products."""

from __future__ import annotations

import asyncio
import dataclasses
import json
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from sqlalchemy import Engine, select

from tests import synthetic_walmart as syn
from tests.conftest import CONFIG, STORE_KEY
from tests.integration.helpers import seed
from tests.mock_scrapedo import DIAPERING, MILK, PRIMARY, MockScrapeDo, listing
from walmart_headless.acquisition import scrapedo as sd
from walmart_headless.collection import reconcile
from walmart_headless.collection.config import CollectionConfig, DetailConfig, Limits
from walmart_headless.collection.nodes import Node
from walmart_headless.collection.walmart import Listing, WalmartCollector
from walmart_headless.core.settings import load_private_label, load_settings, load_stores
from walmart_headless.core.timeutil import iso
from walmart_headless.db.models import (
    CategorySource,
    Event,
    NodeCoverage,
    OfferObservationRow,
    PageFetch,
    ProductObservation,
    RecordRow,
    Run,
    StoreAttestation,
    Task,
)
from walmart_headless.publishing import supporting_log
from walmart_headless.publishing.exports import verify_manifest
from walmart_headless.storage.local import LocalStorageAdapter
from walmart_headless.worker.pipeline import Pipeline

pytestmark = [pytest.mark.postgres]

CRUMBS = ["5427", "5427_486190"]
DIAPERS = "https://www.walmart.com/browse/diapering/diapers/5427_486190_1"
WIPES = "https://www.walmart.com/browse/diapering/wipes/5427_486190_2"
DEPARTMENTS = [
    ("5427_486190_1", "Diapers", "/browse/diapering/diapers/5427_486190_1"),
    ("5427_486190_2", "Wipes", "/browse/diapering/wipes/5427_486190_2"),
    # A grandchild the facet also names: read only if its own parent overflows.
    ("5427_486190_1_9", "Size 5 Diapers", "/browse/diapering/size-5/5427_486190_1_9"),
]


def items(*ids: int, **kw: Any) -> list[syn.Item]:
    return [syn.Item(str(9000 + i), f"Synthetic Product {i}, 12 oz", "$1.99", **kw) for i in ids]


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


def serve(env: dict[str, Any], pages: dict[str, Callable[[int], str]]) -> None:
    """Listing pages by URL (page number -> html), served through the store endpoint."""

    def override(url: str) -> httpx.Response | None:
        u = urlsplit(url)
        base = f"{u.scheme}://{u.netloc}{u.path}"
        if base not in pages:
            return None
        n = int(parse_qs(u.query).get("page", ["1"])[0])
        headers = {"Scrape.do-Request-Cost": "10"}
        if env["mock"].store_header:
            headers["Scrape.do-Walmart-Store-Id"] = env["mock"].store_header
        return httpx.Response(200, text=pages[base](n), headers=headers)

    env["mock"].page_override = override


def run_diapering(
    env: dict[str, Any],
    *,
    settings_update: dict[str, Any] | None = None,
    snapshot: dict[str, Any] | None = None,
) -> tuple[str, str]:
    settings = load_settings(CONFIG / "settings.yaml")
    if settings_update:
        cov = settings.coverage.model_copy(update=settings_update)
        settings = settings.model_copy(update={"coverage": cov})
    pipe = Pipeline(env["engine"], env["storage"], settings, env["store"], env["private_label"])
    cfg = CollectionConfig(limits=Limits(), detail=DetailConfig(enabled=False))
    with env["factory"]() as s:
        cat = s.scalar(select(CategorySource.id).where(CategorySource.category_name == "Diapering"))
        assert cat is not None
        node = Node(4, "Diapering", cat, "", "5427_486190", DIAPERING)
        run_id = pipe.create_live_run(
            s,
            [node],
            trigger="manual",
            snapshot={
                "plan": {"nodes": [node.as_dict()], "skipped": []},
                "started_by": "test",
                "retailer": "walmart",
                "provider": "scrapedo",
                "collection": cfg.model_dump(mode="json"),
                "pilot": False,
                **(snapshot or {}),
            },
        )
        s.commit()
    collector = WalmartCollector(pipe, run_id, config=cfg, trigger="manual")
    status = asyncio.run(pipe.execute(run_id, "test-collector", collector=collector))
    return run_id, status


def cursor(env: dict[str, Any], run_id: str) -> dict[str, Any]:
    with env["factory"]() as s:
        t = s.scalars(select(Task).where(Task.run_id == run_id, Task.kind == "listing_node")).one()
        return dict(t.cursor)


def coverage(env: dict[str, Any], run_id: str) -> dict[str, NodeCoverage]:
    with env["factory"]() as s:
        return {
            c.taxonomy_id: c for c in s.scalars(select(NodeCoverage).where(NodeCoverage.run_id == run_id))
        }


def records(env: dict[str, Any], run_id: str) -> dict[str, RecordRow]:
    with env["factory"]() as s:
        return {r.upc: r for r in s.scalars(select(RecordRow).where(RecordRow.run_id == run_id))}


def window_parent(n: int, *, departments: list[tuple[str, str, str]] | None = DEPARTMENTS) -> str:
    """The parent listing: 10 results reported, 25 pages linked, served only to page 2 (page 3 is empty
    and reports 0 results, as Walmart's listings did at page 11)."""
    served = {1: items(1, 2, 3), 2: items(4, 5, 6)}
    if n in served:
        return listing(
            served[n], page=n, max_page=25, total=10, cat=("Diapering", CRUMBS), departments=departments
        )
    return listing([], page=n, max_page=25, total=0, cat=("Diapering", CRUMBS))


def test_an_empty_page_past_the_result_window_is_never_the_listings_end(env: dict[str, Any]) -> None:
    serve(env, {DIAPERING: lambda n: window_parent(n, departments=None)})
    run_id, _ = run_diapering(env)
    cov = coverage(env, run_id)["5427_486190"]
    assert cov.status == "INCOMPLETE" and cov.partition["end"] == "RESULT_WINDOW"
    reason = cov.partition["reason"]
    assert "reports 10 results" in reason and reason.startswith(
        "accessible pages exhausted; coverage incomplete"
    )
    pages = cov.partition["result_pages"]
    assert [p["reported_total"] for p in pages] == [10, 10, 0] and pages[-1]["products"] == 0
    with env["factory"]() as s:
        run = s.get(Run, run_id)
        assert run is not None and run.counts["collection_complete"] is False
        assert run.counts["gates"]["G3"] == "FAIL"  # incomplete coverage can never be published


def test_a_listing_larger_than_its_window_is_read_through_its_own_child_categories(
    env: dict[str, Any],
) -> None:
    serve(
        env,
        {
            DIAPERING: window_parent,
            # The children overlap the parent (9001) and each other's totals are never added up.
            DIAPERS: lambda n: listing(
                items(1, 7, 8), page=n, max_page=1, total=3, cat=("Diapers", [*CRUMBS, "5427_486190_1"])
            ),
            WIPES: lambda n: listing(
                items(9, 10), page=n, max_page=1, total=2, cat=("Wipes", [*CRUMBS, "5427_486190_2"])
            ),
        },
    )
    run_id, _ = run_diapering(env)
    cov = coverage(env, run_id)
    assert cov["5427_486190"].status == "PARTITIONED"
    assert cov["5427_486190_1"].partition["parent"] == "5427_486190"
    assert cov["5427_486190_1"].partition["via"] == "departments_facet"
    assert "5427_486190_1_9" not in cov  # a grandchild is read only when its own parent overflows
    cur = cursor(env, run_id)
    assert cur["status"] == "DONE"  # the parent and its children: 10 distinct products of 10 reported
    calls = [u for _, path, u in env["mock"].calls if path == "/plugin/walmart/store"]
    assert any(u.startswith(DIAPERS) for u in calls) and any(u.startswith(WIPES) for u in calls)


def moving_window_parent(n: int) -> str:
    """The parent listing of ``window_parent`` with a total that moved while it was read (12 on page 1, 10 on
    page 2): 6 served, then page 3 of the 25 linked empty, as live Laundry on 2026-11-03 (615, 613, 614, 611
    reported; 393 served; page 11 of 16 empty)."""
    served = {1: items(1, 2, 3), 2: items(4, 5, 6)}
    if n in served:
        return listing(
            served[n], page=n, max_page=25, total=12 if n == 1 else 10, cat=("Diapering", CRUMBS),
            departments=DEPARTMENTS,
        )  # fmt: skip
    return listing([], page=n, max_page=25, total=0, cat=("Diapering", CRUMBS))


def test_a_moving_total_does_not_hide_a_window_end_and_the_listing_is_read_through_its_children(
    env: dict[str, Any],
) -> None:
    # Release 1.6.2. Until 1.6.1 the moved total ended the listing "not reconciled" and unpartitioned.
    serve(
        env,
        {
            DIAPERING: moving_window_parent,
            DIAPERS: lambda n: listing(
                items(1, 7, 8), page=n, max_page=1, total=3, cat=("Diapers", [*CRUMBS, "5427_486190_1"])
            ),
            WIPES: lambda n: listing(
                items(9, 10), page=n, max_page=1, total=2, cat=("Wipes", [*CRUMBS, "5427_486190_2"])
            ),
        },
    )
    run_id, _ = run_diapering(env)
    cov = coverage(env, run_id)
    parent = cov["5427_486190"]
    assert parent.status == "PARTITIONED" and parent.partition["end"] == "RESULT_WINDOW"
    assert parent.partition["reason"].startswith("accessible pages exhausted; coverage incomplete")
    assert "between 10 and 12 results" in parent.partition["reason"]
    assert cov["5427_486190_1"].partition["parent"] == "5427_486190"
    calls = [u for _, path, u in env["mock"].calls if path == "/plugin/walmart/store"]
    assert any(u.startswith(DIAPERS) for u in calls) and any(u.startswith(WIPES) for u in calls)
    # Its own total moved, so the partition can never reconcile it: the row stays incomplete, never published.
    assert cursor(env, run_id)["status"] != "DONE"
    with env["factory"]() as s:
        run = s.get(Run, run_id)
        assert run is not None and run.counts["collection_complete"] is False
        assert run.counts["gates"]["G3"] == "FAIL"


SIZE_5 = "https://www.walmart.com/browse/diapering/size-5/5427_486190_1_9"
SIZE_4 = "https://www.walmart.com/browse/diapering/size-4/5427_486190_1_8"
OVERNIGHT = "https://www.walmart.com/browse/diapering/size-5-overnight/5427_486190_1_9_1"
DIAPERS_CRUMBS = [*CRUMBS, "5427_486190_1"]
SIZE_5_CRUMBS = [*DIAPERS_CRUMBS, "5427_486190_1_9"]


def windowed(
    served: dict[int, list[syn.Item]],
    *,
    total: int,
    cat: tuple[str, list[str]],
    departments: list[tuple[str, str, str]] | None = None,
) -> Callable[[int], str]:
    """A listing larger than its result window: the pages in ``served``, then an empty page reporting 0."""

    def page(n: int) -> str:
        if n in served:
            return listing(served[n], page=n, max_page=25, total=total, cat=cat, departments=departments)
        return listing([], page=n, max_page=25, total=0, cat=cat)

    return page


def deep_branch() -> dict[str, Callable[[int], str]]:
    """Diapering (10 reported) > Diapers (4, one page served) > Size 5 (2, one page served) > Size 5
    Overnight (1): the result window ends at every level above the last, so the branch balances only three
    levels down (release 1.3.1 stopped at depth 2 by default)."""
    return {
        DIAPERING: window_parent,
        DIAPERS: windowed(
            {1: items(1, 7)},
            total=4,
            cat=("Diapers", DIAPERS_CRUMBS),
            departments=[
                ("5427_486190_1_9", "Size 5 Diapers", "/browse/diapering/size-5/5427_486190_1_9"),
                ("5427_486190_1_8", "Size 4 Diapers", "/browse/diapering/size-4/5427_486190_1_8"),
            ],
        ),
        SIZE_5: windowed(
            {1: items(8)},
            total=2,
            cat=("Size 5 Diapers", SIZE_5_CRUMBS),
            departments=[
                (
                    "5427_486190_1_9_1",
                    "Size 5 Overnight Diapers",
                    "/browse/diapering/size-5-overnight/5427_486190_1_9_1",
                )
            ],
        ),
        OVERNIGHT: lambda n: listing(
            items(9),
            page=n,
            max_page=1,
            total=1,
            cat=("Size 5 Overnight Diapers", [*SIZE_5_CRUMBS, "5427_486190_1_9_1"]),
        ),
        SIZE_4: lambda n: listing(
            items(7),
            page=n,
            max_page=1,
            total=1,
            cat=("Size 4 Diapers", [*DIAPERS_CRUMBS, "5427_486190_1_8"]),
        ),
        WIPES: lambda n: listing(
            items(10), page=n, max_page=1, total=1, cat=("Wipes", [*CRUMBS, "5427_486190_2"])
        ),
    }


def test_partitioning_goes_as_deep_as_the_child_categories_overflow(env: dict[str, Any]) -> None:
    serve(env, deep_branch())
    run_id, _ = run_diapering(env)
    cov = coverage(env, run_id)
    assert cov["5427_486190"].status == "PARTITIONED"
    assert cov["5427_486190_1"].status == "PARTITIONED"
    assert cov["5427_486190_1_9"].status == "PARTITIONED"
    assert cov["5427_486190_1_9"].partition["parent"] == "5427_486190_1"
    assert cov["5427_486190_1_9_1"].partition["parent"] == "5427_486190_1_9"
    assert cov["5427_486190_1_9_1"].status == "DONE"
    assert cursor(env, run_id)["status"] == "DONE"  # 10 distinct identities of 10 reported, three levels down


def test_a_partition_depth_cap_leaves_the_deeper_branch_incomplete_and_says_so(env: dict[str, Any]) -> None:
    serve(env, deep_branch())
    run_id, _ = run_diapering(env, settings_update={"partition_max_depth": 1})
    cov = coverage(env, run_id)
    assert "5427_486190_1_9" not in cov  # never read: its parent is at the cap
    assert (
        "not partitioned: the run's partition depth cap is reached (coverage.partition_max_depth = 1, this "
        "listing is at depth 1)"
    ) in cov["5427_486190_1"].partition["reason"]
    assert cursor(env, run_id)["status"] == "INCOMPLETE"


def test_a_partitioned_listings_row_is_written_when_the_run_stops_in_its_children(
    env: dict[str, Any],
) -> None:
    """The run's credit limit stops it before the first child category: the parent's coverage row already
    says PARTITIONED with its result-window end (it was IN_PROGRESS in 1.2.0 until the row finished)."""
    serve(env, {DIAPERING: window_parent})
    settings = load_settings(CONFIG / "settings.yaml")
    pipe = Pipeline(env["engine"], env["storage"], settings, env["store"], env["private_label"])
    cfg = CollectionConfig(limits=Limits(max_credits_per_run=40), detail=DetailConfig(enabled=False))
    with env["factory"]() as s:
        cat = s.scalar(select(CategorySource.id).where(CategorySource.category_name == "Diapering"))
        assert cat is not None
        node = Node(4, "Diapering", cat, "", "5427_486190", DIAPERING)
        run_id = pipe.create_live_run(
            s,
            [node],
            trigger="manual",
            snapshot={
                "plan": {"nodes": [node.as_dict()], "skipped": []},
                "started_by": "test",
                "retailer": "walmart",
                "provider": "scrapedo",
                "collection": cfg.model_dump(mode="json"),
                "pilot": True,
            },
        )
        s.commit()
    collector = WalmartCollector(pipe, run_id, config=cfg, trigger="manual")
    asyncio.run(pipe.execute(run_id, "test-collector", collector=collector))
    with env["factory"]() as s:
        run = s.get(Run, run_id)
        assert run is not None and run.stop_code == "RUN_CREDIT_LIMIT"
    row = coverage(env, run_id)["5427_486190"]
    assert row.status == "PARTITIONED" and row.partition["end"] == "RESULT_WINDOW"


def test_a_partition_that_does_not_cover_the_parents_total_stays_incomplete(env: dict[str, Any]) -> None:
    serve(
        env,
        {
            DIAPERING: window_parent,
            DIAPERS: lambda n: listing(
                items(1, 7), page=n, max_page=1, total=2, cat=("Diapers", [*CRUMBS, "5427_486190_1"])
            ),
            WIPES: lambda n: listing(
                items(9), page=n, max_page=1, total=1, cat=("Wipes", [*CRUMBS, "5427_486190_2"])
            ),
        },
    )
    run_id, _ = run_diapering(env)
    cur = cursor(env, run_id)
    assert cur["status"] == "INCOMPLETE"
    # Release 1.3.1 states the balance it checked: identities placed (organic, sponsored-only) against the
    # total, with the signed difference.
    assert (
        "partition does not reconcile with the listing: 8 organic and 0 sponsored-only identities through "
        "the listing and 2 child categories, 10 reported (difference 2)"
    ) in cur["reason"]


def three_a_page(n: int, *, total: int) -> str:
    """Two linked result pages of three products each."""
    return listing(
        items(3 * n, 3 * n + 1, 3 * n + 2), page=n, max_page=2, total=total, cat=("Diapering", CRUMBS)
    )


def test_reaching_the_last_linked_page_short_of_the_total_is_a_result_window(env: dict[str, Any]) -> None:
    serve(env, {DIAPERING: lambda n: three_a_page(n, total=40)})
    run_id, _ = run_diapering(env, settings_update={"partition_large_listings": False})
    cov = coverage(env, run_id)["5427_486190"]
    assert cov.status == "INCOMPLETE" and cov.partition["end"] == "RESULT_WINDOW"
    assert cov.organic_upcs == 6 and cov.total_count == 40


def test_a_complete_listing_ends_done_with_its_count_reconciled(env: dict[str, Any]) -> None:
    serve(env, {DIAPERING: lambda n: three_a_page(n, total=6)})
    run_id, _ = run_diapering(env)
    cov = coverage(env, run_id)["5427_486190"]
    assert cov.status == "DONE" and cov.partition["end"] == "LAST_PAGE" and cov.coverage_ratio == 1.0


def test_a_repeated_page_is_not_the_end_of_the_listing(env: dict[str, Any]) -> None:
    serve(
        env,
        {
            DIAPERING: lambda n: listing(
                items(1, 2, 3), page=n, max_page=5, total=15, cat=("Diapering", CRUMBS)
            )
        },
    )
    run_id, _ = run_diapering(env, settings_update={"partition_large_listings": False})
    cov = coverage(env, run_id)["5427_486190"]
    assert cov.status == "INCOMPLETE" and cov.partition["end"] == "REPEATED_PAGE"


def test_an_empty_page_for_another_store_stops_the_run_instead_of_ending_the_listing(
    env: dict[str, Any],
) -> None:
    def pages(n: int) -> str:
        if n == 1:
            return listing(items(1, 2), page=1, max_page=3, total=4, cat=("Diapering", CRUMBS))
        return listing([], page=n, max_page=3, total=0, store="9999", cat=("Diapering", CRUMBS))

    serve(env, {DIAPERING: pages})
    run_id, _ = run_diapering(env)
    with env["factory"]() as s:
        run = s.get(Run, run_id)
        assert run is not None and run.stop_code == "STORE_NOT_VERIFIED"


def test_out_of_stock_without_a_store_line_is_unresolved_until_verified_earlier(env: dict[str, Any]) -> None:
    complete = 1  # one product, one page: a complete listing each time

    def first(n: int) -> str:
        return listing(items(1), page=n, max_page=complete, total=1, cat=("Diapering", CRUMBS))

    serve(env, {DIAPERING: first})
    first_run, _ = run_diapering(env)
    assert records(env, first_run)["wm:9001"].status == "valid"

    def second(n: int) -> str:
        return listing(
            [
                *items(1, lines=(), availability="OUT_OF_STOCK"),
                *items(2, lines=(), availability="OUT_OF_STOCK"),
            ],
            page=n,
            max_page=1,
            total=2,
            cat=("Diapering", CRUMBS),
        )

    serve(env, {DIAPERING: second})
    later, _ = run_diapering(env)
    recs = records(env, later)
    # Verified at the store by the first run: kept with its identity and size, its prices empty now.
    known = recs["wm:9001"]
    assert known.status == "exported_not_valid" and "NO_LOCAL_OFFER" in known.flags
    assert known.record["regular_price"] == "" and known.record["weight"] == "12 oz"
    # Never seen with a store line: not claimed as the store's.
    assert recs["wm:9002"].status == "excluded" and "ASSORTMENT_UNRESOLVED" in recs["wm:9002"].reasons
    with env["factory"]() as s:
        obs = s.scalars(
            select(ProductObservation).where(
                ProductObservation.run_id == later, ProductObservation.upc == "wm:9001"
            )
        ).one()
        decided = obs.provenance["assortment"]
    assert decided["status"] == "verified_earlier" and decided["verified"]["regular_price"] == "1.99"
    assert decided["verified"]["run_id"] == first_run  # the available -> unavailable transition's evidence


def children(diapers: list[syn.Item]) -> dict[str, Callable[[int], str]]:
    """The parent listing past its result window (:func:`window_parent`) and its two child categories."""
    return {
        DIAPERS: lambda n: listing(
            diapers, page=n, max_page=1, total=3, cat=("Diapers", [*CRUMBS, "5427_486190_1"])
        ),
        WIPES: lambda n: listing(
            items(9, 10), page=n, max_page=1, total=2, cat=("Wipes", [*CRUMBS, "5427_486190_2"])
        ),
    }


def card(env: dict[str, Any], run_id: str, key: str) -> ProductObservation:
    """The observation a run's record of ``key`` is kept from (one per record)."""
    with env["factory"]() as s:
        return s.scalars(
            select(ProductObservation).where(
                ProductObservation.run_id == run_id,
                ProductObservation.upc == key,
                ProductObservation.source == "card",
            )
        ).one()


def page_urls(env: dict[str, Any], run_id: str) -> dict[str, str]:
    with env["factory"]() as s:
        return {pf.id: pf.url for pf in s.scalars(select(PageFetch).where(PageFetch.run_id == run_id))}


def test_a_later_tile_of_the_same_run_decides_the_record_and_the_earlier_state_is_kept(
    env: dict[str, Any],
) -> None:
    """Release 1.3.1. Found with Fresh Strawberries 8.8 oz (item 1175460573) in the main run of 2026-10-26: in
    stock with store 3891's Pickup line at 21:52Z on Fresh Fruits, out of stock without the line at 22:29Z on
    Strawberries. Release 1.3.0 kept the first tile and counted the later one as a duplicate, so the run
    exported a Pickup price its own later page no longer showed. The record now holds the product's latest
    state in the run. The earlier tile verifies the product at the store, and its state stays in the log with
    its page and time; it also verifies the product for a later run."""
    serve(
        env,
        {
            DIAPERING: window_parent,
            **children([*items(1, lines=(), availability="OUT_OF_STOCK"), *items(2, 7)]),
        },
    )
    run_id, _ = run_diapering(env)
    recs = records(env, run_id)
    rec = recs["wm:9001"]
    assert rec.status == "exported_not_valid" and "NO_LOCAL_OFFER" in rec.flags and rec.reasons == []
    assert rec.record["regular_price"] == rec.record["ppm"] == "" and rec.record["weight"] == "12 oz"
    # Its category stays the one of the listing it was first recorded from.
    assert rec.record["sub_category"] == recs["wm:9003"].record["sub_category"]
    urls = page_urls(env, run_id)
    obs = card(env, run_id, "wm:9001")
    assert urls[obs.page_fetch_id].startswith(DIAPERS)
    [before] = obs.provenance["earlier_in_run"]
    assert urls[before["page_fetch_id"]].startswith(DIAPERING) and before["observed_at"] < iso(
        obs.observed_at
    )
    assert before["status"] == "valid" and before["record"]["regular_price"] == "1.99"
    decided = obs.provenance["assortment"]
    assert decided["status"] == "verified_earlier" and decided["verified"]["run_id"] == run_id
    assert decided["verified"]["page_fetch_id"] == before["page_fetch_id"]
    assert decided["verified"]["regular_price"] == "1.99"
    assert obs.provenance["missing_kind"]["regular_price"] == "context_failed"
    # The same state on another listing changes nothing: the record keeps its first tile.
    same = card(env, run_id, "wm:9002")
    assert urls[same.page_fetch_id].startswith(DIAPERING) and "earlier_in_run" not in same.provenance
    assert recs["wm:9002"].status == "valid"
    # The exports' record map shows the earlier state with its page, time and prices.
    with env["factory"]() as s:
        rows = {r["key"]: r for r in supporting_log.record_map(s, run_id)["rows"]}
        logged = supporting_log.supporting_log(s, run_id)["records"]
    [shown] = rows["wm:9001"]["earlier_in_run"]
    assert shown["regular_price"] == "1.99" and shown["page_fetch_id"] == before["page_fetch_id"]
    assert shown["observed_at"] == before["observed_at"] and shown["availability"] == "IN_STOCK"
    assert logged["wm:9001"]["earlier_in_run"] == rows["wm:9001"]["earlier_in_run"]
    assert "earlier_in_run" not in rows["wm:9002"]
    # A later run that shows the product out of stock again is verified by this run's earlier tile.
    serve(
        env,
        {
            DIAPERING: lambda n: listing(
                items(1, lines=(), availability="OUT_OF_STOCK"),
                page=n,
                max_page=1,
                total=1,
                cat=("Diapering", CRUMBS),
            )
        },
    )
    later, _ = run_diapering(env)
    kept = records(env, later)["wm:9001"]
    assert kept.status == "exported_not_valid" and "NO_LOCAL_OFFER" in kept.flags
    verified = card(env, later, "wm:9001").provenance["assortment"]["verified"]
    assert verified["run_id"] == run_id and verified["page_fetch_id"] == before["page_fetch_id"]
    assert verified["regular_price"] == "1.99"


def test_a_tile_observed_before_the_records_own_is_kept_and_verifies_it_as_if_read_in_order(
    env: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two workers' requests can overlap, so a tile observed earlier may be processed after a later one.
    Here this is simulated by dating the child listing's page one minute before the parent's first page. The
    record still holds the latest observed state (the parent's tile: out of stock, no line for the store).
    The earlier tile shows the store's Pickup line, so it verifies the product: the record is the one the
    tiles give when read in order. Before it is processed, the record's assortment is unresolved."""

    def parent(n: int) -> str:
        if n == 1:
            return listing(
                [*items(1, lines=(), availability="OUT_OF_STOCK"), *items(2, 3)],
                page=n,
                max_page=25,
                total=10,
                cat=("Diapering", CRUMBS),
                departments=DEPARTMENTS,
            )
        return window_parent(n)

    serve(env, {DIAPERING: parent, **children(items(1, 7, 8))})
    original = WalmartCollector.record_page
    first: dict[str, str] = {}

    def dated(
        self: WalmartCollector,
        s: Any,
        node: Node,
        lst: Listing,
        fetch: Any,
        tiles: list[Any],
        page: int,
    ) -> Any:
        if lst.url.startswith(DIAPERING) and page == 1:
            first["at"] = fetch.started_at
        if lst.url.startswith(DIAPERS):
            at = datetime.fromisoformat(first["at"].replace("Z", "+00:00")) - timedelta(minutes=1)
            fetch = dataclasses.replace(fetch, started_at=iso(at))
        return original(self, s, node, lst, fetch, tiles, page)

    monkeypatch.setattr(WalmartCollector, "record_page", dated)
    run_id, _ = run_diapering(env)
    rec = records(env, run_id)["wm:9001"]
    assert rec.status == "exported_not_valid" and "NO_LOCAL_OFFER" in rec.flags and rec.reasons == []
    assert rec.record["regular_price"] == rec.record["ppm"] == ""
    urls = page_urls(env, run_id)
    obs = card(env, run_id, "wm:9001")
    assert urls[obs.page_fetch_id].startswith(DIAPERING)  # the latest tile stays the record's
    [before] = obs.provenance["earlier_in_run"]
    assert urls[before["page_fetch_id"]].startswith(DIAPERS) and before["observed_at"] < iso(obs.observed_at)
    assert before["status"] == "valid" and before["record"]["regular_price"] == "1.99"
    decided = obs.provenance["assortment"]
    assert decided["status"] == "verified_earlier" and decided["basis"] == "local_offer_observed_earlier"
    assert decided["verified"]["run_id"] == run_id
    assert decided["verified"]["page_fetch_id"] == before["page_fetch_id"]
    assert obs.provenance["missing"]["regular_price"].startswith("no local offer at store")
    assert obs.provenance["missing_kind"]["regular_price"] == "context_failed"
    assert "regular_price" not in obs.provenance["field_observed_at"]
    assert "NO_LOCAL_OFFER" in obs.flags


def test_a_later_tile_with_another_price_gives_the_record_its_latest_price(env: dict[str, Any]) -> None:
    """The latest observed price of the run is the record's; the earlier price stays in the log."""
    later_price = syn.Item("9001", "Synthetic Product 1, 12 oz", "$2.49")
    serve(env, {DIAPERING: window_parent, **children([later_price, *items(7, 8)])})
    run_id, _ = run_diapering(env)
    rec = records(env, run_id)["wm:9001"]
    assert rec.status == "valid" and rec.record["regular_price"] == "2.49"
    obs = card(env, run_id, "wm:9001")
    assert page_urls(env, run_id)[obs.page_fetch_id].startswith(DIAPERS)
    [before] = obs.provenance["earlier_in_run"]
    assert before["record"]["regular_price"] == "1.99" and before["status"] == "valid"
    assert obs.provenance["assortment"]["basis"] == "pickup_line"


def test_the_offers_exported_are_those_of_the_tile_the_record_is_kept_from(env: dict[str, Any]) -> None:
    """Release 1.3.1 (a6dd836) decided a record again from a later tile of the run and added that tile's
    offers, but the earlier tile's offers stayed in offers.json beside them: an offer the record no longer
    had (or the same offer twice), with nothing to tell the two tiles apart. offers.json now holds the offers
    of the page each record is kept from, each with that page; the earlier tile's stay in the database."""
    first = syn.Item("9001", "Synthetic Product 1, 12 oz", "$1.99", badges=(("MULTI", "2 for $3.00"),))
    later = syn.Item("9001", "Synthetic Product 1, 12 oz", "$2.49", badges=(("MULTI", "3 for $6.00"),))

    def parent(n: int) -> str:
        if n == 1:
            return listing(
                [first, *items(2, 3)],
                page=n,
                max_page=25,
                total=10,
                cat=("Diapering", CRUMBS),
                departments=DEPARTMENTS,
            )
        return window_parent(n)

    serve(env, {DIAPERING: parent, **children([later, *items(7, 8)])})
    run_id, _ = run_diapering(env)
    rec = records(env, run_id)["wm:9001"]
    assert rec.record["regular_price"] == "2.49"
    # Release 1.6.0: the deal fields are always "" for Walmart; the later tile's offer is the one kept as
    # evidence (what the 1.5.x rules would have exported), the earlier tile's is not.
    assert rec.record["volume_deals_description"] == "" and rec.record["volume_deals_price"] == ""
    obs = card(env, run_id, "wm:9001")
    derived = obs.provenance["fields"]["_deal_fields_not_exported"]["derived"]
    assert "3 for $6.00" in derived["volume_deals_description"]
    assert "2 for $3.00" not in derived["volume_deals_description"]
    offers = json.loads(env["storage"].get_bytes(f"runs/{STORE_KEY}/{run_id}/exports/offers.json"))
    mine = [o for o in offers if o["upc"] == "wm:9001"]
    assert [o["text"] for o in mine] == ["3 for $6.00"]
    assert [o["page_fetch_id"] for o in mine] == [obs.page_fetch_id]
    with env["factory"]() as s:
        kept = s.scalars(
            select(OfferObservationRow).where(
                OfferObservationRow.run_id == run_id, OfferObservationRow.upc == "wm:9001"
            )
        ).all()
    assert {(o.description, o.page_fetch_id == obs.page_fetch_id) for o in kept} == {
        ("2 for $3.00", False),
        ("3 for $6.00", True),
    }


def test_memberships_and_offers_are_exported_in_a_total_order(env: dict[str, Any]) -> None:
    """Two offline reprocessings of the same stored pages (2026-10-27, attempts 4 and 5) exported the same 845
    memberships in another order. The export ordered them by category and listing only; within a listing the
    order was whatever the database returned (here: by product key, from an index), and its sort is not
    stable. The offers had no order at all. Memberships are now in page order (category, listing, result
    page, position, product, placement) and offers by product, page and content, so the same rows always
    give the same bytes."""
    tiles = [
        syn.Item("9008", "Synthetic Product 8, 12 oz", "$1.99", badges=(("MULTI", "3 for $6.00"),)),
        syn.Item(
            "9007",
            "Synthetic Product 7, 12 oz",
            "$1.99",
            badges=(("MULTI", "3 for $5.00"), ("MULTI2", "2 for $3.00")),
        ),
    ]
    serve(env, {DIAPERING: window_parent, **children(tiles)})
    run_id, _ = run_diapering(env)
    prefix = f"runs/{STORE_KEY}/{run_id}/exports"
    members = json.loads(env["storage"].get_bytes(f"{prefix}/memberships.json"))
    order = [
        (m["category_source_id"], m["listing"], m["page"], m["position"], m["key"], m["via"]) for m in members
    ]
    assert len(order) > 5 and order == sorted(order)
    child = [m["key"] for m in members if m["listing"] == "5427_486190_1"]
    assert child == ["wm:9008", "wm:9007"]  # the page's order, not the product keys'
    offers = json.loads(env["storage"].get_bytes(f"{prefix}/offers.json"))
    assert [(o["upc"], o["text"]) for o in offers] == [
        ("wm:9007", "2 for $3.00"),
        ("wm:9007", "3 for $5.00"),
        ("wm:9008", "3 for $6.00"),
    ]


def test_the_reports_count_by_reason_in_a_fixed_order(env: dict[str, Any]) -> None:
    """The coverage report's counts by reason (other_exclusions, follow_up_outcomes) and the validation
    report's excluded_by_reason were written in the order the database returned the records, which it does
    not fix: two reprocessings of the same stored pages (2026-10-27, attempts 5 and 6) wrote one listing's
    exclusions in another order. They are now sorted by reason."""
    # A product sold by weight is no longer excluded for that alone (release 1.4.0): a shipping-only offer.
    ship = syn.Item("9001", "Synthetic Product 1, 12 oz", "$1.99", lines=(("SHIPPING", "0"),))
    market = syn.Item(
        "9002", "Synthetic Product 2, 12 oz", "$1.99", seller="Other Seller LLC", lines=(("SHIPPING", "0"),)
    )
    tiles = [ship, market, *items(3)]
    serve(
        env,
        {DIAPERING: lambda n: listing(tiles, page=n, max_page=1, total=3, cat=("Diapering", CRUMBS))},
    )
    run_id, _ = run_diapering(env)
    with env["factory"]() as s:
        data = reconcile.reconcile(s, run_id)
    [row] = [r for r in data["rows"] if r["listing_id"] == "5427_486190"]
    by_listing = row["other_exclusions"]
    assert "SHIP_ONLY" in by_listing and "MARKETPLACE_OFFER" in by_listing
    assert list(by_listing) == sorted(by_listing)
    report = json.loads(env["storage"].get_bytes(f"runs/{STORE_KEY}/{run_id}/exports/validation_report.json"))
    by_reason = report["excluded_by_reason"]
    assert "SHIP_ONLY" in by_reason and "MARKETPLACE_OFFER" in by_reason
    assert list(by_reason) == sorted(by_reason)


def test_a_delivery_line_alone_never_gives_the_pickup_price(env: dict[str, Any]) -> None:
    serve(
        env,
        {
            DIAPERING: lambda n: listing(
                items(1, lines=(("DELIVERY", "{store}"),)),
                page=n,
                max_page=1,
                total=1,
                cat=("Diapering", CRUMBS),
            )
        },
    )
    run_id, _ = run_diapering(env)
    rec = records(env, run_id)["wm:9001"]
    assert rec.status == "exported_not_valid" and "NO_PICKUP_OFFER" in rec.flags
    assert rec.record["regular_price"] == rec.record["sale_price"] == ""


def test_earlier_observations_count_only_under_the_current_rules(env: dict[str, Any]) -> None:
    """An observation an earlier release accepted on "out of stock" alone, or whose title states an
    approximate weight, is not carried forward as a verified store product."""
    serve(
        env,
        {DIAPERING: lambda n: listing(items(1, 2), page=n, max_page=1, total=2, cat=("Diapering", CRUMBS))},
    )
    first, _ = run_diapering(env)
    with env["factory"]() as s:
        # What release 1.1.0 stored for two of its products (an out-of-stock acceptance without a store line,
        # an approximate weight left in the title): valid records the current rules no longer accept.
        obs = s.scalars(
            select(ProductObservation).where(
                ProductObservation.run_id == first, ProductObservation.upc == "wm:9001"
            )
        ).one()
        obs.structured = {"walmart": {**obs.structured["walmart"], "fulfillment_lines": []}}
        rec = s.scalars(select(RecordRow).where(RecordRow.run_id == first, RecordRow.upc == "wm:9002")).one()
        rec.record = {**rec.record, "product_title": "Grapes, Bag (2.25 lbs/Bag Est.)"}
        s.commit()
    serve(
        env, {DIAPERING: lambda n: listing(items(3), page=n, max_page=1, total=1, cat=("Diapering", CRUMBS))}
    )
    later, _ = run_diapering(env)
    recs = records(env, later)
    assert "wm:9001" not in recs and "wm:9002" not in recs
    with env["factory"]() as s:
        run = s.get(Run, later)
        assert run is not None and run.counts["historical"]["not_verified_by_current_rules"] == 2


def test_exports_hold_the_fresh_products_and_a_record_map_listed_in_the_manifest(env: dict[str, Any]) -> None:
    serve(
        env,
        {DIAPERING: lambda n: listing(items(1, 2), page=n, max_page=1, total=2, cat=("Diapering", CRUMBS))},
    )
    first, _ = run_diapering(env)
    serve(
        env, {DIAPERING: lambda n: listing(items(1), page=n, max_page=1, total=1, cat=("Diapering", CRUMBS))}
    )
    later, _ = run_diapering(env)
    storage: LocalStorageAdapter = env["storage"]
    prefix = f"runs/{STORE_KEY}/{later}/exports"
    manifest = json.loads(storage.get_bytes(f"{prefix}/manifest.json"))
    assert {"products_fresh.json", "products_fresh.csv", "record_map.json"} <= set(manifest["files"])
    assert not verify_manifest(storage, f"{prefix}/manifest.json")
    fresh = json.loads(storage.get_bytes(f"{prefix}/products_fresh.json"))
    retained = json.loads(storage.get_bytes(f"{prefix}/products.json"))
    assert len(fresh) == 1 and len(retained) == 2 and manifest["fresh_record_count"] == 1
    rows = {r["key"]: r for r in json.loads(storage.get_bytes(f"{prefix}/record_map.json"))["rows"]}
    carried, observed = rows["wm:9002"], rows["wm:9001"]
    assert carried["observation_kind"] == "carried_forward" and carried["observed_by_run"] == first
    assert observed["observed_by_run"] == later and observed["page"]["stored_page_sha256"]
    assert observed["page"]["store_check"]["result"] == "PASS" and observed["fields"]["product_title"]
    assert observed["field_observed_at"]["product_title"] == observed["observed_at"]
    assert observed["code"]["version"]


def run_food(env: dict[str, Any]) -> tuple[str, str]:
    """The Food row: its category page (/cp/) names the Milk and Snacks listings (mock pages)."""
    settings = load_settings(CONFIG / "settings.yaml")
    pipe = Pipeline(env["engine"], env["storage"], settings, env["store"], env["private_label"])
    cfg = CollectionConfig(limits=Limits(), detail=DetailConfig(enabled=False))
    with env["factory"]() as s:
        cat = s.scalar(select(CategorySource.id).where(CategorySource.category_name == "Food"))
        assert cat is not None
        node = Node(
            0, "Food", cat, "", "976759", "https://www.walmart.com/cp/food/976759", kind="landing",
            excluded=("Shop All Foods", "Recipes"),
        )  # fmt: skip
        run_id = pipe.create_live_run(
            s,
            [node],
            trigger="manual",
            snapshot={
                "plan": {"nodes": [node.as_dict()], "skipped": []},
                "started_by": "test",
                "retailer": "walmart",
                "provider": "scrapedo",
                "collection": cfg.model_dump(mode="json"),
                "pilot": False,
            },
        )
        s.commit()
    collector = WalmartCollector(pipe, run_id, config=cfg, trigger="manual")
    return run_id, asyncio.run(pipe.execute(run_id, "test-collector", collector=collector))


def test_the_category_page_is_read_through_the_general_api_never_the_store_plugin(
    env: dict[str, Any],
) -> None:
    """On 2026-10-23 the store plugin answered every /cp/ page with its own 502 ("Walmart-store plugin
    failure."); a category page is read only for its navigation, so it goes through the general API.
    Release 1.6.8: so does a subcategory page of its own that the row's navigation links (the Dairy & Eggs
    page the SYNTHETIC Food page links), read for the listings it names."""
    run_id, _ = run_food(env)
    cp = [(path, u) for _, path, u in env["mock"].calls if "/cp/" in u]
    assert cp == [
        ("/", "https://www.walmart.com/cp/food/976759"),
        ("/", "https://www.walmart.com/cp/dairy-eggs/9176907"),
    ]
    listings = [u for _, path, u in env["mock"].calls if path == "/plugin/walmart/store"]
    assert listings and all("/browse/" in u for u in listings)  # the listings stay store-scoped
    assert any(r.status == "valid" for r in records(env, run_id).values())


HUB = "/cp/dairy-shop/9176900"


def no_grid(route: str, *, links: bool = True) -> str:
    """A page without a result grid: with ``route`` "/cp/[...categoryParams]", what the listing link
    "Fresh Flowers" served on 2026-11-03 (the category page "Flower Shop": modules linking other listings;
    a SYNTHETIC copy with invented names); with another route, a page of an unknown shape."""
    modules = [
        {
            "configs": {
                "categories": [
                    {
                        "image": {
                            "alt": "Whole Milk",
                            "clickThrough": {"value": "/browse/food/whole/976759_9176907_1"},
                        }
                    },
                    {
                        "image": {
                            "alt": "Oat Milk",
                            "clickThrough": {"value": "/browse/food/oat/976759_9176907_2"},
                        }
                    },
                ]
            }
        }
    ]
    data = {
        "page": route,
        "props": {
            "pageProps": {
                "pageUrl": f"{HUB}?povid=synthetic",
                "initialData": {},
                "initialTempoData": {"contentLayout": {"modules": modules if links else []}},
            }
        },
    }
    return f"<!doctype html><html><body>{syn.next_data_script(data)}</body></html>"


def test_a_listing_link_that_serves_a_category_page_is_recorded_unread_and_the_run_goes_on(
    env: dict[str, Any],
) -> None:
    # Release 1.6.2. Release 1.6.1 stopped the run (ABNORMAL_RESULT, not resumable) and the store was held.
    serve(env, {MILK: lambda n: no_grid("/cp/[...categoryParams]")})
    run_id, _ = run_food(env)
    cov = coverage(env, run_id)
    milk = cov["976759_9176907"]
    assert milk.status == "INCOMPLETE" and milk.partition["end"] == "CATEGORY_PAGE"
    assert milk.partition["reason"] == (
        f"not read: the site served the category page {HUB} for this listing link (links to other listings, "
        "no result grid); that page links 2 listings: Whole Milk; Oat Milk"
    )
    assert milk.total_count is None and milk.organic_upcs == 0  # never an empty listing, no product from it
    # The row's other listing is still read: the run went on past the category page.
    assert cov["976759_976787"].status == "DONE"
    assert any(r.status == "valid" for r in records(env, run_id).values())
    with env["factory"]() as s:
        run = s.get(Run, run_id)
        assert run is not None and run.stop_code is None
        assert run.counts["collection_complete"] is False and run.counts["gates"]["G3"] == "FAIL"


def test_a_listing_link_the_site_answers_with_its_not_found_page_is_recorded_unread_and_the_run_goes_on(
    env: dict[str, Any],
) -> None:
    """Release 1.6.3. Release 1.6.2 did not recognize the page data of Walmart's minified not-found page
    (its id unquoted), called the page a challenge, stopped the run (SITE_REFUSAL) and held the store: live L6
    of 2026-11-04, the Shampoo child listing "nexxus-shampoo"."""
    serve(env, {MILK: lambda n: syn.not_found_page()})
    run_id, _ = run_food(env)
    cov = coverage(env, run_id)
    milk = cov["976759_9176907"]
    assert milk.status == "INCOMPLETE" and milk.partition["end"] == "NOT_FOUND"
    assert milk.partition["reason"] == (
        "not read: the site answered this listing link with its not-found page "
        "(page data route /404, HTTP 200)"
    )
    assert milk.total_count is None and milk.organic_upcs == 0  # never an empty listing, no product from it
    assert cov["976759_976787"].status == "DONE"  # the row's other listing is still read
    assert any(r.status == "valid" for r in records(env, run_id).values())
    with env["factory"]() as s:
        run = s.get(Run, run_id)
        assert run is not None and run.stop_code is None
        assert run.counts["collection_complete"] is False and run.counts["gates"]["G3"] == "FAIL"
        codes = [
            (e.code, (e.data or {}).get("listing"))
            for e in s.scalars(select(Event).where(Event.run_id == run_id))
        ]
    assert ("LISTING_NOT_FOUND", "976759_9176907") in codes
    assert not [c for c, _ in codes if c == "CHALLENGE_DETECTED"]  # never called a refusal


SHIPPING_ONLY = items(51, 52, 53, lines=(("SHIPPING", "0"),))


def test_a_listing_whose_pickup_grid_is_empty_beside_a_shipping_carousel_is_empty_and_the_run_goes_on(
    env: dict[str, Any],
) -> None:
    """Release 1.6.4. Release 1.6.3 took the listing's reported 0 for a missing total, read the number of the
    carousel's products as the total and stopped the run ("the page reports results but shows no product",
    ABNORMAL_RESULT, store held): live L7 of 2026-11-04, the Household Essentials link "Bidets"
    (tests/captures/listing_pages_20261104)."""
    serve(env, {MILK: lambda n: syn.empty_pickup_grid_page(SHIPPING_ONLY, store="3891", title="Milk")})
    run_id, _ = run_food(env)
    cov = coverage(env, run_id)
    milk = cov["976759_9176907"]
    assert milk.status == "EMPTY" and milk.partition["end"] == "EMPTY_PAGE"
    assert milk.partition["reason"] == "the listing shows 0 results"
    assert milk.total_count == 0 and milk.organic_upcs == 0
    assert cov["976759_976787"].status == "DONE"  # the row's other listing is still read
    recs = records(env, run_id).values()
    assert any(r.status == "valid" for r in recs)
    carousel = {i.item_id for i in SHIPPING_ONLY}
    assert not [r for r in recs if str(r.record.get("url", "")).rsplit("/", 1)[-1] in carousel]  # not results
    with env["factory"]() as s:
        run = s.get(Run, run_id)
        assert run is not None and run.stop_code is None
        milk_fetches = [
            f.id
            for f in s.scalars(select(PageFetch).where(PageFetch.run_id == run_id))
            if f.url.startswith(MILK)
        ]
        assert len(milk_fetches) == 1  # one page: the listing ends at its empty first page
        # The empty page ended the listing only after its own store check (the page location names the store
        # and PICKUP); every check of the run passed.
        attested = {
            (a.phase, a.result)
            for a in s.scalars(select(StoreAttestation).where(StoreAttestation.run_id == run_id))
        }
        assert ("task_start", "PASS") in attested and {r for _, r in attested} == {"PASS"}


def test_a_page_that_reports_results_it_does_not_show_still_stops_the_run(env: dict[str, Any]) -> None:
    # Unchanged in release 1.6.4: the same page reporting 5 results, its result grid empty.
    serve(env, {MILK: lambda n: syn.empty_pickup_grid_page(SHIPPING_ONLY, store="3891", reported=5)})
    run_id, _ = run_food(env)
    with env["factory"]() as s:
        run = s.get(Run, run_id)
        assert run is not None and run.stop_code == "ABNORMAL_RESULT"
        assert "the page reports results but shows no product" in (run.stop_detail or "")


@pytest.mark.parametrize(
    ("route", "first_page_listing"),
    [("/browse/[...slug]", False), ("/cp/[...categoryParams]", True)],
    ids=["an-unknown-page-without-a-grid", "a-category-page-after-the-first-result-page"],
)
def test_any_other_page_without_a_result_grid_still_stops_the_run(
    env: dict[str, Any], route: str, first_page_listing: bool
) -> None:
    def pages(n: int) -> str:
        if n == 1 and first_page_listing:
            return listing(items(1, 2, 3), page=1, max_page=3, total=9, cat=("Diapering", CRUMBS))
        return no_grid(route)

    serve(env, {DIAPERING: pages})
    run_id, _ = run_diapering(env)
    with env["factory"]() as s:
        run = s.get(Run, run_id)
        assert run is not None and run.stop_code == "ABNORMAL_RESULT"
        assert "the page data has no search result (unexpected shape)" in (run.stop_detail or "")


def test_a_provider_store_header_naming_another_store_fails_the_page(env: dict[str, Any]) -> None:
    env["mock"].store_header = "1234"
    serve(
        env, {DIAPERING: lambda n: listing(items(1), page=n, max_page=1, total=1, cat=("Diapering", CRUMBS))}
    )
    run_id, _ = run_diapering(env)
    with env["factory"]() as s:
        run = s.get(Run, run_id)
        assert run is not None and run.stop_code == "STORE_NOT_VERIFIED"
        assert "provider_store_header" in (run.stop_detail or "")


def test_verified_store_products_have_no_age_limit() -> None:
    from walmart_headless.config_file import HistoricalConfig

    with pytest.raises(ValueError, match="kept indefinitely"):
        HistoricalConfig(max_age_days=30)
    assert HistoricalConfig().max_age_days is None


def partitioned_diapering(env: dict[str, Any], parent: Callable[[int], str]) -> dict[str, Any]:
    """Diapering read through its two child categories (Diapers 3, Wipes 2), with ``parent`` as its own pages;
    the run's coverage report."""
    serve(
        env,
        {
            DIAPERING: parent,
            DIAPERS: lambda n: listing(
                items(1, 7, 8), page=n, max_page=1, total=3, cat=("Diapers", [*CRUMBS, "5427_486190_1"])
            ),
            WIPES: lambda n: listing(
                items(9, 10), page=n, max_page=1, total=2, cat=("Wipes", [*CRUMBS, "5427_486190_2"])
            ),
        },
    )
    run_id, _ = run_diapering(env)
    with env["factory"]() as s:
        return reconcile.reconcile(s, run_id)


def test_the_coverage_report_judges_a_partition_through_its_children_and_gives_each_csv_row_its_verdict(
    env: dict[str, Any],
) -> None:
    """Release 1.6.7. The listing is larger than its window and its two child categories, both read to their
    last page, balance its total (10 distinct products of 10 reported): the collector calls the row DONE.
    1.6.6's report left the listing ``PARTITIONED``, so no CSV row with a partition could ever be reported
    complete; the report now gives the listing's effective outcome and each CSV row its own verdict."""
    report = partitioned_diapering(env, window_parent)
    row = next(r for r in report["rows"] if r["listing_id"] == "5427_486190")
    assert (row["status"], row.get("effective_status")) == ("PARTITIONED", "DONE"), row
    by_row = {r["category"]: r for r in report.get("csv_rows", [])}
    assert by_row.get("Diapering", {}).get("complete") is True, by_row.get("Diapering")
    assert by_row["Diapering"]["why_not_complete"] == "" and by_row["Diapering"]["listings"] == 1
    others = [r for c, r in by_row.items() if c != "Diapering"]
    assert len(others) == 10 and {r["why_not_complete"] for r in others} == {"not planned by this run"}
    assert report["csv_rows_complete"] == 1 and report["coverage_complete"] is False  # ten rows not planned


def test_a_partition_whose_total_moved_leaves_its_csv_row_incomplete_in_the_report(
    env: dict[str, Any],
) -> None:
    """Release 1.6.7: the same partition, but the listing's own total moved while it was read (12, then 10):
    the partition can never reconcile it. The listing's effective outcome is incomplete, and so is its CSV
    row, with the listing named."""
    report = partitioned_diapering(env, moving_window_parent)
    row = next(r for r in report["rows"] if r["listing_id"] == "5427_486190")
    assert (row["status"], row.get("effective_status")) == ("PARTITIONED", "INCOMPLETE"), row
    by_row = {r["category"]: r for r in report.get("csv_rows", [])}
    diapering = by_row.get("Diapering", {})
    assert diapering.get("complete") is False, diapering
    assert "5427_486190 INCOMPLETE" in diapering["why_not_complete"], diapering
    assert report["csv_rows_complete"] == 0 and report["coverage_complete"] is False
