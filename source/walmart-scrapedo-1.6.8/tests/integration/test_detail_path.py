"""Release 1.5.0: a product's own page for a missing UPC or size, through the run pipeline against the mock of
Scrape.do. Every page here is SYNTHETIC. Nothing reaches Scrape.do or Walmart.

Before 1.5.0 a product whose result page stated a UPC never had its page read for a missing size, so its size
stayed empty with no outcome at all; an earlier read counted by the record key, not the item; a page budget
always spent itself on the same first products; and a blank field said nothing about why it was blank."""

from __future__ import annotations

import gzip
import json
from datetime import timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx
import pytest
from sqlalchemy import select

from tests import mock_scrapedo as mock
from tests import synthetic_walmart as syn
from tests.conftest import STORE_KEY
from tests.integration.test_scrapedo_walmart import _detail_calls, _records, _run, env  # noqa: F401
from walmart_headless.collection import detail_captures, follow_queue
from walmart_headless.collection.config import DetailConfig, Limits
from walmart_headless.collection.walmart import WalmartCollector
from walmart_headless.core.schema import ordered_record
from walmart_headless.core.timeutil import iso, utcnow
from walmart_headless.db.models import DetailObservation, FollowUpItem, RecordRow, Run, Store
from walmart_headless.publishing import dispositions as disp
from walmart_headless.publishing.exports import record_sha256

pytestmark = [pytest.mark.postgres]

PINNED_UPC = "078742371245"


def product_page(
    item: str,
    *,
    upc: str | None = None,
    specs: dict[str, str] | None = None,
    variants: dict[str, list[tuple[str, bool]]] | None = None,
    unit_price: str = "",
    serving: str = "",
) -> str:
    """A SYNTHETIC product page with the page data the size reader reads."""
    product: dict[str, Any] = {
        "usItemId": item,
        "name": f"Synthetic item {item}",
        "variantCriteria": [
            {"id": cid, "variantList": [{"id": n, "name": n, "selected": sel} for n, sel in options]}
            for cid, options in (variants or {}).items()
        ],
    }
    if upc:
        product["upc"] = upc
    if unit_price:
        product["priceInfo"] = {"unitPrice": {"priceString": unit_price}}
    idml: dict[str, Any] = {"specifications": [{"name": k, "value": v} for k, v in (specs or {}).items()]}
    if serving:
        idml["nutritionFacts"] = {"servingInfo": {"values": [{"value": serving}]}}
    data = {"props": {"pageProps": {"initialData": {"data": {"product": product, "idml": idml}}}}}
    return f"<!doctype html><html><body>{syn.next_data_script(data)}</body></html>"


def pages(by_item: dict[str, str]) -> Any:
    def answer(url: str) -> httpx.Response | None:
        if "/ip/" not in url:
            return None
        item = urlsplit(url).path.rstrip("/").rsplit("/", 1)[-1]
        return httpx.Response(200, text=by_item[item]) if item in by_item else None

    return answer


def one_product(monkeypatch: pytest.MonkeyPatch, item: syn.Item) -> None:
    """Only one product in the run: one listing page holding it, the other listings empty of products."""
    monkeypatch.setitem(mock.PAGES, mock.MILK, [[item]])
    monkeypatch.setitem(mock.PAGES, mock.SNACKS, [[]])
    monkeypatch.setitem(mock.PAGES, mock.DIAPERING, [[]])


def exports(e: dict[str, Any], run_id: str) -> Path:
    return e["storage"].root / "runs" / STORE_KEY / run_id / "exports"


def field_rows(e: dict[str, Any], run_id: str) -> dict[str, dict[str, Any]]:
    rows = json.loads((exports(e, run_id) / "field_dispositions.json").read_text("utf-8"))
    return {r["key"]: r for r in rows}


def test_a_listing_upc_with_no_size_has_its_page_read_for_the_size_only(
    env: dict[str, Any],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Before 1.5.0 this product's page was never read: the size stayed empty with no outcome."""
    one_product(monkeypatch, syn.Item("7101", "Whole Milk", "$3.12", upc=PINNED_UPC))
    env["mock"].page_override = pages(
        {"7101": product_page("7101", upc=PINNED_UPC, specs={"Size": "1 Gallon", "Serving size": "1 cup"})}
    )
    run_id, status = _run(env)
    assert status == "validated"
    rec = _records(env, run_id)[PINNED_UPC]
    assert rec.record["upc"] == PINNED_UPC and rec.record["weight"] == "1 Gallon"
    d = rec.provenance["upc_detail"]
    assert (
        d["listing_upc"] is True and d["size_filled"] is True and d["weight_observed_at"] == d["requested_at"]
    )
    assert d["size"]["outcome"] == "single_statement"
    assert d["size"]["path"].endswith(".idml.specifications[0].value")
    products = json.loads((exports(env, run_id) / "products.json").read_text("utf-8"))
    assert [p["weight"] for p in products] == ["1 Gallon"]
    row = field_rows(env, run_id)[PINNED_UPC]
    assert row["observation_kind"] == "fresh"
    assert row["upc"]["disposition"] == disp.PRESENT and row["upc"]["source_run"] == run_id
    assert row["weight"]["disposition"] == disp.FETCHED and row["weight"]["value"] == "1 Gallon"
    assert row["weight"]["observed_at"] == d["requested_at"] and row["weight"]["source_run"] == run_id
    with env["factory"]() as s:
        run = s.get(Run, run_id)
        assert run is not None
        assert run.counts["field_dispositions"] == {"upc": {disp.PRESENT: 1}, "weight": {disp.FETCHED: 1}}
    table = (exports(env, run_id) / "field_dispositions.csv").read_text("utf-8-sig").splitlines()
    assert table[0].split(",")[:2] == ["key", "observation_kind"]
    assert len(table) == 2 and disp.FETCHED in table[1]


def test_a_page_never_replaces_a_stated_upc_and_a_disagreement_is_flagged(
    env: dict[str, Any],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    one_product(monkeypatch, syn.Item("7101", "Whole Milk", "$3.12", upc=PINNED_UPC))
    env["mock"].page_override = pages({"7101": product_page("7101", upc="028400090896")})
    run_id, _ = _run(env)
    rec = _records(env, run_id)[PINNED_UPC]
    assert rec.record["upc"] == PINNED_UPC and "UPC_SOURCE_MISMATCH" in rec.flags
    row = field_rows(env, run_id)[PINNED_UPC]
    assert row["upc"]["disposition"] == disp.PRESENT and "028400090896" in row["upc"]["conflicts"][0]
    assert row["weight"]["disposition"] == disp.ABSENT


def test_sizes_that_disagree_are_all_kept_flagged_and_none_is_chosen(
    env: dict[str, Any],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    one_product(monkeypatch, syn.Item("7101", "Whole Milk", "$3.12"))
    env["mock"].page_override = pages(
        {"7101": product_page("7101", specs={"Size": "12 oz", "Net content statement": "16 oz"})}
    )
    run_id, status = _run(env)
    assert status == "validated"
    rec = _records(env, run_id)["wm:7101"]
    assert rec.record["weight"] == "" and "SIZE_CONFLICT" in rec.flags
    row = field_rows(env, run_id)["wm:7101"]["weight"]
    assert row["disposition"] == disp.CONFLICT and "'12 oz'" in row["conflicts"][0]
    kept = rec.provenance["upc_detail"]["size"]["observations"]
    assert {o["value"] for o in kept} == {"12 oz", "16 oz"}
    with env["factory"]() as s:
        [saved] = s.scalars(select(DetailObservation).where(DetailObservation.item_id == "7101"))
        assert {o["value"] for o in saved.size_statements} == {"12 oz", "16 oz"}


def test_a_title_size_stays_and_a_page_that_disagrees_with_it_is_flagged(
    env: dict[str, Any],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The shape of real item 49986668: the title says 66 loads, its page 88."""
    one_product(monkeypatch, syn.Item("7101", "Detergent, 141 oz, 66 Loads", "$3.12"))
    env["mock"].page_override = pages({"7101": product_page("7101", specs={"Number of loads": "88"})})
    run_id, _ = _run(env)
    rec = _records(env, run_id)["wm:7101"]
    assert rec.record["weight"] == "141 oz, 66 Loads" and "SIZE_CONFLICT" in rec.flags
    row = field_rows(env, run_id)["wm:7101"]["weight"]
    assert row["disposition"] == disp.PRESENT and row["value"] == "141 oz, 66 Loads" and row["conflicts"]


def test_serving_size_unit_price_and_sibling_variants_never_fill_a_size(
    env: dict[str, Any],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    one_product(monkeypatch, syn.Item("7101", "Whole Milk", "$3.12"))
    env["mock"].page_override = pages(
        {
            "7101": product_page(
                "7101",
                serving="8 fl oz",
                unit_price="2.4 ¢/fl oz",
                variants={"size": [("1 gal", False), ("0.5 gal", False)]},
                specs={"Weight": "8.6 lb", "Serving size": "1 cup"},
            )
        }
    )
    run_id, _ = _run(env)
    rec = _records(env, run_id)["wm:7101"]
    assert rec.record["weight"] == "" and "SIZE_CONFLICT" not in rec.flags
    row = field_rows(env, run_id)["wm:7101"]["weight"]
    assert row["disposition"] == disp.ABSENT and row["observed_at"]


def test_approximate_wording_on_the_page_excludes_the_whole_product(
    env: dict[str, Any],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    one_product(monkeypatch, syn.Item("7101", "Sweet Potato", "$3.12"))
    env["mock"].page_override = pages({"7101": product_page("7101", specs={"Size": "3 lb approx"})})
    run_id, _ = _run(env)
    rec = _records(env, run_id)["wm:7101"]
    assert rec.status == "excluded" and "APPROX_WEIGHT" in rec.reasons
    assert rec.provenance["upc_detail"]["approx_weight"]["text"]


def test_a_saved_read_is_reused_with_its_own_time_run_and_revision_for_both_fields(
    env: dict[str, Any],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    one_product(monkeypatch, syn.Item("7101", "Whole Milk", "$3.12"))
    env["mock"].page_override = pages(
        {"7101": product_page("7101", upc=PINNED_UPC, specs={"Size": "1 Gallon"})}
    )
    first, _ = _run(env)
    read_at = _records(env, first)["wm:7101"].provenance["upc_detail"]["requested_at"]
    env["mock"].calls.clear()
    second, _ = _run(env)
    assert _detail_calls(env) == []  # no page is requested again
    rec = _records(env, second)["wm:7101"]
    assert rec.record["upc"] == PINNED_UPC and rec.record["weight"] == "1 Gallon"
    d = rec.provenance["upc_detail"]
    assert d["fresh"] is False and d["reused_from"]["run_id"] == first
    assert d["upc_observed_at"] == read_at and d["weight_observed_at"] == read_at
    row = field_rows(env, second)["wm:7101"]
    for field in ("upc", "weight"):
        assert row[field]["disposition"] == disp.RECOVERED
        assert row[field]["observed_at"] == read_at and row[field]["source_run"] == first
        assert row[field]["origin"] == "fetched"
        assert row[field]["source_revision"]


def _evidence_of(e: dict[str, Any], run_id: str, key: str) -> dict[str, dict[str, Any]]:
    """The same product in the three evidence files of a run."""
    root = exports(e, run_id)
    prov = json.loads((root / "provenance.json").read_text("utf-8"))["records"][key]
    rows = json.loads((root / "record_map.json").read_text("utf-8"))["rows"]
    return {
        "provenance": prov,
        "record_map": next(r for r in rows if r["key"] == key),
        "field_dispositions": field_rows(e, run_id)[key],
    }


def test_all_evidence_files_name_the_read_a_reused_value_comes_from(
    env: dict[str, Any],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Release 1.5.2, the defect of 1.5.1's S6 (item 10402650): ``provenance.json`` named the tile's title
    for a size recovered from a saved page, with ``missing.weight`` still set and no UPC source at all."""
    one_product(monkeypatch, syn.Item("7101", "Whole Milk", "$3.12"))
    env["mock"].page_override = pages(
        {"7101": product_page("7101", upc=PINNED_UPC, specs={"Size": "1 Gallon"})}
    )
    first, _ = _run(env)
    read = _records(env, first)["wm:7101"].provenance["upc_detail"]
    second, _ = _run(env)
    files = _evidence_of(env, second, "wm:7101")
    prov, mapped, row = files["provenance"], files["record_map"], files["field_dispositions"]
    for field, place in (
        ("upc", "props.pageProps.initialData.data.product.upc"),
        ("weight", "props.pageProps.initialData.data.idml.specifications[0].value"),
    ):
        src = prov["fields"][field]
        assert src == mapped["fields"][field] or src.keys() == mapped["fields"][field].keys()
        assert src["source"] == disp.SOURCE_OWN_PAGE
        assert src["fetch_id"] == read["page_fetch_id"] == row[field]["page_fetch_id"]
        assert src["observed_at"] == read["requested_at"] == row[field]["observed_at"]
        assert src["source_run"] == first == row[field]["source_run"]
        assert src["source_revision"] == row[field]["source_revision"] and src["source_revision"]
        assert src["item_id"] == "7101" == row["item_id"] == prov["upc_detail"]["item_id"]
        assert src["selector_or_path"].startswith(place) and row[field]["path"] == place
        assert field not in prov["missing"] and field not in prov["missing_kind"]
    assert prov["fields"]["upc"]["body_sha256"] == read["body_sha256"] == row["upc"]["body_sha256"]
    assert mapped["upc"]["page_fetch_id"] == read["page_fetch_id"]


def test_each_field_source_names_the_hash_of_its_stored_page(env: dict[str, Any]) -> None:  # noqa: F811
    """``response_sha256`` was empty on every field until 1.5.1, the page's hash only in ``record_map``."""
    run_id, _ = _run(env)
    root = exports(env, run_id)
    rows = json.loads((root / "record_map.json").read_text("utf-8"))["rows"]
    records = json.loads((root / "provenance.json").read_text("utf-8"))["records"]
    assert rows
    for row in rows:
        page = row["page"]
        for fields in (row["fields"], records[row["key"]]["fields"]):
            tile = [f for f in fields.values() if f.get("fetch_id") == page["page_fetch_id"]]
            assert tile and all(f["response_sha256"] == page["stored_page_sha256"] for f in tile)
            unhashed = {k: v for k, v in fields.items() if v.get("fetch_id") and not v["response_sha256"]}
            assert not unhashed, unhashed


def test_a_page_nobody_requested_is_never_called_absent_in_any_evidence_file(
    env: dict[str, Any],  # noqa: F811
) -> None:
    """Until 1.5.1 ``missing_kind.upc`` read ``source_absent`` on the 226 products of S6 whose page was not
    requested, while ``field_dispositions.json`` said not attempted."""
    run_id, _ = _run(env, detail=DetailConfig(enabled=False))
    records = json.loads((exports(env, run_id) / "provenance.json").read_text("utf-8"))["records"]
    exported = [r for r in records.values() if r["exported"]]
    assert exported
    for record in exported:
        assert record["missing_kind"]["upc"] == disp.NOT_ATTEMPTED
        assert "product detail reading is off" in record["missing"]["upc"]


def test_a_carried_row_names_the_sources_of_its_own_earlier_run(
    env: dict[str, Any],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A carried row showed no sources at all in ``provenance.json`` until 1.5.1."""
    one_product(monkeypatch, syn.Item("7101", "Whole Milk", "$3.12"))
    env["mock"].page_override = pages(
        {"7101": product_page("7101", upc=PINNED_UPC, specs={"Size": "1 Gallon"})}
    )
    first, _ = _run(env)
    monkeypatch.setitem(
        mock.PAGES, mock.MILK, [[syn.Item("7201", "Skim Milk, 1 gal", "$3.00", upc="028400090896")]]
    )
    second, _ = _run(env)
    files = _evidence_of(env, second, "wm:7101")
    prov = files["provenance"]
    assert prov["observation_kind"] == "carried_forward"
    assert prov["historical"]["run_id"] == first
    assert prov["fields"]["upc"]["source"] == disp.SOURCE_OWN_PAGE
    assert prov["fields"]["upc"]["source_run"] == first
    assert prov["fields"]["url"]["fetch_id"] == files["record_map"]["page"]["page_fetch_id"]
    assert prov["fields"]["url"]["response_sha256"] == files["record_map"]["page"]["stored_page_sha256"]
    assert "upc" not in prov["missing"]


def test_a_source_that_states_nothing_is_not_asked_again_and_says_when_it_was_inspected(
    env: dict[str, Any],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    one_product(monkeypatch, syn.Item("7101", "Whole Milk", "$3.12"))
    env["mock"].page_override = pages({"7101": product_page("7101")})
    first, _ = _run(env)
    read_at = _records(env, first)["wm:7101"].provenance["upc_detail"]["requested_at"]
    env["mock"].calls.clear()
    second, _ = _run(env)
    assert _detail_calls(env) == []
    row = field_rows(env, second)["wm:7101"]
    assert row["upc"]["disposition"] == disp.ABSENT and row["upc"]["observed_at"] == read_at
    assert row["weight"]["disposition"] == disp.ABSENT and row["weight"]["source_run"] == first


def test_a_page_budget_does_not_read_the_same_first_products_run_after_run(
    env: dict[str, Any],  # noqa: F811
) -> None:
    """Before 1.5.0 a budget took the lowest record ids each time, with no memory: with no reuse window, the
    first products were read in every run and the last never. The store's queue reads the never-read first."""
    read: list[list[str]] = []
    for _ in range(4):
        env["mock"].calls.clear()
        run_id, _status = _run(env, detail=DetailConfig(max_per_run=1, reuse_days=0))
        read.append([item for _, item in _detail_calls(env)])
        rows = field_rows(env, run_id)
        limited = [r for r in rows.values() if r["upc"]["disposition"] == disp.INTERRUPTED]
        assert len(limited) == 3 and all("detail limit (1 pages)" in r["upc"]["reason"] for r in limited)
    assert [len(r) for r in read] == [1, 1, 1, 1]
    assert sorted(i for r in read for i in r) == ["7101", "7201", "7203", "7301"]
    with env["factory"]() as s:
        queued = list(s.scalars(select(FollowUpItem).where(FollowUpItem.kind == "detail")))
    assert sorted(q.item_id for q in queued) == ["7101", "7201", "7203", "7301"]  # no duplicates
    assert all(q.pages_read == 1 and q.runs_seen == 4 for q in queued)
    # With no reuse window, what the last run did not read is still owed: one resolved, three waiting.
    assert sorted(q.state for q in queued) == ["pending", "pending", "pending", "resolved"]


def test_a_page_budget_never_stops_what_earlier_reads_already_established(
    env: dict[str, Any],  # noqa: F811
) -> None:
    """Release 1.5.1. The never-read products come first in the queue, so until 1.5.0 a spent budget ended the
    loop before the products whose page was already saved: they stayed blank at no saving of any request.
    The live campaign's repeat of 2026-10-31 showed it: the same product blank in one run and filled in the
    next. With one page never read behind the budget, a second pass of the loop hid this, so two are left."""
    first, _ = _run(env, detail=DetailConfig(max_per_run=1))
    read_first = {item for _, item in _detail_calls(env)}
    assert len(read_first) == 1
    env["mock"].calls.clear()
    second, _ = _run(env, detail=DetailConfig(max_per_run=1))
    read_second = [item for _, item in _detail_calls(env)]
    assert len(read_second) == 1 and read_second[0] not in read_first  # still goes to a never-read one
    rows = field_rows(env, second)
    by_disposition: dict[str, set[str]] = {}
    for key, row in rows.items():
        by_disposition.setdefault(row["upc"]["disposition"], set()).add(key.removeprefix("wm:"))
    assert by_disposition[disp.RECOVERED] == read_first  # no request, and each names the run that read it
    assert by_disposition[disp.FETCHED] == set(read_second)
    assert len(by_disposition[disp.INTERRUPTED]) == 2  # the page limit still says what it left unread
    assert all(rows[f"wm:{i}"]["upc"]["source_run"] == first for i in read_first)
    left = by_disposition[disp.INTERRUPTED]
    assert all("detail limit (1 pages)" in rows[f"wm:{i}"]["upc"]["reason"] for i in left)


def test_a_run_that_ends_before_its_detail_pass_still_uses_what_earlier_reads_established(
    env: dict[str, Any],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Release 1.6.1. Saved reads were used only by the detail pass, so a run that ended before it (a stop, a
    deadline, a credit limit) exported its products blank, "the run stopped before this product's page was
    read", although an earlier read answered for them at no request: the live S7 of 2026-10-31 (release 1.5.1)
    left 32 products blank that S6's saved reads answered for, and later runs carried them blank. The assembly
    now gives each one that read, as the pass would have; a product no earlier read answers for still says why
    it is blank."""
    milk = syn.Item("7101", "Whole Milk", "$3.12")
    one_product(monkeypatch, milk)
    env["mock"].page_override = pages(
        {"7101": product_page("7101", upc=PINNED_UPC, specs={"Size": "1 Gallon"})}
    )
    first, _ = _run(env)
    read_at = _records(env, first)["wm:7101"].provenance["upc_detail"]["requested_at"]
    monkeypatch.setitem(mock.PAGES, mock.MILK, [[milk, syn.Item("7102", "Oat Milk", "$4.10")]])

    async def never(self: WalmartCollector, ctx: Any, **_kw: Any) -> None:
        return None  # the run ends before its detail pass

    monkeypatch.setattr(WalmartCollector, "read_details", never)
    env["mock"].calls.clear()
    second, _ = _run(env)
    assert _detail_calls(env) == []  # nothing is requested for it
    rec = _records(env, second)["wm:7101"]
    assert rec.record["upc"] == PINNED_UPC and rec.record["weight"] == "1 Gallon"
    d = rec.provenance["upc_detail"]
    assert d["fresh"] is False and d["reused_from"]["run_id"] == first
    rows = field_rows(env, second)
    for field in ("upc", "weight"):
        assert rows["wm:7101"][field]["disposition"] == disp.RECOVERED
        assert rows["wm:7101"][field]["source_run"] == first
        assert rows["wm:7101"][field]["observed_at"] == read_at
    assert rows["wm:7102"]["upc"]["disposition"] == disp.INTERRUPTED
    assert rows["wm:7102"]["upc"]["reason"] == "the run stopped before this product's page was read"


def test_a_run_with_detail_reading_off_still_uses_what_earlier_reads_established(
    env: dict[str, Any],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Release 1.6.3. Product detail reading off (``detail.enabled: false``, ``--pilot-no-detail``: the census
    and the partition checks of 2026-11-03/04) turned reuse off too: such a run exported its products blank,
    "product detail reading is off", although a saved read answered for them at no request. Reading off turns
    off requests only; a product no earlier read answers for still says why it is blank."""
    milk = syn.Item("7101", "Whole Milk", "$3.12")
    one_product(monkeypatch, milk)
    env["mock"].page_override = pages(
        {"7101": product_page("7101", upc=PINNED_UPC, specs={"Size": "1 Gallon"})}
    )
    first, _ = _run(env)
    read_at = _records(env, first)["wm:7101"].provenance["upc_detail"]["requested_at"]
    monkeypatch.setitem(mock.PAGES, mock.MILK, [[milk, syn.Item("7102", "Oat Milk", "$4.10")]])
    env["mock"].calls.clear()
    second, _ = _run(env, detail=DetailConfig(enabled=False))
    assert _detail_calls(env) == []  # reading off: no product page is requested
    rec = _records(env, second)["wm:7101"]
    assert rec.record["upc"] == PINNED_UPC and rec.record["weight"] == "1 Gallon"
    d = rec.provenance["upc_detail"]
    assert d["fresh"] is False and d["reused_from"]["run_id"] == first
    rows = field_rows(env, second)
    for field in ("upc", "weight"):
        assert rows["wm:7101"][field]["disposition"] == disp.RECOVERED
        assert rows["wm:7101"][field]["source_run"] == first
        assert rows["wm:7101"][field]["observed_at"] == read_at
    assert rows["wm:7102"]["upc"]["disposition"] == disp.NOT_ATTEMPTED
    assert rows["wm:7102"]["upc"]["reason"] == "product detail reading is off"


def _carried_blank(
    e: dict[str, Any], monkeypatch: pytest.MonkeyPatch, *, later: list[syn.Item]
) -> tuple[str, str]:
    """A product whose own page a first run read (UPC and size), then observed again blank by a run that
    reused nothing (``reuse_days: 0``, as releases before 1.6.3 did with reading off); a third run's listing
    shows ``later`` instead, so it carries the product from the second run. Returns (first, second)."""
    one_product(monkeypatch, syn.Item("7101", "Whole Milk", "$3.12"))
    e["mock"].page_override = pages(
        {"7101": product_page("7101", upc=PINNED_UPC, specs={"Size": "1 Gallon"})}
    )
    first, _ = _run(e)
    second, _ = _run(e, detail=DetailConfig(enabled=False, reuse_days=0))
    blank = _records(e, second)["wm:7101"]
    assert blank.status == "valid" and blank.record["upc"] == "" and blank.record["weight"] == ""
    monkeypatch.setitem(mock.PAGES, mock.MILK, [later])
    return first, second


def test_a_carried_row_gets_its_empty_upc_and_size_from_a_saved_read_that_it_names(
    env: dict[str, Any],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Release 1.6.3. A carried row kept the empty fields of the run it came from, although a saved read of
    the item's own page answered for them at no request: the live L5 of 2026-11-04 (release 1.6.2) carried
    rows with a blank UPC that 1.5.1's S6 had read. The row now gets them, each naming that read (its time,
    run, revision and page); its listing observation (crawl date, prices, page) stays the earlier run's, and
    the record as it was carried keeps its hash."""
    first, second = _carried_blank(
        env, monkeypatch, later=[syn.Item("7201", "Skim Milk, 1 gal", "$3.00", upc="028400090896")]
    )
    read = _records(env, first)["wm:7101"].provenance["upc_detail"]
    blank = _records(env, second)["wm:7101"]
    env["mock"].calls.clear()
    third, _ = _run(env)
    assert "7101" not in [item for _, item in _detail_calls(env)]  # nothing is requested for it
    rec = _records(env, third)["wm:7101"]
    assert rec.status == "historical"
    hist = rec.provenance["historical"]
    assert hist["run_id"] == second
    assert rec.record["upc"] == PINNED_UPC and rec.record["weight"] == "1 Gallon"
    unchanged = {k: v for k, v in rec.record.items() if k not in ("upc", "weight")}
    assert unchanged == {k: v for k, v in blank.record.items() if k not in ("upc", "weight")}
    assert hist["record_as_carried_sha256"] == blank.record_sha256 != rec.record_sha256
    assert rec.record_sha256 == record_sha256(ordered_record(rec.record))
    for field, value in (("upc", PINNED_UPC), ("weight", "1 Gallon")):
        got = hist["recovered_fields"][field]
        assert got["value"] == value and got["run_id"] == first
        assert got["page_fetch_id"] == read["page_fetch_id"]
    d = rec.provenance["upc_detail"]
    assert d["fresh"] is False and d["reused_from"]["run_id"] == first
    assert d["for_carried_row"] == {"run_id": third, "earlier_run": second}
    files = _evidence_of(env, third, "wm:7101")
    row = files["field_dispositions"]
    assert row["observation_kind"] == "carried_forward"
    for field in ("upc", "weight"):
        assert row[field]["disposition"] == disp.RECOVERED
        assert row[field]["source_run"] == first and row[field]["page_fetch_id"] == read["page_fetch_id"]
        assert row[field]["source_revision"]  # the read's, or its run's when the read named none
        assert files["provenance"]["fields"][field]["source_run"] == first
        assert field not in files["provenance"]["missing"]
    assert files["record_map"]["upc"]["reused_from_run"] == first
    assert files["record_map"]["observed_by_run"] == second  # the listing observation stays the earlier run's
    with env["factory"]() as s:
        run = s.get(Run, third)
        assert run is not None
        assert run.counts["carried_details"]["upc_filled"] == 1
        assert run.counts["carried_details"]["weight_filled"] == 1
    products = json.loads((exports(env, third) / "products.json").read_text("utf-8"))
    assert [p["upc"] for p in products if p["url"].endswith("/7101")] == [PINNED_UPC]


def test_a_size_conflict_never_withholds_the_upc_the_same_read_verifies_for_a_carried_row(
    env: dict[str, Any],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Release 1.6.7 (the client's review of 1.6.6): 1.6.6 left a carried row's UPC blank when the saved read
    that states it also states sizes that conflict (``recovery_withheld``: 4 rows in L8, 12 in L10). The UPC
    and the size are separate values: the read's UPC is filled and names the read; the size stays blank,
    with the conflict as its reason and the read that said it."""
    one_product(monkeypatch, syn.Item("7101", "Whole Milk", "$3.12"))
    env["mock"].page_override = pages(
        {
            "7101": product_page(
                "7101", upc=PINNED_UPC, specs={"Size": "12 oz", "Net content statement": "16 oz"}
            )
        }
    )
    first, _ = _run(env)
    second, _ = _run(env, detail=DetailConfig(enabled=False, reuse_days=0))
    blank = _records(env, second)["wm:7101"]
    assert blank.record["upc"] == "" and blank.record["weight"] == ""
    monkeypatch.setitem(
        mock.PAGES, mock.MILK, [[syn.Item("7201", "Skim Milk, 1 gal", "$3.00", upc="028400090896")]]
    )
    env["mock"].calls.clear()
    third, _ = _run(env)
    assert "7101" not in [item for _, item in _detail_calls(env)]  # nothing is requested for it
    rec = _records(env, third)["wm:7101"]
    assert rec.status == "historical"
    hist = rec.provenance["historical"]
    assert rec.record["upc"] == PINNED_UPC, hist.get("recovery_withheld")
    assert rec.record["weight"] == ""
    assert "recovery_withheld" not in hist
    assert hist["recovered_fields"]["upc"]["run_id"] == first and "weight" not in hist["recovered_fields"]
    assert hist["size_withheld"]["reason"] == "the read's statements about size conflict"
    assert hist["size_withheld"]["read"]["run_id"] == first
    row = field_rows(env, third)["wm:7101"]
    assert row["upc"]["disposition"] == disp.RECOVERED and row["upc"]["source_run"] == first
    assert row["weight"]["disposition"] == disp.CONFLICT, row["weight"]
    with env["factory"]() as s:
        run = s.get(Run, third)
        assert run is not None
        assert run.counts["carried_details"]["upc_filled"] == 1
        assert run.counts["carried_details"]["weight_filled"] == 0
        assert run.counts["carried_details"]["size_withheld"] == 1
    products = json.loads((exports(env, third) / "products.json").read_text("utf-8"))
    assert [(p["upc"], p["weight"]) for p in products if p["url"].endswith("/7101")] == [(PINNED_UPC, "")]


def test_a_carried_row_never_takes_a_upc_another_exported_row_has(
    env: dict[str, Any],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Release 1.6.3: the saved read's UPC is the one a row of this run states (one product). A row of this
    run would be excluded as a duplicate; the carried row is left as it was carried, and says why."""
    first, second = _carried_blank(
        env, monkeypatch, later=[syn.Item("7301", "Whole Milk Again, 1 gal", "$3.12", upc=PINNED_UPC)]
    )
    blank = _records(env, second)["wm:7101"]
    third, _ = _run(env)
    rec = _records(env, third)["wm:7101"]
    assert rec.status == "historical" and rec.record == blank.record
    assert rec.record_sha256 == blank.record_sha256
    withheld = rec.provenance["historical"]["recovery_withheld"]
    assert PINNED_UPC in withheld["reason"] and "another exported row" in withheld["reason"]
    assert withheld["read"]["run_id"] == first
    assert "upc_detail" not in rec.provenance and "recovered_fields" not in rec.provenance["historical"]
    row = field_rows(env, third)["wm:7101"]
    assert row["upc"]["disposition"] == disp.NOT_ATTEMPTED  # the earlier run's outcome, unchanged
    with env["factory"]() as s:
        run = s.get(Run, third)
        assert run is not None and run.counts["carried_details"]["withheld"] == 1


def test_a_product_page_that_is_the_site_not_found_page_is_a_failed_request_never_a_parse_failure(
    env: dict[str, Any],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Release 1.6.3. Release 1.6.2 did not find the page data of Walmart's minified not-found page (its id
    unquoted) and recorded "parse_failed", "the page carries no Walmart page data"."""
    one_product(monkeypatch, syn.Item("7101", "Whole Milk", "$3.12"))
    env["mock"].page_override = pages({"7101": syn.not_found_page()})
    run_id, _ = _run(env)
    d = _records(env, run_id)["wm:7101"].provenance["upc_detail"]
    assert d["status"] == "request_failed"
    assert d["reason"] == "the site answered with its not-found page (page data route /404, HTTP 200)"
    row = field_rows(env, run_id)["wm:7101"]
    assert (
        row["upc"]["disposition"] == disp.REQUEST_FAILED
        and row["weight"]["disposition"] == disp.REQUEST_FAILED
    )
    with env["factory"]() as s:
        run = s.get(Run, run_id)
        assert run is not None and run.stop_code is None  # never a refusal


def test_two_workers_never_read_past_a_page_budget(env: dict[str, Any]) -> None:  # noqa: F811
    """The budget counts the other worker's page still on its way: both workers checking at once could read
    one page each past it."""
    run_id, _status = _run(env, detail=DetailConfig(max_per_run=2, reuse_days=0), workers=2)
    read = [item for _, item in _detail_calls(env)]
    assert len(read) == 2 and len(set(read)) == 2, read
    rows = field_rows(env, run_id)
    assert sum(r["upc"]["disposition"] == disp.INTERRUPTED for r in rows.values()) == 2


def test_every_outcome_of_an_empty_field_is_told_apart(env: dict[str, Any]) -> None:  # noqa: F811
    def answer(url: str) -> httpx.Response | None:
        if "/ip/" not in url:
            return None
        item = urlsplit(url).path.rstrip("/").rsplit("/", 1)[-1]
        if item == "7101":
            return httpx.Response(200, text="<html><title>Robot or human?</title></html>")
        if item == "7201":
            return httpx.Response(200, text="<html><body>no data</body></html>")
        if item == "7203":
            return httpx.Response(200, text=mock.product_page("9999", "012345678905"))
        return httpx.Response(200, text=product_page("7301"))

    env["mock"].page_override = answer
    run_id, _ = _run(env)
    rows = field_rows(env, run_id)
    assert rows["wm:7101"]["upc"]["disposition"] == disp.BLOCKED
    assert rows["wm:7201"]["upc"]["disposition"] == disp.PARSE_FAILURE
    assert rows["wm:7203"]["upc"]["disposition"] == disp.IDENTITY_MISMATCH
    assert rows["wm:7301"]["upc"]["disposition"] == disp.ABSENT
    assert all(r["upc"]["value"] == "" for r in rows.values())
    # Reading off (a pilot): no page is requested. A product whose earlier read was refused or failed is not
    # attempted, and nothing claims the source lacks it. Release 1.6.3: the product whose page an earlier read
    # did inspect (7301: it states no UPC) keeps that read's outcome, named as that read (its run and time),
    # never as read now; until 1.6.2 reading off reused nothing, so 7301 was "not attempted" too.
    env["mock"].page_override = None
    env["mock"].calls.clear()
    off, _ = _run(env, detail=DetailConfig(enabled=False))
    assert _detail_calls(env) == []
    rows = field_rows(env, off)
    failed = {k: r for k, r in rows.items() if k != "wm:7301"}
    assert {"wm:7101", "wm:7201", "wm:7203"} <= set(failed)
    assert {r["upc"]["disposition"] for r in failed.values()} == {disp.NOT_ATTEMPTED}
    assert {r["upc"]["reason"] for r in failed.values()} == {"product detail reading is off"}
    inspected = rows["wm:7301"]["upc"]
    assert inspected["disposition"] == disp.ABSENT and inspected["value"] == ""
    assert inspected["source_run"] == run_id
    assert (
        inspected["observed_at"] == _records(env, run_id)["wm:7301"].provenance["upc_detail"]["requested_at"]
    )


def test_a_failed_page_stays_in_the_queue_and_is_read_again(env: dict[str, Any]) -> None:  # noqa: F811
    env["mock"].page_override = pages({"7101": "<html><body>no data</body></html>"})
    _run(env)
    env["mock"].page_override = None
    env["mock"].calls.clear()
    second, _ = _run(env)
    assert [i for _, i in _detail_calls(env)] == [
        "7101"
    ]  # the others are reused, the failed one is asked again
    assert _records(env, second)["wm:7101"].record["upc"] == mock.PRODUCT_UPCS["7101"]
    with env["factory"]() as s:
        store = s.scalar(select(Store).where(Store.key == STORE_KEY))
        assert store is not None
        assert follow_queue.counts(s, store_id=store.id)["by_kind_and_state"] == {"detail:resolved": 4}


def test_a_carried_row_names_the_run_that_read_its_fields(env: dict[str, Any]) -> None:  # noqa: F811
    first, _ = _run(env)
    second, _ = _run(env, limits=Limits(max_pages_per_listing=1))
    row = field_rows(env, second)["wm:7203"]
    assert row["observation_kind"] == "carried_forward"
    assert row["upc"]["disposition"] == disp.FETCHED and row["upc"]["source_run"] == first


def test_saved_pages_load_with_their_own_time_and_serve_a_later_run_as_recovered(
    env: dict[str, Any],  # noqa: F811
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The offline step before any paid page: a stored page answers for its item, under its original time, run
    and revision. Pages of another item, or without page data, are refused and listed."""
    one_product(monkeypatch, syn.Item("7101", "Whole Milk", "$3.12"))
    saved = tmp_path / "saved"
    saved.mkdir()
    (saved / "good.html.gz").write_bytes(
        gzip.compress(product_page("7101", upc=PINNED_UPC, specs={"Size": "1 Gallon"}).encode("utf-8"))
    )
    (saved / "other.html").write_text(product_page("9999", upc="012345678905"), encoding="utf-8")
    (saved / "challenge.html").write_text("<html><title>Robot or human?</title></html>", encoding="utf-8")
    at = iso(utcnow() - timedelta(days=2))
    entries = [
        {
            "item_id": "7101",
            "observed_at": at,
            "run_id": "01M60F6GHNXCTZPJ6G1PRM7KW7",
            "page_fetch_id": "01FETCH",
            "source_revision": "1.4.1 37ffca8",
            "url": "https://www.walmart.com/ip/x/7101",
            "path": "good.html.gz",
        },
        {"item_id": "7102", "observed_at": at, "run_id": "R", "path": "other.html"},
        {"item_id": "7103", "observed_at": at, "run_id": "R", "path": "challenge.html"},
        {"item_id": "7104", "observed_at": at, "run_id": "R", "path": "not-there.html"},
    ]
    with env["factory"]() as s:
        store = s.scalar(select(Store).where(Store.key == STORE_KEY))
        assert store is not None
        out = detail_captures.load(s, store.id, entries, saved)
        again = detail_captures.load(s, store.id, entries[:1], saved)
        s.commit()
    assert out["counts"] == {
        "identity_mismatch": 1,
        "loaded_extracted": 1,
        "missing_file": 1,
        "parse_failed": 1,
    }
    assert again["counts"] == {"already_loaded": 1}
    run_id, _ = _run(env)
    assert _detail_calls(env) == []
    rec = _records(env, run_id)["wm:7101"]
    assert rec.record["upc"] == PINNED_UPC and rec.record["weight"] == "1 Gallon"
    row = field_rows(env, run_id)["wm:7101"]
    for field in ("upc", "weight"):
        assert row[field]["disposition"] == disp.RECOVERED and row[field]["origin"] == "imported"
        assert row[field]["source_run"] == "01M60F6GHNXCTZPJ6G1PRM7KW7"
        assert row[field]["source_revision"] == "1.4.1 37ffca8"
        assert row[field]["observed_at"] == at


def test_a_duplicate_upc_from_a_saved_page_is_still_excluded(
    env: dict[str, Any],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        mock.PAGES,
        mock.MILK,
        [[syn.Item("7101", "Whole Milk", "$3.12"), syn.Item("7102", "Whole Milk Again", "$3.12")]],
    )
    monkeypatch.setitem(mock.PAGES, mock.SNACKS, [[]])
    monkeypatch.setitem(mock.PAGES, mock.DIAPERING, [[]])
    env["mock"].page_override = pages(
        {
            "7101": product_page("7101", upc=PINNED_UPC, specs={"Size": "1 Gallon"}),
            "7102": product_page("7102", upc=PINNED_UPC, specs={"Size": "1 Gallon"}),
        }
    )
    first, _ = _run(env)
    with env["factory"]() as s:
        rows = list(s.scalars(select(RecordRow).where(RecordRow.run_id == first)))
    assert sorted(r.status for r in rows) == ["excluded", "valid"]
    excluded = next(r for r in rows if r.status == "excluded")
    assert "DUPLICATE_UPC" in excluded.reasons
