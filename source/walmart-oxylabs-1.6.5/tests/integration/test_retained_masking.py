"""Release 1.4.0: retained products never mask an almost-empty fresh run (the 2026-10-28 brief, section 7:
"Historical retained products must not mask an almost-empty fresh run").

A run publishes, with the products it observed, the products verified by earlier runs of the store that it
did not observe, carried forward unchanged (status ``historical``). They are never the run's yield. A run
whose listing showed one product of the ten an earlier run verified published ten products; without a last
good run to compare with (a bounded run is never compared, nor is a store's first complete run), release
1.3.1 validated it. Release 1.4.0 weighs the retained products against the fresh valid ones (G4), by
category and for the whole run; a bounded run counts the retained products of the listings it read only,
since it carries the others by design.

SYNTHETIC pages through the Scrape.do mock (tests/mock_scrapedo.py); nothing reaches a provider."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from sqlalchemy import select

from tests.conftest import CONFIG
from tests.integration.test_coverage_and_assortment import (
    CRUMBS,
    WIPES,
    env,  # noqa: F401  (env is a fixture)
    items,
    records,
    run_diapering,
    serve,
)
from tests.mock_scrapedo import DIAPERING, listing
from walmart_headless.collection.config import CollectionConfig, DetailConfig, Limits
from walmart_headless.collection.nodes import Node
from walmart_headless.collection.walmart import WalmartCollector
from walmart_headless.core.settings import load_settings
from walmart_headless.db.models import CategorySource, ValidationFinding
from walmart_headless.worker.pipeline import Pipeline

pytestmark = [pytest.mark.postgres]

TEN = tuple(range(1, 11))


def diapering(*ids: int) -> Any:
    return lambda n: listing(items(*ids), page=n, max_page=1, total=len(ids), cat=("Diapering", CRUMBS))


def g4(e: dict[str, Any], run_id: str) -> list[tuple[str, str | None, str, str]]:
    with e["factory"]() as s:
        rows = s.scalars(
            select(ValidationFinding)
            .where(ValidationFinding.run_id == run_id, ValidationFinding.gate == "G4")
            .order_by(ValidationFinding.scope, ValidationFinding.code)
        )
        return [(f.scope, f.ref, f.code, f.severity) for f in rows]


def run_wipes(e: dict[str, Any], *, pilot: bool) -> tuple[str, str]:
    """A run of the Wipes listing alone (a child category of Diapering, ``5427_486190_2``)."""
    settings = load_settings(CONFIG / "settings.yaml")
    pipe = Pipeline(e["engine"], e["storage"], settings, e["store"], e["private_label"])
    cfg = CollectionConfig(limits=Limits(), detail=DetailConfig(enabled=False))
    with e["factory"]() as s:
        cat = s.scalar(select(CategorySource.id).where(CategorySource.category_name == "Diapering"))
        assert cat is not None
        node = Node(4, "Diapering", cat, "Wipes", "5427_486190_2", WIPES)
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
    collector = WalmartCollector(pipe, run_id, config=cfg, trigger="manual")
    status = asyncio.run(pipe.execute(run_id, "test-collector", collector=collector))
    return run_id, status


@pytest.mark.parametrize("pilot", [True, False], ids=["bounded", "complete"])
def test_a_run_that_observed_almost_nothing_is_rejected_whatever_it_retained(
    env: dict[str, Any],  # noqa: F811
    pilot: bool,
) -> None:
    serve(env, {DIAPERING: diapering(*TEN)})
    first, status = run_diapering(env, snapshot={"pilot": pilot})
    assert status in ("validated", "published") and not g4(env, first)
    # The listing now shows one product, read to its end: the nine others are carried forward.
    serve(env, {DIAPERING: diapering(1)})
    second, status = run_diapering(env, snapshot={"pilot": pilot})
    recs = records(env, second)
    assert sorted(r.status for r in recs.values()) == ["historical"] * 9 + ["valid"]
    assert status == "rejected"
    found = g4(env, second)
    assert ("category", "Diapering", "RETAINED_MASKS_YIELD", "FAIL") in found
    assert ("run", None, "RETAINED_MASKS_YIELD", "FAIL") in found
    # A bounded run is never compared with the last good run: before release 1.4.0 nothing rejected it.
    assert any(code == "LOW_YIELD" for _, _, code, _ in found) is not pilot
    with env["factory"]() as s:
        message = s.scalars(
            select(ValidationFinding.message).where(
                ValidationFinding.run_id == second,
                ValidationFinding.code == "RETAINED_MASKS_YIELD",
                ValidationFinding.scope == "run",
            )
        ).one()
    assert (
        message == "90% of the published products are retained from earlier runs (9 retained, 1 fresh valid)"
    )


@pytest.mark.parametrize("pilot", [True, False], ids=["bounded", "complete"])
def test_a_bounded_run_counts_the_retained_products_of_the_listings_it_read(
    env: dict[str, Any],  # noqa: F811
    pilot: bool,
) -> None:
    """The ten products of the Diapering listing are carried into a run of the Wipes listing alone. A
    bounded run did not read their listing (its limits left it out): they are published with it, not
    counted against it. A complete run was to read every listing: they count."""
    serve(env, {DIAPERING: diapering(*TEN)})
    first, _ = run_diapering(env)
    serve(
        env,
        {
            WIPES: lambda n: listing(
                items(21, 22, 23), page=n, max_page=1, total=3, cat=("Wipes", [*CRUMBS, "5427_486190_2"])
            )
        },
    )
    second, status = run_wipes(env, pilot=pilot)
    recs = records(env, second)
    assert sorted(r.status for r in recs.values()) == ["historical"] * 10 + ["valid"] * 3
    hist = (recs["wm:9001"].provenance or {})["historical"]
    assert hist["run_id"] == first and hist["listing"] == "5427_486190"
    masked = [f for f in g4(env, second) if f[2] == "RETAINED_MASKS_YIELD"]
    if pilot:
        assert not masked and status == "validated"
    else:
        assert ("category", "Diapering", "RETAINED_MASKS_YIELD", "FAIL") in masked and status == "rejected"
