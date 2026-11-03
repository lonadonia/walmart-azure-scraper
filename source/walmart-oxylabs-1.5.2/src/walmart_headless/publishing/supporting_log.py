"""The supporting log of a run: where each value came from and why an empty value is empty.

Product files keep exactly the 22 fields (brief §6); everything else about a record lives here: its
status, exclusion reasons and flags, the page and selector or JSON path of each field, why each empty
field is empty, what the site's own product response says about the product's store, fulfillment and
stock, its offers with their details, the store-assortment decision apart from the current offer, the UPC
outcome of its own product page, and which collection segment saw it.

Two kinds of observation are told apart:

* ``fresh``: observed by this run. A resumed run keeps what an earlier *segment of the same run* observed
  (``observation.earlier_segment`` true) and does not observe it again;
* ``carried_forward``: not observed by this run at all; the store's last verified observation from an
  *earlier run* is kept unchanged (its own run, page and crawl date in ``historical``, with why this run did
  not observe it). Its prices are the ones observed on its crawl date, not verified by this run.

A replay observes nothing: its rows are ``replayed``, observed by its source run (that run's time and stored
page) and read again by the replay's own code. (Release 1.3.1 labelled them ``fresh``, observed by the
replay run.)
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from walmart_headless.core.timeutil import iso, utcnow
from walmart_headless.db.models import (
    Artifact,
    CollectionSegment,
    PageFetch,
    ProductObservation,
    RecordRow,
    Run,
    StoreAttestation,
)
from walmart_headless.publishing import dispositions

EXPORTED_STATUSES = ("valid", "exported_not_valid", "historical")

# The observations a record comes from: a result tile, the product's own page, a coupon's item list (a
# sponsored placement is never a record's source; it is followed to the product's own page).
RECORD_SOURCES = ("card", "pdp", "coupon_items")


def _code(run: Run | None) -> dict[str, Any]:
    """The code that observed a run's products: its version and source revision (a replay: also the run it
    read again and that run's code)."""
    if run is None:
        return {}
    snap = run.config_snapshot or {}
    code = dict(snap.get("code") or {})
    out: dict[str, Any] = {
        "version": code.get("version") or run.parser_version,
        "commit": code.get("commit"),
        "uncommitted_changes": code.get("uncommitted_changes"),
    }
    replay = snap.get("replay") or {}
    if replay:
        out["replay_of"] = replay.get("source_run")
        out["source_code"] = replay.get("source_code")
    return out


def _earlier_in_run(prov: Mapping[str, Any]) -> list[dict[str, Any]]:
    """The states this run's earlier tiles of the product showed before the tile its record is kept from
    (release 1.3.1: a record holds the product's latest state in the run), each with its page and time."""
    return [
        {
            "observed_at": e.get("observed_at"),
            "page_fetch_id": e.get("page_fetch_id"),
            "listing": e.get("listing"),
            "page": e.get("page"),
            "position": e.get("position"),
            "status": e.get("status"),
            "flags": e.get("flags") or [],
            "availability": (
                (((e.get("structured") or {}).get("walmart") or {}).get("availability")) or {}
            ).get("value"),
            "local_offer": e.get("local_offer"),
            **{f: str((e.get("record") or {}).get(f) or "") for f in ("regular_price", "sale_price", "ppm")},
        }
        for e in prov.get("earlier_in_run") or []
        if isinstance(e, Mapping)
    ]


def _replay_source(run: Run | None) -> str | None:
    """The run a replay read again (None for any other run)."""
    if run is None or run.mode != "REPLAY":
        return None
    source = ((run.config_snapshot or {}).get("replay") or {}).get("source_run")
    return str(source) if source else None


def _first_read(s: Session, origin: str, hist: Mapping[str, Any], replay_source: str | None) -> str | None:
    """The run that requested the pages a replay read again for this row, if a replay read them: this run's
    source, or, for a row carried from a run that was itself a replay, that replay's source (until release
    1.5.2 such a row said the replay had observed it and had fetched its product page)."""
    return _replay_source(s.get(Run, origin)) if hist else replay_source


def _read_again(detail: Mapping[str, Any] | None, source: str, replay: str) -> dict[str, Any] | None:
    """A replay's UPC outcome: a product page its source run requested names that run (whose time and stored
    page it is) and the replay that read it again, instead of being 'fresh' (release 1.3.1 marked it fresh, as
    if the replay had requested it). A UPC reused from an earlier run keeps 'reused_from'."""
    if detail is None:
        return None
    out = {k: v for k, v in detail.items() if k != "fresh"}
    if detail.get("fresh"):
        out.update(observed_by_run=source, read_again_by_run=replay)
    return out


def _revision(code: Mapping[str, Any]) -> str | None:
    return f"{code.get('version') or ''} {code.get('commit') or ''}".strip() or None


def _item_id(r: RecordRow, detail: Mapping[str, Any] | None) -> str:
    """The Walmart item the row is: its own page's outcome names it, or its key does."""
    return str((detail or {}).get("item_id") or r.upc.removeprefix("wm:"))


def _dispositions(
    r: RecordRow,
    detail: Mapping[str, Any] | None,
    *,
    origin: str,
    replay_source: str | None,
    run_id: str,
    observed_at: Any,
    code_of: Any,
) -> dict[str, dict[str, Any]]:
    """Why the row's UPC and size are filled or empty, each with the run, time and source revision of the
    read it comes from (a read before release 1.5.0 recorded no revision: its run's is named)."""
    seen = _read_again(detail, replay_source, run_id) if replay_source and detail else detail
    fields = dispositions.of_record(r.record, seen or {})
    stated = (r.provenance or {}).get("field_observed_at") or {}
    for name, field in fields.items():
        if field["disposition"] == dispositions.PRESENT:
            field.update(observed_at=stated.get(name) or observed_at, source_run=replay_source or origin)
        if field.get("origin") == "fetched" and not field.get("source_run"):
            field["source_run"] = replay_source or origin
        if field.get("source_run") and not field.get("source_revision"):
            field["source_revision"] = _revision(code_of(str(field["source_run"])))
    return fields


def _origin(s: Session, r: RecordRow, run_id: str) -> tuple[str, RecordRow | None, ProductObservation | None]:
    """The run that observed a row, with its record and observation there: a carried row points to its own
    earlier run, never to this one."""
    hist = (r.provenance or {}).get("historical") or {}
    origin = str(hist.get("run_id") or run_id)
    record = (
        s.scalar(select(RecordRow).where(RecordRow.run_id == origin, RecordRow.upc == r.upc)) if hist else r
    )
    obs = s.scalars(
        select(ProductObservation)
        .where(
            ProductObservation.run_id == origin,
            ProductObservation.upc == r.upc,
            ProductObservation.source.in_(RECORD_SOURCES),
        )
        .order_by(ProductObservation.observed_at, ProductObservation.id)
        .limit(1)
    ).first()
    return origin, record, obs


def _stored_hashes(s: Session, fetch_ids: set[str]) -> dict[str, str]:
    """The SHA-256 of each page's stored copy, as ``record_map`` names it (``stored_page_sha256``)."""
    known = sorted(f for f in fetch_ids if f)
    out: dict[str, str] = {}
    for start in range(0, len(known), 500):
        q = (
            select(PageFetch.id, Artifact.sha256)
            .join(Artifact, Artifact.id == PageFetch.dom_artifact_id)
            .where(PageFetch.id.in_(known[start : start + 500]))
        )
        for fetch_id, sha in s.execute(q).all():
            out[str(fetch_id)] = str(sha)
    return out


def _sources(
    prov: Mapping[str, Any], row: Mapping[str, Mapping[str, Any]]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """The observation's ``fields``, ``missing`` and ``missing_kind`` as the record's dispositions establish
    them (release 1.5.2)."""
    return dispositions.apply_to_sources(
        prov.get("fields") or {}, prov.get("missing") or {}, prov.get("missing_kind") or {}, row
    )


def _with_hashes(fields: Mapping[str, Any], hashes: Mapping[str, str]) -> dict[str, Any]:
    """Each field's source with the SHA-256 of the capture it names (empty until 1.5.1)."""
    return {
        name: {**src, "response_sha256": hashes.get(str(src.get("fetch_id"))) or src.get("response_sha256")}
        if isinstance(src, Mapping)
        else src
        for name, src in fields.items()
    }


def field_dispositions(s: Session, run_id: str) -> list[dict[str, Any]]:
    """One row per exported record of the run: why its UPC and its size are filled or empty
    (``publishing/dispositions.py``), in the record's own order of keys."""
    run = s.get(Run, run_id)
    replay_source = _replay_source(run)
    runs: dict[str, dict[str, Any]] = {}

    def code_of(rid: str) -> dict[str, Any]:
        if rid not in runs:
            runs[rid] = _code(s.get(Run, rid))
        return runs[rid]

    rows: list[dict[str, Any]] = []
    for r in s.scalars(
        select(RecordRow)
        .where(RecordRow.run_id == run_id, RecordRow.status.in_(EXPORTED_STATUSES))
        .order_by(RecordRow.upc)
    ):
        prov = r.provenance or {}
        hist = prov.get("historical") or {}
        origin = str(hist.get("run_id") or run_id)
        detail = prov.get("upc_detail")
        if hist:
            first = s.scalar(select(RecordRow).where(RecordRow.run_id == origin, RecordRow.upc == r.upc))
            detail = ((first.provenance or {}) if first is not None else {}).get("upc_detail")
        fields = _dispositions(
            r,
            detail,
            origin=origin,
            replay_source=_first_read(s, origin, hist, replay_source),
            run_id=origin,
            observed_at=hist.get("observed_at") or r.record.get("crawl_date"),
            code_of=code_of,
        )
        rows.append(
            {
                "key": r.upc,
                "observation_kind": ("carried_forward" if hist else "replayed" if replay_source else "fresh"),
                "item_id": _item_id(r, detail),
                "url": r.record.get("url"),
                "category": r.record.get("category"),
                "sub_category": r.record.get("sub_category"),
                "product_title": r.record.get("product_title"),
                **fields,
            }
        )
    return rows


def record_map(s: Session, run_id: str) -> dict[str, Any]:
    """Every exported row of the run with where it comes from: the run and time that observed it, the code
    revision of that run, the stored page (key and SHA-256), the store and fulfillment checks of that page,
    the store-assortment decision, each field's source and observation time, and the UPC's own outcome. A
    carried-forward row points to its own earlier run and page, never to this run's."""
    run = s.get(Run, run_id)
    runs: dict[str, Run | None] = {run_id: run}
    pages: dict[str, dict[str, Any]] = {}
    hashes: dict[str, str] = {}
    replay_source = _replay_source(run)

    def run_of(rid: str) -> Run | None:
        if rid not in runs:
            runs[rid] = s.get(Run, rid)
        return runs[rid]

    def page_of(fetch_id: str | None) -> dict[str, Any]:
        if not fetch_id:
            return {}
        if fetch_id not in pages:
            pf = s.get(PageFetch, fetch_id)
            art = s.get(Artifact, pf.dom_artifact_id) if pf is not None and pf.dom_artifact_id else None
            att = s.scalars(
                select(StoreAttestation)
                .where(StoreAttestation.checks["fetch_id"].astext == fetch_id)
                .order_by(StoreAttestation.created_at)
                .limit(1)
            ).first()
            pages[fetch_id] = {
                "page_fetch_id": fetch_id,
                "url": pf.url if pf is not None else None,
                "purpose": pf.purpose if pf is not None else None,
                "http_status": pf.http_status if pf is not None else None,
                "fetched_at": iso(pf.started_at) if pf is not None else None,
                "stored_page": art.key if art is not None else None,
                "stored_page_sha256": art.sha256 if art is not None else None,
                "store_check": {
                    "result": att.result,
                    "checks": {c.get("check"): c.get("status") for c in (att.checks or {}).get("checks", [])},
                }
                if att is not None
                else None,
            }
        return pages[fetch_id]

    rows: list[dict[str, Any]] = []
    for r in s.scalars(
        select(RecordRow)
        .where(RecordRow.run_id == run_id, RecordRow.status.in_(EXPORTED_STATUSES))
        .order_by(RecordRow.upc)
    ):
        extra = dict(r.provenance or {})
        hist = extra.get("historical") or {}
        origin, origin_record, obs = _origin(s, r, run_id)
        first_read = _first_read(s, origin, hist, replay_source)
        prov = dict(obs.provenance or {}) if obs is not None else {}
        detail = ((origin_record.provenance or {}) if origin_record is not None else {}).get("upc_detail")
        fields = _dispositions(
            r,
            detail,
            origin=origin,
            replay_source=first_read,
            run_id=origin,
            observed_at=hist.get("observed_at") or r.record.get("crawl_date"),
            code_of=lambda rid: _code(run_of(rid)),
        )
        sources = _sources(prov, fields)[0]
        named = {str(v.get("fetch_id")) for v in sources.values() if isinstance(v, Mapping)}
        hashes.update(_stored_hashes(s, named - set(hashes)))
        rows.append(
            {
                "key": r.upc,
                "item_id": _item_id(r, detail),
                "url": r.record.get("url"),
                "status": r.status,
                "observation_kind": "carried_forward" if hist else "replayed" if replay_source else "fresh",
                # A replay's row was observed by its source run (that run's time and stored page); the replay
                # read it again with its own code ("code"). A row carried from a replay says the same of it.
                "observed_by_run": first_read or origin,
                **({"read_again_by_run": origin} if first_read else {}),
                "observed_at": iso(obs.observed_at) if obs is not None else hist.get("observed_at"),
                "crawl_date": r.record.get("crawl_date"),
                "code": _code(run_of(origin)),
                "page": page_of(obs.page_fetch_id if obs is not None else hist.get("page_fetch_id")),
                "listing": prov.get("listing"),
                "listing_url": prov.get("listing_url"),
                "result_page": prov.get("page"),
                "position": prov.get("position"),
                "local_offer": prov.get("local_offer"),
                "assortment": prov.get("assortment"),
                **({"earlier_in_run": _earlier_in_run(prov)} if prov.get("earlier_in_run") else {}),
                "fields": _with_hashes(sources, hashes),
                "field_observed_at": prov.get("field_observed_at") or {},
                "upc": {
                    "status": (detail or {}).get("status"),
                    "observed_at": (detail or {}).get("upc_observed_at")
                    or fields["upc"].get("observed_at")
                    or (detail or {}).get("requested_at"),
                    "page_fetch_id": fields["upc"].get("page_fetch_id"),
                    "reason": (detail or {}).get("reason"),
                    "reused_from_run": ((detail or {}).get("reused_from") or {}).get("run_id"),
                },
                "weight": {
                    "observed_at": (detail or {}).get("weight_observed_at")
                    or (prov.get("field_observed_at") or {}).get("weight"),
                    "page_size": (detail or {}).get("size"),
                },
                "dispositions": fields,
                "carried": {
                    "why_not_observed": hist.get("why_not_observed"),
                    "age_days": hist.get("age_days"),
                    "replay_of": hist.get("replay_of"),
                }
                if hist
                else None,
            }
        )
    return {
        "run_id": run_id,
        "mode": run.mode if run is not None else None,
        "code": _code(run),
        "generated_at": iso(utcnow()),
        "about": (
            "One entry per exported row (products.json): the run and time that observed it, the code "
            "revision of that run, the stored page with its SHA-256 and store checks, the store-assortment "
            "decision, each field's source and observation time, and the UPC outcome. A carried-forward row "
            "points to its own earlier run. A replay's row is 'replayed': observed by the replay's source "
            "run (observed_by_run, at observed_at, on its stored page) and read again by the replay "
            "(read_again_by_run) with the code in 'code'; never a fresh observation. A row carried from a "
            "replay names the same two runs."
        ),
        "rows": rows,
    }


def supporting_log(s: Session, run_id: str) -> dict[str, Any]:
    from walmart_headless.collection import segments as seg_stats  # collection imports publishing

    run = s.get(Run, run_id)
    segments = list(
        s.scalars(
            select(CollectionSegment)
            .where(CollectionSegment.run_id == run_id)
            .order_by(CollectionSegment.started_at, CollectionSegment.id)
        )
    )
    last_segment = segments[-1].id if segments else None
    replay_source = _replay_source(run)
    runs: dict[str, dict[str, Any]] = {}

    def code_of(rid: str) -> dict[str, Any]:
        if rid not in runs:
            runs[rid] = _code(s.get(Run, rid))
        return runs[rid]

    first_seen: dict[str, ProductObservation] = {}
    for seen in s.scalars(
        select(ProductObservation)
        .where(ProductObservation.run_id == run_id, ProductObservation.source.in_(RECORD_SOURCES))
        .order_by(ProductObservation.observed_at, ProductObservation.id)
    ):
        first_seen.setdefault(seen.upc, seen)

    records: dict[str, Any] = {}
    observed = {
        "fresh": 0,
        "fresh_earlier_segment": 0,
        "replayed": 0,
        "carried_forward": 0,
        "not_recorded": 0,
    }
    upc_outcomes: dict[str, int] = {}
    by_status: dict[str, int] = {}
    rows = list(s.scalars(select(RecordRow).where(RecordRow.run_id == run_id).order_by(RecordRow.upc)))
    # What the file says of each row's fields, then the stored pages it names, read once.
    named: dict[str, tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]]] = {}
    for r in rows:
        o = first_seen.get(r.upc)
        extra = dict(r.provenance or {})
        historical = extra.get("historical")
        origin, origin_record, source_obs = _origin(s, r, run_id) if historical else (run_id, r, o)
        detail = ((origin_record.provenance or {}) if origin_record is not None else {}).get("upc_detail")
        named[r.upc] = _sources(
            dict(source_obs.provenance or {}) if source_obs is not None else {},
            _dispositions(
                r,
                detail,
                origin=origin,
                replay_source=_first_read(s, origin, historical or {}, replay_source),
                run_id=origin,
                observed_at=(historical or {}).get("observed_at") or r.record.get("crawl_date"),
                code_of=code_of,
            ),
        )
    hashes = _stored_hashes(
        s,
        {
            str(src.get("fetch_id"))
            for fields, _, _ in named.values()
            for src in fields.values()
            if isinstance(src, Mapping)
        },
    )
    for r in rows:
        o = first_seen.get(r.upc)
        prov: dict[str, Any] = dict(o.provenance or {}) if o is not None else {}
        segment = prov.get("segment")
        earlier = None if segment is None or last_segment is None else segment != last_segment
        extra = dict(r.provenance or {})
        historical = extra.get("historical")
        sources, missing, missing_kind = named[r.upc]
        if historical:
            kind = "carried_forward"
        elif o is None:
            kind = "not_recorded"
        elif replay_source:
            kind = "replayed"
        else:
            kind = "fresh_earlier_segment" if earlier else "fresh"
        observed[kind] += 1
        by_status[r.status] = by_status.get(r.status, 0) + 1
        detail = extra.get("upc_detail")
        if r.status in EXPORTED_STATUSES and not historical:
            key = str((detail or {}).get("status", "none"))
            upc_outcomes[key] = upc_outcomes.get(key, 0) + 1
        records[r.upc] = {
            "observation_kind": "carried_forward" if historical else "replayed" if replay_source else "fresh",
            # For a carried-forward product: the earlier run's observation (run, page, date, age, prices) and
            # why this run did not observe it.
            "historical": historical,
            # The product's own page, read for the UPC/GTIN its result page did not state: extracted,
            # absent_in_source, blocked, request_failed, parse_failed, identity_mismatch or not_attempted,
            # with the page fetch, time, HTTP status, body hash and JSON path (or the earlier run reused).
            "upc_detail": _read_again(detail, replay_source, run_id) if replay_source else detail,
            "upc_source": extra.get("upc_source"),  # the earlier sample of product pages (release 1.0.0)
            # Store assortment apart from the current offer: verified on this page, verified by an earlier
            # run (exported without a local price), unresolved (not exported), or not decided.
            "assortment": prov.get("assortment"),
            # The states the run's earlier tiles of the product showed before the one the record is kept
            # from (release 1.3.1: a record holds the product's latest state in the run).
            **({"earlier_in_run": _earlier_in_run(prov)} if prov.get("earlier_in_run") else {}),
            "status": r.status,
            "exported": r.status in EXPORTED_STATUSES,
            "reasons": list(r.reasons or []),
            "flags": list(r.flags or []),
            "observation": {
                "page_fetch_id": o.page_fetch_id if o is not None else None,
                "observed_at": iso(o.observed_at) if o is not None else None,
                "segment": segment,
                "browser_session": prov.get("session"),
                "node": prov.get("node"),
                "step": prov.get("step"),
                "listing": prov.get("listing"),  # Walmart: the listing and result page the product was on
                "page": prov.get("page"),
                "position": prov.get("position"),
                "earlier_segment": earlier,
            },
            # Each field's real source, the capture it names with that capture's SHA-256: a value from a
            # product's own page names that page and its run, time and revision, also when it is reused
            # (release 1.5.2). A carried row names its own earlier run's sources.
            "fields": _with_hashes(sources, hashes),
            "missing": missing,
            # Walmart: why each empty field is empty, by kind: source_absent (a page was read and does not
            # show it), extraction_failed (shown, not read), context_failed (not the store's local offer),
            # rule; for a UPC or size, also not_attempted, budget_deadline_interruption, blocked,
            # request_failed, parse_failure, identity_mismatch, conflicting_evidence.
            "missing_kind": missing_kind,
            "local_offer": prov.get("local_offer"),
            "source_check": prov.get("source_check") or {},
            "offers": prov.get("offers") or [],
            "site_data": (o.structured or {}) if o is not None else {},
        }
    return {
        "run_id": run_id,
        "mode": run.mode if run is not None else None,
        "generated_at": iso(utcnow()),
        "about": (
            "Supporting log of the products file: field sources, missing-value reasons, store and "
            "fulfillment checks against the site's own data, offer details, the store-assortment decision "
            "apart from the current offer, the UPC outcome of each product's own page, and the collection "
            "segment that observed each product. 'observation_kind' is 'fresh' (observed by this run; "
            "'observation.earlier_segment' is true when an earlier segment of this resumed run observed "
            "it) or 'carried_forward' (not observed by this run: an earlier run's verified observation kept "
            "unchanged, with its own crawl date, in 'historical'). A replay's products are 'replayed': "
            "observed by the replay's source run (replay_of), read again from its stored pages by this run's "
            "code; never fresh observations. A replay's UPC outcomes name the run that requested each "
            "product page (upc_detail.observed_by_run) and the replay (upc_detail.read_again_by_run)."
        ),
        **({"replay_of": replay_source} if replay_source else {}),
        # Each collection segment with its statistics from durable observations (the provider ledger, the
        # observations, the pages) beside its own counters; a segment a killed process left open says so,
        # with the bounds of its unobserved end (collection/segments.py).
        "segments": [
            {**g, "stop_code": g["recorded"]["stop_code"]}
            for g in seg_stats.run_statistics(s, run_id)["segments"]
        ],
        "counts": {
            "records": len(records),
            "by_status": by_status,
            "observed": observed,
            ("upc_outcomes_of_replayed_exported" if replay_source else "upc_outcomes_of_fresh_exported"): (
                upc_outcomes
            ),
        },
        "records": records,
    }
