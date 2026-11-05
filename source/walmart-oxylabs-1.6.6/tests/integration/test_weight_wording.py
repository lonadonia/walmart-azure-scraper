"""Release 1.4.0: approximate or estimated-weight wording excludes the whole product within a run.

Walmart shows the estimate next to the price of a product sold by the piece and charged by weight ("each
(est.)") on its organic result tile, and no wording on a sponsored tile of the same product (the Apples page
of 2026-10-26: items 43923746 and 51259330). Release 1.4.0 excludes a product for that wording, not for being
sold by weight, so a run that saw the product on both tiles must exclude it whichever tile it read last.

SYNTHETIC pages through the Scrape.do mock (tests/mock_scrapedo.py); nothing reaches a provider."""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy import select

from tests import synthetic_walmart as syn
from tests.integration.test_coverage_and_assortment import (
    CRUMBS,
    env,  # noqa: F401  (env is a fixture)
    records,
    run_diapering,
    serve,
)
from tests.mock_scrapedo import DIAPERING, listing
from walmart_headless.db.models import Event, ProductObservation

pytestmark = [pytest.mark.postgres]

PLAIN = syn.Item("9001", "Synthetic Apple, Each", "$1.12", unit="$2.24/lb", weight_priced=True)
ESTIMATED = syn.Item(
    "9001", "Synthetic Apple, Each", "$1.12", unit="$2.24/lb", weight_priced=True, condition="each (est.)"
)
PEAR = syn.Item("9002", "Synthetic Pear, 2 lb Bag", "$3.47")
PLUM = syn.Item("9003", "Synthetic Plum, 1 lb", "$2.98")


def two_pages(e: dict[str, Any], first: syn.Item, second: syn.Item) -> None:
    """One listing of 3 products on 2 pages: the apple's tile on each page, in this order."""
    served = {1: [first, PEAR], 2: [second, PLUM]}
    serve(
        e,
        {
            DIAPERING: lambda n: listing(
                served.get(n, []), page=n, max_page=2, total=3, cat=("Diapering", CRUMBS)
            )
        },
    )


def fields(e: dict[str, Any], run_id: str, key: str) -> dict[str, Any]:
    """The field provenance of the result tile a product's record is kept from."""
    with e["factory"]() as s:
        obs = s.scalars(
            select(ProductObservation).where(
                ProductObservation.run_id == run_id,
                ProductObservation.upc == key,
                ProductObservation.source == "card",
            )
        ).one()
        return dict((obs.provenance or {}).get("fields") or {})


@pytest.mark.parametrize("order", ["estimate_first", "estimate_last"])
def test_estimated_weight_wording_on_any_tile_excludes_the_whole_product(
    env: dict[str, Any],  # noqa: F811
    order: str,
) -> None:
    first, second = (ESTIMATED, PLAIN) if order == "estimate_first" else (PLAIN, ESTIMATED)
    two_pages(env, first, second)
    run_id, _ = run_diapering(env)
    recs = records(env, run_id)
    apple = recs["wm:9001"]
    assert apple.status == "excluded" and apple.reasons == ["APPROX_WEIGHT"]
    assert {"RELATIVE_PRICE", "SOLD_BY_WEIGHT"} <= set(apple.flags or [])
    trace = fields(env, run_id, "wm:9001")["_approx_weight"]
    assert (trace["field"], trace["text"], trace["value"]) == (
        "price_display_condition",
        "est.",
        "each (est.)",
    )
    assert trace["path"].endswith("priceInfo.priceDisplayCodes.priceDisplayCondition")
    with env["factory"]() as s:
        changed = [
            e.data["key"]
            for e in s.scalars(
                select(Event).where(Event.run_id == run_id, Event.code == "RECORD_STATE_CHANGED_IN_RUN")
            )
        ]
    # Estimate first: the later tile without wording keeps the exclusion, nothing changes. Estimate last: the
    # later tile with the wording decides the record again.
    assert changed == ([] if order == "estimate_first" else ["wm:9001"])
    # The products sold at a fixed price are kept.
    assert recs["wm:9002"].status == recs["wm:9003"].status == "valid"


def test_a_product_sold_by_weight_whose_tiles_show_no_estimate_is_kept(
    env: dict[str, Any],  # noqa: F811
) -> None:
    two_pages(env, PLAIN, PLAIN)
    run_id, _ = run_diapering(env)
    apple = records(env, run_id)["wm:9001"]
    assert apple.status == "valid" and not apple.reasons
    assert {"RELATIVE_PRICE", "SOLD_BY_WEIGHT"} <= set(apple.flags or [])
    assert "_approx_weight" not in fields(env, run_id, "wm:9001")
    assert (apple.record["regular_price"], apple.record["ppm"]) == ("1.12", "$2.24/lb")
