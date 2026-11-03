from __future__ import annotations

from walmart_headless.core.findings import DataMode, Severity
from walmart_headless.core.schema import build_record
from walmart_headless.core.settings import Settings
from walmart_headless.validation.gates import (
    AttestationSummary,
    CategoryOutcome,
    GateStatus,
    RunEvidence,
    deal_price_supported,
    run_gates,
)

S = Settings()


def rec(upc: str, **kw: str) -> dict[str, str]:
    base = {
        "upc": upc,
        "product_title": "T",
        "url": f"https://www.marianos.com/p/t/{upc}",
        "category": "Produce",
        "regular_price": "1.00",
        "crawl_date": "2026-10-17",
    }
    return build_record({**base, **kw})


def good_evidence(n: int = 600) -> RunEvidence:
    records = [rec(f"{i:013d}", category=["Produce", "Meat", "Dairy"][i % 3]) for i in range(n)]
    return RunEvidence(
        mode=DataMode.LIVE,
        attestations=(AttestationSummary("preflight", True), AttestationSummary("final", True)),
        categories=(CategoryOutcome(1, "Produce", "DONE", 200, 210, node_difference={"06111": 0}),),
        exported_records=records,
        valid_upcs=frozenset(r["upc"] for r in records),
        contract_canary_ok=True,
        tasks_all_terminal=True,
        artifact_hashes_verified=True,
        manifest_complete=True,
    )


def status(ev: RunEvidence) -> dict[str, GateStatus]:
    return {r.gate: r.status for r in run_gates(ev, S).results}


def test_good_run_is_publishable_and_contest_ready() -> None:
    out = run_gates(good_evidence(), S)
    assert out.publishable and out.contest_ready, [(r.gate, r.findings) for r in out.results if r.findings]


def test_location_failure_blocks_publication() -> None:
    ev = good_evidence()
    ev.attestations = (
        AttestationSummary("preflight", True),
        AttestationSummary("periodic", False, ("A4",)),
        AttestationSummary("final", True),
    )
    out = run_gates(ev, S)
    assert status(ev)["G1"] is GateStatus.FAIL and not out.publishable


def test_duplicate_upc_fails_g7() -> None:
    ev = good_evidence(10)
    ev.exported_records = [*ev.exported_records, ev.exported_records[0]]
    assert status(ev)["G7"] is GateStatus.FAIL


def test_yield_drop_thresholds() -> None:
    ev = good_evidence()
    ev.categories = (CategoryOutcome(1, "Produce", "DONE", 60, 100),)
    assert status(ev)["G4"] is GateStatus.WARN
    ev.categories = (CategoryOutcome(1, "Produce", "DONE", 40, 100),)
    assert status(ev)["G4"] is GateStatus.FAIL
    ev.categories = (CategoryOutcome(1, "Produce", "DONE", 0, 0),)
    assert status(ev)["G4"] is GateStatus.FAIL
    ev.categories = (CategoryOutcome(1, "Produce", "DONE", 0, 0, zero_rule_holds=True),)
    assert status(ev)["G4"] is GateStatus.PASS


def test_retained_products_never_mask_an_almost_empty_fresh_run() -> None:
    """Release 1.4.0 (the 2026-10-28 brief, section 7). Retained products (carried forward from earlier runs)
    are published with a run's fresh products but are never its yield. Without a last good run to compare
    with (a bounded run, or a store's first), 2 fresh products published with 300 retained passed G4 up to
    release 1.3.1."""
    ev = good_evidence()
    ev.categories = (CategoryOutcome(1, "Produce", "DONE", 2, None, retained_records=300),)
    out = run_gates(ev, S)
    g4 = next(r for r in out.results if r.gate == "G4")
    assert g4.status is GateStatus.FAIL and not out.publishable
    assert [(f.scope, f.ref, f.code, f.severity) for f in g4.findings] == [
        ("category", "Produce", "RETAINED_MASKS_YIELD", Severity.FAIL),
        ("run", None, "RETAINED_MASKS_YIELD", Severity.FAIL),
    ]
    assert g4.findings[1].metrics == {"retained": 300, "fresh_valid": 2, "retained_share": 0.9934}
    assert g4.metrics == {"fresh_valid": 2, "retained": 300}
    # A category whose listings all showed "no results" is refused too when earlier products fill it.
    ev.categories = (
        CategoryOutcome(1, "Produce", "DONE", 0, None, zero_rule_holds=True, retained_records=50),
    )
    assert status(ev)["G4"] is GateStatus.FAIL
    # Above 30% retained warns; 30% or less passes.
    ev.categories = (CategoryOutcome(1, "Produce", "DONE", 60, None, retained_records=40),)
    assert status(ev)["G4"] is GateStatus.WARN
    ev.categories = (CategoryOutcome(1, "Produce", "DONE", 70, None, retained_records=30),)
    assert status(ev)["G4"] is GateStatus.PASS
    # By category and for the whole run: a masked category fails the run whatever the others yield.
    ev.categories = (
        CategoryOutcome(1, "Produce", "DONE", 900, None),
        CategoryOutcome(2, "Meat", "DONE", 1, None, retained_records=99),
    )
    g4 = next(r for r in run_gates(ev, S).results if r.gate == "G4")
    assert g4.status is GateStatus.FAIL
    assert [(f.scope, f.ref, f.severity) for f in g4.findings] == [("category", "Meat", Severity.FAIL)]


def test_coverage_has_no_ratio_threshold() -> None:
    # Release 1.3.1: no 98 % / 90 % tolerance. A listing short by 1 of its reported total is not complete,
    # and a DONE category may not carry any unreconciled difference (an overcount neither).
    ev = good_evidence()
    assert status(ev)["G3"] is GateStatus.PASS
    for diff in (1, -2):
        ev.categories = (CategoryOutcome(1, "Produce", "DONE", 200, None, node_difference={"06111": diff}),)
        assert status(ev)["G3"] is GateStatus.FAIL
    ev.categories = (CategoryOutcome(1, "Produce", "INCOMPLETE", 200, None, node_difference={"06111": 1}),)
    assert status(ev)["G3"] is GateStatus.FAIL
    ev.categories = (CategoryOutcome(1, "Produce", "BLOCKED", 200, None),)
    st = status(ev)
    assert st["G2"] is GateStatus.FAIL and st["G3"] is GateStatus.FAIL


def test_fixture_mode_is_never_contest_ready() -> None:
    ev = good_evidence()
    ev.mode = DataMode.FIXTURE
    out = run_gates(ev, S)
    assert out.publishable and not out.contest_ready


def test_promotion_sanity() -> None:
    assert deal_price_supported("2 For $5.00", "5.00")
    assert deal_price_supported("4/$10 when you buy 4 or more", "10.00")
    assert not deal_price_supported("Buy 1, Get 1 Free", "2.50")
    ev = good_evidence(10)
    ev.exported_records = [
        rec("0000000000001", volume_deals_description="Buy 1, Get 1 Free", volume_deals_price="2.50")
    ]
    assert status(ev)["G11"] is GateStatus.FAIL


def test_missing_integrity_and_contract_fail() -> None:
    ev = good_evidence()
    ev.contract_canary_ok = None
    ev.manifest_complete = False
    st = status(ev)
    assert st["G12"] is GateStatus.FAIL and st["G13"] is GateStatus.FAIL


def test_a_carried_record_that_no_longer_serves_fails_g13() -> None:
    ev = good_evidence(10)
    assert status(ev)["G13"] is GateStatus.PASS
    ev.carried_problems = ("carried record wm:1: run R failed G12: its observations are not trusted",)
    out = run_gates(ev, S)
    g13 = next(r for r in out.results if r.gate == "G13")
    assert g13.status is GateStatus.FAIL and not out.publishable
    assert [f.message for f in g13.findings] == list(ev.carried_problems)
