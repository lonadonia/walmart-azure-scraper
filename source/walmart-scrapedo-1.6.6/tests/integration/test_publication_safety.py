"""Safe publication through the real pipeline and its after-run publication path (SYNTHETIC pages,
injected faults; nothing reaches Scrape.do or Walmart).

Each test runs in its own throwaway database and data folder: an isolated namespace that cannot touch an
operational dataset. A complete run of the store is published first; a later run that is incomplete,
refused by the site, priced for another store, empty or suspiciously thin must not replace it. The
incomplete, empty and thin runs are assembled with the earlier run's products carried forward into their
export, and are refused all the same: carry-forward never hides missing coverage. The publication pointer,
the published bytes (latest.json, the manifest it names and that manifest's products.json) and the first
run's product observations are compared before and after. A run whose product pages stopped being read, a run
of mixed lineage and a run interrupted part-way are refused the same way, while one refused product page does
not cost the run its publication. An interrupted publication is retried once and replaces the dataset
atomically. With ``PUBLICATION_EVIDENCE_DIR`` set, each test writes its before/after
hashes there as JSON (the delivery's evidence of these checks).
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
import pytest
import yaml
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from tests import synthetic_walmart as syn
from tests.conftest import STORE_KEY
from tests.integration.test_operations import Env, _raise_sigterm_on, env  # noqa: F401  (env is a fixture)
from tests.mock_scrapedo import DIAPERING, MILK, PAGES, PRIMARY, SNACKS, listing
from walmart_headless import operations
from walmart_headless.acquisition import lineage
from walmart_headless.db.models import (
    CollectionSegment,
    ProductObservation,
    Publication,
    PublicationPointer,
    RecordRow,
    Store,
)

pytestmark = [pytest.mark.postgres]


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def snapshot(e: Env, first_run: str) -> dict[str, Any]:
    """The published state: pointer, publication rows, latest.json, the manifest it names and that
    manifest's products.json, and the first run's observations."""
    factory = sessionmaker(e.engine, expire_on_commit=False)
    with factory() as s:
        store = s.scalar(select(Store).where(Store.key == STORE_KEY))
        assert store is not None
        ptr = s.get(PublicationPointer, store.id)
        pubs = int(s.scalar(select(func.count()).select_from(Publication)) or 0)
        obs = sorted(
            (o.upc, o.observed_at.isoformat(), json.dumps(o.provenance, sort_keys=True, default=str))
            for o in s.scalars(select(ProductObservation).where(ProductObservation.run_id == first_run))
        )
        recs = sorted(
            (r.upc, r.status, r.record_sha256)
            for r in s.scalars(select(RecordRow).where(RecordRow.run_id == first_run))
        )
    latest = (e.data / "published" / STORE_KEY / "latest.json").read_bytes()
    body = json.loads(latest)
    manifest = (e.data / body["manifest_key"]).read_bytes()
    assert _sha(manifest) == body["manifest_sha256"]
    products = (e.data / json.loads(manifest)["files"]["products.json"]["key"]).read_bytes()
    return {
        "pointer": {
            "publication_id": ptr.publication_id if ptr else None,
            "version": ptr.version if ptr else None,
        },
        "publications": pubs,
        "published_run": body.get("run_id"),
        "latest_json_sha256": _sha(latest),
        "manifest_sha256": _sha(manifest),
        "products_sha256": _sha(products),
        "published_products": len(json.loads(products)),
        "first_run_observations_sha256": _sha(json.dumps(obs).encode()),
        "first_run_records_sha256": _sha(json.dumps(recs).encode()),
        "first_run_observations": len(obs),
    }


def _evidence(name: str, data: dict[str, Any]) -> None:
    out = os.environ.get("PUBLICATION_EVIDENCE_DIR")
    if out:
        Path(out).mkdir(parents=True, exist_ok=True)
        (Path(out) / f"{name}.json").write_text(json.dumps(data, indent=1, default=str), encoding="utf-8")


def _refuse(prefix: str) -> Callable[[str], httpx.Response | None]:
    def override(url: str) -> httpx.Response | None:
        if url.startswith(prefix):  # Walmart's own refusal page, delivered by the provider
            return httpx.Response(200, text=syn.CHALLENGE_PAGE, headers={"Scrape.do-Request-Cost": "10"})
        return None

    return override


def _other_store(url: str) -> httpx.Response | None:
    if url.startswith(MILK):  # a page priced for store 9999, not 3891
        item = syn.Item("7101", "Milk, Gallon, 128 fl oz", "$3.12", unit="2.4 ¢/fl oz")
        return httpx.Response(
            200,
            text=listing([item], page=1, max_page=1, total=1, store="9999"),
            headers={"Scrape.do-Request-Cost": "10"},
        )
    return None


FAULTS = ("incomplete", "site_refusal", "wrong_store", "empty", "thin")
CARRIES_FORWARD = ("incomplete", "empty", "thin")  # assembled: the export holds carried-forward rows


@pytest.mark.parametrize("fault", FAULTS)
def test_a_published_dataset_is_never_replaced_by_a_run_that_fails_its_checks(
    env: Env,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    code, _ = env.result("run", "--store", STORE_KEY)
    first = env.runs()[0]
    assert code == 0 and first.status == "published"
    before = snapshot(env, first.id)
    if fault == "incomplete":
        env.mock.remaining[PRIMARY] = 25  # robots, store page and two pages: the run stops part-way
    elif fault == "site_refusal":
        env.mock.page_override = _refuse(SNACKS)
    elif fault == "wrong_store":
        env.mock.page_override = _other_store
    elif fault == "empty":
        for key in (MILK, SNACKS, DIAPERING):
            monkeypatch.setitem(PAGES, key, [[]])
    elif fault == "thin":  # every Food product but one gone: far below the last complete run
        monkeypatch.setitem(PAGES, SNACKS, [[]])
    code2, _ = env.cli("run", "--store", STORE_KEY)
    second = env.runs()[-1]
    after = snapshot(env, first.id)
    factory = sessionmaker(env.engine, expire_on_commit=False)
    with factory() as s:
        carried = int(
            s.scalar(
                select(func.count())
                .select_from(RecordRow)
                .where(RecordRow.run_id == second.id, RecordRow.status == "historical")
            )
            or 0
        )
    _evidence(
        f"publication_refused_{fault}",
        {
            "fault": fault,
            "synthetic": True,
            "first_run": first.id,
            "second_run": second.id,
            "second_run_status": second.status,
            "second_run_stop_code": second.stop_code,
            "second_run_exit_code": code2,
            "second_run_carried_forward_rows": carried,
            "before": before,
            "after": after,
            "unchanged": before == after,
        },
    )
    assert second.id != first.id and second.status != "published"
    assert after == before  # pointer, publication rows, published bytes and first-run observations
    if fault in CARRIES_FORWARD:
        assert carried > 0  # the earlier run's products filled the export, and still the run was refused


def test_an_interrupted_publication_keeps_the_last_good_dataset_and_one_retry_publishes_atomically(
    env: Env,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    code, _ = env.result("run", "--store", STORE_KEY)
    first = env.runs()[0]
    assert code == 0 and first.status == "published"
    before = snapshot(env, first.id)
    real = operations.publish_run
    calls = {"n": 0}

    class Crash(Exception):
        pass

    def interrupted(*args: Any, **kwargs: Any) -> Any:
        calls["n"] += 1
        if calls["n"] == 1:

            def fault(stage: str) -> None:
                if stage == "inside_commit":
                    raise Crash(stage)

            return real(*args, **kwargs, fault=fault)
        return real(*args, **kwargs)

    monkeypatch.setattr(operations, "publish_run", interrupted)
    with pytest.raises(Crash):
        operations.after_run(operations.Context(env.config), STORE_KEY, _run_second(env))
    second = env.runs()[-1]
    middle = snapshot(env, first.id)
    assert middle == before and second.status == "validated"  # nothing half-published
    code, _ = env.result("publish", "--run", second.id)
    after = snapshot(env, first.id)
    _evidence(
        "publication_interrupted_then_retried",
        {
            "synthetic": True,
            "first_run": first.id,
            "second_run": second.id,
            "before": before,
            "after_interruption": middle,
            "after_retry": after,
            "retry_exit_code": code,
        },
    )
    assert code == 0 and after["published_run"] == second.id
    assert after["pointer"]["version"] == before["pointer"]["version"] + 1
    assert after["publications"] == before["publications"] + 1  # exactly one new publication, no duplicate
    assert after["first_run_observations_sha256"] == before["first_run_observations_sha256"]


def _reread_product_pages(e: Env) -> None:
    """The next run reads product pages again instead of reusing the first run's outcomes."""
    data = yaml.safe_load(e.config.read_text(encoding="utf-8"))
    collection = data["collections"][STORE_KEY]
    collection["detail"] = {**collection.get("detail", {}), "reuse_days": 0}
    e.config.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def test_a_run_whose_product_pages_stopped_is_refused_and_keeps_the_last_good_dataset(
    env: Env,  # noqa: F811
) -> None:
    code, _ = env.result("run", "--store", STORE_KEY)
    first = env.runs()[0]
    assert code == 0 and first.status == "published"
    before = snapshot(env, first.id)
    _reread_product_pages(env)
    env.mock.page_override = _refuse("https://www.walmart.com/ip/")
    code2, _ = env.cli("run", "--store", STORE_KEY)
    second = env.runs()[-1]
    after = snapshot(env, first.id)
    counts = second.counts or {}
    _evidence(
        "publication_refused_failed_detail",
        {
            "fault": "failed_detail",
            "synthetic": True,
            "first_run": first.id,
            "second_run": second.id,
            "second_run_status": second.status,
            "second_run_exit_code": code2,
            "detail_paused": counts.get("upc_detail_paused"),
            "before": before,
            "after": after,
            "unchanged": before == after,
        },
    )
    assert counts.get("upc_detail_paused")  # the path stopped after the configured number of refusals
    assert second.status == "rejected" and code2 == int(operations.Exit.REJECTED)
    assert (counts.get("gates") or {}).get("G2") == "FAIL"
    assert after == before
    code3, _ = env.cli("publish", "--run", second.id)  # no operator's command publishes it either
    assert code3 == int(operations.Exit.REJECTED) and snapshot(env, first.id) == before


def test_one_refused_product_page_is_not_a_reason_to_refuse_the_run(
    env: Env,  # noqa: F811
) -> None:
    """A field that is optional in the source stays empty with its reason, and the run still publishes: the
    protection against a stopped path must not turn into a blanket refusal of every missing value."""
    code, _ = env.result("run", "--store", STORE_KEY)
    first = env.runs()[0]
    assert code == 0 and first.status == "published"
    before = snapshot(env, first.id)
    _reread_product_pages(env)

    def refuse_one(url: str) -> httpx.Response | None:
        if "/ip/" in url and url.rstrip("/").rsplit("/", 1)[-1] == "7201":
            return httpx.Response(200, text=syn.CHALLENGE_PAGE, headers={"Scrape.do-Request-Cost": "1"})
        return None

    env.mock.page_override = refuse_one
    code2, _ = env.result("run", "--store", STORE_KEY)
    second = env.runs()[-1]
    after = snapshot(env, first.id)
    assert code2 == 0 and second.status == "published"
    assert not (second.counts or {}).get("upc_detail_paused")
    assert (
        after["published_run"] == second.id
        and after["pointer"]["version"] == before["pointer"]["version"] + 1
    )
    assert after["first_run_observations_sha256"] == before["first_run_observations_sha256"]
    code3, dispositions = env.result("field-dispositions", "--run", second.id)
    assert code3 == 0
    rows = [r for r in dispositions["rows"] if r["url"].rstrip("/").rsplit("/", 1)[-1] == "7201"]
    assert len(rows) == 1  # the product is exported once, under one identity
    assert rows[0]["upc"]["disposition"] == "blocked" and rows[0]["upc"]["value"] == ""
    _evidence(
        "publication_allowed_one_failed_detail",
        {
            "fault": "one_failed_detail",
            "synthetic": True,
            "first_run": first.id,
            "second_run": second.id,
            "second_run_status": second.status,
            "before": before,
            "after": after,
        },
    )


def test_a_run_with_mixed_lineage_is_refused_even_on_a_test_target(
    env: Env,  # noqa: F811
) -> None:
    code, _ = env.result("run", "--store", STORE_KEY)
    first = env.runs()[0]
    assert code == 0 and first.status == "published"
    before = snapshot(env, first.id)
    second = _run_second(env)
    factory = sessionmaker(env.engine, expire_on_commit=False)
    with factory() as s:
        # This process's pages are substituted, so a segment of the other origin is the mixed case.
        seg = s.scalars(select(CollectionSegment).where(CollectionSegment.run_id == second)).first()
        assert seg is not None
        seg.stats = {**(seg.stats or {}), "lineage": {"transport": "network", "replaced": []}}
        s.commit()
        lin = lineage.of_run(s, second)
    assert lin.problems and lin.lineage == lineage.SUBSTITUTED
    code2, _ = env.cli("publish", "--run", second)
    after = snapshot(env, first.id)
    _evidence(
        "publication_refused_mixed_lineage",
        {
            "fault": "mixed_lineage",
            "synthetic": True,
            "first_run": first.id,
            "second_run": second,
            "problems": list(lin.problems),
            "publish_exit_code": code2,
            "before": before,
            "after": after,
            "unchanged": before == after,
        },
    )
    assert code2 == int(operations.Exit.REJECTED)
    assert after == before


def test_an_interrupted_run_keeps_the_last_good_dataset_until_its_resume_completes(
    env: Env,  # noqa: F811
) -> None:
    code, _ = env.result("run", "--store", STORE_KEY)
    first = env.runs()[0]
    assert code == 0 and first.status == "published"
    before = snapshot(env, first.id)
    env.mock.page_override = _raise_sigterm_on(SNACKS)
    code2, _ = env.cli("run", "--store", STORE_KEY)
    second = env.runs()[-1]
    middle = snapshot(env, first.id)
    assert code2 == int(operations.Exit.INTERRUPTED) and second.status == "interrupted"
    assert middle == before
    code3, _ = env.cli("publish", "--run", second.id)  # an unfinished run cannot be published by hand
    assert code3 == int(operations.Exit.REJECTED) and snapshot(env, first.id) == before
    env.mock.page_override = None
    code4, _ = env.result("resume", "--store", STORE_KEY)
    after = snapshot(env, first.id)
    _evidence(
        "publication_interrupted_run_then_resumed",
        {
            "fault": "interrupted_run",
            "synthetic": True,
            "first_run": first.id,
            "second_run": second.id,
            "interrupted_exit_code": code2,
            "manual_publish_exit_code": code3,
            "resume_exit_code": code4,
            "before": before,
            "after_interruption": middle,
            "after_resume": after,
            "unchanged_until_resume": before == middle,
        },
    )
    assert code4 == 0 and after["published_run"] == second.id
    assert after["pointer"]["version"] == before["pointer"]["version"] + 1
    assert after["first_run_observations_sha256"] == before["first_run_observations_sha256"]


def _run_second(e: Env) -> str:
    """A second complete run, collected and validated but not published yet (its publication is driven by
    the test)."""
    data = json.loads(json.dumps(operations.Context(e.config).config.collector.publish.model_dump()))
    assert data["auto"] is True
    e.edit()  # unchanged configuration
    cfg = e.config.read_text(encoding="utf-8")
    e.config.write_text(cfg.replace("  auto: true", "  auto: false"), encoding="utf-8")
    code, _ = e.result("run", "--store", STORE_KEY)
    e.config.write_text(cfg, encoding="utf-8")
    run = e.runs()[-1]
    assert code == 0 and run.status == "validated", (code, run.status)
    return run.id
