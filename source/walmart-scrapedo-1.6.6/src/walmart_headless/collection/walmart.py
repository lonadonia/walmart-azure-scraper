"""Live collection of one Walmart store through a page provider, on the run pipeline's tasks (headless).

A ``preflight`` task, one ``listing_node`` task per row of Walmart's category CSV, two ``follow_up`` tasks
(after every listing), then ``assemble``, ``validate`` and ``export``. The run's limits and a stop request
are checked before every request; a refusal (HTTP 403/429, "Robot or human?"), a page not priced for the
store, or a page without its data stops the run for review; nothing is retried with another identity.

Provider. One per run (``collection.provider``, recorded in the run's snapshot; a change of provider is
another run): Scrape.do's store-scoped endpoint (``/plugin/walmart/store`` with the store's ``storeid`` and
``zipcode``), or the Oxylabs Web API's Walmart source (``/v1/scrape/walmart`` with ``store_id`` and
``fulfillment_type``). Either returns Walmart's own page for the store.

Store and fulfillment. The request parameters are recorded but never taken as proof: Walmart's store page
must describe the configured store (number, ZIP, house number of the address), and every listing page must
name the store with the configured intent (``pageMetadata.location``) and show fulfillment lines for that
store only. A page whose products show no line for the store is accepted only when its own location context
names the store and no product names another store.

Local offers (:func:`walmart_headless.sites.walmart.records.local_offer`). Store assortment, availability
and the local price are decided apart (:meth:`WalmartCollector.assortment`). A price is kept only for
Walmart's own offer with a line of the configured fulfillment for the store; a Delivery line of the store
shows the product is the store's but not its Pickup price (exported without prices). Marketplace and
shipping-only offers are recorded as excluded, with the reason. A product shown with no line for the store
(out of stock, or no fulfillment at all) is the store's only when an earlier run (or an earlier tile of the
same run) verified it there: it is then exported with its identity and size and empty prices; otherwise its
assortment is unresolved and it is recorded, not exported. The marketplace, shipping or unverified price is
never adopted.

A product's latest state in the run (release 1.3.1; :meth:`WalmartCollector.repeated_tile`). A product is
recorded once per run. When a tile observed later in the run shows another local state (availability, the
store's line, a price, an offer), the record is decided again from that tile, and the state it replaces is
kept in the observation's ``earlier_in_run`` with its page and time. Release 1.3.0 kept the first tile and
counted later ones as duplicates.

Catalogue. A CSV row is a category page (``/cp/``) or a listing (``/browse/``). A category page is read
once (its data names its subcategory listings; the CSV's exclusions and the run's subcategory limit are
applied); each listing is read with Walmart's own ``page=N`` links. Products are de-duplicated by identity
(the UPC when shown, else Walmart's item ID ``wm:<id>``; each size, pack and variant is its own item), and
every placement is kept. The task's checkpoint keeps the listing and the next page to read, so a resumed
task continues there. A listing link that serves a category page instead of a listing (its data is the
page ``/cp/[...categoryParams]``: links, no result grid) is ``INCOMPLETE`` (``CATEGORY_PAGE``) with the
listings that page links, and the run goes on (release 1.6.2); so is a link the site answers with its own
not-found page (its data is the page ``/404``: ``NOT_FOUND``, release 1.6.3); any other page without a result
grid stops the run (``ABNORMAL_RESULT``). A listing whose first page reports 0 results (``aggregatedCount``)
and shows none is ``EMPTY`` once the page's own data names the store and the fulfillment, whatever other
modules it shows (release 1.6.4); a first page that reports results and shows none stops the run.

Completion is decided from evidence, never from the last page reached. Every result page is recorded (its
products, new identities, the listing's reported total and page count); only its result grid is the listing's
results (:func:`page_data.page_items`). A listing is ``DONE`` only when it ended (an empty later page, or its
last page) with a total that stayed the same on every page and that what its results placed balances exactly
(:func:`close_listing`, :func:`reconcile_listing`: its organic identities, those plus its sponsored-only
identities, or its tiles; no tolerance threshold, and more identities than reported is an overcount, never
done); an empty later page is accepted as an end only when its own data still names the store and fulfillment.
A listing that keeps serving pages past ``SAFETY_MAX_PAGES`` (50; Walmart links at most 25) stops
``INCOMPLETE`` (``SAFETY_LIMIT``). Otherwise it is ``INCOMPLETE`` with the reason: the site's result window
("accessible pages exhausted; coverage incomplete": an empty page, or the last linked page, while the listing
reports more results than were served, as Walmart's listings did at page 11 on 2026-10-23), a repeated page, a
contradictory page count. The advertised total can include offers that are not the store's, so a gap is
reported, never taken as proof either way. A listing larger than its result window is partitioned, when
``coverage.partition_large_listings`` is on, through the child categories its own "Departments" facet names
(ids that extend the listing's id): each child is read as its own listing, linked to its parent. Children may
overlap: the parent is complete only when the distinct products of the parent and all its children balance its
total exactly; counts are never added up.

Automated canary. After the first result page that recorded products, the run continues only when that
page passes automated checks (records parsed, required fields filled, every valid record matching the
page's own JSON read independently); otherwise it stops with ``CANARY_CHECK_FAILED`` and the reasons.

Follow-ups (:meth:`WalmartCollector.h_follow_up`). After every listing, the product pages of products the
run saw only in sponsored placements and of the variant siblings result tiles name (each its own item id
and link in the tile's ``variantCriteria``) but never show as their own tile: the options of every result
tile, the one a product was recorded from and its other tiles (a repeated tile, which may name options the
first did not, or a sponsored tile; release 1.3.0 read the first only). Each page is requested in the
store's context and must identify the item, be shown for the store (``product.location``), and file the item
under the listing's category; the local offer and assortment are then decided as for a result page (an
advertisement alone establishes neither). Every candidate ends ``included``, ``duplicate``, ``excluded``
(with the reason), ``inaccessible`` (the page could not be read for the store) or ``not_attempted`` (with the
reason), in the task's checkpoint and the run's counts.
"""

from __future__ import annotations

import hashlib
import re
import zlib
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field, fields, replace
from datetime import datetime, timedelta
from time import monotonic
from typing import Any, cast
from urllib.parse import urlsplit

from selectolax.lexbor import LexborHTMLParser
from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from walmart_headless.acquisition import lineage, oxylabs
from walmart_headless.acquisition.errors import ProviderError, ProviderErrorKind
from walmart_headless.acquisition.oxylabs_session import RESULT_COST, OxylabsWalmartSession
from walmart_headless.acquisition.pages import ChallengeDetected, NotInSource, PageFetch
from walmart_headless.acquisition.scrapedo import WALMART_STORE_ENDPOINT, Key, Ledger, Transport, key_rows
from walmart_headless.acquisition.scrapedo import load_keys as scrapedo_keys
from walmart_headless.acquisition.scrapedo import redact as scrapedo_redact
from walmart_headless.acquisition.scrapedo_session import (
    FULFILLMENT_FACETS,
    WALMART_PAGE_COST,
    ScrapeDoWalmartSession,
)
from walmart_headless.assembly.offers import format_description
from walmart_headless.assembly.record_builder import (
    BuiltRecord,
    CategoryAssignment,
    FieldSource,
    RecordStatus,
    StoreFields,
    build_product_record,
)
from walmart_headless.checks import source_check
from walmart_headless.collection import follow_queue, retention
from walmart_headless.collection.base import (
    FINISHED_NODE,
    AbnormalPage,
    BaseCollector,
    offer_summaries,
)
from walmart_headless.collection.limits import StopCode, product_limit_code, product_room
from walmart_headless.collection.nodes import Node
from walmart_headless.collection.verification import StoreCheck, StoreVerification
from walmart_headless.config_file import CanaryConfig, HistoricalConfig
from walmart_headless.core import jsonvalues as jv
from walmart_headless.core.findings import DataMode, RecordFlag
from walmart_headless.core.ids import new_id
from walmart_headless.core.paths import PARSER_VERSION
from walmart_headless.core.schema import ordered_record
from walmart_headless.core.timeutil import iso, store_local_date
from walmart_headless.db import queue
from walmart_headless.db.models import (
    DETAIL_STATUSES,
    DetailObservation,
    FollowUpItem,
    MembershipRow,
    NodeCoverage,
    OfferObservationRow,
    ProductObservation,
    RecordRow,
    Run,
    StoreAttestation,
    Task,
)
from walmart_headless.db.observations import insert_memberships
from walmart_headless.publishing import dispositions
from walmart_headless.publishing.exports import record_sha256
from walmart_headless.publishing.supporting_log import field_dispositions
from walmart_headless.sites.walmart import pack_size as wps
from walmart_headless.sites.walmart import page_data as wpd
from walmart_headless.sites.walmart import records as wrec
from walmart_headless.sites.walmart.sanitize import sanitize_html as walmart_sanitize
from walmart_headless.worker.runner import RunStop, TaskContext
from walmart_headless.worker.runs import event, transition

WALMART_BASE = "https://www.walmart.com"
RETAILER = "walmart"
_GENERIC_LINK = re.compile(r"^(?:shop|see|view)\s+all$", re.I)
SAFETY_MAX_PAGES = 50  # Walmart links at most 25 result pages; a listing that keeps going is abnormal
STORE_LOGO_NOTE = "the store page's header shows no logo image (no image in its Walmart Homepage link)"
# Exclusion reasons that only say the page showed no local offer this time (assortment apart from offer).
NOT_LOCAL_REASONS = frozenset(
    {RecordFlag.LOCATION_UNATTESTED, RecordFlag.MARKETPLACE_OFFER, RecordFlag.SHIP_ONLY}
)
# The fields of a local offer: emptied for a verified product shown without a local offer.
OFFER_FIELDS = (
    "regular_price",
    "sale_price",
    "volume_deals_description",
    "volume_deals_price",
    "digital_deals_description",
    "digital_deals_price",
    "ppm",
)
# Product detail outcomes (``provenance.upc_detail.status``) that consumed a request.
DETAIL_FETCHED = frozenset(
    {"extracted", "absent_in_source", "blocked", "request_failed", "parse_failed", "identity_mismatch"}
)
# Opening a provider session needs room for robots.txt, the store page and one page (Oxylabs: results).
OXYLABS_MIN_SESSION = 3.0
FOLLOW_STATUSES = ("included", "duplicate", "excluded", "inaccessible", "not_attempted")


def follow_shard(item_id: str, shards: int) -> int:
    """The follow-up task, of the ``shards`` of its kind, that reads this product: the same one in every task
    and execution, so no two tasks of a kind read the same candidate."""
    return zlib.crc32(item_id.encode("utf-8")) % max(1, shards)


def merge_follow_summary(earlier: Mapping[str, Any] | None, summary: Mapping[str, Any]) -> dict[str, Any]:
    """A kind's follow-up summary over its tasks: counts add up, and the queue's state after the task is the
    latest one."""
    if not earlier:
        return dict(summary)
    merged = dict(earlier)
    for key, value in summary.items():
        if isinstance(value, int) and key != "queue_pending_after":
            merged[key] = int(merged.get(key) or 0) + value
        else:
            merged[key] = value
    return merged


def _name_key(name: str) -> str:
    """A subcategory name for comparisons: case and spacing ignored, and a final "s" (the client's CSV says
    'Farm Animals' where Walmart's navigation says 'Farm Animal')."""
    n = " ".join(name.casefold().split())
    return n[:-1] if n.endswith("s") else n


# -- state ----------------------------------------------------------------------------------------------


@dataclass
class Listing:
    name: str  # subcategory name as the category page shows it ("" for a CSV listing row)
    url: str
    id: str  # the listing's own ID (last path segment)
    note: str = ""  # why it is not read (excluded, limit), when it is not
    # PENDING | IN_PROGRESS | DONE | EMPTY | INCOMPLETE | PARTITIONED | SKIPPED | CAPPED
    status: str = "PENDING"
    pages_read: int = 0
    total: int | None = None  # results the listing reports (its latest result page)
    max_page: int | None = None
    seen: list[str] = field(default_factory=list)
    reason: str = ""
    # Why reading stopped: LAST_PAGE | EMPTY_PAGE | RESULT_WINDOW | REPEATED_PAGE | PAGE_LIMIT |
    # SAFETY_LIMIT | ROBOTS | IDENTITY | NOT_IN_SOURCE | CATEGORY_LIMIT | CATEGORY_PAGE | NOT_FOUND ("" while
    # reading).
    end: str = ""
    # How the listing was found: csv (the row itself), category_page, configured, departments_facet.
    via: str = ""
    parent: str = ""  # a child category's parent listing id (read because the parent exceeds its window)
    depth: int = 0
    # The direct child categories the listing's own "Departments" facet names (id, name, url).
    children: list[dict[str, str]] = field(default_factory=list)
    # One entry per result page read: products, organic, sponsored, new identities, reported totals.
    pages: list[dict[str, Any]] = field(default_factory=list)
    # Identities the listing's results showed in sponsored placements (an identity may also be organic).
    sponsored: list[str] = field(default_factory=list)
    # How the listing's served results compare with its reported total when it ended (reconcile_listing).
    reconciliation: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Mapping[str, object], where: str) -> Listing:
        """A listing of a stored checkpoint, each value checked (a checkpoint of an earlier release lacks
        the later fields: they read as empty)."""
        unknown = sorted(set(d) - {f.name for f in fields(cls)})
        if unknown:
            raise jv.CorruptJson(f"{where}: unknown listing fields {unknown}")

        def t(key: str) -> str:
            return jv.text(d.get(key), f"{where}.{key}")

        def n(key: str) -> int | None:
            return jv.integer(d.get(key), f"{where}.{key}")

        return cls(
            name=t("name"),
            url=t("url"),
            id=t("id"),
            note=t("note"),
            status=t("status") or "PENDING",
            pages_read=n("pages_read") or 0,
            total=n("total"),
            max_page=n("max_page"),
            seen=jv.texts(d.get("seen"), f"{where}.seen"),
            reason=t("reason"),
            end=t("end"),
            via=t("via"),
            parent=t("parent"),
            depth=n("depth") or 0,
            children=[
                {k: jv.text(v, f"{where}.children[{i}].{k}") for k, v in c.items()}
                for i, c in enumerate(jv.objects(d.get("children"), f"{where}.children"))
            ],
            pages=[dict(p) for p in jv.objects(d.get("pages"), f"{where}.pages")],
            sponsored=jv.texts(d.get("sponsored"), f"{where}.sponsored"),
            reconciliation=dict(jv.obj(d.get("reconciliation"), f"{where}.reconciliation")),
        )


# Ends that mean the site served fewer results than the listing reports (a partition may cover the rest).
WINDOW_ENDS = frozenset({"RESULT_WINDOW"})
# Ends at which the site has no more results to serve: the only ends a listing can be complete at.
FINAL_ENDS = frozenset({"LAST_PAGE", "EMPTY_PAGE"})


def reported_totals(pages: Sequence[Mapping[str, Any]]) -> list[int]:
    """The totals a listing's result pages reported. The 0 an empty page reports is no total: Walmart's
    empty page past its result window reports 0 results while the page before reported tens of thousands
    (2026-10-23), and the listing keeps its earlier count (``WalmartCollector._page``)."""
    return [
        p["reported_total"]
        for p in pages
        if isinstance(p.get("reported_total"), int) and (p["reported_total"] or int(p.get("products") or 0))
    ]


def page_placements(pages: Sequence[Mapping[str, Any]]) -> int:
    """Product tiles in the result stacks of the pages read (organic and sponsored, repeats included)."""
    return sum(int(p.get("products") or 0) for p in pages)


def reconcile_listing(
    identities: tuple[set[str], set[str]], totals: list[int], total: int | None, placements: int
) -> dict[str, Any]:
    """The served results of a listing (or a partition tree) against the total it reports.

    ``identities``: (organic, sponsored) identities its result stacks placed; ``totals``: every total its
    result pages reported; ``placements``: the product tiles of its result stacks on the pages read. The
    difference is signed (reported minus identities placed): an overcount is negative and is never
    clamped. ``basis`` names the exact balance that holds, if one does, with a stable total:

    * ``organic``: the distinct organic identities equal the total;
    * ``organic_and_sponsored``: with the identities seen only in sponsored placements, they equal it;
    * ``placements``: the tiles served equal it, and the identities are fewer only because sponsored tiles
      repeat organic products (live 2026-10-26, Apples: 39 reported, 39 tiles, 33 organic products and 6
      sponsored repeats of 6 of them). The repeats are counted per identity (``repeat_placements``).

    "" when none holds or the total changed while the listing was read. The basis is recorded with the
    outcome so a reviewer can tell which balance a completed listing rests on. ``unresolved_difference`` is
    what the total leaves unexplained: 0 when a basis holds (sponsored-only identities outside an organic
    total, or sponsored repeats of organic products, are explained), else the signed difference."""
    organic, sponsored = identities
    sponsored_only = sponsored - organic
    placed = len(organic) + len(sponsored_only)
    stable = len(set(totals)) <= 1
    basis = ""
    if total is not None and stable:
        if len(organic) == total:
            basis = "organic"
        elif placed == total:
            basis = "organic_and_sponsored"
        elif placements == total and placements >= placed:
            basis = "placements"
    return {
        "reported_total": total,
        "totals_reported": list(dict.fromkeys(totals)),
        "total_stable": stable,
        "organic": len(organic),
        "sponsored_only": len(sponsored_only),
        "placed": placed,
        "placements": placements,
        "repeat_placements": placements - placed,
        "difference": None if total is None else total - placed,
        "basis": basis,
        "unresolved_difference": None if total is None else (0 if basis else total - placed),
    }


BASIS_TEXT = {
    "organic": "the organic identities equal the total",
    "organic_and_sponsored": "the organic and sponsored-only identities equal the total",
    "placements": "the {placements} tiles served equal the total ({repeat_placements} sponsored tiles repeat "
    "organic products)",
}


def _served(r: Mapping[str, Any]) -> str:
    return f"{r['organic']} organic and {r['sponsored_only']} sponsored-only identities"


def listing_outcomes(listings: list[Listing]) -> list[dict[str, Any]]:
    """Each top-level listing's effective outcome. A partitioned listing counts the distinct identities of
    itself and all its child categories (never their counts added up) against its own reported total, and
    is complete only when they balance exactly and every child category ended."""
    by_parent: dict[str, list[Listing]] = {}
    for x in listings:
        if x.parent:
            by_parent.setdefault(x.parent, []).append(x)

    def tree(x: Listing) -> list[Listing]:
        out = [x]
        for c in by_parent.get(x.id, []):
            out.extend(tree(c))
        return out

    out: list[dict[str, Any]] = []
    for x in listings:
        if x.parent or x.status == "SKIPPED":
            continue
        members = tree(x)
        organic = set().union(*(set(m.seen) for m in members))
        sponsored = set().union(*(set(m.sponsored) for m in members))
        own = reported_totals(x.pages)
        r = reconcile_listing((organic, sponsored), own, x.total, page_placements(x.pages))
        status = x.status
        reason = x.reason
        if status == "PARTITIONED":
            open_children = [m for m in members[1:] if m.status in ("PENDING", "IN_PROGRESS")]
            if r["basis"] and not open_children:
                status = "DONE"
                reason = (
                    f"partition reconciled: {_served(r)} through the listing and {len(members) - 1} child "
                    f"categories = {x.total} reported"
                )
            elif any(m.status == "CAPPED" for m in members):
                status, reason = "CAPPED", "a page or product limit of this run stopped a child category"
            else:
                status = "INCOMPLETE"
                reason = (
                    f"partition does not reconcile with the listing: {_served(r)} through the listing and "
                    f"{len(members) - 1} child categories, {x.total} reported (difference {r['difference']})"
                    + (f"; {len(open_children)} child categories not read" if open_children else "")
                )
        out.append(
            {
                "id": x.id,
                "name": x.name,
                "url": x.url,
                "status": status,
                "listing_status": x.status,
                "end": x.end,
                "reason": reason,
                "total": x.total,
                "seen": len(x.seen),
                "distinct_with_children": len(organic),
                "placed_with_children": r["placed"],
                "difference": r["difference"],
                "basis": r["basis"],
                "unresolved_difference": r["unresolved_difference"],
                "children": [
                    {"id": m.id, "status": m.status, "total": m.total, "seen": len(m.seen), "end": m.end}
                    for m in members[1:]
                ],
            }
        )
    return out


def _short_whatever_the_count(r: Mapping[str, Any], reported: list[int]) -> bool:
    """The results served fall short of the smallest total the listing reported by more than its totals
    moved while it was read: short of the listing however the count is taken (release 1.6.2)."""
    low = min(reported)
    margin = max(reported) - low
    return bool(r["placed"] < low - margin and r["placements"] < low - margin)


def close_listing(lst: Listing, end: str, page: int, detail: str = "") -> None:
    """The listing stopped at ``page`` (``end``: why). ``DONE`` only at the last page the site serves, with
    a total that stayed the same on every page, and when what its results placed balances that total
    exactly (:func:`reconcile_listing`). Otherwise ``INCOMPLETE`` with the signed difference: fewer tiles
    than reported at the last page is a result-window end ("accessible pages exhausted"); more identities
    than reported is an overcount, and any other imbalance is unreconciled (both need reconciling:
    sponsored placements, scope, variants or a stale total).

    A total that changed while the listing was read is never reconciled. Release 1.6.2: when the site still
    served fewer results than the smallest total it reported, by more than the total moved, the pages ended
    short of the listing whatever its exact count, so that is a result-window end too and the listing is read
    through its child categories. Until 1.6.1 a total that moved by a few products hid such a shortfall (live
    2026-11-03, Laundry: 615, 613, 614 and 611 reported, page 11 of 16 empty, 393 served) and the listing was
    left unpartitioned."""
    totals = reported_totals(lst.pages)
    r = reconcile_listing((set(lst.seen), set(lst.sponsored)), totals, lst.total, page_placements(lst.pages))
    lst.reconciliation, lst.end = r, end
    served = f"{lst.pages_read} result pages, {_served(r)}"
    total = lst.total
    lst.status = "INCOMPLETE"
    reported = [t for t in r["totals_reported"] if isinstance(t, int)]
    if total is None:
        lst.reason = f"result page {page}: the listing reports no result count"
    elif end not in FINAL_ENDS:
        lst.reason = f"{detail or end}: {served}; {total} reported (difference {r['difference']})"
    elif not r["total_stable"] and reported and _short_whatever_the_count(r, reported):
        low, high = min(reported), max(reported)
        lst.end = "RESULT_WINDOW"
        lst.reason = (
            f"accessible pages exhausted; coverage incomplete: the site served {served} and no more "
            f"({detail or end.lower().replace('_', ' ')}), while the listing reported between {low} and "
            f"{high} results (the total changed while it was read: {r['totals_reported']}); not reconciled"
        )
    elif not r["total_stable"]:
        lst.reason = (
            f"the reported total changed while the listing was read ({r['totals_reported']}): {served}; "
            "not reconciled"
        )
    elif r["basis"]:
        lst.status = "DONE"
        basis = BASIS_TEXT[r["basis"]].format(**r)
        lst.reason = f"reconciled at the last page: {served}; {total} reported; {basis}"
    elif r["placed"] < total and r["placements"] < total:
        lst.end = "RESULT_WINDOW"
        lst.reason = (
            f"accessible pages exhausted; coverage incomplete: the site served {served} and no more "
            f"({detail or end.lower().replace('_', ' ')}), while the listing reports {total} results"
        )
    elif r["placed"] > total:
        lst.reason = (
            f"overcount: {served}, more than the {total} the listing reports (difference "
            f"{r['difference']}); reconciliation required"
        )
    else:
        lst.reason = (
            f"unreconciled: {served} in {r['placements']} tiles, {total} reported; reconciliation required"
        )
    lst.reason = lst.reason[:500]


@dataclass
class Cursor:
    """A listing task's checkpoint: the listings of its CSV row and where reading stands."""

    status: str = "IN_PROGRESS"
    reason: str = ""
    listings: list[Listing] | None = None  # None until a category page was read
    index: int = 0  # the listing being read
    page: int = 1  # its next page to read
    discovered: list[dict[str, Any]] = field(default_factory=list)  # every link the category page named

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> Cursor:
        raw = d.get("listings")
        return cls(
            status=str(d.get("status") or "IN_PROGRESS"),
            reason=str(d.get("reason") or ""),
            listings=None
            if raw is None
            else [
                Listing.from_dict(x, f"checkpoint listings[{i}]")
                for i, x in enumerate(jv.objects(raw, "checkpoint listings"))
            ],
            index=int(d.get("index") or 0),
            page=int(d.get("page") or 1),
            discovered=list(d.get("discovered") or []),
        )

    def as_dict(self, node: Node) -> dict[str, Any]:
        listings = self.listings or []
        seen = list(dict.fromkeys(k for lst in listings for k in lst.seen))
        # Top-level listings only: a child category's total is part of its parent's.
        totals = [lst.total for lst in listings if lst.total is not None and not lst.parent]
        return {
            "node": node.as_dict(),
            "status": self.status,
            "reason": self.reason,
            "listings": None if self.listings is None else [asdict(x) for x in self.listings],
            "index": self.index,
            "page": self.page,
            "discovered": self.discovered,
            # What the shared run outcome reads (BaseCollector.node_outcomes):
            "seen": seen,
            # The sum of the top-level listings' reported totals, for messages only: listings may overlap,
            # so coverage is decided per listing (listing_outcomes), never from this sum.
            "total": sum(totals) if totals else None,
            "steps_done": sum(lst.pages_read for lst in listings),
        }


def direct_listings(node: Node) -> list[Listing] | None:
    """The listings of a category row narrowed to subcategory listings named by their own ``/browse/`` path
    (or URL), when every one of them carries the row's category id in its listing id (``1115193_1071967``
    under Household Essentials, ``1115193``): they are read directly, without the category page. Each one's
    name comes from its own first result page, which must place it under the row's category (``_page``).
    ``None``: discover the row's listings on its category page."""
    if node.kind != "landing" or not node.only:
        return None
    out = []
    for entry in node.only:
        path = urlsplit(entry).path
        lid = wpd.listing_id(path)
        if not path.startswith("/browse/") or node.taxonomy_id not in lid.split("_"):
            return None
        out.append(Listing("", wpd.absolute(path), lid, via="configured"))
    return out


@dataclass
class Selection:
    """The store check of the current provider session."""

    store_page_fetch: str
    confirm_fetch: str
    details: wpd.StoreDetails
    observed_at: str
    result: dict[str, Any]
    logo: str = ""  # the logo image the store page's header shows (absolute URL)
    logo_ref: str = ""  # where it was read


@dataclass
class PageResult:
    products: int = 0
    new_keys: int = 0  # products this listing had not shown on an earlier page
    new_records: int = 0
    new_verified: int = 0
    duplicates: int = 0
    sponsored: int = 0
    excluded: int = 0
    capped: StopCode | None = None
    category_capped: bool = False


@dataclass
class TileBuild:
    """The record a result tile gives, with what its observation keeps
    (:meth:`WalmartCollector.tile_record`)."""

    built: BuiltRecord
    log: dict[str, Any]
    assortment: dict[str, Any]
    missing_kind: dict[str, str]
    field_observed_at: dict[str, str]

    @property
    def verified(self) -> bool:
        return self.built.status is RecordStatus.VALID


def local_state(
    record: Mapping[str, Any], status: str, reasons: Sequence[str], flags: Sequence[str]
) -> tuple[str, list[str], list[str], list[str]]:
    """What another tile of the same product can change: the status, its reasons and flags, and the local
    offer's fields. Identity fields (title, size, image, URL, UPC) do not count."""
    return status, sorted(reasons), sorted(flags), [str(record.get(f) or "") for f in OFFER_FIELDS]


def state_time(state: Mapping[str, Any]) -> datetime:
    """When a stored state (``earlier_in_run``) was observed."""
    return datetime.fromisoformat(str(state["observed_at"]).replace("Z", "+00:00"))


def displayed_approx(states: Sequence[Mapping[str, Any]]) -> dict[str, str] | None:
    """The approximate or estimated-weight wording the latest of ``states`` (this run's tiles of a product)
    that displayed one showed, traced to its tile (release 1.4.0); ``None`` when none did."""
    for st in sorted(states, key=state_time, reverse=True):
        log = (st.get("structured") or {}).get("walmart") or {}
        approx = log.get("approx_weight")
        if isinstance(approx, Mapping) and approx.get("text"):
            return {
                **{str(k): str(v) for k, v in approx.items()},
                "page_fetch_id": str(st.get("page_fetch_id") or ""),
                "observed_at": str(st.get("observed_at") or ""),
            }
    return None


def merged_siblings(*groups: Any) -> list[dict[str, Any]]:
    """The variant siblings several tiles of a product name, each item once (first naming kept)."""
    out: dict[str, dict[str, Any]] = {}
    for group in groups:
        for v in group or []:
            if isinstance(v, Mapping):
                out.setdefault(str(v.get("item_id")), dict(v))
    return list(out.values())


def category_verified(s: Session, run_id: str, category: str) -> int:
    return int(
        s.scalar(
            select(func.count(func.distinct(ProductObservation.upc))).where(
                ProductObservation.run_id == run_id,
                ProductObservation.provenance["verified"].as_boolean().is_(True),
                ProductObservation.provenance["category"].astext == category,
            )
        )
        or 0
    )


# -- the collector ------------------------------------------------------------------------------------


def _same_read(detail: Mapping[str, Any], hit: Mapping[str, Any]) -> bool:
    """Whether a product's detail outcome comes from the saved read ``hit`` (the same page fetch)."""
    reused = detail.get("reused_from")
    source = reused if isinstance(reused, Mapping) else detail
    fetch = source.get("page_fetch_id")
    return bool(fetch) and fetch == hit.get("page_fetch_id")


class WalmartCollector(BaseCollector):
    LISTING_SETTLE_MS = 0
    CAPTURE_KINDS: tuple[str, ...] = ("walmart_location",)
    # Walmart's listings show no UPC (product pages do): UPC is "scrape when available" there.
    REQUIRED_FIELDS: tuple[str, ...] = ("product_title", "url", "category")

    def __init__(
        self,
        pipe: Any,
        run_id: str,
        *,
        keys: list[Key] | None = None,
        oxylabs_key: Key | None = None,
        canary: CanaryConfig | None = None,
        historical: HistoricalConfig | None = None,
        **kw: Any,
    ):
        super().__init__(pipe, run_id, **kw)
        self._init_kw = {
            "keys": keys,
            "oxylabs_key": oxylabs_key,
            "canary": canary,
            "historical": historical,
            **kw,
        }
        self.selection: Selection | None = None
        self.modality = self.store.modality.value
        self.canary_cfg = canary or CanaryConfig()
        self.historical_cfg = historical or HistoricalConfig()
        with self.factory() as s:
            run = s.get(Run, run_id)
            snap = (run.config_snapshot or {}) if run is not None else {}
            counts = (run.counts or {}) if run is not None else {}
            self.run_mode = run.mode if run is not None else DataMode.LIVE.value
        self.pilot = bool(snap.get("pilot"))
        self.canary_done = (counts.get("canary") or {}).get("status") == "passed"
        # The run's page provider (its snapshot; runs made before 1.3.0 name Scrape.do).
        self.provider = str(snap.get("provider") or "scrapedo")
        # The provider's key from the environment (a secret file reference in production).
        self.scrapedo_keys: list[Key] = (
            (scrapedo_keys() if keys is None else keys) if self.provider == "scrapedo" else []
        )
        self.scrapedo_ledger: Ledger | None = (
            Ledger(self.factory, self.scrapedo_keys) if self.scrapedo_keys else None
        )
        self.oxylabs_key: Key | None = (
            (oxylabs.load_key() if oxylabs_key is None else oxylabs_key)
            if self.provider == "oxylabs"
            else None
        )
        self.oxylabs_ledger: oxylabs.OxylabsLedger | None = (
            oxylabs.OxylabsLedger(self.factory, self.oxylabs_key) if self.oxylabs_key else None
        )
        # Products verified at the store by earlier runs (loaded once per process; see retention.py).
        self.registry: dict[str, retention.Verified] | None = None
        # Only history observed before this time counts (a replay: what was known before the run it reads).
        self.history_before: datetime | None = None
        # Product detail pages (UPC): pages read in this process, consecutive failures, a pause reason.
        self.detail_reads = 0
        self.detail_failures = 0
        self.detail_paused: str | None = None
        self._upc_cache: dict[str, dict[str, Any]] | None = None
        # Follow-up product pages: consecutive refusals or failures, and a pause reason.
        self.follow_failures = 0
        self.follow_paused: str | None = None

    @property
    def base(self) -> str:
        if self.plan:
            parts = urlsplit(self.plan[0].url)
            return f"{parts.scheme}://{parts.netloc}"
        return WALMART_BASE

    @staticmethod
    def _origin(fetch: PageFetch) -> str:
        """The site a page was served from: its links and product URLs are on the same site."""
        parts = urlsplit(fetch.final_url or fetch.url)
        return f"{parts.scheme}://{parts.netloc}"

    @property
    def store_page_url(self) -> str:
        return self.store.store_page_url or f"{self.base}/store/{self.store.location_id}"

    def redact(self, text: str) -> str:
        text = scrapedo_redact(text, self.scrapedo_keys)
        return oxylabs.redact(text, self.oxylabs_key)

    @property
    def provider_label(self) -> str:
        return "Oxylabs Web API" if self.provider == "oxylabs" else "Scrape.do"

    # What the log says of the session's pages; a replay's names the run whose stored pages it reads.
    def store_method(self) -> str:
        return f"{self.provider_label} store-scoped requests (the provider applies the store; no click)"

    def store_selected_message(self) -> str:
        return (
            f"Walmart store {self.store.location_id} verified on its own page; {self.provider_label} "
            "applies it on every page and each page's own data is checked"
        )

    def traffic_message(self) -> str:
        return f"requests of the closed {self.provider_label} session ({self.worker_name})"

    def detail_event_data(self, detail: Mapping[str, Any]) -> dict[str, Any]:
        """What the event of a product page's outcome (``PRODUCT_DETAIL_READ``) records."""
        keys = (
            "item_id",
            "status",
            "fresh",
            "page_fetch_id",
            "http_status",
            "value",
            "duplicate_of",
            "size_filled",
        )
        return {k: detail.get(k) for k in keys}

    # -- parallel workers ------------------------------------------------------------------------------

    def sibling(self, index: int) -> WalmartCollector:
        """Another worker's collector for this execution: its own provider session and store check, the
        same run, segment, limits and recorded products (see ``collection/base.py``)."""
        other = WalmartCollector(self.pipe, self.run_id, **self._init_kw)
        other.adopt(self, index)
        other.history_before = self.history_before
        other.registry = self.registry
        return other

    def handlers(self) -> dict[str, Any]:
        return {**super().handlers(), "follow_up": self.h_follow_up}

    # -- provider transport -----------------------------------------------------------------------------

    def _transport(self) -> Transport | oxylabs.OxylabsTransport:
        if self.provider == "oxylabs":
            assert self.oxylabs_ledger is not None
            return oxylabs.OxylabsTransport(
                self.oxylabs_ledger,
                run_id=self.run_id,
                retailer=RETAILER,
                actor="collector",
                segment_id=self.segment_id,
                worker=self.owner_name,
            )
        return self._scrapedo_transport()

    def _scrapedo_transport(self) -> Transport:
        assert self.scrapedo_ledger is not None
        return Transport(
            self.scrapedo_ledger,
            run_id=self.run_id,
            retailer=RETAILER,
            actor="collector",
            segment_id=self.segment_id,
            worker=self.owner_name,
        )

    # -- Oxylabs Web API ------------------------------------------------------------------------------

    def _read_oxylabs(self, purpose: str) -> tuple[int | None, dict[str, Any]]:
        """The room the operator's Oxylabs ceiling (and the task's budget) leaves now, recorded with the
        run (Oxylabs has no balance API: the ledger is the record)."""
        with self.factory() as s:
            room, reading = oxylabs.ceiling_room(s)
            event(
                s,
                self.run_id,
                "INFO",
                "PROVIDER_BALANCE",
                f"Oxylabs Web API ceiling {purpose}",
                {
                    "provider": "oxylabs",
                    "key_fingerprint": self.oxylabs_key.fingerprint if self.oxylabs_key else None,
                    "balance_api": "none (Oxylabs documents no balance or usage endpoint)",
                    **reading,
                },
            )
            s.commit()
        return room, reading

    # -- Scrape.do ------------------------------------------------------------------------------------

    async def _read_scrapedo(self, purpose: str) -> tuple[float, dict[str, dict[str, Any]]]:
        """The key's balance (free ``/info``), recorded with the run; a key whose own reading shows less
        than one page's cost is confirmed exhausted. Returns the usable credits."""
        assert self.scrapedo_ledger is not None
        transport = self._scrapedo_transport()
        try:
            balances = await transport.read_balances()
        finally:
            await transport.aclose()
        usable = 0.0
        for k in self.scrapedo_keys:
            b = balances.get(k.role) or {}
            remaining = b.get("RemainingMonthlyRequest")
            if "error" in b or remaining is None:
                continue
            with self.factory() as s:
                row = key_rows(s).get(k.role)
            if row is not None and row.exhausted_at is not None:
                continue
            if float(remaining) < WALMART_PAGE_COST:
                reason = (
                    f"GET /info RemainingMonthlyRequest={remaining}, below one page's {WALMART_PAGE_COST:g}"
                )
                self.scrapedo_ledger.exhaust(k, reason, "collector", self.run_id)  # audit and run event
                continue
            usable += float(remaining)
        with self.factory() as s:
            exhausted = {r.role: iso(r.exhausted_at) for r in key_rows(s).values() if r.exhausted_at}
            event(
                s,
                self.run_id,
                "INFO",
                "PROVIDER_BALANCE",
                f"Scrape.do balance {purpose}",
                {
                    "provider": "scrape.do",
                    "keys": {
                        role: {
                            "fingerprint": b.get("fingerprint"),
                            "remaining": b.get("RemainingMonthlyRequest"),
                            "monthly": b.get("MaxMonthlyRequest"),
                            "read_at": b.get("read_at"),
                            "error": b.get("error"),
                            "exhausted_at": exhausted.get(role),
                        }
                        for role, b in balances.items()
                    },
                    "usable": usable,
                },
            )
            s.commit()
        return usable, balances

    def account_stop(self, code: StopCode, detail: str) -> tuple[StopCode, str]:
        if self.provider != "oxylabs":
            return code, detail
        with self.factory() as s:
            room, reading = oxylabs.ceiling_room(s)
        return (
            StopCode.SPENDING_CEILING,
            f"about {room if room is not None else 0} Oxylabs submissions left under the operator's ceiling "
            f"and the task's money budget (rooms {reading.get('rooms')}); the next request could cross them",
        )

    async def open_account(self) -> tuple[str, str] | None:
        if self.provider == "oxylabs":
            if self.oxylabs_ledger is None:
                return (
                    StopCode.NO_API_KEY,
                    "No Oxylabs Web API key is configured (OXYLABS_WEB_API_KEY or OXYLABS_WEB_API_KEY_FILE).",
                )
            room, reading = self._read_oxylabs("before collecting")
            if room is None:
                return (
                    StopCode.SPENDING_CEILING,
                    "no Oxylabs ceiling is set ('walmart-collector set-ceiling --provider oxylabs'): no "
                    "request is sent without one",
                )
            if room < OXYLABS_MIN_SESSION:
                return (
                    StopCode.SPENDING_CEILING,
                    f"the Oxylabs ceiling leaves {room} submissions (rooms {reading.get('rooms')}), fewer "
                    f"than a session needs ({OXYLABS_MIN_SESSION:g})",
                )
            self.account_start = int(room)
            return None
        if self.scrapedo_ledger is None:
            return (
                StopCode.NO_API_KEY,
                "No Scrape.do API key is configured (SCRAPEDO_API_KEY or SCRAPEDO_API_KEY_FILE).",
            )
        usable, balances = await self._read_scrapedo("before collecting")
        if balances and all("auth" in str(b.get("error") or "").lower() for b in balances.values()):
            return StopCode.PROVIDER_AUTH, "Scrape.do refused the configured key"
        if all("error" in b for b in balances.values()):
            return StopCode.ACCOUNT_UNAVAILABLE, "no Scrape.do balance could be read"
        if usable < WALMART_PAGE_COST:
            return StopCode.CREDITS_EXHAUSTED, "the Scrape.do key has less than one page's credits left"
        self.account_start = int(usable)
        return None

    async def account_remaining_now(self) -> int | None:
        if self.provider == "oxylabs":
            if self.oxylabs_ledger is None:
                return None
            room, _ = self._read_oxylabs("after collecting")
            return room
        if self.scrapedo_ledger is None:
            return None
        try:
            usable, _ = await self._read_scrapedo("after collecting")
        except Exception:  # the segment is closed whatever the account says
            return None
        return int(usable)

    def step_credits(self) -> float:
        return RESULT_COST if self.provider == "oxylabs" else WALMART_PAGE_COST

    def min_session_credits(self) -> float:
        return OXYLABS_MIN_SESSION if self.provider == "oxylabs" else super().min_session_credits()

    def _store_scope(self) -> dict[str, str]:
        """The store parameters every store-scoped request of the run's provider carries."""
        if self.provider == "oxylabs":
            ox = self.cfg.oxylabs
            scope = {"store_id": self.store.location_id, "fulfillment_type": ox.fulfillment_type}
            if ox.delivery_zip:
                scope["delivery_zip"] = ox.delivery_zip
            return scope
        return {"storeid": self.store.location_id, "zipcode": self.store.expected.postal_code[:5]}

    def _store_endpoint(self) -> str:
        return oxylabs.WALMART_ENDPOINT if self.provider == "oxylabs" else WALMART_STORE_ENDPOINT

    async def open_session(self, ctx: TaskContext) -> None:
        """A provider session with robots.txt loaded (the store is checked on Walmart's store page before
        any listing page)."""
        stop = self.limit_stop(opening=True)
        if stop is not None:
            raise RunStop(stop[0], stop[1], resumable=True)
        session: ScrapeDoWalmartSession
        if self.provider == "oxylabs":
            session = OxylabsWalmartSession(
                cast(oxylabs.OxylabsTransport, self._transport()),
                self.storage,
                self.prefix,
                store_id=self.store.location_id,
                zipcode=self.store.expected.postal_code[:5],
                store_page_url=self.store_page_url,
                sanitizer=walmart_sanitize,
                fulfillment_type=self.cfg.oxylabs.fulfillment_type,
                delivery_zip=self.cfg.oxylabs.delivery_zip,
            )
        else:
            session = ScrapeDoWalmartSession(
                cast(Transport, self._transport()),
                self.storage,
                self.prefix,
                store_id=self.store.location_id,
                zipcode=self.store.expected.postal_code[:5],
                store_page_url=self.store_page_url,
                sanitizer=walmart_sanitize,
                # Walmart's own grid filter for the store's fulfillment on every result page (release 1.4.1:
                # the store endpoint alone returned the store's unfiltered grid).
                listing_facet=FULFILLMENT_FACETS.get(self.modality),
            )
        session.keepalive = ctx.heartbeat
        session.limiter = self.crew.limiter
        await session.__aenter__()
        self.session, self.session_opened = session, monotonic()
        self.sessions_opened += 1
        policy = await session.load_robots(f"{self.base}/robots.txt")
        with self.factory() as s:
            run = s.get(Run, self.run_id)
            assert run is not None
            run.robots_sha256 = policy.sha256
            self.persist(s, ctx)
            event(
                s,
                self.run_id,
                "INFO",
                "PROVIDER_SESSION_OPENED",
                f"{self.provider_label} session opened (Walmart store-scoped requests); robots.txt loaded",
                {
                    "session": self.sessions_opened,
                    "session_id": session.session_id,
                    "worker": self.worker_name,
                    "robots_sha256": policy.sha256,
                    "provider": self.provider,
                    "endpoint": self._store_endpoint(),
                    "store_scope": self._store_scope(),
                },
            )
            s.commit()

    async def select_store(self, ctx: TaskContext, node: Node) -> None:
        """The provider applies the store itself (its store parameters): the store's own page must describe
        the configured store, and every listing page is then checked against the store from Walmart's own
        data (its location context and the products' fulfillment lines)."""
        session = self.session
        assert session is not None
        self.check(ctx)
        fetch = await session.navigate(self.store_page_url, "store_page", settle_ms=0)
        self.steps += 1
        details, checks = self._store_page_checks(fetch)
        result = {
            "method": self.store_method(),
            "provider": self.provider,
            "endpoint": self._store_endpoint(),
            **self._store_scope(),
        }
        v = StoreVerification(
            fetch.fetch_id,
            fetch.purpose,
            fetch.final_url or fetch.url,
            checks,
            self._context(details, selected_on=fetch.fetch_id),
        )
        with self.factory() as s:
            self.persist(s, ctx)
            self.attest(s, v, "preflight" if not self._attested(s) else "task_start")
            if not v.passed:
                s.commit()
                raise RunStop(
                    StopCode.STORE_NOT_VERIFIED,
                    "Walmart's store page does not describe the configured store: " + "; ".join(v.failures()),
                    resumable=False,
                )
            event(
                s,
                self.run_id,
                "INFO",
                "STORE_SELECTED",
                self.store_selected_message(),
                {"store_page": fetch.fetch_id, "result": result},
            )
            s.commit()
        assert details is not None
        logo, logo_ref = wpd.header_logo(self.html(fetch), self._origin(fetch))
        self.selection = Selection(
            fetch.fetch_id, fetch.fetch_id, details, fetch.started_at, result, logo, logo_ref
        )

    def _provider_checks(self, fetch: PageFetch, nd: Mapping[str, Any] | None) -> list[StoreCheck]:
        """Walmart's own location context of the page (store and intent), and the store scope the page was
        requested with (recorded; the request parameters alone are not proof)."""
        loc = wpd.page_location(nd) if nd is not None else None
        scope = fetch.notes.get("store_scope") or {}
        headers = fetch.notes.get("provider_headers") or {}
        expected_scope = self._store_scope()
        if self.provider == "oxylabs":
            raw_params = headers.get("params")
            params: Mapping[str, Any] = raw_params if isinstance(raw_params, Mapping) else {}
            applied = str(params.get("store_id") or "")
            provider_check = StoreCheck(
                "provider_params",
                None if not applied else applied == self.store.location_id,
                dict(params) or None,
                {"store_id": self.store.location_id},
                required=False,
                note="the parameters Oxylabs says it applied (its answer's params); recorded, never the "
                "proof",
            )
        else:
            provider_store = str(headers.get("scrape.do-walmart-store-id") or "")
            provider_check = StoreCheck(
                "provider_store_header",
                None if not provider_store else provider_store == self.store.location_id,
                provider_store or None,
                self.store.location_id,
                required=bool(provider_store),
                note="the store the provider says the response reflects (Scrape.do-Walmart-Store-Id); a "
                "provider statement, recorded and never contradicting the page",
            )
        return [
            StoreCheck(
                "page_location_store",
                loc is not None and loc.store_id == self.store.location_id,
                asdict(loc) if loc else None,
                f"pageMetadata.location.storeId {self.store.location_id}",
            ),
            StoreCheck(
                "page_intent",
                loc is not None and loc.intent == self.modality,
                loc.intent if loc else None,
                self.modality,
            ),
            StoreCheck(
                "store_scoped_request",
                scope == expected_scope,
                scope or None,
                expected_scope,
                note="the parameters the provider was asked for; the page's own data above is the proof",
            ),
            provider_check,
        ]

    async def close_session(self) -> None:
        session = self.session
        await super().close_session()
        self.selection = None
        if session is not None:
            with self.factory() as s:
                event(
                    s,
                    self.run_id,
                    "INFO",
                    "PROVIDER_TRAFFIC",
                    self.traffic_message(),
                    {**session.cost_snapshot(), "worker": self.worker_name},
                )
                s.commit()

    def check(self, ctx: TaskContext) -> None:
        super().check(ctx)
        if self.session is not None:
            self.session.keepalive = ctx.heartbeat

    def _store_selected(self) -> bool:
        return self.selection is not None

    def _store_page_checks(self, fetch: PageFetch) -> tuple[wpd.StoreDetails | None, list[StoreCheck]]:
        expected = self.store.expected
        html = self.html(fetch)
        try:
            details = wpd.store_details(wpd.next_data(html), self.store.location_id)
            note = "" if details else f"the page data names no store {self.store.location_id} with an address"
        except wpd.PageDataMissing as exc:
            details, note = None, str(exc)
        house = expected.address_line1.split(" ")[0] if expected.address_line1 else ""
        if details is None and str(self.store.location_id) in urlsplit(fetch.final_url or fetch.url).path:
            # The store's own page (its URL names the store) shows the address as text.
            tree = LexborHTMLParser(html)
            heading = tree.css_first("h1")
            body = tree.body.text(separator="\n") if tree.body is not None else ""
            name = " ".join((heading.text() if heading is not None else "").split())
            details = wpd.store_details_from_text(body, self.store.location_id, house, name)
            note = note if details is None else ""
        if details is None:
            return None, [StoreCheck("store_page_data", False, note, f"store {self.store.location_id}")]
        return details, [
            StoreCheck("store_page_data", True, details.path, f"store {self.store.location_id}"),
            StoreCheck(
                "store_id",
                details.store_id == self.store.location_id,
                details.store_id,
                self.store.location_id,
            ),
            StoreCheck(
                "postal_code",
                details.postal_code[:5] == expected.postal_code[:5],
                details.postal_code,
                expected.postal_code,
            ),
            StoreCheck(
                "address",
                bool(house) and details.address_line1.split(" ")[0] == house,
                details.address_line1,
                expected.address_line1,
                note="house number compared; the street's spelling may differ",
            ),
        ]

    def _context(self, details: wpd.StoreDetails | None, *, selected_on: str) -> dict[str, Any]:
        d = details
        return {
            "stores": [
                {
                    "location_id": d.store_id if d else None,
                    "vanity_name": d.name if d else None,
                    "postal_code": d.postal_code if d else None,
                    "address": d.location_text if d else None,
                }
            ],
            "active_modality": None,
            "modality_source": "walmart store page",
            "selected_on": selected_on,
        }

    def verify(self, fetch: PageFetch) -> StoreVerification:
        """A listing page's store check from its own data (see the module docstring)."""
        loc, kind = self.store.location_id, self.modality
        checks: list[StoreCheck] = []
        items: list[wpd.WalmartItem] = []
        contexts: list[wpd.StoreContext] = []
        nd: dict[str, Any] | None = None
        try:
            nd = wpd.next_data(self.html(fetch))
            items = wpd.page_items(nd, self._origin(fetch))
            contexts = wpd.store_contexts(nd)
            checks.append(StoreCheck("page_data", True, f"{len(items)} products", "__NEXT_DATA__"))
        except (wpd.PageDataMissing, wpd.PageShapeUnclear) as exc:
            checks.append(StoreCheck("page_data", False, str(exc), "__NEXT_DATA__"))
        mine = [i.item_id for i in items if any(f.kind == kind and f.store_id == loc for f in i.fulfillment)]
        others = sorted(
            {
                f.store_id
                for i in items
                for f in i.fulfillment
                if f.kind == kind and f.store_id and f.store_id != loc
            }
        )
        located = (
            nd is not None
            and (pl := wpd.page_location(nd)) is not None
            and pl.store_id == loc
            and pl.intent == kind
        )
        # With the page's own location context naming the store and the fulfillment, a page whose products
        # all lack a line for the store (out of stock, shipping only) is still the store's page: an
        # unavailable product of the store's assortment is not a reason to reject it. A line for another
        # store is.
        fulfil_ok: bool | None = True if mine else (None if located and not others else False)
        checks.append(
            StoreCheck(
                "fulfillment_store",
                fulfil_ok,
                {"products_with_line": len(mine), "products": len(items)},
                f"a {kind} line for store {loc}",
                required=fulfil_ok is not None,
                note=""
                if fulfil_ok is not None
                else "no product here shows a line for the store; the page location context names the store",
            )
        )
        checks.append(StoreCheck("no_other_store", not others, others, f"no {kind} line for another store"))
        sel = self.selection
        order = [f.fetch_id for f in self.session.fetches] if self.session else []
        checked_before = (
            sel is not None
            and sel.confirm_fetch in order
            and fetch.fetch_id in order
            and order.index(fetch.fetch_id) > order.index(sel.confirm_fetch)
        )
        checks.append(
            StoreCheck(
                "store_page_checked", checked_before, sel.confirm_fetch if sel else None, "in this session"
            )
        )
        checks.extend(self._provider_checks(fetch, nd))
        context = self._context(sel.details if sel else None, selected_on=sel.confirm_fetch if sel else "")
        context.update(
            {
                "active_modality": kind if mine else None,
                "modality_source": "walmart fulfillmentSummary",
                "products_for_store": len(mine),
                "other_stores": others,
                "page_contexts": [asdict(c) for c in contexts[:20]],
            }
        )
        return StoreVerification(fetch.fetch_id, fetch.purpose, fetch.final_url or fetch.url, checks, context)

    def attest(self, s: Session, v: StoreVerification, phase: str) -> None:
        ctx = v.context
        details = (ctx.get("stores") or [{}])[0]
        checks = [
            {**c, "check": c["name"], "status": "PASS" if c["ok"] else "FAIL" if c["ok"] is False else "N/A"}
            for c in v.as_dict()["checks"]
        ]
        s.add(
            StoreAttestation(
                run_id=self.run_id,
                mode=self.run_mode,
                phase=phase,
                observed_location_id=(details.get("location_id") or None),
                observed_name=details.get("vanity_name"),
                observed_postal_code=details.get("postal_code"),
                modality=ctx.get("active_modality"),
                modality_source=ctx.get("modality_source"),
                is_trusted=None,
                laf_store_id=None,
                cms_scope="",
                result="PASS" if v.passed else "FAIL",
                checks={"fetch_id": v.fetch_id, "url": v.url, "checks": checks, "context": ctx},
                evidence_artifact_ids=[],
                observed_at=self.clock(),
            )
        )

    # -- handlers ---------------------------------------------------------------------------------

    async def h_preflight(self, ctx: TaskContext) -> dict[str, Any]:
        """robots.txt and the store check on Walmart's store page (each listing page is then checked
        against the store from its own data)."""
        if not self.plan:
            raise RunStop(
                StopCode.NOTHING_TO_COLLECT, "the run has no listing page to visit", resumable=False
            )
        self.check(ctx)

        async def select() -> str | None:
            for node in self.plan:
                if await self.ensure_session(ctx, node):
                    return node.url
            return None

        url = await self._with_reconnects(ctx, select)
        if url is None:
            raise RunStop(
                StopCode.NOTHING_TO_COLLECT, "robots.txt allows none of the planned pages", resumable=False
            )
        with self.factory() as s:
            run = s.get(Run, self.run_id)
            assert run is not None
            run.site_version = "walmart-next"
            event(
                s,
                self.run_id,
                "INFO",
                "STORE_VERIFIED",
                f"{self.store.expected.display_name} verified on Walmart's store page; every listing page is "
                f"checked for {self.modality} at store {self.store.location_id}",
                {"url": self.store_page_url},
            )
            if run.status == "preflight":
                transition(s, self.run_id, "running")
            s.commit()
        return {**ctx.cursor, "verified_on": self.store_page_url}

    async def h_listing(self, ctx: TaskContext) -> dict[str, Any]:
        node = Node.from_dict(ctx.cursor["node"])
        cur = Cursor.from_dict(ctx.cursor)
        if cur.status in (*FINISHED_NODE, "CAPPED"):
            return dict(ctx.cursor)
        self.check(ctx)
        return await self._with_reconnects(
            ctx, lambda: self.collect_node(ctx, node, Cursor.from_dict(ctx.cursor))
        )

    async def collect_node(self, ctx: TaskContext, node: Node, cur: Cursor) -> dict[str, Any]:
        if not await self.ensure_session(ctx, node):
            cur.status, cur.reason = "SKIPPED", "robots.txt does not allow this page"
            return self._finish(node, cur)
        if cur.listings is None:
            direct = direct_listings(node)
            if direct is not None:
                cur.listings = direct
                with self.factory() as s:
                    event(
                        s,
                        self.run_id,
                        "INFO",
                        "SUBCATEGORIES_CONFIGURED",
                        f"{node.category}: {len(direct)} configured subcategory listings read directly "
                        "(their listing ids are under the category's id; the category page is not read)",
                        {"node": node.taxonomy_id, "listings": [x.url for x in direct]},
                    )
                    s.commit()
            elif node.kind == "landing":
                await self.discover(ctx, node, cur)
            else:
                cur.listings = [Listing(node.sub_category, node.url, node.taxonomy_id, via="csv")]
            ctx.checkpoint(cur.as_dict(node))
        assert cur.listings is not None
        if cur.status == "INCOMPLETE" and not cur.listings:
            return self._finish(node, cur)
        while cur.index < len(cur.listings):
            lst = cur.listings[cur.index]
            if lst.status == "PENDING" and not lst.note:
                lst.status = "IN_PROGRESS"
            if lst.status == "IN_PROGRESS":
                await self.collect_listing(ctx, node, cur, lst)
            if cur.status == "CAPPED":
                break
            cur.index, cur.page = cur.index + 1, 1
            ctx.checkpoint(cur.as_dict(node))
        # Product pages of this category's products still without a UPC (left over by an interruption).
        await self.read_details(ctx)
        if cur.status != "CAPPED":
            # Subcategories the client's CSV excludes, or the run did not choose, are not part of it. Each
            # top-level listing counts with its child categories (listing_outcomes).
            outcomes = listing_outcomes(cur.listings)
            statuses = {o["status"] for o in outcomes}
            if cur.listings and not outcomes:
                cur.status = "INCOMPLETE"
                cur.reason = "every subcategory the category page names is excluded or not chosen"
            elif not cur.listings or statuses <= {"EMPTY"}:
                cur.status = "EMPTY"
            elif statuses <= {"DONE", "EMPTY"}:
                cur.status = "DONE"
            elif "CAPPED" in statuses:
                cur.status = "CAPPED"
                cur.reason = cur.reason or "a page or subcategory limit of this run was reached"
            else:
                cur.status = "INCOMPLETE"
                cur.reason = (
                    cur.reason
                    or "; ".join(
                        sorted({f"{o['name'] or o['id']}: {o['reason']}" for o in outcomes if o["reason"]})
                    )[:500]
                )
        return self._finish(node, cur)

    # -- store assortment apart from the current offer -------------------------------------------------

    def history(self, s: Session) -> dict[str, retention.Verified]:
        """Products verified at the store by earlier runs (loaded once per process; see retention.py)."""
        if self.registry is None:
            self.registry = retention.verified_local(
                s,
                self.store_id,
                self.store.location_id,
                self.modality,
                exclude_run=self.run_id,
                before=self.history_before,
                exclude_relative=self.settings.records.exclude_relative_price_items,
            )
        return self.registry

    @staticmethod
    def _unpriced(
        built: BuiltRecord, why: str, flag: RecordFlag, keep: tuple[RecordFlag, ...]
    ) -> BuiltRecord:
        """The record with its local-offer fields empty (each saying why), exported but not valid. An emptied
        field names no source: where the displayed value was read is kept apart, as a value not used."""
        record = dict(built.record)
        missing = dict(built.missing)
        for name in OFFER_FIELDS:
            record[name] = ""
            missing[name] = why
        provenance = {k: v for k, v in built.provenance.items() if k not in OFFER_FIELDS}
        if unused := {k: v for k, v in built.provenance.items() if k in OFFER_FIELDS}:
            provenance["_offer_values_not_used"] = {"why": why, "read_from": unused}
        flags = (*built.flags, *keep)
        return replace(
            built,
            record=record,
            status=RecordStatus.EXPORTED_NOT_VALID,
            reasons=(),
            flags=tuple(dict.fromkeys((*flags, flag))),
            missing=missing,
            provenance=provenance,
        )

    def assortment(
        self,
        s: Session,
        key: str,
        built: BuiltRecord,
        offer: wrec.LocalOffer,
        observed: datetime,
        same_run: retention.Verified | None = None,
    ) -> tuple[BuiltRecord, dict[str, Any]]:
        """Store assortment (A), availability and the local price (B) decided apart.

        * A line of the configured fulfillment for the store: the store's product with the store's price
          (out of stock or not).
        * Another local line for the store (Delivery from the store) only: the store's product, but its
          displayed price is not the configured fulfillment's: exported without prices (``NO_PICKUP_OFFER``).
        * No line for the store (out of stock without fulfillment, shipping only, a marketplace seller): the
          store's product only when an earlier run verified it there, or an earlier tile of this run
          (``same_run``, release 1.3.1), then exported with its identity and size and empty prices
          (``NO_LOCAL_OFFER``); otherwise its assortment is unresolved: recorded with the reason, not
          exported. A shipping, marketplace or unverified price is never used."""
        modality = self.modality
        store = self.store.location_id
        if offer.accepted and offer.pickup_price:
            return built, {
                "status": "verified",
                "basis": "pickup_line",
                "price": "the store's price for the configured fulfillment",
                "evidence": offer.note,
            }
        if offer.accepted:
            if built.status is RecordStatus.EXCLUDED:
                return built, {
                    "status": "verified",
                    "basis": "store_line_other_fulfillment",
                    "evidence": offer.note,
                }
            if offer.for_store and not offer.seller_verified:
                return self._unpriced(built, offer.note, RecordFlag.SELLER_UNVERIFIED, ()), {
                    "status": "verified",
                    "basis": "store_line_seller_not_named",
                    "price": "none: the page names no seller",
                    "evidence": offer.note,
                }
            why = (
                f"no {modality} line for store {store} on this page ({offer.note}): the displayed price is "
                f"not taken as the {modality} price"
            )
            return self._unpriced(built, why, RecordFlag.NO_PICKUP_OFFER, ()), {
                "status": "verified",
                "basis": "store_line_other_fulfillment",
                "price": "none: no line of the configured fulfillment",
                "evidence": offer.note,
            }
        reasons = set(built.reasons)
        if not reasons or not reasons <= NOT_LOCAL_REASONS:
            other = sorted(r.value for r in reasons - NOT_LOCAL_REASONS)
            return built, {
                "status": "not_decided",
                "store_line": offer.store_line,
                "evidence": offer.note,
                "note": "excluded for another reason: " + ", ".join(other) if other else "",
            }
        earlier = same_run or self.history(s).get(key)  # this run's own tile is the later one
        if earlier is None:
            return replace(built, reasons=(*built.reasons, RecordFlag.ASSORTMENT_UNRESOLVED)), {
                "status": "unresolved",
                "evidence": offer.note,
                "note": f"no line for store {store} on this page and no earlier verified observation at "
                "the store: the product is not claimed as the store's (kept here with the reason)",
            }
        why = (
            f"no local offer at store {store} on this page ({offer.note}); a shipping, marketplace or "
            "unverified value is never used"
        )
        keep = tuple(r for r in built.reasons if r is not RecordFlag.LOCATION_UNATTESTED)
        return self._unpriced(built, why, RecordFlag.NO_LOCAL_OFFER, keep), {
            "status": "verified_earlier",
            "basis": "local_offer_observed_earlier",
            "evidence": offer.note,
            "verified": earlier.summary(observed),
        }

    # -- product detail pages (UPC and size) -----------------------------------------------------------------

    def _detail_pending(self, s: Session) -> list[RecordRow]:
        """Exported products of this run whose result page stated no UPC or no size and whose own page was
        not read."""
        return list(
            s.scalars(
                select(RecordRow)
                .where(
                    RecordRow.run_id == self.run_id,
                    RecordRow.status.in_((RecordStatus.VALID.value, RecordStatus.EXPORTED_NOT_VALID.value)),
                    or_(RecordRow.record["upc"].astext == "", RecordRow.record["weight"].astext == ""),
                    ~func.coalesce(RecordRow.provenance.has_key("upc_detail"), False),
                )
                .order_by(RecordRow.id)
            )
        )

    def _details_read(self, s: Session) -> int:
        """Detail pages this run requested (across processes: from the records)."""
        return int(
            s.scalar(
                select(func.count())
                .select_from(RecordRow)
                .where(
                    RecordRow.run_id == self.run_id,
                    RecordRow.provenance["upc_detail"]["fresh"].astext == "true",
                )
            )
            or 0
        )

    def _detail_lineage(self) -> str:
        """The lineage of the store's detail queue this run works on; "" for a replay, which requests nothing
        and neither notes nor reads the queue."""
        lin = str(self.segment_lineage.get("transport") or "")
        return lin if lin in (lineage.NETWORK, lineage.SUBSTITUTED) else ""

    def saved_details(self, s: Session) -> dict[str, dict[str, Any]]:
        """What earlier reads of each item's own page established, within ``reuse_days``: the newest read of
        each item, with its time, run, source revision and page hash (``detail_observations``). A read
        recorded before release 1.5.0 has no saved statements about size, so it answers for the UPC only."""
        if self._upc_cache is None:
            self._upc_cache = {}
            days = self.cfg.detail.reuse_days
            if days > 0:
                since = self.clock() - timedelta(days=days)
                q = (
                    select(RecordRow.upc, RecordRow.run_id, RecordRow.provenance)
                    .join(Run, Run.id == RecordRow.run_id)
                    .where(
                        Run.store_id == self.store_id,
                        Run.id != self.run_id,
                        Run.mode == DataMode.LIVE.value,
                        RecordRow.provenance.has_key("upc_detail"),
                    )
                )
                for row in s.execute(q).all():
                    key, run_id, prov = cast(tuple[str, str, dict[str, Any] | None], tuple(row))
                    d = (prov or {}).get("upc_detail") or {}
                    at = str(d.get("requested_at") or "")
                    if d.get("status") != "extracted" or not d.get("fresh") or not d.get("value") or not at:
                        continue
                    when = datetime.fromisoformat(at.replace("Z", "+00:00"))
                    if when < since or (self.history_before is not None and when >= self.history_before):
                        continue
                    item = str(d.get("item_id") or key.removeprefix(wrec.KEY_PREFIX))
                    self._upc_cache[item] = {
                        "status": "extracted",
                        "value": d["value"],
                        "run_id": run_id,
                        "page_fetch_id": d.get("page_fetch_id"),
                        "requested_at": at,
                        "path": d.get("path"),
                        "body_sha256": d.get("body_sha256"),
                        "source_revision": d.get("source_revision"),
                        "origin": "fetched",
                        "size_statements": None,
                    }
                saved = select(DetailObservation).where(
                    DetailObservation.store_id == self.store_id,
                    DetailObservation.run_id != self.run_id,
                    DetailObservation.observed_at >= since,
                )
                if self.history_before is not None:
                    saved = saved.where(DetailObservation.observed_at < self.history_before)
                for obs in s.scalars(saved.order_by(DetailObservation.observed_at, DetailObservation.id)):
                    prior = self._upc_cache.get(obs.item_id)
                    if obs.status != "extracted" and prior is not None and prior["status"] == "extracted":
                        continue  # a later page that states no UPC does not erase what an earlier one stated
                    self._upc_cache[obs.item_id] = {
                        "status": obs.status,
                        "value": obs.upc or "",
                        "run_id": obs.run_id,
                        "page_fetch_id": obs.page_fetch_id,
                        "requested_at": iso(obs.observed_at),
                        "path": obs.upc_path,
                        "body_sha256": obs.body_sha256,
                        "source_revision": obs.source_revision,
                        "origin": obs.origin,
                        "size_statements": obs.size_statements,
                    }
        return self._upc_cache

    def _detail_item(self, row: RecordRow) -> str:
        return (
            row.upc[len(wrec.KEY_PREFIX) :]
            if row.upc.startswith(wrec.KEY_PREFIX)
            else wpd.item_id_from_url(str(row.record.get("url") or ""))
        )

    def _detail_order(self, s: Session, pending: list[RecordRow]) -> list[RecordRow]:
        """The products to read, in the store's queue order: never attempted first, the longest waiting first,
        then those whose page failed before (``follow_queue.ordered``). The same products at the front of the
        listings therefore cannot use a page budget up run after run."""
        lin = self._detail_lineage()
        if not lin or not pending:
            return pending
        rows_by_item = {self._detail_item(r): r for r in pending if self._detail_item(r)}
        candidates = [
            {"kind": "detail", "item_id": item, "url": r.record.get("url")}
            for item, r in rows_by_item.items()
        ]
        queued = follow_queue.note_seen(
            s,
            store_id=self.store_id,
            run_id=self.run_id,
            lineage=lin,
            candidates=candidates,
            now=self.clock(),
        )
        ordered = [rows_by_item[str(c["item_id"])] for c in follow_queue.ordered(candidates, queued)]
        return ordered + [r for r in pending if not self._detail_item(r)]

    async def read_details(self, ctx: TaskContext, *, listings_done: bool = False) -> None:
        """Read the own page of each exported product whose result page stated no UPC or no size, once in the
        run. The UPC or GTIN that page states for the same item is kept exactly as written (never the item id,
        never another variant's), and its statements about size are read apart by what they measure
        (:mod:`walmart_headless.sites.walmart.pack_size`). Every product gets an outcome in
        ``provenance.upc_detail``: ``extracted``, ``absent_in_source`` (the item's page states none),
        ``blocked`` (a refusal or challenge), ``request_failed``, ``parse_failed`` (no page data),
        ``identity_mismatch`` (the page is another item's), or later ``not_attempted`` with the reason. No
        price is taken from these pages.

        Production reads them as the listings go. A pilot's page budget waits until the listings have named
        every product of the run (:meth:`_budgeted_details`): read as they go, a budget would always go to the
        first listing's products, whatever the queue's order."""
        cfg = self.cfg.detail
        if not cfg.enabled or self.detail_paused is not None or self.session is None:
            return
        if cfg.max_per_run is not None and not listings_done:
            return
        with self.factory() as s:
            pending = self._detail_order(s, self._detail_pending(s))
            saved = self.saved_details(s)
            run = s.get(Run, self.run_id)
            paused = ((run.counts or {}) if run is not None else {}).get("upc_detail_paused")
            s.commit()
        if paused:
            self.detail_paused = str(paused)
            return
        claims = self.crew.claims
        # What an earlier read established costs no request, so a page budget never stops it (release 1.5.1).
        # Before, the products behind the budget's last page stayed blank with their saved page unused.
        pending.sort(key=lambda r: self._reusable(r, saved) is None)
        for row in pending:
            if row.id in claims:
                continue  # another worker of this execution reads it
            claims.add(row.id)
            self.crew.detail_in_flight += 1
            try:
                if not await self._read_detail(ctx, row, cfg, saved):
                    return
            except BaseException:
                claims.discard(row.id)  # not read: free for a later pass
                raise
            finally:
                self.crew.detail_in_flight -= 1

    async def _budgeted_details(self, ctx: TaskContext) -> None:
        """A pilot's detail page budget, in the store's queue order (see :meth:`read_details`)."""
        with self.factory() as s:
            if not self._detail_pending(s):
                return
        self.check(ctx)
        if await self.ensure_session(ctx, self.plan[0]):
            await self.read_details(ctx, listings_done=True)

    def _reusable(self, row: RecordRow, saved: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
        """The earlier read that answers for this product, if any. A read with no saved statements about size
        answers only for a product whose title already states one."""
        hit = saved.get(self._detail_item(row))
        if hit is not None and (row.record.get("weight") or hit.get("size_statements") is not None):
            return hit
        return None

    def _reused_detail(self, item_id: str, hit: Mapping[str, Any], title_size: str) -> dict[str, Any]:
        """A product's outcome from an earlier read of its own page: that read's time, run, revision and page
        stay on it, and nothing says it was fetched now."""
        detail: dict[str, Any] = {
            "status": hit["status"],
            "fresh": False,
            "item_id": item_id,
            "reused_from": {k: v for k, v in hit.items() if k != "size_statements"},
        }
        if hit["status"] == "extracted":
            detail["value"] = hit["value"]
        else:
            detail["reason"] = "an earlier read of the item's own page states no UPC or GTIN"
        statements = hit.get("size_statements")
        if statements is not None:
            detail["size"] = wps.decide(
                tuple(
                    wps.SizeObservation(o["kind"], o["measures"], o["value"], o["path"]) for o in statements
                ),
                title_size,
            ).as_dict()
        return detail

    async def _read_detail(
        self, ctx: TaskContext, row: RecordRow, cfg: Any, saved: dict[str, dict[str, Any]]
    ) -> bool:
        """One product's own page (see :meth:`read_details`). False: stop reading details."""
        assert self.session is not None
        url = str(row.record.get("url") or "")
        item_id = self._detail_item(row)
        if not item_id or not url:
            self._set_detail(
                ctx, row.id, {"status": "not_attempted", "fresh": False, "reason": "no item id or URL"}
            )
            return True
        title_size = str(row.record.get("weight") or "")
        hit = self._reusable(row, saved)
        if hit is not None:
            self._set_detail(ctx, row.id, self._reused_detail(item_id, hit, title_size))
            return True
        if cfg.max_per_run is not None:
            with self.factory() as s:
                done = self._details_read(s)  # across workers and processes
            # Another worker's page still on its way counts: two workers never read past the budget.
            if done + self.crew.detail_in_flight - 1 >= cfg.max_per_run:
                return False  # the rest are "not_attempted" (the detail limit), set at assembly
        self.check(ctx)
        detail: dict[str, Any] = {"item_id": item_id, "url": url, "endpoint": cfg.endpoint, "fresh": True}
        fetch: PageFetch | None = None
        try:
            fetch = await self.session.navigate(
                url,
                "product_detail" if cfg.endpoint == "general" else "product_page",
                expect_initial_state=False,
            )
        except NotInSource as exc:
            # A replay: the run it reads again never requested this product's page.
            self._set_detail(
                ctx,
                row.id,
                {"status": "not_attempted", "fresh": False, "item_id": item_id, "reason": str(exc)[:300]},
            )
            return True
        except ChallengeDetected as exc:
            fetch = exc.fetch
            detail.update(status="blocked", reason="; ".join(exc.fetch.challenge.reasons))
        except ProviderError as exc:
            if exc.kind in (
                ProviderErrorKind.BUDGET,
                ProviderErrorKind.CEILING,
                ProviderErrorKind.QUOTA,
                ProviderErrorKind.AUTH,
                ProviderErrorKind.CONFIG,
            ):
                raise
            detail.update(status="request_failed", reason=str(exc)[:300])
        self.steps += 1
        if fetch is not None:
            detail.update(
                page_fetch_id=fetch.fetch_id,
                requested_at=fetch.started_at,
                http_status=fetch.status,
                body_sha256=fetch.notes.get("raw_sha256"),
                raw_key=fetch.notes.get("raw_key"),
                credits=fetch.notes.get("credits"),
                request_id=fetch.notes.get("request_id"),
                observed_by_run=self.run_id,
            )
        if "status" not in detail and fetch is not None:
            if fetch.status != 200:
                detail.update(status="request_failed", reason=f"HTTP {fetch.status}")
            else:
                html = self.html(fetch)
                ident = wpd.product_identifier(html, item_id)
                detail.update(
                    page_item=ident.page_item,
                    matched=ident.matched,
                    candidates=[list(c) for c in ident.candidates[:10]],
                )
                if not ident.page_data:
                    detail.update(status="parse_failed", reason="the page carries no Walmart page data")
                elif ident.page_item and ident.page_item != item_id:
                    detail.update(
                        status="identity_mismatch",
                        reason=f"the page is for item {ident.page_item}, not {item_id}",
                    )
                elif (
                    not ident.matched
                    and not ident.page_item
                    and (missing := wpd.not_found_page(wpd.next_data(html)))
                ):
                    # Release 1.6.3: the site's own not-found page, no usable answer (until then its page data
                    # was not found: "parse_failed", "the page carries no Walmart page data").
                    detail.update(
                        status="request_failed",
                        reason=f"the site answered with its not-found page (page data route {missing}, "
                        f"HTTP {fetch.status})",
                    )
                elif not ident.matched and not ident.page_item:
                    detail.update(
                        status="identity_mismatch",
                        reason="the page's data names no item: its identifiers cannot be tied to it",
                    )
                else:
                    if ident.value:
                        detail.update(
                            status="extracted", value=ident.value, source=ident.source, path=ident.path
                        )
                    else:
                        detail.update(
                            status="absent_in_source", reason="the item's own page data states no UPC or GTIN"
                        )
                    detail["size"] = wps.pack_size(wpd.next_data(html), title_size).as_dict()
                    detail["body_sha256"] = (
                        detail.get("body_sha256") or hashlib.sha256(html.encode("utf-8")).hexdigest()
                    )
        failed = detail.get("status") in ("blocked", "request_failed")
        self.detail_failures = self.detail_failures + 1 if failed else 0
        self._set_detail(ctx, row.id, detail)
        if self.detail_failures >= cfg.pause_after_failures:
            self.detail_paused = (
                f"{self.detail_failures} consecutive detail requests refused or failed "
                f"(last: {detail.get('reason')})"
            )
            with self.factory() as s:
                run = s.get(Run, self.run_id)
                assert run is not None
                run.counts = {**(run.counts or {}), "upc_detail_paused": self.detail_paused}
                event(
                    s,
                    self.run_id,
                    "WARN",
                    "PRODUCT_DETAIL_PAUSED",
                    self.detail_paused,
                    {"item_id": item_id},
                )
                s.commit()
            return False
        return True

    def _save_detail_observation(self, s: Session, rec: RecordRow, detail: dict[str, Any]) -> None:
        """Keep what a fresh read of an item's own page established for later runs of the store."""
        size = detail.get("size") or {}
        at = str(detail.get("requested_at") or "")
        if not at or not detail.get("body_sha256"):
            return
        run = s.get(Run, self.run_id)
        code = ((run.config_snapshot or {}).get("code") or {}) if run is not None else {}
        revision = f"{code.get('version') or ''} {code.get('commit') or ''}".strip() or None
        detail["source_revision"] = revision
        seen = s.scalar(
            select(DetailObservation.id).where(
                DetailObservation.store_id == self.store_id,
                DetailObservation.item_id == str(detail["item_id"]),
                DetailObservation.body_sha256 == str(detail["body_sha256"]),
            )
        )
        if seen is None:
            s.add(
                DetailObservation(
                    store_id=self.store_id,
                    item_id=str(detail["item_id"]),
                    observed_at=datetime.fromisoformat(at.replace("Z", "+00:00")),
                    run_id=self.run_id,
                    page_fetch_id=detail.get("page_fetch_id"),
                    source_revision=revision,
                    origin="fetched",
                    url=detail.get("url"),
                    body_sha256=str(detail["body_sha256"]),
                    status=str(detail["status"]),
                    upc=str(detail.get("value") or "") or None,
                    upc_path=detail.get("path"),
                    size_statements=list(size.get("observations") or []),
                )
            )

    def _set_detail(self, ctx: TaskContext, row_id: str, detail: dict[str, Any]) -> None:
        """Record a product's detail outcome; a UPC or size the result page did not state goes into the record
        (a second product of the run with the same UPC is the same product: it is excluded as
        ``DUPLICATE_UPC``). A value the result page did state is never replaced: a page that disagrees with it
        is recorded and flagged."""
        with self.factory() as s:
            self.persist(s, ctx)
            rec = s.get(RecordRow, row_id)
            assert rec is not None
            record = dict(rec.record)
            status = str(detail.get("status"))
            value = str(detail.get("value") or "") if status == "extracted" else ""
            read_at = detail.get("requested_at") or (detail.get("reused_from") or {}).get("requested_at")
            if record.get("upc"):
                detail["listing_upc"] = True
                if value and value != record["upc"]:
                    detail["upc_conflict"] = f"the listing states {record['upc']}, its own page {value}"
            elif value:
                dup = s.scalar(
                    select(RecordRow.upc)
                    .where(
                        RecordRow.run_id == self.run_id,
                        RecordRow.upc != rec.upc,
                        RecordRow.record["upc"].astext == value,
                        RecordRow.status.in_(
                            (RecordStatus.VALID.value, RecordStatus.EXPORTED_NOT_VALID.value)
                        ),
                    )
                    .limit(1)
                )
                record["upc"] = value
                if dup is not None:
                    detail["duplicate_of"] = dup
                    rec.status = RecordStatus.EXCLUDED.value
                    rec.reasons = [*(rec.reasons or []), RecordFlag.DUPLICATE_UPC.value]
                # The UPC's own time: when its page was read (or, reused, when the earlier run read it).
                detail["upc_observed_at"] = read_at
            size = detail.get("size") or {}
            shown = str(size.get("value") or "")
            approx = next(
                (
                    {"text": text, "path": o["path"]}
                    for o in size.get("observations") or []
                    if o["measures"] == wps.PACK and (text := wrec.approx_weight_text(o["value"]))
                ),
                None,
            )
            if approx:
                # The source's own size wording is approximate: the whole product is out, as from a title.
                rec.status = RecordStatus.EXCLUDED.value
                rec.reasons = [*(rec.reasons or []), RecordFlag.APPROX_WEIGHT.value]
                detail["approx_weight"] = approx
            elif shown and not record.get("weight"):
                record["weight"] = shown
                detail["size_filled"] = True
                detail["weight_observed_at"] = read_at
            if record != rec.record:
                rec.record = record
                rec.record_sha256 = record_sha256(ordered_record(record))
            if size.get("conflicts") or detail.get("upc_conflict"):
                flag = (
                    RecordFlag.SIZE_CONFLICT.value
                    if size.get("conflicts")
                    else RecordFlag.UPC_SOURCE_MISMATCH.value
                )
                if flag not in (rec.flags or []):
                    rec.flags = [*(rec.flags or []), flag]
            if detail.get("fresh") and status in DETAIL_STATUSES and self._detail_lineage():
                self._save_detail_observation(s, rec, detail)
            rec.provenance = {**(rec.provenance or {}), "upc_detail": detail}
            lin = self._detail_lineage()
            if lin and detail.get("item_id"):
                follow_queue.record_outcome(
                    s,
                    store_id=self.store_id,
                    lineage=lin,
                    out={
                        "kind": "detail",
                        "item_id": detail["item_id"],
                        "status": (
                            "included"
                            if status in DETAIL_STATUSES
                            else "not_attempted"
                            if status == "not_attempted"
                            else "inaccessible"
                        ),
                        "reason": detail.get("reason") or status,
                        "page_fetch_id": detail.get("page_fetch_id"),
                    },
                    run_id=self.run_id,
                    now=self.clock(),
                )
            queue.heartbeat(s, ctx.lease, lease_s=ctx.lease_s)  # fence: only the task's owner writes
            event(
                s,
                self.run_id,
                "INFO" if status in DETAIL_STATUSES else "WARN",
                "PRODUCT_DETAIL_READ",
                f"{detail.get('item_id')}: {status}"
                + (f" {value}" if value else "")
                + (f" size {shown}" if shown else "")
                + (f" ({detail['reason']})" if detail.get("reason") else ""),
                self.detail_event_data(detail),
            )
            s.commit()

    def reuse_saved_details(self, ctx: TaskContext) -> int:
        """When the run is assembled, before :meth:`close_details`: each exported product whose own page this
        run did not read, and for which an earlier read answers (:meth:`saved_details`, the reuse window),
        gets that read's outcome exactly as the detail pass would have given it (:meth:`_reused_detail`: the
        read's own time, run, revision and page; nothing says it was fetched now). Release 1.6.1: until then
        only the detail pass reused, so a run that ended before it (a stop, a deadline, a credit limit) left
        these products blank as "the run stopped before this product's page was read", saving no request: the
        live S7 of 2026-10-31 (release 1.5.1) left 32 products blank that S6's saved reads answered for.
        Release 1.6.3: also with product detail reading off (``detail.enabled: false``,
        ``--pilot-no-detail``), which turns off requests, not what earlier reads established: until then
        such a run exported these products blank, "product detail reading is off", although a saved read
        answered for them at no request (the live runs of 2026-11-03/04 left UPCs blank that 1.5.1's S6 had
        read).
        ``detail.reuse_days: 0`` turns reuse off. Returns the products answered."""
        with self.factory() as s:
            saved = self.saved_details(s)
            todo = [
                (row.id, item, str(row.record.get("weight") or ""), hit)
                for row in self._detail_pending(s)
                if (item := self._detail_item(row)) and (hit := self._reusable(row, saved)) is not None
            ]
            s.commit()
        for row_id, item, title_size, hit in todo:
            self._set_detail(ctx, row_id, self._reused_detail(item, hit, title_size))
        return len(todo)

    def recover_carried_details(self, s: Session) -> dict[str, Any]:
        """When the run is assembled, after ``retention.carry_forward``: a carried row whose UPC or size is
        empty gets what a saved read of the item's own page establishes (:meth:`saved_details`, the reuse
        window), as a product of this run does (:meth:`reuse_saved_details`). The value names that read (its
        time, run, revision and page) in ``provenance.upc_detail.reused_from`` and
        ``provenance.historical.recovered_fields``; the listing observation stays the earlier run's (its crawl
        date, prices and page), and ``historical.record_as_carried_sha256`` is the record as carried. Release
        1.6.3: until then a carried row kept the empty fields of the run it came from, although a saved read
        answered for them at no request (the live runs of 2026-11-03/04 carried rows with blank UPCs that
        1.5.1's S6 had read).

        Never forced: the row stays as it was, with the reason in ``historical.recovery_withheld``, when the
        read states a UPC another exported row of the run has (one product: a row of this run would be
        excluded as ``DUPLICATE_UPC``), an approximate size, sizes that conflict, or another UPC than the row
        has, or when the record would fail the record checks. A read the row's earlier outcome already names
        adds nothing."""
        out: dict[str, Any] = {
            "rows_with_empty_fields": 0,
            "answered_by_saved_read": 0,
            "upc_filled": 0,
            "weight_filled": 0,
            "already_from_that_read": 0,
            "withheld": 0,
        }
        rows = list(
            s.scalars(
                select(RecordRow)
                .where(
                    RecordRow.run_id == self.run_id,
                    RecordRow.status == retention.CARRIED_STATUS,
                    or_(RecordRow.record["upc"].astext == "", RecordRow.record["weight"].astext == ""),
                )
                .order_by(RecordRow.upc)
            )
        )
        if not rows:
            return out
        saved = self.saved_details(s)
        exported = (RecordStatus.VALID.value, RecordStatus.EXPORTED_NOT_VALID.value, retention.CARRIED_STATUS)
        taken = {
            str(u)
            for u in s.scalars(
                select(RecordRow.record["upc"].astext).where(
                    RecordRow.run_id == self.run_id, RecordRow.status.in_(exported)
                )
            )
            if u
        }
        for row in rows:
            out["rows_with_empty_fields"] += 1
            item = self._detail_item(row)
            hit = self._reusable(row, saved) if item else None
            if hit is None:
                continue
            hist = dict((row.provenance or {}).get("historical") or {})
            earlier = s.scalar(
                select(RecordRow).where(
                    RecordRow.run_id == str(hist.get("run_id") or ""), RecordRow.upc == row.upc
                )
            )
            before: Mapping[str, Any] = (
                ((earlier.provenance or {}).get("upc_detail") or {}) if earlier is not None else {}
            )
            if _same_read(before, hit):
                out["already_from_that_read"] += 1
                continue
            record = dict(row.record)
            detail = self._reused_detail(item, hit, str(record.get("weight") or ""))
            value = str(detail.get("value") or "") if detail["status"] == "extracted" else ""
            size = detail.get("size") or {}
            from_listing = bool(
                before.get("listing_upc") or before.get("source") == dispositions.LISTING_SOURCE
            )
            why = ""
            if record.get("upc"):
                if value and value != record["upc"]:
                    why = f"the read states UPC {value}, the carried row {record['upc']}"
                elif not value and not from_listing:
                    why = "the read states no UPC, the carried row's UPC comes from another read"
                elif from_listing:
                    detail["listing_upc"] = True
            elif value and value in taken:
                why = f"the read states UPC {value}, which another exported row of the run has (one product)"
            if not why and any(
                o["measures"] == wps.PACK and wrec.approx_weight_text(o["value"])
                for o in size.get("observations") or []
            ):
                why = (
                    "the read states an approximate size (a row of this run would be excluded: APPROX_WEIGHT)"
                )
            if not why and (size.get("conflicts") or size.get("outcome") == "conflict"):
                why = "the read's statements about size conflict"
            read = {
                k: hit.get(k)
                for k in (
                    "run_id",
                    "page_fetch_id",
                    "requested_at",
                    "source_revision",
                    "body_sha256",
                    "origin",
                )
            }
            filled: dict[str, Any] = {}
            if not why and value and not record.get("upc"):
                record["upc"] = value
                detail["upc_observed_at"] = hit["requested_at"]
                filled["upc"] = {"value": value, "path": hit.get("path"), **read}
            shown = str(size.get("value") or "")
            if not why and shown and not record.get("weight"):
                record["weight"] = shown
                detail["size_filled"] = True
                detail["weight_observed_at"] = hit["requested_at"]
                filled["weight"] = {
                    "value": shown,
                    "path": size.get("path"),
                    "rule": size.get("rule"),
                    **read,
                }
            problems = retention.record_problems(record) if filled else []
            if problems:
                why = "the record with the read's values would fail the record checks: " + "; ".join(problems)
                filled = {}
            if why:
                hist["recovery_withheld"] = {"reason": why[:300], "read": read}
                row.provenance = {**(row.provenance or {}), "historical": hist}
                out["withheld"] += 1
                continue
            detail["for_carried_row"] = {"run_id": self.run_id, "earlier_run": hist.get("run_id")}
            if filled:
                taken.add(str(record.get("upc") or ""))
                hist["recovered_fields"] = filled
                hist["record_as_carried_sha256"] = row.record_sha256
                hist["note"] = (
                    "an earlier run's verified local observation, carried forward: its prices are the ones "
                    "observed on its crawl date, not verified by this run; its empty "
                    + " and ".join(sorted(filled))
                    + " filled from a saved read of the item's own page (recovered_fields: that read's run, "
                    "time, revision and page)"
                )
                row.record = record
                row.record_sha256 = record_sha256(ordered_record(record))
            row.provenance = {**(row.provenance or {}), "historical": hist, "upc_detail": detail}
            out["answered_by_saved_read"] += 1
            out["upc_filled"] += int("upc" in filled)
            out["weight_filled"] += int("weight" in filled)
        return out

    def close_details(self, s: Session) -> dict[str, int]:
        """When the run is assembled: every exported product gets a UPC outcome. A UPC the result page stated
        is ``extracted`` from the listing; a product whose page was not read says why, and stays waiting in
        the store's queue."""
        cfg = self.cfg.detail
        run = s.get(Run, self.run_id)
        assert run is not None
        paused = (run.counts or {}).get("upc_detail_paused")
        done = self._details_read(s)
        lin = self._detail_lineage()
        self._detail_order(s, self._detail_pending(s))  # what is left stays in the store's queue
        if not cfg.enabled:
            unread = "product detail reading is off"
        elif paused:
            unread = f"detail reading paused: {paused}"
        elif cfg.max_per_run is not None and done >= cfg.max_per_run:
            unread = f"the run's detail limit ({cfg.max_per_run} pages) was reached"
        else:
            unread = "the run stopped before this product's page was read"
        for rec in s.scalars(
            select(RecordRow).where(
                RecordRow.run_id == self.run_id,
                RecordRow.status.in_((RecordStatus.VALID.value, RecordStatus.EXPORTED_NOT_VALID.value)),
                ~func.coalesce(RecordRow.provenance.has_key("upc_detail"), False),
            )
        ):
            if rec.record.get("upc"):
                detail: dict[str, Any] = {
                    "status": "extracted",
                    "fresh": False,
                    "source": dispositions.LISTING_SOURCE,
                    "value": rec.record["upc"],
                }
                if not rec.record.get("weight"):
                    detail["size_unread_reason"] = unread
            else:
                detail = {"status": "not_attempted", "fresh": False, "reason": unread}
                item = self._detail_item(rec)
                if lin and item:
                    follow_queue.record_outcome(
                        s,
                        store_id=self.store_id,
                        lineage=lin,
                        out={"kind": "detail", "item_id": item, "status": "not_attempted", "reason": unread},
                        run_id=self.run_id,
                        now=self.clock(),
                    )
            rec.provenance = {**(rec.provenance or {}), "upc_detail": detail}
        out: dict[str, int] = {}
        prov: dict[str, Any] | None
        for prov in s.scalars(
            select(RecordRow.provenance).where(
                RecordRow.run_id == self.run_id,
                RecordRow.status.in_((RecordStatus.VALID.value, RecordStatus.EXPORTED_NOT_VALID.value)),
            )
        ):
            d: dict[str, Any] = (prov or {}).get("upc_detail") or {}
            k = str(d.get("status"))
            if k == "extracted" and d.get("reused_from"):
                k = "extracted_reused"
            elif k == "extracted" and (d.get("listing_upc") or not d.get("fresh")):
                k = "extracted_from_listing"
            out[k] = out.get(k, 0) + 1
        return out

    async def discover(self, ctx: TaskContext, node: Node, cur: Cursor) -> None:
        """Read a category page for the subcategory listings its data names."""
        assert self.session is not None
        self.check(ctx)
        try:
            fetch = await self.session.navigate(node.url, "category_page", settle_ms=self.LISTING_SETTLE_MS)
        except NotInSource as exc:
            cur.listings, cur.status, cur.reason = [], "INCOMPLETE", str(exc)[:500]
            return
        self.steps += 1
        groups: dict[str, str] = {}  # listing URL -> its navigation group
        try:
            nd = wpd.next_data(self.html(fetch))
            nav = wpd.category_nav(nd, self._origin(fetch))
            if nav:
                # The category page's own navigation (live layout, 2026-10-21): each group's links.
                links = []
                for g in nav:
                    for link in g.links:
                        links.append(link)
                        groups.setdefault(link.url, g.name)
            else:
                links = wpd.subcategory_links(nd, self._origin(fetch))
            problem = None if links else f"{node.url}: the category page names no subcategory listing"
        except wpd.PageDataMissing as exc:
            links, problem = [], f"{node.url}: {exc}"
        with self.factory() as s:
            self.persist(s, ctx)
            self._contract(s, problem)
            s.commit()
        if problem is not None:
            # Never an empty category: the category is incomplete (the run's checks fail on it) and the
            # page is kept for review; the other categories are still collected.
            cur.listings, cur.status, cur.reason = [], "INCOMPLETE", problem[:500]
            return
        excluded = {_name_key(e) for e in node.excluded}
        only = {o.rstrip("/") for o in node.only}
        limit = self.cfg.limits.max_subcategories_per_category
        listings: list[Listing] = []
        chosen = 0
        seen_paths: set[str] = set()
        for link in links:
            path = urlsplit(link.url).path.rstrip("/")
            if path in seen_paths:
                continue  # a listing the navigation names twice is read once
            seen_paths.add(path)
            group = groups.get(link.url, "")
            # A link named only "Shop all" stands for its navigation group: the group's name is the
            # subcategory ("Tailgating Food" › "Shop all" gives "Tailgating Food").
            name = group if group and _GENERIC_LINK.match(" ".join(link.name.split())) else link.name
            lst = Listing(name, link.url, wpd.listing_id(link.url), via="category_page")
            if _name_key(link.name) in excluded or (group and _name_key(group) in excluded):
                lst.status, lst.note = "SKIPPED", "excluded by the client's CSV"
            elif not path.startswith("/browse/"):
                lst.status, lst.note = "SKIPPED", "a category page or other page, not a product listing"
            elif only and path not in only and link.url.rstrip("/") not in only:
                lst.status, lst.note = "SKIPPED", "not among the subcategories chosen for this run"
            elif limit is not None and chosen >= limit:
                lst.status, lst.note = "CAPPED", f"subcategory limit of this run ({limit}) reached"
            else:
                chosen += 1
            listings.append(lst)
        cur.listings = listings
        cur.discovered = [{**asdict(x), "group": groups.get(x.url, "")} for x in links]
        with self.factory() as s:
            event(
                s,
                self.run_id,
                "INFO",
                "SUBCATEGORIES_FOUND",
                f"{node.category}: {len(links)} subcategory listings on the category page, {chosen} to read",
                {
                    "node": node.taxonomy_id,
                    "excluded_by_csv": sorted(excluded),
                    "listings": [{"name": x.name, "url": x.url, "note": x.note} for x in listings],
                },
            )
            s.commit()

    def _end(self, lst: Listing, end: str, page: int, detail: str = "") -> None:
        close_listing(lst, end, page, detail)

    def _partition(self, cur: Cursor, lst: Listing) -> None:
        """A listing larger than its result window: read the child categories its own "Departments" facet
        names, each as its own listing linked to it (never their counts added up)."""
        cov = self.settings.coverage
        if cur.listings is None:
            return
        known = {x.id for x in cur.listings}
        added = [
            Listing(c["name"], c["url"], c["id"], via="departments_facet", parent=lst.id, depth=lst.depth + 1)
            for c in lst.children
            if c["id"] not in known
        ]
        # A listing left unpartitioned says why (never silently).
        why = ""
        if not cov.partition_large_listings:
            why = "partitioning is turned off (coverage.partition_large_listings)"
        elif cov.partition_max_depth is not None and lst.depth >= cov.partition_max_depth:
            why = (
                f"the run's partition depth cap is reached (coverage.partition_max_depth = "
                f"{cov.partition_max_depth}, this listing is at depth {lst.depth})"
            )
        elif not lst.children:
            why = "its own Departments facet names no child category"
        elif not added:
            why = "every child category its Departments facet names is already read in this row"
        if why:
            lst.reason = f"{lst.reason}; not partitioned: {why}"[:500]
            return
        cur.listings.extend(added)
        lst.status = "PARTITIONED"
        lst.reason = (
            f"{lst.reason}; partitioned into {len(added)} child categories its own Departments facet names"
        )[:500]
        with self.factory() as s:
            event(
                s,
                self.run_id,
                "INFO",
                "LISTING_PARTITIONED",
                f"{lst.name or lst.id}: {lst.total} results reported, {len(lst.seen)} served; "
                f"{len(added)} child categories to read",
                {"listing": lst.id, "children": [x.id for x in added], "end": lst.end},
            )
            s.commit()

    async def collect_listing(self, ctx: TaskContext, node: Node, cur: Cursor, lst: Listing) -> None:
        assert self.session is not None and self.session.robots is not None
        limits = self.cfg.limits
        while lst.status == "IN_PROGRESS":
            page = cur.page
            if limits.max_pages_per_listing is not None and page > limits.max_pages_per_listing:
                lst.status, lst.end = "CAPPED", "PAGE_LIMIT"
                lst.reason = f"page limit of this run ({limits.max_pages_per_listing}) reached"
                break
            if page > SAFETY_MAX_PAGES:
                lst.status, lst.end = "INCOMPLETE", "SAFETY_LIMIT"
                lst.reason = f"more than {SAFETY_MAX_PAGES} result pages"
                break
            url = wpd.page_url(lst.url, page)
            if not self.session.robots.allowed(url):
                lst.status, lst.end = "INCOMPLETE", "ROBOTS"
                lst.reason = f"robots.txt does not allow result page {page}"
                break
            self.check(ctx)
            try:
                fetch = await self.session.navigate(url, "listing", settle_ms=self.LISTING_SETTLE_MS)
            except NotInSource as exc:
                lst.status, lst.end, lst.reason = "INCOMPLETE", "NOT_IN_SOURCE", str(exc)[:500]
                break
            self.steps += 1
            res = self._page(ctx, node, cur, lst, fetch, page)
            if res is None:  # the listing ended here (or is empty): _page set why
                break
            lst.pages_read += 1
            if res.capped is None and not res.category_capped:
                cur.page = page + 1
                if lst.max_page is not None and page >= lst.max_page:
                    self._end(
                        lst, "LAST_PAGE", page, f"result page {page} is the last page the listing links"
                    )
                elif page > 1 and res.new_keys == 0 and res.products > res.sponsored:
                    # A later page that shows only products of earlier pages: the site repeated a page.
                    self._end(lst, "REPEATED_PAGE", page, f"result page {page} repeated earlier products")
            ctx.checkpoint(cur.as_dict(node))
            self.canary(fetch, res)
            # The own pages of this result page's products (their UPC), before the next result page.
            await self.read_details(ctx)
            if res.capped is not None:
                usage = self.usage()
                if res.capped is StopCode.RUN_PRODUCT_LIMIT:
                    detail = f"{usage.run_products} verified products in this run"
                    detail += f" (limit {limits.max_products_per_run})"
                else:
                    detail = f"{usage.day_products} verified products today"
                    detail += f" (limit {limits.max_products_per_day})"
                raise RunStop(res.capped, detail, resumable=True)
            if res.category_capped:
                lst.status, lst.end = "CAPPED", "CATEGORY_LIMIT"
                lst.reason = f"product limit per category of this run ({limits.max_products_per_category})"
                cur.status, cur.reason = "CAPPED", lst.reason
                for rest in cur.listings or []:
                    if rest.status == "PENDING":
                        rest.status, rest.note = "CAPPED", lst.reason
                break
        if lst.status == "INCOMPLETE" and lst.end in WINDOW_ENDS:
            self._partition(cur, lst)
            ctx.checkpoint(cur.as_dict(node))
        # The listing's final state in its coverage row now (a run stopped later in the row keeps it).
        with self.factory() as s:
            self._coverage(s, node, lst)
            s.commit()

    def _page(
        self, ctx: TaskContext, node: Node, cur: Cursor, lst: Listing, fetch: PageFetch, page: int
    ) -> PageResult | None:
        """Check one result page and record its products, or end the listing with the reason."""
        try:
            nd = wpd.next_data(self.html(fetch))
        except wpd.PageDataMissing as exc:
            with self.factory() as s:
                self.persist(s, ctx)
                self._contract(s, f"{fetch.url}: {exc}")
                s.commit()
            raise AbnormalPage(f"{fetch.url}: {exc}") from None
        if missing := wpd.not_found_page(nd):
            # The site's own not-found page for this link (its data is the page /404): the listing is not
            # read, says so, and the run goes on (release 1.6.3). Never an empty listing, never a refusal:
            # release 1.6.2 called the page a challenge (its minified page data was not recognized), stopped
            # the run and held the store, on the Shampoo child "nexxus-shampoo" on 2026-11-04.
            lst.status, lst.end = "INCOMPLETE", "NOT_FOUND"
            lst.reason = (
                "not read: the site answered "
                + ("this listing link" if page == 1 else f"result page {page} of this listing")
                + f" with its not-found page (page data route {missing}, HTTP {fetch.status})"
            )[:500]
            with self.factory() as s:
                self.persist(s, ctx)
                self._coverage(s, node, lst)
                event(
                    s,
                    self.run_id,
                    "WARN",
                    "LISTING_NOT_FOUND",
                    f"{lst.name or lst.id}: {lst.reason}",
                    {"listing": lst.id, "page": page, "page_fetch_id": fetch.fetch_id, "url": fetch.url},
                )
                s.commit()
            return None
        if wpd.search_result(nd) is None:
            served = wpd.category_page(nd) if page == 1 else ""
            if served:
                # The site served a category page (links to other listings, no result grid) for this listing
                # link: the listing is not read, says so with the listings that page links, and the run goes
                # on (release 1.6.2; release 1.6.1 stopped the run and held the store, as for an unknown
                # page, when "Fresh Flowers" served "Flower Shop" on 2026-11-03). Never an empty listing.
                links = wpd.subcategory_links(nd, self._origin(fetch))
                lst.status, lst.end = "INCOMPLETE", "CATEGORY_PAGE"
                lst.reason = (
                    f"not read: the site served the category page {served} for this listing link (links to "
                    f"other listings, no result grid); that page links {len(links)} listings"
                    + (": " + "; ".join(x.name for x in links) if links else "")
                )[:500]
                with self.factory() as s:
                    self.persist(s, ctx)
                    self._coverage(s, node, lst)
                    s.commit()
                return None
            # A page without its search result is not an empty listing: a new layout or a cut response.
            with self.factory() as s:
                self.persist(s, ctx)
                self._contract(s, f"{fetch.url}: the page data has no search result")
                s.commit()
            raise AbnormalPage(f"{fetch.url}: the page data has no search result (unexpected shape)")
        if page == 1 and (lst.parent or (node.kind == "landing" and not lst.name)):
            # A configured listing read without its category page (direct_listings) must place itself under
            # the row's category; a child category under its parent listing (a partition).
            name, crumbs = wpd.listing_identity(nd)
            under = lst.parent or node.taxonomy_id
            placed = (
                any(under in c.split("_") for c in crumbs)
                if not lst.parent
                else any(c == under or c.startswith(f"{under}_") for c in crumbs)
            )
            if not name or not placed:
                lst.status, lst.end = "INCOMPLETE", "IDENTITY"
                lst.reason = (
                    f"the listing's own page does not place it under {under}: name {name!r}, "
                    f"breadcrumb {crumbs}"
                )[:500]
                with self.factory() as s:
                    self.persist(s, ctx)
                    self._coverage(s, node, lst)
                    s.commit()
                return None
            lst.name = lst.name or name
        try:
            items = wpd.page_items(nd, self._origin(fetch))
            stacks = wpd.item_stacks(nd)
        except wpd.PageShapeUnclear as exc:
            # The listing's results cannot be told from the page's other modules: a site contract failure.
            with self.factory() as s:
                self.persist(s, ctx)
                self._contract(s, f"{fetch.url}: {exc}")
                s.commit()
            raise AbnormalPage(f"{fetch.url}: {exc}") from None
        pag = wpd.pagination(nd)
        previous_total = lst.total
        if page == 1:
            lst.total, lst.max_page = pag.total_count, pag.max_page
            lst.children = [
                {"id": c.id, "name": c.name, "url": c.url, "path": c.path}
                for c in wpd.child_categories(nd, lst.id, self._origin(fetch))
                if c.id.count("_") == lst.id.count("_") + 1
            ]
        elif pag.total_count:
            lst.total = pag.total_count  # the latest count the listing reports
        organic = [i for i in items if not i.sponsored]
        # The fulfillment Walmart filtered the result grid for (release 1.4.1), from the grid's own data:
        # "Pickup", or "none" when the grid names no filter (the store's whole grid, out-of-stock and
        # shipping-only items too). What the reported total counts depends on it.
        grid_filter = "; ".join(sorted({x.fulfillment_filter or "none" for x in stacks if x.primary}))
        lst.pages.append(
            {
                "page": page,
                "fetch_id": fetch.fetch_id,
                "products": len(items),
                "organic": len(organic),
                "sponsored": len(items) - len(organic),
                "new_identities": len({wrec.product_key(i) for i in organic} - set(lst.seen)),
                "reported_total": pag.total_count,
                "page_count": pag.page_count,
                "max_page": pag.max_page,
                "result_stacks": [x.index for x in stacks if x.primary],
                "grid_filter": grid_filter or "no result grid",
                # Other modules on the page (e.g. an "Available for shipping" carousel): evidence only, their
                # products are not results of the listing and are not recorded.
                "other_modules": [
                    {"stack": x.index, "layout": x.layout, "title": x.title, "products": x.products}
                    for x in stacks
                    if not x.primary
                ],
            }
        )
        if not items:
            if page == 1 and (pag.total_count not in (0, None) or wpd.placements(nd)):
                with self.factory() as s:
                    self.persist(s, ctx)
                    self._contract(s, f"{fetch.url}: results reported but no product could be read")
                    s.commit()
                raise AbnormalPage(f"{fetch.url}: the page reports results but shows no product")
            # An empty page ends the listing only as the store's own page: its data must name the store and
            # the fulfillment like any other page (a page for another store or context is no end).
            v = self.verify(fetch)
            with self.factory() as s:
                self.persist(s, ctx)
                self.attest(s, v, "task_start" if page == 1 else "periodic")
                if not v.passed:
                    s.commit()
                    raise RunStop(
                        StopCode.STORE_NOT_VERIFIED,
                        f"{fetch.final_url or fetch.url}: "
                        + ("; ".join(v.failures()) or "store context incomplete"),
                        resumable=False,
                    )
                self._contract(s, None)
                if page == 1:
                    lst.status, lst.end, lst.reason = "EMPTY", "EMPTY_PAGE", "the listing shows 0 results"
                else:
                    # Walmart's listings answered an empty page 11 that reports 0 results while page 10
                    # reported tens of thousands and 25 linked pages (2026-10-23): the window ends there.
                    contradictory = (
                        bool(previous_total)
                        and not pag.total_count
                        and pag.max_page is not None
                        and page <= pag.max_page
                    )
                    detail = (
                        f"result page {page} shows no products and reports {pag.total_count or 0} results, "
                        f"while page {page - 1} reported {previous_total} and the listing links "
                        f"{pag.max_page} pages"
                        if contradictory
                        else f"result page {page} shows no products"
                    )
                    lst.total = previous_total  # the empty page's count does not replace the listing's
                    self._end(lst, "EMPTY_PAGE", page, detail)
                self._coverage(s, node, lst)
                s.commit()
            return None
        v = self.verify(fetch)
        problem = None if lst.total is not None else f"{fetch.url}: no result count in the page data"
        with self.factory() as s:
            self.persist(s, ctx)
            self.attest(s, v, "task_start" if page == 1 else "periodic")
            self._contract(s, problem)
            if not v.passed:
                s.commit()
                raise RunStop(
                    StopCode.STORE_NOT_VERIFIED,
                    f"{fetch.final_url or fetch.url}: "
                    + ("; ".join(v.failures()) or "store context incomplete"),
                    resumable=False,
                )
            res = self.record_page(s, node, lst, fetch, items, page)
            self._coverage(s, node, lst)
            self.heartbeat(s)
            queue.heartbeat(s, ctx.lease, lease_s=ctx.lease_s)  # fence: only the task's owner writes
            event(
                s,
                self.run_id,
                "INFO",
                "PAGE_COLLECTED",
                f"{node.category} › {lst.name or node.category}: result page {page}",
                {
                    "node": node.taxonomy_id,
                    "listing": lst.id,
                    "page": page,
                    "products": res.products,
                    "new_records": res.new_records,
                    "new_verified": res.new_verified,
                    "duplicates": res.duplicates,
                    "sponsored": res.sponsored,
                    "excluded": res.excluded,
                    "total": lst.total,
                    "max_page": lst.max_page,
                    "seen": len(lst.seen),
                    "bytes": fetch.notes.get("bytes_received"),
                },
            )
            s.commit()
        return res

    def _coverage(self, s: Session, node: Node, lst: Listing) -> None:
        organic, total = len(lst.seen), lst.total
        totals = reported_totals(lst.pages)
        r = reconcile_listing((set(lst.seen), set(lst.sponsored)), totals, total, page_placements(lst.pages))
        values = {
            "total_count": total,
            "organic_upcs": organic,
            # Placed identities over the reported total, never clamped (above 1.0: an overcount).
            "coverage_ratio": (1.0 if r["placed"] == 0 else None)
            if total == 0
            else (r["placed"] / total if total else None),
            "status": lst.status if lst.status != "IN_PROGRESS" else "IN_PROGRESS",
            "partition": {
                "reconciliation": r,
                "url": lst.url,
                "pages": lst.pages_read,
                "max_page": lst.max_page,
                # A listing not read says why (excluded, not a listing, not chosen, a limit of the run).
                "reason": lst.reason or lst.note,
                "end": lst.end,
                "via": lst.via,
                "parent": lst.parent,
                "depth": lst.depth,
                "children_named": [c["id"] for c in lst.children],
                "result_pages": lst.pages,
            },
        }
        s.execute(
            insert(NodeCoverage)
            .values(
                id=new_id(),
                run_id=self.run_id,
                category_source_id=node.category_source_id,
                taxonomy_id=(lst.id or node.taxonomy_id)[:64],
                **values,
            )
            .on_conflict_do_update(constraint="uq_node_coverage_key", set_=values)
        )

    def _finish(self, node: Node, cur: Cursor) -> dict[str, Any]:
        with self.factory() as s:
            for lst in cur.listings or []:
                if lst.status != "PENDING" or lst.note:
                    self._coverage(s, node, lst)
            d = cur.as_dict(node)
            outcomes = listing_outcomes(cur.listings or [])
            event(
                s,
                self.run_id,
                "INFO" if cur.status in ("DONE", "EMPTY") else "WARN",
                f"NODE_{cur.status}",
                f"{node.category}: {len(d['seen'])} distinct products in {len(outcomes)} listings"
                + (f" ({cur.reason})" if cur.reason else ""),
                {
                    "node": node.taxonomy_id,
                    "pages": d["steps_done"],
                    "listings": [
                        {
                            k: o[k]
                            for k in (
                                "id",
                                "status",
                                "end",
                                "total",
                                "seen",
                                "difference",
                                "basis",
                                "unresolved_difference",
                            )
                        }
                        for o in outcomes
                    ],
                },
            )
            s.commit()
        return cur.as_dict(node)

    def listing_coverage(self, cursor: Mapping[str, Any]) -> list[dict[str, Any]] | None:
        cur = Cursor.from_dict(cursor)
        if not cur.listings:
            return None
        return listing_outcomes(cur.listings)

    # -- records ----------------------------------------------------------------------------------

    def store_values(self) -> tuple[StoreFields, dict[str, FieldSource]]:
        sel = self.selection
        assert sel is not None
        d = sel.details
        src = FieldSource("walmart_store_page", d.path, sel.store_page_fetch, None, sel.observed_at)
        fields = StoreFields(
            zipcode=d.postal_code, store_name=d.name, store_location=d.location_text, store_logo=sel.logo
        )
        prov = {"zipcode": src, "store_name": src, "store_location": src}
        if sel.logo:
            prov["store_logo"] = FieldSource(
                "walmart_page_header", sel.logo_ref, sel.store_page_fetch, None, sel.observed_at
            )
        return fields, prov

    def record_page(
        self, s: Session, node: Node, lst: Listing, fetch: PageFetch, items: list[wpd.WalmartItem], page: int
    ) -> PageResult:
        """Records for the products of one verified result page, within the product limits; every
        placement is kept as a membership. A product is recorded once per run; a later tile of it that shows
        another local state decides its record again (:meth:`repeated_tile`). The options a tile names when
        no record is kept from it (a repeated tile of a product already recorded, or a sponsored tile) are
        kept for the variant follow-up, one ``tile_options`` observation per product and page."""
        res = PageResult(products=len(items))
        observed = datetime.fromisoformat(fetch.started_at.replace("Z", "+00:00"))
        limits = self.cfg.limits
        room = product_room(limits, self.usage())
        cat_room = (
            None
            if limits.max_products_per_category is None
            else limits.max_products_per_category - category_verified(s, self.run_id, node.category)
        )
        seen = set(lst.seen)
        memberships: list[dict[str, Any]] = []
        options: dict[str, list[wpd.WalmartItem]] = {}  # product key: its tiles with options no record keeps
        for item in items:
            key = wrec.product_key(item)
            memberships.append(
                {
                    "run_id": self.run_id,
                    "mode": self.run_mode,
                    "upc": key,
                    "category_source_id": node.category_source_id,
                    "taxonomy_id": (lst.id or node.taxonomy_id)[:64],
                    "coupon_id": None,
                    "page_offset": page,
                    "position": item.position,
                    "via": "paid" if item.sponsored else "organic",
                }
            )
            if item.sponsored:
                res.sponsored += 1
                if key not in lst.sponsored:
                    lst.sponsored.append(key)
                if item.variants:
                    options.setdefault(key, []).append(item)
                # Kept as its own observation (never a record): the follow-up reads the product's own page.
                s.execute(
                    insert(ProductObservation)
                    .values(
                        id=new_id(),
                        run_id=self.run_id,
                        mode=self.run_mode,
                        upc=key,
                        page_fetch_id=fetch.fetch_id,
                        source="sponsored_card",
                        displayed=wrec.displayed(item),
                        structured={},
                        provenance={
                            "verified": False,
                            "sponsored": True,
                            "retailer": RETAILER,
                            "item_id": item.item_id,
                            "url": item.url,
                            "name": item.name,
                            "node": node.taxonomy_id,
                            "listing": lst.id,
                            "listing_url": lst.url,
                            "category": node.category,
                            "sub_category": lst.name,
                            "page": page,
                            "position": item.position,
                            "segment": self.segment_id,
                            "worker": self.worker_name,
                        },
                        flags=[],
                        parser_version=PARSER_VERSION,
                        observed_at=observed,
                    )
                    .on_conflict_do_nothing(constraint="uq_product_observations_key")
                )
                continue
            if key not in seen:
                seen.add(key)
                lst.seen.append(key)
                res.new_keys += 1
            if key in self.recorded:
                res.duplicates += 1
                if item.variants:
                    options.setdefault(key, []).append(item)
                has_room = (room is None or room > 0) and (cat_room is None or cat_room > 0)
                change, category = self.repeated_tile(
                    s, node, lst, fetch, item, key, page, observed, has_room
                )
                if room is not None:
                    room -= change
                if cat_room is not None and category == node.category:
                    cat_room -= change
                continue
            tile = self.tile_record(
                s, key, item, fetch, observed, CategoryAssignment(node.category, lst.name)
            )
            built = tile.built
            verified = tile.verified
            if verified and room is not None and room <= 0:
                res.capped = product_limit_code(limits, self.usage()) or StopCode.RUN_PRODUCT_LIMIT
                break
            if verified and cat_room is not None and cat_room <= 0:
                res.category_capped = True
                break
            s.execute(
                insert(ProductObservation)
                .values(
                    id=new_id(),
                    run_id=self.run_id,
                    mode=self.run_mode,
                    upc=key,
                    page_fetch_id=fetch.fetch_id,
                    source="card",
                    displayed=wrec.displayed(item),
                    structured={"walmart": tile.log},
                    provenance=self.card_provenance(node, lst, page, item, tile),
                    flags=[f.value for f in built.flags],
                    parser_version=PARSER_VERSION,
                    observed_at=observed,
                )
                .on_conflict_do_nothing(constraint="uq_product_observations_key")
            )
            s.execute(
                insert(RecordRow)
                .values(
                    id=new_id(),
                    run_id=self.run_id,
                    mode=self.run_mode,
                    upc=key,
                    record=built.record,
                    record_sha256=record_sha256(built.record),
                    primary_category_source_id=node.category_source_id,
                    status=built.status.value,
                    reasons=[r.value for r in built.reasons],
                    flags=[f.value for f in built.flags],
                )
                .on_conflict_do_nothing(constraint="uq_records_run_upc")
            )
            self.add_offers(s, key, fetch, built)
            self.recorded.add(key)
            res.new_records += 1
            if built.status is RecordStatus.EXCLUDED:
                res.excluded += 1
            if verified:
                res.new_verified += 1
                if room is not None:
                    room -= 1
                if cat_room is not None:
                    cat_room -= 1
        for key, tiles in options.items():
            siblings = {v.item_id: asdict(v) for t in tiles for v in t.variants}
            s.execute(
                insert(ProductObservation)
                .values(
                    id=new_id(),
                    run_id=self.run_id,
                    mode=self.run_mode,
                    upc=key,
                    page_fetch_id=fetch.fetch_id,
                    source="tile_options",
                    displayed={},
                    structured={},
                    provenance={
                        "verified": False,
                        "retailer": RETAILER,
                        "item_id": tiles[0].item_id,
                        "url": tiles[0].url,
                        "name": tiles[0].name,
                        "node": node.taxonomy_id,
                        "listing": lst.id,
                        "listing_url": lst.url,
                        "category": node.category,
                        "sub_category": lst.name,
                        "page": page,
                        "tiles": [{"position": t.position, "sponsored": t.sponsored} for t in tiles],
                        "variant_siblings": list(siblings.values()),
                        "segment": self.segment_id,
                        "worker": self.worker_name,
                    },
                    flags=[],
                    parser_version=PARSER_VERSION,
                    observed_at=observed,
                )
                .on_conflict_do_nothing(constraint="uq_product_observations_key")
            )
        insert_memberships(s, memberships)
        return res

    def tile_record(
        self,
        s: Session,
        key: str,
        item: wpd.WalmartItem,
        fetch: PageFetch,
        observed: datetime,
        category: CategoryAssignment,
        same_run: retention.Verified | None = None,
        approx_seen: Mapping[str, str] | None = None,
    ) -> TileBuild:
        """The record a result tile gives, with store assortment decided apart from the local offer
        (:meth:`assortment`). ``same_run`` is a tile of this run, observed earlier, that verified the product
        at the store (release 1.3.1: a later tile of the same run is judged with it). ``approx_seen`` is the
        approximate or estimated-weight wording another tile of the product displayed in this run (release
        1.4.0): the whole product is excluded, also from a tile that shows no wording (a sponsored tile shows
        none next to an "each (est.)" price)."""
        observed_iso = iso(observed)
        store_values, store_prov = self.store_values()
        ev, offer, log = wrec.evidence(
            item,
            fetch_id=fetch.fetch_id,
            observed_at=observed_iso,
            store_id=self.store.location_id,
            modality=self.modality,
            page_verified=True,
        )
        if approx_seen and not ev.approx_weight_text:
            ev = replace(ev, approx_weight_text=approx_seen["text"], approx_weight_source=approx_seen)
        built = build_product_record(
            ev,
            store=store_values,
            category=category,
            crawl_date=store_local_date(observed, self.store.timezone),
            settings=self.settings.records,
            detector=self.pipe.detector,
            configured_modality=self.modality,
            store_provenance=store_prov,
        )
        built = wrec.explain_missing(built, item, offer, STORE_LOGO_NOTE)
        built, assortment = self.assortment(s, key, built, offer, observed, same_run)
        missing_kind = wrec.missing_kinds(built, item, offer)
        if assortment.get("basis") in ("local_offer_observed_earlier", "store_line_other_fulfillment"):
            missing_kind.update({f: "context_failed" for f in OFFER_FIELDS if f in built.missing})
        # When each exported value was observed (all on this page, the store's on its store page; a UPC
        # read later from the product's own page adds its own time).
        field_observed_at = {f: observed_iso for f, v in built.record.items() if v}
        for f in ("zipcode", "store_name", "store_location", "store_logo"):
            if built.record.get(f) and self.selection is not None:
                field_observed_at[f] = self.selection.observed_at
        return TileBuild(built, log, assortment, missing_kind, field_observed_at)

    def card_provenance(
        self, node: Node, lst: Listing, page: int, item: wpd.WalmartItem, tile: TileBuild
    ) -> dict[str, Any]:
        """The provenance of the observation a record is kept from (its result tile)."""
        built = tile.built
        return {
            "verified": tile.verified,
            "retailer": RETAILER,
            "node": node.taxonomy_id,
            "listing": lst.id,
            "listing_url": lst.url,
            "category": node.category,
            "sub_category": lst.name,
            "page": page,
            "position": item.position,
            "store_check": "PASS",
            "local_offer": tile.log["local_offer"],
            # Store assortment (A) apart from the current offer (B): see retention.py.
            "assortment": tile.assortment,
            "segment": self.segment_id,
            "worker": self.worker_name,
            "session": self.sessions_opened,
            "session_id": self.session.session_id if self.session else None,
            "pilot": self.pilot,
            # Other items the tile offers as options (followed by the run's follow-up task).
            "variant_siblings": [asdict(v) for v in item.variants],
            "fields": built.provenance,
            "field_observed_at": tile.field_observed_at,
            "missing": built.missing,
            "missing_kind": tile.missing_kind,
            "source_check": built.source_check,
            "offers": offer_summaries(built, self.settings),
        }

    def add_offers(self, s: Session, key: str, fetch: PageFetch, built: BuiltRecord) -> None:
        """The offers a tile shows, one row each (the record's deal fields are decided from them)."""
        for c in built.deals.classified:
            s.add(
                OfferObservationRow(
                    run_id=self.run_id,
                    mode=self.run_mode,
                    upc=key,
                    page_fetch_id=fetch.fetch_id,
                    source=c.offer.source.value,
                    tag=c.offer.tag,
                    headline=c.offer.text,
                    description=format_description(c.offer, self.settings.records.deal_description_format),
                    expiry_text=c.offer.expiry_text,
                    requires_clip=c.requires_clip,
                    kind=c.kind.value,
                    explicit_price=c.explicit_price,
                    modalities=sorted(c.restricted_to) if c.restricted_to else [],
                    flags=[f.value for f in c.flags],
                )
            )

    def repeated_tile(
        self,
        s: Session,
        node: Node,
        lst: Listing,
        fetch: PageFetch,
        item: wpd.WalmartItem,
        key: str,
        page: int,
        observed: datetime,
        has_room: bool,
    ) -> tuple[int, str]:
        """Another result tile of a product this run already recorded (release 1.3.1; release 1.3.0 counted it
        as a duplicate only).

        The record holds the latest state of the product the run observed. When a tile observed later shows
        another local state (availability, the store's line, a price, an offer), the record is decided again
        from that tile. The run's own earlier tiles count as the store verification. The state the record
        held is kept in its observation's ``earlier_in_run``, with its page and time.

        A tile observed before the record's own (two workers' requests overlapping) does not replace the
        record; its state is kept there too. If that tile verifies the product, a record whose assortment
        was unresolved is kept without a local price, exactly as when the tiles are read in order.

        Approximate or estimated-weight wording any tile of the run displayed excludes the whole product
        (release 1.4.0): a later tile without it (a sponsored tile shows no "each (est.)") keeps the
        exclusion and its trace to the tile that showed it, and a tile observed earlier that showed it
        decides the record even when processed later.

        These stay as they were: the record's category (the listing it was first recorded from), the UPC
        read from the product's own page, and a duplicate-UPC exclusion. A later tile that would make the
        record verified while the run's product limit is used up is not applied (an event says so). Returns
        the change in the run's verified records and the record's category."""
        rec = s.scalar(select(RecordRow).where(RecordRow.run_id == self.run_id, RecordRow.upc == key))
        obs = s.scalar(
            select(ProductObservation).where(
                ProductObservation.run_id == self.run_id,
                ProductObservation.upc == key,
                ProductObservation.source == "card",
            )
        )
        if rec is None or obs is None or RecordFlag.DUPLICATE_UPC.value in (rec.reasons or []):
            return 0, ""  # recorded from a product page, or another record's duplicate: kept as it is
        category = CategoryAssignment(
            str(rec.record.get("category") or ""), str(rec.record.get("sub_category") or "")
        )
        prov = dict(obs.provenance or {})
        states = [*retention.earlier_in_run(prov), self.held_state(rec, obs)]
        same_run = self.run_verified(rec, [st for st in states if state_time(st) < observed])
        tile = self.tile_record(s, key, item, fetch, observed, category, same_run, displayed_approx(states))
        built = tile.built
        record = dict(built.record)
        if not record.get("upc") and rec.record.get("upc"):
            record["upc"] = str(rec.record["upc"])  # the identity read from the product's own page stays
        reasons = [r.value for r in built.reasons]
        flags = [f.value for f in built.flags]
        if local_state(record, built.status.value, reasons, flags) == local_state(
            rec.record, rec.status, rec.reasons or [], rec.flags or []
        ):
            return 0, category.category
        was = {"page_fetch_id": obs.page_fetch_id, "observed_at": iso(obs.observed_at), "status": rec.status}
        now = {"page_fetch_id": fetch.fetch_id, "observed_at": iso(observed), "status": built.status.value}
        approx = RecordFlag.APPROX_WEIGHT.value
        if observed > obs.observed_at or (approx in reasons and approx not in (rec.reasons or [])):
            was_verified = rec.status == RecordStatus.VALID.value
            if tile.verified and not was_verified and not has_room:
                event(
                    s,
                    self.run_id,
                    "WARN",
                    "LATER_TILE_NOT_APPLIED",
                    f"{key}: a later tile would make the record valid; the run's product limit is used up",
                    {"key": key, "record": was, "tile": now},
                )
                return 0, category.category
            replaced = dict(self.card_provenance(node, lst, page, item, tile))
            replaced.update(
                category=category.category,
                sub_category=category.sub_category,
                variant_siblings=merged_siblings(prov.get("variant_siblings"), replaced["variant_siblings"]),
                earlier_in_run=sorted(states, key=state_time),
            )
            obs.page_fetch_id = fetch.fetch_id
            obs.displayed = wrec.displayed(item)
            obs.structured = {"walmart": tile.log}
            obs.provenance = replaced
            obs.flags = flags
            obs.parser_version = PARSER_VERSION
            obs.observed_at = observed
            rec.record = record
            rec.record_sha256 = record_sha256(ordered_record(record))
            rec.status = built.status.value
            rec.reasons = reasons
            rec.flags = flags
            self.add_offers(s, key, fetch, built)
            event(
                s,
                self.run_id,
                "INFO",
                "RECORD_STATE_CHANGED_IN_RUN",
                f"{key}: {was['status']} at {was['observed_at']} -> {now['status']} at {now['observed_at']} "
                f"({lst.id} page {page})",
                {"key": key, "from": was, "to": now},
            )
            return int(tile.verified) - int(was_verified), category.category
        # Observed before the record's own tile: kept with the earlier states, never the record's state.
        entry = {
            "observed_at": iso(observed),
            "page_fetch_id": fetch.fetch_id,
            "listing": lst.id,
            "listing_url": lst.url,
            "page": page,
            "position": item.position,
            "status": built.status.value,
            "reasons": reasons,
            "flags": flags,
            "record": record,
            "local_offer": tile.log["local_offer"],
            "assortment": tile.assortment,
            "structured": {"walmart": tile.log},
            "displayed": wrec.displayed(item),
        }
        prov["earlier_in_run"] = sorted([*retention.earlier_in_run(prov), entry], key=state_time)
        verifying = self.run_verified(rec, [entry])
        decided = dict(prov.get("assortment") or {})
        if verifying is not None and RecordFlag.ASSORTMENT_UNRESOLVED.value in (rec.reasons or []):
            self.retain_unresolved(rec, obs, prov, verifying)
        elif (
            verifying is not None
            and decided.get("status") == "verified_earlier"
            and state_time(decided.get("verified") or {"observed_at": "1970-01-01T00:00:00Z"}) < observed
        ):
            prov["assortment"] = {**decided, "verified": verifying.summary(obs.observed_at)}
        obs.provenance = prov
        event(
            s,
            self.run_id,
            "INFO",
            "TILE_OBSERVED_BEFORE_RECORD",
            f"{key}: a tile observed at {now['observed_at']} was processed after the record's tile of "
            f"{was['observed_at']}; kept with the earlier states",
            {"key": key, "record": was, "tile": now},
        )
        return 0, category.category

    @staticmethod
    def held_state(rec: RecordRow, obs: ProductObservation) -> dict[str, Any]:
        """The state a record holds now, with the tile it is kept from (an ``earlier_in_run`` entry)."""
        p = obs.provenance or {}
        return {
            "observed_at": iso(obs.observed_at),
            "page_fetch_id": obs.page_fetch_id,
            "listing": p.get("listing"),
            "listing_url": p.get("listing_url"),
            "page": p.get("page"),
            "position": p.get("position"),
            "status": rec.status,
            "reasons": list(rec.reasons or []),
            "flags": list(rec.flags or []),
            "record": dict(rec.record),
            "local_offer": p.get("local_offer"),
            "assortment": p.get("assortment"),
            "structured": dict(obs.structured or {}),
            "displayed": dict(obs.displayed or {}),
        }

    def run_verified(self, rec: RecordRow, states: list[dict[str, Any]]) -> retention.Verified | None:
        """The latest of ``states`` (this run's tiles of the product) that verifies it at the store under the
        current rules (:func:`retention.state_refusal`), as a verification."""
        for st in sorted(states, key=state_time, reverse=True):
            why = retention.state_refusal(
                st,
                self.store.location_id,
                self.modality,
                self.settings.records.exclude_relative_price_items,
            )
            if why is None:
                return retention.Verified(
                    rec.upc,
                    self.run_id,
                    state_time(st),
                    dict(st.get("record") or {}),
                    tuple(st.get("flags") or []),
                    rec.primary_category_source_id,
                    st.get("listing"),
                    str(st.get("page_fetch_id") or ""),
                )
        return None

    def retain_unresolved(
        self, rec: RecordRow, obs: ProductObservation, prov: dict[str, Any], verified: retention.Verified
    ) -> None:
        """Keep a record whose assortment was unresolved without a local price, when a tile of the same run
        observed before it verifies the product. The result is what :meth:`assortment` and :meth:`_unpriced`
        give for a tile read after the verifying one."""
        note = str((prov.get("local_offer") or {}).get("note") or "")
        why = (
            f"no local offer at store {self.store.location_id} on this page ({note}); a shipping, "
            "marketplace or unverified value is never used"
        )
        reasons = [r for r in rec.reasons or [] if r != RecordFlag.ASSORTMENT_UNRESOLVED.value]
        keep = [r for r in reasons if r != RecordFlag.LOCATION_UNATTESTED.value]
        flags = list(dict.fromkeys([*(rec.flags or []), *keep, RecordFlag.NO_LOCAL_OFFER.value]))
        record = {**rec.record, **{f: "" for f in OFFER_FIELDS}}
        sources = dict(prov.get("fields") or {})
        fields = {k: v for k, v in sources.items() if k not in OFFER_FIELDS}
        if unused := {k: v for k, v in sources.items() if k in OFFER_FIELDS}:
            fields["_offer_values_not_used"] = {"why": why, "read_from": unused}
        rec.record = record
        rec.record_sha256 = record_sha256(ordered_record(record))
        rec.status = RecordStatus.EXPORTED_NOT_VALID.value
        rec.reasons = []
        rec.flags = flags
        obs.flags = flags
        prov.update(
            fields=fields,
            missing={**(prov.get("missing") or {}), **{f: why for f in OFFER_FIELDS}},
            missing_kind={**(prov.get("missing_kind") or {}), **{f: "context_failed" for f in OFFER_FIELDS}},
            field_observed_at={
                k: v for k, v in (prov.get("field_observed_at") or {}).items() if k not in OFFER_FIELDS
            },
            assortment={
                "status": "verified_earlier",
                "basis": "local_offer_observed_earlier",
                "evidence": note,
                "verified": verified.summary(obs.observed_at),
            },
        )

    # -- follow-ups: sponsored-only products and tile-only variant siblings --------------------------------

    def _listings(self, s: Session) -> dict[str, tuple[Node, Listing]]:
        """Every listing this run read (by listing id) with its CSV row, from the listing tasks'
        checkpoints."""
        out: dict[str, tuple[Node, Listing]] = {}
        for task_id, raw in s.execute(
            select(Task.id, Task.cursor)
            .where(Task.run_id == self.run_id, Task.kind == "listing_node")
            .order_by(Task.id)
        ):
            cursor = jv.obj(raw, f"checkpoint of task {task_id}")
            if "node" not in cursor:
                continue
            node = Node.from_dict(jv.obj(cursor["node"], f"checkpoint of task {task_id}: node"))
            for lst in Cursor.from_dict(cursor).listings or []:
                if lst.pages_read:
                    out.setdefault(lst.id, (node, lst))
        return out

    def follow_candidates(self, s: Session, kind: str) -> list[dict[str, Any]]:
        """The items to follow, seeds first: products seen only in sponsored placements (``sponsored``), or
        items result tiles offer as options and the run never saw as their own tile (``variant``), named by
        the tile a product was recorded from (``card``) or by its other tiles (``tile_options``)."""
        out: dict[str, dict[str, Any]] = {}
        for seed in self.cfg.follow_up.seeds:
            if seed.kind == kind:
                key = f"{wrec.KEY_PREFIX}{seed.item_id}"
                out.setdefault(
                    key,
                    {
                        "kind": kind,
                        "key": key,
                        "item_id": seed.item_id,
                        "url": seed.url,
                        "listing": seed.listing_id,
                        "named_by": seed.named_by,
                        "seed": seed.source or "configured",
                    },
                )
        if kind == "sponsored":
            rows = s.execute(
                select(
                    ProductObservation.upc, ProductObservation.provenance, ProductObservation.page_fetch_id
                )
                .where(
                    ProductObservation.run_id == self.run_id, ProductObservation.source == "sponsored_card"
                )
                .order_by(ProductObservation.observed_at, ProductObservation.id)
            )
            for key, prov, fetch_id in rows:
                p = jv.obj(prov, f"provenance of sponsored observation {key}")
                found = out.setdefault(
                    key,
                    {
                        "kind": kind,
                        "key": key,
                        "item_id": jv.text(p.get("item_id"), f"{key}: item_id")
                        or key.removeprefix(wrec.KEY_PREFIX),
                        "url": jv.text(p.get("url"), f"{key}: url") or None,
                        "listing": jv.text(p.get("listing"), f"{key}: listing") or None,
                        "named_by": "",
                    },
                )
                found.setdefault("seen_on", fetch_id)
        else:
            rows = s.execute(
                select(
                    ProductObservation.upc, ProductObservation.provenance, ProductObservation.page_fetch_id
                )
                .where(
                    ProductObservation.run_id == self.run_id,
                    ProductObservation.source.in_(("card", "tile_options")),
                    ProductObservation.provenance.has_key("variant_siblings"),
                )
                .order_by(ProductObservation.observed_at, ProductObservation.id)
            )
            for parent, prov, fetch_id in rows:
                p = jv.obj(prov, f"provenance of observation {parent}")
                listing = jv.text(p.get("listing"), f"{parent}: listing") or None
                for i, v in enumerate(jv.objects(p.get("variant_siblings"), f"{parent}: variant_siblings")):
                    where = f"{parent}: variant_siblings[{i}]"
                    item_id = jv.text(v.get("item_id"), f"{where}.item_id")
                    if not item_id:
                        raise jv.CorruptJson(f"{where}: no item_id")
                    key = f"{wrec.KEY_PREFIX}{item_id}"
                    found = out.setdefault(
                        key,
                        {
                            "kind": kind,
                            "key": key,
                            "item_id": item_id,
                            "url": jv.text(v.get("url"), f"{where}.url") or None,
                            "listing": listing,
                            "named_by": parent.removeprefix(wrec.KEY_PREFIX),
                            "option": {
                                "criterion": jv.text(v.get("criterion"), f"{where}.criterion") or None,
                                "value": jv.text(v.get("value"), f"{where}.value") or None,
                            },
                        },
                    )
                    found.setdefault("seen_on", fetch_id)
        return list(out.values())

    async def h_follow_up(self, ctx: TaskContext) -> dict[str, Any]:
        cursor = dict(ctx.cursor)
        name = str(cursor.get("follow") or "")
        kind = {"sponsored": "sponsored", "variants": "variant"}.get(name)
        if self.plan and self.cfg.detail.enabled and self.cfg.detail.max_per_run is not None:
            await self._with_reconnects(ctx, lambda: self._budgeted_details(ctx))
        if kind is None or not getattr(self.cfg.follow_up, name, False):
            return {**cursor, "status": "OFF", "reason": "this follow-up is off in the run's configuration"}
        if not self.plan:
            return {**cursor, "status": "EMPTY", "reason": "the run has no listing"}
        self.check(ctx)
        return await self._with_reconnects(ctx, lambda: self.follow_up(ctx, name, kind))

    def _queued_candidate(self, row: FollowUpItem) -> dict[str, Any]:
        """A candidate an earlier run of the store named and no run has read to a decision (the queue)."""
        return {
            "kind": row.kind,
            "key": f"{wrec.KEY_PREFIX}{row.item_id}",
            "item_id": row.item_id,
            "url": row.url,
            "listing": row.listing,
            "named_by": row.named_by or "",
            **({"option": row.option} if row.option else {}),
            "queued_from": row.first_seen_run,
        }

    async def follow_up(self, ctx: TaskContext, name: str, kind: str) -> dict[str, Any]:
        cursor = dict(ctx.cursor)
        done: list[str] = list(cursor.get("done") or [])
        counts: dict[str, int] = dict(cursor.get("counts") or {})
        fetched = int(cursor.get("fetched") or 0)
        # A run with several workers has one task per kind and worker, each with its own share of the
        # candidates (:func:`follow_shard`), so the follow-ups of a large queue run in parallel.
        shard, shards = int(cursor.get("shard") or 0), int(cursor.get("shards") or 1)
        cap = self.cfg.follow_up.max_pages
        if cap is not None and shards > 1:
            cap = cap // shards + (1 if shard < cap % shards else 0)  # the pilot's budget, divided
        # The store's follow-up queue (collection/follow_queue.py), of the run's lineage; a replay requests
        # nothing and leaves it alone.
        lin = str(self.segment_lineage.get("transport") or "")
        queued = lin in (lineage.NETWORK, lineage.SUBSTITUTED)
        from_queue = 0
        with self.factory() as s:
            candidates = [
                c for c in self.follow_candidates(s, kind) if follow_shard(str(c["item_id"]), shards) == shard
            ]
            named = len(candidates)
            listings = self._listings(s)
            if queued:
                rows = follow_queue.note_seen(
                    s,
                    store_id=self.store_id,
                    run_id=self.run_id,
                    lineage=lin,
                    candidates=candidates,
                    now=self.clock(),
                )
                for row in follow_queue.waiting(
                    s,
                    store_id=self.store_id,
                    lineage=lin,
                    kind=kind,
                    listings=listings,
                    exclude={str(c["item_id"]) for c in candidates},
                ):
                    if follow_shard(row.item_id, shards) != shard:
                        continue
                    candidates.append(self._queued_candidate(row))
                    rows[(row.kind, row.item_id)] = row
                    from_queue += 1
                candidates = follow_queue.ordered(candidates, rows)
                s.commit()
            tiles = set(s.scalars(select(MembershipRow.upc).where(MembershipRow.run_id == self.run_id)))
            # Products seen as their own organic tile (memberships, and the tiles recorded as cards).
            cards = set(
                s.scalars(
                    select(ProductObservation.upc).where(
                        ProductObservation.run_id == self.run_id, ProductObservation.source == "card"
                    )
                )
            )
            organic = cards | set(
                s.scalars(
                    select(MembershipRow.upc).where(
                        MembershipRow.run_id == self.run_id, MembershipRow.via == "organic"
                    )
                )
            )
            tiles |= cards
        for cand in candidates:
            if cand["item_id"] in done:
                continue
            where = listings.get(str(cand.get("listing") or ""))
            seen_own = cand["key"] in (organic if kind == "sponsored" else tiles)
            # A variant whose only tiles in this run were sponsored has no record from them: the sponsored
            # follow-up reads its own page, or this one does when that follow-up is off (release 1.4.1;
            # release 1.4.0 called it recorded from that placement).
            paid_only = seen_own and kind == "variant" and cand["key"] not in organic
            if paid_only and self.cfg.follow_up.sponsored:
                out = self._follow_out(
                    cand,
                    where,
                    "duplicate",
                    "this run saw it only as a sponsored tile: the sponsored follow-up reads its own page",
                )
            elif seen_own and not paid_only:
                out = self._follow_out(
                    cand,
                    where,
                    "duplicate",
                    "this run saw it as its own result tile"
                    + (" (an organic placement)" if kind == "sponsored" else "")
                    + ": recorded from that placement",
                )
            elif where is None:
                out = self._follow_out(
                    cand,
                    None,
                    "not_attempted",
                    f"the listing {cand.get('listing')} is not among the listings this run read",
                )
            elif cand["key"] in self.recorded:
                out = self._follow_out(cand, where, "duplicate", "already recorded in this run")
            elif not cand.get("url"):
                out = self._follow_out(cand, where, "not_attempted", "the source gave no product link")
            elif cap is not None and fetched >= cap:
                out = self._follow_out(
                    cand,
                    where,
                    "not_attempted",
                    f"the run's follow-up page limit ({cap} pages per kind), a pilot budget, was reached"
                    + (
                        "; the candidate stays in the store's follow-up queue for the next run"
                        if queued
                        else ""
                    ),
                )
            elif self.follow_paused is not None:
                out = self._follow_out(
                    cand, where, "not_attempted", f"follow-ups paused: {self.follow_paused}"
                )
            elif (room := product_room(self.cfg.limits, self.usage())) is not None and room <= 0:
                out = self._follow_out(cand, where, "not_attempted", "the run's product limit was reached")
            else:
                node, _ = where
                if not await self.ensure_session(ctx, node):
                    out = self._follow_out(
                        cand, where, "not_attempted", "robots.txt does not allow the listing"
                    )
                else:
                    async with self.crew.follow_lock(cand["key"]):
                        if cand["key"] in self.recorded:  # another worker's candidate read it meanwhile
                            out = self._follow_out(cand, where, "duplicate", "already recorded in this run")
                        else:
                            out = await self._follow_one(ctx, cand, where)
                            if out.get("page_fetch_id"):
                                fetched += 1
            done.append(cand["item_id"])
            counts[out["status"]] = counts.get(out["status"], 0) + 1
            with self.factory() as s:
                if queued:
                    follow_queue.record_outcome(
                        s, store_id=self.store_id, lineage=lin, out=out, run_id=self.run_id, now=self.clock()
                    )
                event(
                    s,
                    self.run_id,
                    "INFO" if out["status"] in ("included", "duplicate") else "WARN",
                    f"FOLLOW_UP_{out['status'].upper()}",
                    f"{kind} {cand['item_id']}: {out['status']}"
                    + (f" ({out['reason']})" if out.get("reason") else ""),
                    out,
                )
                s.commit()
            ctx.checkpoint({**cursor, "done": done, "counts": counts, "fetched": fetched})
        summary = {"kind": kind, "candidates": len(candidates), "pages_read": fetched, **counts}
        with self.factory() as s:
            if queued:
                # What the store's queue holds after this task: never-read and unread candidates stay there.
                left = follow_queue.counts(s, store_id=self.store_id, lineage=lin)["by_kind_and_state"]
                summary |= {
                    "named_by_run": named,
                    "from_queue": from_queue,
                    "queue_pending_after": int(left.get(f"{kind}:{follow_queue.PENDING}", 0)),
                }
            run = s.get(Run, self.run_id, with_for_update=True)
            assert run is not None
            follow = dict((run.counts or {}).get("follow_up") or {})
            follow[name] = merge_follow_summary(follow.get(name), summary)
            run.counts = {**(run.counts or {}), "follow_up": follow}
            event(s, self.run_id, "INFO", "FOLLOW_UP_DONE", f"{name}: {summary}", summary)
            s.commit()
        return {**cursor, "done": done, "counts": counts, "fetched": fetched, "status": "DONE"}

    def _follow_out(
        self, cand: Mapping[str, Any], where: tuple[Node, Listing] | None, status: str, reason: str = ""
    ) -> dict[str, Any]:
        node, lst = where if where is not None else (None, None)
        return {
            "status": status,
            "reason": reason,
            "kind": cand["kind"],
            "item_id": cand["item_id"],
            "key": cand["key"],
            "url": cand.get("url"),
            "listing": cand.get("listing"),
            "listing_name": lst.name if lst is not None else None,
            "category": node.category if node is not None else None,
            "named_by": cand.get("named_by") or None,
            "option": cand.get("option"),
            "seen_on": cand.get("seen_on"),
            "seed": cand.get("seed"),
            # An earlier run of the store named it and no run had read it to a decision (the queue).
            "queued_from": cand.get("queued_from"),
        }

    async def _follow_one(
        self, ctx: TaskContext, cand: Mapping[str, Any], where: tuple[Node, Listing]
    ) -> dict[str, Any]:
        """One candidate's own page in the store's context: identity, store, category, then the record as for
        a result page (local offer and assortment decided apart) and its UPC as the page states it."""
        session = self.session
        assert session is not None and session.robots is not None
        node, lst = where
        item_id, key = str(cand["item_id"]), str(cand["key"])
        url = wpd.absolute(str(cand["url"]), self.base)
        if not session.robots.allowed(url):
            return self._follow_out(
                cand, where, "not_attempted", "robots.txt does not allow the product page"
            )
        self.check(ctx)
        try:
            fetch = await session.navigate(url, "product_page", expect_initial_state=False)
        except NotInSource as exc:
            return self._follow_out(cand, where, "not_attempted", str(exc)[:300])
        except ChallengeDetected as exc:
            self._persist_now(ctx)
            self._follow_failed("refused (challenge)")
            out = self._follow_out(
                cand,
                where,
                "inaccessible",
                "access failed: refused (" + "; ".join(exc.fetch.challenge.reasons) + ")",
            )
            return {**out, "page_fetch_id": exc.fetch.fetch_id}
        except ProviderError as exc:
            if exc.kind in (
                ProviderErrorKind.BUDGET,
                ProviderErrorKind.CEILING,
                ProviderErrorKind.QUOTA,
                ProviderErrorKind.AUTH,
                ProviderErrorKind.CONFIG,
            ):
                raise
            self._follow_failed(f"provider: {exc.kind.value}")
            return self._follow_out(
                cand, where, "inaccessible", f"access failed: {self.redact(str(exc))[:250]}"
            )
        self.steps += 1
        base = {
            "page_fetch_id": fetch.fetch_id,
            "requested_at": fetch.started_at,
            "http_status": fetch.status,
            "credits": fetch.notes.get("credits"),
            "request_id": fetch.notes.get("request_id"),
        }
        if fetch.status != 200:
            self._persist_now(ctx)
            self._follow_failed(f"HTTP {fetch.status}")
            return {
                **self._follow_out(cand, where, "inaccessible", f"access failed: HTTP {fetch.status}"),
                **base,
            }
        html = self.html(fetch)
        try:
            nd = wpd.next_data(html)
        except wpd.PageDataMissing as exc:
            self._persist_now(ctx)
            self._follow_failed(f"parsing failed: {exc}")
            return {**self._follow_out(cand, where, "inaccessible", f"parsing failed: {exc}"), **base}
        if missing := wpd.not_found_page(nd):
            # Release 1.6.3: the site's own not-found page (until then its page data was not found: "parsing
            # failed: no __NEXT_DATA__ script in the page").
            self._persist_now(ctx)
            self._follow_failed(f"the site's not-found page ({missing})")
            reason = f"access failed: the site answered with its not-found page (page data route {missing})"
            return {**self._follow_out(cand, where, "inaccessible", reason), **base}
        pp = wpd.product_page(nd, self._origin(fetch))
        if pp is None or pp.item is None:
            self._persist_now(ctx)
            self._follow_failed("parsing failed: no product in the page data")
            return {
                **self._follow_out(
                    cand, where, "inaccessible", "parsing failed: the page data has no product"
                ),
                **base,
            }
        base["store_context"] = {
            "store_ids": list(pp.store_ids),
            "pickup_store": pp.pickup_store,
            "postal_code": pp.postal_code,
            "intent": pp.intent,
        }
        if pp.page_item != item_id:
            self._persist_now(ctx)
            self._follow_failed(f"the link led to item {pp.page_item}")
            return {
                **self._follow_out(
                    cand,
                    where,
                    "inaccessible",
                    f"the link leads to item {pp.page_item}'s page, not {item_id}'s",
                ),
                **base,
            }
        store = self.store.location_id
        if store not in pp.store_ids:
            self._persist_now(ctx)
            self._follow_failed(f"a page not shown for store {store}")
            return {
                **self._follow_out(
                    cand,
                    where,
                    "inaccessible",
                    f"the page was not shown for store {store} (its location names stores "
                    f"{list(pp.store_ids) or 'none'}, ZIP {pp.postal_code or 'none'})",
                ),
                **base,
            }
        self.follow_failures = 0  # the product's own page, in the store's context
        under, evidence = pp.under(lst.id, lst.name)
        base["category_evidence"] = evidence
        if not under:
            self._persist_now(ctx)
            return {
                **self._follow_out(
                    cand,
                    where,
                    "excluded",
                    f"required category not established: its own page files it under {evidence}, not under "
                    f"{lst.name or lst.id} ({lst.id})",
                ),
                **base,
            }
        ident = wpd.product_identifier(html, item_id)
        observed = datetime.fromisoformat(fetch.started_at.replace("Z", "+00:00"))
        with self.factory() as s:
            self.persist(s, ctx)
            if key in self.recorded:
                s.commit()
                return {
                    **self._follow_out(cand, where, "duplicate", "recorded meanwhile by another worker"),
                    **base,
                }
            if ident.value:
                twin = s.scalar(
                    select(RecordRow.upc)
                    .where(RecordRow.run_id == self.run_id, RecordRow.record["upc"].astext == ident.value)
                    .limit(1)
                )
                if twin is not None:
                    s.commit()
                    return {
                        **self._follow_out(
                            cand,
                            where,
                            "duplicate",
                            f"its page states UPC {ident.value}, already recorded as {twin}",
                        ),
                        **base,
                    }
            row_id, built, assortment = self._follow_record(s, node, lst, fetch, pp.item, key, observed, cand)
            queue.heartbeat(s, ctx.lease, lease_s=ctx.lease_s)  # fence: only the task's owner writes
            s.commit()
        self.recorded.add(key)
        detail: dict[str, Any] = {
            "item_id": item_id,
            "url": url,
            "endpoint": "store",
            "fresh": True,
            "page_fetch_id": fetch.fetch_id,
            "requested_at": fetch.started_at,
            "http_status": fetch.status,
            "body_sha256": fetch.notes.get("raw_sha256"),
            "raw_key": fetch.notes.get("raw_key"),
            "credits": fetch.notes.get("credits"),
            "request_id": fetch.notes.get("request_id"),
            "page_item": ident.page_item,
            "matched": ident.matched,
            "candidates": [list(c) for c in ident.candidates[:10]],
            "read_by": "follow_up",
            "observed_by_run": self.run_id,
        }
        if ident.value:
            detail.update(status="extracted", value=ident.value, source=ident.source, path=ident.path)
        else:
            detail.update(status="absent_in_source", reason="the item's own page data states no UPC or GTIN")
        detail["size"] = wps.pack_size(wpd.next_data(html), str(built.record.get("weight") or "")).as_dict()
        detail["body_sha256"] = detail["body_sha256"] or hashlib.sha256(html.encode("utf-8")).hexdigest()
        self._set_detail(ctx, row_id, detail)
        exported = built.status in (RecordStatus.VALID, RecordStatus.EXPORTED_NOT_VALID)
        reasons = [r.value for r in built.reasons]
        return {
            **self._follow_out(
                cand,
                where,
                "included" if exported else "excluded",
                ""
                if exported
                else "the product page shows no eligible local offer or assortment: " + ", ".join(reasons),
            ),
            **base,
            "record_status": built.status.value,
            "reasons": reasons,
            "flags": [f.value for f in built.flags],
            "assortment": assortment.get("status"),
            "upc": ident.value or None,
        }

    def _follow_failed(self, last: str) -> None:
        """One more consecutive product page refused or failed; at the detail limit the follow-ups pause
        for this execution (the rest are recorded as not attempted, with the reason)."""
        self.follow_failures += 1
        if self.follow_paused is None and self.follow_failures >= self.cfg.detail.pause_after_failures:
            self.follow_paused = (
                f"{self.follow_failures} consecutive product pages refused or failed (last: {last})"
            )
            with self.factory() as s:
                event(s, self.run_id, "WARN", "FOLLOW_UP_PAUSED", self.follow_paused[:500])
                s.commit()

    def _follow_record(
        self,
        s: Session,
        node: Node,
        lst: Listing,
        fetch: PageFetch,
        item: wpd.WalmartItem,
        key: str,
        observed: datetime,
        cand: Mapping[str, Any],
    ) -> tuple[str, BuiltRecord, dict[str, Any]]:
        """The record of a followed product from its own page, exactly as a result tile's (the identity is
        its item id; the UPC is added from the same page by the detail rules)."""
        item = replace(item, upc="")
        observed_iso = iso(observed)
        store_values, store_prov = self.store_values()
        ev, offer, log = wrec.evidence(
            item,
            fetch_id=fetch.fetch_id,
            observed_at=observed_iso,
            store_id=self.store.location_id,
            modality=self.modality,
            page_verified=True,
        )
        built = build_product_record(
            ev,
            store=store_values,
            category=CategoryAssignment(node.category, lst.name),
            crawl_date=store_local_date(observed, self.store.timezone),
            settings=self.settings.records,
            detector=self.pipe.detector,
            configured_modality=self.modality,
            store_provenance=store_prov,
        )
        built = wrec.explain_missing(built, item, offer, STORE_LOGO_NOTE)
        built, assortment = self.assortment(s, key, built, offer, observed)
        missing_kind = wrec.missing_kinds(built, item, offer)
        if assortment.get("basis") in ("local_offer_observed_earlier", "store_line_other_fulfillment"):
            missing_kind.update({f: "context_failed" for f in OFFER_FIELDS if f in built.missing})
        field_observed_at = {f: observed_iso for f, v in built.record.items() if v}
        for f in ("zipcode", "store_name", "store_location", "store_logo"):
            if built.record.get(f) and self.selection is not None:
                field_observed_at[f] = self.selection.observed_at
        verified = built.status is RecordStatus.VALID
        s.execute(
            insert(ProductObservation)
            .values(
                id=new_id(),
                run_id=self.run_id,
                mode=self.run_mode,
                upc=key,
                page_fetch_id=fetch.fetch_id,
                source="pdp",
                displayed=wrec.displayed(item),
                structured={"walmart": log},
                provenance={
                    "verified": verified,
                    "retailer": RETAILER,
                    "node": node.taxonomy_id,
                    "listing": lst.id,
                    "listing_url": lst.url,
                    "category": node.category,
                    "sub_category": lst.name,
                    "store_check": "PASS",
                    "local_offer": log["local_offer"],
                    "assortment": assortment,
                    "segment": self.segment_id,
                    "worker": self.worker_name,
                    "session_id": self.session.session_id if self.session else None,
                    "pilot": self.pilot,
                    "fields": built.provenance,
                    "field_observed_at": field_observed_at,
                    "missing": built.missing,
                    "missing_kind": missing_kind,
                    "source_check": built.source_check,
                    "offers": offer_summaries(built, self.settings),
                    "follow_up": {
                        "kind": cand["kind"],
                        "named_by": cand.get("named_by") or None,
                        "option": cand.get("option"),
                        "seen_on": cand.get("seen_on"),
                        "seed": cand.get("seed"),
                    },
                },
                flags=[f.value for f in built.flags],
                parser_version=PARSER_VERSION,
                observed_at=observed,
            )
            .on_conflict_do_nothing(constraint="uq_product_observations_key")
        )
        row_id = new_id()
        s.execute(
            insert(RecordRow)
            .values(
                id=row_id,
                run_id=self.run_id,
                mode=self.run_mode,
                upc=key,
                record=built.record,
                record_sha256=record_sha256(built.record),
                primary_category_source_id=node.category_source_id,
                status=built.status.value,
                reasons=[r.value for r in built.reasons],
                flags=[f.value for f in built.flags],
            )
            .on_conflict_do_nothing(constraint="uq_records_run_upc")
        )
        for c in built.deals.classified:
            s.add(
                OfferObservationRow(
                    run_id=self.run_id,
                    mode=self.run_mode,
                    upc=key,
                    page_fetch_id=fetch.fetch_id,
                    source=c.offer.source.value,
                    tag=c.offer.tag,
                    headline=c.offer.text,
                    description=format_description(c.offer, self.settings.records.deal_description_format),
                    expiry_text=c.offer.expiry_text,
                    requires_clip=c.requires_clip,
                    kind=c.kind.value,
                    explicit_price=c.explicit_price,
                    modalities=sorted(c.restricted_to) if c.restricted_to else [],
                    flags=[f.value for f in c.flags],
                )
            )
        return row_id, built, assortment

    # -- automated canary ---------------------------------------------------------------------------

    def canary_checks(self, fetch: PageFetch) -> tuple[bool, dict[str, Any]]:
        """The first recorded page's records checked automatically: enough valid records, required fields
        filled, prices in two-decimal form, and every valid record equal to the page's own item data read
        independently of the collector's parser (:mod:`walmart_headless.checks.source_check`)."""
        cfg = self.canary_cfg
        with self.factory() as s:
            rows = list(
                s.scalars(
                    select(RecordRow)
                    .join(
                        ProductObservation,
                        (ProductObservation.run_id == RecordRow.run_id)
                        & (ProductObservation.upc == RecordRow.upc),
                    )
                    .where(
                        RecordRow.run_id == self.run_id,
                        ProductObservation.page_fetch_id == fetch.fetch_id,
                        ProductObservation.source == "card",
                    )
                )
            )
        valid = [r for r in rows if r.status == RecordStatus.VALID.value]
        problems: list[str] = []
        if len(valid) < cfg.min_valid_records:
            problems.append(
                f"{len(valid)} valid records on the first page (at least {cfg.min_valid_records})"
            )
        ratio = len(valid) / len(rows) if rows else 0.0
        if rows and ratio < cfg.min_valid_ratio:
            problems.append(
                f"{ratio:.0%} of the page's records are valid (at least {cfg.min_valid_ratio:.0%})"
            )
        missing: dict[str, int] = {}
        bad_prices = 0
        for r in valid:
            for name in cfg.required_fields:
                if not str(r.record.get(name) or "").strip():
                    missing[name] = missing.get(name, 0) + 1
            for name in ("regular_price", "sale_price"):
                value = str(r.record.get(name) or "")
                if value and not re.fullmatch(r"\d+\.\d{2}", value):
                    bad_prices += 1
        if missing:
            problems.append(f"required fields empty in valid records: {missing}")
        if bad_prices:
            problems.append(f"{bad_prices} prices not in two-decimal form")
        source: dict[str, Any] = {"checked": 0, "mismatch": 0, "unverified": 0}
        if cfg.source_check and valid:
            nd = source_check.page_json_text(self.html(fetch))
            # A product the page shows twice (an organic and a sponsored placement): the placement that
            # matches the record best, as the full source check reads a run's pages.
            items: dict[str, list[dict[str, Any]]] = {}
            for _, it in source_check.items_of(nd or {}):
                items.setdefault(str(it.get("usItemId")), []).append(it)
            for r in valid:
                item_id = source_check.item_id_of(str(r.record.get("url") or ""))
                placements = items.get(item_id or "")
                if not placements:
                    source["unverified"] += 1
                    continue
                ok = min(
                    (source_check.compare(r.record, it)[0] for it in placements),
                    key=lambda checks: sum(not v for v in checks.values()),
                )
                source["checked"] += 1
                if not all(ok.values()):
                    source["mismatch"] += 1
            if source["mismatch"] or source["unverified"]:
                problems.append(
                    f"{source['mismatch']} valid records differ from the page's own data and "
                    f"{source['unverified']} could not be found in it"
                )
        summary = {
            "page": fetch.fetch_id,
            "url": fetch.final_url or fetch.url,
            "records": len(rows),
            "valid": len(valid),
            "valid_ratio": round(ratio, 3),
            "source_check": source,
            "problems": problems,
        }
        return not problems, summary

    def canary(self, fetch: PageFetch, res: PageResult) -> None:
        """After the first result page that recorded products: continue only when its automated checks pass;
        otherwise stop the run (not resumable) with the reasons."""
        done = any(getattr(m, "canary_done", False) for m in self.crew.members)
        if not self.canary_cfg.enabled or done or res.new_records == 0:
            return
        passed, summary = self.canary_checks(fetch)
        self.canary_done = passed
        with self.factory() as s:
            run = s.get(Run, self.run_id)
            assert run is not None
            run.counts = {
                **(run.counts or {}),
                "canary": {"status": "passed" if passed else "failed", "at": iso(self.clock()), **summary},
            }
            event(
                s,
                self.run_id,
                "INFO" if passed else "WARN",
                "CANARY_PASSED" if passed else "CANARY_FAILED",
                "first recorded page passed the automated checks: collection continues"
                if passed
                else "first recorded page failed the automated checks: " + "; ".join(summary["problems"]),
                summary,
            )
            s.commit()
        if not passed:
            raise RunStop(
                StopCode.CANARY_CHECK_FAILED,
                "; ".join(summary["problems"])[:2000],
                resumable=False,
            )

    # -- retention of the store's verified products ----------------------------------------------------

    async def h_assemble(self, ctx: TaskContext) -> dict[str, Any]:
        """Every exported product gets its UPC outcome; products verified by earlier runs of the store and not
        observed by this run are carried forward unchanged (``retention.py``); then the shared assembly."""
        self.reuse_saved_details(ctx)  # release 1.6.1: what earlier reads established, even after a stop
        with ctx.session() as s:
            details = self.close_details(s)
            run = s.get(Run, self.run_id)
            assert run is not None
            nodes = self.node_outcomes(s)
            complete = bool(nodes) and all(n["status"] in ("DONE", "EMPTY") for n in nodes)
            cfg = self.historical_cfg
            kept = (
                retention.carry_forward(
                    s,
                    self.run_id,
                    self.store_id,
                    self.clock(),
                    location_id=self.store.location_id,
                    modality=self.modality,
                    run_complete=complete,
                    before=self.history_before,
                    mode=self.run_mode,
                    exclude_relative=self.settings.records.exclude_relative_price_items,
                )
                if cfg.enabled
                else {
                    "carried_forward": 0,
                    "not_verified_by_current_rules": 0,
                    "refused_sources": 0,
                    "not_valid_now": 0,
                }
            )
            s.flush()
            recovered = self.recover_carried_details(s)  # release 1.6.3
            s.flush()
            run.counts = {
                **(run.counts or {}),
                "historical": kept,
                "upc_detail": details,
                "carried_details": recovered,
                "field_dispositions": dispositions.counts(field_dispositions(s, self.run_id)),
            }
            if recovered["answered_by_saved_read"] or recovered["withheld"]:
                event(
                    s,
                    self.run_id,
                    "INFO",
                    "CARRIED_DETAILS_RECOVERED",
                    f"{recovered['upc_filled']} UPCs and {recovered['weight_filled']} sizes of carried rows "
                    "filled from saved reads of the items' own pages (each with that read's time, run, "
                    f"revision and page); {recovered['withheld']} left as carried, with the reason",
                    recovered,
                )
            event(
                s,
                self.run_id,
                "INFO",
                "PRODUCT_DETAILS_CLOSED",
                "UPC outcomes of the exported products",
                details,
            )
            if any(kept.values()):
                event(
                    s,
                    self.run_id,
                    "INFO",
                    "HISTORICAL_OBSERVATIONS",
                    f"{kept['carried_forward']} products verified by earlier runs and not observed by this "
                    "run carried forward unchanged (each with its own crawl date)",
                    kept,
                )
            s.commit()
        return await super().h_assemble(ctx)
