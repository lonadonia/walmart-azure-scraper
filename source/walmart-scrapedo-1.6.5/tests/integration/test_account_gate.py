"""The account-wide spending gate around every Oxylabs submission (1.6.0). SYNTHETIC: the Web API is an
in-memory mock (tests/mock_oxylabs.py) and the gate a recording fake; nothing reaches Oxylabs."""

from __future__ import annotations

from typing import Any

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from tests.integration.test_operations import STORE_KEY, Env, env  # noqa: F401
from tests.mock_oxylabs import OXY_KEY, MockOxylabs
from walmart_headless.acquisition import oxylabs
from walmart_headless.db.models import ProviderUsage


class FakeGate:
    """Refuses once ``cap`` submissions are held or spent; records every call in order."""

    def __init__(self, cap: int, *, fail_settle: bool = False) -> None:
        self.cap = cap
        self.fail_settle = fail_settle
        self.calls: list[tuple[str, str]] = []
        self.state: dict[str, str] = {}
        self.keys: set[str] = set()
        self.calls_at_dispatch: list[int] = []
        self.mock: MockOxylabs | None = None

    def reserve(
        self, *, purpose: str, endpoint: str, target_url: str, attempt: int, usd: float, key: str
    ) -> str:
        held = sum(1 for v in self.state.values() if v != "unsent")
        if held >= self.cap:
            raise oxylabs.GateRefused(f"account allowance: {held} of {self.cap} submissions held (test)")
        assert usd == 0.0015 and key not in self.keys  # one reservation per collector row
        self.keys.add(key)
        ref = f"g{len(self.state) + 1}"
        self.state[ref] = "reserved"
        self.calls.append(("reserve", ref))
        return ref

    def dispatched(self, ref: str) -> None:
        assert self.state[ref] == "reserved"
        self.state[ref] = "dispatched"
        self.calls.append(("dispatched", ref))
        assert self.mock is not None
        self.calls_at_dispatch.append(len(self.mock.calls))

    def unsent(self, ref: str, reason: str) -> None:
        self.state[ref] = "unsent"
        self.calls.append(("unsent", ref))

    def settled(self, ref: str, *, status: int, kind: str | None, charged: bool | None, usd: float) -> None:
        assert self.state[ref] == "dispatched"
        if self.fail_settle:
            raise OSError("the gate's disk is full (test)")
        self.state[ref] = "settled" if charged is not None else "unknown"
        self.calls.append(("settled", ref))

    def unknown(self, ref: str, reason: str) -> None:
        self.state[ref] = "unknown"
        self.calls.append(("unknown", ref))


@pytest.fixture
def oxy(env: Env, monkeypatch: pytest.MonkeyPatch) -> MockOxylabs:  # noqa: F811
    monkeypatch.setenv(oxylabs.ENV_KEY, OXY_KEY)
    mock = MockOxylabs(env.mock)
    monkeypatch.setattr(
        oxylabs.OxylabsTransport,
        "client_factory",
        lambda: httpx.AsyncClient(transport=httpx.MockTransport(mock.handler)),
    )
    return mock


def use_gate(monkeypatch: pytest.MonkeyPatch, gate: FakeGate, mock: MockOxylabs) -> None:
    gate.mock = mock
    monkeypatch.setattr(oxylabs.OxylabsTransport, "account_gate_factory", lambda: gate)


def ceiling(e: Env) -> None:
    code, _ = e.result(
        "set-ceiling",
        "--provider",
        "oxylabs",
        "--submissions",
        "200",
        "--usd-per-result",
        "0.0015",
        "--basis",
        "test ceiling",
    )
    assert code == 0


def usage(e: Env) -> list[ProviderUsage]:
    with sessionmaker(e.engine, expire_on_commit=False)() as s:
        return list(s.scalars(select(ProviderUsage).where(ProviderUsage.provider == "oxylabs")))


def test_every_submission_is_reserved_and_marked_dispatched_by_the_gate_before_it_is_sent(
    env: Env,  # noqa: F811
    oxy: MockOxylabs,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate = FakeGate(cap=10_000)
    use_gate(monkeypatch, gate, oxy)
    ceiling(env)
    code, _ = env.result("run", "--store", STORE_KEY, "--provider", "oxylabs")
    assert code == 0
    sent = len(oxy.calls)
    assert sent > 0 and len(gate.state) == sent == len(usage(env))
    # Each request left after its own reservation and dispatch mark, and before the next one's.
    assert gate.calls_at_dispatch == list(range(sent))
    order = [c for c, _ in gate.calls]
    assert order == ["reserve", "dispatched", "settled"] * sent
    assert set(gate.state.values()) == {"settled"}


def test_a_refusal_of_the_gate_sends_nothing_more_and_stops_the_run_as_a_ceiling(
    env: Env,  # noqa: F811
    oxy: MockOxylabs,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate = FakeGate(cap=3)
    use_gate(monkeypatch, gate, oxy)
    ceiling(env)
    code, _ = env.result("run", "--store", STORE_KEY, "--provider", "oxylabs")
    assert code == 4
    [run] = env.runs()
    assert run.status == "interrupted" and run.stop_code == "SPENDING_CEILING"
    assert "account-wide spending gate" in (run.stop_detail or "")
    assert len(oxy.calls) == 3 == len(gate.state)  # the fourth was refused before anything was sent
    rows = usage(env)
    refused = [r for r in rows if r.outcome == "gate_refused"]
    assert len(refused) == 1 and refused[0].cost_usd == 0.0  # the collector's own row, never sent
    assert OXY_KEY not in (run.stop_detail or "")


def test_a_failure_to_record_an_outcome_keeps_the_answer_and_the_gate_holds_its_reservation(
    env: Env,  # noqa: F811
    oxy: MockOxylabs,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate = FakeGate(cap=10_000, fail_settle=True)
    use_gate(monkeypatch, gate, oxy)
    ceiling(env)
    code, _ = env.result("run", "--store", STORE_KEY, "--provider", "oxylabs")
    assert code == 0  # the answers were kept and used
    assert set(gate.state.values()) == {"dispatched"}  # held at the gate: never released as free


def test_an_unanswered_submission_is_reported_to_the_gate_as_unknown(
    env: Env,  # noqa: F811
    oxy: MockOxylabs,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate = FakeGate(cap=10_000)
    use_gate(monkeypatch, gate, oxy)
    ceiling(env)
    n = {"calls": 0}

    def cut(endpoint: str, body: dict[str, Any]) -> httpx.Response | None:
        n["calls"] += 1
        if n["calls"] == 1:
            raise httpx.ReadTimeout("no answer (test)")
        return None

    oxy.answer_override = cut
    env.result("run", "--store", STORE_KEY, "--provider", "oxylabs")
    assert gate.state["g1"] == "unknown"  # sent, no answer: held, never assumed free
    assert ("unknown", "g1") in gate.calls
