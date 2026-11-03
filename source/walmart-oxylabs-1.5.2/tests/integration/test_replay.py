"""``walmart-collector replay``: an earlier run's stored pages read again offline by the current code, through
the CLI and the run pipeline (SYNTHETIC pages of the Scrape.do mock; nothing reaches Scrape.do or Walmart)."""

from __future__ import annotations

import json
import signal
from pathlib import Path
from typing import Any, cast

import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from tests.integration.test_followups import PRODUCTS, TILES, site
from tests.integration.test_operations import Env, env  # noqa: F401  (the CLI fixture)
from walmart_headless.collection import reconcile
from walmart_headless.collection.replay import ReplaySession
from walmart_headless.db.models import (
    Event,
    FollowUpItem,
    ProductObservation,
    PublicationPointer,
    RecordRow,
    Run,
    ValidationFinding,
)

STORE = "walmart-3891-pickup"


def _rows(e: Env, run_id: str) -> dict[str, RecordRow]:
    with sessionmaker(e.engine, expire_on_commit=False)() as s:
        return {r.upc: r for r in s.scalars(select(RecordRow).where(RecordRow.run_id == run_id))}


def _observed(e: Env, run_id: str) -> dict[str, str]:
    with sessionmaker(e.engine, expire_on_commit=False)() as s:
        return {
            o.upc: o.observed_at.isoformat()
            for o in s.scalars(select(ProductObservation).where(ProductObservation.run_id == run_id))
        }


def test_a_replay_reads_the_stored_pages_again_without_any_request_and_keeps_their_times(env: Env) -> None:  # noqa: F811
    assert env.result("run", "--store", STORE)[0] == 0
    [source] = env.runs()
    calls = len(env.mock.calls)
    with sessionmaker(env.engine, expire_on_commit=False)() as s:
        published_before = s.get(PublicationPointer, source.store_id)

    code, _ = env.result("replay", "--run", source.id)
    assert code == 0
    assert len(env.mock.calls) == calls  # not one request: robots.txt, store page, listings, product pages
    replay = next(r for r in env.runs() if r.id != source.id)
    assert replay.mode == "REPLAY" and replay.trigger == "replay"
    assert replay.config_snapshot["replay"]["source_run"] == source.id
    # The same products, observed when the source run observed them (so the same crawl dates).
    src_rows, rep_rows = _rows(env, source.id), _rows(env, replay.id)
    assert {k for k, r in rep_rows.items() if r.status != "historical"} == {
        k for k, r in src_rows.items() if r.status != "historical"
    }
    assert _observed(env, replay.id) == _observed(env, source.id)
    assert all(rep_rows[k].record["crawl_date"] == src_rows[k].record["crawl_date"] for k in rep_rows)
    # The product pages the source run read are read again from storage, with their original time.
    replayed = {
        k: r.provenance["upc_detail"] for k, r in rep_rows.items() if (r.provenance or {}).get("upc_detail")
    }
    original = {
        k: r.provenance["upc_detail"] for k, r in src_rows.items() if (r.provenance or {}).get("upc_detail")
    }
    for k, d in replayed.items():
        assert d["status"] == original[k]["status"] and d.get("value") == original[k].get("value")
        if d.get("requested_at"):
            assert d["requested_at"] == original[k]["requested_at"]
    with sessionmaker(env.engine, expire_on_commit=False)() as s:
        findings = [
            f.message
            for f in s.scalars(select(ValidationFinding).where(ValidationFinding.run_id == replay.id))
        ]
        published_after = s.get(PublicationPointer, source.store_id)
    assert any("REPLAY" in m and "not a fresh observation" in m for m in findings)  # G14, never contest data
    # Each result page's grid filter is read again from the stored page (release 1.4.1): the source run asked
    # for Walmart's Pickup grid, and the replay finds each page under the collector's own URL.
    with sessionmaker(env.engine, expire_on_commit=False)() as s:
        grids = [
            {r["listing_id"]: r["grid_fulfillment_filter"] for r in reconcile.reconcile(s, run)["rows"]}
            for run in (source.id, replay.id)
        ]
    assert grids[0] == grids[1] and {f for v in grids[0].values() for f in v} == {"Pickup"}
    # Never published: the store's published dataset is the one before the replay.
    assert (published_before.publication_id if published_before else None) == (
        published_after.publication_id if published_after else None
    )


def test_a_replays_exports_say_its_rows_were_read_again_never_observed_by_it(env: Env) -> None:  # noqa: F811
    # Release 1.3.1: a replay's record map called each row a fresh observation of the replay run
    # (observation_kind "fresh", observed_by_run the replay), its supporting log counted them as fresh and its
    # manifest as fresh records, although a replay requests nothing. Found in the offline reprocessing of the
    # 2026-10-26 Azure run 01M5X364ZR83MZ9M60QGPFR7TX.
    assert env.result("run", "--store", STORE)[0] == 0
    [source] = env.runs()
    assert env.result("replay", "--run", source.id)[0] == 0
    replay = next(r for r in env.runs() if r.id != source.id)
    exports = env.data / "runs" / STORE / replay.id / "exports"
    manifest = json.loads((exports / "manifest.json").read_text("utf-8"))
    rows = json.loads((exports / "record_map.json").read_text("utf-8"))["rows"]
    fresh_file = json.loads((exports / "products_fresh.json").read_text("utf-8"))
    assert manifest["mode"] == "REPLAY" and "fresh_record_count" not in manifest
    assert rows and manifest["replayed_record_count"] == len(fresh_file) == len(rows)
    assert {r["observation_kind"] for r in rows} == {"replayed"}
    assert {(r["observed_by_run"], r["read_again_by_run"], r["code"]["replay_of"]) for r in rows} == {
        (source.id, replay.id, source.id)
    }
    observed = _observed(env, source.id)
    assert all(r["observed_at"] == observed[r["key"]].replace("+00:00", "Z") for r in rows)
    log = json.loads((exports / "provenance.json").read_text("utf-8"))
    assert log["replay_of"] == source.id
    assert {v["observation_kind"] for v in log["records"].values() if v["exported"]} == {"replayed"}
    # The supporting log covers every record (excluded ones too); the record map the exported rows.
    counts = log["counts"]["observed"]
    replayed = [v for v in log["records"].values() if v["observation_kind"] == "replayed"]
    assert counts["fresh"] == counts["fresh_earlier_segment"] == 0
    assert counts["replayed"] == len(replayed) and len(replayed) > len(rows)
    # The source run's own exports keep their labels.
    source_manifest = json.loads(
        (env.data / "runs" / STORE / source.id / "exports" / "manifest.json").read_text("utf-8")
    )
    assert source_manifest["mode"] == "LIVE" and source_manifest["fresh_record_count"] == len(rows)
    source_rows = json.loads(
        (env.data / "runs" / STORE / source.id / "exports" / "record_map.json").read_text("utf-8")
    )["rows"]
    assert {(r["observation_kind"], r["observed_by_run"]) for r in source_rows} == {("fresh", source.id)}
    assert all("read_again_by_run" not in r for r in source_rows)


def test_a_replays_supporting_log_names_the_run_that_read_each_product_page(env: Env) -> None:  # noqa: F811
    # Release 1.3.1 (df6fb7c) relabelled a replay's rows, but its supporting log still counted their UPC
    # outcomes as "upc_outcomes_of_fresh_exported" and marked each product page it read again from storage
    # "fresh", as if the replay had requested it. Found in the offline reprocessing of the 2026-10-26 Azure
    # run 01M5X364ZR83MZ9M60QGPFR7TX.
    assert env.result("run", "--store", STORE)[0] == 0
    [source] = env.runs()
    assert env.result("replay", "--run", source.id)[0] == 0
    replay = next(r for r in env.runs() if r.id != source.id)

    def log_of(run_id: str) -> dict[str, Any]:
        path = env.data / "runs" / STORE / run_id / "exports" / "provenance.json"
        return cast(dict[str, Any], json.loads(path.read_text("utf-8")))

    log = log_of(replay.id)
    exported = [v for v in log["records"].values() if v["exported"]]
    assert "upc_outcomes_of_fresh_exported" not in log["counts"]
    assert sum(log["counts"]["upc_outcomes_of_replayed_exported"].values()) == len(exported)
    details = [v["upc_detail"] for v in log["records"].values() if v["upc_detail"]]
    assert details and all("fresh" not in d for d in details)
    # A product page the source run requested names that run, at its own time, and the replay that read it.
    read = [d for d in details if d.get("page_fetch_id")]
    assert read and {(d["observed_by_run"], d["read_again_by_run"]) for d in read} == {(source.id, replay.id)}
    source_log = log_of(source.id)
    by_item = {d["item_id"]: d for d in (v["upc_detail"] for v in source_log["records"].values()) if d}
    assert all(d["requested_at"] == by_item[d["item_id"]]["requested_at"] for d in read)
    # The source run's own log keeps its labels: it requested those pages.
    assert "upc_outcomes_of_fresh_exported" in source_log["counts"]
    assert all(by_item[d["item_id"]]["fresh"] is True for d in read)
    assert all("read_again_by_run" not in d for d in by_item.values())
    # The same in the run's log: each product page's event (PRODUCT_DETAIL_READ) of the replay names the run
    # that requested the page and the replay, never "fresh" (the seventh offline reprocessing of 2026-10-27
    # found "fresh": true in 612 of the replay's events).
    with sessionmaker(env.engine, expire_on_commit=False)() as s:
        events = {
            run_id: [
                e.data
                for e in s.scalars(
                    select(Event).where(Event.run_id == run_id, Event.code == "PRODUCT_DETAIL_READ")
                )
            ]
            for run_id in (source.id, replay.id)
        }
    assert events[replay.id] and all("fresh" not in d for d in events[replay.id])
    read_events = [d for d in events[replay.id] if d.get("page_fetch_id")]
    assert {(d["observed_by_run"], d["read_again_by_run"]) for d in read_events} == {(source.id, replay.id)}
    assert all(d["fresh"] is True for d in events[source.id] if d.get("page_fetch_id"))
    assert all("read_again_by_run" not in d for d in events[source.id])


def test_a_run_is_replayed_once_and_only_live_runs_are_replayed(env: Env) -> None:  # noqa: F811
    assert env.result("run", "--store", STORE)[0] == 0
    [source] = env.runs()
    assert env.result("replay", "--run", source.id)[0] == 0
    replay = next(r for r in env.runs() if r.id != source.id)
    code, lines = env.cli("replay", "--run", source.id)
    assert code == 2 and "already replayed" in str(lines)
    code, lines = env.cli("replay", "--run", replay.id)
    assert code == 2 and "only LIVE runs are replayed" in str(lines)


def test_an_interrupted_replay_resumes_as_a_replay_and_requests_nothing(
    env: Env,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Release 1.5.2. Until 1.5.1 ``resume`` built the live collector for any run: a replay stopped part-way
    went on with live requests inside a REPLAY run, on whatever provider key the machine held."""
    assert env.result("run", "--store", STORE)[0] == 0
    [source] = env.runs()
    calls = len(env.mock.calls)
    with sessionmaker(env.engine, expire_on_commit=False)() as s:
        published = s.get(PublicationPointer, source.store_id)
        assert published is not None
        pointer = published.publication_id

    real = ReplaySession.navigate
    sent: list[str] = []

    async def stop_on_a_listing(self: ReplaySession, url: str, purpose: str, **kw: Any) -> Any:
        if purpose == "listing" and not sent:
            sent.append(url)
            signal.raise_signal(signal.SIGTERM)
        return await real(self, url, purpose, **kw)

    with monkeypatch.context() as m:
        m.setattr(ReplaySession, "navigate", stop_on_a_listing)
        code, _ = env.cli("replay", "--run", source.id)
    assert sent and code == 75, (sent, code)
    replay = next(r for r in env.runs() if r.id != source.id)
    assert replay.mode == "REPLAY" and replay.status == "interrupted"

    code, _ = env.result("resume", "--run", replay.id)
    assert code == 0
    assert len(env.mock.calls) == calls  # not one request, though the machine holds a provider key
    done = next(r for r in env.runs() if r.id == replay.id)
    assert done.mode == "REPLAY" and done.status in ("validated", "rejected")
    src_rows, rep_rows = _rows(env, source.id), _rows(env, replay.id)
    assert {k for k, r in rep_rows.items() if r.status != "historical"} == {
        k for k, r in src_rows.items() if r.status != "historical"
    }
    assert _observed(env, replay.id) == _observed(env, source.id)
    with sessionmaker(env.engine, expire_on_commit=False)() as s:
        after = s.get(PublicationPointer, source.store_id)
        assert after is not None and after.publication_id == pointer  # a replay is never published


def test_an_interrupted_replay_can_be_finalized_without_a_request(
    env: Env,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert env.result("run", "--store", STORE)[0] == 0
    [source] = env.runs()
    calls = len(env.mock.calls)
    real = ReplaySession.navigate
    sent: list[str] = []

    async def stop_on_a_listing(self: ReplaySession, url: str, purpose: str, **kw: Any) -> Any:
        if purpose == "listing" and not sent:
            sent.append(url)
            signal.raise_signal(signal.SIGTERM)
        return await real(self, url, purpose, **kw)

    with monkeypatch.context() as m:
        m.setattr(ReplaySession, "navigate", stop_on_a_listing)
        code, _ = env.cli("replay", "--run", source.id)
    assert sent and code == 75, (sent, code)
    replay = next(r for r in env.runs() if r.id != source.id)
    env.cli("finalize", "--run", replay.id)
    assert len(env.mock.calls) == calls
    done = next(r for r in env.runs() if r.id == replay.id)
    assert done.mode == "REPLAY" and done.status in ("validated", "rejected")


def test_a_later_live_run_carries_the_replayed_observations_forward(env: Env) -> None:  # noqa: F811
    assert env.result("run", "--store", STORE)[0] == 0
    [source] = env.runs()
    assert env.result("replay", "--run", source.id)[0] == 0
    replay = next(r for r in env.runs() if r.id != source.id)
    # A partial run of Diapering only: the Food products are carried forward from the replay, not the source.
    assert env.result("run", "--store", STORE, "--categories", "4")[0] == 0
    later = env.runs()[-1]
    carried = [r for r in _rows(env, later.id).values() if r.status == "historical"]
    assert carried
    assert all(r.provenance["historical"]["run_id"] == replay.id for r in carried)
    assert all(r.provenance["historical"]["replay_of"] == source.id for r in carried)
    with sessionmaker(env.engine, expire_on_commit=False)() as s:
        run = s.get(Run, later.id)
        assert run is not None and run.mode == "LIVE"


def test_a_row_carried_from_a_replay_names_the_live_run_that_fetched_its_page(
    env: Env,  # noqa: F811
    tmp_path: Path,
) -> None:
    # Release 1.5.2's agreement check over the campaign's replays found it. A row carried from a replay said
    # the replay had observed it, and that the replay had fetched its product page (fetched_detail, origin
    # "fetched", source_run the replay), though a replay requests nothing. Any run that carried such a row
    # said so, live or not.
    assert env.result("run", "--store", STORE)[0] == 0
    [source] = env.runs()
    assert env.result("replay", "--run", source.id)[0] == 0
    replay = next(r for r in env.runs() if r.id != source.id)
    assert env.result("run", "--store", STORE, "--categories", "4")[0] == 0
    later = env.runs()[-1]
    assert env.result("replay", "--run", later.id)[0] == 0
    second = next(r for r in env.runs() if r.id not in (source.id, replay.id, later.id))

    def exported(run_id: str) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
        out = tmp_path / run_id
        assert env.result("export", "--run", run_id, "--out", str(out))[0] == 0
        rows = json.loads((out / "field_dispositions.json").read_text("utf-8"))
        maps = json.loads((out / "record_map.json").read_text("utf-8"))["rows"]
        records = json.loads((out / "provenance.json").read_text("utf-8"))["records"]
        return (
            [r for r in rows if r["observation_kind"] == "carried_forward"],
            {m["key"]: m for m in maps},
            records,
        )

    source_map = exported(source.id)[1]
    revision = next(iter(source_map.values()))["code"]
    for run_id in (later.id, second.id):
        rows, maps, records = exported(run_id)
        assert rows
        for row in rows:
            key = row["key"]
            assert maps[key]["observed_by_run"] == source.id
            assert maps[key]["read_again_by_run"] == replay.id
            assert records[key]["historical"]["run_id"] == replay.id
            assert records[key]["historical"]["replay_of"] == source.id
        read = [r for r in rows if r["upc"].get("page_fetch_id")]
        assert read
        for row in read:
            field = row["upc"]
            assert field["disposition"] == "recovered_from_saved_detail"
            assert field["origin"] == "read_again"
            assert field["source_run"] == source.id
            assert field["source_revision"] == f"{revision['version']} {revision['commit']}".strip()
            assert field["observed_at"] == source_map[row["key"]]["upc"]["observed_at"]
            named = records[row["key"]]["fields"]["upc"]
            assert (named["source_run"], named["origin"]) == (source.id, "read_again")
            assert named["observed_at"] == field["observed_at"]
        listed = [r["weight"] for r in rows if r["weight"]["disposition"] == "present_in_listing"]
        assert listed and {w["source_run"] for w in listed} == {source.id}


def test_a_replay_leaves_the_stores_follow_up_queue_alone(env: Env) -> None:  # noqa: F811
    """Release 1.3.1: the follow-up queue is the store's live work; a replay requests nothing and neither
    notes nor reads it."""

    def queue() -> dict[tuple[str, str], tuple[object, ...]]:
        with sessionmaker(env.engine, expire_on_commit=False)() as s:
            return {
                (r.kind, r.item_id): (r.state, r.last_run, r.last_status, r.runs_seen, r.pages_read)
                for r in s.scalars(select(FollowUpItem))
            }

    # A Diapering listing with sponsored tiles and variants. Since release 1.5.0 a product with a blank field
    # is queued as well (kind "detail"). This site refuses their product pages, and three refusals in a row
    # reject the run and its replay (G2 DETAIL_PAUSED), so a page budget of 1 leaves them queued unread.
    site({"mock": env.mock}, TILES, PRODUCTS)
    env.result("run", "--store", STORE, "--pilot-detail-pages", "1")
    [source] = env.runs()
    before = queue()
    assert {k for k, _ in before} == {"sponsored", "variant", "detail"}
    calls = len(env.mock.calls)
    assert env.result("replay", "--run", source.id)[0] == 0
    assert len(env.mock.calls) == calls
    assert queue() == before
