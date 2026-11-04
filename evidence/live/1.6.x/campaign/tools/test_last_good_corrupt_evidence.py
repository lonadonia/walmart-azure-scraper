"""Delivery verification (Walmart 1.6.1, W6): a run whose evidence is corrupted on disk between its export and its
publication is refused, and the last good publication keeps its pointer and its bytes (SYNTHETIC pages; nothing
reaches a provider or Walmart).

This file is not part of the frozen 1.6.1 tree. It is copied beside the frozen tests of a clean extraction of
WALMART_OXYLABS_SOURCE_1.6.1.zip (tests/integration/) and run there with the tree's own fixtures, so the code under
test is the frozen code. The corruption is real: the files are changed on disk, as a damaged disk would change them;
the publication's own integrity check (publishing/exports.py: verify_manifest, called by publish_run before the
pointer is moved) finds it. The comparison is the frozen suite's own snapshot: the publication pointer, the
publication rows, latest.json, the manifest it names, that manifest's products.json and the first run's
observations, before and after.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tests.conftest import STORE_KEY
from tests.integration.test_operations import Env, env  # noqa: F401  (env is a fixture)
from tests.integration.test_publication_safety import _evidence, snapshot
from walmart_headless.publishing import publish as publish_module

pytestmark = [pytest.mark.postgres]

CORRUPTIONS = ("export_file_changed", "export_file_truncated", "manifest_changed")


def _corrupt(e: Env, manifest_key: str, how: str) -> dict[str, Any]:
    manifest_path = e.data / manifest_key
    body = json.loads(manifest_path.read_bytes())
    products = Path(e.data / body["files"]["products.json"]["key"])
    if how == "export_file_changed":
        data = products.read_bytes()
        products.write_bytes(data.replace(b'"', b"'", 1))  # one byte changed
        return {"file": "products.json", "change": "one byte changed"}
    if how == "export_file_truncated":
        data = products.read_bytes()
        products.write_bytes(data[: len(data) // 2])
        return {"file": "products.json", "change": f"truncated from {len(data)} to {len(data) // 2} bytes"}
    raw = manifest_path.read_bytes()
    manifest_path.write_bytes(raw.replace(b"{", b"{ ", 1))  # still valid JSON, other bytes
    return {"file": "manifest.json", "change": "one byte added"}


@pytest.mark.parametrize("how", CORRUPTIONS)
def test_a_run_whose_evidence_is_corrupted_before_publication_is_refused_and_keeps_the_last_good_dataset(
    env: Env,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    how: str,
) -> None:
    code, _ = env.result("run", "--store", STORE_KEY)
    first = env.runs()[0]
    assert code == 0 and first.status == "published"
    before = snapshot(env, first.id)

    real = publish_module.verify_manifest
    done: dict[str, Any] = {}

    def corrupt_then_verify(storage: Any, manifest_key: str, expected_sha256: str | None = None) -> list[str]:
        if not done:  # the second run's own export, after it was written and before it is checked
            done.update(_corrupt(env, manifest_key, how), manifest_key=manifest_key)
        problems = real(storage, manifest_key, expected_sha256)
        done["problems"] = problems
        return problems

    monkeypatch.setattr(publish_module, "verify_manifest", corrupt_then_verify)
    code2, _ = env.cli("run", "--store", STORE_KEY)
    second = env.runs()[-1]
    after = snapshot(env, first.id)
    _evidence(
        f"publication_refused_corrupt_{how}",
        {
            "fault": f"corrupt evidence: {how}",
            "synthetic": True,
            "first_run": first.id,
            "second_run": second.id,
            "second_run_status": second.status,
            "second_run_exit_code": code2,
            "corruption": done,
            "before": before,
            "after": after,
            "unchanged": before == after,
        },
    )
    assert done.get("problems"), "the integrity check found nothing"
    assert second.id != first.id and second.status != "published"
    assert after == before  # pointer, publication rows, published bytes and first-run observations
