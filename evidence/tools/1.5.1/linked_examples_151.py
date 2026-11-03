"""Brief section 6: linked examples of PPM, genuine packs, offers, missing values and products without offers.

Every row is an AUTHENTIC value from a stored page of the owner-funded campaign of 2026-10-31 (or, where the row says
so, a saved page of the 1.4.1 evidence), resolved again here: the export's value is compared with what the stored page
holds at the path the provenance names, and the stored page's SHA-256 is recorded. A case the stored pages do not hold
is written PENDING: a synthetic parser test does not stand in for it. No request is made.

usage: <edition venv python> -I -X utf8 linked_examples_151.py OUT_DIR STAGE [STAGE...]
       STAGE order is the order of preference: the first stage holding a case gives its example.
"""

from __future__ import annotations

import csv
import glob
import gzip
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from walmart_headless import __version__ as VERSION
from walmart_headless.sites.walmart import page_data as wpd

EV = Path(r"C:\w7\evidence\live150")
DATA = Path(r"C:\w7\live\data\runs\walmart-3891-pickup")
FIELDS = [
    "example_id", "group", "case", "stage", "run_id", "source_revision", "evidence_class", "item_id", "product_title",
    "field", "exported_value", "source_value", "source_path", "check", "check_result", "page_fetch_id", "page_file",
    "page_sha256", "observed_at", "listing", "page", "position", "note",
]
PATH_TOKEN = re.compile(r"([^.\[\]]+)|\[(\d+)\]")


def resolve(data: Any, path: str) -> Any:
    """The value at a provenance path of a page's data; a trailing "(rule)" is the rule's name, not part of it."""
    node = data
    for name, index in PATH_TOKEN.findall(path.split(" (", 1)[0]):
        node = node[int(index)] if index else node[name]
    return node


class Stage:
    def __init__(self, name: str, run: str) -> None:
        self.name, self.run = name, run
        base = EV / "runs" / name / "exports"
        self.products = {self._item(p["url"]): p for p in json.loads((base / "products.json").read_text("utf-8"))}
        self.prov = json.loads((base / "provenance.json").read_text("utf-8"))["records"]
        self.disp = {r["key"]: r for r in json.loads((base / "field_dispositions.json").read_text("utf-8"))}
        self.memberships = json.loads((base / "memberships.json").read_text("utf-8"))
        self.revision = ""
        for row in self.disp.values():
            for field in ("weight", "upc"):
                if row[field].get("source_run") == run and row[field].get("source_revision"):
                    self.revision = str(row[field]["source_revision"])
                    break
            if self.revision:
                break

    @staticmethod
    def _item(url: str) -> str:
        return url.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1]

    def fresh(self) -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
        out = []
        for item, product in self.products.items():
            prov = self.prov.get(f"wm:{item}") or next(
                (v for v in self.prov.values() if (v.get("upc_detail") or {}).get("item_id") == item), None
            )
            if prov is not None and prov.get("observation_kind") == "fresh":
                out.append((item, product, prov))
        return sorted(out, key=lambda t: t[0])


class Pages:
    def __init__(self) -> None:
        self.cache: dict[str, tuple[Any, str, str]] = {}

    def page(self, run: str, fetch: str) -> tuple[Any, str, str]:
        if fetch not in self.cache:
            file = DATA / run / "live" / "dom" / f"{fetch}.html.gz"
            raw = file.read_bytes()
            self.cache[fetch] = (
                wpd.next_data(gzip.decompress(raw).decode("utf-8")),
                hashlib.sha256(raw).hexdigest(),
                f"1_new_live/runs/{run}/pages/{fetch}.html.gz",
            )
        return self.cache[fetch]


def example(pages: Pages, st: Stage, group: str, case: str, item: str, product: dict[str, Any], prov: dict[str, Any],
            field: str, check: str, note: str = "") -> dict[str, Any]:
    spec = prov["fields"][field]
    data, sha, file = pages.page(st.run, spec["fetch_id"])
    source = resolve(data, spec["selector_or_path"])
    exported = product[field]
    source_text = str(source)
    if check == "equal":
        ok = exported == source_text
    elif check == "title holds each part":
        ok = all(part.strip() in source_text for part in exported.split(","))
    elif check == "price as displayed":
        ok = exported in source_text.replace("$", "") and bool(re.fullmatch(r"\d+\.\d{2}", exported))
    else:
        raise SystemExit(f"unknown check {check}")
    obs = prov.get("observation") or {}
    return {
        "group": group, "case": case, "stage": st.name, "run_id": st.run, "source_revision": st.revision,
        "evidence_class": "LIVE VERIFIED", "item_id": item, "product_title": product["product_title"], "field": field,
        "exported_value": exported, "source_value": source_text, "source_path": spec["selector_or_path"], "check": check,
        "check_result": "PASS" if ok else "FAIL", "page_fetch_id": spec["fetch_id"], "page_file": file, "page_sha256": sha,
        "observed_at": spec.get("observed_at", ""), "listing": obs.get("listing", ""), "page": obs.get("page", ""),
        "position": obs.get("position", ""), "note": note,
    }


def pick_ppm(pages: Pages, stages: list[Stage]) -> list[dict[str, Any]]:
    unit = re.compile(r"/\s*(?:\d+\s*)?([A-Za-z ]+)$")
    out, seen = [], set()
    for st in stages:
        for item, product, prov in st.fresh():
            ppm = product.get("ppm") or ""
            m = unit.search(ppm)
            if not m:
                continue
            kind = ("$" if ppm.startswith("$") else "¢") + "/" + ("N " if re.search(r"/\s*\d", ppm) else "") + m.group(1).strip()
            if kind in seen or not (prov["fields"].get("ppm") or {}).get("selector_or_path"):
                continue
            seen.add(kind)
            out.append(example(pages, st, "PPM", f"displayed unit {kind}", item, product, prov, "ppm", "equal",
                               "copied as displayed, never calculated"))
    return out


def pick_packs(pages: Pages, stages: list[Stage]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    shapes = [
        ("bracketed multipack kept beside the size (release 1.5.1)",
         lambda w, r, t: r == "multipack_in_title" and re.match(r"\d+\s?pack, ", w, re.I) is not None),
        ("unbracketed pack in the title kept beside the size (release 1.5.1)",
         lambda w, r, t: r == "multipack_in_title" and re.match(r"\d+-pack, ", w, re.I) is not None),
        ("size and pack both in the trailing segments",
         lambda w, r, t: r == "trailing_segments" and re.search(r"\d\s?-?\s?pack", w, re.I) is not None),
        ("pack of N in the size", lambda w, r, t: re.search(r"pack of \d", w, re.I) is not None),
        ("family wording in the title is not a multipack", lambda w, r, t: bool(w) and re.search(r"family", t, re.I) is not None),
        ("bulk wording in the title is not a multipack", lambda w, r, t: bool(w) and re.search(r"\bbulk\b", t, re.I) is not None),
        ("value-pack wording in the title is not a multipack", lambda w, r, t: bool(w) and re.search(r"value pack", t, re.I) is not None),
        ("count stated with its unit", lambda w, r, t: re.fullmatch(r"\d+ (?:Count|ct|Ct)", w) is not None),
    ]
    for case, test in shapes:
        taken = 0
        for st in stages:
            for item, product, prov in st.fresh():
                if taken >= (2 if "wording" in case else 3):
                    break
                spec = prov["fields"].get("weight") or {}
                path = str(spec.get("selector_or_path") or "")
                rule = path.rsplit("(", 1)[-1].rstrip(")") if "(" in path else ""
                # A size recovered from a saved product page keeps fields.weight on the tile's title with rule "none" (a known
                # limitation of provenance.json in 1.5.1): it is not an example of what a title holds, and is shown in the group
                # "missing value" with its lineage from field_dispositions.json instead.
                if spec.get("source") != "walmart_title" or rule in ("", "none") or item in seen or not test(product["weight"], rule, product["product_title"]):
                    continue
                seen.add(item)
                taken += 1
                out.append(example(pages, st, "genuine pack", case, item, product, prov, "weight",
                                   "title holds each part", f"rule {rule}; displayed unit price {product.get('ppm') or 'none'}"))
            if taken >= (2 if "wording" in case else 3):
                break
        if not taken:
            saved = saved_title(case)
            note = "no authentic product of this shape on the stored pages of these stages"
            if "bulk" in case:
                note = ("no authentic product whose title uses bulk wording and states a size: the campaign's one bulk title, "
                        "Fresh Bulk Yellow Lemons (item 41752773, stages S1, S2, S4, S5a), shows no size on its tile and exports "
                        "a blank weight; no size was invented from it")
            out.append(saved or {"group": "genuine pack", "case": case, "evidence_class": "PENDING", "note": note})
    return out


# Shapes the campaign's pages may not hold: an authentic title of the 1.4.1 saved pages (all_titles.json), read here by
# the installed release's rule. Offline: nothing was requested, and the page's other fields are not claimed.
SAVED_SHAPES = {
    "unbracketed pack in the title kept beside the size (release 1.5.1)": "Play-Doh 8-Pack Rainbow Colors",
    "pack of N in the size": "Similac 360 Total Care Made With Whole Milk Ready-to-Feed Baby Formula, 8-fl-oz Bottle, Pack of 6",
}


def saved_title(case: str) -> dict[str, Any] | None:
    from walmart_headless.sites.walmart import records as wrec

    start = SAVED_SHAPES.get(case)
    if not start:
        return None
    titles = json.loads(Path(r"C:\w7\evidence\pack_fix_151\all_titles.json").read_text("utf-8"))["titles"]
    title = next((t for t in sorted(titles) if t.startswith(start)), None)
    if title is None:
        return None
    size = wrec.size_from_title(title)
    release, run, fetch = titles[title]["first"]
    found = sorted(glob.glob(f"C:/w7/b/*/*/*_new_live_*/runs/*/{run}/pages/dom/{fetch}.html.gz"))
    file = Path(found[0]) if found else None
    return {
        "group": "genuine pack", "case": case, "stage": f"saved page of release {release}", "run_id": run,
        "source_revision": f"title read offline by the rule of release {VERSION}", "evidence_class": "OFFLINE REPROCESSING",
        "item_id": ", ".join(titles[title]["items"]), "product_title": title, "field": "weight", "exported_value": size.value,
        "source_value": title, "source_path": "the tile's name", "check": "title holds each part",
        "check_result": "PASS" if all(p.strip() in title for p in size.value.split(",")) else "FAIL", "page_fetch_id": fetch,
        "page_file": file.as_posix().removeprefix("C:/w7/b/") if file else "",
        "page_sha256": hashlib.sha256(file.read_bytes()).hexdigest() if file else "",
        "note": f"rule {size.outcome}; no live example of this shape on the campaign's stored pages; the 1.4.1 edition evidence holds this page",
    }


def pick_sale(pages: Pages, stages: list[Stage]) -> list[dict[str, Any]]:
    out = []
    for st in stages:
        for item, product, prov in st.fresh():
            spec = prov["fields"].get("sale_price") or {}
            if product.get("sale_price") and spec.get("selector_or_path"):
                out.append(example(pages, st, "not an offer", "a Rollback: a displayed sale price, not a volume or digital deal",
                                   item, product, prov, "sale_price", "price as displayed",
                                   "volume and digital fields stay empty; the price is the one the page displays"))
                return out
    return out


def pick_missing(pages: Pages, stages: list[Stage]) -> list[dict[str, Any]]:
    out = []
    wanted = [
        ("upc", "budget_deadline_interruption"), ("upc", "absent_in_source"), ("upc", "not_attempted"),
        ("upc", "inaccessible_challenged"), ("upc", "parse_failure"), ("upc", "identity_mismatch"),
        ("weight", "budget_deadline_interruption"), ("weight", "absent_in_source"), ("weight", "unresolved_conflict"),
        ("weight", "not_attempted"), ("weight", "inaccessible_challenged"), ("weight", "parse_failure"),
        ("weight", "identity_mismatch"),
    ]
    for field, disposition in wanted:
        hit = None
        for st in stages:
            for key, row in sorted(st.disp.items()):
                if row[field]["disposition"] == disposition and row.get("observation_kind") == "fresh":
                    hit = (st, key, row)
                    break
            if hit:
                break
        base = {"group": "missing value", "case": f"{field}: {disposition}", "field": field}
        if hit is None:
            saved = saved_outcome(field, disposition)
            out.append({**base, **saved} if saved else {
                **base, "evidence_class": "PENDING",
                "note": "no fresh product of the campaign has this outcome: no live example exists; the tests "
                        "that show it are synthetic and do not stand in for one"})
            continue
        st, key, row = hit
        d = row[field]
        out.append({
            **base, "stage": st.name, "run_id": st.run, "source_revision": st.revision, "evidence_class": "LIVE VERIFIED",
            "item_id": key.removeprefix("wm:"), "product_title": row["product_title"], "exported_value": d.get("value", ""),
            "source_value": "; ".join(d.get("conflicts") or []) or d.get("reason", ""), "source_path": d.get("path") or "",
            "check": "exported value empty", "check_result": "PASS" if d.get("value", "") == "" else "FAIL",
            "page_fetch_id": d.get("page_fetch_id", ""), "page_sha256": d.get("body_sha256", ""),
            "observed_at": d.get("observed_at", ""),
            "note": f"read by run {d.get('source_run')} at revision {d.get('source_revision')}" if d.get("source_run") else "",
        })
    return out


def saved_outcome(field: str, disposition: str) -> dict[str, Any] | None:
    """An outcome no fresh product of the campaign had: from the saved pages of the 1.4.1 evidence, offline."""
    if field == "upc" and disposition in ("absent_in_source", "not_attempted"):
        table = Path(r"C:\w7\evidence\reprocessing_b3\reconciliation\B3_FIELD_DISPOSITIONS_662.csv")
        for row in csv.DictReader(table.open(encoding="utf-8-sig")):
            if row["upc_disposition_after"] == disposition:
                return {
                    "stage": "B3 reprocessed offline", "run_id": row["upc_source_run_after"], "evidence_class": "OFFLINE REPROCESSING",
                    "item_id": row["item_id"], "product_title": row["product_title"], "exported_value": row["upc_after"],
                    "source_value": row["upc_reason_after"], "check": "exported value empty",
                    "check_result": "PASS" if not row["upc_after"] else "FAIL", "observed_at": row["upc_observed_at_after"],
                    "note": "run B3 of release 1.4.1 reprocessed offline; its saved pages only",
                }
    if disposition in ("identity_mismatch", "parse_failure"):
        logs = list((EV / "logs").glob("*_import_detail_captures.jsonl"))
        lines = logs[0].read_text("utf-8", errors="replace").splitlines()
        result = [json.loads(x)["result"] for x in lines if x.startswith("{") and '"result"' in x][-1]
        want = "identity_mismatch" if disposition == "identity_mismatch" else "parse_failed"
        refused = [r for r in result["refused"] if r["refused"] == want]
        hit = next((r for r in refused if "is for item" in r.get("reason", "")), refused[0] if refused else None)
        if hit:
            return {
                "stage": "import of the 1.4.1 saved pages", "run_id": hit["path"].split("/runs/")[1].split("/")[1],
                "evidence_class": "OFFLINE REPROCESSING", "item_id": hit["item_id"],
                "exported_value": "", "source_value": hit.get("reason", ""), "source_path": hit["path"],
                "check": "the page was refused and nothing was taken from it", "check_result": "PASS",
                "note": f"one of {result['counts'].get(want)} saved pages refused with this outcome when the 1,441 saved "
                        "pages were loaded; applies to the UPC and the size of the same page",
            }
    return None


def pick_no_offer(pages: Pages, stages: list[Stage], offers_csv: Path) -> list[dict[str, Any]]:
    rows = list(csv.DictReader(offers_csv.open(encoding="utf-8-sig")))
    by_stage = {s.name: s for s in stages}
    out, seen_categories = [], set()
    # Products whose own page was read come first: the tile and the page both say so.
    rows.sort(key=lambda r: (r["product_page"].startswith("product_page_not_read"), [s.name for s in stages].index(r["stage"]) if r["stage"] in by_stage else 99))
    for row in rows:
        st = by_stage.get(row["stage"])
        if st is None or row["tile_disposition"] != "absent_on_result_tile":
            continue
        product = st.products.get(row["item_id"])
        prov = st.prov.get(f"wm:{row['item_id']}")
        if not product or not prov or product["category"] in seen_categories or prov.get("observation_kind") != "fresh":
            continue
        seen_categories.add(product["category"])
        page_read = not row["product_page"].startswith("product_page_not_read")
        spec = prov["fields"]["product_title"]
        data, sha, file = pages.page(st.run, spec["fetch_id"])
        tile = resolve(data, spec["selector_or_path"].rsplit(".name", 1)[0])
        has_promo = bool(tile.get("promoDiscount"))
        out.append({
            "group": "product without an offer",
            "case": f"{product['category']}: " + ("read on its tile and its own page" if page_read else "read on its tile; its own page not read"),
            "stage": st.name, "run_id": st.run, "source_revision": st.revision, "evidence_class": "LIVE VERIFIED",
            "item_id": row["item_id"], "product_title": product["product_title"], "field": "volume_deals_description, digital_deals_description",
            "exported_value": product["volume_deals_description"] + product["digital_deals_description"],
            "source_value": f"badges on the tile: {row['tile_badges'] or 'none'}; promoDiscount on the tile: {has_promo}; product page: {row['product_page']}",
            "source_path": spec["selector_or_path"].rsplit(".name", 1)[0],
            "check": "both exported descriptions empty and no promotion wording or structure on the tile",
            "check_result": "PASS" if not (product["volume_deals_description"] or product["digital_deals_description"] or row["tile_promotion_texts"] or has_promo) else "FAIL",
            "page_fetch_id": spec["fetch_id"], "page_file": file, "page_sha256": sha, "observed_at": spec.get("observed_at", ""),
            "note": "absent, not unparsed: the tile and the product page were both read" if page_read
                    else "absent from the tile; whether its own page shows an offer is not claimed: not read in the campaign",
        })
    return out


def main() -> int:
    out_dir = Path(sys.argv[1])
    names = sys.argv[2:]
    if out_dir.exists():
        raise SystemExit(f"{out_dir} exists: a new folder only")
    runs = json.loads((EV / "runs.json").read_text("utf-8"))
    stages = [Stage(n, runs[n]) for n in names]
    pages = Pages()
    offers_dir = Path(next(p for p in (r"C:\w7\evidence\offers_live_final", r"C:\w7\evidence\offers_live_pre_s5a") if Path(p).is_dir()))
    rows: list[dict[str, Any]] = []
    rows += pick_ppm(pages, stages)
    rows += pick_packs(pages, stages)
    rows += pick_sale(pages, stages)
    rows += pick_missing(pages, stages)
    rows += pick_no_offer(pages, stages, next(offers_dir.glob("LIVE_OFFER_DISPOSITIONS_1_5_*.csv")))
    pending_note = (
        "no authentic product on the campaign's stored pages or the 1.4.1 saved pages displays such an offer: the "
        "campaign's listing and product pages hold none, and the 9 promoDiscount structures of 129 saved listing pages "
        "carry no displayed terms. Synthetic parser tests do not satisfy this requirement."
    )
    rows.append({"group": "offer", "case": "displayed volume offer (multi-unit or BOGO, no clipping)", "evidence_class": "PENDING", "note": pending_note})
    rows.append({"group": "offer", "case": "displayed digital offer (clipping or activation, explicit eligibility)", "evidence_class": "PENDING", "note": pending_note})
    for n, row in enumerate(rows, start=1):
        row["example_id"] = f"E{n:03d}"
    out_dir.mkdir(parents=True)
    with (out_dir / "LINKED_EXAMPLES.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows({k: r.get(k, "") for k in FIELDS} for r in rows)
    failed = [r["example_id"] for r in rows if r.get("check_result") == "FAIL"]
    from collections import Counter

    summary = {
        "evidence_class_of_rows": dict(Counter(r["evidence_class"] for r in rows)),
        "by_group": dict(Counter(r["group"] for r in rows)),
        "checks_failed": failed,
        "stages": {s.name: s.run for s in stages},
        "offers_source": str(offers_dir),
    }
    (out_dir / "LINKED_EXAMPLES_SUMMARY.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", "utf-8")
    print(json.dumps(summary, indent=1, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
