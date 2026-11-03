"""The editions of the collector (release 1.4.0): one source, built for one provider each.

Both editions of a release are built from the same revision of this collector: the same code, settings,
tests and documents. An edition differs from that revision in its configuration only, and :func:`build`
makes exactly these changes, each recorded in ``EDITION.json`` with its SHA-256 before and after:

* ``config/collector.yaml``: the ``edition:`` line names the edition and its one provider, and each store's
  ``provider:`` value is that provider (the lines replaced are listed). A run, a resumed run or a provider
  command naming another provider is refused before any request (``operations.check_edition``);
* ``.env.example``: the edition's own (``editions/<name>.env.example``), naming its provider's variables only;
* ``BUILD_INFO.json`` (added): the revision, its commit time and the edition, recorded with every run.

``EDITION.json`` also gives the SHA-256 of every other file, and of the whole tree.
``deploy/build_edition.py`` exports a revision with ``git archive``, builds an edition from it and writes its
source ZIP. A tree built this way is checked against its own ``EDITION.json`` (:func:`check_tree`;
``tests/unit/test_editions.py`` does so in every tree)."""

from __future__ import annotations

import difflib
import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from walmart_headless.core import jsonvalues as jv

CONFIG = "config/collector.yaml"
ENV_EXAMPLE = ".env.example"
RECORD = "EDITION.json"
BUILD_INFO = "BUILD_INFO.json"
CORE_LINE = "edition: { name: core, providers: [scrapedo, oxylabs] }"
_PROVIDER_LINE = re.compile(r"^(?P<lead>\s+provider: )(?P<value>scrapedo|oxylabs)(?P<rest>(?:\s+#.*)?)$")


@dataclass(frozen=True)
class Edition:
    name: str
    provider: str
    title: str


EDITIONS: dict[str, Edition] = {
    "scrapedo": Edition("scrapedo", "scrapedo", "Scrape.do, Walmart store endpoint (/plugin/walmart/store)"),
    "oxylabs": Edition("oxylabs", "oxylabs", "Oxylabs Web API (Bearer key; not the Classic product)"),
}


class EditionError(ValueError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def edition_line(ed: Edition) -> str:
    return f"edition: {{ name: {ed.name}, providers: [{ed.provider}] }}"


def edit_config(text: str, ed: Edition) -> tuple[str, list[dict[str, Any]]]:
    """The core configuration made the edition's, with each line replaced (1-based line, core, edition)."""
    lines = text.split("\n")
    at = [i for i, line in enumerate(lines) if line == CORE_LINE]
    if len(at) != 1:
        raise EditionError(f"{CONFIG}: {len(at)} core edition lines ({CORE_LINE!r}), exactly 1 expected")
    replaced: list[dict[str, Any]] = []

    def put(i: int, new: str) -> None:
        if lines[i] != new:
            replaced.append({"line": i + 1, "core": lines[i], "edition": new})
            lines[i] = new

    put(at[0], edition_line(ed))
    stores = 0
    for i, line in enumerate(lines):
        m = _PROVIDER_LINE.match(line)
        if m is None:
            continue
        stores += 1
        rest = m["rest"]
        if rest:  # the comment keeps its column
            spaces = len(rest) - len(rest.lstrip(" "))
            rest = " " * max(1, spaces + len(m["value"]) - len(ed.provider)) + rest.lstrip(" ")
        put(i, m["lead"] + ed.provider + rest)
    if not stores:
        raise EditionError(f"{CONFIG}: no store names its provider")
    return "\n".join(lines), replaced


def build(
    files: Mapping[str, bytes], name: str, *, revision: str, committed_at: str, version: str
) -> dict[str, bytes]:
    """The edition ``name`` of a source tree (paths relative to the collector folder, ``/`` separated)."""
    ed = EDITIONS.get(name)
    if ed is None:
        raise EditionError(f"no edition {name!r} (editions: {', '.join(EDITIONS)})")
    for path in (RECORD, BUILD_INFO):
        if path in files:
            raise EditionError(f"{path} is already in the tree: an edition is built from the core")
    out = dict(files)
    config, replaced = edit_config(files[CONFIG].decode("utf-8"), ed)
    out[CONFIG] = config.encode("utf-8")
    out[ENV_EXAMPLE] = files[f"editions/{name}.env.example"]
    out[BUILD_INFO] = _json({"commit": revision, "built_at": committed_at, "edition": name})
    changes = [
        {
            "path": CONFIG,
            "sha256_core": sha256(files[CONFIG]),
            "sha256_edition": sha256(out[CONFIG]),
            "replaced_lines": replaced,
        },
        {
            "path": ENV_EXAMPLE,
            "sha256_core": sha256(files[ENV_EXAMPLE]),
            "sha256_edition": sha256(out[ENV_EXAMPLE]),
            "from": f"editions/{name}.env.example",
            "diff": "".join(
                difflib.unified_diff(
                    files[ENV_EXAMPLE].decode("utf-8").splitlines(keepends=True),
                    out[ENV_EXAMPLE].decode("utf-8").splitlines(keepends=True),
                    f"core/{ENV_EXAMPLE}",
                    f"{name}/{ENV_EXAMPLE}",
                )
            ),
        },
        {"path": BUILD_INFO, "added": True, "sha256_edition": sha256(out[BUILD_INFO])},
    ]
    tree = {path: sha256(data) for path, data in sorted(out.items())}
    out[RECORD] = _json(
        {
            "edition": ed.name,
            "provider": ed.provider,
            "title": ed.title,
            "version": version,
            "source_revision": revision,
            "committed_at": committed_at,
            "changes": changes,
            "files": len(tree),
            "tree_sha256": tree_digest(tree),
            "file_sha256": tree,
            "note": "the revision's own files but for the changes listed; the other edition of the release "
            "is built from the same revision",
        }
    )
    return out


def tree_digest(tree: Mapping[str, str]) -> str:
    """One SHA-256 over every file's (sorted) path and SHA-256, ``sha256sum`` style."""
    return sha256("".join(f"{tree[p]}  {p}\n" for p in sorted(tree)).encode("utf-8"))


def _config_change(record: Mapping[str, object]) -> Mapping[str, object]:
    for change in jv.objects(record.get("changes"), "changes"):
        if change.get("path") == CONFIG:
            return change
    raise EditionError(f"{RECORD} records no change of {CONFIG}")


def core_config(edition_text: str, record: Mapping[str, object]) -> str:
    """The core configuration an edition's was made from (its record's replaced lines, undone)."""
    lines = edition_text.split("\n")
    for rep in jv.objects(_config_change(record).get("replaced_lines"), "replaced_lines"):
        line = jv.integer(rep.get("line"), "replaced line")
        if line is None or not 0 < line <= len(lines) or lines[line - 1] != rep.get("edition"):
            raise EditionError(f"{CONFIG} line {line} is not the edition's line {RECORD} names")
        lines[line - 1] = jv.text(rep.get("core"), "core line")
    return "\n".join(lines)


def check_tree(files: Mapping[str, bytes]) -> list[str]:
    """What in an edition's tree differs from its ``EDITION.json`` ([] when nothing): every file's SHA-256,
    the tree's, and the configuration rebuilt from the core one the record's changes started from."""
    record = jv.obj(json.loads(files[RECORD]), RECORD)
    problems: list[str] = []
    tree = {p: sha256(d) for p, d in files.items() if p != RECORD}
    recorded = {
        k: jv.text(v, f"file_sha256.{k}") for k, v in jv.obj(record.get("file_sha256"), "file_sha256").items()
    }
    for p in sorted(set(tree) | set(recorded)):
        if tree.get(p) != recorded.get(p):
            problems.append(f"{p}: SHA-256 {tree.get(p)} in the tree, {recorded.get(p)} in {RECORD}")
    if tree_digest(tree) != record.get("tree_sha256"):
        problems.append(f"the tree's SHA-256 is not the one {RECORD} records")
    ed = EDITIONS.get(jv.text(record.get("edition"), "edition"))
    if ed is None:
        return [*problems, f"{RECORD} names no known edition"]
    try:
        core = core_config(files[CONFIG].decode("utf-8"), record)
    except EditionError as exc:
        return [*problems, str(exc)]
    if sha256(core.encode("utf-8")) != _config_change(record).get("sha256_core"):
        problems.append(f"{CONFIG}: the core configuration its changes undo to is not the recorded one")
    if edit_config(core, ed)[0].encode("utf-8") != files[CONFIG]:
        problems.append(f"{CONFIG}: rebuilding the edition from the core configuration gives another file")
    if files[ENV_EXAMPLE] != files[f"editions/{ed.name}.env.example"]:
        problems.append(f"{ENV_EXAMPLE} is not editions/{ed.name}.env.example")
    return problems


def _json(data: Mapping[str, Any]) -> bytes:
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
