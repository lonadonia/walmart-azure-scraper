"""OWNER DRILL (not part of the release; copied beside the edition's own integration tests to run): the ordinary
operator commands in the order an operator uses them, through the collector's command line (``main``), against
the in-memory mock of Scrape.do serving SYNTHETIC Walmart pages (no request leaves the process) and the
PostgreSQL database the integration tests are given. Each command, its exit code and what it returned are
written to the transcript named by DRILL_TRANSCRIPT (JSON lines).

Steps: the schema check; a run (start); status of the store and of the run (where its files are kept); export of
the run; a run paused by its execution limit and resumed by the next execution; a refused automatic publication
(ERROR, exit 6) and a manual publish of that run (refused again, exit 6), the last-good pointer unchanged; a run
whose provider credits run out (partial, never published) and the export of the store's published dataset (the
last good one); a second configured store that is never collected while the first one is."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx
import pytest
import yaml
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from tests.conftest import STORE_KEY
from tests.integration.test_operations import (  # noqa: F401 - env is the command-line fixture
    Env,
    _ExecutionClock,
    _slow_first_page,
    env,
)
from tests.mock_scrapedo import MILK, PRIMARY
from walmart_headless.db.models import Store

pytestmark = [pytest.mark.postgres]
OTHER = "walmart-2585-pickup"


class Transcript:
    def __init__(self, env: Env) -> None:  # noqa: F811
        self.env = env
        self.path = Path(os.environ.get("DRILL_TRANSCRIPT", str(env.data.parent / "drill.jsonl")))
        self.n = 0

    def files(self) -> list[str]:
        return sorted(str(p.relative_to(self.env.data)).replace("\\", "/") for p in self.env.data.rglob("*") if p.is_file())

    def latest(self) -> str | None:
        p = self.env.data / "published" / STORE_KEY / "latest.json"
        return json.loads(p.read_text("utf-8"))["run_id"] if p.is_file() else None

    def step(self, what: str, *args: str, expect: int, keep: tuple[str, ...] = ()) -> tuple[int, Any]:
        code, lines = self.env.cli(*args)
        result = lines[-1].get("result") if lines and isinstance(lines[-1], dict) else None
        events = [
            {k: x.get(k) for k in ("level", "event", "message", "exit_code") if k in x}
            for x in lines
            if isinstance(x, dict) and x.get("event") in ("PUBLICATION_REFUSED", "RUN_FINISHED", "RUN_PAUSED",
                                                          "SEGMENT_DURATION_LIMIT", "RUN_STOPPED", "PUBLISHED")
        ]
        self.n += 1
        entry = {
            "n": self.n,
            "step": what,
            "command": "walmart-collector " + " ".join(args),
            "exit": code,
            "expected_exit": expect,
            "result_keys": sorted(result) if isinstance(result, dict) else None,
            "result": {k: result.get(k) for k in keep if k in result} if isinstance(result, dict) and keep else None,
            "result_excerpt": self.clean(json.dumps(result, default=str))[:3000] if result is not None else None,
            "events": events,
            "published_run": self.latest(),
        }
        line = self.clean(json.dumps(entry, default=str))
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        assert code == expect, line
        return code, result

    def clean(self, text: str) -> str:
        """The drill's temporary folder, in each form the JSON text can hold it, is shown as <tmp>."""
        base = self.env.data.parent
        forms = {str(base), base.as_posix(), json.dumps(str(base))[1:-1], json.dumps(base.as_posix())[1:-1]}
        for form in sorted(forms, key=len, reverse=True):
            text = text.replace(form, "<tmp>")
        return text


def test_the_operator_commands_in_order(env: Env, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:  # noqa: F811
    t = Transcript(env)
    # A second store, configured and enabled, that this drill never collects.
    stores_file = env.config.parent / "stores.yaml"
    stores = yaml.safe_load(stores_file.read_text("utf-8"))
    other = dict(stores["stores"][0], key=OTHER, location_id="2585", store_number="2585",
                 expected={"display_name": "Walmart #2585 (SYNTHETIC drill store)", "postal_code": "60085",
                           "address_line1": "1 Drill Way"},
                 store_page_url="https://www.walmart.com/store/2585-drill",
                 notes="SYNTHETIC second store of the owner drill: configured, never collected")
    stores["stores"].append(other)
    stores_file.write_text(yaml.safe_dump(stores, sort_keys=False), encoding="utf-8")
    sent: list[str] = []
    handler = env.mock.handler

    def recording(request: httpx.Request) -> httpx.Response:
        sent.append(str(request.url.params.get("storeid") or ""))
        return handler(request)

    monkeypatch.setattr(env.mock, "handler", recording)

    t.step("schema and configuration check", "validate-config", "--check-db", expect=0, keep=("database", "stores"))
    t.step("load the stores and the category CSV", "sync-config", expect=0)
    _, first = t.step("start a run (complete)", "run", "--store", STORE_KEY, expect=0,
                      keep=("run_id", "status", "dataset", "records", "stop_code"))
    _, st = t.step("status of the stores", "status", expect=0, keep=("stores",))
    keys = [s.get("store") for s in st["stores"]]
    assert STORE_KEY in keys and OTHER in keys
    run1 = env.runs()[-1]
    t.step("status of the run (its statistics and export files)", "status", "--run", run1.id, expect=0,
           keep=("run", "exports", "files", "statistics"))
    t.step("export the run", "export", "--run", run1.id, "--out", str(tmp_path / "export_run1"), expect=0,
           keep=("run_id", "files", "out"))

    # Pause and resume: one execution limited to 60 minutes; the first listing page "takes" an hour.
    from walmart_headless.collection import base as base_mod

    clock = _ExecutionClock()
    monkeypatch.setattr(base_mod, "monotonic", clock)
    env.edit(limits={"max_run_minutes": 2880, "max_segment_minutes": 60})
    env.mock.page_override = _slow_first_page(clock, MILK, 3601)
    t.step("a run paused by its execution limit (resumable)", "run", "--store", STORE_KEY, expect=75,
           keep=("run_id", "status", "stop_code"))
    paused = env.runs()[-1]
    assert paused.status == "interrupted" and paused.stop_code == "SEGMENT_DURATION_LIMIT"
    t.step("status while paused", "status", "--store", STORE_KEY, expect=0, keep=("stores",))
    env.mock.page_override = None
    t.step("resume: the next execution continues the same run", "resume", "--store", STORE_KEY, expect=0,
           keep=("run_id", "status", "dataset"))
    resumed = env.runs()[-1]
    assert resumed.id == paused.id and resumed.status == "published"
    good = t.latest()
    assert good == paused.id

    # A refused automatic publication: the pages did not come from the network and this is not a test target.
    settings = env.config.parent / "settings.yaml"
    text = settings.read_text(encoding="utf-8")
    settings.write_text(text.replace("publication: { test_target: true }", "publication: { test_target: false }"),
                        encoding="utf-8")
    t.step("a run whose automatic publication is refused (ERROR, exit 6)", "run", "--store", STORE_KEY, expect=6,
           keep=("run_id", "status", "publication"))
    refused = env.runs()[-1]
    assert refused.status == "validated" and t.latest() == good
    t.step("publish the refused run by hand (refused again)", "publish", "--run", refused.id, expect=6)
    assert t.latest() == good
    settings.write_text(text, encoding="utf-8")

    # A failed run never replaces the published dataset; the store's export is the last good one.
    # robots, store page and two pages, then nothing left (release 1.6.8: one credit more for the Dairy & Eggs
    # category page the SYNTHETIC Food page links, as in test_operations.py of commit 85c29e7)
    env.mock.remaining[PRIMARY] = 26
    t.step("a run whose provider credits run out (partial, never published)", "run", "--store", STORE_KEY, expect=4,
           keep=("run_id", "status", "stop_code", "dataset"))
    assert t.latest() == good
    _, exported = t.step("export the store's published dataset (the last good run)", "export", "--store", STORE_KEY,
                         "--out", str(tmp_path / "export_published"), expect=0, keep=("run_id", "files"))
    assert exported["run_id"] == good
    t.step("status at the end", "status", "--store", STORE_KEY, expect=0, keep=("stores",))

    # Store isolation: only the requested store's id was ever sent, the other store has no run and no folder.
    assert set(x for x in sent if x) == {"3891"}, sorted(set(sent))
    assert not (env.data / "runs" / OTHER).exists() and not (env.data / "published" / OTHER).exists()
    with sessionmaker(env.engine)() as s:
        other_id = s.scalar(select(Store.id).where(Store.key == OTHER))
    assert other_id is not None and not [r for r in env.runs() if r.store_id == other_id]
    with t.path.open("a", encoding="utf-8") as f:
        f.write(t.clean(json.dumps({"n": t.n + 1, "step": "store isolation and storage location",
                            "store_ids_sent": sorted(set(x for x in sent if x)),
                            "requests_seen_by_the_mock": len(sent),
                            "other_store_runs": [r.id for r in env.runs() if r.store_id == other_id],
                            "data_dir_files": t.files()})) + "\n")
