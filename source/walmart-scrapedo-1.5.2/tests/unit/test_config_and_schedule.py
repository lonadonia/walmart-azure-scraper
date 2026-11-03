"""The configuration file, the Azure cron expression and the store-local schedule guard (no database)."""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from tests.conftest import CONFIG, STORE_KEY
from walmart_headless.config_file import LoadedConfig, StoreCollection
from walmart_headless.operations import due_occurrence, utc_cron


def _config(tmp_path: Path, **collector: object) -> Path:
    d = tmp_path / "config"
    shutil.copytree(CONFIG, d)
    data = yaml.safe_load((d / "collector.yaml").read_text(encoding="utf-8"))
    data.update(collector)
    (d / "collector.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return d / "collector.yaml"


def test_the_shipped_configuration_names_store_3891_pickup_twice_a_week() -> None:
    cfg = LoadedConfig(CONFIG / "collector.yaml")
    store = cfg.store(STORE_KEY)
    assert (store.location_id, store.expected.postal_code, store.modality.value) == (
        "3891",
        "60085",
        "PICKUP",
    )
    assert store.expected.address_line1 == "3900 Fountain Square Pl"
    coll = cfg.collection(STORE_KEY)
    # Twice a week is configured, but the schedule ships OFF until the client switches it on.
    assert not coll.schedule.enabled and len(coll.schedule.weekdays) == 2
    assert coll.timezone == "America/Chicago"
    assert not coll.limits.bounded()  # production collects the full configured scope
    assert cfg.categories_csv.name == "Walmart_Category_URLs.csv"


def test_the_shipped_schedule_never_cuts_a_full_scope_run_short() -> None:
    """Release 1.3.1: a full-scope run lasts longer than the interval between two starts (OPERATIONS.md,
    Capacity), so the shipped schedule collects all day, lets an unfinished run go on past the next start
    (on_overlap: continue) and sets no time limit; it stays off until the client switches it on."""
    coll = LoadedConfig(CONFIG / "collector.yaml").collection(STORE_KEY)
    sched = coll.schedule
    assert not sched.enabled and sched.continue_unfinished and sched.on_overlap == "continue"
    assert (sched.window_start, sched.window_end) == ("00:00", None)
    assert coll.limits.max_run_minutes is None and coll.limits.max_segment_minutes == 300
    assert StoreCollection.model_validate({}).schedule.on_overlap == "continue"
    with pytest.raises(ValidationError):
        StoreCollection.model_validate({"schedule": {"on_overlap": "skip"}})


def test_configuration_errors_are_refused(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        LoadedConfig(_config(tmp_path / "a", retailer="marianos"))
    with pytest.raises(ValidationError):
        LoadedConfig(_config(tmp_path / "b", provider="oxylabs"))  # no other provider can be configured
    with pytest.raises(ValueError, match=r"not in stores.yaml"):
        LoadedConfig(_config(tmp_path / "c", collections={"walmart-9999": {}}))
    with pytest.raises(ValidationError):
        StoreCollection.model_validate({"schedule": {"enabled": True, "weekdays": []}})
    with pytest.raises(ValidationError):
        StoreCollection.model_validate({"timezone": "Mars/Olympus"})


def test_the_cron_expression_covers_standard_and_daylight_time() -> None:
    coll = StoreCollection.model_validate(
        {
            "timezone": "America/Chicago",
            "schedule": {"enabled": True, "weekdays": [1, 4], "start_time": "06:00"},
        }
    )
    cron = utc_cron(coll, year=2026)
    assert cron["cron_utc"] == "0 11,12 * * 2,5"  # Tuesday and Friday; 11:00 UTC in CDT, 12:00 in CST
    late = StoreCollection.model_validate(
        {"timezone": "America/Chicago", "schedule": {"enabled": True, "weekdays": [1], "start_time": "21:30"}}
    )
    # 21:30 Chicago is the next UTC day (02:30 or 03:30 UTC on Wednesday).
    assert utc_cron(late, year=2026)["cron_utc"] == "30 2,3 * * 3"


@pytest.mark.parametrize(
    ("utc", "due"),
    [
        (datetime(2026, 7, 14, 11, 0, tzinfo=UTC), True),  # 06:00 CDT
        (datetime(2026, 7, 14, 12, 0, tzinfo=UTC), False),  # 07:00 CDT: the other firing
        (datetime(2026, 7, 14, 10, 57, tzinfo=UTC), True),  # a few minutes early
        (datetime(2026, 7, 14, 11, 40, tzinfo=UTC), True),  # within the tolerance (45 min)
        (datetime(2026, 7, 14, 11, 50, tzinfo=UTC), False),
        (datetime(2026, 1, 13, 12, 0, tzinfo=UTC), True),  # 06:00 CST
        (datetime(2026, 1, 13, 11, 0, tzinfo=UTC), False),  # 05:00 CST
        (datetime(2026, 3, 10, 11, 0, tzinfo=UTC), True),  # the Tuesday after the March change: CDT
        (datetime(2026, 11, 3, 12, 0, tzinfo=UTC), True),  # the Tuesday after the November change: CST
        (datetime(2026, 7, 15, 11, 0, tzinfo=UTC), False),  # Wednesday
    ],
)
def test_only_the_due_local_occurrence_is_acted_on(utc: datetime, due: bool) -> None:
    coll = StoreCollection.model_validate(
        {"timezone": "America/Chicago", "schedule": {"enabled": True, "weekdays": [1], "start_time": "06:00"}}
    )
    assert (due_occurrence(coll, utc) is not None) is due
