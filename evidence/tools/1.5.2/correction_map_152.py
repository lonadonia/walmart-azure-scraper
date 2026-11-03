"""Correction maps of release 1.5.2: what its OFFLINE REPLAY of a live run says that the run's original exports did not.

The original exports stay as they were; this only reads them. For each product of a stage it compares, by key:
  products.json            the 22 exported fields
  provenance.json          fields, missing and missing_kind, upc_source
  field_dispositions.json  the upc and weight outcomes
Every difference is one row, with what kind of change it is, so a reader can tell a changed value from a changed
explanation of the same value.

usage: <collector venv python> -I -X utf8 correction_map_152.py BEFORE_EXPORTS AFTER_EXPORTS LABEL SOURCE_RUN REPLAY_RUN OUT
Writes OUT/<LABEL>_CORRECTION_MAP.csv and OUT/<LABEL>_CORRECTION_SUMMARY.json. OUT may exist; a file is never replaced.
"""

from __future__ import annotations

import collections
import csv
import io
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, "C:/w7/wt/headless/walmart-azure-headless/src")
from walmart_headless.sites.walmart import page_data as wpd  # noqa: E402

FIELDS = (
    "zipcode store_name store_location store_logo store_brand category sub_category product_title weight "
    "regular_price sale_price volume_deals_description volume_deals_price digital_deals_description "
    "digital_deals_price image_url url upc gupc ppm unit_price crawl_date"
).split()
RENAMED = {"inaccessible_challenged": ("blocked", "request_failed")}
# What any replay differs by, whatever the release: counted in the summary, not listed row by row. Neither says
# anything about the value.
INHERENT_FETCH = "replay_read_id"
INHERENT_ORIGIN = "replay_read_again"
ADDED_HASH = "capture_hash_added"
COUNTED_ONLY = {INHERENT_FETCH, ADDED_HASH}
COLS = [
    "item_id",
    "key",
    "observation_kind_after",
    "change_class",
    "file",
    "path",
    "before",
    "after",
    "why",
]


def load(path: Path) -> Any:
    return json.loads(path.read_text("utf-8"))


def rows_of(path: Path) -> list[dict]:
    d = load(path)
    return d["products"] if isinstance(d, dict) else d


def text(v: Any) -> str:
    if v is None:
        return ""
    return v if isinstance(v, str) else json.dumps(v, sort_keys=True, ensure_ascii=False)


def by_item(rows: list[dict]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for r in rows:
        out[wpd.item_id_from_url(r["url"])] = r
    return out


def walk(a: Any, b: Any, path: str):
    """The leaves where two JSON values differ."""
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            yield from walk(a.get(k), b.get(k), f"{path}.{k}" if path else k)
        return
    if a != b:
        yield path, a, b


def value_class(field: str, before: str, after: str) -> tuple[str, str]:
    if field == "store_brand":
        return "store_brand_value", "docs/PRIVATE_LABEL.md: a brand confirmed in the USPTO's records as Walmart's"
    if field == "weight":
        return "size_value", "the title rules of 1.5.2 (docs/VERIFICATION.md) or a carried row's own corrected run"
    if field == "upc":
        return "upc_value", "a saved page of the item, or the run's own read"
    return "other_value", "see the replay's provenance"


def provenance_class(path: str, before: Any, after: Any) -> tuple[str, str]:
    leaf = path.split(".")[-1]
    head = path.split(".")[0]
    if head == "missing_kind":
        if before == "source_absent":
            return (
                "missing_kind_corrected",
                "the page was never read or the value was found: only a page that was read can call a field absent",
            )
        if after is None:
            return "missing_kind_resolved", "the value is filled from its own page"
        return "missing_kind_corrected", "the disposition of the field's page"
    if head == "missing":
        return "missing_resolved", "a filled value no longer reads as missing"
    if head == "fields" and leaf == "fetch_id" and isinstance(before, str) and isinstance(after, str):
        return INHERENT_FETCH, "the replay's own read of the same stored page"
    if head == "fields" and leaf == "response_sha256" and not before:
        return ADDED_HASH, "the SHA-256 of the capture, always empty until 1.5.1"
    if head == "fields":
        return "field_source_corrected", "names the page the value really came from"
    if head in ("upc_source", "upc_detail"):
        return "upc_source_added", "the UPC's own page, place in the response, hash and time"
    return "provenance_other", leaf


def disposition_class(path: str, before: Any, after: Any) -> tuple[str, str]:
    leaf = path.split(".")[-1]
    if leaf == "disposition" and before in RENAMED:
        return "class_renamed", "inaccessible_challenged is split into blocked and request_failed"
    if leaf == "page_fetch_id" and before and after:
        return INHERENT_FETCH, "the replay's own read of the same stored page"
    if leaf == "origin" and after == "read_again":
        return INHERENT_ORIGIN, "a replay reads a page again: it never fetches one"
    if leaf == "disposition" and before == "fetched_detail" and after == "recovered_from_saved_detail":
        return INHERENT_ORIGIN, "a replay reads a page again: it never fetches one"
    if leaf in ("page_fetch_id", "path", "body_sha256", "item_id", "origin", "source"):
        return "disposition_detail_added", "the capture of the value: fetch, place in the response, hash"
    return "disposition_changed", "the field's outcome read again by 1.5.2"


def main() -> int:
    before_dir, after_dir, label, src, rp, out = (
        Path(sys.argv[1]),
        Path(sys.argv[2]),
        sys.argv[3],
        sys.argv[4],
        sys.argv[5],
        Path(sys.argv[6]),
    )
    out.mkdir(parents=True, exist_ok=True)
    target = out / f"{label}_CORRECTION_MAP.csv"
    summary_path = out / f"{label}_CORRECTION_SUMMARY.json"
    if target.exists() or summary_path.exists():
        raise SystemExit(f"{target} exists: never replaced")
    b_rows = by_item(rows_of(before_dir / "products.json"))
    a_rows = by_item(rows_of(after_dir / "products.json"))
    b_prov = load(before_dir / "provenance.json")["records"]
    a_prov = load(after_dir / "provenance.json")["records"]
    b_disp = {r["key"]: r for r in load(before_dir / "field_dispositions.json")}
    a_disp = {r["key"]: r for r in load(after_dir / "field_dispositions.json")}
    rows: list[dict[str, str]] = []
    counts: collections.Counter[str] = collections.Counter()

    def add(key: str, kind: str, cls: str, file: str, path: str, before: Any, after: Any, why: str) -> None:
        counts[cls] += 1
        if cls in COUNTED_ONLY:
            return
        rows.append(
            {
                "item_id": key.split(":", 1)[-1],
                "key": key,
                "observation_kind_after": kind,
                "change_class": cls,
                "file": file,
                "path": path,
                "before": text(before),
                "after": text(after),
                "why": why,
            }
        )

    only_before = sorted(set(b_rows) - set(a_rows))
    only_after = sorted(set(a_rows) - set(b_rows))
    for item in sorted(set(b_rows) & set(a_rows), key=int):
        key = f"wm:{item}"
        kind = (a_disp.get(key) or {}).get("observation_kind") or ""
        b, a = b_rows[item], a_rows[item]
        for f in FIELDS:
            if b[f] != a[f]:
                cls, why = value_class(f, b[f], a[f])
                add(key, kind, cls, "products.json", f, b[f], a[f], why)
    for key in sorted(set(b_prov) & set(a_prov)):
        kind = (a_disp.get(key) or {}).get("observation_kind") or ""
        pb, pa = b_prov[key], a_prov[key]
        for name in ("fields", "missing", "missing_kind", "upc_source"):
            for path, x, y in walk(pb.get(name), pa.get(name), name):
                cls, why = provenance_class(path, x, y)
                add(key, kind, cls, "provenance.json", path, x, y, why)
    for key in sorted(set(b_disp) & set(a_disp)):
        kind = a_disp[key].get("observation_kind") or ""
        for name in ("upc", "weight"):
            for path, x, y in walk(b_disp[key].get(name), a_disp[key].get(name), name):
                cls, why = disposition_class(path, x, y)
                add(key, kind, cls, "field_dispositions.json", path, x, y, why)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    target.write_bytes(("\ufeff" + buf.getvalue()).encode("utf-8"))
    values = collections.Counter(r["path"] for r in rows if r["file"] == "products.json")
    summary = {
        "evidence_class": "OFFLINE REPLAY",
        "label": f"OFFLINE REPLAY of live run {src} by replay run {rp}: no request was made, and the run's original "
        "exports are unchanged",
        "source_run": src,
        "replay_run": rp,
        "products_before": len(b_rows),
        "products_after": len(a_rows),
        "only_before": only_before,
        "only_after": only_after,
        "rows": len(rows),
        "by_change_class": dict(sorted(counts.items())),
        "counted_here_not_listed_in_the_map": sorted(COUNTED_ONLY),
        "exported_values_changed_by_field": dict(sorted(values.items())),
    }
    summary_path.write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(summary, indent=1)[:1600])
    return 0


if __name__ == "__main__":
    sys.exit(main())
