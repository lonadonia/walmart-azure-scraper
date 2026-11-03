"""Release 1.3.0 rules that need no database: the variant siblings a result tile names (only real items with
their own link), a product page's store context and category evidence, the stored-page sanitizer keeping
category paths, the follow-up and parallel configuration, the coverage rule without a tolerance threshold,
and the command line's provider options. Every page value here is SYNTHETIC."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from tests.conftest import CONFIG, STORE_KEY
from walmart_headless.cli import build_parser, main
from walmart_headless.collection.config import (
    CollectionConfig,
    DetailConfig,
    FollowSeed,
    FollowUpConfig,
    Limits,
    ParallelConfig,
)
from walmart_headless.config_file import LoadedConfig
from walmart_headless.core.settings import CoverageSettings, load_settings
from walmart_headless.sites.walmart import page_data as wpd
from walmart_headless.sites.walmart.sanitize import redact


def tile(**extra: Any) -> dict[str, Any]:
    return {"usItemId": "9001", "name": "Diapers A, Size 1", "canonicalUrl": "/ip/Diapers-A/9001", **extra}


def test_variant_siblings_are_the_items_a_tile_links_never_a_label() -> None:
    item = tile(
        variantCriteria=[
            {
                "name": "diaper_size",
                "variantList": [
                    {"name": "Size 1", "selectedProduct": {"usItemId": "9001", "canonicalUrl": "/ip/a/9001"}},
                    {
                        "name": "Size 2",
                        "availabilityStatus": "out_of_stock",
                        "selectedProduct": {"usItemId": "9101", "canonicalUrl": "/ip/Diapers-A-Size-2/9101"},
                    },
                    {"name": "Size 3", "selectedProduct": {"canonicalUrl": "/ip/Diapers-A-Size-3/9102"}},
                    {"name": "More sizes", "selectedProduct": {}},
                    {"name": "No link", "selectedProduct": {"usItemId": "9103"}},
                ],
            },
            {
                "id": "count",
                "variantList": [{"displayName": "3 Pack", "usItemId": "9104", "canonicalUrl": "/ip/x/9104"}],
            },
        ]
    )
    refs = wpd.variant_refs(item)
    assert [(r.item_id, r.criterion, r.value, r.availability) for r in refs] == [
        ("9101", "diaper_size", "Size 2", "OUT_OF_STOCK"),
        ("9102", "diaper_size", "Size 3", ""),  # the id from its own link
        ("9104", "count", "3 Pack", ""),
    ]
    assert refs[0].url == "https://www.walmart.com/ip/Diapers-A-Size-2/9101"
    assert wpd.variant_refs(tile()) == ()


def product_nd(**product: Any) -> dict[str, Any]:
    return {"props": {"pageProps": {"initialData": {"data": {"product": {"usItemId": "9201", **product}}}}}}


def test_a_product_page_states_its_store_and_the_category_it_is_filed_under() -> None:
    pp = wpd.product_page(
        product_nd(
            name="Sponsored Diapers D",
            location={
                "storeIds": ["3891"],
                "pickupLocation": {"storeId": "3891"},
                "intent": "pickup",
                "postalCode": "60085",
            },
            category={
                "categoryPathId": "0:5427:486190:1101406",
                "path": [
                    {"name": "Baby", "url": "/cp/baby/5427"},
                    {"name": "Diapers", "url": "/browse/x/5427_486190_1101406"},
                ],
            },
            fulfillmentOptions=[
                {"type": "PICKUP", "availabilityStatus": "IN_STOCK", "locationText": "Waukegan"}
            ],
        )
    )
    assert pp is not None and pp.item is not None
    assert (pp.page_item, pp.store_ids, pp.pickup_store, pp.intent) == ("9201", ("3891",), "3891", "PICKUP")
    assert pp.under("5427_486190") == (True, "categoryPathId 0:5427:486190:1101406")
    assert pp.under("5427_486190_1101406")[0] is True
    # The ids in order, never a shared prefix of another id or an id out of order.
    assert pp.under("5427_48619")[0] is False and pp.under("486190_5427")[0] is False
    assert pp.under("976759_976793_9756351", "Fresh Fruits")[0] is False
    by_name = wpd.product_page(product_nd(category={"path": [{"name": "Baby"}, {"name": "Diapering"}]}))
    assert by_name is not None and by_name.under("5427_486190", "Diapering") == (
        True,
        "breadcrumb Baby > Diapering",
    )
    bare = wpd.product_page(product_nd())
    assert bare is not None and bare.under("5427_486190", "Diapering") == (
        False,
        "the page states no category path",
    )
    assert wpd.product_page({"props": {}}) is None


def test_the_sanitizer_keeps_category_paths_and_still_redacts_addresses() -> None:
    data = {
        "category": {"categoryPathId": "0:976759:976793:9756351"},
        "client": {
            "ip": "203.0.113.7",
            "ip6": "2001:db8::1",
            "full": "2001:0db8:0000:0000:0000:ff00:0042:8329",
        },
    }
    n = redact(data)
    assert data["category"]["categoryPathId"] == "0:976759:976793:9756351"
    assert n == 3 and "203.0.113.7" not in json.dumps(data) and "2001:db8::1" not in json.dumps(data)


def test_follow_up_seeds_parallel_workers_and_the_provider_are_validated() -> None:
    seed = FollowSeed(
        kind="variant",
        item_id="19700114741",
        url="https://www.walmart.com/ip/Pumpkin-Light/19700114741",
        listing_id="976759_976793_8910423",
        named_by="19921256834",
    )
    cfg = CollectionConfig(
        provider="oxylabs", follow_up=FollowUpConfig(seeds=[seed]), parallel=ParallelConfig(workers=2)
    )
    again = CollectionConfig.model_validate(cfg.model_dump(mode="json"))
    assert again.follow_up.seeds[0].item_id == "19700114741" and again.parallel.workers == 2
    for bad in (
        {"item_id": "12a"},
        {"url": "https://example.com/ip/x/1"},
        {"listing_id": "fresh-fruits"},
        {"kind": "label"},
    ):
        with pytest.raises(ValidationError):
            FollowSeed.model_validate({**seed.model_dump(), **bad})
    with pytest.raises(ValidationError):
        ParallelConfig(workers=9)
    with pytest.raises(ValidationError):
        CollectionConfig.model_validate({"provider": "another"})


def test_a_listing_is_complete_only_at_its_reported_total() -> None:
    assert load_settings(CONFIG / "settings.yaml").coverage.node_min_coverage_ratio == 1.0
    with pytest.raises(ValidationError):
        CoverageSettings(node_min_coverage_ratio=0.98)


def test_the_command_line_takes_the_provider_workers_and_ceilings() -> None:
    p = build_parser()
    a = p.parse_args(
        ["run", "--store", "s", "--provider", "oxylabs", "--workers", "2", "--follow-up-pages", "5"]
    )
    assert (a.provider, a.workers, a.follow_up_pages) == ("oxylabs", 2, 5)
    assert p.parse_args(["resume", "--store", "s", "--workers", "2"]).workers == 2
    c = p.parse_args(
        [
            "set-ceiling",
            "--provider",
            "oxylabs",
            "--submissions",
            "12",
            "--usd",
            "0.05",
            "--minutes",
            "15",
            "--basis",
            "probe",
        ]
    )
    assert (c.provider, c.submissions, c.usd, c.minutes) == ("oxylabs", 12, 0.05, 15.0)
    assert p.parse_args(["set-budget", "--usd", "1.5", "--basis", "b"]).usd == 1.5
    assert p.parse_args(["coverage-report", "--run", "r", "--out", "x"]).out == Path("x")
    with pytest.raises(SystemExit):
        p.parse_args(["run", "--store", "s", "--provider", "classic"])


def test_validate_config_requires_the_oxylabs_key_only_for_a_store_that_uses_it(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    secret = tmp_path / "oxylabs.env"
    secret.write_text("OXYLABS_API: " + "K" * 44 + "\n", encoding="utf-8")
    monkeypatch.setenv("OXYLABS_WEB_API_KEY_FILE", str(secret))
    monkeypatch.setenv("SCRAPEDO_API_KEY", "9" * 32)
    capsys.readouterr()
    code = main(["--config", str(CONFIG / "collector.yaml"), "validate-config", "--require-credentials"])
    out = capsys.readouterr().out
    assert code == 0 and "K" * 44 not in out and "9" * 32 not in out
    result = [json.loads(x) for x in out.splitlines() if x.startswith("{")][-1]["result"]
    oxy = result["environment"]["oxylabs_key"]
    assert oxy["configured"] is True and oxy["source"] == "OXYLABS_WEB_API_KEY_FILE"
    assert "Classic" in oxy["api"]


def test_every_page_budget_and_scope_limit_makes_a_run_a_pilot() -> None:
    """Release 1.3.1: a follow-up or detail page budget narrows a run like a scope limit (1.3.0 counted only
    the scope limits), so a run it cut short is a pilot, never published as the store's complete dataset."""
    production = LoadedConfig(CONFIG / "collector.yaml").collection(STORE_KEY)
    assert production.pilot_budgets() == {} and not production.bounded()
    assert CollectionConfig().pilot_budgets() == {}
    cases = {
        "follow_up.max_pages": CollectionConfig(follow_up=FollowUpConfig(max_pages=60)),
        "follow_up.variants": CollectionConfig(follow_up=FollowUpConfig(variants=False)),
        "detail.max_per_run": CollectionConfig(detail=DetailConfig(max_per_run=5)),
        "detail.enabled": CollectionConfig(detail=DetailConfig(enabled=False)),
        "limits.max_pages_per_listing": CollectionConfig(limits=Limits(max_pages_per_listing=2)),
    }
    for name, cfg in cases.items():
        assert list(cfg.pilot_budgets()) == [name] and cfg.bounded(), name
    assert CollectionConfig(pdp_sample=3).pilot_budgets() == {"detail.max_per_run": 3}
    assert CollectionConfig(follow_up=FollowUpConfig(max_pages=60)).pilot_budgets() == {
        "follow_up.max_pages": 60
    }
