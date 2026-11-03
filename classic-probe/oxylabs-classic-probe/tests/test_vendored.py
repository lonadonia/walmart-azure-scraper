"""The vendored Walmart readers are the collector's files, unchanged (OFFLINE)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "src" / "classic_probe" / "vendor"
RECORD = json.loads((VENDOR / "VENDORED.json").read_text("utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_each_vendored_file_is_the_recorded_copy() -> None:
    listed = {f["vendored"] for f in RECORD["files"]}
    present = {p.relative_to(ROOT).as_posix() for p in VENDOR.glob("*.py") if p.name != "__init__.py"}
    assert listed == present
    for f in RECORD["files"]:
        assert _sha(ROOT / f["vendored"]) == f["sha256"], f["vendored"]


def test_the_vendored_files_are_still_the_collectors_files() -> None:
    collector = ROOT.parent / "walmart-azure-headless"
    if not collector.is_dir():
        pytest.skip("the Walmart collector's source is not beside this probe (a probe-only extraction)")
    for f in RECORD["files"]:
        assert _sha(ROOT.parent / f["origin"]) == f["sha256"], f"{f['origin']} changed: copy it again"
