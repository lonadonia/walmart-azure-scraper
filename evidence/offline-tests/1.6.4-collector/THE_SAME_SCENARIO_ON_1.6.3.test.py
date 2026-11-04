"""Run only in the clean 1.6.3 copy (not part of any release): the scenario of the 1.6.4 integration test,
asserting what release 1.6.3 does with it."""

from typing import Any

from tests import synthetic_walmart as syn
from tests.integration.test_coverage_and_assortment import SHIPPING_ONLY, env, run_food, serve  # noqa: F401
from tests.mock_scrapedo import MILK
from walmart_headless.db.models import Run


def test_on_1_6_3_an_empty_pickup_grid_beside_a_carousel_stops_the_run(env: dict[str, Any]) -> None:  # noqa: F811
    serve(env, {MILK: lambda n: syn.empty_pickup_grid_page(SHIPPING_ONLY, store="3891", title="Milk")})
    run_id, status = run_food(env)
    with env["factory"]() as s:
        run = s.get(Run, run_id)
        assert run is not None
        print("STATUS", status, "STOP", run.stop_code, "DETAIL", run.stop_detail)
        assert run.stop_code == "ABNORMAL_RESULT"
        assert "the page reports results but shows no product" in (run.stop_detail or "")
