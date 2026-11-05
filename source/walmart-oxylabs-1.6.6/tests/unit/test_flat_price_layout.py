"""Release 1.6.5: the source check reads Walmart's flat price layout.

Live census L10 of 2026-11-04 (run 01M6KA3CKYJSD6WDY4TDAAV73Y, release 1.6.4): one listing page (Beauty's
"New Arrivals", fetch 01M6KB69AJA2N65MDQP4V1QWTE) gave its items' prices as flat display strings
(``priceInfo.linePriceDisplay``/``linePrice``, ``priceInfo.unitPrice``) with no price line. The collector's
page reader reads that layout, and the records it exported show the page's prices. The source check
(:mod:`walmart_headless.checks.source_check`) read only the price lines and the nested price objects: it
reported 21 of the run's 10,301 records as mismatches, and ``validate-export`` exited 6. The canary compares a
run's first recorded page in the same way, so a first page in this layout would have stopped a run.

The authentic pages, and the run's exported records that it read from the flat page, are
``tests/captures/listing_pages_20261104_flat``; the changed values below are SYNTHETIC."""

from __future__ import annotations

import copy
import gzip
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from walmart_headless.checks import source_check

PAGES = Path(__file__).resolve().parents[1] / "captures" / "listing_pages_20261104_flat"
FLAT, LINES = "flat_layout_page.html.gz", "price_lines_page.html.gz"
STORE = "3891"


def records() -> list[dict[str, Any]]:
    data: list[dict[str, Any]] = json.loads((PAGES / "l10_records.json").read_text("utf-8"))
    return data


def placements(name: str) -> list[dict[str, Any]]:
    nd = source_check.page_json(PAGES / name)
    assert nd is not None
    return [item for _, item in source_check.items_of(nd)]


def item(name: str, item_id: str) -> dict[str, Any]:
    return next(it for it in placements(name) if str(it["usItemId"]) == item_id)


def record(item_id: str) -> dict[str, Any]:
    return next(r for r in records() if source_check.item_id_of(r["url"]) == item_id)


def folder(tmp_path: Path, *names: str) -> Path:
    out = tmp_path / "pages"
    out.mkdir()
    for name in names:
        shutil.copyfile(PAGES / name, out / name)
    return out


def test_the_fixture_matches_its_manifest() -> None:
    for entry in json.loads((PAGES / "MANIFEST.json").read_text("utf-8")):
        data = (PAGES / entry["file"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry["source_sha256"], entry["file"]
        assert hashlib.sha256(gzip.decompress(data)).hexdigest() == entry["content_sha256"], entry["file"]


def test_the_live_page_gives_its_prices_as_flat_strings_only() -> None:
    flat = placements(FLAT)
    assert (len(flat), len({str(it["usItemId"]) for it in flat})) == (50, 42)
    for it in flat:
        info = it["priceInfo"]
        assert not (info.get("priceDetails") or {}).get("priceLines")
        assert not isinstance(info.get("currentPrice"), dict)
        assert info["linePriceDisplay"] and info["linePrice"]
    # The other page gives its prices in price lines, as every other stored page of the live runs; one of its
    # placements shows no price.
    other = placements(LINES)
    assert not any(
        it["priceInfo"].get("linePriceDisplay") or it["priceInfo"].get("linePrice") for it in other
    )
    assert sum(1 for it in other if (it["priceInfo"].get("priceDetails") or {}).get("priceLines")) == 58
    assert len(other) == 59


def test_the_prices_read_are_those_the_page_displays() -> None:
    assert source_check.expected_prices(item(FLAT, "20585873588")) == ("$5.00", "", "")
    assert source_check.expected_prices(item(FLAT, "18905414013")) == ("$16.97", "", "$1.06/oz")
    assert source_check.expected_prices(item(FLAT, "20485002977")) == ("$9.74", "", "$32.47/fl oz")


def test_the_records_the_run_read_from_the_page_are_verified_against_it(tmp_path: Path) -> None:
    recs = records()
    assert len(recs) == 26 and sum(1 for r in recs if r["ppm"]) == 19
    res = source_check.check(recs, folder(tmp_path, FLAT), STORE)
    assert res["summary"] == {"records": 26, "verified": 26, "mismatch": 0, "unverified": 0}
    assert {r["source"]["page"] for r in res["results"]} == {FLAT}
    assert all(r["page"]["pickup_at_store"] for r in res["results"])


def test_a_record_seen_on_two_pages_is_judged_on_the_page_it_was_read_from(tmp_path: Path) -> None:
    """Head & Shoulders 20409871453: a placement on each page; the price-lines page shows another image size.
    Release 1.6.4 could not read the flat page's prices, judged the record on the other page and reported its
    image as a mismatch."""
    rec = record("20409871453")
    [res] = source_check.check([rec], folder(tmp_path, FLAT, LINES), STORE)["results"]
    assert res["result"] == "verified" and res["mismatched_fields"] == []
    assert (res["source"]["page"], res["source"]["pages_with_item"]) == (FLAT, 3)
    assert item(LINES, "20409871453")["imageInfo"]["thumbnailUrl"] != rec["image_url"]


def test_the_canary_comparison_accepts_the_page() -> None:
    """The canary judges each valid record of a run's first recorded page by ``compare`` against its best
    placement on that page."""
    flat = placements(FLAT)
    for rec in records():
        options = [it for it in flat if str(it["usItemId"]) == source_check.item_id_of(rec["url"])]
        best = min(
            (source_check.compare(rec, it)[0] for it in options), key=lambda c: sum(not v for v in c.values())
        )
        assert all(best.values()), (rec["url"], best)


def test_a_wrong_price_or_unit_price_is_still_a_mismatch(tmp_path: Path) -> None:
    rec = record("18905414013")  # SYNTHETIC changes of an authentic record
    wrong = [dict(rec, regular_price="99.99"), dict(rec, ppm="$0.01/oz"), dict(rec, regular_price="", ppm="")]
    res = source_check.check(wrong, folder(tmp_path, FLAT), STORE)
    assert res["summary"] == {"records": 3, "verified": 0, "mismatch": 3, "unverified": 0}
    assert [r["mismatched_fields"] for r in res["results"]] == [
        ["regular_price"],
        ["ppm"],
        ["regular_price", "ppm"],
    ]


def test_a_flat_was_price_above_the_current_price_is_a_sale() -> None:
    it = copy.deepcopy(item(FLAT, "18905414013"))  # SYNTHETIC: the live page shows no was-price
    it["priceInfo"]["wasPrice"] = "$19.97"
    assert source_check.expected_prices(it) == ("$19.97", "$16.97", "$1.06/oz")
    it["priceInfo"]["wasPrice"] = "$15.00"  # not above the current price: no sale
    assert source_check.expected_prices(it) == ("$16.97", "", "$1.06/oz")
