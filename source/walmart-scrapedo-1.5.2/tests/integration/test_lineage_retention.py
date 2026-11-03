"""Release 1.3.1 lineage and retention (acquisition/lineage.py, collection/retention.py): an earlier
observation serves a run only from a run of the same lineage that passed the checks invalidating its
observations, read from a page that was no challenge, and a carried record is checked again.

SYNTHETIC pages through the Scrape.do mock (tests/mock_scrapedo.py): every collected run here has the
``substituted`` lineage. The ``network`` runs that receive history are run rows created directly (no page
is collected for them), so nothing reaches a provider."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from tests.conftest import STORE_KEY
from tests.integration.test_coverage_and_assortment import (
    CRUMBS,
    env,  # noqa: F401  (env is a fixture)
    items,
    records,
    run_diapering,
    serve,
)
from tests.mock_scrapedo import DIAPERING, listing
from walmart_headless.acquisition import lineage
from walmart_headless.collection import retention
from walmart_headless.core.settings import Settings
from walmart_headless.core.timeutil import utcnow
from walmart_headless.db.models import (
    CollectionSegment,
    PageFetch,
    ProductObservation,
    RecordRow,
    Run,
    Store,
    ValidationFinding,
)
from walmart_headless.worker.runs import create_run

pytestmark = [pytest.mark.postgres]


def page(*ids: int) -> Any:
    return lambda n: listing(items(*ids), page=n, max_page=1, total=len(ids), cat=("Diapering", CRUMBS))


def store_row(s: Session) -> Store:
    return s.scalars(select(Store).where(Store.key == STORE_KEY)).one()


def receiving_run(e: dict[str, Any], transport: str | None) -> str:
    """A LIVE run row recording ``transport`` (None: none, as a run made before release 1.3.1)."""
    with e["factory"]() as s:
        run = create_run(s, store_row(s), Settings(), mode="LIVE", trigger="test")
        if transport is not None:
            run.config_snapshot = {**run.config_snapshot, "lineage": {"transport": transport, "replaced": []}}
        s.commit()
        return run.id


def carry(e: dict[str, Any], run_id: str, exclude_relative: bool = False) -> dict[str, int]:
    with e["factory"]() as s:
        counts = retention.carry_forward(
            s,
            run_id,
            store_row(s).id,
            utcnow(),
            location_id=e["store"].location_id,
            modality=e["store"].modality.value,
            run_complete=True,
            exclude_relative=exclude_relative,
        )
        s.commit()
    return counts


def lineage_of(e: dict[str, Any], run_id: str) -> lineage.RunLineage:
    with e["factory"]() as s:
        return lineage.of_run(s, run_id)


def fail(e: dict[str, Any], run_id: str, gate: str) -> None:
    with e["factory"]() as s:
        s.add(
            ValidationFinding(
                run_id=run_id, scope="run", gate=gate, severity="FAIL", code="SYNTHETIC", message="test"
            )
        )
        s.commit()


def historical(e: dict[str, Any], run_id: str) -> dict[str, int]:
    with e["factory"]() as s:
        run = s.get(Run, run_id)
        assert run is not None
        return dict(run.counts["historical"])


def test_synthetic_observations_never_become_the_history_of_a_network_run(env: dict[str, Any]) -> None:  # noqa: F811
    serve(env, {DIAPERING: page(1, 2)})
    first, _ = run_diapering(env, snapshot={"lineage": lineage.current()})
    assert lineage_of(env, first).lineage == lineage.SUBSTITUTED  # the mock replaced the transport

    real = receiving_run(env, lineage.NETWORK)
    counts = carry(env, real)
    assert counts["carried_forward"] == 0 and counts["refused_sources"] == 2
    assert records(env, real) == {}
    with env["factory"]() as s:
        refused: dict[str, str] = {}
        st = store_row(s)
        got = retention.verified_local(
            s, st.id, env["store"].location_id, "PICKUP", exclude_run=real, refused=refused
        )
        assert got == {} and set(refused) == {"wm:9001", "wm:9002"}
        assert "lineage substituted" in refused["wm:9001"]

    legacy = receiving_run(env, None)  # records no lineage and attested by nobody: takes nothing
    assert lineage_of(env, legacy).lineage == lineage.UNRECORDED
    assert carry(env, legacy)["carried_forward"] == 0 and records(env, legacy) == {}

    same = receiving_run(env, lineage.SUBSTITUTED)  # the same observations serve their own lineage
    assert carry(env, same)["carried_forward"] == 2
    hist = records(env, same)["wm:9001"].provenance["historical"]
    assert hist["run_id"] == first and hist["lineage"] == lineage.SUBSTITUTED


def test_a_run_made_before_1_3_1_serves_only_once_attested_and_its_history_is_traceable(
    env: dict[str, Any],  # noqa: F811
) -> None:
    serve(env, {DIAPERING: page(1, 2)})
    first, _ = run_diapering(env)
    with env["factory"]() as s:
        # What release 1.3.0 stored: no lineage in the run or in its segments.
        for seg in s.scalars(select(CollectionSegment).where(CollectionSegment.run_id == first)):
            seg.stats = {k: v for k, v in (seg.stats or {}).items() if k != "lineage"}
        s.commit()
    assert lineage_of(env, first).lineage == lineage.UNRECORDED
    real = receiving_run(env, lineage.NETWORK)
    assert carry(env, real)["carried_forward"] == 0  # unattested: it does not serve

    with env["factory"]() as s:
        lineage.attest(
            s, first, actor="operator", reason="collected by release 1.3.0", evidence="journal, ledger"
        )
        s.commit()
    assert carry(env, real)["carried_forward"] == 2
    rec = records(env, real)["wm:9001"]
    hist = rec.provenance["historical"]
    assert rec.status == "historical" and "CARRIED_FORWARD" in rec.flags
    assert hist["run_id"] == first and hist["lineage"] == lineage.NETWORK
    assert hist["lineage_basis"].startswith("attested by operator") and hist["crawl_date"]
    with env["factory"]() as s:
        fetch = s.get(PageFetch, hist["page_fetch_id"])
        assert fetch is not None and fetch.run_id == first  # the page it was read from
        assert retention.carried_problems(s, real) == []

    # A segment of another lineage, found later, withdraws the attestation's effect.
    with env["factory"]() as s:
        seg = s.scalars(select(CollectionSegment).where(CollectionSegment.run_id == first)).first()
        assert seg is not None
        seg.stats = {**(seg.stats or {}), "lineage": {"transport": "substituted", "replaced": ["scrapedo"]}}
        s.commit()
        assert lineage.of_run(s, first).lineage == lineage.SUBSTITUTED
        problems = retention.carried_problems(s, real)
    assert len(problems) == 2 and all("lineage substituted" in p for p in problems)


def test_a_run_failing_a_check_that_invalidates_its_observations_never_serves(env: dict[str, Any]) -> None:  # noqa: F811
    serve(env, {DIAPERING: page(1, 2)})
    first, _ = run_diapering(env)
    fail(env, first, "G1")  # the store check: its observations are not the store's
    serve(env, {DIAPERING: page(3)})
    later, _ = run_diapering(env)
    recs = records(env, later)
    assert set(recs) == {"wm:9003"}
    assert historical(env, later)["refused_sources"] == 2

    # Rejected only for its coverage, a run keeps its authentic observations.
    with env["factory"]() as s:
        for f in s.scalars(select(ValidationFinding).where(ValidationFinding.run_id == first)):
            if f.gate == "G1" and f.code == "SYNTHETIC":
                s.delete(f)
        s.commit()
    fail(env, first, "G3")
    third, _ = run_diapering(env)
    recs = records(env, third)
    assert recs["wm:9001"].status == recs["wm:9002"].status == "historical"
    assert recs["wm:9001"].provenance["historical"]["run_id"] == first


def test_an_observation_read_from_a_challenged_page_never_serves(env: dict[str, Any]) -> None:  # noqa: F811
    serve(env, {DIAPERING: page(1, 2)})
    first, _ = run_diapering(env)
    with env["factory"]() as s:
        obs = s.scalars(
            select(ProductObservation).where(
                ProductObservation.run_id == first, ProductObservation.upc == "wm:9001"
            )
        ).one()
        fetch = s.get(PageFetch, obs.page_fetch_id)
        assert fetch is not None
        fetch.challenge = True  # the page, judged again, was a challenge (both products are on it)
        s.commit()
    serve(env, {DIAPERING: page(3)})
    later, _ = run_diapering(env)
    assert set(records(env, later)) == {"wm:9003"}
    assert historical(env, later)["refused_sources"] == 2


def test_a_carried_record_is_checked_again_and_g13_lists_what_no_longer_serves(env: dict[str, Any]) -> None:  # noqa: F811
    serve(env, {DIAPERING: page(1, 2)})
    first, _ = run_diapering(env)
    with env["factory"]() as s:
        rec = s.scalars(select(RecordRow).where(RecordRow.run_id == first, RecordRow.upc == "wm:9002")).one()
        rec.record = {**rec.record, "regular_price": "1.9"}  # a record the format check (G6) refuses
        s.commit()
    serve(env, {DIAPERING: page(3)})
    later, _ = run_diapering(env)
    recs = records(env, later)
    assert recs["wm:9001"].status == "historical" and "wm:9002" not in recs
    assert historical(env, later)["not_valid_now"] == 1
    with env["factory"]() as s:
        run = s.get(Run, later)
        assert run is not None and run.counts["gates"]["G13"] == "PASS"
        assert retention.carried_problems(s, later) == []

    fail(env, first, "G12")  # found after the carry: the source's observations are not trusted now
    with env["factory"]() as s:
        problems = retention.carried_problems(s, later)
    assert problems == [f"carried record wm:9001: run {first} failed G12: its observations are not trusted"]


def rewrite_logs(e: dict[str, Any], run_id: str, key: str, change: Callable[[dict[str, Any]], None]) -> None:
    """Change the stored log of every result-tile observation of ``key`` in ``run_id``."""
    with e["factory"]() as s:
        observations = list(
            s.scalars(
                select(ProductObservation).where(
                    ProductObservation.run_id == run_id,
                    ProductObservation.upc == key,
                    ProductObservation.source == "card",
                )
            )
        )
        assert observations
        for obs in observations:
            log = dict(obs.structured["walmart"])
            change(log)
            obs.structured = {**obs.structured, "walmart": log}
        s.commit()


def rejected_now(e: dict[str, Any], receiving: str) -> dict[str, str]:
    with e["factory"]() as s:
        rejected: dict[str, str] = {}
        retention.verified_local(
            s, store_row(s).id, e["store"].location_id, "PICKUP", exclude_run=receiving, rejected=rejected
        )
    return rejected


def test_an_earlier_observation_is_carried_unless_it_displayed_estimated_weight_wording(
    env: dict[str, Any],  # noqa: F811
) -> None:
    """Release 1.4.0 (the client's rule: approximate or estimated-weight wording excludes a product, being
    sold by weight alone does not). An earlier observation of a product charged by weight is carried
    forward when it displayed no such wording; one that showed an estimate next to its price ("each
    (est.)") is not; one of a release that kept no reading of that wording (1.3.0) is not either, since
    whether it showed one is unknown. With relative prices excluded (records.exclude_relative_price_items,
    the 1.3.1 rule) none is carried."""
    serve(env, {DIAPERING: page(1, 2)})
    first, _ = run_diapering(env, snapshot={"lineage": lineage.current()})

    def sold_by_weight(log: dict[str, Any]) -> None:  # a release 1.3.1+ tile showing no wording
        log.update(sales_unit="EACH_WEIGHT", price_condition=None)
        log["weight_priced"] = {"value": True, "by": ["sales unit EACH_WEIGHT", "price line SOLD_BY_WEIGHT"]}

    rewrite_logs(env, first, "wm:9001", sold_by_weight)
    kept = receiving_run(env, lineage.SUBSTITUTED)
    assert carry(env, kept)["carried_forward"] == 2
    assert set(records(env, kept)) == {"wm:9001", "wm:9002"}
    relative = receiving_run(env, lineage.SUBSTITUTED)
    counts = carry(env, relative, exclude_relative=True)
    assert counts["carried_forward"] == 1 and counts["not_verified_by_current_rules"] == 1
    with env["factory"]() as s:
        rejected: dict[str, str] = {}
        retention.verified_local(
            s,
            store_row(s).id,
            env["store"].location_id,
            "PICKUP",
            exclude_run=relative,
            rejected=rejected,
            exclude_relative=True,
        )
    assert rejected["wm:9001"].startswith(
        "its final cost depends on the weight (sales unit EACH_WEIGHT, price line SOLD_BY_WEIGHT): a "
        "relative price, not exported"
    )

    def estimated(log: dict[str, Any]) -> None:  # "each (est.)" next to the price, read by release 1.3.1
        log["price_condition"] = {
            "text": "each (est.)",
            "path": "priceInfo.priceDisplayCodes.priceDisplayCondition",
        }

    rewrite_logs(env, first, "wm:9001", estimated)
    not_kept = receiving_run(env, lineage.SUBSTITUTED)
    counts = carry(env, not_kept)
    assert counts["carried_forward"] == 1 and counts["not_verified_by_current_rules"] == 1
    assert set(records(env, not_kept)) == {"wm:9002"}
    assert rejected_now(env, not_kept)["wm:9001"].startswith(
        f"it displayed approximate or estimated-weight wording in that run (est.; run {first}"
    )

    def release_1_3_0(log: dict[str, Any]) -> None:  # its sales unit, no reading of its own
        for k in ("weight_priced", "price_condition", "approx_weight"):
            log.pop(k, None)

    rewrite_logs(env, first, "wm:9001", release_1_3_0)
    unknown = receiving_run(env, lineage.SUBSTITUTED)
    counts = carry(env, unknown)
    assert counts["carried_forward"] == 1 and counts["not_verified_by_current_rules"] == 1
    assert rejected_now(env, unknown)["wm:9001"].startswith(
        "its final cost depends on the weight (sales unit EACH_WEIGHT) and its release kept no reading of "
        "Walmart's wording next to the price"
    )


def test_a_run_recording_the_network_lineage_never_runs_with_a_substituted_transport(
    env: dict[str, Any],  # noqa: F811
) -> None:
    serve(env, {DIAPERING: page(1)})
    run_id, status = run_diapering(env, snapshot={"lineage": {"transport": "network", "replaced": []}})
    with env["factory"]() as s:
        run = s.get(Run, run_id)
        assert run is not None and status == run.status == "interrupted"
        assert run.stop_code == "LINEAGE_MISMATCH" and "substituted" in (run.stop_detail or "")
        assert s.scalars(select(CollectionSegment).where(CollectionSegment.run_id == run_id)).first() is None
        assert s.scalars(select(PageFetch).where(PageFetch.run_id == run_id)).first() is None
    assert not [c for c in env["mock"].calls if c[1] == "/plugin/walmart/store"]


def test_the_carried_synthetic_record_of_the_2026_10_26_test_target_cannot_recur(
    env: dict[str, Any],  # noqa: F811
) -> None:
    """On 2026-10-26 the VM's publication test target (database walmart_pubtest) published run 01M5X82X
    with one record carried from run 01M5X7ZR, a rejected run of the fault-injection harness (synthetic
    pages: "SYNTHETIC Milk, Gallon, 128 fl oz"). The same shape here: a rejected run of a substituted
    transport, then a network run of the store. It takes nothing; and a record carried the 1.3.0 way (no
    lineage check) fails G13, so such a run cannot be published."""
    serve(env, {DIAPERING: page(1, 2)})
    injected, _ = run_diapering(env, snapshot={"lineage": lineage.current()})
    with env["factory"]() as s:
        run = s.get(Run, injected)
        assert run is not None
        run.status = "rejected"  # as the harness's runs were
        s.commit()
    real = receiving_run(env, lineage.NETWORK)
    assert carry(env, real)["carried_forward"] == 0 and records(env, real) == {}

    # What release 1.3.0 did: the earlier record carried without asking where its pages came from.
    with env["factory"]() as s:
        src = s.scalars(
            select(RecordRow).where(RecordRow.run_id == injected, RecordRow.upc == "wm:9001")
        ).one()
        obs = s.scalars(
            select(ProductObservation).where(
                ProductObservation.run_id == injected, ProductObservation.upc == "wm:9001"
            )
        ).one()
        s.add(
            RecordRow(
                run_id=real,
                mode="LIVE",
                upc=src.upc,
                record=dict(src.record),
                record_sha256=src.record_sha256,
                status=retention.CARRIED_STATUS,
                reasons=["CARRIED_FORWARD"],
                flags=["CARRIED_FORWARD"],
                provenance={"historical": {"run_id": injected, "page_fetch_id": obs.page_fetch_id}},
            )
        )
        s.commit()
        problems = retention.carried_problems(s, real)
    assert len(problems) == 1 and problems[0].startswith("carried record wm:9001: run ")
    assert "lineage substituted" in problems[0] and "the receiving run's is network" in problems[0]
