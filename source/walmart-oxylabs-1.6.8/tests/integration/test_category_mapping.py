"""Release 1.6.7: the agreed category mapping (sub_category is the name the CSV row's category page gives the
listing), and a CSV row read in part is never complete. Through the command line, as in test_operations.py:
a throwaway PostgreSQL and the in-memory mock of Scrape.do serving SYNTHETIC Walmart pages. Nothing here
reaches Scrape.do or Walmart.

The live discrepancy reproduced: Walmart's Household Essentials category page names listing
``1115193_1071967_1630538`` "Fabric Softeners"; that listing's own result page names itself "Fabric Softener".
L7 and L10 (which read the category page) exported the first; L8 and L12 (which read the listing by its path,
``--subcategory``) the second. Here the mock's Milk listing names itself "Milk Products" on its own page,
while the mock's Food category page names it "Milk"."""

from __future__ import annotations

import copy
import csv
import io
import json
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from tests import mock_scrapedo
from tests import synthetic_walmart as syn
from tests.conftest import STORE_KEY
from tests.integration.test_operations import Env, env  # noqa: F401 - the command-line fixture
from tests.mock_scrapedo import MILK, SNACKS
from walmart_headless.db.models import Event, RecordRow, Run, Task

pytestmark = [pytest.mark.postgres]

MILK_PATH = "0:/browse/food/milk/976759_9176907"
SNACKS_PATH = "0:" + SNACKS.removeprefix("https://www.walmart.com")


@pytest.fixture
def own_page_name(monkeypatch: pytest.MonkeyPatch) -> str:
    """The mock's Milk listing page names itself otherwise than the Food category page names it."""
    name = "Milk Products"
    monkeypatch.setitem(mock_scrapedo.LISTING_CATS, MILK, (name, ["976759", "976759_9176907"]))
    return name


def products(env: Env, run: Run) -> list[dict[str, Any]]:  # noqa: F811
    exports = env.data / "runs" / STORE_KEY / run.id / "exports"
    return list(json.loads((exports / "products.json").read_text("utf-8")))


def coverage(env: Env, run: Run) -> dict[str, Any]:  # noqa: F811
    """The run's coverage reconciliation, as ``coverage-report --out`` writes it (rows included)."""
    out = env.data / "coverage-report" / run.id
    code, report = env.result("coverage-report", "--run", run.id, "--out", str(out))
    assert code == 0, report
    full = json.loads((out / f"coverage_reconciliation_{run.id}.json").read_text("utf-8"))
    assert full["coverage_complete"] == report["coverage_complete"]
    return dict(full)


def events(env: Env, run: Run, code: str) -> list[Event]:  # noqa: F811
    with sessionmaker(env.engine, expire_on_commit=False)() as s:
        return list(s.scalars(select(Event).where(Event.run_id == run.id, Event.code == code)))


def test_a_listing_read_by_its_path_takes_the_name_its_stored_category_page_gave_it(
    env: Env,  # noqa: F811
    own_page_name: str,
) -> None:
    # A census of Food reads the category page: its listings are named as the page names them.
    code, _ = env.result("run", "--store", STORE_KEY, "--categories", "0")
    assert code in (0, 6)
    census = env.runs()[-1]
    assert {p["sub_category"] for p in products(env, census) if p["url"].endswith("/7101")} == {"Milk"}
    # The same listing read by its path: its own page says "Milk Products"; the stored category page wins.
    code, _ = env.result("run", "--store", STORE_KEY, "--categories", "0", "--subcategory", MILK_PATH)
    assert code == 0
    narrowed = env.runs()[-1]
    milk = [p for p in products(env, narrowed) if p["url"].endswith("/7101")]
    assert [p["sub_category"] for p in milk] == ["Milk"], milk
    [configured] = events(env, narrowed, "SUBCATEGORIES_CONFIGURED")
    named = (configured.data.get("names") or {}).get("976759_9176907") or {}
    assert named.get("name") == "Milk" and named.get("run_id") == census.id, configured.data
    row = next(r for r in coverage(env, narrowed)["rows"] if r["listing_id"] == "976759_9176907")
    assert row["listing_name"] == "Milk" and row["found_via"] == "configured"


def test_without_a_stored_category_page_the_listings_own_name_is_used_and_said(
    env: Env,  # noqa: F811
    own_page_name: str,
) -> None:
    code, _ = env.result("run", "--store", STORE_KEY, "--categories", "0", "--subcategory", MILK_PATH)
    assert code == 0
    run = env.runs()[-1]
    assert {p["sub_category"] for p in products(env, run)} == {own_page_name}
    with sessionmaker(env.engine)() as s:
        task_cursor = s.execute(
            select(Event.data).where(Event.run_id == run.id, Event.code == "SUBCATEGORIES_CONFIGURED")
        ).scalar_one()
    assert task_cursor.get("names") == {"976759_9176907": None}, task_cursor


def test_a_carried_record_takes_the_category_pages_name_and_its_lineage_says_so(
    env: Env,  # noqa: F811
    own_page_name: str,
) -> None:
    """The Milk product is first read through its path, with no category page stored: "Milk Products".
    A category page that names the listing "Milk" is then stored (here: its SUBCATEGORIES_FOUND event, as a
    census run records it). A later run that does not observe the product carries it forward with the
    category page's name; the lineage keeps the name it had and the source record's hash."""
    code, _ = env.result("run", "--store", STORE_KEY, "--categories", "0", "--subcategory", MILK_PATH)
    first = env.runs()[-1]
    assert code == 0 and {p["sub_category"] for p in products(env, first)} == {own_page_name}
    with sessionmaker(env.engine)() as s:
        s.add(
            Event(
                run_id=first.id,
                level="INFO",
                code="SUBCATEGORIES_FOUND",
                message="SYNTHETIC TEST: the Food category page's links, as a census run records them",
                data={"node": "976759", "listings": [{"name": "Milk", "url": MILK, "note": ""}]},
            )
        )
        s.commit()
    code, _ = env.result("run", "--store", STORE_KEY, "--categories", "0", "--subcategory", SNACKS_PATH)
    assert code == 0
    later = env.runs()[-1]
    milk = [p for p in products(env, later) if p["url"].endswith("/7101")]
    assert [p["sub_category"] for p in milk] == ["Milk"], milk
    with sessionmaker(env.engine)() as s:
        rec = s.scalars(
            select(RecordRow).where(RecordRow.run_id == later.id, RecordRow.status == "historical")
        ).all()
    [carried] = [r for r in rec if r.record["url"].endswith("/7101")]
    renamed = carried.provenance["historical"].get("renamed_by_mapping") or {}
    assert (renamed.get("was"), renamed.get("now"), renamed.get("listing")) == (
        own_page_name,
        "Milk",
        "976759_9176907",
    ), carried.provenance["historical"]
    assert renamed["named_by"]["run_id"] == first.id and len(renamed["source_record_sha256"]) == 64
    assert carried.record["crawl_date"] == milk[0]["crawl_date"]  # its own date, unchanged
    assert later.counts["historical"].get("renamed_by_mapping") == 1


def mock_rows_only(env: Env) -> None:  # noqa: F811
    """The client's CSV cut to the two rows the mock serves (Food, row 0, and Diapering), every row planned:
    a run of the mock can then cover the whole CSV. The copied configuration only; the CSV's own format."""
    path = env.config.parent / "Walmart_Category_URLs.csv"
    rows = list(csv.reader(io.StringIO(path.read_bytes().decode("utf-8"))))
    assert [r[1] for r in rows[1:]][:5] == [
        "Food",
        "Household Essentials",
        "Personal Care",
        "Beauty",
        "Diapering",
    ]
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\r\n").writerows([rows[0], rows[1], rows[5]])
    path.write_bytes(buf.getvalue().encode("utf-8"))
    env.edit(categories=[])  # every row of the CSV


def food_outcomes(env: Env, run: Run) -> list[Event]:  # noqa: F811
    with sessionmaker(env.engine, expire_on_commit=False)() as s:
        nodes = s.scalars(select(Event).where(Event.run_id == run.id, Event.code.like("NODE_%")))
        return [e for e in nodes if e.data.get("node") == "976759"]


def test_a_row_read_only_through_its_configured_listings_is_never_complete(env: Env) -> None:  # noqa: F811
    """With every CSV row planned, a run that reads every listing covers the CSV. The same run narrowed to
    Food's Milk listing (by its path) reads a complete listing, but not the row's other listings: the row is
    CAPPED, never DONE, and the run's coverage is not complete."""
    mock_rows_only(env)
    code, _ = env.result("run", "--store", STORE_KEY)
    assert code == 0
    whole = env.runs()[-1]
    report = coverage(env, whole)
    summary = {k: v for k, v in report.items() if k != "rows"}
    assert report["coverage_complete"] is True, summary  # the control: a whole read is complete
    assert [e.code for e in food_outcomes(env, whole)] == ["NODE_DONE"]
    code, _ = env.result("run", "--store", STORE_KEY, "--subcategory", MILK_PATH)
    assert code == 0
    narrowed = env.runs()[-1]
    report = coverage(env, narrowed)
    summary = {k: v for k, v in report.items() if k != "rows"}
    food = food_outcomes(env, narrowed)
    assert ([e.code for e in food], report["coverage_complete"]) == (["NODE_CAPPED"], False), (
        [e.message for e in food],
        summary,
    )
    assert "the row was read in part" in food[0].message, food[0].message
    assert report["csv_rows_read_in_part"] == ["0"] and report["csv_rows_not_planned"] == [], summary
    row = next(r for r in report["rows"] if r["listing_id"] == "976759_9176907")
    assert row["status"] == "DONE"  # the listing itself is complete; the row is not
    manifest = json.loads(
        (env.data / "runs" / STORE_KEY / narrowed.id / "exports" / "manifest.json").read_text("utf-8")
    )
    assert manifest["dataset"] == "pilot", manifest


def test_a_replay_names_listings_only_from_pages_stored_before_its_source_and_a_rows_own_page_wins(
    env: Env,  # noqa: F811
) -> None:
    """``navigation.category_page_names``: ``before`` (a replay: its source run's creation) leaves out names
    stored at or after it; with ``node``, the name the CSV row's own category page gave wins over a name
    another row's page gave the same listing. SYNTHETIC events on a run that read no category page."""
    from walmart_headless.collection import navigation  # new in release 1.6.7

    code, _ = env.result("run", "--store", STORE_KEY, "--categories", "0", "--subcategory", MILK_PATH)
    assert code == 0
    run = env.runs()[-1]
    t0 = datetime(2026, 11, 1, 6, 0, tzinfo=UTC)
    with sessionmaker(env.engine)() as s:
        assert navigation.category_page_names(s, run.store_id) == {}  # a run by path reads no category page
        for minutes, node, name in ((0, "976759", "Milk"), (10, "1115193", "Dairy Milk")):
            s.add(
                Event(
                    run_id=run.id,
                    ts=t0 + timedelta(minutes=minutes),
                    level="INFO",
                    code=navigation.FOUND_CODE,
                    message="SYNTHETIC TEST: a category page's links",
                    data={"node": node, "listings": [{"name": name, "url": MILK, "note": ""}]},
                )
            )
        s.commit()
        latest = navigation.category_page_names(s, run.store_id)["976759_9176907"]
        own = navigation.category_page_names(s, run.store_id, node="976759")["976759_9176907"]
        before = navigation.category_page_names(s, run.store_id, before=t0 + timedelta(minutes=5))
        none_before = navigation.category_page_names(s, run.store_id, before=t0)
    assert (latest.name, latest.node) == ("Dairy Milk", "1115193")  # the latest page, of another row
    assert (own.name, own.node) == ("Milk", "976759")  # the row's own page wins
    assert before["976759_9176907"].name == "Milk" and none_before == {}


# Release 1.6.8: one listing that a category page links twice, by two paths, under two names. SYNTHETIC:
# another path to the mock's Milk listing (Walmart serves a listing by its ID, whatever the path's words).
PROMO_MILK = "https://www.walmart.com/browse/subscriptions/milk/976759_9176907"


def test_a_listing_the_category_page_links_twice_is_read_once_under_its_first_name(
    env: Env,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A category page can link one listing twice, by two paths, under two names. Live, the Food page links
    976759_976794_2002490 as "Pantry" (its 9th link) and again as "Great Value Pantry" (its 55th, another path
    to the same listing; L4, 2026-11-03, and L7, 2026-11-04); the Feeding page links 5427_132943_2441534 as
    "Baby Health Care" and as "Baby Healthcare" (L10). Up to the second 1.6.8 candidate a run read such a
    listing once per path, and its
    products took the name of the read that placed them (L10 recorded products under both names).
    The listing is read once, under the first name the page gives it. SYNTHETIC: the Food page links Milk
    again, from a "Subscription" group, by another path to the same listing (no filter: the same view)."""
    monkeypatch.setattr(
        mock_scrapedo,
        "category_page",
        lambda: mock_scrapedo.nav_page(
            [
                ("Recipes", [("Shop All", "/i/recipes")]),
                ("Dairy & Eggs", [("Shop All", "/cp/dairy-eggs/9176907"), ("Milk", MILK)]),
                ("Snacks", [("Shop all", SNACKS)]),
                ("Subscription", [("Subscription", PROMO_MILK)]),
            ]
        ),
    )
    monkeypatch.setitem(mock_scrapedo.PAGES, PROMO_MILK, mock_scrapedo.PAGES[MILK])  # the same listing
    monkeypatch.setitem(mock_scrapedo.LISTING_CATS, PROMO_MILK, mock_scrapedo.LISTING_CATS[MILK])
    before = len(env.mock.calls)
    code, _ = env.result("run", "--store", STORE_KEY, "--categories", "0")
    assert code in (0, 6)
    run = env.runs()[-1]
    milk_reads = [
        url
        for _, path, url in env.mock.calls[before:]
        if path == "/plugin/walmart/store" and "976759_9176907" in url
    ]
    assert len(milk_reads) == 1 and "/browse/food/milk/" in milk_reads[0], milk_reads
    assert [p["sub_category"] for p in products(env, run) if p["url"].endswith("/7101")] == ["Milk"]
    [found] = [e for e in events(env, run, "SUBCATEGORIES_FOUND") if e.data.get("node") == "976759"]
    named = [x["name"] for x in found.data["listings"] if x["url"].rstrip("/").endswith("/976759_9176907")]
    assert named == ["Milk"], found.data["listings"]


def test_a_stored_category_page_that_named_a_listing_twice_gives_it_its_first_name(
    env: Env,  # noqa: F811
    own_page_name: str,
) -> None:
    """Runs up to the second 1.6.8 candidate recorded both links of a listing a category page names twice
    (the Food page: "Pantry", then "Great Value Pantry"). ``category_page_names`` kept the last, so the
    agreed mapping of 1.6.7 renamed 43 carried records of L12's replay "Great Value Pantry" (and, through
    filtered views, 268 "Subscription" and 35 "Men's Deodorant": see the filtered-view tests below). The first
    name a page gives a listing is its name; a later page still replaces an earlier page's name. SYNTHETIC
    events, as such a run recorded them."""
    from walmart_headless.collection import navigation

    code, _ = env.result("run", "--store", STORE_KEY, "--categories", "0", "--subcategory", MILK_PATH)
    assert code == 0
    first = env.runs()[-1]
    t0 = datetime(2026, 11, 1, 6, 0, tzinfo=UTC)
    twice = [
        {"name": "Milk", "url": MILK, "note": ""},
        {"name": "Subscription", "url": PROMO_MILK, "note": ""},
    ]
    with sessionmaker(env.engine)() as s:
        s.add(
            Event(
                run_id=first.id,
                ts=t0,
                level="INFO",
                code=navigation.FOUND_CODE,
                message="SYNTHETIC TEST: a category page that links Milk twice, as earlier runs recorded it",
                data={"node": "976759", "listings": twice},
            )
        )
        s.commit()
        named = navigation.category_page_names(s, first.store_id)
        own = navigation.category_page_names(s, first.store_id, node="976759")
    assert named["976759_9176907"].name == "Milk" and own["976759_9176907"].name == "Milk"
    # A run that reads the listing by its path takes that name, never the later link's.
    code, _ = env.result("run", "--store", STORE_KEY, "--categories", "0", "--subcategory", MILK_PATH)
    assert code == 0
    narrowed = env.runs()[-1]
    assert [p["sub_category"] for p in products(env, narrowed) if p["url"].endswith("/7101")] == ["Milk"]
    # A later page of the row replaces the earlier page's name, by its own first link.
    later = [{"name": "Dairy Milk", "url": PROMO_MILK, "note": ""}, {"name": "Milk", "url": MILK, "note": ""}]
    with sessionmaker(env.engine)() as s:
        s.add(
            Event(
                run_id=first.id,
                ts=t0 + timedelta(minutes=10),
                level="INFO",
                code=navigation.FOUND_CODE,
                message="SYNTHETIC TEST: a later page of the same row",
                data={"node": "976759", "listings": later},
            )
        )
        s.commit()
        assert navigation.category_page_names(s, first.store_id)["976759_9176907"].name == "Dairy Milk"


# Release 1.6.8: a link that shows a listing filtered. Live, Health & Wellness links listing
# 976760_4661388_6244277_7158394 only through two filtered views, "Cough" (facet=health_concern:Cough) and
# "Subscription" (facet=subscription_eligible:Subscription item); Personal Care links 1005862_1001487 as
# "Deodorant" and, filtered, as "Men's Deodorant" (facet=gender:Male). A filtered view is part of the listing,
# never the listing itself. SYNTHETIC: filtered links to the mock's Milk listing.
ORGANIC_MILK = MILK + "?facet=organic%3AYes&povid=FoodCP_LHN_Organic_Milk"
SUBSCRIPTION_MILK = PROMO_MILK + "?facet=subscription_eligible%3ASubscription+item"
W = "https://www.walmart.com"


def food_page(monkeypatch: pytest.MonkeyPatch, *groups: tuple[str, list[tuple[str, str]]]) -> None:
    monkeypatch.setattr(mock_scrapedo, "category_page", lambda: mock_scrapedo.nav_page(list(groups)))


def store_reads(env: Env, before: int, needle: str) -> list[str]:  # noqa: F811
    """The listing URLs the run asked the store endpoint for that contain ``needle``."""
    return [
        url for _, path, url in env.mock.calls[before:] if path == "/plugin/walmart/store" and needle in url
    ]


def test_a_listing_linked_only_through_filtered_views_is_read_itself_in_full_once(
    env: Env,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    own_page_name: str,
) -> None:
    """The third 1.6.8 candidate read only the first filtered view (its key was the listing ID alone): the
    listing's other products were never read, the listing could be called complete from part of it, and the
    filter's name ("Cough") named every product of the listing. The listing itself is read, once, without the
    filters; the page names it only through filtered views, so its own page names it, and says so."""
    food_page(
        monkeypatch,
        ("Snacks", [("Shop all", SNACKS)]),
        ("Deals", [("Organic Milk", ORGANIC_MILK), ("Subscription", SUBSCRIPTION_MILK)]),
    )
    monkeypatch.setitem(mock_scrapedo.PAGES, PROMO_MILK, mock_scrapedo.PAGES[MILK])
    monkeypatch.setitem(mock_scrapedo.LISTING_CATS, PROMO_MILK, mock_scrapedo.LISTING_CATS[MILK])
    before = len(env.mock.calls)
    code, _ = env.result("run", "--store", STORE_KEY, "--categories", "0")
    assert code in (0, 6)
    run = env.runs()[-1]
    reads = store_reads(env, before, "976759_9176907")
    assert len(reads) == 1 and "organic" not in reads[0] and "subscription" not in reads[0], reads
    assert [p["sub_category"] for p in products(env, run) if p["url"].endswith("/7101")] == [own_page_name]
    [found] = [e for e in events(env, run, "SUBCATEGORIES_FOUND") if e.data.get("node") == "976759"]
    views = found.data["filtered_views"]
    assert [(v["name"], v["listing"]) for v in views] == [
        ("Organic Milk", "976759_9176907"),
        ("Subscription", "976759_9176907"),
    ], views
    assert all(v["note"].startswith("a filtered view of listing 976759_9176907") for v in views), views
    [itself] = [x for x in found.data["listings"] if x["url"].endswith("/976759_9176907")]
    assert itself == {"name": "", "url": MILK, "note": ""}, found.data["listings"]
    report = coverage(env, run)
    row = next(r for r in report["rows"] if r["listing_id"] == "976759_9176907")
    assert (row["listing_name"], row["filtered_view"], row["effective_status"]) == (own_page_name, "", "DONE")
    assert len(report["filtered_views"]) == 2, report["filtered_views"]


def test_a_link_to_the_listing_itself_after_a_filtered_view_names_it_and_it_is_read_once(
    env: Env,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    own_page_name: str,
) -> None:
    """The page links the listing filtered first, and the listing itself later ("Men's Deodorant" first
    would make it so for Deodorant). The third 1.6.8 candidate read the filtered view and skipped the link to
    the listing itself. The listing is read once, without the filter, under the name the page gives the
    listing itself."""
    food_page(
        monkeypatch,
        ("Deals", [("Organic Milk", ORGANIC_MILK)]),
        ("Dairy & Eggs", [("Milk", MILK)]),
        ("Snacks", [("Shop all", SNACKS)]),
    )
    before = len(env.mock.calls)
    code, _ = env.result("run", "--store", STORE_KEY, "--categories", "0")
    assert code in (0, 6)
    run = env.runs()[-1]
    reads = store_reads(env, before, "976759_9176907")
    assert len(reads) == 1 and "organic" not in reads[0], reads
    assert [p["sub_category"] for p in products(env, run) if p["url"].endswith("/7101")] == ["Milk"]
    [found] = [e for e in events(env, run, "SUBCATEGORIES_FOUND") if e.data.get("node") == "976759"]
    assert [x["name"] for x in found.data["listings"] if x["url"].endswith("/976759_9176907")] == ["Milk"]
    assert [v["name"] for v in found.data["filtered_views"]] == ["Organic Milk"]


SHELVES = {
    W + "/browse/pre-cut-fruits/0/0": (
        "Fresh Fruit",
        "8210692",
        syn.Item("7401", "Apple Slices, 2 oz", "$1.00"),
    ),
    W + "/browse/kids-lunches-&-snacks/0/0": (
        "Snack packs",
        "7195079",
        syn.Item("7402", "Cheese Snack Pack, 4 ct", "$2.00"),
    ),
}


def test_two_shelves_that_share_listing_id_0_are_two_listings(
    env: Env,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Live, the Food page links two shelves, "Fresh Fruit" (/browse/pre-cut-fruits/0/0, shelf 8210692) and
    "Snack packs" (/browse/kids-lunches-&-snacks/0/0, shelf 7195079): listing ID 0, a shelf's query being the
    whole listing. The third 1.6.8 candidate read the first only (one key, ``browse:0``); before it, both
    were read under one ID, 0, and so one coverage record. Each shelf is read, under its own ID."""
    links = []
    for base, (name, shelf, item) in SHELVES.items():
        links.append(
            (name, f"{base}?_refineresult=true&_be_shelf_id={shelf}&facet=shelf_id%3A{shelf}&povid=x")
        )
        monkeypatch.setitem(mock_scrapedo.PAGES, base, [[item]])
    food_page(monkeypatch, ("Featured shops", links))
    before = len(env.mock.calls)
    code, _ = env.result("run", "--store", STORE_KEY, "--categories", "0")
    assert code in (0, 6)
    run = env.runs()[-1]
    assert len(store_reads(env, before, "/0/0")) == 2
    rows = {r["listing_id"]: r for r in coverage(env, run)["rows"]}
    assert {k: (r["listing_name"], r["status"]) for k, r in rows.items() if k.startswith("0")} == {
        "0@shelf_id:8210692": ("Fresh Fruit", "DONE"),
        "0@shelf_id:7195079": ("Snack packs", "DONE"),
    }, sorted(rows)


def test_a_filtered_view_of_the_rows_own_category_is_not_a_listing_of_its_own(
    env: Env,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Live, Household Essentials links its own category filtered, "Clearance"
    (/browse/household-essentials/1115193?facet=special_offers:Clearance), and Pets "Under $5"
    (/browse/5440?max_price=5): part of what the row's subcategories list. It is recorded, not read; the row
    is complete when its listings are. The third 1.6.8 candidate read it as a listing."""
    mock_rows_only(env)
    food_page(
        monkeypatch,
        ("Recipes", [("Shop All", "/i/recipes")]),
        ("Dairy & Eggs", [("Shop All", "/cp/dairy-eggs/9176907"), ("Milk", MILK)]),
        ("Snacks", [("Shop all", SNACKS)]),
        ("Deals", [("Clearance", "/browse/food/976759?facet=special_offers%3AClearance&povid=FoodCP")]),
    )
    monkeypatch.setitem(mock_scrapedo.PAGES, W + "/browse/food/976759", mock_scrapedo.PAGES[MILK])
    before = len(env.mock.calls)
    code, _ = env.result("run", "--store", STORE_KEY)
    assert store_reads(env, before, "/browse/food/976759") == []
    assert code == 0
    run = env.runs()[-1]
    [found] = [e for e in events(env, run, "SUBCATEGORIES_FOUND") if e.data.get("node") == "976759"]
    [view] = found.data["filtered_views"]
    assert (view["name"], view["listing"]) == ("Clearance", "976759"), view
    assert view["note"].startswith("a filtered view of category 976759, which the row reads through"), view
    report = coverage(env, run)
    assert report["coverage_complete"] is True, {k: v for k, v in report.items() if k != "rows"}
    assert [v["name"] for v in report["filtered_views"]] == ["Clearance"]


def test_a_subcategory_page_that_links_a_listing_filtered_has_it_read_itself_and_found_on_the_page(
    env: Env,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    own_page_name: str,
) -> None:
    """A subcategory page of its own links a listing only filtered, and its own category filtered. The listing
    itself is read, once, as a listing found on that page; the filtered view of the page's own category is
    part of what the page's listings list, and is not read. Both links are recorded."""
    food_page(monkeypatch, ("Dairy & Eggs", [("Shop All", "/cp/dairy-eggs/9176907")]))
    monkeypatch.setitem(
        mock_scrapedo.CATEGORY_PAGES,
        "/cp/dairy-eggs/9176907",
        mock_scrapedo.nav_page(
            [
                (
                    "Dairy",
                    [
                        ("Organic Milk", ORGANIC_MILK),
                        ("Clearance", "/browse/dairy-eggs/9176907?facet=special_offers%3AClearance"),
                    ],
                )
            ]
        ),
    )
    monkeypatch.setitem(mock_scrapedo.PAGES, W + "/browse/dairy-eggs/9176907", mock_scrapedo.PAGES[MILK])
    before = len(env.mock.calls)
    code, _ = env.result("run", "--store", STORE_KEY, "--categories", "0")
    assert code in (0, 6)
    run = env.runs()[-1]
    reads = store_reads(env, before, "976759_9176907")
    assert len(reads) == 1 and "organic" not in reads[0], reads
    assert store_reads(env, before, "/browse/dairy-eggs/9176907") == []
    assert [p["sub_category"] for p in products(env, run) if p["url"].endswith("/7101")] == [own_page_name]
    [page] = events(env, run, "SUBCATEGORY_PAGE_READ")
    assert [(v["name"], v["listing"]) for v in page.data["filtered_views"]] == [
        ("Organic Milk", "976759_9176907"),
        ("Clearance", "9176907"),
    ], page.data
    row = next(r for r in coverage(env, run)["rows"] if r["listing_id"] == "976759_9176907")
    assert (row["found_via"], row["found_on"], row["listing_name"]) == (
        "subcategory_page",
        "9176907",
        own_page_name,
    )
    assert row["navigation_evidence"].startswith(
        "linked, only through filtered views, by the subcategory page"
    )


def test_a_name_a_page_gives_a_filtered_view_never_renames_the_listing_itself(
    env: Env,  # noqa: F811
    own_page_name: str,
) -> None:
    """Runs up to 1.6.7 recorded a filtered link among the listings a page names (L10's Health & Wellness:
    "Cough", facet=health_concern:Cough). The third 1.6.8 candidate keyed a name by the listing ID alone:
    it would have renamed the 249 carried records of 976760_4661388_6244277_7158394 that L12 exported as
    "Shop all Cold Cough & Flu Medicine" (read from the listing itself) "Cough". A filtered view's name names
    that view only. SYNTHETIC events, as such a run recorded them."""
    from walmart_headless.collection import navigation

    code, _ = env.result("run", "--store", STORE_KEY, "--categories", "0", "--subcategory", MILK_PATH)
    assert code == 0
    first = env.runs()[-1]
    assert {p["sub_category"] for p in products(env, first)} == {own_page_name}
    with sessionmaker(env.engine)() as s:
        s.add(
            Event(
                run_id=first.id,
                level="INFO",
                code=navigation.FOUND_CODE,
                message="SYNTHETIC TEST: a category page that links Milk only filtered, as 1.6.7 recorded it",
                data={
                    "node": "976759",
                    "listings": [{"name": "Organic Milk", "url": ORGANIC_MILK, "note": ""}],
                },
            )
        )
        s.commit()
        names = navigation.category_page_names(s, first.store_id, node="976759")
    code, _ = env.result("run", "--store", STORE_KEY, "--categories", "0", "--subcategory", SNACKS_PATH)
    assert code == 0
    later = env.runs()[-1]
    milk = [p for p in products(env, later) if p["url"].endswith("/7101")]
    assert [p["sub_category"] for p in milk] == [own_page_name], milk
    assert later.counts["historical"].get("renamed_by_mapping") == 0
    assert set(names) == {"976759_9176907?facet=organic%3AYes"}, names
    # A run that reads the listing by its path takes no name from the filtered link either.
    code, _ = env.result("run", "--store", STORE_KEY, "--categories", "0", "--subcategory", MILK_PATH)
    assert code == 0
    [configured] = events(env, env.runs()[-1], "SUBCATEGORIES_CONFIGURED")
    assert configured.data.get("names") == {"976759_9176907": None}, configured.data


def test_a_stored_read_of_a_filtered_view_never_completes_its_listing_in_the_coverage_report(
    env: Env,  # noqa: F811
) -> None:
    """A run of an earlier release read a filtered link as if it were the listing (L10: "Allergy",
    facet=subscription_eligible, 0 results; "Contact solution", 30 results: the 1.6.6 and earlier 1.6.8
    coverage tables called both COMPLETE). Its results are part of the listing: the listing is not complete,
    and its row stays open. A filtered view of the row's own category (L10: Personal Care "Clearance") is not
    a listing of the row. SYNTHETIC: a whole run's stored Food checkpoint, its Milk link given a filter as
    such a run recorded it, and a filtered link to Food itself added."""
    mock_rows_only(env)
    code, _ = env.result("run", "--store", STORE_KEY)
    assert code == 0
    run = env.runs()[-1]
    assert coverage(env, run)["coverage_complete"] is True  # the control: as read
    with sessionmaker(env.engine)() as s:
        tasks = s.scalars(select(Task).where(Task.run_id == run.id, Task.kind == "listing_node")).all()
        [task] = [t for t in tasks if (t.cursor.get("node") or {}).get("taxonomy_id") == "976759"]
        cursor = copy.deepcopy(task.cursor)
        [milk] = [x for x in cursor["listings"] if x["id"] == "976759_9176907"]
        milk["url"] = ORGANIC_MILK
        cursor["listings"].append(
            {
                **copy.deepcopy(milk),
                "id": "976759",
                "name": "Clearance",
                "url": W + "/browse/food/976759?facet=special_offers%3AClearance",
                "seen": [],
            }
        )
        task.cursor = cursor
        s.commit()
    report = coverage(env, run)
    rows = {r["listing_id"]: r for r in report["rows"]}
    milk_row, own_row = rows["976759_9176907"], rows["976759"]
    assert (milk_row["effective_status"], milk_row.get("filtered_view_of")) == ("INCOMPLETE", "listing"), (
        milk_row["effective_reason"]
    )
    assert milk_row["effective_reason"].startswith(
        "only a filtered view of the listing was read (facet=organic:Yes)"
    )
    assert milk_row["status"] == "DONE"  # as the run recorded it
    assert (own_row["effective_status"], own_row["filtered_view_of"]) == ("SKIPPED", "row"), own_row
    food = next(r for r in report["csv_rows"] if r["csv_row"] == 0)
    assert food["complete"] is False and "976759_9176907 INCOMPLETE" in food["why_not_complete"], food
    assert "976759 " not in food["why_not_complete"].replace("976759_", ""), food
    assert report["coverage_complete"] is False
