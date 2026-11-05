"""Project-relative locations, overridable with environment variables."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def config_dir() -> Path:
    """``WALMART_COLLECTOR_CONFIG_DIR``, else ``./config`` of the working directory, else the project's."""
    env = os.environ.get("WALMART_COLLECTOR_CONFIG_DIR")
    if env:
        return Path(env)
    local = Path.cwd() / "config"
    return local if local.is_dir() else PROJECT_ROOT / "config"


def data_dir() -> Path:
    return Path(os.environ.get("WALMART_COLLECTOR_DATA_DIR") or PROJECT_ROOT / "data")


# The version of this collector (and of its parser): every run and export records it.
PARSER_VERSION = "1.6.6"
# The verified application release this standalone collector was derived from.
DERIVED_FROM = "mscraper 1.2.6 (f9c03085aee2156cfdb21751db233e521b5a2d4c)"
