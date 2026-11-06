"""Release 1.3.0 follow-ups through the run pipeline, against the Scrape.do mock serving SYNTHETIC Walmart
pages (tests/mock_scrapedo.py): after the listings, a product seen only in sponsored placements and an item
a result tile names as one of its options (a variant sibling) are read on their own product page in the
store's context. Each is included only when its own page identifies it, is shown for the store and files
it under the listing's category; otherwise the outcome says why (excluded, inaccessible, duplicate, not
attempted). The coverage reconciliation counts the placements and the outcomes per listing. Nothing here
reaches Scrape.do or Walmart."""

from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from sqlalchemy import select

from tests import synthetic_walmart as syn
from tests.conftest import CONFIG
from tests.integration.test_coverage_and_assortment import env, records  # noqa: F401  (the fixture)
from tests.mock_scrapedo import DIAPERING, listing
from walmart_headless.collection import reconcile
from walmart_headless.collection.config import (
    CollectionConfig,
    DetailConfig,
    FollowSeed,
    FollowUpConfig,
    Limits,
)
from walmart_headless.collection.nodes import Node
from walmart_headless.collection.walmart import WalmartCollector
from walmart_headless.core.settings import load_settings
from walmart_headless.db.models import CategorySource, Event, ProductObservation, Run, Task, ValidationFinding
from walmart_headless.worker.pipeline import Pipeline

pytestmark = [pytest.mark.postgres]

CAT = ("Diapering", ["5427", "5427_486190"])
DIAPERING_CRUMBS = (("Baby", "/cp/baby/5427"), ("Diapering", "/browse/diapering/5427_486190"))
FRUIT_CRUMBS = (
    ("Food", "/cp/food/976759"),
    ("Fresh Fruits", "/browse/food/fresh-fruits/976759_976793_9756351"),
)


def option(item_id: str, name: str, *, availability: str = "IN_STOCK") -> dict[str, Any]:
    url = f"/ip/{name.replace(' ', '-')}/{item_id}"
    return {
        "name": name,
        "availabilityStatus": availability,
        "selectedProduct": {"usItemId": item_id, "canonicalUrl": url},
    }


SIZES = {
    "variantCriteria": [
        {
            "name": "diaper_size",
            "variantList": [
                option("9001", "Size 1"),
                option("9101", "Size 2"),
                option("9102", "Size 3", availability="OUT_OF_STOCK"),
                option("9002", "Size 4"),
                {"name": "More sizes", "selectedProduct": {}},  # a label without an item: never followed
            ],
        }
    ]
}
TILES = [
    syn.Item("9001", "Diapers A, Size 1, 84 Count", "$9.97", unit="11.9 ¢/ea", extra=SIZES),
    syn.Item("9002", "Diapers B, Size 4, 60 Count", "$10.97", unit="18.3 ¢/ea"),
    syn.Item("9003", "Wipes C, 3 Pack", "$5.97"),
    syn.Item("9201", "Sponsored Diapers D, Size 3, 31 Count", "$12.97", sponsored=True),
    syn.Item("9202", "Sponsored Fruit E, 2 lb", "$3.97", sponsored=True),
    syn.Item("9203", "Sponsored Wipes F, 6 Pack", "$8.97", sponsored=True),
    # Also an organic tile: the same product in a sponsored placement.
    syn.Item("9002", "Diapers B, Size 4, 60 Count", "$10.97", unit="18.3 ¢/ea", sponsored=True),
]


def product_page(
    it: syn.Item,
    *,
    path_id: str = "0:5427:486190",
    crumbs: tuple[tuple[str, str], ...] = DIAPERING_CRUMBS,
    store: str = "3891",
    upc: str = "",
) -> str:
    """A SYNTHETIC store-scoped product page: the item's own data with the location it is shown for and the
    category path Walmart files it under (``initialData.data.product``)."""
    p = syn.item_json(it, store)
    p.update(
        location={
            "storeIds": [store],
            "pickupLocation": {"storeId": store},
            "intent": "PICKUP",
            "postalCode": "60085",
        },
        category={"categoryPathId": path_id, "path": [{"name": n, "url": u} for n, u in crumbs]},
        fulfillmentOptions=[
            {"type": "PICKUP", "availabilityStatus": "IN_STOCK", "locationText": "Waukegan Supercenter"}
        ],
        offerType="ONLINE_AND_STORE",
        sellerType="INTERNAL",
    )
    if upc:
        p["upc"] = upc
    data = {"props": {"pageProps": {"initialData": {"data": {"product": p}}}}}
    return f"<!doctype html><html><body>{syn.next_data_script(data)}</body></html>"


PRODUCTS = {
    "9101": product_page(
        syn.Item("9101", "Diapers A, Size 2, 76 Count", "$9.97", unit="13.1 ¢/ea"),
        path_id="0:5427:486190:1101406",
        upc="000123456789",
    ),
    "9201": product_page(
        syn.Item("9201", "Sponsored Diapers D, Size 3, 31 Count", "$12.97"), upc="036000451293"
    ),
    "9202": product_page(
        syn.Item("9202", "Sponsored Fruit E, 2 lb", "$3.97"),
        path_id="0:976759:976793:9756351",
        crumbs=FRUIT_CRUMBS,
    ),
    "9203": product_page(syn.Item("9203", "Sponsored Wipes F, 6 Pack", "$8.97"), store="5260"),
    "9301": product_page(syn.Item("9301", "Seeded Diapers G, Size 5", "$14.97")),
}


def site(e: dict[str, Any], tiles: list[syn.Item], products: dict[str, str]) -> list[str]:
    """The listing (one page) and the product pages, through the store endpoint; returns the product
    pages requested, in order."""
    asked: list[str] = []
    organic = sum(1 for t in {t.item_id: t for t in tiles if not t.sponsored}.values())

    def override(url: str) -> httpx.Response | None:
        u = urlsplit(url)
        headers = {"Scrape.do-Request-Cost": "10", "Scrape.do-Walmart-Store-Id": "3891"}
        if u.path.startswith("/ip/"):
            item = u.path.rstrip("/").rsplit("/", 1)[-1]
            asked.append(item)
            if item not in products:
                return httpx.Response(404, text="not found", headers=headers)
            return httpx.Response(200, text=products[item], headers=headers)
        if f"{u.scheme}://{u.netloc}{u.path}" == DIAPERING:
            n = int(parse_qs(u.query).get("page", ["1"])[0])
            html = listing(tiles if n == 1 else [], page=n, max_page=1, total=organic, cat=CAT)
            return httpx.Response(200, text=html, headers=headers)
        return None

    e["mock"].page_override = override
    return asked


def run(e: dict[str, Any], follow_up: FollowUpConfig | None = None, workers: int = 1) -> tuple[str, str]:
    settings = load_settings(CONFIG / "settings.yaml")
    pipe = Pipeline(e["engine"], e["storage"], settings, e["store"], e["private_label"])
    cfg = CollectionConfig(
        limits=Limits(), detail=DetailConfig(enabled=False), follow_up=follow_up or FollowUpConfig()
    )
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
                "pilot": False,
            },
            follow_shards=workers,
        )
        s.commit()
    collector = WalmartCollector(pipe, run_id, config=cfg, trigger="manual")
    status = asyncio.run(pipe.execute(run_id, "test-collector", collector=collector, workers=workers))
    return run_id, status


def outcomes(e: dict[str, Any], run_id: str) -> dict[tuple[str, str], dict[str, Any]]:
    with e["factory"]() as s:
        events = s.scalars(
            select(Event)
            .where(Event.run_id == run_id, Event.code.like("FOLLOW_UP_%"), Event.code != "FOLLOW_UP_DONE")
            .order_by(Event.ts, Event.id)
        )
        return {(e.data["kind"], e.data["item_id"]): dict(e.data) for e in events if "kind" in (e.data or {})}


def test_sponsored_only_products_and_variant_siblings_are_followed_to_their_own_pages(
    env: dict[str, Any],  # noqa: F811
) -> None:
    asked = site(env, TILES, PRODUCTS)
    run_id, final = run(env)
    out = outcomes(env, run_id)
    status = {k: v["status"] for k, v in out.items()}
    assert status == {
        ("sponsored", "9201"): "included",
        ("sponsored", "9202"): "excluded",
        ("sponsored", "9203"): "inaccessible",
        ("sponsored", "9002"): "duplicate",
        ("variant", "9101"): "included",
        ("variant", "9102"): "inaccessible",
        ("variant", "9002"): "duplicate",
    }
    # A sponsored label alone neither excludes nor includes: the product's own page decides.
    assert out[("sponsored", "9202")]["reason"].startswith("required category not established")
    assert "976759" in out[("sponsored", "9202")]["category_evidence"]
    assert "not shown for store 3891" in out[("sponsored", "9203")]["reason"]
    assert out[("variant", "9102")]["reason"] == "access failed: HTTP 404"
    assert out[("variant", "9101")]["named_by"] == "9001"
    assert out[("variant", "9101")]["option"] == {"criterion": "diaper_size", "value": "Size 2"}
    assert "own result tile" in out[("sponsored", "9002")]["reason"]
    # Only real items are followed (never the "More sizes" label), each page once; duplicates cost nothing.
    assert sorted(asked) == ["9101", "9102", "9201", "9202", "9203"]
    recs = records(env, run_id)
    assert recs["wm:9201"].status == "valid" and recs["wm:9101"].status == "valid"
    assert recs["wm:9101"].record["upc"] == "000123456789"  # as the page states it (leading zeros kept)
    assert not {"wm:9202", "wm:9203", "wm:9102"} & set(recs)
    with env["factory"]() as s:
        obs = {
            (o.upc, o.source)
            for o in s.scalars(select(ProductObservation).where(ProductObservation.run_id == run_id))
        }
        assert {("wm:9002", "card"), ("wm:9002", "sponsored_card")} <= obs  # both placements kept
        assert {("wm:9201", "sponsored_card"), ("wm:9201", "pdp"), ("wm:9101", "pdp")} <= obs
        r = s.get(Run, run_id)
        assert r is not None
        follow = r.counts["follow_up"]
        assert follow["sponsored"]["included"] == 1 and follow["variants"]["inaccessible"] == 1
        data = reconcile.reconcile(s, run_id)
    [row] = [x for x in data["rows"] if x["listing_id"] == "5427_486190"]
    assert row["status"] == "DONE" and row["distinct_identities"] == 3 and row["unresolved_difference"] == 0
    assert row["sponsored_placements"] == 4 and row["sponsored_only_products"] == 3
    # Release 1.3.1: the listing balances on its 3 organic identities; its 3 sponsored-only identities are
    # outside that total and leave nothing unresolved, so the coverage gate (G3) passes.
    assert row["difference_placed"] == -3 and row["reconciliation_basis"] == "organic"
    with env["factory"]() as s:
        g3 = s.scalars(
            select(ValidationFinding).where(
                ValidationFinding.run_id == run_id, ValidationFinding.gate == "G3"
            )
        )
        assert [f.message for f in g3 if f.severity == "FAIL"] == []
    assert final != "rejected"
    assert row["variant_identities_named"] == 3 and row["variant_identities_not_own_tile"] == 2
    assert row["follow_up_outcomes"] == {
        "sponsored:included": 1,
        "sponsored:excluded": 1,
        "sponsored:inaccessible": 1,
        "sponsored:duplicate": 1,
        "variant:included": 1,
        "variant:inaccessible": 1,
        "variant:duplicate": 1,
    }
    assert list(row["follow_up_outcomes"]) == sorted(row["follow_up_outcomes"])  # a fixed order (1.3.1)
    assert len(data["follow_ups"]) == 7
    csv_text = reconcile.as_csv(data["rows"])
    assert csv_text.splitlines()[0].split(",") == list(reconcile.COLUMNS)


def test_options_named_by_a_repeated_or_a_sponsored_tile_are_followed(
    env: dict[str, Any],  # noqa: F811
) -> None:
    # Release 1.3.1: a later tile of a product may name options its first tile does not (live 2026-10-26,
    # Bath & Body: eos 625527254), and a sponsored tile may name options too. Release 1.3.0 kept the options
    # of the tile it recorded only; now every tile's options are kept (``tile_options``) and followed.
    counts = {
        "variantCriteria": [{"name": "count", "variantList": [option("9105", "Diapers D, Size 3, 62 Count")]}]
    }
    tiles = [
        syn.Item("9001", "Diapers A, Size 1, 84 Count", "$9.97", unit="11.9 ¢/ea"),
        syn.Item("9002", "Diapers B, Size 4, 60 Count", "$10.97", unit="18.3 ¢/ea"),
        syn.Item("9001", "Diapers A, Size 1, 84 Count", "$9.97", unit="11.9 ¢/ea", extra=SIZES),
        syn.Item("9201", "Sponsored Diapers D, Size 3, 31 Count", "$12.97", sponsored=True, extra=counts),
    ]
    products = {**PRODUCTS, "9105": product_page(syn.Item("9105", "Diapers D, Size 3, 62 Count", "$21.97"))}
    asked = site(env, tiles, products)
    run_id, _ = run(env, FollowUpConfig(sponsored=False))
    out = outcomes(env, run_id)
    assert {k: v["status"] for k, v in out.items()} == {
        ("variant", "9101"): "included",
        ("variant", "9102"): "inaccessible",
        ("variant", "9002"): "duplicate",
        ("variant", "9105"): "included",
    }
    assert out[("variant", "9101")]["named_by"] == "9001" and out[("variant", "9105")]["named_by"] == "9201"
    assert sorted(asked) == ["9101", "9102", "9105"]
    with env["factory"]() as s:
        opts = {
            o.upc: o.provenance
            for o in s.scalars(
                select(ProductObservation).where(
                    ProductObservation.run_id == run_id, ProductObservation.source == "tile_options"
                )
            )
        }
    # One observation per product and page, for the tiles no record was kept from; never a record itself.
    assert sorted(opts) == ["wm:9001", "wm:9201"]
    assert [t["sponsored"] for t in opts["wm:9001"]["tiles"]] == [False]
    assert [t["sponsored"] for t in opts["wm:9201"]["tiles"]] == [True]
    assert [v["item_id"] for v in opts["wm:9001"]["variant_siblings"]] == ["9101", "9102", "9002"]
    assert opts["wm:9001"]["verified"] is False and opts["wm:9201"]["verified"] is False
    recs = records(env, run_id)
    assert recs["wm:9105"].status == "valid" and "wm:9201" not in recs


@pytest.mark.parametrize("sponsored", [True, False])
def test_a_variant_seen_only_as_a_sponsored_tile_is_read_by_one_follow_up(
    env: dict[str, Any],  # noqa: F811
    sponsored: bool,
) -> None:
    # Release 1.4.1 (live 2026-10-28, Scrape.do: 6 rows in two runs): release 1.4.0 called a variant seen only
    # as a sponsored tile "recorded from that placement", though no record is kept from a sponsored tile, and
    # with the sponsored follow-up off no follow-up read it. The sponsored follow-up reads it; when that is
    # off, the variant follow-up does.
    tiles = [*TILES[:3], syn.Item("9101", "Diapers A, Size 2, 76 Count", "$9.97", sponsored=True)]
    asked = site(env, tiles, PRODUCTS)
    run_id, _ = run(env, FollowUpConfig(sponsored=sponsored))
    out = outcomes(env, run_id)
    assert sorted(asked) == ["9101", "9102"]  # each page once
    assert out[("variant", "9002")]["status"] == "duplicate"  # an organic tile: recorded from it
    assert "recorded from that placement" in out[("variant", "9002")]["reason"]
    if sponsored:
        assert out[("variant", "9101")]["status"] == "duplicate"
        assert out[("variant", "9101")]["reason"] == (
            "this run saw it only as a sponsored tile: the sponsored follow-up reads its own page"
        )
        assert out[("sponsored", "9101")]["status"] == "included"
    else:
        assert out[("variant", "9101")]["status"] == "included"
        assert ("sponsored", "9101") not in out
    assert records(env, run_id)["wm:9101"].status == "valid"


def test_follow_ups_pause_after_consecutive_failures_and_say_what_was_not_attempted(
    env: dict[str, Any],  # noqa: F811
) -> None:
    tiles = TILES[:3] + [
        syn.Item(str(9210 + i), f"Sponsored Item {i}", "$1.00", sponsored=True) for i in range(5)
    ]
    asked = site(env, tiles, {})
    run_id, _ = run(env, FollowUpConfig(variants=False))
    out = outcomes(env, run_id)
    statuses = [out[("sponsored", str(9210 + i))]["status"] for i in range(5)]
    assert statuses == ["inaccessible"] * 3 + ["not_attempted"] * 2
    assert out[("sponsored", "9214")]["reason"].startswith("follow-ups paused: 3 consecutive product pages")
    assert asked == ["9210", "9211", "9212"]  # nothing more was requested after the pause
    with env["factory"]() as s:
        codes = list(
            s.scalars(select(Event.code).where(Event.run_id == run_id, Event.code == "FOLLOW_UP_PAUSED"))
        )
        assert codes == ["FOLLOW_UP_PAUSED"]
        tasks = {
            t.cursor["follow"]: t
            for t in s.scalars(select(Task).where(Task.run_id == run_id, Task.kind == "follow_up"))
        }
        assert tasks["variants"].cursor["status"] == "OFF" and tasks["sponsored"].cursor["status"] == "DONE"


def test_reported_items_are_followed_first_and_a_page_limit_leaves_the_rest_not_attempted(
    env: dict[str, Any],  # noqa: F811
) -> None:
    asked = site(env, TILES, PRODUCTS)
    seeds = [
        FollowSeed(
            kind="sponsored",
            item_id="9301",
            url="https://www.walmart.com/ip/Seeded-Diapers-G/9301",
            listing_id="5427_486190",
            source="report 01M5P24C",
        ),
        FollowSeed(
            kind="variant",
            item_id="9302",
            url="https://www.walmart.com/ip/Seeded-Fruit/9302",
            listing_id="976759_976793_9756351",
            named_by="9001",
            source="report 01M5P24C",
        ),
    ]
    run_id, _ = run(env, FollowUpConfig(max_pages=2, seeds=seeds))
    out = outcomes(env, run_id)
    first = next(iter(k for k in out if k[0] == "sponsored"))
    assert first == ("sponsored", "9301") and out[first]["status"] == "included"
    assert out[first]["seed"] == "report 01M5P24C"
    # A seed whose listing this run did not read is not attempted (never assumed).
    assert out[("variant", "9302")]["status"] == "not_attempted"
    assert "not among the listings this run read" in out[("variant", "9302")]["reason"]
    sponsored = [k for k in out if k[0] == "sponsored"]
    limited = [k for k in sponsored if out[k]["status"] == "not_attempted"]
    assert limited and all("follow-up page limit (2 pages per kind)" in out[k]["reason"] for k in limited)
    assert asked.count("9301") == 1 and len([a for a in asked if a.startswith("92")]) == 1


def test_follow_ups_that_are_off_request_nothing(env: dict[str, Any]) -> None:  # noqa: F811
    asked = site(env, TILES, PRODUCTS)
    run_id, _ = run(env, FollowUpConfig(sponsored=False, variants=False))
    assert asked == [] and outcomes(env, run_id) == {}
    with env["factory"]() as s:
        states = {
            t.cursor.get("status")
            for t in s.scalars(select(Task).where(Task.run_id == run_id, Task.kind == "follow_up"))
        }
        assert states == {"OFF"}


def test_two_workers_share_the_follow_ups_and_read_each_product_page_once(
    env: dict[str, Any],  # noqa: F811
) -> None:
    """Until 1.5.0 the follow-ups were one task per kind, however many workers a run had. Two workers now have
    two tasks per kind, each with its own share of the candidates, and read together what one worker reads."""
    asked = site(env, TILES, PRODUCTS)
    serial, serial_status = run(env)
    serial_pages = sorted(asked)
    asked.clear()
    parallel, parallel_status = run(env, workers=2)
    assert serial_pages and sorted(asked) == serial_pages and len(asked) == len(set(asked))
    assert parallel_status == serial_status
    with env["factory"]() as s:
        tasks = list(s.scalars(select(Task).where(Task.run_id == parallel, Task.kind == "follow_up")))
        assert sorted((t.cursor["follow"], t.cursor["shard"], t.cursor["shards"]) for t in tasks) == [
            ("sponsored", 0, 2),
            ("sponsored", 1, 2),
            ("variants", 0, 2),
            ("variants", 1, 2),
        ]
        assert {t.cursor["status"] for t in tasks} == {"DONE"}
        one = s.get(Run, serial)
        two = s.get(Run, parallel)
        assert one is not None and two is not None
        for name in ("sponsored", "variants"):
            for field in ("candidates", "pages_read", "named_by_run"):
                assert two.counts["follow_up"][name][field] == one.counts["follow_up"][name][field], field
    assert records(env, parallel).keys() == records(env, serial).keys()
    assert {k: r.status for k, r in records(env, parallel).items()} == {
        k: r.status for k, r in records(env, serial).items()
    }


def test_a_pilot_follow_up_budget_is_divided_among_the_workers_tasks(
    env: dict[str, Any],  # noqa: F811
) -> None:
    asked = site(env, TILES, PRODUCTS)
    run_id, _status = run(env, FollowUpConfig(max_pages=2, variants=False), workers=2)
    assert 1 <= len(asked) <= 2 and len(asked) == len(set(asked))
    with env["factory"]() as s:
        r = s.get(Run, run_id)
        assert r is not None
        assert r.counts["follow_up"]["sponsored"]["pages_read"] == len(asked)
