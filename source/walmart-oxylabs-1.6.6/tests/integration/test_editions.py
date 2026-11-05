"""Release 1.4.0: one collector, two editions (the 2026-10-28 brief, section 3).

An edition is the collector built for one provider (``deploy/build_edition.py``, docs/EDITIONS.md): its
configuration names the providers its runs may use. A run, a resumed run or a provider command naming
another is refused before any request, whatever keys the environment holds: a run is never sent to another
provider. A scheduled execution checks the key of the provider it runs with (release 1.3.1 checked the
Scrape.do key whatever the provider, so a scheduled Oxylabs run without a Scrape.do key never started).

SYNTHETIC: the Scrape.do and Oxylabs mocks (tests/mock_scrapedo.py, tests/mock_oxylabs.py); nothing reaches a
provider."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
import yaml

from tests.integration.test_operations import STORE_KEY, Env, _scheduled, env  # noqa: F401
from tests.integration.test_workers_and_oxylabs import oxy  # noqa: F401  (a fixture)
from tests.mock_oxylabs import MockOxylabs
from walmart_headless.acquisition import scrapedo as sd

pytestmark = [pytest.mark.postgres]


def edition(e: Env, name: str, *providers: str, provider: str | None = None) -> None:
    data = yaml.safe_load(e.config.read_text(encoding="utf-8"))
    data["edition"] = {"name": name, "providers": list(providers)}
    if provider is not None:
        data["collections"][STORE_KEY]["provider"] = provider
    e.config.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def refused(e: Env, *args: str) -> tuple[int, str]:
    code, lines = e.cli(*args)
    [line] = [x for x in lines if x["event"] == "COMMAND_REFUSED"]
    return code, str(line["message"])


def test_the_scrape_do_edition_never_sends_a_run_to_oxylabs(
    env: Env,  # noqa: F811
    oxy: MockOxylabs,  # noqa: F811
) -> None:
    edition(env, "scrapedo", "scrapedo")
    # An Oxylabs key and ceiling are there: the edition refuses the provider all the same.
    code, _ = env.result("set-ceiling", "--provider", "oxylabs", "--submissions", "200", "--basis", "test")
    assert code == 0
    code, message = refused(env, "run", "--store", STORE_KEY, "--provider", "oxylabs")
    assert (code, message) == (2, "the scrapedo edition runs scrapedo only: provider oxylabs refused")
    assert env.runs() == [] and oxy.calls == [] and env.mock.calls == []
    code, message = refused(env, "provider-balance", "--provider", "oxylabs")
    assert code == 2 and message.endswith("provider oxylabs refused")
    # Its own provider runs, and the run records the edition.
    code, _ = env.result("run", "--store", STORE_KEY, "--categories", "4")
    assert code == 0
    [run] = env.runs()
    assert (run.config_snapshot["edition"], run.config_snapshot["provider"]) == ("scrapedo", "scrapedo")
    assert oxy.calls == []


def test_the_oxylabs_edition_never_sends_a_run_to_scrape_do(
    env: Env,  # noqa: F811
    oxy: MockOxylabs,  # noqa: F811
) -> None:
    edition(env, "oxylabs", "oxylabs", provider="oxylabs")
    code, message = refused(env, "run", "--store", STORE_KEY, "--provider", "scrapedo")
    assert (code, message) == (2, "the oxylabs edition runs oxylabs only: provider scrapedo refused")
    code, message = refused(env, "provider-balance")  # Scrape.do by default
    assert code == 2 and message.endswith("provider scrapedo refused")
    assert env.runs() == [] and env.mock.calls == [] and oxy.calls == []
    # Its own provider: nothing is sent without the operator's ceiling (release 1.3.0 rule), as before.
    code, _ = env.result("run", "--store", STORE_KEY)
    assert code == 4
    [run] = env.runs()
    assert (run.config_snapshot["edition"], run.stop_code) == ("oxylabs", "SPENDING_CEILING")
    assert env.mock.calls == [] and oxy.calls == []
    # A resumed run is checked again: the same run under the Scrape.do edition is refused.
    edition(env, "scrapedo", "scrapedo", provider="scrapedo")
    code, message = refused(env, "resume", "--store", STORE_KEY)
    assert code == 2 and message.endswith("provider oxylabs refused")
    assert env.mock.calls == [] and oxy.calls == []


def test_a_store_naming_a_provider_outside_the_edition_is_a_configuration_error(
    env: Env,  # noqa: F811
) -> None:
    edition(env, "scrapedo", "scrapedo", provider="oxylabs")
    code, lines = env.cli("validate-config")
    assert code == 2
    [line] = [x for x in lines if x["event"] == "CONFIG_INVALID"]
    assert "the scrapedo edition runs scrapedo only" in line["message"]


def test_a_scheduled_execution_checks_the_key_of_its_own_provider(
    env: Env,  # noqa: F811
    oxy: MockOxylabs,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An Oxylabs store with no Scrape.do key: release 1.3.1 refused the scheduled execution for the missing
    Scrape.do key (exit 3); it now starts the Oxylabs run, which sends nothing without a ceiling (exit 4)."""
    monkeypatch.delenv(sd.ENV_KEY)
    env.edit(provider="oxylabs", schedule={"enabled": True, "weekdays": [1], "start_time": "06:00"})
    assert _scheduled(env, datetime(2026, 7, 14, 11, tzinfo=UTC)) == 4
    [run] = env.runs()
    snap: dict[str, Any] = run.config_snapshot
    assert (snap["provider"], snap["edition"], run.trigger) == ("oxylabs", "core", "schedule")
    assert run.stop_code == "SPENDING_CEILING" and oxy.calls == [] and env.mock.calls == []
