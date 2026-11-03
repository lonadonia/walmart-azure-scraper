"""Release 1.4.0: a run's yield is compared with the store's last complete run (G4, abnormal yield), as the
README says: never with a bounded (pilot) run, and a run whose pages come from the network never with a run
whose pages did not.

Release 1.3.1 compared a run's fresh valid records per category with the store's last validated LIVE run of
any kind. A bounded run that read two products of a category became the measure of the next complete run,
which then passed with one product where the last complete run had verified ten (a 50% drop is a warning,
more than 50% fails); a test's synthetic run could become a real run's measure. Release 1.4.0 compares a run
with the last run that read every page it planned and passed its checks, not bounded; a network run with a
network run only (``collection/base.py``, ``last_good_run``).

SYNTHETIC pages through the Scrape.do mock (tests/mock_scrapedo.py): every collected run here has the
``substituted`` lineage. The network run is a run row created directly (no page is collected for it), so
nothing reaches a provider."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from sqlalchemy import select

from tests.conftest import CONFIG
from tests.integration.test_coverage_and_assortment import (
    CRUMBS,
    env,  # noqa: F401  (env is a fixture)
    items,
    serve,
)
from tests.mock_scrapedo import DIAPERING, listing
from walmart_headless.acquisition import lineage
from walmart_headless.collection.base import last_good_run
from walmart_headless.collection.config import CollectionConfig, DetailConfig, Limits
from walmart_headless.collection.nodes import Node
from walmart_headless.collection.walmart import WalmartCollector
from walmart_headless.config_file import HistoricalConfig
from walmart_headless.core.settings import Settings, load_settings
from walmart_headless.db.models import CategorySource, CollectionSegment, Run, Store, ValidationFinding
from walmart_headless.worker.pipeline import Pipeline
from walmart_headless.worker.runs import create_run

pytestmark = [pytest.mark.postgres]

TEN = tuple(range(1, 11))


def run(e: dict[str, Any], ids: tuple[int, ...], *, pilot: bool) -> tuple[str, str]:
    """A run of the Diapering listing showing products ``ids``, read to its end. Nothing is carried forward
    (``historical`` off), so the yield check alone judges what the run observed."""
    serve(
        e,
        {
            DIAPERING: lambda n: listing(
                items(*ids), page=n, max_page=1, total=len(ids), cat=("Diapering", CRUMBS)
            )
        },
    )
    settings = load_settings(CONFIG / "settings.yaml")
    pipe = Pipeline(e["engine"], e["storage"], settings, e["store"], e["private_label"])
    cfg = CollectionConfig(limits=Limits(), detail=DetailConfig(enabled=False))
    with e["factory"]() as s:
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
                "pilot": pilot,
            },
        )
        s.commit()
    collector = WalmartCollector(
        pipe, run_id, config=cfg, trigger="manual", historical=HistoricalConfig(enabled=False)
    )
    status = asyncio.run(pipe.execute(run_id, "test-collector", collector=collector))
    return run_id, status


def g4(e: dict[str, Any], run_id: str) -> list[tuple[str, str | None, str, str, str, dict[str, Any]]]:
    with e["factory"]() as s:
        rows = s.scalars(
            select(ValidationFinding)
            .where(ValidationFinding.run_id == run_id, ValidationFinding.gate == "G4")
            .order_by(ValidationFinding.scope, ValidationFinding.code)
        )
        return [(f.scope, f.ref, f.code, f.severity, f.message, dict(f.metrics or {})) for f in rows]


def baseline(e: dict[str, Any], run_id: str) -> Any:
    with e["factory"]() as s:
        row = s.get(Run, run_id)
        assert row is not None
        return (row.counts or {}).get("yield_baseline", "not recorded")


def test_a_complete_run_is_compared_with_the_last_complete_run_never_a_bounded_one(
    env: dict[str, Any],  # noqa: F811
) -> None:
    first, status = run(env, TEN, pilot=False)
    assert status in ("validated", "published") and g4(env, first) == []
    bounded, status = run(env, (1, 2), pilot=True)
    assert status == "validated" and g4(env, bounded) == []
    # The listing now shows one product of the ten the last complete run verified.
    third, status = run(env, (1,), pilot=False)
    assert g4(env, third) == [
        (
            "category",
            "Diapering",
            "LOW_YIELD",
            "FAIL",
            "drop 90% vs last good",
            {"assigned": 1, "prior_good": 10},
        )
    ]
    assert status == "rejected"
    assert baseline(env, third) == first
    assert baseline(env, bounded) is None  # a bounded run is never compared


def test_a_network_run_is_never_compared_with_a_run_whose_pages_did_not_come_from_the_network(
    env: dict[str, Any],  # noqa: F811
) -> None:
    first, status = run(env, TEN, pilot=False)
    assert status in ("validated", "published")
    with env["factory"]() as s:
        done = s.get(Run, first)
        assert done is not None
        store = s.get(Store, done.store_id)
        assert store is not None
        real = create_run(s, store, Settings(), mode="LIVE", trigger="test")
        real.config_snapshot = {
            **real.config_snapshot,
            "lineage": {"transport": lineage.NETWORK, "replaced": []},
        }
        s.commit()
        store_id, real_id = store.id, real.id
    # A test's run is compared with the test's last complete run.
    second, status = run(env, (1,), pilot=False)
    assert status == "rejected" and baseline(env, second) == first
    with env["factory"]() as s:
        assert lineage.of_run(s, first).lineage == lineage.SUBSTITUTED
        assert last_good_run(s, store_id, real_id) is None
        # Had the first run's pages come from the network (its lineage rewritten here, in the test database
        # only), it would be the network run's measure, and still the measure of a test's run.
        row = s.get(Run, first)
        assert row is not None
        row.config_snapshot = {
            **row.config_snapshot,
            "lineage": {"transport": lineage.NETWORK, "replaced": []},
        }
        for seg in s.scalars(select(CollectionSegment).where(CollectionSegment.run_id == first)):
            seg.stats = {**(seg.stats or {}), "lineage": {"transport": lineage.NETWORK, "replaced": []}}
        s.commit()
        assert lineage.of_run(s, first).lineage == lineage.NETWORK
        assert last_good_run(s, store_id, real_id) == first
        assert last_good_run(s, store_id, second) == first
