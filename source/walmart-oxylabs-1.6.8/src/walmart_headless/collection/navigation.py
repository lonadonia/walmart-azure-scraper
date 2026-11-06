"""The names the store's category pages give its listings, as earlier runs recorded them (release 1.6.7), and
what a navigation link shows (release 1.6.8).

The agreed category mapping: ``category`` is the client's CSV row and ``sub_category`` the name the row's
category page gives the listing a product was read from ("A listing that a category page names keeps the
site's name", release 1.6.6, TECHNICAL_REPORT section 8). A listing read directly by its path (a run narrowed
with ``--subcategory``) never reads that page, and its own result page may name it otherwise: Walmart's
category page names ``1115193_1071967_1630538`` "Fabric Softeners", the listing's own page "Fabric Softener".
Release 1.6.6's L12 and 1.6.3's L8 exported the second, L7 and L10 the first.

Every category page a run reads is recorded in a ``SUBCATEGORIES_FOUND`` event (the links it names, with their
names). :func:`category_page_names` reads those events of the store's runs, so a listing read by its path
takes the name its category page gave it, from data already stored: no request is made for it. A listing no
stored category page names keeps its own page's name, and says so (``Listing.named_by``).

Release 1.6.8: a link can show a listing filtered. Its query narrows the listing by a facet, a price or a
shelf. Live, Health & Wellness links ``976760_4661388_6244277_7158394`` as "Cough"
(``facet=health_concern:Cough``) and as "Subscription" (``facet=subscription_eligible:Subscription item``).
Each link shows part of the listing, never the listing itself. :func:`view_key` tells such views apart. A name
the page gives a filtered view names that view only, never the listing itself (the agreed mapping per view).
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import select
from sqlalchemy.orm import Session

from walmart_headless.acquisition.scrapedo_session import FULFILLMENT_FACETS
from walmart_headless.core import jsonvalues as jv
from walmart_headless.core.timeutil import iso
from walmart_headless.db.models import Event, Run
from walmart_headless.sites.walmart import page_data as wpd

FOUND_CODE = "SUBCATEGORIES_FOUND"
RULE = (
    "release 1.6.7: sub_category is the name the CSV row's category page gives the listing (the agreed "
    "category mapping); a listing read by its path takes it from the store's stored category pages; release "
    "1.6.8: a name the page gives a filtered view of a listing names that view only"
)
# Release 1.6.8: the query parameter that only says where a link was clicked (Walmart's page-origin tag,
# ``povid``): it does not change what a listing shows.
TRACKING_PARAMS = frozenset({"povid"})
_CATEGORY_ID = re.compile(r"\d+(?:_\d+)*")


def narrowing(url: str) -> tuple[tuple[str, str], ...]:
    """The filters a link's query narrows its listing by (release 1.6.8), sorted. Every query parameter with
    a value counts, an unknown one too (a filter taken for none would read part of a listing as all of it),
    except Walmart's tracking ``povid``, a ``cat_id`` that repeats the link's own ID and the collector's own
    fulfillment facet. A ``facet`` is split into its values, which Walmart joins with "||". A second "?" in a
    query separates parameters (live, Personal Care:
    ``cat_id=1005862_1001487&facet=gender%3AMale?povid=...``), and a parameter without a value is none (live:
    ``povid=..._FSA_&_HAS_2.9``). () for a link to the listing itself."""
    own = set(FULFILLMENT_FACETS.values())
    lid = wpd.listing_id(url)
    out: set[tuple[str, str]] = set()
    for key, value in parse_qsl(urlsplit(url).query.replace("?", "&")):
        k = key.strip()
        if not k or k in TRACKING_PARAMS or (k == "cat_id" and value.strip() == lid):
            continue
        for v in value.split("||") if k == "facet" else [value]:
            v = " ".join(v.split())
            if not v or (k == "facet" and v in own):
                continue
            out.add((k, v))
    return tuple(sorted(out))


def no_category(lid: str) -> bool:
    """A listing ID made of zeros (``/browse/pre-cut-fruits/0/0``): no category; Walmart's shelf links use it,
    their query (``_be_shelf_id``, ``facet=shelf_id:...``) being the whole listing (release 1.6.8)."""
    return bool(lid) and set(lid) <= {"0", "_"}


def view_key(url: str) -> str:
    """The view of a listing a link shows (release 1.6.8): the listing ID and, for a result listing
    (``/browse/``), the filters its query narrows it by. Two links with the same key show the same products,
    by any path. "" for a link without a listing ID. A category page of its own (``/cp/``) is read for its
    navigation, which no filter changes."""
    lid = wpd.listing_id(url)
    if not lid:
        return ""
    filters = narrowing(url) if urlsplit(url).path.startswith("/browse/") else ()
    return f"{lid}?{urlencode(filters)}" if filters else lid


def filtered_listing(url: str) -> str:
    """The URL of the listing a link shows filtered (release 1.6.8): for a ``/browse/`` link to a category
    whose query narrows it, the same path without its query. "" for a link to the listing itself, to a shelf
    (whose filters are the listing), to a category page, or to no category."""
    parts = urlsplit(url)
    lid = wpd.listing_id(url)
    if not parts.path.startswith("/browse/") or not _CATEGORY_ID.fullmatch(lid) or no_category(lid):
        return ""
    if not narrowing(url):
        return ""
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def read_id(url: str) -> str:
    """The ID a listing read through this link is recorded under (release 1.6.8): its listing ID; for a shelf
    (a listing ID of zeros), the ID with the shelf's facets, so that two shelves never share a record:
    ``0@shelf_id:8210692``, or a digest of its filters when no facet names it."""
    lid = wpd.listing_id(url)
    filters = narrowing(url)
    if not no_category(lid) or not filters:
        return lid
    facets = ",".join(v for k, v in filters if k == "facet")
    rid = f"{lid}@{facets}"
    if facets and len(rid) <= 64:
        return rid
    return f"{lid}@{hashlib.sha256(urlencode(filters).encode('utf-8')).hexdigest()[:16]}"


@dataclass(frozen=True)
class NamedBy:
    """The name a category page of the store gave a listing, and where that was recorded."""

    listing_id: str
    name: str
    run_id: str
    event_id: str
    at: datetime
    node: str  # the CSV row's category id the page belongs to

    def describe(self) -> str:
        return (
            f"named {self.name!r} by its category page (node {self.node}) in run {self.run_id} at "
            f"{iso(self.at)}, event {self.event_id}: stored navigation, no request"
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "listing_id": self.listing_id,
            "name": self.name,
            "run_id": self.run_id,
            "event_id": self.event_id,
            "at": iso(self.at),
            "node": self.node,
        }


def category_page_names(
    s: Session, store_id: str, *, before: datetime | None = None, node: str = ""
) -> dict[str, NamedBy]:
    """For each view a category page of the store named (its :func:`view_key`: the listing ID, for a link to
    the listing itself), the name the latest such page gave it. A link the page named but the run skipped
    (excluded, not a listing, not chosen, a filtered view a 1.6.8 run did not read) still has its name. A page
    that names one view twice, by two paths, gives it the first name (release 1.6.8: live, the Food page
    names ``976759_976794_2002490`` "Pantry", then "Great Value Pantry"; until the second 1.6.8 candidate the
    later link won).

    A filtered view of a listing has its own key: its name never names the listing itself (release 1.6.8;
    the third 1.6.8 candidate keyed a name by the listing ID only, and so named all of
    ``976760_4661388_6244277_7158394`` "Cough" after its filtered link).

    ``before`` (a replay: when its source run was created) leaves out what was stored at or after it, so a
    replay names its listings as its source run could have. With ``node`` (a CSV row's category id), a name
    the row's own category page gave wins over a name another row's page gave the same view."""
    query = (
        select(Event.id, Event.run_id, Event.ts, Event.data)
        .join(Run, Run.id == Event.run_id)
        .where(Run.store_id == store_id, Event.code == FOUND_CODE)
    )
    if before is not None:
        query = query.where(Event.ts < before)
    rows = s.execute(query.order_by(Event.ts, Event.id)).all()
    own: dict[str, NamedBy] = {}
    other: dict[str, NamedBy] = {}
    for event_id, run_id, ts, data in rows:
        d: Mapping[str, Any] = jv.obj(data, f"event {event_id}: data")
        page_node = jv.text(d.get("node"), f"event {event_id}: node")
        named_here: set[str] = set()  # the views this page named already
        links = [
            *jv.objects(d.get("listings"), f"event {event_id}: listings"),
            # Release 1.6.8: the filtered views a page links, recorded beside the listings a run reads.
            *jv.objects(d.get("filtered_views"), f"event {event_id}: filtered_views"),
        ]
        for i, link in enumerate(links):
            name = " ".join(jv.text(link.get("name"), f"event {event_id}: link {i}: name").split())
            url = jv.text(link.get("url"), f"event {event_id}: link {i}: url")
            key = view_key(url) if url else ""
            if not name or not key:
                continue
            if key in named_here:
                continue  # the page named this view before, by another path: its first name stands
            named_here.add(key)
            named = NamedBy(wpd.listing_id(url), name, str(run_id), str(event_id), ts, page_node)
            (own if node and page_node == node else other)[key] = named  # later events replace
    return {**other, **own}
