"""Safe publication (brief §12, NN-4).

1. The run is ``validated`` and has no blocking FAIL findings. WARN findings need a recorded reason. Its
   pages came from the network (``acquisition/lineage.py``): a run whose provider transport was
   substituted (a test, the fault-injection harness) is published only to a target configured as a test
   target (``publication.test_target``).
2. The manifest and every export are re-verified from storage.
3. One DB transaction inserts ``publications`` and moves ``publication_pointer`` with an optimistic
   ``version`` check.
4. After commit, ``published/<store>/latest.json`` is written. It is a convenience copy: the DB
   pointer is authoritative and :func:`sync_latest_json` repairs the file after a crash.

A failure at any step leaves the previous pointer untouched. There is no force-publish.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import select, update
from sqlalchemy.orm import Session, sessionmaker

from walmart_headless.acquisition import lineage
from walmart_headless.core.jsonio import dumps_bytes
from walmart_headless.core.timeutil import iso, utcnow
from walmart_headless.db.models import (
    Artifact,
    AuditLog,
    ExportRow,
    Publication,
    PublicationPointer,
    Run,
    Store,
    ValidationFinding,
)
from walmart_headless.publishing.exports import verify_manifest
from walmart_headless.storage.base import StorageAdapter

NON_BLOCKING_GATES = frozenset({"G14"})


class PublicationRefused(RuntimeError):
    pass


class PointerConflict(RuntimeError):
    """Another publication moved the pointer concurrently."""


@dataclass(frozen=True)
class PublishResult:
    publication_id: str
    version: int
    previous_publication_id: str | None


def latest_key(store_key: str) -> str:
    return f"published/{store_key}/latest.json"


def _manifest(session: Session, run_id: str) -> Artifact:
    art = session.scalar(
        select(Artifact)
        .join(ExportRow, ExportRow.artifact_id == Artifact.id)
        .where(ExportRow.run_id == run_id, ExportRow.kind == "manifest")
    )
    if art is None:
        raise PublicationRefused("run has no manifest export")
    return art


def publish_run(
    factory: sessionmaker[Session],
    storage: StorageAdapter,
    run_id: str,
    published_by: str,
    *,
    warn_override_reason: str | None = None,
    fault: Callable[[str], None] | None = None,
    test_target: bool = False,
) -> PublishResult:
    hook = fault or (lambda _stage: None)
    with factory() as s:
        run = s.get(Run, run_id)
        if run is None:
            raise PublicationRefused("unknown run")
        if run.status != "validated":
            raise PublicationRefused(f"run status is {run.status!r}, not 'validated'")
        if run.mode != "LIVE":
            raise PublicationRefused("only LIVE runs are published")
        lin = lineage.of_run(s, run_id)
        if lin.problems:  # no target publishes pages of two origins, a test target included
            raise PublicationRefused("mixed lineage: " + "; ".join(lin.problems))
        if lin.lineage != lineage.NETWORK and not test_target:
            raise PublicationRefused(
                f"the run's pages did not come from the network (lineage {lin.lineage}: {lin.basis}); "
                "only a target configured as a test target publishes it"
            )
        findings = list(s.scalars(select(ValidationFinding).where(ValidationFinding.run_id == run_id)))
        blocking = [f for f in findings if f.severity == "FAIL" and f.gate not in NON_BLOCKING_GATES]
        if blocking:
            raise PublicationRefused(f"{len(blocking)} FAIL finding(s); FAIL cannot be overridden")
        warns = [f for f in findings if f.severity == "WARN"]
        if warns and not (warn_override_reason and warn_override_reason.strip()):
            raise PublicationRefused(f"{len(warns)} WARN finding(s) need a recorded override reason")
        store = s.get(Store, run.store_id)
        assert store is not None
        manifest = _manifest(s, run_id)
        manifest_key, manifest_sha = manifest.key, manifest.sha256
        store_id, store_key, mode = store.id, store.key, run.mode

    problems = verify_manifest(storage, manifest_key, manifest_sha)
    if problems:
        raise PublicationRefused("integrity check failed: " + "; ".join(problems))
    hook("before_commit")

    with factory() as s, s.begin():
        pointer = s.get(PublicationPointer, store_id, with_for_update=True)
        previous_id = pointer.publication_id if pointer else None
        version = pointer.version if pointer else 0
        pub = Publication(
            store_id=store_id,
            run_id=run_id,
            mode=mode,
            manifest_sha256=manifest_sha,
            published_by=published_by,
            previous_publication_id=previous_id,
        )
        s.add(pub)
        s.flush()
        if pointer is None:
            s.add(PublicationPointer(store_id=store_id, publication_id=pub.id, version=1))
        else:
            res = s.execute(
                update(PublicationPointer)
                .where(PublicationPointer.store_id == store_id, PublicationPointer.version == version)
                .values(publication_id=pub.id, version=version + 1)
            )
            if res.rowcount != 1:  # type: ignore[attr-defined]
                raise PointerConflict(store_id)
        s.execute(update(Run).where(Run.id == run_id, Run.status == "validated").values(status="published"))
        s.add(
            AuditLog(
                actor=published_by,
                action="publish",
                target=run_id,
                reason=warn_override_reason,
                data={
                    "publication_id": pub.id,
                    "version": version + 1,
                    "warns": len(warns),
                    "previous_publication_id": previous_id,
                    "lineage": lin.lineage,
                    "test_target": test_target,
                },
            )
        )
        pub_id = pub.id
        hook("inside_commit")
    hook("after_commit")

    _write_latest(storage, store_key, pub_id, run_id, manifest_key, manifest_sha, version + 1, mode)
    return PublishResult(pub_id, version + 1, previous_id)


def _write_latest(
    storage: StorageAdapter,
    store_key: str,
    publication_id: str,
    run_id: str,
    manifest_key: str,
    manifest_sha: str,
    version: int,
    mode: str,
) -> None:
    storage.put_bytes(
        latest_key(store_key),
        dumps_bytes(
            {
                "publication_id": publication_id,
                "run_id": run_id,
                "manifest_key": manifest_key,
                "manifest_sha256": manifest_sha,
                "version": version,
                "mode": mode,
                "written_at": iso(utcnow()),
                "note": "convenience copy; the database publication_pointer is authoritative",
            }
        ),
        "application/json",
    )


def sync_latest_json(factory: sessionmaker[Session], storage: StorageAdapter, store_id: str) -> bool:
    """Rewrite ``latest.json`` from the DB pointer (repairs a crash between commit and file write)."""
    with factory() as s:
        pointer = s.get(PublicationPointer, store_id)
        if pointer is None:
            return False
        pub = s.get(Publication, pointer.publication_id)
        store = s.get(Store, store_id)
        assert pub is not None and store is not None
        manifest = _manifest(s, pub.run_id)
        _write_latest(
            storage,
            store.key,
            pub.id,
            pub.run_id,
            manifest.key,
            pub.manifest_sha256,
            pointer.version,
            pub.mode,
        )
        return True
