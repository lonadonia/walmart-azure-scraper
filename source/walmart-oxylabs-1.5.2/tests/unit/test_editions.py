"""The two editions of release 1.4.0 (the 2026-10-28 brief, section 3: one core, two editions built from the
same revision, with the configuration differences and their hashes recorded).

These tests run in the core (a checkout) and in each edition's extracted source alike: in an edition, the
core configuration is the one its ``EDITION.json`` says it was made from, rebuilt by undoing the lines the
record lists, and the tree is checked against the record."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from walmart_headless import editions
from walmart_headless.config_file import CollectorConfig
from walmart_headless.core.paths import PROJECT_ROOT

REVISION = "0" * 40
COMMITTED = "2026-10-28T00:00:00+00:00"


def read(path: str) -> bytes:
    return (PROJECT_ROOT / path).read_bytes()


def record() -> dict[str, object] | None:
    p = PROJECT_ROOT / editions.RECORD
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def core_files() -> dict[str, bytes]:
    """The core's configuration and environment examples (in an edition: as its record gives them)."""
    rec = record()
    files = {p: read(p) for p in (f"editions/{n}.env.example" for n in editions.EDITIONS)}
    files["README.md"] = read("README.md")
    if rec is None:
        files[editions.CONFIG] = read(editions.CONFIG)
        files[editions.ENV_EXAMPLE] = read(editions.ENV_EXAMPLE)
    else:
        files[editions.CONFIG] = editions.core_config(read(editions.CONFIG).decode("utf-8"), rec).encode()
        files[editions.ENV_EXAMPLE] = b"# the core's own, not part of an edition\n"
    return files


def build(files: dict[str, bytes], name: str) -> dict[str, bytes]:
    return editions.build(files, name, revision=REVISION, committed_at=COMMITTED, version="1.4.0")


@pytest.mark.parametrize("name", sorted(editions.EDITIONS))
def test_an_edition_changes_two_configuration_lines_and_the_environment_example(name: str) -> None:
    core = core_files()
    out = build(core, name)
    changed = sorted(p for p in out if out[p] != core.get(p))
    assert changed == sorted([editions.CONFIG, editions.ENV_EXAMPLE, editions.BUILD_INFO, editions.RECORD])
    info = json.loads(out[editions.RECORD])
    [config_change] = [c for c in info["changes"] if c["path"] == editions.CONFIG]
    # The edition line, and each store's provider line naming another provider (the core's stores name
    # Scrape.do, so the Scrape.do edition replaces the edition line only).
    stores = CollectorConfig.model_validate(yaml.safe_load(core[editions.CONFIG])).collections.values()
    expected = [f"edition: {{ name: {name}, providers: [{name}] }}"] + [
        f"provider: {name}" for c in stores if c.provider != name
    ]
    assert [r["edition"].split("#")[0].strip() for r in config_change["replaced_lines"]] == expected
    # The configuration loads, pins the provider and names it for every store.
    cfg = CollectorConfig.model_validate(yaml.safe_load(out[editions.CONFIG]))
    assert cfg.edition.name == name and cfg.edition.providers == (name,)
    assert {c.provider for c in cfg.collections.values()} == {name}
    # Every other line is the core's.
    core_lines = core[editions.CONFIG].decode().split("\n")
    out_lines = out[editions.CONFIG].decode().split("\n")
    assert len(core_lines) == len(out_lines)
    assert {i + 1 for i, (a, b) in enumerate(zip(core_lines, out_lines, strict=True)) if a != b} == {
        r["line"] for r in config_change["replaced_lines"]
    }
    # Its environment example names its own provider's key only.
    env = out[editions.ENV_EXAMPLE].decode()
    keys = {"scrapedo": ("SCRAPEDO_API_KEY", "OXYLABS"), "oxylabs": ("OXYLABS_WEB_API_KEY", "SCRAPEDO")}
    own, other = keys[name]
    assert own in env and other not in env and f"walmart_{name}" in env
    build_info = json.loads(out[editions.BUILD_INFO])
    assert build_info == {"commit": REVISION, "built_at": COMMITTED, "edition": name}
    # The same input builds the same bytes, and the result checks against its own record.
    assert build(core, name) == out
    assert editions.check_tree(out) == []


def test_both_editions_share_every_other_file() -> None:
    core = core_files()
    a, b = build(core, "scrapedo"), build(core, "oxylabs")
    differing = {p for p in a if a[p] != b[p]}
    assert differing == {editions.CONFIG, editions.ENV_EXAMPLE, editions.BUILD_INFO, editions.RECORD}


def test_this_tree_is_the_core_or_the_edition_its_record_describes() -> None:
    rec = record()
    if rec is None:  # the core: both providers, no edition record
        assert editions.CORE_LINE in read(editions.CONFIG).decode().split("\n")
        assert not (PROJECT_ROOT / editions.BUILD_INFO).exists() or "edition" not in json.loads(
            read(editions.BUILD_INFO)
        )
        return
    recorded = rec["file_sha256"]
    assert isinstance(recorded, dict)
    missing = [p for p in recorded if not (PROJECT_ROOT / p).is_file()]
    assert missing == []
    files = {p: read(p) for p in recorded}
    files[editions.RECORD] = read(editions.RECORD)
    assert editions.check_tree(files) == []


def test_a_tree_that_differs_from_its_record_is_reported(tmp_path: Path) -> None:
    out = build(core_files(), "oxylabs")
    assert editions.check_tree(out) == []
    tampered = {**out, "README.md": out["README.md"] + b"\n"}
    assert [p.split(":")[0] for p in editions.check_tree(tampered)] == [
        "README.md",
        "the tree's SHA-256 is not the one EDITION.json records",
    ]
    config = out[editions.CONFIG].decode().replace("providers: [oxylabs]", "providers: [scrapedo, oxylabs]")
    problems = editions.check_tree({**out, editions.CONFIG: config.encode()})
    assert any("is not the edition's line" in p for p in problems)


def test_an_edition_is_built_from_the_core_only() -> None:
    core = core_files()
    with pytest.raises(editions.EditionError, match="no edition 'classic'"):
        build(core, "classic")
    once = build(core, "scrapedo")
    with pytest.raises(editions.EditionError, match="already in the tree"):
        build(once, "oxylabs")
    no_line = {**core, editions.CONFIG: core[editions.CONFIG].replace(editions.CORE_LINE.encode(), b"")}
    with pytest.raises(editions.EditionError, match="0 core edition lines"):
        build(no_line, "scrapedo")
