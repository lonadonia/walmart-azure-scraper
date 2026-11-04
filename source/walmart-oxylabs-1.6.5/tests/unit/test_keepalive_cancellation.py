"""The provider keep-alive helper never swallows a stop signal (release 1.4.0 regression tests; the 2026-10-28
brief, section 7: "Do not swallow stop signals in provider keep-alive helpers").

While a provider request is in flight, the session renews the run's lease every ``KEEPALIVE_S`` seconds from
a helper task (``ScrapeDoWalmartSession._fetch_alive``; the Oxylabs Web API session inherits it). When the
request ends the helper is cancelled and awaited. A stop (the worker's task cancelled on SIGTERM, ``stop`` or
the run's time limit) can arrive during the request or exactly while the helper is being awaited; in both
cases the request's task must end cancelled. Swallowing the helper's ``CancelledError`` without asking
whether this task is itself being cancelled would turn the second case into a normal return: the stop
would be lost and the worker would go on with the next page.

SYNTHETIC: a stand-in transport, no provider and no network."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from walmart_headless.acquisition import scrapedo_session
from walmart_headless.acquisition.oxylabs_session import OxylabsWalmartSession
from walmart_headless.acquisition.scrapedo_session import ScrapeDoWalmartSession
from walmart_headless.storage.local import LocalStorageAdapter

SESSIONS = [ScrapeDoWalmartSession, OxylabsWalmartSession]
ANSWER = object()  # what the stand-in transport answers


class Transport:
    """Answers after ``delay`` seconds; ``on_answer`` runs just before it answers."""

    def __init__(self, delay: float = 0.0, on_answer: Any = None):
        self.delay, self.on_answer, self.calls = delay, on_answer, 0

    async def fetch(self, req: Any) -> Any:
        self.calls += 1
        await asyncio.sleep(self.delay)
        if self.on_answer is not None:
            self.on_answer()
        return ANSWER


def session(cls: type[ScrapeDoWalmartSession], transport: Transport, tmp: Path, beats: list[int]) -> Any:
    s = cls(
        transport,  # type: ignore[arg-type]
        LocalStorageAdapter(tmp),
        "runs/test",
        store_id="3891",
        zipcode="60085",
        store_page_url="https://www.walmart.com/store/3891-waukegan-il",
        sanitizer=lambda html: (html, None),
    )
    s.keepalive = lambda: beats.append(1)
    return s


@pytest.fixture(autouse=True)
def fast_beat(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scrapedo_session, "KEEPALIVE_S", 0.01)


def others() -> set[asyncio.Task[Any]]:
    return {t for t in asyncio.all_tasks() if t is not asyncio.current_task()}


@pytest.mark.parametrize("cls", SESSIONS)
def test_the_helper_renews_the_lease_and_stops_quietly_after_an_answer(
    cls: type[ScrapeDoWalmartSession], tmp_path: Path
) -> None:
    beats: list[int] = []

    async def scenario() -> Any:
        s = session(cls, Transport(delay=0.08), tmp_path, beats)
        got = await s._fetch_alive("req")
        assert not others()  # the helper ended with the request
        return got

    assert asyncio.run(scenario()) is ANSWER
    assert len(beats) >= 2  # renewed while the request was in flight


@pytest.mark.parametrize("cls", SESSIONS)
def test_a_stop_during_the_request_cancels_it(cls: type[ScrapeDoWalmartSession], tmp_path: Path) -> None:
    beats: list[int] = []

    async def scenario() -> None:
        s = session(cls, Transport(delay=30.0), tmp_path, beats)
        task = asyncio.create_task(s._fetch_alive("req"))
        await asyncio.sleep(0.05)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert task.cancelled()
        await asyncio.sleep(0)
        assert not others()

    asyncio.run(scenario())
    assert beats


@pytest.mark.parametrize("cls", SESSIONS)
def test_a_stop_arriving_while_the_helper_is_stopped_is_not_swallowed(
    cls: type[ScrapeDoWalmartSession], tmp_path: Path
) -> None:
    """The stop is requested as the provider answers: it reaches the task while it waits for the helper to
    end. The task must end cancelled, not return the answer."""

    async def scenario() -> None:
        holder: dict[str, asyncio.Task[Any]] = {}
        transport = Transport(on_answer=lambda: asyncio.get_running_loop().call_soon(holder["task"].cancel))
        s = session(cls, transport, tmp_path, [])
        holder["task"] = task = asyncio.create_task(s._fetch_alive("req"))
        with pytest.raises(asyncio.CancelledError):
            await task
        assert task.cancelled() and transport.calls == 1

    asyncio.run(scenario())


@pytest.mark.parametrize("cls", SESSIONS)
def test_a_failed_renewal_does_not_fail_the_request(
    cls: type[ScrapeDoWalmartSession], tmp_path: Path
) -> None:
    """A renewal that raises is noticed by the next checkpoint; the answer is kept."""

    def broken() -> None:
        raise RuntimeError("lease store unavailable")

    async def scenario() -> Any:
        s = session(cls, Transport(delay=0.05), tmp_path, [])
        s.keepalive = broken
        return await s._fetch_alive("req")

    assert asyncio.run(scenario()) is ANSWER
