"""Coverage reconciliation of a run: one row per scope unit (``walmart-collector coverage-report``).

A scope unit is a listing the run read or decided not to read: a CSV row's own listing, a subcategory
listing its category page names, or a child category a listing's "Departments" facet names. Each row says,
from the run's own records (node coverage, result pages, store attestations, memberships, observations,
records and follow-up outcomes):

* the parent CSV row and category, the listing's URL and how it was found (navigation evidence);
* the store and fulfillment its pages were checked for, and how many passed; the fulfillment each result
  page's grid was filtered for, from the grid's own data (``Pickup``, or ``none``: the store's unfiltered
  grid, whose reported total counts out-of-stock and shipping-only items too; release 1.4.1);
* the total the listing reported on each page and when, the pages visited and their page fetches;
* raw placements, distinct organic identities, identities seen only in sponsored placements, duplicate
  placements, and the products of other modules on its pages (not results of the listing);
* variant identities its tiles named, and what the follow-ups made of them and of its sponsored-only
  products;
* approximate-weight exclusions, other exclusions by reason, retained unavailable products (exported
  without a current local offer, and products carried forward from earlier runs);
* the signed difference between the reported total and the identities placed (an overcount is negative,
  never clamped to zero), the exact balance that holds if one does, the completion status the run recorded
  and the status the release 1.3.1 rule gives from the same stored data.

No threshold is applied: a listing is complete only at the last page the site serves, with a stable
reported total balanced exactly by its organic identities, or by its organic and sponsored-only identities
(``reconciliation_basis``). A result window the site does not serve beyond stays "accessible pages
exhausted; coverage incomplete"; more identities than reported is an overcount to reconcile. CSV rows that
the run did not plan are listed as such.
"""

from __future__ import annotations

import csv
import io
from collections import Counter, defaultdict
from collections.abc import Mapping
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from walmart_headless.collection.walmart import (
    FINAL_ENDS,
    WINDOW_ENDS,
    Listing,
    page_placements,
    reconcile_listing,
    reported_totals,
)
from walmart_headless.core import jsonvalues as jv
from walmart_headless.core.timeutil import iso
from walmart_headless.db.models import (
    CategorySource,
    Event,
    MembershipRow,
    NodeCoverage,
    PageFetch,
    ProductObservation,
    RecordRow,
    Run,
    StoreAttestation,
    Task,
)

EXPORTED = ("valid", "exported_not_valid")
UNAVAILABLE_FLAGS = ("NO_LOCAL_OFFER", "NO_PICKUP_OFFER", "OUT_OF_STOCK")
WINDOW_TEXT = "accessible pages exhausted; coverage incomplete"
# Listing states that are no completion decision (a limit, a choice, an open read): kept as recorded.
NOT_DECIDED = frozenset({"CAPPED", "SKIPPED", "PENDING", "IN_PROGRESS", "PARTITIONED"})
COLUMNS = (
    "csv_row",
    "category",
    "listing_id",
    "listing_name",
    "url",
    "found_via",
    "parent_listing",
    "navigation_evidence",
    "store_id",
    "fulfillment",
    "store_checks_passed",
    "store_checks_failed",
    "grid_fulfillment_filter",
    "reported_total",
    "totals_reported",
    "total_observed_at",
    "pages_visited",
    "page_fetches",
    "raw_placements",
    "organic_placements",
    "distinct_identities",
    "sponsored_only_in_listing",
    "placed_identities",
    "distinct_with_children",
    "duplicate_placements",
    "sponsored_placements",
    "sponsored_only_products",
    "other_module_products",
    "variant_identities_named",
    "variant_identities_not_own_tile",
    "follow_up_outcomes",
    "approx_weight_exclusions",
    "other_exclusions",
    "retained_unavailable",
    "carried_forward",
    "difference_organic",
    "difference_placed",
    "reconciliation_basis",
    "unresolved_difference",
    "status",
    "status_rule_1_3_1",
    "end",
    "stop_reason",
)


def _listings_of(s: Session, run_id: str) -> dict[str, tuple[Mapping[str, object], Listing]]:
    """Every listing of the run's listing tasks (their checkpoints, each value checked), by listing id,
    with its CSV row."""
    out: dict[str, tuple[Mapping[str, object], Listing]] = {}
    for task_id, raw in s.execute(
        select(Task.id, Task.cursor)
        .where(Task.run_id == run_id, Task.kind == "listing_node")
        .order_by(Task.id)
    ):
        cursor = jv.obj(raw, f"checkpoint of task {task_id}")
        node = jv.obj(cursor.get("node"), f"checkpoint of task {task_id}: node")
        for i, item in enumerate(
            jv.objects(cursor.get("listings"), f"checkpoint of task {task_id}: listings")
        ):
            lst = Listing.from_dict(item, f"checkpoint of task {task_id}: listings[{i}]")
            out.setdefault(lst.id, (node, lst))
    return out


def rule_status(lst: Listing, organic: set[str], sponsored: set[str]) -> tuple[str, dict[str, Any]]:
    """The completion status the release 1.3.1 rule gives a listing from the run's stored data (its
    result pages and memberships), and the reconciliation it rests on. A state that is no completion
    decision (a limit, a choice, a partition, an open read) is kept as recorded."""
    totals = reported_totals(lst.pages)
    r = reconcile_listing((organic, sponsored), totals, lst.total, page_placements(lst.pages))
    if lst.status in NOT_DECIDED or lst.note:
        return lst.status, r
    if lst.status == "EMPTY" and lst.total in (0, None) and not organic:
        return "EMPTY", r
    if lst.total is None or lst.end not in FINAL_ENDS | WINDOW_ENDS or not r["total_stable"]:
        return "INCOMPLETE", r
    if r["basis"]:
        return "DONE", r
    return ("INCOMPLETE" if r["placed"] < lst.total else "INCOMPLETE_OVERCOUNT"), r


def reconcile(s: Session, run_id: str) -> dict[str, Any]:
    run = s.get(Run, run_id)
    if run is None:
        raise ValueError(f"unknown run {run_id}")
    snap = jv.obj(run.config_snapshot, f"run {run_id}: config_snapshot")
    store = jv.obj(snap.get("store"), f"run {run_id}: config_snapshot.store")
    sources = {c.id: c for c in s.scalars(select(CategorySource).where(CategorySource.retailer == "walmart"))}
    listings = _listings_of(s, run_id)
    coverage = {
        c.taxonomy_id: c for c in s.scalars(select(NodeCoverage).where(NodeCoverage.run_id == run_id))
    }
    fetch_at = {
        f.id: f
        for f in s.scalars(
            select(PageFetch).where(
                PageFetch.run_id == run_id, PageFetch.purpose.in_(("listing", "category_page"))
            )
        )
    }
    att: dict[str, str] = {}
    for a in s.scalars(select(StoreAttestation).where(StoreAttestation.run_id == run_id)):
        fid = jv.text(jv.obj(a.checks, f"attestation {a.id}: checks").get("fetch_id"), f"attestation {a.id}")
        if fid:
            att[fid] = a.result
    placements: dict[str, Counter[str]] = defaultdict(Counter)
    keys_by_listing: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for m in s.scalars(select(MembershipRow).where(MembershipRow.run_id == run_id)):
        lid = m.taxonomy_id or ""
        placements[lid][m.via] += 1
        keys_by_listing[lid][m.via].add(m.upc)
    first_listing: dict[str, str] = {}
    variants_named: dict[str, set[str]] = defaultdict(set)
    cards: set[str] = set()  # products seen as their own organic tile
    for upc, source, prov in s.execute(
        select(ProductObservation.upc, ProductObservation.source, ProductObservation.provenance)
        .where(ProductObservation.run_id == run_id, ProductObservation.source.in_(("card", "pdp")))
        .order_by(ProductObservation.observed_at, ProductObservation.id)
    ):
        p = jv.obj(prov, f"provenance of observation {upc}")
        lid = jv.text(p.get("listing"), f"{upc}: listing")
        first_listing.setdefault(upc, lid)
        if source == "card":
            cards.add(upc)
        for i, v in enumerate(jv.objects(p.get("variant_siblings"), f"{upc}: variant_siblings")):
            variants_named[lid].add(f"wm:{jv.text(v.get('item_id'), f'{upc}: variant_siblings[{i}]')}")
    own_tiles = {k for by in keys_by_listing.values() for keys in by.values() for k in keys}
    records = list(s.scalars(select(RecordRow).where(RecordRow.run_id == run_id).order_by(RecordRow.upc)))
    excluded: dict[str, Counter[str]] = defaultdict(Counter)
    approx: Counter[str] = Counter()
    unavailable: Counter[str] = Counter()
    carried: Counter[str] = Counter()
    for r in records:
        if r.status == "historical":
            hist = jv.obj(jv.obj(r.provenance, f"record {r.upc}").get("historical"), f"record {r.upc}")
            carried[jv.text(hist.get("listing"), f"record {r.upc}: historical.listing")] += 1
            continue
        lid = first_listing.get(r.upc, "")
        if r.status == "excluded":
            for reason in r.reasons or []:
                if reason == "APPROX_WEIGHT":
                    approx[lid] += 1
                else:
                    excluded[lid][reason] += 1
        elif r.status in EXPORTED and any(f in (r.flags or []) for f in UNAVAILABLE_FLAGS):
            unavailable[lid] += 1
    follow: dict[str, Counter[str]] = defaultdict(Counter)
    follow_rows: list[dict[str, Any]] = []
    for e in s.scalars(
        select(Event)
        .where(Event.run_id == run_id, Event.code.like("FOLLOW_UP_%"))
        .order_by(Event.ts, Event.id)
    ):
        if e.code == "FOLLOW_UP_DONE":
            continue
        d = dict(jv.obj(e.data, f"event {e.id}: data"))
        follow[jv.text(d.get("listing"), f"event {e.id}: listing")][f"{d.get('kind')}:{d.get('status')}"] += 1
        follow_rows.append({"at": iso(e.ts), **d})
    rows: list[dict[str, Any]] = []
    children: dict[str, list[str]] = defaultdict(list)
    for lid, (_, lst) in listings.items():
        if lst.parent:
            children[lst.parent].append(lid)

    def tree(lid: str) -> list[str]:
        out = [lid]
        for c in children.get(lid, []):
            out.extend(tree(c))
        return out

    for lid, (node, lst) in listings.items():
        cov = coverage.get(lid)
        part = jv.obj(cov.partition if cov is not None else None, f"node coverage {lid}: partition")
        stored_pages = jv.objects(part.get("result_pages"), f"node coverage {lid}: result_pages")
        pages: list[Mapping[str, Any]] = [*stored_pages] if stored_pages else [*lst.pages]
        src = sources.get(jv.text(node.get("category_source_id"), f"listing {lid}: node"))
        organic = keys_by_listing[lid]["organic"]
        paid = keys_by_listing[lid]["paid"]
        union = set().union(*(keys_by_listing[x]["organic"] for x in tree(lid)))
        total = lst.total
        fetch_ids = [str(p.get("fetch_id")) for p in pages if p.get("fetch_id")]
        reported = [p for p in pages if p.get("reported_total") is not None]
        observed_at = None
        if reported:
            last = fetch_at.get(str(reported[-1].get("fetch_id")))
            observed_at = iso(last.started_at) if last is not None else None
        via = lst.via
        if via == "category_page":
            evidence = f"named by the category page {jv.text(node.get('url'), f'listing {lid}: node.url')}"
        elif via == "departments_facet":
            evidence = f"named by the Departments facet of listing {lst.parent} (its result page 1)"
        elif via == "configured":
            evidence = "configured subcategory listing (its id extends the row's category id)"
        else:
            evidence = "the CSV row's own listing"
        status = lst.status
        reason = lst.reason or lst.note
        rechecked, rec = rule_status(lst, organic, paid)
        if lst.status == "PARTITIONED":
            # A partitioned listing balances with its child categories (never their totals added up).
            tree_paid = set().union(*(keys_by_listing[x]["paid"] for x in tree(lid)))
            totals = reported_totals(lst.pages)
            tiles = sum(page_placements(listings[x][1].pages) for x in tree(lid) if x in listings)
            rec = reconcile_listing((union, tree_paid), totals, total, tiles)
        named = variants_named.get(lid, set())
        other_modules = sum(
            jv.integer(m.get("products"), f"listing {lid}: other_modules.products") or 0
            for p in pages
            for m in jv.objects(p.get("other_modules"), f"listing {lid}: other_modules")
        )
        rows.append(
            {
                "csv_row": src.csv_row_index if src is not None else None,
                "category": jv.text(node.get("category"), f"listing {lid}: node.category"),
                "listing_id": lid,
                "listing_name": lst.name,
                "url": lst.url,
                "found_via": via,
                "parent_listing": lst.parent or None,
                "navigation_evidence": evidence,
                "store_id": store.get("location_id"),
                "fulfillment": store.get("modality"),
                "store_checks_passed": sum(1 for f in fetch_ids if att.get(f) == "PASS"),
                "store_checks_failed": sum(1 for f in fetch_ids if att.get(f) == "FAIL"),
                # Per result page; a page recorded before release 1.4.1 kept no filter.
                "grid_fulfillment_filter": [str(p.get("grid_filter") or "not recorded") for p in pages],
                "reported_total": total,
                "totals_reported": rec["totals_reported"],
                "total_observed_at": observed_at,
                "pages_visited": [p.get("page") for p in pages],
                "page_fetches": fetch_ids,
                "raw_placements": sum(int(p.get("products") or 0) for p in pages),
                "organic_placements": placements[lid]["organic"],
                "distinct_identities": len(organic),
                "sponsored_only_in_listing": len(paid - organic),
                "placed_identities": len(organic | paid),
                "distinct_with_children": len(union),
                "duplicate_placements": placements[lid]["organic"] - len(organic),
                "sponsored_placements": placements[lid]["paid"],
                "sponsored_only_products": len(paid - organic - cards),
                "other_module_products": other_modules,
                "variant_identities_named": len(named),
                "variant_identities_not_own_tile": len(named - own_tiles),
                # Counts by outcome and by reason, sorted: the same records always give the same report.
                "follow_up_outcomes": dict(sorted(follow.get(lid, {}).items())),
                "approx_weight_exclusions": approx[lid],
                "other_exclusions": dict(sorted(excluded.get(lid, {}).items())),
                "retained_unavailable": unavailable[lid],
                "carried_forward": carried[lid],
                "difference_organic": None if total is None else total - rec["organic"],
                "difference_placed": rec["difference"],
                "reconciliation_basis": rec["basis"],
                "unresolved_difference": rec["unresolved_difference"],
                "status": status,
                "status_rule_1_3_1": rechecked,
                "end": lst.end or None,
                "stop_reason": reason
                or (
                    "the listing's distinct products reach its reported total"
                    if status == "DONE"
                    else ("the listing shows 0 results" if status == "EMPTY" else "")
                ),
            }
        )
    planned = {jv.text(n.get("category_source_id"), "listing node") for n, _ in listings.values()}
    plan_nodes = jv.objects(
        jv.obj(snap.get("plan"), f"run {run_id}: plan").get("nodes"), f"run {run_id}: plan"
    )
    planned |= {jv.text(n.get("category_source_id"), f"run {run_id}: plan node") for n in plan_nodes}
    not_planned = [
        {"csv_row": c.csv_row_index, "category": c.category_name, "url": c.url, "enabled": c.enabled}
        for c in sorted(sources.values(), key=lambda c: c.csv_row_index)
        if c.id not in planned
    ]
    statuses = Counter(r["status"] for r in rows)
    rechecks = Counter(r["status_rule_1_3_1"] for r in rows)
    window = sum(1 for r in rows if WINDOW_TEXT in (r["stop_reason"] or ""))
    return {
        "run_id": run_id,
        "store": dict(store),
        "provider": snap.get("provider"),
        "pilot": bool(snap.get("pilot")),
        "scope_units": len(rows),
        "status_counts": dict(statuses),
        "status_counts_rule_1_3_1": dict(rechecks),
        "result_window_units": window,
        "csv_rows_not_planned": not_planned,
        "coverage_complete": bool(rows)
        and not not_planned
        and set(rechecks) <= {"DONE", "EMPTY", "SKIPPED"}
        and set(statuses) <= {"DONE", "EMPTY", "SKIPPED"},
        "rows": rows,
        "follow_ups": follow_rows,
    }


def as_csv(rows: list[dict[str, Any]], columns: tuple[str, ...] = COLUMNS) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(columns), extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: (";".join(map(str, v)) if isinstance(v, list) else v) for k, v in r.items()})
    return buf.getvalue()


FOLLOW_COLUMNS = (
    "at",
    "kind",
    "item_id",
    "status",
    "reason",
    "listing",
    "listing_name",
    "category",
    "named_by",
    "seed",
    "queued_from",
    "url",
    "page_fetch_id",
    "requested_at",
    "store_context",
    "category_evidence",
    "record_status",
    "reasons",
    "upc",
    "credits",
)
