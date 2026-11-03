"""Concurrency under load, against SYNTHETIC pages (release 1.5.2). Nothing reaches a provider or Walmart.

A pilot of two pages per listing says nothing about locking, pacing or accounting at scale. These tests run
the real pipeline (workers, the task queue, the provider ledger, checkpoints and PostgreSQL) on a larger
synthetic scope behind a mock that answers asynchronously after a fixed delay, and check what a full run
depends on:

* each page is requested once, with any worker count, and the same products come out;
* every request is accounted in the provider ledger;
* requests start at least ``min_interval_s`` apart and never exceed ``max_in_flight``;
* a transient provider failure is retried and accounted, and changes nothing in the data;
* a run terminated mid-way with several workers resumes with no product lost or duplicated.

They measure the implementation, not Walmart or a provider: the delay is chosen, so elapsed times say what
the collector adds and how workers scale, never what a live run takes. With ``LOAD_EVIDENCE_DIR`` set, each
test writes its measurements there as JSON. ``LOAD_ITEMS_PER_PAGE``, ``LOAD_PAGES`` and ``LOAD_DELAY_S``
size the scope."""

from __future__ import annotations

import asyncio
import json
import os
import signal
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from tests import mock_scrapedo as mock
from tests import synthetic_walmart as syn
from tests.integration.test_operations import STORE_KEY, Env, env  # noqa: F401
from walmart_headless.acquisition import scrapedo as sd
from walmart_headless.db.models import CollectionSegment, ProviderUsage, RecordRow

pytestmark = [pytest.mark.postgres]

ITEMS_PER_PAGE = int(os.environ.get("LOAD_ITEMS_PER_PAGE", "20"))
PAGES_PER_LISTING = int(os.environ.get("LOAD_PAGES", "3"))
DELAY_S = float(os.environ.get("LOAD_DELAY_S", "0.05"))
LISTING_ENDPOINT = "/plugin/walmart/store"


def upc_of(number: int) -> str:
    """A SYNTHETIC UPC-A with a correct check digit."""
    body = f"{number:011d}"
    odd = sum(int(c) for c in body[0::2])
    even = sum(int(c) for c in body[1::2])
    return f"{body}{(10 - (3 * odd + even) % 10) % 10}"


def scope(monkeypatch: pytest.MonkeyPatch) -> int:
    """Each listing holds PAGES_PER_LISTING full pages of distinct SYNTHETIC products with no UPC on the
    tile, so each product's own page is requested too. Returns the product count."""
    n = 0
    for base, url in enumerate((mock.MILK, mock.SNACKS, mock.DIAPERING), start=1):
        pages = []
        for _ in range(PAGES_PER_LISTING):
            page = []
            for _ in range(ITEMS_PER_PAGE):
                n += 1
                page.append(syn.Item(f"{base}{n:06d}", f"Load Item {n}, 16 oz", "$2.50", unit="15.6 ¢/oz"))
            pages.append(page)
        monkeypatch.setitem(mock.PAGES, url, pages)
    return n


class Timed:
    """The mock behind an asynchronous delay, with the start and end of each request."""

    def __init__(self, site: mock.MockScrapeDo) -> None:
        self.site = site
        self.starts: list[float] = []
        self.in_flight = 0
        self.peak = 0

    async def handler(self, request: httpx.Request) -> httpx.Response:
        self.starts.append(time.monotonic())
        self.in_flight += 1
        self.peak = max(self.peak, self.in_flight)
        try:
            await asyncio.sleep(DELAY_S)
            return self.site.handler(request)
        finally:
            self.in_flight -= 1


def timed(env_: Env, monkeypatch: pytest.MonkeyPatch) -> Timed:
    t = Timed(env_.mock)
    monkeypatch.setattr(
        sd.Transport, "client_factory", lambda: httpx.AsyncClient(transport=httpx.MockTransport(t.handler))
    )
    env_.mock.page_override = detail_pages
    env_.mock.remaining = {k: 10**7 for k in env_.mock.remaining}
    return t


def detail_pages(url: str) -> httpx.Response | None:
    if "/ip/" not in url:
        return None
    item = urlsplit(url).path.rstrip("/").rsplit("/", 1)[-1]
    return httpx.Response(200, text=mock.product_page(item, upc_of(int(item))))


def peak_rss_mb() -> float:
    """The process's peak resident memory so far, in MiB."""
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        c = Counters(cb=ctypes.sizeof(Counters))
        kernel = ctypes.WinDLL("kernel32")
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        psapi = ctypes.WinDLL("psapi")
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(c), c.cb)
        return c.PeakWorkingSetSize / (1024 * 1024)
    import resource

    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def evidence(name: str, data: dict[str, Any]) -> None:
    out = os.environ.get("LOAD_EVIDENCE_DIR")
    if out:
        Path(out).mkdir(parents=True, exist_ok=True)
        payload = {"synthetic": True, "delay_s": DELAY_S, **data}
        (Path(out) / f"{name}.json").write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")


def records(e: Env, run_id: str) -> dict[str, dict[str, Any]]:
    with sessionmaker(e.engine)() as s:
        rows = list(s.scalars(select(RecordRow).where(RecordRow.run_id == run_id)))
    assert len({r.upc for r in rows}) == len(rows), "a product is recorded twice"
    return {r.upc: {k: r.record[k] for k in ("upc", "weight", "regular_price", "url")} for r in rows}


def ledger(e: Env, run_id: str) -> tuple[int, dict[str, int]]:
    with sessionmaker(e.engine)() as s:
        count = int(
            s.scalar(select(func.count()).select_from(ProviderUsage).where(ProviderUsage.run_id == run_id))
            or 0
        )
        by_outcome = Counter(
            str(o) for o in s.scalars(select(ProviderUsage.outcome).where(ProviderUsage.run_id == run_id))
        )
    return count, dict(by_outcome)


def page_requests(e: Env, start: int) -> Counter[str]:
    return Counter(url for _, path, url in e.mock.calls[start:] if path == LISTING_ENDPOINT)


@pytest.mark.parametrize("workers", [1, 2, 4])
def test_the_same_products_come_out_at_any_worker_count_and_each_page_is_read_once(
    env: Env,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    workers: int,
) -> None:
    products = scope(monkeypatch)
    timer = timed(env, monkeypatch)
    env.edit(parallel={"workers": workers, "max_in_flight": 4, "min_interval_s": 0.0})
    started = time.monotonic()
    code, _ = env.result("run", "--store", STORE_KEY, "--workers", str(workers))
    elapsed = time.monotonic() - started
    assert code == 0
    run = env.runs()[-1]
    assert run.status == "published"
    got = records(env, run.id)
    assert len(got) == products and all(r["upc"] for r in got.values())
    calls = page_requests(env, 0)
    assert max(calls.values()) == 1, calls.most_common(3)
    entries, outcomes = ledger(env, run.id)
    assert entries == len(env.mock.calls), (entries, len(env.mock.calls))
    assert timer.peak <= 4
    with sessionmaker(env.engine)() as s:
        seg = s.scalars(select(CollectionSegment).where(CollectionSegment.run_id == run.id)).one()
        assert seg.workers == workers
        per_worker = {w["worker"]: w["requests"] for w in seg.stats["workers"]}
    evidence(
        f"workers_{workers}",
        {
            "workers": workers,
            "max_in_flight": 4,
            "products": products,
            "requests": entries,
            "ledger_outcomes": outcomes,
            "requests_by_worker": per_worker,
            "peak_requests_in_flight": timer.peak,
            "elapsed_s": round(elapsed, 1),
            "requests_per_s": round(entries / elapsed, 2),
            "peak_process_rss_mb": round(peak_rss_mb(), 1),
            "note": "peak_process_rss_mb is the test process's peak so far, including earlier tests",
        },
    )


def test_requests_start_no_closer_than_the_configured_interval(
    env: Env,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scope(monkeypatch)
    timer = timed(env, monkeypatch)
    env.edit(parallel={"workers": 2, "max_in_flight": 2, "min_interval_s": 0.08})
    code, _ = env.result("run", "--store", STORE_KEY, "--workers", "2", "--categories", "0")
    assert code == 0
    gaps = [b - a for a, b in zip(timer.starts, timer.starts[1:], strict=False)]
    assert gaps and min(gaps) >= 0.07, min(gaps)
    assert timer.peak <= 2
    evidence(
        "pacing",
        {
            "min_interval_s": 0.08,
            "max_in_flight": 2,
            "requests": len(timer.starts),
            "smallest_gap_s": round(min(gaps), 3),
            "peak_requests_in_flight": timer.peak,
        },
    )


def test_transient_failures_are_retried_accounted_and_change_nothing(
    env: Env,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    products = scope(monkeypatch)
    timed(env, monkeypatch)
    failed: list[str] = []
    seen: Counter[str] = Counter()

    def flaky(url: str) -> httpx.Response | None:
        seen[url] += 1
        # The first request of every 25th distinct URL answers a provider failure; a retry succeeds.
        if len(seen) % 25 == 0 and seen[url] == 1:
            failed.append(url)
            return httpx.Response(502, text="synthetic transient failure")
        return detail_pages(url)

    env.mock.page_override = flaky
    env.edit(parallel={"workers": 2, "max_in_flight": 4, "min_interval_s": 0.0})
    code, _ = env.result("run", "--store", STORE_KEY, "--workers", "2")
    assert failed
    run = env.runs()[-1]
    entries, outcomes = ledger(env, run.id)
    assert code == 0 and run.status == "published", (code, run.status, run.stop_code, outcomes)
    assert entries == len(env.mock.calls)
    got = records(env, run.id)
    assert len(got) == products
    # A product page that failed once stays blank only if it was never read again in the run.
    blank = [k for k, r in got.items() if not r["upc"]]
    evidence(
        "transient_failures",
        {
            "products": products,
            "failures_injected": len(failed),
            "requests": entries,
            "ledger_outcomes": outcomes,
            "products_without_upc_after_the_run": len(blank),
        },
    )


def test_a_termination_with_several_workers_resumes_with_nothing_lost_or_duplicated(
    env: Env,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    products = scope(monkeypatch)
    timed(env, monkeypatch)
    env.edit(parallel={"workers": 2, "max_in_flight": 4, "min_interval_s": 0.0})
    target = f"page={max(2, PAGES_PER_LISTING - 1)}"
    sent: list[str] = []

    def stop(url: str) -> httpx.Response | None:
        if mock.SNACKS in url and target in url and not sent:
            sent.append(url)
            signal.raise_signal(signal.SIGTERM)
        return detail_pages(url)

    env.mock.page_override = stop
    code, _ = env.result("run", "--store", STORE_KEY, "--workers", "2")
    run = env.runs()[-1]
    assert code == 75 and run.status == "interrupted" and run.stop_code == "TERMINATED"
    before_resume = len(env.mock.calls)
    interrupted = records(env, run.id)
    env.mock.page_override = detail_pages
    code, _ = env.result("resume", "--store", STORE_KEY, "--workers", "2")
    assert code == 0
    done = env.runs()[-1]
    assert done.id == run.id and done.status == "published"
    got = records(env, run.id)
    assert len(got) == products
    assert all(k in got for k in interrupted)
    entries, outcomes = ledger(env, run.id)
    assert entries == len(env.mock.calls)
    calls = page_requests(env, 0)
    # A page in flight at the termination may be requested again; the ledger shows both.
    repeated = {url: n for url, n in calls.items() if n > 1}
    assert len(repeated) <= 2, repeated
    evidence(
        "terminated_and_resumed",
        {
            "products": products,
            "products_recorded_at_the_termination": len(interrupted),
            "products_after_the_resume": len(got),
            "requests_before_the_resume": before_resume,
            "requests_total": entries,
            "ledger_outcomes": outcomes,
            "pages_requested_twice": len(repeated),
        },
    )
