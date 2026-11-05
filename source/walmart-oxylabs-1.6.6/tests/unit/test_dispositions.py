"""Why a product's UPC and size are filled or empty (publishing/dispositions.py): each outcome the requirement
separates has its own disposition, and an unattempted field is never called absent from the source."""

from __future__ import annotations

import pytest

from walmart_headless.publishing import dispositions as disp

UPC = "012345678905"


@pytest.mark.parametrize(
    ("detail", "expected"),
    [
        ({"status": "absent_in_source", "reason": "states none"}, disp.ABSENT),
        ({"status": "blocked", "reason": "Robot or human?"}, disp.BLOCKED),
        ({"status": "request_failed", "reason": "HTTP 500"}, disp.REQUEST_FAILED),
        ({"status": "parse_failed", "reason": "no page data"}, disp.PARSE_FAILURE),
        ({"status": "identity_mismatch", "reason": "another item"}, disp.IDENTITY_MISMATCH),
        ({"status": "not_attempted", "reason": "no item id or URL"}, disp.NOT_ATTEMPTED),
        ({"reason": "the run's detail limit (1 pages) was reached"}, disp.INTERRUPTED),
    ],
)
def test_each_outcome_of_an_empty_upc_keeps_its_own_disposition(
    detail: dict[str, str], expected: str
) -> None:
    out = disp.upc({"upc": ""}, detail)
    assert out["disposition"] == expected and out["value"] == ""


def test_an_unattempted_upc_is_never_called_absent_from_the_source() -> None:
    assert disp.upc({"upc": ""}, {})["disposition"] != disp.ABSENT


TILE_FIELDS = {
    "weight": {"source": "walmart_title", "selector_or_path": "items[11].name (none)", "fetch_id": "tile"},
    "url": {"source": "walmart_page_data", "selector_or_path": "items[11].canonicalUrl", "fetch_id": "tile"},
}
TILE_MISSING = {"upc": "the listing states no UPC", "weight": "the title states no size", "ppm": "none shown"}
TILE_KIND = {"upc": "source_absent", "weight": "source_absent", "ppm": "source_absent"}
READ = {
    "status": "extracted",
    "value": UPC,
    "item_id": "10402650",
    "fresh": False,
    "size_filled": True,
    "size": {"path": "idml.specifications[3].value", "rule": "spec_net_content", "value": "1 Count"},
    "reused_from": {
        "run_id": "R1",
        "requested_at": "2026-10-31T21:26:39Z",
        "page_fetch_id": "F1",
        "path": "data.product.upc",
        "body_sha256": "ab" * 32,
        "source_revision": "1.5.0 7b6f325",
        "origin": "fetched",
    },
}


def _applied(record: dict[str, str], detail: dict[str, object]) -> tuple[dict, dict, dict]:
    return disp.apply_to_sources(TILE_FIELDS, TILE_MISSING, TILE_KIND, disp.of_record(record, detail))


def test_a_reused_read_keeps_the_place_its_upc_was_read_from() -> None:
    """Until 1.5.1 ``path`` was looked for on the row, and a reused read keeps it on ``reused_from``."""
    assert disp.upc({"upc": UPC}, READ)["path"] == "data.product.upc"


@pytest.mark.parametrize("field", ["upc", "weight"])
def test_a_value_from_an_own_page_names_that_page_and_leaves_missing(field: str) -> None:
    """S6 item 10402650: the size came from a page read 90 minutes earlier in another run, on 1.5.0, while
    ``fields.weight`` named the tile's title with rule "none" and ``missing.weight`` kept the listing's
    text."""
    fields, missing, kind = _applied({"upc": UPC, "weight": "1 Count"}, READ)
    assert field not in missing and field not in kind and missing["ppm"] == "none shown"
    src = fields[field]
    assert src["source"] == disp.SOURCE_OWN_PAGE and src["fetch_id"] == "F1"
    assert (src["observed_at"], src["source_run"]) == ("2026-10-31T21:26:39Z", "R1")
    assert src["source_revision"] == "1.5.0 7b6f325" and src["item_id"] == "10402650"
    assert src["response_sha256"] == "ab" * 32 and src["origin"] == "fetched"
    assert fields["url"] == TILE_FIELDS["url"]


def test_the_place_a_size_was_read_from_names_its_rule() -> None:
    fields, _, _ = _applied({"upc": UPC, "weight": "1 Count"}, READ)
    assert fields["weight"]["selector_or_path"] == "idml.specifications[3].value (spec_net_content)"
    assert fields["upc"]["selector_or_path"] == "data.product.upc"


@pytest.mark.parametrize(
    ("detail", "kind"),
    [
        ({"status": "not_attempted", "reason": "no item id or URL"}, "not_attempted"),
        (
            {"status": "not_attempted", "reason": "the run's detail limit (22 pages) was reached"},
            "budget_deadline_interruption",
        ),
        ({"status": "blocked", "reason": "Robot or human?"}, "blocked"),
        ({"status": "request_failed", "reason": "HTTP 500"}, "request_failed"),
        ({"status": "parse_failed", "reason": "no page data"}, "parse_failure"),
        ({"status": "identity_mismatch", "reason": "another item"}, "identity_mismatch"),
    ],
)
def test_only_a_page_that_was_read_can_call_a_upc_absent(detail: dict[str, str], kind: str) -> None:
    """Until 1.5.1 every UPC a result page did not state read ``source_absent``, the 226 products of S6 whose
    page nobody requested among them."""
    _, missing, kinds = _applied({"upc": "", "weight": ""}, detail)
    assert kinds["upc"] == kind
    assert detail["reason"] in missing["upc"] and "the listing states no UPC" in missing["upc"]


def test_a_page_that_states_nothing_is_absent_and_a_conflict_says_so() -> None:
    size = {"outcome": "conflict", "conflicts": ["'12 oz' against '16 oz'"], "observations": []}
    detail = {"status": "absent_in_source", "reason": "states none", "size": size}
    _, missing, kinds = _applied({"upc": "", "weight": ""}, detail)
    assert kinds["upc"] == "source_absent" and kinds["weight"] == "conflicting_evidence"
    assert "'12 oz' against '16 oz'" in missing["weight"]


def test_a_value_the_listing_stated_keeps_the_listings_source() -> None:
    fields, missing, kinds = disp.apply_to_sources(
        {"weight": {"source": "walmart_title"}},
        {},
        {},
        disp.of_record({"upc": UPC, "weight": "1 Gallon"}, {"listing_upc": True, "status": "extracted"}),
    )
    assert fields == {"weight": {"source": "walmart_title"}} and not missing and not kinds


@pytest.mark.parametrize("field", ["upc", "weight"])
def test_a_detail_limit_of_zero_pages_is_not_attempted_not_a_budget_interruption(field: str) -> None:
    """Release 1.4.1's capped demonstrations (``--pdp-sample 0``, e.g. Oxylabs B3 01M60V2DCCWR72BGVVG3EM9R74)
    recorded "the run's detail limit (0 pages) was reached": no product page was attempted at all, so the
    field is not_attempted (the client's own reading of B3), never a budget that ran out part-way."""
    zero = "the run's detail limit (0 pages) was reached"
    key = "reason" if field == "upc" else "size_unread_reason"
    out = getattr(disp, field)({field: ""}, {key: zero})
    assert (out["disposition"], out["reason"]) == (disp.NOT_ATTEMPTED, zero)
    some = getattr(disp, field)({field: ""}, {key: "the run's detail limit (20 pages) was reached"})
    assert some["disposition"] == disp.INTERRUPTED


def test_a_upc_of_this_runs_read_and_one_reused_are_told_apart() -> None:
    fresh = disp.upc(
        {"upc": UPC},
        {"status": "extracted", "requested_at": "2026-10-31T20:00:00Z", "observed_by_run": "R2"},
    )
    assert fresh["disposition"] == disp.FETCHED and fresh["source_run"] == "R2"
    reused = disp.upc(
        {"upc": UPC},
        {
            "status": "extracted",
            "reused_from": {
                "requested_at": "2026-10-26T10:00:00Z",
                "run_id": "R1",
                "source_revision": "abc",
                "origin": "imported",
            },
        },
    )
    assert reused["disposition"] == disp.RECOVERED
    assert (reused["observed_at"], reused["source_run"], reused["source_revision"]) == (
        "2026-10-26T10:00:00Z",
        "R1",
        "abc",
    )
    assert reused["origin"] == "imported"


def test_a_upc_the_listing_states_is_present_in_the_listing_and_keeps_a_page_that_disagrees() -> None:
    out = disp.upc({"upc": UPC}, {"listing_upc": UPC, "upc_conflict": {"page": "036000451293"}})
    assert out["disposition"] == disp.PRESENT and out["conflicts"] == [{"page": "036000451293"}]
    assert disp.upc({"upc": UPC}, {"source": disp.LISTING_SOURCE})["disposition"] == disp.PRESENT


def test_csv_has_one_row_per_product_with_upc_leading_zeros_as_text() -> None:
    rows = [
        {
            "key": "wm:1",
            "observation_kind": "fresh",
            "url": "https://www.walmart.com/ip/x/1",
            "category": "Food",
            "sub_category": "",
            "product_title": "T",
            "upc": {"disposition": disp.PRESENT, "value": "000123456789"},
            "weight": {"disposition": disp.ABSENT, "value": "", "reason": "states none"},
        }
    ]
    text = disp.csv_bytes(rows).decode("utf-8-sig")  # with a byte-order mark, for spreadsheets
    assert text.splitlines()[0].split(",") == list(disp.CSV_COLUMNS)
    assert "000123456789" in text and disp.counts(rows)["upc"][disp.PRESENT] == 1
