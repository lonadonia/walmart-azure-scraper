"""Saved product pages as observations later runs may reuse (``import-detail-captures``, release 1.5.0).

Each entry of the index names a stored page and how it was obtained: the item it was requested for, when, by
which run and source revision. The page is read with the collector's own identity check and size reader. A
page that is not the item's, or that carries no page data, is refused and listed. What is loaded keeps its
original time, run, revision and hash with ``origin`` ``imported``, so a value reused from it is reported as
recovered from a saved page, never as newly fetched. Nothing here requests anything.
"""

from __future__ import annotations

import gzip
import hashlib
from collections import Counter
from collections.abc import Iterable, Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from walmart_headless.core.timeutil import iso
from walmart_headless.db.models import DetailObservation
from walmart_headless.sites.walmart import pack_size as wps
from walmart_headless.sites.walmart import page_data as wpd

REQUIRED = ("item_id", "observed_at", "run_id", "path")


def read_page(path: Path) -> str:
    raw = path.read_bytes()
    if path.suffix == ".gz":
        raw = gzip.decompress(raw)
    return raw.decode("utf-8", "replace")


def inspect(html: str, item_id: str) -> dict[str, Any]:
    """What a stored page establishes for the item: ``status`` extracted or absent_in_source with the UPC and
    the statements about size, or ``refused`` with the reason (the same checks as a page read by a run)."""
    ident = wpd.product_identifier(html, item_id)
    if not ident.page_data:
        return {"refused": "parse_failed", "reason": "the page carries no Walmart page data"}
    if ident.page_item and ident.page_item != item_id:
        return {"refused": "identity_mismatch", "reason": f"the page is for item {ident.page_item}"}
    if not ident.matched and not ident.page_item:
        return {"refused": "identity_mismatch", "reason": "the page's data names no item"}
    return {
        "status": "extracted" if ident.value else "absent_in_source",
        "upc": ident.value or None,
        "upc_path": ident.path if ident.value else None,
        "size_statements": [o.as_dict() for o in wps.observations(wpd.next_data(html))],
    }


def load(s: Session, store_id: str, entries: Iterable[Mapping[str, Any]], base: Path) -> dict[str, Any]:
    """Load the index's pages for the store; a page already loaded for the item changes nothing."""
    counts: Counter[str] = Counter()
    refused: list[dict[str, Any]] = []
    for entry in entries:
        missing = [k for k in REQUIRED if not entry.get(k)]
        if missing:
            raise ValueError(f"an index entry has no {', '.join(missing)}: {dict(entry)}")
        item_id, path = str(entry["item_id"]), base / str(entry["path"])
        if not path.is_file():
            counts["missing_file"] += 1
            refused.append({"item_id": item_id, "path": str(entry["path"]), "refused": "missing_file"})
            continue
        html = read_page(path)
        found = inspect(html, item_id)
        if "refused" in found:
            counts[str(found["refused"])] += 1
            refused.append({"item_id": item_id, "path": str(entry["path"]), **found})
            continue
        sha = hashlib.sha256(html.encode("utf-8")).hexdigest()
        known = s.scalar(
            select(DetailObservation.id).where(
                DetailObservation.store_id == store_id,
                DetailObservation.item_id == item_id,
                DetailObservation.body_sha256 == sha,
            )
        )
        if known is not None:
            counts["already_loaded"] += 1
            continue
        at = datetime.fromisoformat(str(entry["observed_at"]).replace("Z", "+00:00"))
        s.add(
            DetailObservation(
                store_id=store_id,
                item_id=item_id,
                observed_at=at,
                run_id=str(entry["run_id"]),
                page_fetch_id=entry.get("page_fetch_id"),
                source_revision=entry.get("source_revision"),
                origin="imported",
                url=entry.get("url"),
                body_sha256=sha,
                status=found["status"],
                upc=found["upc"],
                upc_path=found["upc_path"],
                size_statements=found["size_statements"],
            )
        )
        s.flush()
        counts[f"loaded_{found['status']}"] += 1
    return {"counts": dict(sorted(counts.items())), "refused": refused}


def as_dict(row: DetailObservation) -> dict[str, Any]:
    return {
        "item_id": row.item_id,
        "observed_at": iso(row.observed_at),
        "run_id": row.run_id,
        "page_fetch_id": row.page_fetch_id,
        "source_revision": row.source_revision,
        "origin": row.origin,
        "status": row.status,
        "upc": row.upc,
        "body_sha256": row.body_sha256,
    }
