"""Shared fixtures. Synthetic pages (tests/synthetic_walmart.py) are invented; the pages under
tests/captures were captured from Walmart by an earlier live run and are replayed offline."""

from __future__ import annotations

import atexit
import json
import shutil
import tempfile
from pathlib import Path

import pytest

from walmart_headless import editions
from walmart_headless.core.settings import (
    PrivateLabelConfig,
    Settings,
    StoreConfig,
    load_private_label,
    load_settings,
    load_stores,
)

ROOT = Path(__file__).resolve().parents[1]


def _core_config(root: Path) -> Path:
    """The configuration folder the tests use: the core's, which names both providers. In an edition's
    extracted source (docs/EDITIONS.md) it is a copy of the edition's folder whose ``collector.yaml`` is the
    core one the edition was made from (the lines its ``EDITION.json`` lists, undone), so every test runs
    the same configuration in the core and in each edition; ``tests/unit/test_editions.py`` checks the
    edition's own files."""
    shipped = root / "config"
    record = root / editions.RECORD
    if not record.is_file():
        return shipped
    core = editions.core_config(
        (shipped / "collector.yaml").read_text(encoding="utf-8"),
        json.loads(record.read_text(encoding="utf-8")),
    )
    folder = Path(tempfile.mkdtemp(prefix="walmart-core-config-"))
    atexit.register(shutil.rmtree, folder, True)
    shutil.copytree(shipped, folder, dirs_exist_ok=True)
    (folder / "collector.yaml").write_bytes(core.encode("utf-8"))
    return folder


CONFIG = _core_config(ROOT)
CAPTURES = ROOT / "tests" / "captures"
STORE_KEY = "walmart-3891-pickup"


@pytest.fixture(autouse=True)
def no_ambient_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """No test reads a key or a database from the developer's environment."""
    for name in (
        "SCRAPEDO_API_KEY",
        "SCRAPEDO_API_KEY_FILE",
        "OXYLABS_WEB_API_KEY",
        "OXYLABS_WEB_API_KEY_FILE",
        "OXYLABS_API",
        "OXYLABS_API_KEY",
        "WALMART_COLLECTOR_DATABASE_URL",
        "WALMART_COLLECTOR_DATABASE_AUTH",
        "WALMART_COLLECTOR_STORAGE",
        "WALMART_COLLECTOR_DATA_DIR",
        "WALMART_COLLECTOR_BLOB_ACCOUNT_URL",
        "WALMART_COLLECTOR_BLOB_CONTAINER",
        "WALMART_COLLECTOR_CONFIG",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture(scope="session")
def settings() -> Settings:
    return load_settings(CONFIG / "settings.yaml")


def declare_test_target(cfg_dir: Path) -> None:
    """Make a copied configuration a test target: its runs, collected through a substituted transport, may
    be published there (``publication.test_target``); the shipped configuration keeps it false."""
    path = cfg_dir / "settings.yaml"
    text = path.read_text(encoding="utf-8")
    assert text.count("publication: { test_target: false }") == 1
    path.write_text(
        text.replace("publication: { test_target: false }", "publication: { test_target: true }"),
        encoding="utf-8",
    )


@pytest.fixture(scope="session")
def walmart_store() -> StoreConfig:
    return next(s for s in load_stores(CONFIG / "stores.yaml").stores if s.key == STORE_KEY)


@pytest.fixture(scope="session")
def private_label() -> PrivateLabelConfig:
    return load_private_label(CONFIG / "walmart_private_label_brands.yaml")
