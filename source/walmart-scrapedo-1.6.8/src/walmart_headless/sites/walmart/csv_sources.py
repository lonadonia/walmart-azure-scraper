"""Load ``Walmart_Category_URLs.csv``, the client's Walmart category list (same columns as Mariano's).

A row's URL is either a category landing page (``/cp/<slug>/<id>``), whose subcategories are found on the
page when it is collected, or a listing page (``/browse/<path>/<id>``) of products. Subcategories the
client excluded are named in the Notes column in quotes ("Exclude 'Shop All Foods' and 'Recipes'
subcategories"); they are read from there, never written into the collector.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from urllib.parse import urlsplit

EXPECTED_COLUMNS = ("Retailer", "Category (Auto)", "URL", "Scope", "Notes")
SITE_HOST = "www.walmart.com"
_QUOTED = re.compile(r"'([^']+)'")


class SourceKind(StrEnum):
    LANDING = "walmart_landing"  # /cp/<slug>/<id>: a category page linking to its subcategories
    LISTING = "walmart_listing"  # /browse/<path>/<id>: a product listing


@dataclass(frozen=True)
class CategorySource:
    row_index: int
    retailer: str
    category_name: str
    url: str
    scope: str
    notes: str
    kind: SourceKind
    landing_slug: str | None  # the path after /cp/ or /browse/, e.g. "food/976759"
    taxonomy_id: str | None = None  # Walmart category ids ("5427_486190") are kept in landing_slug
    excluded_subcategories: tuple[str, ...] = field(default_factory=tuple)


class CategoryCsvError(ValueError):
    pass


def classify(url: str) -> tuple[SourceKind, str]:
    parts = urlsplit(url)
    if parts.netloc != SITE_HOST:
        raise CategoryCsvError(f"unexpected host in {url!r}")
    path = parts.path.rstrip("/")
    if path.startswith("/cp/"):
        return SourceKind.LANDING, path[len("/cp/") :]
    if path.startswith("/browse/"):
        return SourceKind.LISTING, path[len("/browse/") :]
    raise CategoryCsvError(f"unsupported Walmart category URL {url!r}")


def excluded_subcategories(notes: str) -> tuple[str, ...]:
    """Subcategory names an "Exclude ..." note quotes; nothing for other notes."""
    if not re.search(r"\bexclud", notes, re.I):
        return ()
    return tuple(n.strip() for n in _QUOTED.findall(notes) if n.strip())


def parse_category_csv(data: bytes) -> tuple[list[CategorySource], str]:
    """The rows in file order and the sha256 of the file bytes."""
    sha = hashlib.sha256(data).hexdigest()
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    if tuple(reader.fieldnames or ()) != EXPECTED_COLUMNS:
        raise CategoryCsvError(f"unexpected columns {reader.fieldnames}; expected {EXPECTED_COLUMNS}")
    rows: list[CategorySource] = []
    seen: set[str] = set()
    for i, raw in enumerate(reader):
        name = (raw["Category (Auto)"] or "").strip()
        url = (raw["URL"] or "").strip()
        retailer = (raw["Retailer"] or "").strip()
        if not name or not url:
            raise CategoryCsvError(f"row {i}: category and URL are required")
        if retailer.lower() != "walmart":
            raise CategoryCsvError(f"row {i}: retailer {retailer!r} in the Walmart list")
        if name in seen:
            raise CategoryCsvError(f"row {i}: duplicate category {name!r}")
        seen.add(name)
        kind, slug = classify(url)
        notes = (raw["Notes"] or "").strip()
        rows.append(
            CategorySource(
                row_index=i,
                retailer="walmart",
                category_name=name,
                url=url,
                scope=(raw["Scope"] or "").strip(),
                notes=notes,
                kind=kind,
                landing_slug=slug,
                excluded_subcategories=excluded_subcategories(notes),
            )
        )
    return rows, sha


def load_category_csv(path: Path) -> tuple[list[CategorySource], str]:
    return parse_category_csv(path.read_bytes())
