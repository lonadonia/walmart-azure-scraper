"""The pages a live run visits: one node per row of the client's Walmart category CSV (a category page
whose subcategory listings are read during the run, or a listing)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Node:
    row_index: int
    category: str  # the client's category name (CSV)
    category_source_id: str
    sub_category: str  # the site menu's subcategory title ("" until a landing page names it)
    taxonomy_id: str
    url: str
    # "listing": a page of products; "landing": a category page whose subcategory listings are found on
    # it when the run gets there (Walmart /cp/ pages). Snapshots written before 1.1 have no kind.
    kind: str = "listing"
    excluded: tuple[str, ...] = ()  # subcategory names the client's category list excludes
    only: tuple[str, ...] = ()  # a landing page narrowed to these subcategory listings (URL or path id)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> Node:
        values = dict(d)
        values["excluded"] = tuple(values.get("excluded") or ())
        values["only"] = tuple(values.get("only") or ())
        return cls(**values)


def plan_walmart_nodes(
    sources: Sequence[Mapping[str, Any]],
    categories: Sequence[int],
    subcategories: Mapping[str, Sequence[str]],
) -> tuple[list[Node], list[dict[str, Any]]]:
    """One node per client category row, in CSV order. A listing row (``/browse/``) is a page of
    products; a landing row (``/cp/``) is a category page whose subcategory listings are read from the page
    when the run reaches it, leaving out the subcategories the row's notes exclude.

    ``sources`` are the enabled Walmart ``category_sources`` rows (row_index, category_name, id, url, kind,
    landing_slug, notes). ``subcategories`` optionally narrows a landing row to some subcategory listings
    (their URLs or path ids), for example for a bounded pilot; a listing row ignores it."""
    from walmart_headless.sites.walmart.csv_sources import SourceKind, excluded_subcategories

    by_row = {int(s["row_index"]): s for s in sources}
    wanted = sorted(categories) if categories else sorted(by_row)
    nodes: list[Node] = []
    skipped: list[dict[str, Any]] = []
    for row_index in wanted:
        src = by_row.get(row_index)
        if src is None:
            skipped.append({"row": row_index, "reason": "not an enabled client category"})
            continue
        slug = str(src.get("landing_slug") or "")
        node_id = slug.rsplit("/", 1)[-1] or str(row_index)
        landing = src.get("kind") == SourceKind.LANDING.value
        chosen = tuple(str(x) for x in subcategories.get(str(row_index), []))
        nodes.append(
            Node(
                row_index,
                str(src["category_name"]),
                str(src["id"]),
                "" if landing else str(src["category_name"]),
                node_id,
                str(src["url"]),
                kind="landing" if landing else "listing",
                excluded=excluded_subcategories(str(src.get("notes") or "")),
                only=chosen if landing else (),
            )
        )
    return nodes, skipped
