"""Release 1.6.0, the client's clarification: Walmart's four deal fields are ALWAYS empty strings.

Each test starts from pages that DISPLAY multi-unit and coupon offers (SYNTHETIC tiles through the Scrape.do
mock, tests/mock_scrapedo.py; nothing reaches Scrape.do or Walmart) and proves the final files hold "" in the
four fields, with exactly the 22 string fields in order: the fresh rows (products and products_fresh, JSON
and CSV), a carried row of an earlier release that held deal values (its values kept as lineage only), an
offline replay and its export, the store's published dataset and the ``export`` command's copy. The offers
themselves stay as evidence in offers.json and the provenance. The exporters refuse a row that breaks the rule
(tests/unit/test_exports_policy.py)."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from tests import synthetic_walmart as syn
from tests.integration.test_followups import CAT, product_page
from tests.integration.test_operations import Env, env  # noqa: F401  (the CLI fixture)
from tests.mock_scrapedo import DIAPERING, listing
from walmart_headless.core.schema import DEAL_FIELDS, OUTPUT_FIELDS, ordered_record
from walmart_headless.db.models import RecordRow
from walmart_headless.publishing.exports import record_sha256

pytestmark = [pytest.mark.postgres]

STORE = "walmart-3891-pickup"
OFFERS = (
    ("ROLLBACK", "Rollback"),
    ("MULTI", "2 for $5.00"),
    ("CPN", "Clip coupon: $3.99"),
    ("CASH", "Earn $2 Walmart Cash"),
)
DEAL_TILES = [
    syn.Item("9001", "Diapers A, Size 1, 84 Count", "$9.97", unit="11.9 ¢/ea", badges=OFFERS),
    syn.Item("9002", "Wipes B, 3 Pack", "$5.97", badges=(("MULTI", "3 for $15.00"),)),
    syn.Item("9003", "Diapers C, Size 4, 60 Count", "$10.97", was="$12.97", badges=(("CPN", "Save $1.00"),)),
]

UPCS = {"9001": "036000451293", "9002": "000123456789", "9003": "078742000000"}


def serve_tiles(e: Env, tiles: list[syn.Item]) -> None:
    organic = len({t.item_id for t in tiles})

    def override(url: str) -> httpx.Response | None:
        u = urlsplit(url)
        headers = {"Scrape.do-Request-Cost": "10", "Scrape.do-Walmart-Store-Id": "3891"}
        if f"{u.scheme}://{u.netloc}{u.path}" == DIAPERING:
            n = int(parse_qs(u.query).get("page", ["1"])[0])
            html = listing(tiles if n == 1 else [], page=n, max_page=1, total=organic, cat=CAT)
            return httpx.Response(200, text=html, headers=headers)
        if u.path.startswith("/ip/"):
            item = u.path.rstrip("/").rsplit("/", 1)[-1]
            tile = next((t for t in tiles if t.item_id == item), None)
            if tile is None:
                return httpx.Response(404, text="not found", headers=headers)
            return httpx.Response(200, text=product_page(tile, upc=UPCS[item]), headers=headers)
        return None

    e.mock.page_override = override


def products_files(exports: Path) -> dict[str, list[dict[str, str]]]:
    """Every products file of an export folder, each row checked: 22 string fields in order, deals empty."""
    out: dict[str, list[dict[str, str]]] = {}
    for name in ("products.json", "products_fresh.json"):
        if not (exports / name).is_file():
            continue
        rows = json.loads((exports / name).read_text("utf-8"))
        for r in rows:
            assert list(r) == list(OUTPUT_FIELDS), name
            assert all(isinstance(v, str) for v in r.values()), name
            assert [r[f] for f in DEAL_FIELDS] == ["", "", "", ""], (name, r["url"])
        out[name] = rows
    for name in ("products.csv", "products_fresh.csv"):
        if not (exports / name).is_file():
            continue
        table = list(csv.reader(io.StringIO((exports / name).read_bytes().decode("utf-8-sig"))))
        assert table[0] == list(OUTPUT_FIELDS), name
        rows = [dict(zip(table[0], line, strict=True)) for line in table[1:]]
        assert all(r[f] == "" for r in rows for f in DEAL_FIELDS), name
        out[name] = rows
    # The JSON and CSV forms hold the same rows.
    for stem in ("products", "products_fresh"):
        if f"{stem}.json" in out:
            assert out[f"{stem}.json"] == out[f"{stem}.csv"]
    return out


def exports_of(e: Env, run_id: str) -> Path:
    return e.data / "runs" / STORE / run_id / "exports"


def test_fresh_rows_never_carry_a_deal_value_and_the_offers_stay_as_evidence(env: Env) -> None:  # noqa: F811
    serve_tiles(env, DEAL_TILES)
    env.edit(categories=[4])  # the configured scope: a complete run, published (narrowing makes a pilot)
    assert env.result("run", "--store", STORE)[0] == 0
    [run] = env.runs()
    assert run.status == "published"
    files = products_files(exports_of(env, run.id))
    fresh = {r["url"].rsplit("/", 1)[-1]: r for r in files["products_fresh.json"]}
    assert {"9001", "9002", "9003"} <= set(fresh)
    assert fresh["9003"]["sale_price"] == "10.97" and fresh["9003"]["regular_price"] == "12.97"  # own rules
    offers = json.loads((exports_of(env, run.id) / "offers.json").read_text("utf-8"))
    texts = {o["text"] for o in offers}
    assert {"2 for $5.00", "3 for $15.00"} <= texts  # the displayed offers, kept as evidence
    log = json.loads((exports_of(env, run.id) / "provenance.json").read_text("utf-8"))
    kept = [v for v in log["records"].values() if "_deal_fields_not_exported" in json.dumps(v)]
    assert kept, "the offers the 1.5.x rules would have exported are kept in the provenance"
    # The store's published dataset (the pointer names this run's manifest) and the export command's copy.
    latest = json.loads((env.data / "published" / STORE / "latest.json").read_text("utf-8"))
    assert latest["run_id"] == run.id
    products_files(exports_of(env, run.id))
    out = env.data.parent / "exported"
    code, res = env.result("export", "--store", STORE, "--out", str(out))  # the published dataset
    assert code == 0 and res["run_id"] == run.id
    assert products_files(out)["products.json"] == files["products.json"]


def test_a_carried_row_of_an_earlier_release_is_exported_without_its_deal_values(env: Env) -> None:  # noqa: F811
    serve_tiles(env, DEAL_TILES)
    assert env.result("run", "--store", STORE, "--categories", "4")[0] == 0
    [first] = env.runs()
    # As release 1.5.2 stored it: the same row with deal values (and its own consistent hash).
    with sessionmaker(env.engine, expire_on_commit=False)() as s:
        row = s.scalars(
            select(RecordRow).where(
                RecordRow.run_id == first.id, RecordRow.record["url"].astext.like("%/9002")
            )
        ).one()
        legacy = {
            **ordered_record(row.record),
            "volume_deals_description": "3 for $15.00",
            "volume_deals_price": "15.00",
        }
        row.record = legacy
        row.record_sha256 = record_sha256(ordered_record(legacy))
        legacy_sha = row.record_sha256
        s.commit()
    serve_tiles(env, [t for t in DEAL_TILES if t.item_id != "9002"])  # 9002 is not observed again
    assert env.result("run", "--store", STORE, "--categories", "4")[0] == 0
    second = next(r for r in env.runs() if r.id != first.id)
    files = products_files(exports_of(env, second.id))
    carried = next(r for r in files["products.json"] if r["url"].endswith("/9002"))
    assert carried["regular_price"] == "5.97" and carried["crawl_date"]  # its own observation, unchanged
    assert all(not r["url"].endswith("/9002") for r in files["products_fresh.json"])  # carried, not fresh
    with sessionmaker(env.engine, expire_on_commit=False)() as s:
        crow = s.scalars(
            select(RecordRow).where(
                RecordRow.run_id == second.id, RecordRow.record["url"].astext.like("%/9002")
            )
        ).one()
    hist = crow.provenance["historical"]
    assert hist["run_id"] == first.id
    assert hist["withheld_by_policy"]["fields"] == {
        "volume_deals_description": "3 for $15.00",
        "volume_deals_price": "15.00",
    }
    assert hist["withheld_by_policy"]["source_record_sha256"] == legacy_sha
    assert crow.record_sha256 == record_sha256(ordered_record(crow.record))


def test_a_replay_and_its_export_keep_the_deal_fields_empty(env: Env) -> None:  # noqa: F811
    serve_tiles(env, DEAL_TILES)
    assert env.result("run", "--store", STORE, "--categories", "4")[0] == 0
    [source] = env.runs()
    calls = len(env.mock.calls)
    assert env.result("replay", "--run", source.id)[0] == 0
    assert len(env.mock.calls) == calls  # offline
    replay = next(r for r in env.runs() if r.id != source.id)
    rows = products_files(exports_of(env, replay.id))["products_fresh.json"]
    assert {r["url"].rsplit("/", 1)[-1] for r in rows} >= {"9001", "9002", "9003"}
    out = env.data.parent / "replay_export"
    assert env.result("export", "--run", replay.id, "--out", str(out))[0] == 0
    products_files(out)


def test_the_export_contract_check_reports_a_deal_value(tmp_path: Path) -> None:
    from walmart_headless.checks.contract import check

    row: dict[str, Any] = {f: "" for f in OUTPUT_FIELDS}
    row.update(url="https://www.walmart.com/ip/x/9001", crawl_date="2026-11-03", regular_price="1.00")
    good, bad = tmp_path / "good.json", tmp_path / "bad.json"
    good.write_text(json.dumps([row]), "utf-8")
    bad.write_text(json.dumps([{**row, "digital_deals_description": "Clip coupon"}]), "utf-8")
    assert check(good)["passed"] is True
    res = check(bad)
    assert res["passed"] is False
    assert res["problems"] == {"a deal field not empty (client rule: always empty for Walmart)": 1}
