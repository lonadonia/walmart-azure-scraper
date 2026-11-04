"""Release 1.3.1: the store's follow-up queue (collection/follow_queue.py, table ``follow_up_queue``) keeps
every candidate a run named and did not read to a decision, across runs. A pilot budget never drops a
candidate for good: the next run reads the longest-waiting first, even a candidate it no longer sees itself,
and a run takes only the candidates of its own lineage. SYNTHETIC pages through the Scrape.do mock
(tests/mock_scrapedo.py); nothing reaches a provider."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy import select

from tests.conftest import STORE_KEY
from tests.integration.test_coverage_and_assortment import records
from tests.integration.test_followups import PRODUCTS, TILES, env, outcomes, run, site  # noqa: F401
from walmart_headless.collection import follow_queue
from walmart_headless.collection.config import FollowUpConfig
from walmart_headless.db.models import FollowUpItem, Run, Store

pytestmark = [pytest.mark.postgres]

BUDGET = FollowUpConfig(variants=False, max_pages=1)  # a pilot budget: one product page per kind and run


def queue(e: dict[str, Any], kind: str = "sponsored") -> dict[str, FollowUpItem]:
    with e["factory"]() as s:
        return {r.item_id: r for r in s.scalars(select(FollowUpItem).where(FollowUpItem.kind == kind))}


def follow_counts(e: dict[str, Any], run_id: str) -> dict[str, Any]:
    with e["factory"]() as s:
        r = s.get(Run, run_id)
        assert r is not None
        return dict(r.counts["follow_up"]["sponsored"])


def test_a_pilot_budget_leaves_candidates_queued_and_later_runs_read_the_longest_waiting_first(
    env: dict[str, Any],  # noqa: F811
) -> None:
    asked = site(env, TILES, PRODUCTS)
    first, _ = run(env, BUDGET)
    assert asked == ["9201"]
    out = outcomes(env, first)
    assert out[("sponsored", "9201")]["status"] == "included"
    for item in ("9202", "9203"):
        assert out[("sponsored", item)]["status"] == "not_attempted"
        assert "a pilot budget, was reached" in out[("sponsored", item)]["reason"]
        assert "stays in the store's follow-up queue" in out[("sponsored", item)]["reason"]
    q = queue(env)
    assert {k: r.state for k, r in q.items()} == {
        "9201": "resolved",
        "9202": "pending",
        "9203": "pending",
        "9002": "resolved",  # its own organic tile: a duplicate, no page needed
    }
    assert q["9202"].first_seen_run == first and q["9202"].pages_read == 0
    assert q["9202"].lineage == "substituted"  # the mock transport: never taken by a network run
    assert follow_counts(env, first)["queue_pending_after"] == 2

    asked.clear()
    second, _ = run(env, BUDGET)
    assert asked == ["9202"]  # the longest-waiting unread candidate, before the one the first run read
    out = outcomes(env, second)
    assert out[("sponsored", "9202")]["status"] == "excluded"
    assert out[("sponsored", "9203")]["status"] == out[("sponsored", "9201")]["status"] == "not_attempted"

    asked.clear()
    third, _ = run(env, BUDGET)
    assert asked == ["9203"]  # never read until now: before those read once
    q = queue(env)
    assert (q["9203"].state, q["9203"].last_status, q["9203"].pages_read) == ("pending", "inaccessible", 1)
    assert q["9202"].runs_seen == 3 and q["9202"].first_seen_run == first
    # Each run says what it left: the candidates named again but not read stay pending, with the reason.
    assert follow_counts(env, third)["queue_pending_after"] == 3
    assert {r.last_run for r in q.values()} == {third}

    asked.clear()
    production, _ = run(env, FollowUpConfig(variants=False))  # no budget: every candidate is read
    assert sorted(asked) == ["9201", "9202", "9203"]
    q = queue(env)
    assert {k: r.state for k, r in q.items()} == {
        "9201": "resolved",
        "9202": "resolved",
        "9203": "pending",  # its page still fails: it stays queued, never dropped
        "9002": "resolved",
    }
    assert follow_counts(env, production)["queue_pending_after"] == 1


def test_a_later_run_reads_a_queued_candidate_that_it_no_longer_sees(env: dict[str, Any]) -> None:  # noqa: F811
    asked = site(env, TILES, PRODUCTS)
    first, _ = run(env, FollowUpConfig(variants=False, max_pages=0))
    assert asked == []
    asked = site(env, [t for t in TILES if t.item_id != "9201"], PRODUCTS)  # its sponsored placement is gone
    second, _ = run(env, FollowUpConfig(variants=False))
    out = outcomes(env, second)
    assert out[("sponsored", "9201")]["status"] == "included"
    assert out[("sponsored", "9201")]["queued_from"] == first
    assert "9201" in asked
    assert records(env, second)["wm:9201"].status == "valid"  # read from its own page, in this run
    q = queue(env)
    assert (q["9201"].state, q["9201"].last_run, q["9201"].runs_seen) == ("resolved", second, 1)
    counts = follow_counts(env, second)
    assert counts["from_queue"] == 1 and counts["named_by_run"] == 3  # 9202, 9203 and 9002


def test_a_run_takes_only_the_queued_candidates_of_its_own_lineage(env: dict[str, Any]) -> None:  # noqa: F811
    seen = datetime(2026, 10, 26, 22, 0, tzinfo=UTC)
    with env["factory"]() as s:
        store_id = s.scalar(select(Store.id).where(Store.key == STORE_KEY))
        assert store_id is not None
        # A pending candidate a network run of the store left (as a real collection would): a run whose pages
        # come through a substituted transport never reads it.
        s.add(
            FollowUpItem(
                store_id=store_id,
                kind="sponsored",
                item_id="9301",
                lineage="network",
                url="https://www.walmart.com/ip/Seeded-Diapers-G/9301",
                listing="5427_486190",
                origin="observed",
                first_seen_run="01M5X364ZR83MZ9M60QGPFR7TX",
                first_seen_at=seen,
                last_seen_run="01M5X364ZR83MZ9M60QGPFR7TX",
                last_seen_at=seen,
                runs_seen=1,
                state="pending",
                pages_read=0,
            )
        )
        s.commit()
    asked = site(env, TILES, PRODUCTS)
    run_id, _ = run(env, FollowUpConfig(variants=False))
    assert "9301" not in asked and ("sponsored", "9301") not in outcomes(env, run_id)
    with env["factory"]() as s:
        network = s.scalars(select(FollowUpItem).where(FollowUpItem.lineage == "network")).one()
        assert (network.state, network.pages_read, network.last_run) == ("pending", 0, None)
        assert follow_queue.counts(s, store_id=store_id, lineage="network")["by_kind_and_state"] == {
            "sponsored:pending": 1
        }
