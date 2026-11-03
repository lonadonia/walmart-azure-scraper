"""Why a product's UPC and size are filled or empty, field by field (release 1.5.0).

An empty field is a different fact depending on what happened: the source was inspected and states nothing,
the page was refused, the request failed, it was another item's, or nobody asked. These classes keep those
apart, and a value reused from an earlier read keeps that read's time, run and source revision instead of
looking newly fetched. Export: ``field_dispositions.json`` and ``field_dispositions.csv`` of each run, and
``field-dispositions``.

Release 1.5.2: :func:`apply_to_sources` carries the same facts into a record's ``fields``, ``missing`` and
``missing_kind``, the file ``provenance.json`` and ``record_map.json`` show. Until 1.5.1 those kept what the
result page's tile said (a size recovered from a saved page still named the tile's title, a UPC read from
its own page stayed "missing", and a page nobody requested read ``source_absent``) while this table held the
truth.
"""

from __future__ import annotations

import csv
import io
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

PRESENT = "present_in_listing"
RECOVERED = "recovered_from_saved_detail"
FETCHED = "fetched_detail"
NOT_ATTEMPTED = "not_attempted"
BLOCKED = "blocked"  # a refusal or challenge page answered (until 1.5.1: "inaccessible_challenged")
REQUEST_FAILED = "request_failed"  # no usable answer (until 1.5.1: "inaccessible_challenged" too)
PARSE_FAILURE = "parse_failure"
IDENTITY_MISMATCH = "identity_mismatch"
ABSENT = "absent_in_source"
INTERRUPTED = "budget_deadline_interruption"
CONFLICT = "unresolved_conflict"
ALL = (
    PRESENT,
    RECOVERED,
    FETCHED,
    NOT_ATTEMPTED,
    BLOCKED,
    REQUEST_FAILED,
    PARSE_FAILURE,
    IDENTITY_MISMATCH,
    ABSENT,
    INTERRUPTED,
    CONFLICT,
)
# The outcome of a product whose result page stated the UPC (``provenance.upc_detail.source``).
LISTING_SOURCE = "result page data (the listing stated the UPC)"

# The ``source`` of a value a product's own page gave, in a record's ``fields``.
SOURCE_OWN_PAGE = "walmart_product_page"
# ``missing_kind`` of a field a product's own page left empty: the disposition, under the names the tile's
# kinds use (``source_absent`` is only ever a page that was read and states nothing).
_EMPTY_KIND = {ABSENT: "source_absent", CONFLICT: "conflicting_evidence"}

_BY_STATUS = {
    "blocked": BLOCKED,
    "request_failed": REQUEST_FAILED,
    "parse_failed": PARSE_FAILURE,
    "identity_mismatch": IDENTITY_MISMATCH,
}
# A page not read because a budget, a limit, a ceiling, a deadline or a stop came first.
_INTERRUPTION = re.compile(
    r"\blimit\b|\bbudget\b|\bceiling\b|\bdeadline\b|\bstopped before\b|\bquota\b", re.I
)
# A limit of zero pages (release 1.4.1's capped demonstrations, ``--pdp-sample 0``): nothing was attempted,
# so no budget ran out part-way. Release 1.5.0 refuses such a limit; earlier runs still carry the reason.
_ZERO_LIMIT = re.compile(r"\blimit \(0 pages?\)", re.I)


def _unread(reason: str) -> str:
    if _ZERO_LIMIT.search(reason):
        return NOT_ATTEMPTED
    return INTERRUPTED if _INTERRUPTION.search(reason) else NOT_ATTEMPTED


def _origin(detail: Mapping[str, Any]) -> dict[str, Any]:
    """The read a value comes from: this run's, or the earlier one it was reused from."""
    reused = detail.get("reused_from")
    if isinstance(reused, Mapping):
        return {
            "observed_at": reused.get("requested_at"),
            "source_run": reused.get("run_id"),
            "source_revision": reused.get("source_revision"),
            "origin": reused.get("origin") or "fetched",
            "page_fetch_id": reused.get("page_fetch_id"),
            "body_sha256": reused.get("body_sha256"),
            "item_id": detail.get("item_id"),
        }
    return {
        "observed_at": detail.get("requested_at"),
        "source_run": detail.get("observed_by_run"),
        "source_revision": detail.get("source_revision"),
        "origin": "read_again" if detail.get("read_again_by_run") else "fetched",
        "page_fetch_id": detail.get("page_fetch_id"),
        "body_sha256": detail.get("body_sha256"),
        "item_id": detail.get("item_id"),
    }


def _upc_path(detail: Mapping[str, Any]) -> Any:
    """Where the UPC stands in the page it was read from (a reused read keeps it on that read)."""
    reused = detail.get("reused_from")
    return detail.get("path") or (reused.get("path") if isinstance(reused, Mapping) else None)


def _read_earlier(detail: Mapping[str, Any]) -> bool:
    return bool(detail.get("reused_from") or detail.get("read_again_by_run"))


def upc(record: Mapping[str, Any], detail: Mapping[str, Any]) -> dict[str, Any]:
    status = str(detail.get("status") or "")
    value = str(record.get("upc") or "")
    if value and (detail.get("listing_upc") or detail.get("source") == LISTING_SOURCE):
        out: dict[str, Any] = {"disposition": PRESENT, "value": value}
        if detail.get("upc_conflict"):
            out["conflicts"] = [detail["upc_conflict"]]
        return out
    if status == "extracted":
        kind = RECOVERED if _read_earlier(detail) else FETCHED
        return {"disposition": kind, "value": value, **_origin(detail), "path": _upc_path(detail)}
    if status == "absent_in_source":
        return {"disposition": ABSENT, "value": "", **_origin(detail), "reason": detail.get("reason")}
    if status in _BY_STATUS:
        return {
            "disposition": _BY_STATUS[status],
            "value": "",
            **_origin(detail),
            "reason": detail.get("reason"),
        }
    reason = str(detail.get("reason") or "no outcome recorded")
    return {"disposition": _unread(reason), "value": "", "reason": reason}


def weight(record: Mapping[str, Any], detail: Mapping[str, Any]) -> dict[str, Any]:
    status = str(detail.get("status") or "")
    value = str(record.get("weight") or "")
    size = detail.get("size")
    size = size if isinstance(size, Mapping) else {}
    conflicts = list(size.get("conflicts") or [])
    if value and detail.get("size_filled"):
        return {
            "disposition": RECOVERED if _read_earlier(detail) else FETCHED,
            "value": value,
            **_origin(detail),
            "path": size.get("path"),
            "rule": size.get("rule"),
        }
    if value:
        out: dict[str, Any] = {"disposition": PRESENT, "value": value}
        if conflicts:
            out.update(conflicts=conflicts, page=_origin(detail))
        return out
    if size.get("outcome") == "conflict":
        return {"disposition": CONFLICT, "value": "", **_origin(detail), "conflicts": conflicts}
    if size:
        return {
            "disposition": ABSENT,
            "value": "",
            **_origin(detail),
            "reason": "the item's own page states no size of its pack",
        }
    if status in _BY_STATUS:
        return {
            "disposition": _BY_STATUS[status],
            "value": "",
            **_origin(detail),
            "reason": detail.get("reason"),
        }
    reason = str(detail.get("size_unread_reason") or detail.get("reason") or "no outcome recorded")
    if status in ("extracted", "absent_in_source") and "size_unread_reason" not in detail:
        # A read recorded before release 1.5.0 kept the UPC only: its page was not inspected for a size.
        reason = "the page read for its UPC was not inspected for a size (a read before release 1.5.0)"
    return {"disposition": _unread(reason), "value": "", "reason": reason}


def of_record(record: Mapping[str, Any], detail: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {"upc": upc(record, detail), "weight": weight(record, detail)}


def _own_page_source(field: Mapping[str, Any]) -> dict[str, Any]:
    """Where a value from a product's own page comes from, in the shape of a record's ``fields``: the capture,
    its place in the response, the time it was read, the product and the code that read it."""
    path, rule = field.get("path"), field.get("rule")
    return {
        "source": SOURCE_OWN_PAGE,
        "selector_or_path": f"{path} ({rule})" if path and rule else path,
        "fetch_id": field.get("page_fetch_id"),
        "response_sha256": field.get("body_sha256"),
        "body_sha256": field.get("body_sha256"),
        "observed_at": field.get("observed_at"),
        "item_id": field.get("item_id"),
        "source_run": field.get("source_run"),
        "source_revision": field.get("source_revision"),
        "origin": field.get("origin"),
    }


def apply_to_sources(
    fields: Mapping[str, Any],
    missing: Mapping[str, Any],
    missing_kind: Mapping[str, Any],
    row: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """A record's ``fields``, ``missing`` and ``missing_kind`` as its dispositions ``row`` (see
    :func:`of_record` and ``supporting_log``) establish them: a filled value names its own page and leaves
    ``missing``; an empty one says what became of its page, and only a page that was read and states nothing
    is ``source_absent``. A value the listing stated keeps the listing's source."""
    out_fields, out_missing, out_kind = dict(fields), dict(missing), dict(missing_kind)
    for name, field in row.items():
        disposition = str(field["disposition"])
        if disposition in (RECOVERED, FETCHED):
            out_fields[name] = _own_page_source(field)
            out_missing.pop(name, None)
            out_kind.pop(name, None)
        elif disposition != PRESENT:
            out_kind[name] = _EMPTY_KIND.get(disposition, disposition)
            reason = field.get("reason") or "; ".join(field.get("conflicts") or [])
            if reason:
                listing = out_missing.get(name)
                out_missing[name] = f"{listing}; its own page: {reason}" if listing else str(reason)
    return out_fields, out_missing, out_kind


def counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, int]]:
    out: dict[str, Counter[str]] = {"upc": Counter(), "weight": Counter()}
    for row in rows:
        for field in out:
            out[field][str(row[field]["disposition"])] += 1
    return {k: dict(sorted(v.items())) for k, v in out.items()}


CSV_COLUMNS = (
    "key",
    "observation_kind",
    "item_id",
    "url",
    "category",
    "sub_category",
    "product_title",
    "upc",
    "upc_disposition",
    "upc_observed_at",
    "upc_source_run",
    "upc_source_revision",
    "upc_page_fetch_id",
    "upc_path",
    "upc_body_sha256",
    "upc_reason",
    "upc_conflicts",
    "weight",
    "weight_disposition",
    "weight_observed_at",
    "weight_source_run",
    "weight_source_revision",
    "weight_page_fetch_id",
    "weight_path",
    "weight_body_sha256",
    "weight_reason",
    "weight_conflicts",
)


def _field_cells(field: Mapping[str, Any]) -> list[Any]:
    return [
        field.get("value", ""),
        field.get("disposition", ""),
        field.get("observed_at") or "",
        field.get("source_run") or "",
        field.get("source_revision") or "",
        field.get("page_fetch_id") or "",
        field.get("path") or "",
        field.get("body_sha256") or "",
        field.get("reason") or "",
        "; ".join(field.get("conflicts") or []),
    ]


def csv_bytes(rows: Sequence[Mapping[str, Any]]) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow(CSV_COLUMNS)
    for row in rows:
        w.writerow(
            [
                *(row.get(k, "") for k in CSV_COLUMNS[:7]),
                *_field_cells(row["upc"]),
                *_field_cells(row["weight"]),
            ]
        )
    return ("﻿" + buf.getvalue()).encode("utf-8")
