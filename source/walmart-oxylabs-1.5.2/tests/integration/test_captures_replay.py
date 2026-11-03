"""Authentic Walmart pages captured by the earlier live run W1 (tests/captures/w1_20261021) replayed
offline through the collector's whole pipeline: the store page, robots.txt and two Diapering result pages
are served by the Scrape.do mock exactly as Walmart returned them. The collector must find the store and
Pickup context in Walmart's own data and export the products W1 exported, with the same values."""

from __future__ import annotations

import gzip
import json
import shutil
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
import yaml
from sqlalchemy import Engine, select
from sqlalchemy.orm import sessionmaker

from tests.conftest import CAPTURES, CONFIG, STORE_KEY
from tests.mock_scrapedo import PRIMARY, MockScrapeDo
from walmart_headless.acquisition import scrapedo as sd
from walmart_headless.checks.source_check import item_id_of
from walmart_headless.cli import main
from walmart_headless.db.models import RecordRow, Run, StoreAttestation

pytestmark = [pytest.mark.postgres, pytest.mark.captures]

W1 = CAPTURES / "w1_20261021"
DIAPERING_PATH = "/browse/diapering/5427_486190"
# Fields that depend on when and in which category a product was first met, not on the page.
CONTEXT_FIELDS = ("crawl_date", "category", "sub_category")
SPARK = (
    "https://i5.walmartimages.com/dfw/63fd9f59-14e2/9d304ce6-96de-4331-b8ec-c5191226d378/v1/spark-icon.svg"
)


class CapturedWalmart(MockScrapeDo):
    """Scrape.do's API (cost headers, /info) answering with the captured pages."""

    def page(self, path: str, request: httpx.Request) -> tuple[str, int]:
        u = urlsplit(request.url.params.get("url", ""))
        if path == "/" and u.path == "/robots.txt":
            return (W1 / "robots.txt").read_text(encoding="utf-8"), 200
        if path == "/" and u.path == "/store/3891-waukegan-il":
            return gzip.decompress((W1 / "store_page.html.gz").read_bytes()).decode("utf-8"), 200
        if path == "/plugin/walmart/store" and u.path == DIAPERING_PATH:
            n = int(parse_qs(u.query).get("page", ["1"])[0])
            f = W1 / f"diapering_page{n}.html.gz"
            if f.is_file():
                return gzip.decompress(f.read_bytes()).decode("utf-8"), 200
        return "not found", 404


@pytest.fixture
def replay(
    migrated_engine: Engine, pg_url: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> dict[str, Any]:
    cfg_dir = tmp_path / "config"
    shutil.copytree(CONFIG, cfg_dir)
    data = yaml.safe_load((cfg_dir / "collector.yaml").read_text(encoding="utf-8"))
    # W1 read no product pages, and these captures hold none: the comparison is of the result pages alone.
    # (Since 1.5.0 repeated failures of the product-page path fail the run's access check, so the path is
    # switched off here rather than left to fail against pages that were never captured.)
    data["collections"][STORE_KEY].update(
        categories=[4],
        limits={"max_pages_per_listing": 2},
        follow_up={"sponsored": False, "variants": False},
        detail={"enabled": False},
    )
    (cfg_dir / "collector.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    monkeypatch.setenv("WALMART_COLLECTOR_DATABASE_URL", pg_url)
    monkeypatch.setenv(sd.ENV_KEY, PRIMARY)
    monkeypatch.setenv("WALMART_COLLECTOR_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(sd, "INFO_MIN_INTERVAL_S", 0.0)
    mock = CapturedWalmart()
    monkeypatch.setattr(
        sd.Transport, "client_factory", lambda: httpx.AsyncClient(transport=httpx.MockTransport(mock.handler))
    )
    return {"config": cfg_dir / "collector.yaml", "engine": migrated_engine, "data": tmp_path / "data"}


def test_the_captured_pages_give_the_records_w1_exported(
    replay: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["--config", str(replay["config"]), "run", "--store", STORE_KEY])
    capsys.readouterr()
    assert code == 0
    factory = sessionmaker(replay["engine"], expire_on_commit=False)
    with factory() as s:
        [run] = list(s.scalars(select(Run)))
        assert run.config_snapshot["pilot"] is True and run.counts["canary"]["status"] == "passed"
        checks = {
            c["check"]: c["status"]
            for a in s.scalars(select(StoreAttestation).where(StoreAttestation.run_id == run.id))
            for c in a.checks["checks"]
        }
    # Walmart's own data on the captured pages names store 3891 and Pickup.
    assert checks["page_location_store"] == "PASS" and checks["page_intent"] == "PASS"
    assert checks["store_page_checked"] == "PASS"
    exports = replay["data"] / "runs" / STORE_KEY / run.id / "exports"
    ours = {item_id_of(r["url"]): r for r in json.loads((exports / "products.json").read_text("utf-8"))}
    w1 = {item_id_of(r["url"]): r for r in json.loads((W1 / "w1_exported_records.json").read_text("utf-8"))}
    with factory() as s:
        statuses = {
            r.upc: (r.status, r.reasons, r.flags)
            for r in s.scalars(select(RecordRow).where(RecordRow.run_id == run.id))
        }
    missing = {i: statuses.get(f"wm:{i}") for i in set(w1) - set(ours)}
    assert set(ours) == set(w1), (sorted(set(ours) - set(w1)), missing)
    differences = {
        item: {
            k: (ours[item][k], w1[item][k])
            for k in ours[item]
            if k not in CONTEXT_FIELDS and ours[item][k] != w1[item][k]
        }
        for item in ours
    }
    # Release 1.2.0 reads a size written inside the title, which W1's parser left empty: the only allowed
    # difference, and the size is the title's own text, unchanged.
    sizes_added = {
        item: d.pop("weight") for item, d in differences.items() if d.get("weight", ("", "x"))[1] == ""
    }
    # Release 1.2.1 reads the logo the store page's header shows, which W1 left empty (the same image on
    # the captured store page): https://i5.walmartimages.com/.../spark-icon.svg.
    logos = {d.pop("store_logo") for d in differences.values() if "store_logo" in d}
    assert logos == {(SPARK, "")}
    assert all(ours[item]["weight"] in ours[item]["product_title"] for item in sizes_added)
    assert sizes_added  # the captures hold such titles ("1.76 oz", "24-Pack", ...)
    # Release 1.5.1 keeps the multipack the title states beside the size ("(2 pack) Baby Dove ...,13 fl oz"):
    # W1's size stays as it was, after the pack. Only this one authentic product of the captures changes.
    multipack = {
        item: differences[item].pop("weight")
        for item in ours
        if "pack" in ours[item]["weight"].split(",")[0] and "weight" in differences[item]
    }
    assert multipack == {"18030205038": ("2 pack, 13 fl oz", "13 fl oz")}
    assert not {k: v for k, v in differences.items() if v}
    assert all(r["category"] == "Diapering" for r in ours.values())
    capsys.readouterr()
    code = main(["--config", str(replay["config"]), "validate-export", "--run", run.id])
    out = capsys.readouterr().out
    result = [json.loads(x) for x in out.splitlines() if x.startswith("{")][-1]["result"]
    assert code == 0 and result["source_check"]["summary"]["verified"] == len(ours)
